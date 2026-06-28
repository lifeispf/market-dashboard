# 1.0 Reference Release Checklist

작성 기준일: 2026-06-28

## 목적

`market-dashboard`를 `investrader` 2.0과 섞이지 않는 1.0 reference package로 봉인하기 위한 실제 작업 체크리스트다.

## Release 목표

```text
Release name: v1.0-reference
Role: 2.0 설계/구현의 비교 기준
Scope: 현재 market-dashboard 기능과 운영 경험 보존
```

## Release 전 정리

```text
[ ] 현재 미커밋 변경을 분류한다.
[ ] 1.0 유지보수 코드 변경과 문서 변경을 분리한다.
[ ] 생성물(`dashboard.db`, `kv_payloads.json`)이 커밋되지 않는지 확인한다.
[ ] `docs/1.0/*` 문서가 최신인지 확인한다.
[ ] `docs/investrader/*` 문서가 2.0 code를 포함하지 않는지 확인한다.
```

## 테스트

최소 테스트:

```powershell
python -m unittest discover engine/tests
```

권장 테스트:

```powershell
python scripts/generate_payloads.py --out kv_payloads.json
cd frontend
npm.cmd run build
```

주의:

- `kv_payloads.json`은 생성물이며 커밋하지 않는다.
- `dashboard.db`도 생성물이며 커밋하지 않는다.

## Git 봉인 옵션

### Option A: tag

현재 `master`를 1.0 reference로 봉인한다.

```powershell
git tag v1.0-reference
git push origin v1.0-reference
```

장점:

- 가장 단순하다.
- 1.0 기준점을 명확히 찍는다.

단점:

- 이후 1.0 유지보수 흐름을 별도로 관리하려면 branch가 추가로 필요하다.

### Option B: release branch

1.0 유지보수 branch를 만든다.

```powershell
git switch -c release/1.0-reference
git push -u origin release/1.0-reference
```

장점:

- 1.0 hotfix와 문서 정리를 계속 받을 수 있다.

단점:

- branch 관리가 늘어난다.

## 권장

1. 현재 미커밋 변경을 먼저 커밋한다.
2. `release/1.0-reference` branch를 만든다.
3. 그 branch에 `v1.0-reference` tag를 찍는다.
4. `master`는 더 이상 2.0 production code를 받지 않는다.
5. `investrader`는 새 repo에서 시작한다.

## 1.0 Release Notes 초안

```text
market-dashboard v1.0-reference

Purpose:
- KOSPI/NASDAQ 시장·섹터·종목 판단 prototype.
- investrader 2.0의 reference/oracle.

Included:
- FastAPI backend.
- React/Vite dashboard.
- Python market/sector/stock engine.
- SQLite dashboard cache.
- GitHub Actions refresh workflow.
- Cloudflare KV payload generation.

Excluded:
- Actual trading execution.
- Broker API integration.
- Validated automated trading signal.
- investrader 2.0 production code.
```

## Freeze 후 운영 규칙

- 1.0은 reference와 bugfix만 허용.
- 2.0 구현은 별도 repo `investrader`.
- 1.0과 2.0 사이 공유는 문서, 테스트 fixture, 비교 결과로만 한다.
