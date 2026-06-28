# 1.0 Commit Plan

작성 기준일: 2026-06-28

## 목적

현재 worktree에는 1.0 reference packaging 문서 변경과 NASDAQ OHLC 기능 변경이 함께 존재한다. 1.0을 깔끔하게 봉인하려면 두 변경을 별도 커밋으로 분리해야 한다.

## 변경분 분류

### A. 1.0 reference packaging 문서

포함:

- `README.md`
- `PROJECT_VERSION.md`
- `docs/**`

성격:

- 1.0 reference package 선언.
- `investrader` 2.0 handoff와 bootstrap 계획.
- 현재 구현 인벤토리, 9단계 로드맵, 모듈 문서.
- 운영/배포/검증/테스트 문서.

권장 커밋:

```text
docs(1.0): package market-dashboard as investrader reference
```

### B. NASDAQ OHLC snapshot 기능 변경

포함:

- `.github/workflows/refresh-payloads.yml`
- `backend/store/db.py`
- `backend/store/ingest.py`
- `data/us_fetcher.py`
- `scripts/generate_payloads.py`
- `engine/tests/test_ohlc_storage.py`

성격:

- `series_ohlc_daily` 추가.
- NASDAQ `^IXIC` open/close phase snapshot.
- GitHub Actions schedule별 `MARKET_SNAPSHOT_PHASE`.
- OHLC open/close 누적 테스트.

권장 커밋:

```text
feat(data): capture Nasdaq OHLC open and close snapshots
```

### C. 기존 별도 untracked 항목

포함:

- `증시 예측/AGENTS.md`

성격:

- 이번 1.0 packaging/release 작업과 무관.
- stage하지 않는다.

## 권장 순서

1. 문서 링크와 기본 테스트를 확인한다.
2. A만 stage하고 커밋한다.
3. B는 별도 검증 후 stage/커밋한다.
4. C는 사용자 확인 전까지 건드리지 않는다.
5. 두 커밋이 정리되면 `release/1.0-reference` branch 또는 `v1.0-reference` tag를 만든다.

## Stage 명령

문서 패키징만 stage:

```powershell
git add README.md PROJECT_VERSION.md docs
```

NASDAQ OHLC 기능 변경 stage:

```powershell
git add .github/workflows/refresh-payloads.yml backend/store/db.py backend/store/ingest.py data/us_fetcher.py scripts/generate_payloads.py engine/tests/test_ohlc_storage.py
```

## Release 후보

문서 커밋과 기능 커밋이 모두 정리된 뒤:

```powershell
git switch -c release/1.0-reference
git tag v1.0-reference
```

단, tag/branch 생성은 worktree가 정리된 뒤 수행한다.
