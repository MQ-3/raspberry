import random
import time
from dataclasses import dataclass

import config


MOCK_MIN_VALUE = 300
MOCK_MAX_VALUE = 3500


@dataclass
class SensorReading:
    value: int
    average: float
    samples: list[int]
    source: str


def read_real_sensor():
    from adc import MCP3208

    adc = MCP3208()
    try:
        samples = []
        for _ in range(config.SENSOR_SAMPLE_COUNT):
            samples.append(adc.read_channel(config.SENSOR_CHANNEL))
            time.sleep(config.SENSOR_SAMPLE_DELAY)

        average = sum(samples) / len(samples)
        return SensorReading(
            value=round(average),
            average=average,
            samples=samples,
            source="real",
        )
    finally:
        adc.close()


def read_mock_sensor():
    samples = []
    for _ in range(config.SENSOR_SAMPLE_COUNT):
        samples.append(random.randint(MOCK_MIN_VALUE, MOCK_MAX_VALUE))
        time.sleep(config.SENSOR_SAMPLE_DELAY)

    average = sum(samples) / len(samples)
    return SensorReading(
        value=round(average),
        average=average,
        samples=samples,
        source="mock",
    )


def read_sensor():
    if config.USE_MOCK_SENSOR:
        return read_mock_sensor()
    return read_real_sensor()
