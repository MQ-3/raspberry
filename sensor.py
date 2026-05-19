import time
from adc import MCP3208


MQ_CHANNEL = 3          # 현재 ADC3 사용 기준
SAMPLE_COUNT = 10
SAMPLE_DELAY = 0.05


adc = MCP3208()


def get_raw_value(channel: int = MQ_CHANNEL) -> int:
    return adc.read_channel(channel)


def get_average_value(channel: int = MQ_CHANNEL, sample_count: int = SAMPLE_COUNT) -> float:
    values = []
    for _ in range(sample_count):
        values.append(adc.read_channel(channel))
        time.sleep(SAMPLE_DELAY)
    return sum(values) / len(values)


def get_sensor_data(channel: int = MQ_CHANNEL) -> dict:
    raw = get_raw_value(channel)
    avg = get_average_value(channel)
    return {
        "raw": raw,
        "avg": round(avg, 2)
    }
