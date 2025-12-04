import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


class Servo:
    def __init__(self, pin: int, min_duty: float = 2.5, max_duty: float = 12.5):
        self.pin = pin
        self.min_duty = min_duty
        self.max_duty = max_duty
        self.pwm = None

        if GPIO is not None:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            self.pwm = GPIO.PWM(self.pin, 50)
            self.pwm.start(0)

    def _angle_to_duty(self, angle: float) -> float:
        return self.min_duty + (self.max_duty - self.min_duty) * (angle / 180.0)

    def set_angle(self, angle: float):
        if GPIO is None or self.pwm is None:
            return
        duty = self._angle_to_duty(angle)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(0.4)
        self.pwm.ChangeDutyCycle(0)

    def cleanup(self):
        if GPIO is not None and self.pwm is not None:
            self.pwm.stop()