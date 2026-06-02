import random
import time
from dataclasses import dataclass

import config


@dataclass
class SensorReading:
    value: int        # 분류에 사용되는 peak 값
    average: float    # API 응답용 (peak와 동일)
    samples: list[int]
    source: str
    baseline: float   # 불기 전 기저값
    peak: int         # 불기 구간 최고값


def read_real_sensor():
    from adc import MCP3208

    adc = MCP3208()
    try:
        # 1단계: 기저값 측정
        baseline_samples = []
        end = time.time() + config.BASELINE_DURATION
        while time.time() < end:
            baseline_samples.append(adc.read_channel(config.SENSOR_CHANNEL))
            time.sleep(config.SENSOR_SAMPLE_DELAY)
        baseline = sum(baseline_samples) / len(baseline_samples)

        # 2단계: 불기 구간 - peak 캡처
        blow_samples = []
        peak = baseline
        end = time.time() + config.BLOW_DURATION
        while time.time() < end:
            val = adc.read_channel(config.SENSOR_CHANNEL)
            blow_samples.append(val)
            if val > peak:
                peak = val
            time.sleep(config.SENSOR_SAMPLE_DELAY)

        # 3단계: 안정화 (측정만, 결과에 미반영)
        end = time.time() + config.STABILIZE_DURATION
        while time.time() < end:
            adc.read_channel(config.SENSOR_CHANNEL)
            time.sleep(config.SENSOR_SAMPLE_DELAY)

        peak = round(peak)
        return SensorReading(
            value=peak,
            average=float(peak),
            samples=blow_samples,
            source="real",
            baseline=round(baseline, 1),
            peak=peak,
        )
    finally:
        adc.close()


def read_mock_sensor():
    baseline = random.uniform(900, 1100)
    time.sleep(config.BASELINE_DURATION)

    samples = []
    peak = baseline
    end = time.time() + config.BLOW_DURATION
    while time.time() < end:
        val = random.uniform(baseline * 1.5, baseline * 3.5)
        samples.append(round(val))
        if val > peak:
            peak = val
        time.sleep(config.SENSOR_SAMPLE_DELAY)

    time.sleep(config.STABILIZE_DURATION)

    peak = round(peak)
    return SensorReading(
        value=peak,
        average=float(peak),
        samples=samples,
        source="mock",
        baseline=round(baseline, 1),
        peak=peak,
    )


def read_sensor():
    if config.USE_MOCK_SENSOR:
        return read_mock_sensor()
    return read_real_sensor()
