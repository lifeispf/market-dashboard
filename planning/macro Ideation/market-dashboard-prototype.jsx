import React, { useState, useMemo } from "react";
import { ArrowUp, ArrowDown, Minus, AlertTriangle, CheckCircle2, TrendingUp } from "lucide-react";

/* ============================== DATA ============================== */

const MARKETS = {
  KOSPI: {
    label: "KOSPI",
    asOf: "2026-06-20",
    pill: "후기 강세장 · 반도체 슈퍼사이클",
    flow: {
      level: 9064,
      chgPct: 0.8,
      yoyPct: 199,
      fwdPER: 7.5,
      trailingPER: 11.2,
      breadthText: "상승 197 · 하락 673",
      breadthNote: "반도체·전력·증권 중심 압축 상승",
      volLabel: "VKOSPI(근사)",
      volValue: 19.4,
      volDir: "down",
      spark: [58, 60, 59, 63, 66, 65, 70, 75, 79, 77, 85, 90, 88, 95, 100],
    },
    bands: {
      base: { lo: 10500, hi: 11000 },
      bull: { lo: 12000, hi: 13000 },
      hyper: { lo: 14000, hi: 16000 },
      hyperOpen: true,
    },
    composite: 44,
    narrative: {
      flow: "신고가권 · 반도체·전력 중심 압축 상승(breadth 쏠림)",
      leadership: "반도체(외국인 복귀)가 견인, 전력기기가 다음 순환매 후보로 진입 중",
    },
    sources: [
      { id: "SRC01", name: "중앙은행 정책", scope: "Fed · BOK", headroom: 20, color: "tight", dir: "down",
        dirLabel: "긴축편향 · 메인 탭 거의 잠김",
        state: "Fed 3.50–3.75% 동결, 2026 인하 dot 삭제. 한은 2.50% 동결, 약한 원화·가계부채로 매파 기울기." },
      { id: "SRC02", name: "외국인 자금", scope: "KOSPI 한정", headroom: 75, color: "open", dir: "up",
        dirLabel: "저포지션 · 살 여지 큼(환율이 관건)",
        state: "반도체 비중이 평균 대비 1.3σ 낮은 저포지션. 순매수 회복 중이나 약한 원화가 유입 게이트." },
      { id: "SRC03", name: "국내 신용·레버리지", scope: "KOSPI · KOSDAQ", headroom: 30, color: "tight", dir: "down",
        dirLabel: "스트레치 · 반대매매 리스크 내재",
        state: "개인 참여 사상 최고, 추가 상승분이 신용융자 의존으로 조달되는 비중 확대." },
      { id: "SRC04", name: "美 대기자금·자사주", scope: "글로벌 공통배경", headroom: 60, color: "locked", dir: "flat",
        dirLabel: "규모 큼 · 고금리에 잠김",
        state: "MMF 사상 최고 수준이나 3.5%+ 금리에 묶여 회전 지연. KOSPI엔 간접 배경 변수." },
      { id: "SRC05", name: "원/달러 환율", scope: "증폭기 / 게이트", headroom: 25, color: "tight", dir: "down",
        dirLabel: "약세가 외인 유입 발목(이익엔 +)",
        state: "1,475–1,558 레인지 약세. 외인 유입은 억제하나 수출기업 이익(분모)은 부풀림." },
      { id: "SRC06", name: "글로벌 신용·금융환경", scope: "공통 배경", headroom: 55, color: "neutral", dir: "flat",
        dirLabel: "완화적이나 후기국면 · 반전 취약",
        state: "HY OAS 타이트, 위험자본 조달 원활. 스프레드 반전 시 멀티플 전제 빠르게 붕괴." },
    ],
    sectors: {
      semi: { name: "반도체", weight: 28, ytd: 142, rsR: 1.42, rsM: 0.8,
        key: [
          { t: "005930", n: "삼성전자", role: "메모리·파운드리 벨웨더", ytd: "+120%대 YTD",
            thesis: "AI 메모리 슈퍼사이클 최대 수혜주. HBM·D램 계약가 퀀텀점프와 외국인 저포지션 정상화가 동시에 작동.",
            stats: [["역할", "지수 최대 비중"], ["YTD", "+120%대"], ["수급", "외국인 연속 순매수"]],
            risk: "메모리 가격 사이클 반전 · 단일 섹터 쏠림" },
          { t: "000660", n: "SK하이닉스", role: "HBM 1위 공급자", ytd: "+150%대 YTD",
            thesis: "HBM3E/HBM4 선두 공급자로 AI 데이터센터 수요 직접 수혜. 6월 반도체 랠리의 진앙.",
            stats: [["포지션", "HBM 1위"], ["YTD", "+150%대"], ["촉매", "HBM4 출하 확대"]],
            risk: "고객 집중도 · 캐파 증설 사이클" },
        ],
        star: [
          { t: "042700", n: "한미반도체", role: "HBM 패키징 본더", ytd: "강세",
            thesis: "HBM 패키징 핵심 공정인 TC본더의 사실상 독점적 공급자. SK하이닉스 HBM 증설 사이클에 직결되는 장비주.",
            stats: [["역할", "HBM 본더 공급"], ["고객", "SK하이닉스 등"], ["테마", "후공정 장비"]],
            risk: "고객사 집중 · 수주 변동성" },
          { t: "058470", n: "리노공업", role: "반도체 테스트 소켓", ytd: "강세",
            thesis: "비메모리·시스템반도체 테스트 소켓 점유율 1위. 생산 확대 국면에서 고마진 부품주로 재평가.",
            stats: [["역할", "테스트소켓 1위"], ["마진", "고마진 구조"], ["테마", "후공정 부품"]],
            risk: "환율 민감 · 신규 경쟁 진입" },
        ] },
      power: { name: "전력기기", weight: 6, ytd: 58, rsR: 0.92, rsM: 1.3,
        key: [
          { t: "267260", n: "HD현대일렉트릭", role: "전력기기·변압기", ytd: "강세",
            thesis: "AI 데이터센터발 전력 인프라 수요 확대의 2차 수혜. 반도체 랠리에 후행해 순환매 진입 구간.",
            stats: [["테마", "전력 인프라"], ["순환매", "improving→leading 전환 중"], ["드라이버", "DC 전력수요"]],
            risk: "수주 변동성 · 밸류에이션 부담" },
          { t: "010120", n: "LS ELECTRIC", role: "전력기기", ytd: "강세",
            thesis: "전력망·변전 설비 확대 수혜. 반도체 다음 순환매 후보로 자금 유입이 시작되는 구간.",
            stats: [["테마", "전력 인프라"], ["순환매", "improving"], ["드라이버", "글로벌 전력망 투자"]],
            risk: "원자재 비용 · 수주 사이클" },
        ],
        star: [
          { t: "033100", n: "제룡전기", role: "변압기 부품", ytd: "강세",
            thesis: "북미향 변압기 부품 수출 확대. 대형주 다음으로 자금이 흘러드는 스몰캡 순환매 후보.",
            stats: [["테마", "변압기 부품"], ["수출", "북미향 확대"], ["순환매", "improving"]],
            risk: "환율·관세 노출 · 단일 고객 비중" },
        ] },
      sec: { name: "증권", weight: 5, ytd: 31, rsR: 1.08, rsM: 0.6, top: "미래에셋증권 · 한국금융지주 · 키움증권" },
      auto: { name: "자동차", weight: 8, ytd: 6, rsR: 0.97, rsM: -0.1, top: "현대차 · 기아 · 현대모비스" },
      chem: { name: "화학·2차전지", weight: 6, ytd: -8, rsR: 0.88, rsM: 0.2, top: "LG에너지솔루션 · 에코프로 · 포스코퓨처엠" },
      bio: { name: "바이오", weight: 5, ytd: 4, rsR: 0.95, rsM: -0.3, top: "삼성바이오로직스 · 셀트리온 · 유한양행" },
      bank: { name: "은행·지주", weight: 7, ytd: 18, rsR: 1.02, rsM: -0.4, top: "KB금융 · 신한지주 · 하나금융지주" },
      ship: { name: "조선·기계", weight: 4, ytd: 22, rsR: 1.05, rsM: -0.2, top: "HD현대중공업 · 한화오션 · 두산에너빌리티" },
      telco: { name: "통신", weight: 3, ytd: 9, rsR: 0.99, rsM: -0.05, top: "SK텔레콤 · KT · LG유플러스" },
      cons: { name: "유통·필수소비", weight: 4, ytd: 5, rsR: 0.96, rsM: 0.05, top: "이마트 · BGF리테일 · CJ제일제당" },
    },
    watchlist: [
      { ind: "Fed 점도표 · WALCL", trig: "인하 dot 부활 / 순증 전환 = 완화", sig: "open", freq: "분기·주간" },
      { ind: "외국인 일별 순매수", trig: "3일 연속 순매도 전환 = 한계매수자 이탈", sig: "tight", freq: "일별" },
      { ind: "신용융자잔고 · 반대매매", trig: "잔고 급증 후 반대매매 출현", sig: "tight", freq: "일·주별" },
      { ind: "USD/KRW", trig: "1,500 하회(원화 강세) = 외인 게이트 개방", sig: "open", freq: "실시간" },
      { ind: "HY OAS · VIX", trig: "스프레드 확대 + 변동성 레짐 전환", sig: "tight", freq: "일별" },
      { ind: "breadth", trig: "신고가에도 음수 지속 = 집중심화", sig: "tight", freq: "일별" },
    ],
  },

  NASDAQ: {
    label: "NASDAQ",
    asOf: "2026-06-18",
    pill: "후기 강세장 · 금리인상 리스크",
    flow: {
      level: 26700,
      chgPct: 1.6,
      yoyPct: 38,
      fwdPER: 26.4,
      trailingPER: 29.1,
      breadthText: "섹터 9개 상승 · 2개 하락",
      breadthNote: "Tech +32% 견인, Financials -5% 소외",
      volLabel: "VIX",
      volValue: 17.2,
      volDir: "down",
      spark: [70, 69, 71, 73, 72, 75, 77, 76, 80, 83, 85, 84, 88, 92, 100],
    },
    bands: {
      base: { lo: 24000, hi: 25500 },
      bull: { lo: 28000, hi: 30500 },
      hyper: { lo: 36000, hi: 39000 },
      hyperOpen: true,
    },
    composite: 40,
    narrative: {
      flow: "후기 강세장 · 반도체 랠리가 지수 견인, VIX 한 주간 -6.8%",
      leadership: "Tech 집중 지속, Financials는 저점 탈피 조짐(improving 진입)",
    },
    sources: [
      { id: "SRC01", name: "중앙은행 정책", scope: "Fed", headroom: 20, color: "tight", dir: "down",
        dirLabel: "긴축편향 · 메인 탭 거의 잠김",
        state: "정책금리 3.50–3.75%, 6/17 동결. Warsh 의장 체제로 2026 인하 dot 삭제, 인상 쪽으로 재가격." },
      { id: "SRC02", name: "외국인 자금(참고)", scope: "간접 배경", headroom: 75, color: "open", dir: "up",
        dirLabel: "글로벌 자금의 美 비중 변화 참고지표",
        state: "美 시장은 외국인 비중 변수보다 국내 대기자금·자사주가 핵심. 참고용으로만 추적." },
      { id: "SRC03", name: "신용·레버리지(마진)", scope: "글로벌 참고", headroom: 30, color: "tight", dir: "down",
        dirLabel: "마진 레버리지 확대 · 되감기 리스크",
        state: "신용거래 레버리지가 사이클 후반 수준으로 확대. 변동성 급등 시 되감기 압력." },
      { id: "SRC04", name: "美 대기자금·자사주", scope: "NASDAQ 핵심", headroom: 60, color: "locked", dir: "flat",
        dirLabel: "규모 큼 · 고금리에 잠김",
        state: "MMF 사상 최고 수준의 '실탄'이나 3.5%+ 금리에 묶여 회전 지연. 자사주는 구조적 매수 기반이나 블랙아웃 구간엔 공백." },
      { id: "SRC05", name: "달러지수(DXY)", scope: "글로벌 배경", headroom: 25, color: "tight", dir: "down",
        dirLabel: "약달러가 EM 유입엔 우호적",
        state: "광의 달러지수 약세 흐름. 글로벌 위험자산 전반엔 우호적이나 환변동성 동반." },
      { id: "SRC06", name: "글로벌 신용·금융환경", scope: "핵심 배경", headroom: 55, color: "neutral", dir: "flat",
        dirLabel: "완화적이나 후기국면 · 반전 취약",
        state: "HY OAS 타이트, 위험자본 조달 원활. 신고가 국면의 전형적 후기 특징이라 반전 시 취약." },
    ],
    sectors: {
      Tech: { name: "Technology", weight: 32, ytd: 32, rsR: 1.30, rsM: 0.7,
        key: [
          { t: "NVDA", n: "Nvidia", role: "AI GPU 벨웨더", ytd: "약 +10% YTD",
            thesis: "AI 인프라 사이클의 중심축. 리더십이 동종 칩으로 분산되는 흐름이며 Vera Rubin 출하가 하반기 모멘텀의 관건.",
            stats: [["역할", "섹터 벨웨더"], ["YTD", "약 +10%"], ["촉매", "Vera Rubin 하반기 램프"]],
            risk: "리더십 분산 진행 · 높은 밸류에이션 · AI 버블 논쟁" },
          { t: "AVGO", n: "Broadcom", role: "커스텀 실리콘·네트워킹", ytd: "약 +11% YTD",
            thesis: "하이퍼스케일러 ASIC와 네트워킹 핵심. 2분기 매출 $22.2B(+48%)·AI칩 $10.8B(+143%) 호실적이나 차기 가이던스가 기대를 밑돌아 차익실현 유발.",
            stats: [["2Q 매출", "$22.2B (+48%)"], ["AI칩", "$10.8B (+143%)"], ["FY27 목표", "$100B 유지"]],
            risk: "가이던스 실망 · ASIC 성장 병목 가능성" },
          { t: "MU", n: "Micron", role: "HBM 메모리 리더", ytd: "강세",
            thesis: "HBM3/HBM4 핵심 공급자로 AI 수요 직접 수혜. 6월 반등장에서 약 +9.9%, 메모리 업종 톱픽.",
            stats: [["포지션", "HBM3/HBM4 리더"], ["6월 반등", "약 +9.9%"], ["등급", "Overweight"]],
            risk: "메모리 가격·사이클 변동성 · 캐파 출회" },
        ],
        star: [
          { t: "CRDO", n: "Credo Technology", role: "커넥티비티·실리콘 포토닉스", ytd: "약 +74% YTD",
            thesis: "AEC·실리콘 포토닉스 신흥 강자. DustPhotonics 인수로 광 포트폴리오 강화, 올해 NVDA·AVGO를 크게 앞선 상승률.",
            stats: [["YTD", "약 +74%"], ["M&A", "DustPhotonics 인수"], ["테마", "광 인터커넥트"]],
            risk: "스몰캡 변동성 · 고객 집중도" },
          { t: "ALAB", n: "Astera Labs", role: "데이터센터 커넥티비티", ytd: "강세",
            thesis: "PCIe/CXL 리타이머 등 데이터센터 연결 핵심 스몰캡. AI 인프라 확장의 두 번째 파생 수혜.",
            stats: [["영역", "PCIe/CXL"], ["평가", "대표 스몰캡 픽"], ["드라이버", "DC 캐펙스 확대"]],
            risk: "밸류에이션 부담 · 단일 테마 의존" },
        ] },
      Fin: { name: "Financials", weight: 13, ytd: -5, rsR: 0.85, rsM: 0.25,
        key: [
          { t: "JPM", n: "JPMorgan", role: "최대 美 은행", ytd: "섹터 부진",
            thesis: "섹터 부진의 중심. '연내 인하' 기대가 '인상'으로 재가격되며 금융주 약세. 규모·자본력은 견고.",
            stats: [["포지션", "최대 美 은행"], ["섹터 YTD", "약 -5%"], ["변수", "Fed 인상 재가격"]],
            risk: "순이자마진 압력 · 신용 정상화" },
          { t: "BAC", n: "Bank of America", role: "금리 민감 대형은행", ytd: "섹터 부진",
            thesis: "장기금리 상승에 채권 포트폴리오(AOCI) 민감도가 큰 대표 종목. 예금비용·금리 경로가 핵심 변수.",
            stats: [["민감도", "장기금리·AOCI"], ["섹터 YTD", "약 -5%"], ["변수", "예금비용"]],
            risk: "금리 변동성 · 예대 스프레드" },
        ],
        star: [
          { t: "HOOD", n: "Robinhood", role: "리테일·핀테크", ytd: "강세",
            thesis: "전통 은행 부진 속에서도 리테일 거래·크립토 확장으로 모멘텀 유지. 섹터를 역행하는 대표 핀테크.",
            stats: [["성장축", "리테일·크립토"], ["대비", "섹터 역행 상승"], ["테마", "핀테크 디스럽션"]],
            risk: "리테일 거래량 민감 · 규제" },
          { t: "SOFI", n: "SoFi", role: "핀테크 플랫폼", ytd: "강세",
            thesis: "대출+핀테크 플랫폼 성장 스토리. 멤버 증가·교차판매가 동력이나 금리·신용에 노출.",
            stats: [["모델", "대출+플랫폼"], ["동력", "멤버·교차판매"], ["테마", "디지털 뱅킹"]],
            risk: "신용 품질 · 조달비용 · 금리" },
        ] },
      Energy: { name: "Energy", weight: 3, ytd: 26, rsR: 1.15, rsM: -0.4, top: "XOM · CVX · COP" },
      ConsDisc: { name: "Consumer Disc.", weight: 10, ytd: 4, rsR: 0.97, rsM: -0.2, top: "AMZN · TSLA · HD" },
      Health: { name: "Health Care", weight: 10, ytd: -3, rsR: 0.80, rsM: -0.3, top: "LLY · UNH · JNJ" },
      Comm: { name: "Communication", weight: 9, ytd: 6, rsR: 0.92, rsM: 0.15, top: "META · GOOGL · NFLX" },
      Indus: { name: "Industrials", weight: 8, ytd: 12, rsR: 1.08, rsM: 0.3, top: "GE · CAT · RTX" },
      Staples: { name: "Cons. Staples", weight: 6, ytd: 7, rsR: 0.93, rsM: -0.1, top: "COST · WMT · PG" },
      Util: { name: "Utilities", weight: 2.5, ytd: 5, rsR: 0.90, rsM: -0.05, top: "NEE · SO · DUK" },
      RE: { name: "Real Estate", weight: 2, ytd: 10, rsR: 0.95, rsM: 0.35, top: "PLD · AMT · EQIX" },
      Mat: { name: "Materials", weight: 2, ytd: 13, rsR: 1.05, rsM: -0.15, top: "LIN · SHW · FCX" },
    },
    watchlist: [
      { ind: "Fed 점도표 · WALCL", trig: "인하 dot 부활 / 순증 전환 = 완화", sig: "open", freq: "분기·주간" },
      { ind: "MMF 총자산 흐름", trig: "주간 감소 전환 = 대기자금 회전 개시", sig: "open", freq: "주간" },
      { ind: "자사주 매입 · 블랙아웃", trig: "블랙아웃 구간 진입 = 구조적 비드 공백", sig: "tight", freq: "수시" },
      { ind: "HY OAS · VIX", trig: "스프레드 확대 + 변동성 레짐 전환", sig: "tight", freq: "일별" },
      { ind: "DXY(달러지수)", trig: "강달러 전환 = 위험자산 역풍", sig: "tight", freq: "일별" },
      { ind: "섹터 breadth", trig: "상승 섹터 수 감소 = 집중심화", sig: "tight", freq: "일별" },
    ],
  },
};

const FRESHNESS = [
  { label: "KOSPI/NASDAQ 지수", freq: "일·실시간", last: "2026-06-20", stale: false },
  { label: "Fed 금리·대차대조표(FRED)", freq: "일·주간", last: "2026-06-19", stale: false },
  { label: "외국인 순매매(pykrx)", freq: "일", last: "2026-06-19", stale: false },
  { label: "HY OAS·VIX·DXY(FRED)", freq: "일", last: "2026-06-19", stale: false },
  { label: "선행 EPS(컨센서스)", freq: "분기", last: "2026-04-15", stale: false },
  { label: "신용융자잔고(freesis)", freq: "일", last: "2026-06-18", stale: false },
  { label: "MMF 총자산(ICI)", freq: "주", last: "2026-06-18", stale: false },
  { label: "자사주 매입·블랙아웃 캘린더", freq: "수시", last: "2026-05-30", stale: true },
];

/* ============================== HELPERS ============================== */

const fmt = (n) => Math.round(n).toLocaleString();

function rank(value, bands) {
  if (value >= bands.hyper.lo) return 3;
  if (value >= bands.bull.lo) return 2;
  if (value >= bands.base.lo) return 1;
  return 0;
}
function allowedRank(composite) {
  if (composite >= 67) return 3;
  if (composite >= 34) return 2;
  return 1;
}
function regimeLabel(composite) {
  if (composite >= 67) return "HYPER 연료 존재";
  if (composite >= 34) return "BULL 도달가능";
  return "BASE only";
}
const bandMid = (b) => (b.lo + b.hi) / 2;
const bandByRank = (bands, r) => (r === 3 ? bands.hyper : r === 2 ? bands.bull : bands.base);
const bandName = (r) => (r === 3 ? "HYPER" : r === 2 ? "BULL" : r === 1 ? "BASE" : "BASE 미달");

function reconciliation(market) {
  const a = rank(market.flow.level, market.bands);
  const al = allowedRank(market.composite);
  const supported = bandMid(bandByRank(market.bands, al));
  const distSupportedPct = ((supported - market.flow.level) / market.flow.level) * 100;
  const nextCeil = market.flow.level < market.bands.base.lo
    ? bandMid(market.bands.base)
    : market.flow.level < market.bands.bull.lo
    ? bandMid(market.bands.bull)
    : bandMid(market.bands.hyper);
  const distNextPct = ((nextCeil - market.flow.level) / market.flow.level) * 100;

  let state, symbol, label;
  if (a === al) { state = "aligned"; symbol = "🟢"; label = "정합"; }
  else if (a > al) { state = "overheat"; symbol = "🔴"; label = "과열 — 연료 없이 앞섬"; }
  else { state = "room"; symbol = "🟡"; label = "여유 — 유동성이 상방 지지"; }

  return { achievedRank: a, allowedRank: al, supported, distSupportedPct, nextCeil, distNextPct, state, symbol, label };
}

function quadrant(s) {
  if (s.rsR >= 1 && s.rsM >= 0) return "leading";
  if (s.rsR >= 1 && s.rsM < 0) return "weakening";
  if (s.rsR < 1 && s.rsM >= 0) return "improving";
  return "lagging";
}
const QUAD_COLOR = { leading: "open", weakening: "tight", improving: "neutral", lagging: "locked" };
const QUAD_KR = { leading: "주도 지속", weakening: "차익 임박", improving: "순환매 진입", lagging: "소외" };

/* ============================== STYLES ============================== */

const STYLES = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap');
.ld-root{
  --ink:#0b1418; --panel:#11212a; --panel-2:#162c37; --line:#23404c; --line-soft:#1b333d;
  --text:#e9e7dd; --text-dim:#9bb0b8; --text-faint:#5f7984;
  --brass:#d9a441; --brass-soft:#b78a38;
  --open:#5fb98e; --neutral:#cdb15a; --tight:#d06b4a; --locked:#7f93c4;
  --mono:'IBM Plex Mono',monospace; --disp:'Space Grotesk','IBM Plex Sans KR',sans-serif; --body:'IBM Plex Sans KR','IBM Plex Sans',sans-serif;
  background:var(--ink); color:var(--text); font-family:var(--body); font-weight:300; line-height:1.6;
  -webkit-font-smoothing:antialiased; min-height:100vh; padding-bottom:40px;
}
.ld-root *{box-sizing:border-box}
.ld-wrap{max-width:1080px;margin:0 auto;padding:0 18px}
.ld-proto-banner{background:var(--panel-2);border-bottom:1px solid var(--line);padding:8px 18px;font-family:var(--mono);font-size:11px;color:var(--text-faint);text-align:center;letter-spacing:.04em}
.ld-proto-banner b{color:var(--brass)}

/* global macro bar */
.ld-macro{display:flex;flex-wrap:wrap;gap:18px;padding:14px 18px;background:var(--panel-2);border-bottom:1px solid var(--line);font-family:var(--mono);font-size:11.5px;color:var(--text-faint)}
.ld-macro b{color:var(--text);font-weight:500}

/* header / toggle */
.ld-header{padding:22px 0 14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
.ld-toggle{display:flex;gap:6px;background:var(--panel);border:1px solid var(--line-soft);border-radius:8px;padding:4px}
.ld-toggle button{font-family:var(--mono);font-size:12.5px;letter-spacing:.04em;padding:8px 16px;border-radius:6px;border:none;background:transparent;color:var(--text-faint);cursor:pointer;font-weight:500}
.ld-toggle button.active{background:var(--brass);color:#1a1306}
.ld-pill{font-family:var(--mono);font-size:11px;padding:6px 12px;border-radius:7px;background:#3a2e12;color:var(--brass);letter-spacing:.03em}
.ld-asof{font-family:var(--mono);font-size:11px;color:var(--text-faint)}

/* cross narrative badge */
.ld-narrative{margin:6px 0 26px;padding:18px 20px;background:linear-gradient(180deg,var(--panel-2),var(--panel));border:1px solid var(--line);border-radius:6px;position:relative;overflow:hidden}
.ld-narrative::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,var(--brass),var(--tight))}
.ld-narrative-row{display:flex;flex-wrap:wrap;gap:8px 0;font-size:13.5px;color:var(--text-dim);align-items:center}
.ld-narrative-seg{display:flex;align-items:center;gap:7px;padding:4px 12px 4px 0;margin-right:10px;border-right:1px solid var(--line-soft)}
.ld-narrative-seg:last-child{border-right:none}
.ld-narrative-seg b{color:var(--text);font-weight:500}
.ld-narrative-lab{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--brass);display:block;margin-bottom:6px}

/* section */
.ld-section{padding:30px 0 4px}
.ld-sec-head{display:flex;align-items:baseline;gap:14px;margin-bottom:4px}
.ld-sec-num{font-family:var(--mono);font-size:11px;color:var(--brass);letter-spacing:.1em}
.ld-h2{font-family:var(--disp);font-weight:500;font-size:19px;color:var(--text)}
.ld-sec-sub{color:var(--text-faint);font-size:12.5px;margin:4px 0 18px;max-width:70ch}

/* KPI strip */
.ld-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:6px}
.ld-kpi{background:var(--panel);border:1px solid var(--line-soft);border-radius:8px;padding:12px 14px}
.ld-kpi .l{font-size:11.5px;color:var(--text-faint);font-family:var(--mono)}
.ld-kpi .v{font-size:21px;font-weight:600;margin:3px 0;font-family:var(--disp)}
.ld-kpi .c{font-size:12px;display:flex;align-items:center;gap:4px}
.c-up{color:var(--open)} .c-down{color:var(--tight)} .c-flat{color:var(--text-faint)}
.ld-spark-wrap{margin-top:18px;background:var(--panel);border:1px solid var(--line-soft);border-radius:8px;padding:12px 16px}
.ld-spark-lab{font-family:var(--mono);font-size:10.5px;color:var(--text-faint);letter-spacing:.1em;margin-bottom:6px}

/* ceiling chart */
.ld-grid2{display:grid;grid-template-columns:1.4fr 1fr;gap:16px;align-items:stretch}
.ld-card{background:var(--panel);border:1px solid var(--line-soft);border-radius:6px;padding:18px 20px}
.ld-card-title{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--brass);margin-bottom:10px}
.ceilbox{position:relative;height:300px;margin:10px 4px 4px}
.ceilplot{position:relative;height:100%}
.band{position:absolute;left:0;right:0;border-radius:2px}
.band-open{background:rgba(95,185,142,.16);border-top:1px solid rgba(95,185,142,.55);border-bottom:1px solid rgba(95,185,142,.55)}
.band-neutral{background:rgba(205,177,90,.16);border-top:1px solid rgba(205,177,90,.55);border-bottom:1px solid rgba(205,177,90,.55)}
.band-tight{background:rgba(208,107,74,.16);border-top:1px solid rgba(208,107,74,.55);border-bottom:1px solid rgba(208,107,74,.55)}
.band-label{position:absolute;left:8px;top:4px;font-family:var(--mono);font-size:10.5px;color:var(--text-dim);white-space:nowrap}
.curline{position:absolute;left:0;right:0;border-top:2px solid var(--text);z-index:2}
.curline-label{position:absolute;right:0;top:-19px;font-family:var(--mono);font-size:11px;color:var(--ink);background:var(--text);padding:2px 8px;border-radius:3px;font-weight:600}
.supline{position:absolute;left:0;right:0;border-top:2px dashed var(--brass);z-index:1}
.supline-label{position:absolute;left:0;top:5px;font-family:var(--mono);font-size:10px;color:var(--brass);background:var(--ink);padding:1px 6px;border-radius:3px}

/* gauge */
.ld-gaugebox{display:flex;flex-direction:column;gap:14px;height:100%;justify-content:center}
.track{height:9px;background:#0a1316;border:1px solid var(--line-soft);border-radius:5px;overflow:hidden}
.fill{height:100%;border-radius:4px}
.f-open{background:linear-gradient(90deg,#3f8c69,var(--open))}
.f-neutral{background:linear-gradient(90deg,#9c8736,var(--neutral))}
.f-tight{background:linear-gradient(90deg,#8f4730,var(--tight))}
.f-locked{background:linear-gradient(90deg,#4f5f8c,var(--locked))}
.ld-gauge-val{font-family:var(--mono);font-size:24px;font-weight:600}
.ld-gauge-lab{font-family:var(--mono);font-size:11px;color:var(--text-faint);letter-spacing:.08em;margin-top:4px}
.ld-reconcile{display:flex;align-items:flex-start;gap:10px;padding:12px 14px;border-radius:6px;border:1px solid var(--line-soft);background:var(--panel-2);margin-top:4px}
.ld-reconcile .t{font-size:13px;color:var(--text-dim);line-height:1.55}
.ld-reconcile .t b{color:var(--text);font-weight:500}

/* source panels */
.ld-sources{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:14px}
.ld-src{background:var(--panel);border:1px solid var(--line-soft);border-radius:6px;padding:16px 18px}
.ld-src-top{display:flex;align-items:center;gap:9px;margin-bottom:6px;flex-wrap:wrap}
.ld-src-id{font-family:var(--mono);font-size:10px;color:var(--brass);border:1px solid var(--line);border-radius:3px;padding:2px 6px}
.ld-src-name{font-family:var(--disp);font-size:14.5px;font-weight:500}
.ld-src-scope{font-family:var(--mono);font-size:9.5px;text-transform:uppercase;color:var(--text-faint);margin-left:auto}
.ld-src-state{font-size:12.5px;color:var(--text-dim);line-height:1.6;margin-bottom:10px}
.ld-src-gauge-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}
.ld-src-gauge-row .gv{font-family:var(--mono);font-size:12px;font-weight:600}
.ld-dir{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:10.5px;margin-top:6px}
.c-open{color:var(--open)} .c-neutral{color:var(--neutral)} .c-tight{color:var(--tight)} .c-locked{color:var(--locked)}

/* treemap */
.ld-treemap{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px;margin-bottom:14px}
.ld-cell{flex-grow:1;min-width:88px;height:78px;border:none;border-radius:8px;padding:8px 10px;text-align:left;cursor:pointer;display:flex;flex-direction:column;justify-content:space-between;font-family:inherit;transition:filter .12s,transform .12s}
.ld-cell:hover{filter:brightness(1.15);transform:translateY(-1px)}
.ld-cell.sel{box-shadow:inset 0 0 0 2px var(--text)}
.ld-cell .nm{font-size:12px;font-weight:600;line-height:1.2}
.ld-cell .pc{font-size:14.5px;font-weight:700}
.ld-cell.deep{box-shadow:inset 0 0 0 2px rgba(217,164,65,.45)}

/* RRG */
.rrgbox{height:280px;margin:10px 0 4px}
.rrgplot{position:relative;height:100%;background:var(--panel);border:1px solid var(--line-soft);border-radius:6px;overflow:hidden}
.rrg-quad span{position:absolute;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;color:var(--text-faint);padding:7px}
.rrg-axis-x{position:absolute;top:0;bottom:0;width:1px;background:var(--line)}
.rrg-axis-y{position:absolute;left:0;right:0;height:1px;background:var(--line)}
.rrg-dot{position:absolute;transform:translate(-50%,-50%);width:11px;height:11px;border-radius:50%;border:2px solid var(--ink);cursor:pointer;padding:0}
.rrg-dot.sel{outline:2px solid var(--text);outline-offset:1px}
.dot-open{background:var(--open)} .dot-neutral{background:var(--neutral)} .dot-tight{background:var(--tight)} .dot-locked{background:var(--locked)}
.rrg-dot-label{position:absolute;left:13px;top:-7px;font-family:var(--mono);font-size:10px;color:var(--text-dim);white-space:nowrap;pointer-events:none}
.ld-rrg-legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-family:var(--mono);font-size:10.5px;color:var(--text-faint)}
.ld-rrg-legend span{display:inline-flex;align-items:center;gap:5px}
.ld-rrg-legend i{width:8px;height:8px;border-radius:50%;display:inline-block}

/* leader cards */
.ld-hint{font-size:11.5px;color:var(--text-faint);margin-bottom:10px}
.ld-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:9px}
.ld-pcard{text-align:left;background:var(--panel);border:1px solid var(--line-soft);border-radius:8px;padding:12px 14px;cursor:pointer;font-family:inherit;color:var(--text)}
.ld-pcard:hover{border-color:var(--brass-soft)}
.ld-pcard.sel{border-color:var(--brass)}
.ld-pcard .top{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.ld-pcard .tk{font-weight:700;font-size:13.5px;font-family:var(--mono)}
.ld-tag{font-size:9.5px;padding:2px 7px;border-radius:5px;font-weight:600;font-family:var(--mono)}
.ld-tag.k{background:#10243d;color:#7eb3ff}
.ld-tag.s{background:#0e2c25;color:var(--open)}
.ld-pcard .nm{font-size:12px;color:var(--text-dim)}
.ld-pcard .rl{font-size:10.5px;color:var(--text-faint);margin-top:3px}
.ld-detail{margin-top:14px;background:var(--panel-2);border:1px solid var(--line);border-radius:8px;padding:16px 18px}
.ld-detail .dn{font-family:var(--disp);font-size:16px;font-weight:600}
.ld-detail .dr{font-size:12px;color:var(--text-faint);margin-bottom:10px}
.ld-detail .thesis{font-size:13px;line-height:1.7;color:var(--text-dim);margin-bottom:12px}
.ld-detail .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:12px}
.ld-detail .stat{background:var(--panel);border-radius:6px;padding:8px 10px}
.ld-detail .stat .sl{font-size:10.5px;color:var(--text-faint);font-family:var(--mono)}
.ld-detail .stat .sv{font-size:12.5px;font-weight:500;margin-top:2px}
.ld-risk{display:flex;gap:8px;background:#2a1414;border-radius:6px;padding:9px 12px;font-size:12px;color:#ffb3b3}
.ld-simple{font-size:12.5px;color:var(--text-dim)}

/* watchlist */
.ld-watch-wrap{overflow-x:auto;border:1px solid var(--line-soft);border-radius:6px;margin-top:6px}
.ld-table{width:100%;border-collapse:collapse;min-width:560px}
.ld-table thead th{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--brass);text-align:left;padding:11px 14px;background:var(--panel-2);border-bottom:1px solid var(--line)}
.ld-table tbody td{padding:11px 14px;font-size:12.5px;color:var(--text-dim);border-bottom:1px solid var(--line-soft);vertical-align:top}
.ld-table tbody tr:last-child td{border-bottom:none}
.ld-table td:first-child{color:var(--text)}
.ld-freq{font-family:var(--mono);font-size:10.5px;color:var(--text-faint)}
.sig-open{color:var(--open)} .sig-tight{color:var(--tight)}

/* freshness */
.ld-fresh{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.ld-fresh-item{display:flex;align-items:center;gap:7px;font-family:var(--mono);font-size:10.5px;color:var(--text-faint);background:var(--panel);border:1px solid var(--line-soft);border-radius:5px;padding:6px 10px}
.ld-fresh-dot{width:7px;height:7px;border-radius:50%}
.ld-fresh-dot.ok{background:var(--open)} .ld-fresh-dot.bad{background:var(--neutral)}

.ld-footer{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);font-size:11.5px;color:var(--text-faint);line-height:1.7}

@media (max-width:760px){
  .ld-grid2{grid-template-columns:1fr}
}
`;

/* ============================== SMALL COMPONENTS ============================== */

function Sparkline({ data, color = "var(--brass)" }) {
  const w = 100, h = 28;
  const min = Math.min(...data), max = Math.max(...data);
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / (max - min || 1)) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: 40 }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.6" />
    </svg>
  );
}

function DirIcon({ dir, size = 12 }) {
  if (dir === "up") return <ArrowUp size={size} />;
  if (dir === "down") return <ArrowDown size={size} />;
  return <Minus size={size} />;
}

function CeilingChart({ bands, current, supported }) {
  const min = Math.min(current, bands.base.lo) * 0.92;
  const max = bands.hyper.hi * 1.12;
  const pct = (v) => Math.max(0, Math.min(100, ((max - v) / (max - min)) * 100));
  const order = [
    { key: "hyper", lo: bands.hyper.lo, hi: bands.hyper.hi, cls: "tight", name: "HYPER", open: bands.hyperOpen },
    { key: "bull", lo: bands.bull.lo, hi: bands.bull.hi, cls: "neutral", name: "BULL" },
    { key: "base", lo: bands.base.lo, hi: bands.base.hi, cls: "open", name: "BASE" },
  ];
  return (
    <div className="ceilbox">
      <div className="ceilplot">
        {order.map((b) => (
          <div key={b.key} className={`band band-${b.cls}`} style={{ top: pct(b.hi) + "%", height: (pct(b.lo) - pct(b.hi)) + "%" }}>
            <span className="band-label">{b.name} {fmt(b.lo)}–{fmt(b.hi)}{b.open ? "+" : ""}</span>
          </div>
        ))}
        <div className="supline" style={{ top: pct(supported) + "%" }}>
          <span className="supline-label">유동성 지지 천장 {fmt(supported)}</span>
        </div>
        <div className="curline" style={{ top: pct(current) + "%" }}>
          <span className="curline-label">현재 {fmt(current)}</span>
        </div>
      </div>
    </div>
  );
}

function RRGChart({ sectors, selectedKey, onSelect }) {
  const list = Object.entries(sectors).map(([code, s]) => ({ ...s, code }));
  const xs = list.map((s) => s.rsR), ys = list.map((s) => s.rsM);
  const xmin = Math.min(0.75, ...xs) - 0.04, xmax = Math.max(1.45, ...xs) + 0.04;
  const ymin = Math.min(-0.6, ...ys) - 0.08, ymax = Math.max(1.4, ...ys) + 0.08;
  const leftPct = (v) => ((v - xmin) / (xmax - xmin)) * 100;
  const topPct = (v) => ((ymax - v) / (ymax - ymin)) * 100;
  const xZero = leftPct(1.0), yZero = topPct(0);
  return (
    <div className="rrgbox">
      <div className="rrgplot">
        <div className="rrg-quad" style={{ position: "absolute", left: xZero + "%", top: 0, right: 0, height: yZero + "%" }}>
          <span style={{ top: 0, right: 0 }}>LEADING</span>
        </div>
        <div className="rrg-quad" style={{ position: "absolute", left: xZero + "%", top: yZero + "%", right: 0, bottom: 0 }}>
          <span style={{ bottom: 0, right: 0 }}>WEAKENING</span>
        </div>
        <div className="rrg-quad" style={{ position: "absolute", left: 0, top: 0, width: xZero + "%", height: yZero + "%" }}>
          <span style={{ top: 0, left: 0 }}>IMPROVING</span>
        </div>
        <div className="rrg-quad" style={{ position: "absolute", left: 0, top: yZero + "%", width: xZero + "%", bottom: 0 }}>
          <span style={{ bottom: 0, left: 0 }}>LAGGING</span>
        </div>
        <div className="rrg-axis-x" style={{ left: xZero + "%" }} />
        <div className="rrg-axis-y" style={{ top: yZero + "%" }} />
        {list.map((s) => {
          const q = quadrant(s);
          return (
            <button key={s.code} className={`rrg-dot dot-${QUAD_COLOR[q]} ${selectedKey === s.code ? "sel" : ""}`}
              style={{ left: leftPct(s.rsR) + "%", top: topPct(s.rsM) + "%" }}
              onClick={() => onSelect(s.code)} title={s.name}>
              <span className="rrg-dot-label">{s.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ============================== LAYOUT COMPONENTS ============================== */

function GlobalMacroBar() {
  return (
    <div className="ld-macro">
      <span>Fed Funds <b>3.50–3.75%</b></span>
      <span>USD/KRW <b>≈1,510</b></span>
      <span>DXY <b>약세 추세</b></span>
      <span>HY OAS <b>타이트</b></span>
      <span>VIX <b>17.2</b></span>
    </div>
  );
}

function Header({ market, setMarket, data }) {
  return (
    <div className="ld-header">
      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <div className="ld-toggle">
          {["KOSPI", "NASDAQ"].map((m) => (
            <button key={m} className={market === m ? "active" : ""} onClick={() => setMarket(m)}>{m}</button>
          ))}
        </div>
        <span className="ld-pill">{data.pill}</span>
      </div>
      <span className="ld-asof">기준일 {data.asOf} · 스냅샷</span>
    </div>
  );
}

function CrossNarrativeBadge({ data, rec }) {
  return (
    <div className="ld-narrative">
      <span className="ld-narrative-lab">흐름 ▸ 여력 ▸ 주도 ▸ 정합성</span>
      <div className="ld-narrative-row">
        <span className="ld-narrative-seg"><b>흐름</b>&nbsp;{data.narrative.flow}</span>
        <span className="ld-narrative-seg"><b>여력</b>&nbsp;{regimeLabel(data.composite)} (상방 {rec.distNextPct >= 0 ? "+" : ""}{rec.distNextPct.toFixed(0)}%)</span>
        <span className="ld-narrative-seg"><b>주도</b>&nbsp;{data.narrative.leadership}</span>
        <span className="ld-narrative-seg">{rec.symbol}&nbsp;<b>정합성</b>&nbsp;{rec.label}</span>
      </div>
    </div>
  );
}

function FlowSection({ data }) {
  return (
    <div className="ld-section">
      <div className="ld-sec-head"><span className="ld-sec-num">LAYER 1</span><h2 className="ld-h2">흐름</h2></div>
      <p className="ld-sec-sub">지금 지수가 어디서 · 어떻게 움직이는지 — 가격, breadth, 변동성.</p>
      <div className="ld-kpis">
        <div className="ld-kpi">
          <div className="l">현재가</div>
          <div className="v">{fmt(data.flow.level)}</div>
          <div className={`c c-${data.flow.chgPct >= 0 ? "up" : "down"}`}><DirIcon dir={data.flow.chgPct >= 0 ? "up" : "down"} />{data.flow.chgPct >= 0 ? "+" : ""}{data.flow.chgPct}% (1D)</div>
        </div>
        <div className="ld-kpi">
          <div className="l">YoY</div>
          <div className="v">+{data.flow.yoyPct}%</div>
          <div className="c c-flat">52주 신고가권</div>
        </div>
        <div className="ld-kpi">
          <div className="l">선행 PER</div>
          <div className="v">{data.flow.fwdPER}x</div>
          <div className="c c-flat">trailing {data.flow.trailingPER}x</div>
        </div>
        <div className="ld-kpi">
          <div className="l">Breadth</div>
          <div className="v" style={{ fontSize: 15 }}>{data.flow.breadthText}</div>
          <div className="c c-flat">{data.flow.breadthNote}</div>
        </div>
        <div className="ld-kpi">
          <div className="l">{data.flow.volLabel}</div>
          <div className="v">{data.flow.volValue}</div>
          <div className={`c c-${data.flow.volDir === "down" ? "up" : "down"}`}><DirIcon dir={data.flow.volDir} />{data.flow.volDir === "down" ? "안정화" : "상승"}</div>
        </div>
      </div>
      <div className="ld-spark-wrap">
        <div className="ld-spark-lab">최근 추세 (상대 형태)</div>
        <Sparkline data={data.flow.spark} />
      </div>
    </div>
  );
}

function LiquiditySection({ data, rec }) {
  return (
    <div className="ld-section">
      <div className="ld-sec-head"><span className="ld-sec-num">LAYER 2</span><h2 className="ld-h2">여력 (유동성)</h2></div>
      <p className="ld-sec-sub">그 움직임을 떠받칠 연료가 어디까지 차 있는지 — 시나리오별 천장과 6원천 헤드룸.</p>
      <div className="ld-grid2">
        <div className="ld-card">
          <div className="ld-card-title">시나리오별 천장 밴드</div>
          <CeilingChart bands={data.bands} current={data.flow.level} supported={rec.supported} />
        </div>
        <div className="ld-card">
          <div className="ld-card-title">유동성 Regime</div>
          <div className="ld-gaugebox">
            <div>
              <div className="ld-gauge-val">{data.composite}<span style={{ fontSize: 13, color: "var(--text-faint)" }}>/100</span></div>
              <div className="ld-gauge-lab">{regimeLabel(data.composite)}</div>
              <div className="track" style={{ marginTop: 10 }}>
                <div className={`fill f-${data.composite >= 67 ? "tight" : data.composite >= 34 ? "neutral" : "open"}`} style={{ width: data.composite + "%" }} />
              </div>
            </div>
            <div className="ld-reconcile">
              <span style={{ fontSize: 16 }}>{rec.symbol}</span>
              <div className="t">
                <b>{bandName(rec.achievedRank)}</b> 도달 vs 유동성 허용 <b>{bandName(rec.allowedRank)}</b><br />
                유동성 지지 천장까지 <b>{rec.distSupportedPct >= 0 ? "+" : ""}{rec.distSupportedPct.toFixed(0)}%</b>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="ld-sources">
        {data.sources.map((s) => (
          <div className="ld-src" key={s.id}>
            <div className="ld-src-top">
              <span className="ld-src-id">{s.id}</span>
              <span className="ld-src-name">{s.name}</span>
              <span className="ld-src-scope">{s.scope}</span>
            </div>
            <div className="ld-src-state">{s.state}</div>
            <div className="ld-src-gauge-row"><span style={{ fontFamily: "var(--mono)", fontSize: 10.5, color: "var(--text-faint)" }}>헤드룸</span><span className="gv">{s.headroom}/100</span></div>
            <div className="track"><div className={`fill f-${s.color}`} style={{ width: s.headroom + "%" }} /></div>
            <div className={`ld-dir c-${s.color}`}><DirIcon dir={s.dir} size={11} />{s.dirLabel}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function treemapColor(ytd) {
  if (ytd > 40) return "rgba(95,185,142,.45)";
  if (ytd > 15) return "rgba(95,185,142,.26)";
  if (ytd >= 0) return "rgba(205,177,90,.22)";
  return "rgba(208,107,74,.28)";
}

function LeadershipSection({ data }) {
  const sectorEntries = Object.entries(data.sectors).map(([code, s]) => ({ ...s, code }));
  const defaultKey = sectorEntries.reduce((a, b) => (b.weight > a.weight ? b : a)).code;
  const [selSector, setSelSector] = useState(defaultKey);
  const [selLeader, setSelLeader] = useState(null);
  const sel = data.sectors[selSector];
  const allLeaders = sel.key ? [
    ...sel.key.map((l) => ({ ...l, tag: "k" })),
    ...(sel.star || []).map((l) => ({ ...l, tag: "s" })),
  ] : [];
  const selLeaderObj = allLeaders.find((l) => l.t === selLeader) || null;

  return (
    <div className="ld-section">
      <div className="ld-sec-head"><span className="ld-sec-num">LAYER 3</span><h2 className="ld-h2">주도 (섹터 · 종목)</h2></div>
      <p className="ld-sec-sub">연료가 지금 어느 섹터 · 종목으로 흐르는지 — 섹터 트리맵, 순환매(RRG), 주도주.</p>

      <div className="ld-card-title" style={{ marginTop: 6 }}>섹터 트리맵 (크기 = 비중, 색 = YTD)</div>
      <div className="ld-treemap">
        {sectorEntries.map((s) => (
          <button key={s.code} className={`ld-cell ${selSector === s.code ? "sel" : ""}`}
            style={{ flexGrow: s.weight, background: treemapColor(s.ytd) }}
            onClick={() => { setSelSector(s.code); setSelLeader(null); }}>
            <span className="nm">{s.name}</span>
            <span className="pc">{s.ytd >= 0 ? "+" : ""}{s.ytd}%</span>
          </button>
        ))}
      </div>

      <div className="ld-grid2" style={{ marginTop: 18 }}>
        <div className="ld-card">
          <div className="ld-card-title">순환매 (RRG) — 상대강도 × 모멘텀</div>
          <RRGChart sectors={data.sectors} selectedKey={selSector} onSelect={(k) => { setSelSector(k); setSelLeader(null); }} />
          <div className="ld-rrg-legend">
            <span><i style={{ background: "var(--open)" }} />leading · 주도 지속</span>
            <span><i style={{ background: "var(--tight)" }} />weakening · 차익 임박</span>
            <span><i style={{ background: "var(--neutral)" }} />improving · 순환매 진입</span>
            <span><i style={{ background: "var(--locked)" }} />lagging · 소외</span>
          </div>
        </div>
        <div className="ld-card">
          <div className="ld-card-title">{sel.name} · {QUAD_KR[quadrant(sel)]}</div>
          <div className="ld-hint">섹터를 클릭하면 종목 정보가 바뀝니다. 카드를 클릭하면 상세가 펼쳐집니다.</div>
          {sel.key ? (
            <>
              <div className="ld-cards">
                {allLeaders.map((l) => (
                  <button key={l.t} className={`ld-pcard ${selLeader === l.t ? "sel" : ""}`}
                    onClick={() => setSelLeader(selLeader === l.t ? null : l.t)}>
                    <div className="top"><span className="tk">{l.t}</span><span className={`ld-tag ${l.tag}`}>{l.tag === "k" ? "Key" : "Star"}</span></div>
                    <div className="nm">{l.n}</div>
                    <div className="rl">{l.role}</div>
                  </button>
                ))}
              </div>
              {selLeaderObj && (
                <div className="ld-detail">
                  <div className="dn">{selLeaderObj.n} <span style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--text-faint)" }}>{selLeaderObj.t}</span></div>
                  <div className="dr">{selLeaderObj.role} · {selLeaderObj.ytd}</div>
                  <div className="thesis">{selLeaderObj.thesis}</div>
                  <div className="stats">
                    {selLeaderObj.stats.map(([k, v], i) => (
                      <div className="stat" key={i}><div className="sl">{k}</div><div className="sv">{v}</div></div>
                    ))}
                  </div>
                  <div className="ld-risk"><AlertTriangle size={14} />{selLeaderObj.risk}</div>
                </div>
              )}
            </>
          ) : (
            <div className="ld-simple">주요종목: {sel.top}</div>
          )}
        </div>
      </div>
    </div>
  );
}

function WatchlistTable({ data }) {
  return (
    <div className="ld-section">
      <div className="ld-sec-head"><span className="ld-sec-num">F</span><h2 className="ld-h2">통합 워치리스트</h2></div>
      <div className="ld-watch-wrap">
        <table className="ld-table">
          <thead><tr><th>지표</th><th>트리거</th><th>상태</th><th>주기</th></tr></thead>
          <tbody>
            {data.watchlist.map((w, i) => (
              <tr key={i}>
                <td>{w.ind}</td>
                <td>{w.trig}</td>
                <td className={`sig-${w.sig}`}>{w.sig === "open" ? "● 우호" : "● 경계"}</td>
                <td className="ld-freq">{w.freq}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FreshnessBar() {
  return (
    <div className="ld-section" style={{ paddingTop: 22 }}>
      <div className="ld-sec-head"><span className="ld-sec-num">H</span><h2 className="ld-h2" style={{ fontSize: 15 }}>데이터 신선도</h2></div>
      <div className="ld-fresh">
        {FRESHNESS.map((f, i) => (
          <span className="ld-fresh-item" key={i}>
            <span className={`ld-fresh-dot ${f.stale ? "bad" : "ok"}`} />
            {f.label} · {f.last} ({f.freq})
          </span>
        ))}
      </div>
    </div>
  );
}

function Footer() {
  return (
    <div className="ld-footer">
      천장 밴드 · 여력 점수 · 주도주 랭킹은 시나리오 · 우선순위 프레임을 위한 정성 · 정량 산출이며 예측이 아닙니다. 투자 판단과 책임은 본인에게 있습니다.
      이 화면은 <b style={{ color: "var(--brass)" }}>스냅샷 프로토타입</b>이며, 실제 서비스는 FastAPI 백엔드가 FRED · pykrx · yfinance를 라이브 호출합니다 (스펙 §3, §8 Phase 0–5).
    </div>
  );
}

export default function App() {
  const [market, setMarket] = useState("KOSPI");
  const data = MARKETS[market];
  const rec = useMemo(() => reconciliation(data), [data]);

  return (
    <div className="ld-root">
      <style>{STYLES}</style>
      <div className="ld-proto-banner">
        <b>프로토타입</b> · 2026-06-20 스냅샷 데이터 · 통합 스펙 §2 레이아웃 구현 · 라이브 FastAPI 연동은 다음 단계
      </div>
      <GlobalMacroBar />
      <div className="ld-wrap">
        <Header market={market} setMarket={setMarket} data={data} />
        <CrossNarrativeBadge data={data} rec={rec} />
        <FlowSection data={data} />
        <LiquiditySection data={data} rec={rec} />
        <LeadershipSection key={market} data={data} />
        <WatchlistTable data={data} />
        <FreshnessBar />
        <Footer />
      </div>
    </div>
  );
}
