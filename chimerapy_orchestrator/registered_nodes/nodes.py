import platform
import time
from typing import Any, Dict

import chimerapy as cp
import cv2
import imutils
import numpy as np
from PIL import ImageGrab

from chimerapy_orchestrator.utils import register_chimerapy_node


@register_chimerapy_node
class WebcamNode(cp.Node):
    def __init__(self):
        super(WebcamNode, self).__init__(name="WebcamNode")

    def prep(self):
        self.vid = cv2.VideoCapture(0)

    def step(self) -> cp.DataChunk:
        time.sleep(1 / 30)
        ret, frame = self.vid.read()
        self.save_video(name="test", data=frame, fps=20)
        data_chunk = cp.DataChunk()
        data_chunk.add("frame", frame, "image")
        return data_chunk

    def teardown(self):
        self.vid.release()


@register_chimerapy_node
class ShowWindow(cp.Node):
    def __init__(self):
        super(ShowWindow, self).__init__(name="ShowWindow")

    def step(self, data_chunks: Dict[str, cp.DataChunk]):
        for name, data_chunk in data_chunks.items():
            self.logger.debug(f"{self}: got from {name}, data={data_chunk}")

            cv2.imshow(name, data_chunk.get("frame")["value"])
            cv2.waitKey(1)


@register_chimerapy_node
class ScreenCaptureNode(cp.Node):
    def __init__(self):
        super(ScreenCaptureNode, self).__init__(name="ScreenCaptureNode")

    def prep(self):
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
        data_chunk = cp.DataChunk()
        data_chunk.add("frame", imutils.resize(frame, width=720), "image")

        # Then send it
        return data_chunk
