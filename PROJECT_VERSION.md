# Project Version Boundary

작성 기준일: 2026-06-28

## 현재 프로젝트

```text
Name: market-dashboard
Version role: 1.0 reference package
Repository: https://github.com/lifeispf/market-dashboard
Primary branch: master
```

## 역할

이 repo는 `investrader` 2.0을 새로 설계하고 구현하기 위한 1.0 reference package다.

1.0은 다음 목적으로 유지한다.

- 기존 동작 확인.
- market/sector/stock 판단 로직 참고.
- Cloudflare KV + GitHub Actions 운영 경험 참고.
- 2.0 구현 결과와 비교할 oracle.
- 2.0으로 옮길 기능과 버릴 기능을 판단하는 실험실.

## 경계

`investrader` 2.0의 새 코드와 새 아키텍처 구현은 이 repo에 섞지 않는다.

허용:

- 1.0 버그 수정.
- 1.0 문서 정리.
- 2.0 설계를 위한 reference 문서.
- 1.0 동작을 고정하는 contract test.

비허용:

- 2.0 production code 추가.
- 자동매매 실행 계층을 1.0에 직접 추가.
- 2.0 아키텍처를 1.0 코드에 대규모로 이식.
- 1.0과 2.0이 같은 runtime path를 공유하도록 만드는 변경.

## 2.0 프로젝트명

```text
investrader
```

2.0은 별도 repo로 시작하는 것을 권장한다.
