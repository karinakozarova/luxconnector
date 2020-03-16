#%%
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

from PIL import Image
from websocket import create_connection


class LuxConnector:
    def __init__(self, zoom_type: str = "IN") -> None:
        self.__start_lux_app()
        self.ws = create_connection("ws://localhost:3333/luxservice")
        self.set_liveview(True)
        self.set_zoom(zoom_type)

    def __start_lux_app(self)-> None:
        """
        Run the Lux server in a subservers
        """
        print("Start Lux Server")
        basefolder_loc = Path(__file__).parents[0]
        exe_loc = os.path.join(
            basefolder_loc, "LuxServer", "CytoSmartLuxService.exe"
        )
        subprocess.Popen(["cmd", "/K", exe_loc])

    def set_liveview(self, state: bool = True)-> None:
        '''
        Turn the liveview on or off

        state: (bool) True = live view on
        '''
        msg1 = {"type": "LIVE_STREAM", "payload": {"enable": state}}
        self.ws.send(json.dumps(msg1))
        result = self.ws.recv()
        print(result)

    def set_zoom(self, zoom_type: str = "IN")-> None:
        '''
        Set zoom type by turning off or on binning.

        zoom_type: (bool) str = IN or OUT
        '''
        zoom_type = zoom_type.upper()
        assert zoom_type in ["IN", "OUT"]

        msg1 = {"type": "ZOOM", "payload": {"action": zoom_type}}
        self.ws.send(json.dumps(msg1))
        result = self.ws.recv()
        print(result)

        # Toggle liveview to enforce the settings
        self.set_liveview(False)
        self.set_liveview(True)

    def set_focus(self, focus_level: float = 0)-> None:
        '''
        Set the relative z-position of the camera.
        And with that the focus.

        focus_level: (float) between 0 and 1 where the camera need to be.
        '''
        assert focus_level <= 1 and focus_level >= 0

        msg1 = {"type": "FOCUS", "payload": {"value": focus_level}}
        self.ws.send(json.dumps(msg1))
        result = self.ws.recv()
        print(result)

    def get_image(self)-> Image:
        '''
        Get the current image of the camera.
        '''
        name = str(uuid.uuid4())
        msg1 = {
            "type": "EXPERIMENT",
            "payload": {
                "action": "START",
                "experimentId": "",
                "name": name,
                "snapshotInterval": 50,
                "autoStopTime": 1,
                "sasToken": "",
            },
        }

        self.ws.send(json.dumps(msg1))
        result = self.ws.recv()
        print(result)
        
        count = 0
        while True:
            try:
                load_location = os.path.join(
                    r"C:\ProgramData", "CytoSmartLuxService", "Images", name
                )

                all_img_names = [i for i in os.listdir(load_location) if i.endswith(".jpg")]

                img = Image.open(os.path.join(load_location, max(all_img_names)))
                break
            except:
                count += 1
                print(f"failed {count} times to load image from experiment")
                time.sleep(1)
                if count >= 10:
                    print(f"After trying {count} times it is still not working")
                    img = None
                    break
        
        msg2 = {
            "type": "EXPERIMENT",
            "payload": {
                "action": "STOP",
                "experimentId": "",
                "name": name,
                "snapshotInterval": 50,
                "autoStopTime": 1,
                "sasToken": "",
            },
        }

        self.ws.send(json.dumps(msg2))

        return img
    