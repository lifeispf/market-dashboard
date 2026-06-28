# API와 KV 계약

작성 기준일: 2026-06-28

## 시장과 시간축

현재 payload generator 기준:

- Markets: `KOSPI`, `NASDAQ`
- Timeframes: `1D`, `1W`, `1M`, `1Q`, `1Y`

## KV key 형식

`scripts/generate_payloads.py`가 생성하는 key는 Cloudflare Worker의 URL to KV key mapping과 일치해야 합니다.

| KV key | 생성 함수 | 설명 |
|---|---|---|
| `market:{MARKET}:{TF}` | `get_market(m, tf)` | 시장 메인 payload |
| `sectors:{MARKET}:{TF}` | `get_sectors(m, tf)` | 섹터 payload |
| `stocks:{MARKET}:{TF}` | `get_stocks(m, tf)` | 종목 payload |
| `history:{MARKET}:{TF}` | `get_history(m, tf)` | 히스토리 payload |
| `verification:{MARKET}` | `get_verification(m)` | 검증 payload |
| `briefing:{MARKET}` | `get_briefing(m)` | cascade briefing |
| `health` | `health()` | 상태 payload |

`market:{MARKET}:{TF}` payload에는 `generatedAt`이 추가 주입됩니다. 프론트 우측 상단 갱신 시각 표시의 기준입니다.

## Endpoint 대응

로컬 FastAPI의 route와 KV key는 논리적으로 다음처럼 대응됩니다.

| 로컬 API | KV key |
|---|---|
| `/api/market/{market}?tf={tf}` | `market:{MARKET}:{TF}` |
| `/api/sectors/{market}?tf={tf}` | `sectors:{MARKET}:{TF}` |
| `/api/stocks/{market}?tf={tf}` | `stocks:{MARKET}:{TF}` |
| `/api/history/{market}?tf={tf}` | `history:{MARKET}:{TF}` |
| `/api/verification/{market}` | `verification:{MARKET}` |
| `/api/briefing/{market}` | `briefing:{MARKET}` |
| `/api/health` | `health` |

정확한 Cloudflare Worker URL route는 현재 workspace에서 확인되지 않았습니다.

## Bulk payload 형식

`kv_payloads.json`은 다음 형태의 배열입니다.

```json
[
  {
    "key": "market:KOSPI:1D",
    "value": "{\"market\":\"KOSPI\"}"
  }
]
```

`value`는 JSON 객체가 아니라 JSON 문자열입니다. 이는 `wrangler kv bulk put` 입력 형식에 맞춘 것입니다.

## 호환성 규칙

- KV key 이름을 바꾸면 Worker와 frontend mapping을 함께 바꿔야 합니다.
- `generatedAt`은 `market` payload에만 보장됩니다.
- endpoint 하나가 실패해도 generator는 전체 실행을 중단하지 않고 실패 목록을 출력합니다.
- 모든 route function은 배포 전 `db.init_db()` 이후 호출되어야 합니다.
