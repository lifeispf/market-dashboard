# 1.0 Freeze Policy

작성 기준일: 2026-06-28

## 목적

`market-dashboard` 1.0을 `investrader` 2.0과 섞이지 않도록 관리한다.

## 기본 원칙

1. 1.0은 reference package다.
2. 2.0 production code는 별도 repo에서 시작한다.
3. 1.0에는 유지보수, 문서, contract test, 비교 oracle 목적의 변경만 허용한다.
4. 1.0에 자동매매 실행 계층을 붙이지 않는다.

## 허용 변경

| 변경 | 허용 여부 |
|---|---|
| 문서 정리 | 허용 |
| 1.0 버그 수정 | 허용 |
| 1.0 API contract test | 허용 |
| Cloudflare/GitHub Actions 운영 안정화 | 허용 |
| 2.0 설계 참고 문서 | 허용 |
| 2.0 production module 구현 | 비허용 |
| broker/order execution 구현 | 비허용 |
| 1.0 runtime을 2.0 runtime으로 변경 | 비허용 |

## 권장 Git 경계

현재 미커밋 변경을 정리한 뒤 다음 중 하나를 수행한다.

Option A: tag.

```powershell
git tag v1.0-reference
git push origin v1.0-reference
```

Option B: branch.

```powershell
git switch -c release/1.0-reference
git push -u origin release/1.0-reference
```

권장:

- 현재 repo는 `market-dashboard` 이름으로 1.0 reference 유지.
- 새 repo는 `investrader` 이름으로 생성.

## Commit 정책

1.0 repo의 커밋 타입은 다음처럼 제한한다.

```text
docs(1.0): ...
fix(1.0): ...
test(contract): ...
ops(1.0): ...
```

2.0 코드는 이 repo에 커밋하지 않는다.

## Freeze 전 체크리스트

```text
[ ] README가 1.0 reference임을 명시한다.
[ ] docs/1.0 package manifest가 있다.
[ ] 현재 미커밋 변경을 정리한다.
[ ] 기본 테스트를 실행한다.
[ ] tag 또는 branch를 만든다.
[ ] investrader 새 repo 생성 여부를 결정한다.
```
