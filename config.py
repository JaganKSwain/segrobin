BROKER_HOST = "localhost"
BROKER_PORT = 1883
MQTT_TOPIC_STATUS = "segrobin/status"
MQTT_TOPIC_FILLLEVEL = "segrobin/fill_level"
MQTT_CLIENT_ID = "segrobin_controller"

# GPIO pins (change to match your wiring)
ULTRASONIC_1_TRIGGER = 5
ULTRASONIC_1_ECHO = 6

ULTRASONIC_3_TRIGGER = 13
ULTRASONIC_3_ECHO = 19

ULTRASONIC_4_TRIGGER = 26
ULTRASONIC_4_ECHO = 21

SERVO_1_PIN = 17
SERVO_2_PIN = 27

LED_RED_PIN = 22
BUZZER_PIN = 23

# Thresholds
DIST_THRESHOLD_OBJECT_CM = 20.0      # object at inlet
DIST_THRESHOLD_BIN_FULL_CM = 5.0     # distance meaning bin is full
LOAD_THRESHOLD_FULL = 5.0            # kg or calibrated units

# Camera / ML
CAMERA_INDEX = 0                     # kept for compatibility, unused by Picamera2
MODEL_PATH = "model.onnx"            # path to your ML model