BROKER_HOST = "f7560ba925b44aefa8ab6e85a541709b.s1.eu.hivemq.cloud"
BROKER_PORT = 8883
MQTT_TOPIC_STATUS = "segrobin/status"
MQTT_TOPIC_FILLLEVEL = "segrobin/fill_level"
MQTT_CLIENT_ID = "segrobin_controller"
MQTT_USERNAME = "segrobin"
MQTT_PASSWORD = "Poiuy@2005trewq"
MQTT_USE_TLS = True

# GPIO pins (change to match your wiring)
ULTRASONIC_1_TRIGGER = 5     # inlet
ULTRASONIC_1_ECHO = 6

ULTRASONIC_REC_TRIGGER = 13  # bin 1: recyclable
ULTRASONIC_REC_ECHO = 19

ULTRASONIC_ORG_TRIGGER = 26  # bin 2: organic
ULTRASONIC_ORG_ECHO = 21

ULTRASONIC_HAZ_TRIGGER = 20  # bin 3: hazardous (choose free pins)
ULTRASONIC_HAZ_ECHO = 16

SERVO_1_PIN = 17
SERVO_2_PIN = 27

LED_RED_PIN = 22
BUZZER_PIN = 23

DIST_THRESHOLD_OBJECT_CM = 20.0
DIST_THRESHOLD_BIN_FULL_CM = 5.0

# Load cell: only recyclable bin weight is monitored
LOAD_THRESHOLD_FULL_REC = 5.0    # kg or your units

# Camera / ML
# Camera / ML
CAMERA_INDEX = 0                     # kept for compatibility, unused by Picamera2
MODEL_PATH = "best_float32.tflite"   # path to your ML model
