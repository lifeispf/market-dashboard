"""Frozen-contract MOCK payloads (Track 0).

These return the EXACT shape of GET /api/market/{market}, populated with the values
from planning/market-dashboard-prototype.jsx so the contract is executable and the
frontend (Track B) can develop against a live endpoint immediately.

Track A replaces api/market.py internals with real assembly from scoring.py/data/*;
the SHAPE returned here must not change without updating frontend/src/api/types.ts.
"""

_KOSPI = {
    "market": "KOSPI",
    "asOf": "2026-06-20",
    "source": "Yahoo Finance",
    "pill": "후기 강세장 · 반도체 슈퍼사이클",
    "flow": {
        "level": 9064, "chgPct": 0.8, "yoyPct": 199, "fwdPER": 7.5, "trailingPER": 11.2,
        "breadthText": "상승 197 · 하락 673", "breadthNote": "반도체·전력·증권 중심 압축 상승",
        "volLabel": "VKOSPI(근사)", "volValue": 19.4, "volDir": "down",
        "spark": [58, 60, 59, 63, 66, 65, 70, 75, 79, 77, 85, 90, 88, 95, 100],
    },
    "bands": {
        "base": {"lo": 10500, "hi": 11000}, "bull": {"lo": 12000, "hi": 13000},
        "hyper": {"lo": 14000, "hi": 16000}, "hyperOpen": True,
    },
    "regime": {"composite": 44, "label": "BULL 도달가능", "nAvailable": 6, "nTotal": 6},
    "fearGreed": {
        "score": 68, "label": "Greed", "nAvailable": 4, "nTotal": 6,
        "factors": [
            {"id": "F1", "name": "모멘텀", "value": 0.06, "score": 75},
            {"id": "F2", "name": "강도", "value": 0.41, "score": 55},
            {"id": "F3", "name": "변동성", "value": 19.4, "score": 70},
            {"id": "F4", "name": "신용", "value": 3.4, "score": 72},
        ],
    },
    "reconciliation": {
        "state": "slack", "symbol": "🟡", "label": "여유",
        "supportedCeiling": 12500, "priceBand": "base", "distancePct": 38,
    },
    "sources": [
        {"id": "S01", "name": "중앙은행 정책", "scope": "Fed · BOK", "headroom": 20, "dir": "down",
         "dirLabel": "긴축편향 · 메인 탭 거의 잠김",
         "state": "Fed 3.50–3.75% 동결, 2026 인하 dot 삭제. 한은 2.50% 동결."},
        {"id": "S02", "name": "외국인 자금", "scope": "KOSPI 한정", "headroom": 75, "dir": "up",
         "dirLabel": "저포지션 · 살 여지 큼(환율이 관건)",
         "state": "반도체 비중이 평균 대비 1.3σ 낮은 저포지션. 약한 원화가 유입 게이트."},
        {"id": "S03", "name": "국내 신용·레버리지", "scope": "KOSPI · KOSDAQ", "headroom": 30, "dir": "down",
         "dirLabel": "스트레치 · 반대매매 리스크 내재",
         "state": "개인 참여 사상 최고, 추가 상승분이 신용융자 의존."},
        {"id": "S04", "name": "美 대기자금·자사주", "scope": "글로벌 공통배경", "headroom": 60, "dir": "flat",
         "dirLabel": "규모 큼 · 고금리에 잠김",
         "state": "MMF 사상 최고 수준이나 3.5%+ 금리에 묶여 회전 지연."},
        {"id": "S05", "name": "원/달러 환율", "scope": "증폭기 / 게이트", "headroom": 25, "dir": "down",
         "dirLabel": "약세가 외인 유입 발목(이익엔 +)",
         "state": "1,475–1,558 레인지 약세. 외인 유입은 억제하나 수출이익은 부풀림."},
        {"id": "S06", "name": "글로벌 신용·금융환경", "scope": "공통 배경", "headroom": 55, "dir": "flat",
         "dirLabel": "완화적이나 후기국면 · 반전 취약",
         "state": "HY OAS 타이트, 위험자본 조달 원활. 스프레드 반전 시 멀티플 전제 붕괴."},
    ],
    "sectors": [
        {"code": "semi", "name": "반도체", "marketCap": 4.29e15, "ytd": 158, "rsRatio": 99.6,
         "rsMomentum": 101.7, "quadrant": "improving"},
        {"code": "power", "name": "전력기기", "marketCap": 7.82e13, "ytd": 78, "rsRatio": 95.8,
         "rsMomentum": 107.3, "quadrant": "improving"},
        {"code": "auto", "name": "자동차", "marketCap": 2.75e14, "ytd": 69, "rsRatio": 90.5,
         "rsMomentum": 89.9, "quadrant": "lagging"},
    ],
    "leaders": {
        "semi": {
            "key": [
                {"ticker": "005930.KS", "name": "삼성전자", "role": "메모리·파운드리 벨웨더",
                 "price": 354000, "ytd": 120,
                 "thesis": "AI 메모리 슈퍼사이클 최대 수혜주. HBM·D램 계약가 퀀텀점프와 외국인 저포지션 정상화가 동시 작동.",
                 "stats": [["역할", "지수 최대 비중"], ["수급", "외국인 연속 순매수"]],
                 "risk": "메모리 가격 사이클 반전 · 단일 섹터 쏠림", "asOf": "2026-06-20"},
            ],
            "star": [
                {"ticker": "042700.KQ", "name": "한미반도체", "role": "HBM 패키징 본더",
                 "price": 295000, "ytd": 140,
                 "thesis": "HBM 패키징 핵심 TC본더의 사실상 독점 공급자. SK하이닉스 증설 사이클에 직결.",
                 "stats": [["역할", "HBM 본더 공급"], ["테마", "후공정 장비"]],
                 "risk": "고객사 집중 · 수주 변동성", "asOf": "2026-06-20"},
            ],
        },
    },
    "narrative": {
        "flow": "신고가권 · 반도체·전력 중심 압축 상승(breadth 쏠림)",
        "liquidity": "BULL 도달가능 (천장까지 +38%)",
        "leadership": "반도체(improving) 견인 · 전력기기 순환매 진입 후보",
        "reconciliation": "🟡 여유",
    },
    "watchlist": [
        {"label": "Fed 점도표·WALCL", "trigger": "인하 dot 부활 / 순증 전환", "meaning": "완화 = hyper 연료 점화", "status": "quiet"},
        {"label": "외국인 일별 순매수", "trigger": "3일 연속 순매도", "meaning": "한계매수자 이탈", "status": "quiet"},
        {"label": "신용융자·반대매매", "trigger": "잔고 급증 후 반대매매", "meaning": "hyper 붕괴 임계", "status": "quiet"},
        {"label": "USD/KRW", "trigger": "1,500 하회", "meaning": "외인 게이트 개방", "status": "manual_check"},
        {"label": "HY OAS·VIX", "trigger": "스프레드 확대 + 변동성 레짐 전환", "meaning": "멀티플 전제 붕괴", "status": "quiet"},
        {"label": "breadth", "trigger": "신고가에도 음수 지속", "meaning": "집중심화·후기국면", "status": "manual_check"},
    ],
    "freshness": [
        {"label": "KOSPI 지수", "source": "Yahoo", "freq": "daily", "last": "2026-06-20", "stale": False},
        {"label": "Fed 금리·대차대조표", "source": "FRED", "freq": "weekly", "last": "2026-06-19", "stale": False},
        {"label": "외국인 순매매", "source": "KRX", "freq": "daily", "last": "2026-06-19", "stale": False},
        {"label": "선행 EPS(컨센서스)", "source": "manual", "freq": "quarterly", "last": "2026-04-15", "stale": False},
        {"label": "섹터 key/star 테제", "source": "manual", "freq": "quarterly", "last": "2026-06-20", "stale": False},
    ],
}

_NASDAQ = {
    "market": "NASDAQ",
    "asOf": "2026-06-18",
    "source": "Yahoo Finance",
    "pill": "후기 강세장 · 금리인상 리스크",
    "flow": {
        "level": 26700, "chgPct": 1.6, "yoyPct": 38, "fwdPER": 26.4, "trailingPER": 29.1,
        "breadthText": "섹터 9개 상승 · 2개 하락", "breadthNote": "Tech +32% 견인, Financials -5% 소외",
        "volLabel": "VIX", "volValue": 17.2, "volDir": "down",
        "spark": [70, 69, 71, 73, 72, 75, 77, 76, 80, 83, 85, 84, 88, 92, 100],
    },
    "bands": {
        "base": {"lo": 24000, "hi": 25500}, "bull": {"lo": 28000, "hi": 30500},
        "hyper": {"lo": 36000, "hi": 39000}, "hyperOpen": True,
    },
    "regime": {"composite": 40, "label": "BULL 도달가능", "nAvailable": 6, "nTotal": 6},
    "fearGreed": {
        "score": 62, "label": "Greed", "nAvailable": 5, "nTotal": 6,
        "factors": [
            {"id": "F1", "name": "모멘텀", "value": 0.04, "score": 65},
            {"id": "F2", "name": "강도", "value": 0.64, "score": 70},
            {"id": "F3", "name": "변동성", "value": 17.2, "score": 75},
            {"id": "F4", "name": "신용", "value": 3.2, "score": 78},
            {"id": "F5", "name": "안전자산", "value": 0.03, "score": 55},
        ],
    },
    "reconciliation": {
        "state": "slack", "symbol": "🟡", "label": "여유",
        "supportedCeiling": 29250, "priceBand": "bull", "distancePct": 9,
    },
    "sources": [
        {"id": "S01", "name": "중앙은행 정책", "scope": "Fed", "headroom": 20, "dir": "down",
         "dirLabel": "긴축편향 · 메인 탭 거의 잠김",
         "state": "정책금리 3.50–3.75%, 6/17 동결. 2026 인하 dot 삭제, 인상 쪽 재가격."},
        {"id": "S02", "name": "외국인 자금(참고)", "scope": "간접 배경", "headroom": 75, "dir": "up",
         "dirLabel": "글로벌 자금의 美 비중 변화 참고지표",
         "state": "美 시장은 국내 대기자금·자사주가 핵심. 참고용으로만 추적."},
        {"id": "S03", "name": "신용·레버리지(마진)", "scope": "글로벌 참고", "headroom": 30, "dir": "down",
         "dirLabel": "마진 레버리지 확대 · 되감기 리스크",
         "state": "신용거래 레버리지가 사이클 후반 수준. 변동성 급등 시 되감기."},
        {"id": "S04", "name": "美 대기자금·자사주", "scope": "NASDAQ 핵심", "headroom": 60, "dir": "flat",
         "dirLabel": "규모 큼 · 고금리에 잠김",
         "state": "MMF 사상 최고 '실탄'이나 3.5%+ 금리에 묶여 회전 지연."},
        {"id": "S05", "name": "달러지수(DXY)", "scope": "글로벌 배경", "headroom": 25, "dir": "down",
         "dirLabel": "약달러가 EM 유입엔 우호적",
         "state": "광의 달러지수 약세. 글로벌 위험자산엔 우호적이나 환변동성 동반."},
        {"id": "S06", "name": "글로벌 신용·금융환경", "scope": "핵심 배경", "headroom": 55, "dir": "flat",
         "dirLabel": "완화적이나 후기국면 · 반전 취약",
         "state": "HY OAS 타이트, 위험자본 조달 원활. 후기 신고가 국면 전형."},
    ],
    "sectors": [
        {"code": "Tech", "name": "Technology", "marketCap": 8.46e12, "ytd": 32, "rsRatio": 101.6,
         "rsMomentum": 99.6, "quadrant": "weakening"},
        {"code": "Fin", "name": "Financials", "marketCap": 1.39e12, "ytd": -2, "rsRatio": 98.9,
         "rsMomentum": 98.0, "quadrant": "lagging"},
        {"code": "Energy", "name": "Energy", "marketCap": 1.05e12, "ytd": 18, "rsRatio": 93.1,
         "rsMomentum": 92.0, "quadrant": "lagging"},
    ],
    "leaders": {
        "Tech": {
            "key": [
                {"ticker": "NVDA", "name": "Nvidia", "role": "AI GPU 벨웨더", "price": 184, "ytd": 10,
                 "thesis": "AI 인프라 사이클의 중심축. 리더십 분산 흐름, Vera Rubin 출하가 하반기 관건.",
                 "stats": [["역할", "섹터 벨웨더"], ["촉매", "Vera Rubin 하반기 램프"]],
                 "risk": "리더십 분산 · 높은 밸류에이션 · AI 버블 논쟁", "asOf": "2026-06-18"},
            ],
            "star": [
                {"ticker": "CRDO", "name": "Credo Technology", "role": "커넥티비티·실리콘 포토닉스",
                 "price": 95, "ytd": 74,
                 "thesis": "AEC·실리콘 포토닉스 신흥 강자. DustPhotonics 인수로 광 포트폴리오 강화.",
                 "stats": [["M&A", "DustPhotonics 인수"], ["테마", "광 인터커넥트"]],
                 "risk": "스몰캡 변동성 · 고객 집중도", "asOf": "2026-06-18"},
            ],
        },
    },
    "narrative": {
        "flow": "후기 강세장 · 반도체 랠리가 지수 견인, VIX 한 주간 -6.8%",
        "liquidity": "BULL 도달가능 (천장까지 +9%)",
        "leadership": "Tech 집중 지속 · Financials 저점 탈피 조짐",
        "reconciliation": "🟡 여유",
    },
    "watchlist": [
        {"label": "Fed 점도표·WALCL", "trigger": "인하 dot 부활 / 순증 전환", "meaning": "완화 = hyper 연료 점화", "status": "quiet"},
        {"label": "MMF 총자산 흐름", "trigger": "주간 감소 전환", "meaning": "대기자금 회전 개시", "status": "manual_check"},
        {"label": "자사주·블랙아웃", "trigger": "블랙아웃 구간 진입", "meaning": "구조적 비드 공백", "status": "quiet"},
        {"label": "HY OAS·VIX", "trigger": "스프레드 확대 + 변동성 레짐 전환", "meaning": "멀티플 전제 붕괴", "status": "quiet"},
        {"label": "DXY(달러지수)", "trigger": "강달러 전환", "meaning": "위험자산 역풍", "status": "quiet"},
        {"label": "섹터 breadth", "trigger": "상승 섹터 수 감소", "meaning": "집중심화", "status": "quiet"},
    ],
    "freshness": [
        {"label": "NASDAQ 지수", "source": "Yahoo", "freq": "daily", "last": "2026-06-18", "stale": False},
        {"label": "Fed 금리·대차대조표", "source": "FRED", "freq": "weekly", "last": "2026-06-19", "stale": False},
        {"label": "HY OAS·VIX·DXY", "source": "FRED", "freq": "daily", "last": "2026-06-19", "stale": False},
        {"label": "선행 EPS(컨센서스)", "source": "manual", "freq": "quarterly", "last": "2026-04-15", "stale": False},
        {"label": "섹터 key/star 테제", "source": "manual", "freq": "quarterly", "last": "2026-06-18", "stale": False},
    ],
}

MOCK_PAYLOADS = {"KOSPI": _KOSPI, "NASDAQ": _NASDAQ}
