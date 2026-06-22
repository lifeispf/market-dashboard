# legacy/ — 1세대 프로토타입 (보관용, 미유지)

`app.py`는 `backend/`(FastAPI) + `frontend/`(React) 스택으로 넘어가기 전의
**1세대 Streamlit 프로토타입**이다. 화면 레이어(Streamlit)는 죽은 경로이며 더 이상
유지되지 않는다.

- `backend/`는 이 파일을 import하지 않는다 — 안전하게 격리됨.
- 단, 계산·데이터 레이어(`scoring.py`, `config_loader.py`, `data/*fetcher.py`)는
  **루트에 그대로 남아 `backend/`와 공유**된다. 여기로 옮기지 않는다.
- 참고용으로만 보관. 실행하려면 리포 루트에서 `sys.path`에 루트를 넣어야 import가 풀린다.

현행 앱은 `backend/main.py`(FastAPI) + `frontend/`(Vite)를 사용한다.
