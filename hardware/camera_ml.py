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

        # Load TFLite model
        try:
            import tensorflow.lite as tflite
        except ImportError:
            raise ImportError("Please install 'tensorflow'")

        print(f"Loading model from {self.model_path}...")
        self.interpreter = tflite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.input_shape = self.input_details[0]['shape']
        print(f"Model input shape: {self.input_shape}")

    def _preprocess(self, frame_rgb):
        """
        Resize and normalize frame for TFLite model.
        """
        import cv2
        import numpy as np

        # Get target size from model input (e.g., [1, 224, 224, 3])
        # input_details[0]['shape'] usually looks like [1, height, width, channels]
        target_h = self.input_shape[1]
        target_w = self.input_shape[2]

        resized = cv2.resize(frame_rgb, (target_w, target_h))
        
        # Check if model expects float or int
        if self.input_details[0]['dtype'] == np.float32:
            # Normalize to [0, 1] if model expects float
            input_data = np.expand_dims(resized, axis=0).astype(np.float32) / 255.0
        else:
            # Keep as uint8 if model expects int (quantized)
            input_data = np.expand_dims(resized, axis=0).astype(self.input_details[0]['dtype'])
            
        return input_data

    def _run_inference(self, input_data):
        """
        Run TFLite inference and return label.
        """
        import numpy as np
        
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Assuming classification model output is [1, num_classes]
        # Map index to label
        # TODO: Update these labels to match your specific model's training
        labels = ["organic", "recyclable", "hazardous"] 
        
        # Get index of highest confidence
        prediction_index = np.argmax(output_data[0])
        
        # Safety check if index is out of bounds
        if prediction_index < len(labels):
            return labels[prediction_index]
        else:
            return "unknown"

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
