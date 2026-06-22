// Direct port of prototype Footer, with the legend updated to reflect that this build
// is now wired to the live FastAPI contract (not a static snapshot prototype).
interface FooterProps {
  mode: "mock" | "live";
  source: string;
}

export default function Footer({ mode, source }: FooterProps) {
  return (
    <div className="ld-footer">
      천장 밴드 · 여력 점수 · 주도주 랭킹은 시나리오 · 우선순위 프레임을 위한 정성 · 정량 산출이며 예측이 아닙니다. 투자 판단과 책임은 본인에게
      있습니다.
      <br />
      이 화면은 FastAPI 백엔드({source})에 연결된 <b style={{ color: "var(--brass)" }}>{mode === "live" ? "라이브" : "mock"}</b> 데이터입니다
      (_mode: {mode}).
    </div>
  );
}
