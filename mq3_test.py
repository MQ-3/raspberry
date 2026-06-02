import spidev
import time


SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 1_000_000

MQ3_CHANNEL = 2   # MQ-3 AO를 MCP3208 CH2에 연결한 경우
SAMPLE_COUNT = 10
SAMPLE_DELAY = 0.05

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = SPI_SPEED_HZ


def read_channel(channel: int) -> int:
    """MCP3208 단일 채널(0~7) 값을 읽어서 0~4095 정수로 반환."""
    if not 0 <= channel <= 7:
        raise ValueError("channel must be between 0 and 7")

    cmd1 = 0b00000110 | ((channel & 0b100) >> 2)
    cmd2 = (channel & 0b011) << 6

    result = spi.xfer2([cmd1, cmd2, 0])
    value = ((result[1] & 0x0F) << 8) | result[2]
    return value

def measure_baseline(channel: int, duration: int = 3) -> float:
    samples = []
    end = time.time() + duration
    while time.time() < end:
        samples.append(read_channel(channel))
        time.sleep(SAMPLE_DELAY)
    return sum(samples) / len(samples)


def classify(value: float, baseline: float) -> str:
    # 기저값 대비 비율로 판단
    ratio = value / baseline
    if ratio < 1.3:
        return "안정 단계"
    elif ratio < 2.0:
        return "주의 단계"
    else:
        return "과음 단계"


try:
    print("MQ-3 테스트 시작\n")

    # 0~3초: 기본값 측정
    print("[1/3] 기본값 측정 중... (3초)")
    baseline = measure_baseline(MQ3_CHANNEL, duration=3)
    print(f"      기본값: {baseline:.1f}\n")

    # 3~7초: 불기 구간 - 최댓값 캡처
    print("[2/3] 불어주세요! (4초)")
    peak = baseline
    end = time.time() + 4
    while time.time() < end:
        val = read_channel(MQ3_CHANNEL)
        if val > peak:
            peak = val
        remaining = end - time.time()
        print(f"      RAW: {val:4d} | 남은시간: {remaining:.1f}s", end="\r")
        time.sleep(SAMPLE_DELAY)
    print(f"\n      최고값: {peak:.0f}\n")

    # 7~10초: 안정화 (측정 계속, 결과에는 반영 안 함)
    print("[3/3] 분석 중... (3초)")
    end = time.time() + 3
    while time.time() < end:
        val = read_channel(MQ3_CHANNEL)
        remaining = end - time.time()
        print(f"      RAW: {val:4d} | 남은시간: {remaining:.1f}s", end="\r")
        time.sleep(SAMPLE_DELAY)
    print()

    # 결과
    status = classify(peak, baseline)
    print(f"\n===== 결과: {status} =====")
    print(f"기본값: {baseline:.1f} | 최고값: {peak:.0f} | 비율: {peak/baseline:.2f}x")

except KeyboardInterrupt:
    print("\n테스트 종료")

finally:
    spi.close()
