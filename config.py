import os
from dotenv import load_dotenv

load_dotenv()

# Flask
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "sulchingu")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

# Sensor
USE_MOCK_SENSOR = os.getenv("USE_MOCK_SENSOR", "true").lower() == "true"
# 백그라운드 상시 측정 루프(spike 자동감지/api/status). 프론트가 /api/measure만
# 쓰면 불필요하며, 같은 SPI 장치를 동시 점유해 측정값을 깨뜨릴 수 있어 기본 off.
ENABLE_SENSOR_LOOP = os.getenv("ENABLE_SENSOR_LOOP", "false").lower() == "true"
SENSOR_CHANNEL = int(os.getenv("SENSOR_CHANNEL", 2))
SENSOR_SAMPLE_DELAY = float(os.getenv("SENSOR_SAMPLE_DELAY", 0.05))
SENSOR_LOOP_INTERVAL = float(os.getenv("SENSOR_LOOP_INTERVAL", 0.1))
BASELINE_DURATION = int(os.getenv("BASELINE_DURATION", 3))
BLOW_DURATION = int(os.getenv("BLOW_DURATION", 4))
STABILIZE_DURATION = int(os.getenv("STABILIZE_DURATION", 3))

# State thresholds
# 1) 상승폭(delta = peak - baseline) 기준 — MQ3 baseline 드리프트에 강함
CAUTION_DELTA = int(os.getenv("CAUTION_DELTA", 400))   # delta >= 이 값이면 caution
DANGER_DELTA = int(os.getenv("DANGER_DELTA", 1500))    # delta >= 이 값이면 danger
# 2) 포화 override — 불기 전부터 센서가 이미 높으면(만취) delta 와 무관하게 danger
SATURATION_VALUE = int(os.getenv("SATURATION_VALUE", 3000))
# 3) baseline 을 모를 때(자동감지 등) 쓰는 절대값 fallback
SAFE_MAX_VALUE = int(os.getenv("SAFE_MAX_VALUE", 1200))
DANGER_MIN_VALUE = int(os.getenv("DANGER_MIN_VALUE", 2400))
