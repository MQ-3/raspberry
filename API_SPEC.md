# 스마트 혼술 케어 시스템 API 명세

이 문서는 Flask 백엔드와 프론트엔드 연동을 위한 API 명세입니다.

이 시스템은 MQ-3 센서의 상대적인 알코올 반응값을 기반으로 상태를 추정합니다. 의료기기 수준의 혈중알코올농도 측정값을 제공하지 않습니다.

## 서버 정보

기본 주소:

```text
http://192.168.30.7:5000  # 7은 바뀔 수 있음(network에서 확인)
```

로컬 테스트:

```text
http://127.0.0.1:5000
```

응답 형식은 모두 JSON입니다.

성공 응답은 기본적으로 다음 필드를 포함합니다.

```json
{
  "success": true
}
```

실패 응답은 다음 형식입니다.

```json
{
  "success": false,
  "message": "error message"
}
```

## 상태값 기준

상태 단계는 3단계입니다.

| level | label | 설명 | 색상 |
| --- | --- | --- | --- |
| safe | 안정 단계 | 현재는 안정적인 상태로 추정 | green |
| caution | 주의 단계 | 알코올 반응 감지 | yellow |
| danger | 과음 주의 단계 | 높은 알코올 반응 감지 | red |

초기 임계값은 `config.py`에서 수정합니다.

```python
SAFE_MAX_VALUE = 1200
DANGER_MIN_VALUE = 2400
```

판별 기준:

```text
value < SAFE_MAX_VALUE                 -> safe
SAFE_MAX_VALUE <= value < DANGER_MIN_VALUE -> caution
value >= DANGER_MIN_VALUE              -> danger
```

## 1. 서버 상태 확인

### GET `/api/health`

서버가 실행 중인지 확인합니다.

요청 body 없음.

응답 예시:

```json
{
  "success": true,
  "message": "server is running"
}
```

## 2. DB 테이블 초기화

### POST `/api/db/init`

`drink_logs`, `shorts` 테이블을 생성하고 초기 숏츠 데이터를 넣습니다.

요청 body 없음.

응답 예시:

```json
{
  "success": true,
  "message": "database tables are ready"
}
```

## 3. 센서 측정

### POST `/api/measure`

mock 센서값 또는 실제 MQ-3 센서값을 읽고 상태를 판별합니다.

현재 개발 단계에서는 `config.py`의 `USE_MOCK_SENSOR = True`이면 mock 값이 반환됩니다.

요청 body 없음.

응답 예시:

```json
{
  "success": true,
  "sensor_value": 1840,
  "source": "mock",
  "samples": [1780, 1901, 1812, 1850],
  "average": 1840.2,
  "state": {
    "level": "caution",
    "label": "주의 단계",
    "message": "알코올 반응이 감지되고 있습니다. 천천히 마시는 것을 권장합니다."
  }
}
```

필드 설명:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| sensor_value | number | 최종 판별에 사용한 센서값 |
| source | string | `mock` 또는 `real` |
| samples | number[] | 여러 번 측정한 샘플값 |
| average | number | 샘플 평균값 |
| state | object | 상태 판별 결과 |

## 4. 음주 기록 저장

### POST `/api/logs`

측정값과 술 종류, 술 양, 메모를 DB에 저장합니다.

요청 예시:

```json
{
  "sensor_value": 1840,
  "state_level": "caution",
  "state_label": "주의 단계",
  "state_message": "알코올 반응이 감지되고 있습니다. 천천히 마시는 것을 권장합니다.",
  "drink_type": "맥주",
  "drink_amount": 500,
  "drink_unit": "ml",
  "memo": "저녁 혼술"
}
```

필수 필드:

```text
sensor_value
state_level
state_label
```

응답 예시:

```json
{
  "success": true,
  "message": "log saved",
  "id": 1
}
```

## 5. 오늘 기록 조회

### GET `/api/logs/today`

오늘 저장된 측정 기록을 시간순으로 반환합니다.

응답 예시:

```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "measured_at": "2026-05-19 21:10:00",
      "sensor_value": 1840,
      "state_level": "caution",
      "state_label": "주의 단계",
      "state_message": "알코올 반응이 감지되고 있습니다. 천천히 마시는 것을 권장합니다.",
      "drink_type": "맥주",
      "drink_amount": 500,
      "drink_unit": "ml",
      "memo": "저녁 혼술"
    }
  ]
}
```

## 6. 이번 주 기록 요약

### GET `/api/logs/week`

이번 주 월요일부터 일요일까지 날짜별 대표 상태를 반환합니다.

하루에 여러 기록이 있으면 가장 높은 상태가 대표 상태가 됩니다.

상태 우선순위:

```text
safe = 1
caution = 2
danger = 3
```

응답 예시:

```json
{
  "success": true,
  "start_date": "2026-05-18",
  "end_date": "2026-05-24",
  "days": [
    {
      "date": "2026-05-19",
      "state_level": "caution",
      "color": "yellow",
      "max_value": 1840
    }
  ]
}
```

## 7. 이번 달 달력 데이터

### GET `/api/calendar/month`

이번 달 날짜별 대표 상태를 반환합니다.

요청 예시:

```text
GET /api/calendar/month
```

특정 월 조회:

```text
GET /api/calendar/month?year=2026&month=5
```

응답 예시:

```json
{
  "success": true,
  "year": 2026,
  "month": 5,
  "days": [
    {
      "date": "2026-05-19",
      "state_level": "caution",
      "color": "yellow",
      "max_value": 1840
    }
  ]
}
```

프론트 달력 색상 기준:

| 상태 | color |
| --- | --- |
| 기록 없음 | gray |
| safe | green |
| caution | yellow |
| danger | red |

## 8. AI 숏츠 목록 조회

### GET `/api/shorts`

숏츠 영상 목록과 잠금 상태를 반환합니다.

응답 예시:

```json
{
  "success": true,
  "shorts": [
    {
      "episode_no": 1,
      "title": "EP.1 비밀 계약의 시작",
      "video_path": "/static/videos/ep1.mp4",
      "is_unlocked": true,
      "unlocked_at": "2026-05-19 21:10:00"
    },
    {
      "episode_no": 2,
      "title": "EP.2 유전자 검사 결과",
      "video_path": "/static/videos/ep2.mp4",
      "is_unlocked": false,
      "unlocked_at": null
    }
  ]
}
```

초기 상태:

```text
EP.1 unlocked
EP.2 locked
EP.3 locked
```

## 9. AI 숏츠 잠금해제

### POST `/api/shorts/unlock`

술친구 체크인을 수행합니다.

동작 순서:

1. 센서 측정
2. 상태 판별
3. 측정 기록 저장
4. 상태가 `safe` 또는 `caution`이면 다음 잠긴 숏츠 1개 잠금해제
5. 상태가 `danger`이면 잠금 유지

요청 body 없음.

safe 또는 caution 응답 예시:

```json
{
  "success": true,
  "sensor_value": 950,
  "state": {
    "level": "safe",
    "label": "안정 단계",
    "message": "현재는 안정적인 상태로 보입니다."
  },
  "unlocked": true,
  "episode": {
    "episode_no": 2,
    "title": "EP.2 유전자 검사 결과",
    "video_path": "/static/videos/ep2.mp4"
  },
  "message": "다음 숏츠가 잠금해제되었습니다."
}
```

danger 응답 예시:

```json
{
  "success": true,
  "sensor_value": 2800,
  "state": {
    "level": "danger",
    "label": "과음 주의 단계",
    "message": "알코올 반응이 높게 감지되었습니다. 물을 마시고 잠시 휴식하세요."
  },
  "unlocked": false,
  "episode": null,
  "message": "지금은 쉬어갈 타이밍입니다. 다음 숏츠는 잠시 후 확인해주세요."
}
```

이미 모든 숏츠가 잠금해제된 경우:

```json
{
  "success": true,
  "sensor_value": 900,
  "state": {
    "level": "safe",
    "label": "안정 단계",
    "message": "현재는 안정적인 상태로 보입니다."
  },
  "unlocked": false,
  "episode": null,
  "message": "이미 모든 숏츠가 잠금해제되었습니다."
}
```

## 프론트엔드 연동 권장 흐름

### 대시보드 첫 진입

```text
GET /api/health
GET /api/shorts
GET /api/logs/today
GET /api/calendar/month
```

### 측정하기 버튼

```text
POST /api/measure
```

사용자가 술 종류/양/메모를 입력한 뒤:

```text
POST /api/logs
```

### 술친구 체크인 버튼

```text
POST /api/shorts/unlock
GET /api/shorts
GET /api/logs/today
GET /api/calendar/month
```

## 백엔드 실행 방법

패키지 설치:

```bash
pip install -r requirements.txt
```

서버 실행:

```bash
python app.py
```

DB 테이블 생성:

```bash
python db.py
```

또는 API로 초기화:

```text
POST /api/db/init
```

## 센서 모드 전환

현재 MQ-3가 없으면 mock 모드로 둡니다.

```python
USE_MOCK_SENSOR = True
```

실제 MQ-3 연결 후:

```python
USE_MOCK_SENSOR = False
SENSOR_CHANNEL = 3
```

센서를 다른 MCP3208 채널에 연결했다면 `SENSOR_CHANNEL` 값을 바꿔야 합니다.
