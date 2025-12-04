import json
from dataclasses import dataclass

import paho.mqtt.client as mqtt  # MQTT client library[web:40][web:41]


@dataclass
class SegrobinMQTT:
    broker_host: str
    broker_port: int
    client_id: str

    def __post_init__(self):
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()

    def publish_status(self, topic: str, payload: dict):
        msg = json.dumps(payload)
        self.client.publish(topic, msg, qos=1, retain=False)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()