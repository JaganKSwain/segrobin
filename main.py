import time
import signal
import sys

from config import (
    BROKER_HOST,
    BROKER_PORT,
    MQTT_TOPIC_STATUS,
    MQTT_TOPIC_FILLLEVEL,
    MQTT_CLIENT_ID,
    ULTRASONIC_1_TRIGGER,
    ULTRASONIC_1_ECHO,
    ULTRASONIC_3_TRIGGER,
    ULTRASONIC_3_ECHO,
    ULTRASONIC_4_TRIGGER,
    ULTRASONIC_4_ECHO,
    SERVO_1_PIN,
    SERVO_2_PIN,
    LED_RED_PIN,
    BUZZER_PIN,
    DIST_THRESHOLD_OBJECT_CM,
    DIST_THRESHOLD_BIN_FULL_CM,
    LOAD_THRESHOLD_FULL,
    CAMERA_INDEX,
    MODEL_PATH,
)

from hardware.ultrasonic import UltrasonicSensor
from hardware.servo import Servo
from hardware.loadcell import LoadCell
from hardware.indicators import Indicators
from hardware.camera_ml import CameraML
from comms.mqtt_client import SegrobinMQTT

RUNNING = True


def handle_sigint(sig, frame):
    global RUNNING
    RUNNING = False


signal.signal(signal.SIGINT, handle_sigint)


def main():
    us_inlet = UltrasonicSensor(ULTRASONIC_1_TRIGGER, ULTRASONIC_1_ECHO)
    us_bin_1 = UltrasonicSensor(ULTRASONIC_3_TRIGGER, ULTRASONIC_3_ECHO)
    us_bin_2 = UltrasonicSensor(ULTRASONIC_4_TRIGGER, ULTRASONIC_4_ECHO)

    servo_position = Servo(SERVO_1_PIN)   # decides which bin
    servo_flap = Servo(SERVO_2_PIN)       # flips flap

    load_cell = LoadCell()
    indicators = Indicators(LED_RED_PIN, BUZZER_PIN)
    camera_ml = CameraML(CAMERA_INDEX, MODEL_PATH)

    mqtt_client = SegrobinMQTT(BROKER_HOST, BROKER_PORT, MQTT_CLIENT_ID)

    try:
        while RUNNING:
            # 1. inlet ultrasonic detects object
            dist_obj = us_inlet.read_distance_cm()
            if 0 < dist_obj < DIST_THRESHOLD_OBJECT_CM:
                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "object_detected",
                    "distance_cm": dist_obj,
                })

                # 2. camera + ML classify object
                label = camera_ml.classify_object()
                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "object_classified",
                    "label": label,
                })

                # 3. move servo-1 to bin based on label
                if label == "plastic":
                    servo_position.set_angle(0)
                    target_bin = "bin_plastic"
                elif label == "metal":
                    servo_position.set_angle(90)
                    target_bin = "bin_metal"
                else:
                    servo_position.set_angle(180)
                    target_bin = "bin_other"

                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "servo1_positioned",
                    "target_bin": target_bin,
                })

                # 4. servo-2 flips flap to drop object
                servo_flap.set_angle(90)
                time.sleep(1.0)
                servo_flap.set_angle(0)

                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "flap_flipped",
                    "target_bin": target_bin,
                })

                # 5. ultrasonic 3 & 4 check fill coverage
                dist_bin_1 = us_bin_1.read_distance_cm()
                dist_bin_2 = us_bin_2.read_distance_cm()
                mqtt_client.publish_status(MQTT_TOPIC_FILLLEVEL, {
                    "bin_1_distance_cm": dist_bin_1,
                    "bin_2_distance_cm": dist_bin_2,
                })

                # 6. load cell checks weight
                weight = load_cell.read_weight()
                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "load_checked",
                    "weight": weight,
                })

                bin_full_ultra = (
                    dist_bin_1 < DIST_THRESHOLD_BIN_FULL_CM
                    or dist_bin_2 < DIST_THRESHOLD_BIN_FULL_CM
                )
                bin_full_load = weight >= LOAD_THRESHOLD_FULL
                any_full = bin_full_ultra or bin_full_load

                if any_full:
                    # 7. bin full: stop, LED red, buzzer
                    indicators.led_red_on()
                    indicators.beep(2.0)
                    mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                        "event": "bin_full",
                        "bin_full_ultra": bin_full_ultra,
                        "bin_full_load": bin_full_load,
                    })
                    # wait until manually stopped
                    while RUNNING:
                        time.sleep(1.0)
                else:
                    # 8. not full: wait 10 s and repeat
                    mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                        "event": "bin_not_full",
                        "next_cycle_in_sec": 10,
                    })
                    time.sleep(10.0)
            else:
                time.sleep(0.2)

    finally:
        camera_ml.release()
        mqtt_client.stop()
        servo_position.cleanup()
        servo_flap.cleanup()
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except ImportError:
            pass


if __name__ == "__main__":
    main()
    