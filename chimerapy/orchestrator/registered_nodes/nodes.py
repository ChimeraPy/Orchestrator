import platform
import time
from typing import Dict

import cv2
import imutils
import numpy as np
from PIL import ImageGrab

import chimerapy.engine as cpe
from chimerapy.orchestrator.registry.utils import sink_node, source_node


@source_node
class WebcamNode(cpe.Node):
    def __init__(self, name: str = "WebcamNode"):
        super().__init__(name=name)

    def setup(self):
        self.vid = cv2.VideoCapture(0)

    def step(self) -> cpe.DataChunk:
        time.sleep(1 / 30)
        ret, frame = self.vid.read()
        self.save_video(name="test", data=frame, fps=20)
        data_chunk = cpe.DataChunk()
        data_chunk.add("frame", frame, "image")
        return data_chunk

    def teardown(self):
        self.vid.release()


@sink_node
class ShowWindow(cpe.Node):
    def __init__(self, name: str = "ShowWindow"):
        super().__init__(name=name)

    def step(self, data_chunks: Dict[str, cpe.DataChunk]):
        for name, data_chunk in data_chunks.items():
            self.logger.debug(f"{self}: got from {name}, data={data_chunk}")

            cv2.imshow(name, data_chunk.get("frame")["value"])
            cv2.waitKey(1)

    def teardown(self):
        cv2.destroyAllWindows()


@source_node
class ScreenCaptureNode(cpe.Node):
    def __init__(self, name: str = "ScreenCaptureNode"):
        super().__init__(name=name)

    def setup(self):
        if platform.system() == "Windows":
            import dxcam

            self.camera = dxcam.create()
        else:
            self.camera = None

    def step(self):
        # Noticed that screencapture methods highly depend on OS
        if platform.system() == "Windows":
            time.sleep(1 / 30)
            frame = self.camera.grab()
            if not isinstance(frame, np.ndarray):
                return None
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            frame = cv2.cvtColor(
                np.array(ImageGrab.grab(), dtype=np.uint8), cv2.COLOR_RGB2BGR
            )

        # Save the frame and package it
        self.save_video(name="screen", data=frame, fps=20)
        data_chunk = cpe.DataChunk()
        data_chunk.add("frame", imutils.resize(frame, width=720), "image")

        # Then send it
        return data_chunk
