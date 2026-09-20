# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 상태

**Phase 0(기반 세팅) 스캐폴딩은 끝났다. 블록체인 구현 코드는 아직 없다 — Phase 1부터 사용자가 만든다.**

- 있는 것: `README.md`, `LICENSE`, `.gitignore`, `docs/` 문서 3종 + `docs/labs/` + `docs/decisions/`,
  `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`,
  `src/bbschain/__init__.py`(버전만) + `src/bbschain/cli.py`(**Phase 0 스텁**, Lab 1.5에서 사용자가 교체),
  `tests/test_smoke.py`(초록 2개) + Phase 1용 선작성 테스트 8개
- 없는 것: `src/bbschain/core/`, `storage/`, `wallet/` … — **Phase 1 이후 랩에서 사용자가 직접 만든다**
- ⚠️ Phase 0의 세 랩(0.1/0.2/0.3)은 **사용자 요청에 따라 에이전트가 대신 구현했다.**
  기록은 [docs/PROGRESS.md](docs/PROGRESS.md)에 있다.
- git 저장소는 초기화되어 있고 origin이 연결되어 있다 (기본 브랜치 `main`). **커밋은 0개이고, 첫 커밋은 사용자가 직접 한다.**

현재 진행 상황은 항상 [docs/PROGRESS.md](docs/PROGRESS.md)가 정본이다. 이 파일이 아니라 거기를 먼저 읽어라.

### 기술 스택 (확정)

| 항목 | 결정 |
|---|---|
| 패키지 / 런타임 | **uv + Python 3.12**, src 레이아웃 (`src/bbschain/`) |
| 웹 / API | FastAPI + uvicorn (Phase 2부터) |
| 템플릿 / 프런트 | Jinja2 + HTMX + SSE |
| 저장소 | Phase 1 JSON 파일 → Phase 2 **SQLite** (표준 `sqlite3`, ORM 없음) |
| 테스트 | **pytest** + pytest-asyncio + hypothesis |
| 품질 | ruff + mypy (`core/`만 strict) |

전체 스택 표와 근거는 [개발계획서 5절](docs/01-개발계획서.md#5-기술-스택).

### 빌드 / 테스트 / 린트 명령

아래 명령은 **Phase 0 완료 시점에 실제로 실행해 확인한 것들이다.**

```
uv sync                                       # 의존성 설치 (.venv + uv.lock)
uv sync --locked --all-groups                 # CI와 동일한 설치 (락이 어긋나면 실패)

uv run pytest                                 # 기본 실행 — 스모크만 (초록이어야 한다)
uv run pytest tests/unit/test_merkle.py -v    # 단일 파일 (명시하면 Phase 1 테스트도 돈다)
uv run pytest tests/unit -v                   # Phase 1 단위 테스트 전부
uv run pytest tests/unit/test_merkle.py -k "proof"   # 테스트 함수 이름으로 필터
uv run pytest tests/unit/test_merkle.py::test_merkle_root_single_leaf   # 함수 하나만

uv run ruff check                             # 린트
uv run ruff check --fix                       # 자동 수정 가능한 것만 고침
uv run mypy src/                              # 타입 체크 (core/ 만 strict)

uv run bbschain --help                        # Phase 0 스텁 — 안내만 내고 종료 코드 2
```

⚠️ **`uv run pytest`는 스모크 테스트만 돈다.**
`pyproject.toml`의 `[tool.pytest.ini_options] testpaths = ["tests/test_smoke.py"]` 때문이다.
`tests/unit/`·`tests/integration/`의 Phase 1 테스트는 **구현이 없어 전부 실패하는 것이 정상**이므로
기본 실행(= CI 판정기)에서 빼 두었다. `testpaths`는 **인자를 주지 않았을 때만** 적용되므로
경로를 명시하면 그대로 수집된다 — 위 단일 파일/단일 함수 명령이 그래서 동작한다.
실패 메시지에는 "어느 랩에서 무엇을 만들면 초록이 되는지"가 배너로 찍힌다 (`tests/conftest.py`).

**Phase 1 구현이 끝나면** `testpaths`를 `["tests"]`로 되돌려 CI가 전부 판정하게 한다.

## 프로젝트 목표 (docs/개발요구서.md 요약)

블록체인을 **학습**하기 위한 프로젝트다. 작은 블록체인 기반 BBS(게시판)를 직접 만들고, 앱으로 배포·테스트하며,
반복 업그레이드하는 과정에서 블록체인 기법을 익히는 것이 목적이다.

요구서가 명시한 산출물:

1. **개발 계획서** — 단계별로 어떤 기능을 만들며 무엇을 배우는지
2. **기술 리서치 문서** — GitHub의 기존 코드를 검색해 참고 구현·사용법·응용법을 기록
3. **학습 계획서** — 사용자가 직접 해보도록 유도하는 형식 (완성 코드를 대신 써주는 것이 아니라 실습 과제와 힌트 위주)

작업 방식에 대한 함의:

- 사용자는 **직접 손으로 해보며 배우는 것**을 원한다. 구현을 통째로 대신하기보다 설계·과제·검증 기준을 제시하고, 사용자가 시도한 결과를 리뷰하는 방향을 우선한다.
- 문서는 `docs/` 아래에 두고 한국어로 작성한다. 코드 식별자·주석·커밋 메시지는 영어.
- "작게 시작해서 업그레이드" 흐름이므로 첫 단계는 최소 블록체인(블록·해시·체인 검증) 수준으로 잡고, 합의·P2P·지갑·스마트컨트랙트 등은 이후 단계로 미룬다.

---

## ⚠️ 가장 중요한 규칙 — 랩 과제를 대신 구현하지 않는다

**학습 랩의 대상이 되는 모듈(`src/bbschain/` 아래 `core`, `wallet`, `consensus`, `mempool`, `p2p`, `storage` 등)은
사용자가 직접 구현한다.**

에이전트가 하는 일 / 하지 않는 일:

| 에이전트가 한다 ✅ | 에이전트가 하지 않는다 ❌ |
|---|---|
| 랩의 테스트를 **미리 작성**한다 (사용자가 통과시킬 대상) | 그 테스트를 통과하는 구현을 작성한다 |
| 사용자가 쓴 코드를 **리뷰**한다 (버그·엣지케이스·설계 지적) | "이렇게 고치면 됩니다" 하고 수정된 전체 코드를 준다 |
| 스캐폴딩 — 설정 파일, 디렉터리 골격, CI 워크플로, `__init__.py` | 랩 과제 모듈의 함수 본문을 채운다 |
| 문서 작성·갱신 (계획서·랩·ADR·PROGRESS) | 랩 문서에 정답 코드를 싣는다 (힌트는 **L3 의사코드까지만**) |
| 막힌 지점에 대해 **질문으로 유도**한다 | 답을 바로 알려준다 |

**예외는 하나다**: 사용자가 명시적으로 **"이건 대신 짜줘"**라고 요청한 경우.
그때도 어느 모듈을 대신 구현했는지 [docs/PROGRESS.md](docs/PROGRESS.md)에 기록한다.
나중에 그 모듈이 자기 손으로 만든 것이 아님을 알아야 하기 때문이다.

**범위 밖이라 자유롭게 구현해도 되는 것**: `deploy/`의 Docker·compose 설정, `.github/workflows/`,
탐색기 템플릿의 순수 CSS/레이아웃, `labs/` 안의 측정·시각화 보조 스크립트.
단 이것들도 해당 랩이 "직접 해볼 것"으로 지정했다면 범위 안이다.

에스컬레이션 규칙(30분 → L1 → 1시간 → L2 → 2시간 → L3 → 리뷰 요청, **정답 요청 금지**)은
[학습계획서 5절](docs/03-학습계획서.md#5-막혔을-때-에스컬레이션-규칙)에 있다.

---

## 문서 3종의 역할 경계 (중복 금지)

| 문서 | 역할 | 여기에만 쓰는 것 |
|---|---|---|
| [docs/01-개발계획서.md](docs/01-개발계획서.md) | **WHAT / WHEN** | Phase 범위, DoD, 기술 스택 결정, 코드 구조, 아키텍처 계약, 위험 |
| [docs/02-기술리서치.md](docs/02-기술리서치.md) | **WHY** | 외부 URL, GitHub 레퍼런스 카드, 라이브러리 비교, 사양 원문, 긴 개념 해설 |
| [docs/03-학습계획서.md](docs/03-학습계획서.md) + [docs/labs/](docs/labs/) | **HOW** | 실습 절차, 힌트 3단, 검증 기준, 랩 템플릿 |
| [docs/PROGRESS.md](docs/PROGRESS.md) | **NOW** | 체크박스, 회고, 막힌 지점 로그 (가변 상태) |
| [docs/decisions/](docs/decisions/) | **결정 1건 = 1파일** | 맥락 / 대안 / 결정 / 결과 |

**중복 방지 규칙**
- 같은 내용을 두 문서에 쓰지 않는다. 필요하면 **한 곳에 두고 나머지는 앵커 링크**를 건다.
- 외부 링크는 **기술리서치에만** 둔다. 다른 문서는 `→ [기술리서치 #앵커](02-기술리서치.md#앵커)` 형태로만 참조한다.
- DoD는 계획서가 정본이고 PROGRESS.md는 복사본이다. **기준이 바뀌면 계획서를 고치고**, 진행이 바뀌면 PROGRESS를 고친다.
- 랩 문서에 Phase 범위나 DoD를 다시 쓰지 않는다. 계획서로 링크한다.
- **기간·주차를 쓰지 않는다.** "1주차" 금지. Phase와 DoD로만 진행을 표현한다. 예상 소요는 괄호 안 참고용.
- 문서는 한국어. 코드 식별자·명령어·파일 경로는 영어 그대로.

## 오케스트레이션 워크플로

이 저장소에는 `orchestrator` 스킬과 전용 워커 에이전트가 설정되어 있다. 요구서도 "오케스트레이션으로" 진행하라고 명시한다.

| 에이전트 | 역할 | 쓰기 권한 |
|---|---|---|
| `architect` | 변경 설계, 영향 범위·수정 파일·인터페이스 정리 | 없음 |
| `implementer` | 실제 코드 작성·수정 (유일한 구현 워커) | 있음 |
| `test-writer` | 구현된 코드에 기존 테스트 스타일로 테스트 추가·실행 | 있음 |
| `code-reviewer` | 정확성·동시성·에러 처리·보안 리뷰, 발견 사항만 보고 | 없음 |

다단계 작업은 `/orchestrator`로 시작해 architect → implementer → test-writer → code-reviewer 순으로 위임하고, 단계 경계마다 사용자 확인을 받는다.

## git 규칙

- **에이전트는 `git commit` / `git push`를 하지 않는다.** 커밋은 사용자가 직접 한다 (랩 단위 커밋이 기본).
- 기본 브랜치는 `main`. origin은 `https://github.com/MacTechIN/block_chain_bbs.git`.
- 커밋 전 `git status`로 `*.key`, `.env`, `keystore/`가 올라가지 않는지 확인한다.
  Phase 3부터 개인키가 실제로 생기므로 습관이 필요하다.

## 이 파일을 갱신해야 할 시점

- **Phase 0 완료 시**: 위 명령 블록이 실제로 도는지 확인하고 확정
- **Phase가 넘어갈 때**: 프로젝트 상태 섹션의 현재 Phase 표기
- **첫 아키텍처가 잡힐 때**: 블록/체인/저장소/네트워크/UI 모듈 경계와 데이터 흐름
  (단, 상세 구조는 [개발계획서 6절](docs/01-개발계획서.md#6-코드-구조)이 정본. 여기엔 요약만)
- **기술 스택이 바뀔 때**: 먼저 `docs/decisions/`에 ADR을 쓰고, 계획서를 고치고, 마지막에 여기를 고친다

진행 상황·체크박스·회고는 **이 파일이 아니라** [docs/PROGRESS.md](docs/PROGRESS.md)에 쓴다.
