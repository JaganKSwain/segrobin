try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
import time

class Indicators:
    def __init__(self, led_red_pin: int, buzzer_pin: int):
        self.led_red_pin = led_red_pin
        self.buzzer_pin = buzzer_pin

        if GPIO is not None:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.led_red_pin, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            GPIO.output(self.led_red_pin, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)

    def led_red_on(self):
        if GPIO is not None:
            GPIO.output(self.led_red_pin, GPIO.HIGH)

    def led_red_off(self):
        if GPIO is not None:
            GPIO.output(self.led_red_pin, GPIO.LOW)

    def beep(self, duration: float = 1.0):
        if GPIO is not None:
            GPIO.output(self.buzzer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.buzzer_pin, GPIO.LOW)