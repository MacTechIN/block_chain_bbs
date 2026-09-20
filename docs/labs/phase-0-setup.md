# Phase 0 랩 — 기반 세팅

> 랩 템플릿·힌트 규칙·에스컬레이션은 [학습계획서](../03-학습계획서.md)에 있다.
> Phase 0의 목표와 DoD는 [개발계획서 Phase 0](../01-개발계획서.md#phase-0--기반-세팅-05일)에 있다.
> 체크와 회고는 [PROGRESS.md](../PROGRESS.md)에 기록한다.

**이 Phase에는 블록체인이 없다.** 그런데도 맨 앞에 있는 이유는 하나다.
앞으로 모든 Phase의 완료 판정이 **"테스트가 통과하는가"**이기 때문이다.
판정기 없이 시작하면, 체인이 깨졌는지를 매번 눈으로 확인하다가 지친다.

랩 3개, 반나절이면 끝난다. 여기서 시간을 끌지 마라.

---

## Lab 0.1 — 실패하는 테스트부터 보기

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 30분 | 없음 | `tests/test_smoke.py`, 초록 1개 | ★☆☆☆☆ |

### 0. 왜 이게 필요한가

앞으로 "체인이 망가졌는지"를 판단해야 하는 순간이 수백 번 온다.
그때마다 터미널에 출력을 찍어 눈으로 비교할 것인가? 블록이 10개일 땐 되고 200개일 땐 안 된다.
그리고 눈으로 보는 판정은 **어제의 나와 오늘의 나가 다른 기준을 쓴다.**
기계가 판정하게 만들어 두고 시작한다.

### 1. 먼저 깨져보기 ⚔

방어 없는 상태 = **테스트가 아예 없는 상태**다. 이 상태가 왜 위험한지 30초 만에 본다.

해볼 것:
1. `src/bbschain/__init__.py`에 아무 함수나 하나 만든다. 예를 들어 두 수를 더하는 함수.
2. 손으로 한 번 실행해서 "잘 되네" 확인한다.
3. 이제 그 함수를 **일부러 틀리게 고친다** (`+`를 `-`로).
4. 아무것도 실행하지 말고 그냥 다음 작업을 시작한다고 상상한다.

네가 봐야 할 것: **아무 일도 일어나지 않는다.** 경고도, 빨간 줄도 없다.
코드는 조용히 틀린 채로 남는다. 이게 테스트가 없는 상태의 기본값이다.

> **질문 (PROGRESS.md에 3줄로)**: 이 "조용한 틀림"이 Phase 1에서 일어나면 어떻게 되나?
> 블록 해시 계산이 미묘하게 틀린 채로 블록 50개를 쌓았다고 해 보자. 언제 알아차리게 될까?

### 2. 사전지식 체크

1. `pytest`는 어떤 파일과 어떤 함수를 테스트로 인식하나? (규칙을 정확히)
2. `assert`가 실패하면 파이썬은 무엇을 던지나? pytest는 그걸로 뭘 하나?
3. 테스트가 **실패하는 것을 먼저 보고** 나서 고치는 순서를 왜 권하나?

못 답하겠으면 → [기술리서치 #pytest](../02-기술리서치.md#pytest)

### 3. 과제

`tests/test_smoke.py`를 만든다.

```python
def test_package_imports() -> None:
    ...

def test_version_is_declared() -> None:
    ...
```

**만족해야 할 불변식**
- `import bbschain`이 예외 없이 성공한다.
- `bbschain.__version__`이 문자열로 존재한다.
- **반드시 실패하는 것을 한 번 본 다음** 통과시킨다. (먼저 `__version__` 없이 테스트를 돌려 빨강을 본다)

### 4. 힌트

<details><summary>L1 — 방향</summary>

패키지가 `src/` 아래 있으면 그냥은 import가 안 된다. 왜 안 되는지부터 생각하라.
"설치"라는 단어가 힌트다.
</details>

<details><summary>L2 — 구조</summary>

- `src/bbschain/__init__.py`에 버전 문자열을 선언한다.
- 테스트 파일은 `tests/` 아래 둔다.
- 테스트가 패키지를 찾으려면 패키지가 현재 환경에 설치돼 있어야 한다 (editable install).
  Lab 0.2에서 `pyproject.toml`로 이 문제를 제대로 푼다. 지금은 실패를 보는 게 목적이다.
</details>

<details><summary>L3 — 의사코드</summary>

```
test_package_imports:
    bbschain 모듈을 import 한다
    import 자체가 성공하면 통과 (별도 assert 불필요하면 모듈이 None 아님을 확인)

test_version_is_declared:
    bbschain 에서 __version__ 을 읽는다
    그 값이 str 타입인지 assert
    빈 문자열이 아닌지 assert
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| `ModuleNotFoundError: No module named 'bbschain'` | src 레이아웃인데 패키지가 설치되지 않음 → Lab 0.2에서 해결 |
| 테스트가 0개 수집됨 (`collected 0 items`) | 파일명이 `test_*.py`가 아니거나 함수명이 `test_`로 시작하지 않음 |
| `import bbschain` 이 되는데 `__version__`이 없다 | `__init__.py`가 비어 있음 |

### 6. 검증

```
uv run pytest tests/test_smoke.py -v
```

통과해야 할 테스트:
- `test_package_imports`
- `test_version_is_declared`

**눈으로 확인**: 터미널 마지막 줄이 **`2 passed`** 초록. 그 전에 빨강(`2 failed`)을 한 번 봤어야 한다.

### 7. 실제 체인에서는

비트코인 코어와 go-ethereum 모두 합의 규칙에 대한 테스트 스위트를 별도로 관리한다.
특히 **합의 규칙을 바꾸는 변경은 테스트 없이는 머지되지 않는다** — 규칙이 한 노드에서만 달라지면
그 노드는 네트워크에서 떨어져 나가기 때문이다. 우리가 Phase 5에서 겪을 일이다.
→ [기술리서치 #레퍼런스-테스트](../02-기술리서치.md#레퍼런스-테스트)

### 8. 더 파보기

1. `pytest -x`, `pytest -k <패턴>`, `pytest --lf`가 각각 뭘 하는지 직접 써 보고 언제 쓸지 정리한다.
2. `conftest.py`가 무엇인지 찾아본다. Phase 1에서 바로 쓰게 된다.

### 9. 회고 3줄

[PROGRESS.md](../PROGRESS.md) 회고 영역에 기록한다.

---

## Lab 0.2 — uv 프로젝트와 src 레이아웃

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 1시간 | Lab 0.1 | `pyproject.toml`, `uv.lock`, ruff/mypy 설정 | ★★☆☆☆ |

### 0. 왜 이게 필요한가

Lab 0.1의 `ModuleNotFoundError`를 매번 `sys.path` 조작이나 `PYTHONPATH`로 때우면,
**내 컴퓨터에서만 되는 프로젝트**가 된다. Phase 7에서 Docker 컨테이너 안에 올리는 순간 전부 터진다.
"설치 가능한 패키지"로 만들어 두면 그 문제가 통째로 사라진다.

### 1. 먼저 깨져보기 ⚔

해볼 것:
1. Lab 0.1의 테스트를 `python -m pytest`로 프로젝트 루트에서 돌려 본다 → 아마 된다(운 좋게).
2. 이제 **다른 디렉터리로 이동해서** 같은 테스트 파일을 절대경로로 지정해 돌려 본다.
3. 혹은 `src/`를 `source/`로 이름만 바꿔 본다.

네가 봐야 할 것:
```
ModuleNotFoundError: No module named 'bbschain'
```
**어디서 실행하느냐에 따라 결과가 달라진다.** 이건 코드의 문제가 아니라 환경의 문제다.

> **질문**: 2번에서는 되고 3번에서는 안 됐다면(혹은 그 반대라면), 파이썬은 `bbschain`을 **어디서** 찾고 있었나?

### 2. 사전지식 체크

1. src 레이아웃(`src/pkg/`)과 flat 레이아웃(`pkg/`)의 차이는? src 레이아웃이 막아 주는 사고는?
2. editable install(`-e`)은 일반 설치와 무엇이 다른가?
3. 락 파일(`uv.lock`)은 왜 커밋해야 하나? `pyproject.toml`의 버전 범위만으로는 왜 부족한가?

→ [기술리서치 #패키징](../02-기술리서치.md#패키징)

### 3. 과제

`pyproject.toml`을 작성한다. 포함해야 할 것:

- 프로젝트 메타데이터: name `bbschain`, requires-python `>=3.12`
- 빌드 설정: src 레이아웃 인식
- 의존성: 지금은 비워도 된다 (`pytest`, `ruff`, `mypy`, `hypothesis`는 dev 그룹)
- 콘솔 스크립트 진입점 `bbschain` (Phase 1에서 CLI가 붙을 자리. 지금은 선언만)
- `[tool.ruff]` — line-length, 대상 파이썬 버전
- `[tool.mypy]` — `src/bbschain/core/`만 strict

**만족해야 할 불변식**
- 저장소를 새로 clone한 사람이 `uv sync` → `uv run pytest` 두 명령으로 초록을 본다.
- 어느 디렉터리에서 실행해도(프로젝트 루트 기준 `uv run`) 결과가 같다.
- `uv.lock`이 생성되고 커밋된다.

### 4. 힌트

<details><summary>L1 — 방향</summary>

`uv init --lib`가 만들어 주는 뼈대를 먼저 보고, 거기서 필요한 것만 남겨라.
dev 의존성은 `uv add --dev`로 넣는다.
</details>

<details><summary>L2 — 구조</summary>

`pyproject.toml`에 들어갈 섹션:
- `[project]` — name, version, requires-python, dependencies
- `[project.scripts]` — `bbschain = "bbschain.cli:main"` (cli 모듈은 Phase 1에 생김. 지금 선언하면 import 에러가 나므로 **주석으로 남겨 두거나 빈 `cli.py`를 만든다** — 어느 쪽이 나은지 직접 판단)
- `[build-system]` — hatchling 등
- `[tool.hatch.build.targets.wheel]` 또는 동등한 설정으로 `src` 지정
- `[dependency-groups]` 또는 `[tool.uv]`의 dev 의존성
- `[tool.ruff]`, `[tool.mypy]`
</details>

<details><summary>L3 — 의사코드</summary>

```
1. uv init 으로 뼈대 생성
2. src/bbschain/ 로 패키지 이동 확인, __init__.py 에 __version__ 선언
3. build-system 에 src 레이아웃을 알려 주는 설정 추가
4. uv add --dev pytest ruff mypy hypothesis
5. uv sync  →  .venv 생성 + uv.lock 생성
6. uv run pytest  →  Lab 0.1 테스트가 이제 통과하는지 확인
7. uv run ruff check  →  경고가 나오면 전부 해소
8. mypy 설정에서 core 디렉터리만 strict 로 지정 (아직 디렉터리는 없어도 됨)
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| `uv sync` 후에도 `ModuleNotFoundError` | build-system이 `src/`를 패키지 루트로 인식하지 못함 |
| `uv run pytest`가 시스템 파이썬을 씀 | `.venv`가 만들어지지 않았거나 `uv run` 없이 실행 |
| ruff가 수백 개 경고 | line-length 등 기본값과 기존 코드가 충돌 → 설정을 먼저 정하고 포맷 |
| `bbschain` 콘솔 스크립트 설치 실패 | 진입점이 가리키는 `cli:main`이 아직 없음 |
| `uv.lock`을 `.gitignore`에 넣음 | 애플리케이션은 락을 커밋한다. 라이브러리와 규칙이 다르다 |

### 6. 검증

```
uv sync
uv run pytest -v
uv run ruff check
uv run mypy src/
```

**눈으로 확인**: 네 명령이 전부 성공. 특히 `uv run pytest`가 **`src/` 어디서든 같은 결과**를 낸다.

### 7. 실제 체인에서는

노드 소프트웨어는 결국 **여러 사람의 컴퓨터에서 완전히 같게 동작해야** 하는 프로그램이다.
버전이 미묘하게 다른 라이브러리가 해시 결과를 바꾸면 그 노드는 체인에서 갈라진다.
락 파일은 그 위험을 줄이는 최소 장치다. Phase 7에서 Docker 이미지를 만들 때 이 결정이 다시 나온다.

### 8. 더 파보기

1. `uv export`로 requirements.txt를 뽑아 보고, Docker 멀티스테이지 빌드에서 왜 쓸모가 있는지 생각해 본다.
2. ruff의 규칙 세트(`select`)를 기본값보다 넓혀 보고, 어떤 규칙이 도움이 되고 어떤 게 방해인지 판단한다.

### 9. 회고 3줄

---

## Lab 0.3 — CI를 초록으로

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 1시간 | Lab 0.2 | `.github/workflows/ci.yml`, 초록 체크 | ★★☆☆☆ |

### 0. 왜 이게 필요한가

로컬에서 초록인 것과 **깨끗한 환경에서 초록인 것**은 다르다.
내 컴퓨터에는 옛날에 설치해 둔 패키지, 손으로 만든 환경변수, 지우다 만 캐시가 있다.
CI는 매번 빈 컴퓨터에서 시작한다. Phase 7에서 서버에 올릴 때 겪을 일을 **미리, 매 커밋마다** 겪어 두는 장치다.

### 1. 먼저 깨져보기 ⚔

해볼 것:
1. `uv.lock`을 임시로 `.gitignore`에 추가하고 커밋해 본다 (실제로 push는 하지 않아도 된다).
2. 혹은 `pyproject.toml`의 dev 의존성 하나를 지우고 `uv run pytest`를 돌려 본다.
3. 임시 디렉터리에 저장소를 clone해서 `uv sync && uv run pytest`를 그대로 돌려 본다.

네가 봐야 할 것: **내 디렉터리에서는 되는데 새로 clone한 곳에서는 안 되는 상태.**
이게 "내 컴퓨터에서는 되는데요"의 실물이다.

> **질문**: 3번에서 실패했다면, 내 작업 디렉터리에 있고 clone본에 없는 것은 무엇인가?
> (`git status --ignored`로 확인해 본다)

### 2. 사전지식 체크

1. GitHub Actions에서 워크플로가 **언제** 돌게 되어 있나? (트리거 이벤트)
2. CI 러너에는 uv가 설치돼 있나? 없다면 어떻게 넣나?
3. 테스트가 CI에서만 실패하고 로컬에서 통과한다면, 가장 먼저 의심할 것 3가지는?

→ [기술리서치 #ci](../02-기술리서치.md#ci)

### 3. 과제

`.github/workflows/ci.yml`을 작성한다.

**만족해야 할 불변식**
- `main`으로의 push와 모든 PR에서 실행된다.
- Python 3.12를 쓴다.
- `uv sync` → `uv run ruff check` → `uv run pytest` 순서로 돌고, **하나라도 실패하면 빨강**이다.
- 로컬에서 실패하는 커밋은 CI에서도 실패한다 (같은 판정기여야 한다).

`.gitignore`와 `LICENSE`, `README.md`도 이 랩에서 확정한다.
특히 **`.gitignore`에 `*.key`, `keystore/`, `.env`가 들어 있는지 반드시 확인한다** — Phase 3에서 개인키가 생기는데,
그때 가서 추가하면 이미 늦을 수 있다.

### 4. 힌트

<details><summary>L1 — 방향</summary>

astral-sh가 공식 setup 액션을 제공한다. 직접 curl로 설치하지 않아도 된다.
캐시 설정을 켜면 두 번째 실행부터 빨라진다.
</details>

<details><summary>L2 — 구조</summary>

워크플로 뼈대:
- `on:` — push(branches: main), pull_request
- `jobs.test.runs-on: ubuntu-latest`
- steps: checkout → uv 설치 → python 버전 고정 → `uv sync --locked` → ruff → pytest

`--locked`를 쓰는 이유를 스스로 설명할 수 있어야 한다. (락과 pyproject가 어긋나면 CI가 실패해야 하나 말아야 하나?)
</details>

<details><summary>L3 — 의사코드</summary>

```
on:
  push to main
  pull_request

job "test":
  runs-on ubuntu-latest
  step 1: actions/checkout
  step 2: astral-sh/setup-uv  (enable-cache: true)
  step 3: uv python install 3.12   (또는 setup-uv 옵션으로 지정)
  step 4: run "uv sync --locked --all-groups"
  step 5: run "uv run ruff check"
  step 6: run "uv run pytest -v"
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| CI에서 `uv: command not found` | setup 액션 단계가 빠졌거나 순서가 뒤바뀜 |
| `uv sync --locked` 실패 | `uv.lock`이 커밋 안 됐거나 `pyproject.toml` 수정 후 재생성 안 됨 |
| 로컬은 통과, CI는 실패 | 커밋 안 된 파일에 의존 / 절대경로 사용 / 환경변수 의존 |
| 워크플로가 아예 안 돌음 | 파일 경로가 `.github/workflows/`가 아님, 또는 YAML 들여쓰기 오류 |
| 커밋했더니 `*.key`가 올라감 | `.gitignore` 추가 **전에** 이미 추적 중이던 파일. `git rm --cached` 필요 |

### 6. 검증

```
uv run ruff check
uv run pytest
```
그리고 push 후 GitHub의 Actions 탭.

**눈으로 확인**: GitHub 커밋 목록에서 내 커밋 옆에 **초록 체크 ✓**.
일부러 테스트 하나를 깨뜨려 push하면 **빨간 ✗**가 뜨는 것까지 확인한다. 둘 다 봐야 판정기를 믿을 수 있다.

### 7. 실제 체인에서는

대형 체인 프로젝트의 CI는 단위 테스트뿐 아니라 **합의 테스트 벡터**(같은 입력에 같은 블록 해시가 나오는지)를
매 커밋 검증한다. 우리도 Phase 1에서 "고정 시각을 주입하면 글 10개 → 같은 머클 루트"를 DoD로 잡는데, 성격이 같은 검사다.

### 8. 더 파보기

1. CI에 `mypy` 단계를 추가하면 어디까지 strict로 갈 수 있는지 시험해 본다.
2. 매트릭스 빌드(3.12 / 3.13)를 켜 보고, 파이썬 버전 차이가 해시 결과에 영향을 줄 수 있는지 생각해 본다.
   (힌트: `dict` 순서, `json.dumps` 기본값 — Phase 1 ADR-0001의 주제다)

### 9. 회고 3줄

---

## Phase 0 마무리

세 랩을 끝냈으면 [PROGRESS.md](../PROGRESS.md)에서 Phase 0의 랩 3개와 DoD 5개를 켠다.
**"보여줄 수 있는 한 장면"**에는 초록 CI 체크 스크린샷을 남긴다.

다음 → [Phase 1 랩](phase-1-chain.md)
