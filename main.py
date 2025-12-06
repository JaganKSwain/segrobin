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
    ULTRASONIC_REC_TRIGGER,
    ULTRASONIC_REC_ECHO,
    ULTRASONIC_ORG_TRIGGER,
    ULTRASONIC_ORG_ECHO,
    ULTRASONIC_HAZ_TRIGGER,
    ULTRASONIC_HAZ_ECHO,
    SERVO_1_PIN,
    SERVO_2_PIN,
    LED_RED_PIN,
    BUZZER_PIN,
    DIST_THRESHOLD_OBJECT_CM,
    DIST_THRESHOLD_BIN_FULL_CM,
    LOAD_THRESHOLD_FULL_REC,
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
    us_bin_rec = UltrasonicSensor(ULTRASONIC_REC_TRIGGER, ULTRASONIC_REC_ECHO)
    us_bin_org = UltrasonicSensor(ULTRASONIC_ORG_TRIGGER, ULTRASONIC_ORG_ECHO)
    us_bin_haz = UltrasonicSensor(ULTRASONIC_HAZ_TRIGGER, ULTRASONIC_HAZ_ECHO)
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
                if label == "recyclable":
                    servo_position.set_angle(0)
                    target_bin = "recyclable"
                elif label == "organic":
                    servo_position.set_angle(120)
                    target_bin = "organic"
                elif label == "hazardous":
                    servo_position.set_angle(240)
                    target_bin = "hazardous"
                else:
                    # default: send to recyclable or a fallback bin
                    servo_position.set_angle(0)
                    target_bin = "recyclable"

                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "servo1_positioned",
                    "target_bin": target_bin,
                })

                # 4. servo-2 flips flap to drop object
                servo_flap.set_angle(45)
                time.sleep(1.0)
                servo_flap.set_angle(0)

                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "flap_flipped",
                    "target_bin": target_bin,
                })
                # 5. ultrasonic sensors check fill coverage of all three bins
                dist_rec = us_bin_rec.read_distance_cm()
                dist_org = us_bin_org.read_distance_cm()
                dist_haz = us_bin_haz.read_distance_cm()

                mqtt_client.publish_status(MQTT_TOPIC_FILLLEVEL, {
                    "recyclable_distance_cm": dist_rec,
                    "organic_distance_cm": dist_org,
                    "hazardous_distance_cm": dist_haz,
                })

                # 6. load cell under recyclable bin only
                weight_rec = load_cell.read_weight()
                mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                    "event": "recyclable_weight_checked",
                    "weight_recyclable": weight_rec,
                })

                # bin-full decisions
                rec_full_ultra = dist_rec < DIST_THRESHOLD_BIN_FULL_CM
                org_full_ultra = dist_org < DIST_THRESHOLD_BIN_FULL_CM
                haz_full_ultra = dist_haz < DIST_THRESHOLD_BIN_FULL_CM

                rec_full_load = weight_rec >= LOAD_THRESHOLD_FULL_REC

                rec_full = rec_full_ultra or rec_full_load
                org_full = org_full_ultra
                haz_full = haz_full_ultra

                any_full = rec_full or org_full or haz_full

                if any_full:
                    # 7. at least one bin is full
                    indicators.led_red_on()
                    indicators.beep(2.0)
                    mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                        "event": "bin_full",
                        "recyclable_full": rec_full,
                        "organic_full": org_full,
                        "hazardous_full": haz_full,
                        "recyclable_weight": weight_rec,
                    })
                    while RUNNING:
                        time.sleep(1.0)
                else:
                    # 8. none are full: wait 10 s and continue
                    mqtt_client.publish_status(MQTT_TOPIC_STATUS, {
                        "event": "bins_not_full",
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
    