import time
from dataclasses import dataclass

try:
    import RPi.GPIO as GPIO
except ImportError:  # for development on non‑Pi
    GPIO = None

@dataclass
class UltrasonicSensor:
    trigger_pin: int
    echo_pin: int

    def __post_init__(self):
        if GPIO is None:
            return
        GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trigger_pin, False)

    def read_distance_cm(self) -> float:
        if GPIO is None:
            # mock value for development
            return 100.0

        # trigger pulse
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)

        start_time = time.time()
        stop_time = time.time()

        # wait for echo start
        while GPIO.input(self.echo_pin) == 0:
            start_time = time.time()

        # wait for echo end
        while GPIO.input(self.echo_pin) == 1:
            stop_time = time.time()

        elapsed = stop_time - start_time
        distance = (elapsed * 34300) / 2.0  # cm
        return distance