from dataclasses import dataclass
import time

from picamera2 import Picamera2  # only dependency besides your ML libs


@dataclass
class CameraML:
    camera_index: int  # kept for compatibility, not used by Picamera2
    model_path: str

    def __post_init__(self):
        # Init PiCamera2
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1.0)  # sensor warm‑up

        # TODO: load your real ML model here
        # Example for ONNX:
        # import onnxruntime as ort
        # self.session = ort.InferenceSession(
        #     self.model_path, providers=["CPUExecutionProvider"]
        # )
        self.session = None

    def _preprocess(self, frame_rgb):
        """
        Convert the PiCamera2 RGB frame (H,W,3) to the input format
        your ML model expects. Replace this stub with your pipeline.
        """
        # Example (no real preprocessing):
        return frame_rgb

    def _run_inference(self, input_data):
        """
        Run model on input_data and return label string.
        Replace this stub with real inference + label mapping.
        """
        # Example dummy logic:
        return "generic_object"

    def classify_object(self) -> str:
        """
        Capture one frame from Pi Camera and return predicted label.
        """
        # Picamera2 gives a NumPy array directly in RGB format
        frame_rgb = self.picam2.capture_array("main")

        # Preprocess for model
        model_input = self._preprocess(frame_rgb)

        # Inference
        label = self._run_inference(model_input)
        return label

    def release(self):
        if self.picam2 is not None:
            self.picam2.stop()
            self.picam2.close()
