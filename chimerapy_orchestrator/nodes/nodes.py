import time
from typing import Any, Dict

import chimerapy as cp
import cv2

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
