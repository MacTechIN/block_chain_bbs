# Lab 0.2 따라하기 — uv 프로젝트와 src 레이아웃

| 대응 랩 | 이론 | 예상 소요 |
|---|---|---|
| [docs/labs/phase-0-setup.md#Lab 0.2](../../docs/labs/phase-0-setup.md#lab-02--uv-프로젝트와-src-레이아웃) | [튜토리얼 Lab 0.2](../../docs/tutorial/phase-0.md#lab-02--uv-프로젝트와-src-레이아웃) | 1시간 |

**이 랩이 만드는 것**: 파이썬이 우리 패키지를 **언제나 같은 곳에서** 찾게 만드는 설정이다.

> 참고 문서 — 막히면 여기로.
> [설정 가이드](설정-가이드.md) · [테스트 실행법](../테스트-실행법.md)

> ## 이 랩은 이미 완료된 상태다
>
> `pyproject.toml`, `uv.lock`, `.venv/`, `src/bbschain/cli.py`가 전부 **에이전트 대행**으로 이미 있다
> ([PROGRESS.md 기록](../../docs/PROGRESS.md#phase-0--기반-세팅)).
>
> **직접 해보고 싶으면 — 무엇을 지우면 출발 상태가 되나**
>
> 이 랩의 산출물은 네 가지다: `pyproject.toml`, `uv.lock`, `.venv/`, `src/bbschain/cli.py`.
> 그런데 **`pyproject.toml`을 지우면 `uv run`이 관리하던 프로젝트 자체가 사라진다.**
> 그래서 저장소를 건드리지 말고 **사본에서** 한다.
>
> ```
> mkdir -p /tmp/lab02 && cd /tmp/lab02
> cp -r <저장소>/src <저장소>/tests <저장소>/README.md <저장소>/LICENSE .
> uv run pytest            # pyproject.toml 이 없는 상태
> ```
>
> 실제로 나오는 출력이다.
>
> ```
> tests/test_smoke.py:10: in <module>
>     import bbschain
> E   ModuleNotFoundError: No module named 'bbschain'
> !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
> ```
>
> **이게 Lab 0.2가 고치는 상태다.** `/tmp/lab02`에서 `pyproject.toml`을 직접 써 나가고,
> 끝나면 저장소의 것과 비교해 보면 된다. **사본은 통째로 지워도 저장소에 영향이 없다.**
>
> 저장소에서 바로 해볼 수 있는 최소 재현은 아래 1절의 ④다. `src/` 이름만 바꿔 본다.
> 파일 내용은 한 글자도 안 바뀐다.

---

## 0. 준비

- [ ] 터미널을 **저장소 루트**에서 연다

**출발점이 초록인지 확인한다.**

```
uv run pytest
```

```
============================== 2 passed in 0.01s ===============================
```

- [ ] 확인했다

**지금 `bbschain`이 어느 파일에서 오는지 봐 둔다.** 1절에서 이게 깨진다.

```
uv run python -c "import bbschain; print(bbschain.__file__)"
```

```
/home/<너>/…/block_chain_bbs/src/bbschain/__init__.py
```

- [ ] 경로를 확인했다. **이 저장소 안의 파일**을 가리킨다

---

## 1. 먼저 깨져보기 ⚔

**보려는 것**: 코드는 한 글자도 안 바뀌었는데,
**어디서 어떻게 실행하느냐에 따라 결과가 갈리는 것.**

### ① 저장소 루트에서 — 기준점

```
uv run pytest tests/test_smoke.py
```

```
============================== 2 passed in 0.01s ===============================
```

- [ ] 된다

### ② 완전히 다른 디렉터리에서, 절대경로로

**`uv run`을 붙여서 돌리면 어떻게 될까.** 먼저 예상해 보고 돌려라.

```
cd /tmp
uv run --project <저장소 절대경로> pytest <저장소 절대경로>/tests/test_smoke.py
```

```
============================== 2 passed in 0.01s ===============================
```

- [ ] 된다. **폴더를 옮겼는데도 결과가 같다**

### ③ 같은 자리에서 uv를 빼고 시스템 파이썬으로

**`uv run`이 없으면 어떻게 될까.** 이것도 예상해 보고 돌려라.

```
cd /tmp
python3 -m pytest <저장소 절대경로>/tests/test_smoke.py
```

```
ImportError while loading conftest '…/tests/conftest.py'.
E   ImportError:
E   hypothesis 가 설치돼 있지 않다. Phase 1 의 property 테스트에 필요하다.
E     uv add --dev hypothesis   (Lab 0.2 에서 pytest/ruff/mypy 와 함께 넣는 그 의존성이다)
E   원인: No module named 'hypothesis'
```

- [ ] 깨진다

**여기서 두 가지를 알 수 있다.** 시스템 파이썬에는 `hypothesis`가 없다.
그리고 **`.venv` 안의 것들은 `uv run`을 거쳐야 보인다.**

> 이 화면에서 pytest 자체가 없다는 에러가 날 수도 있다. 컴퓨터마다 다르다.
> **어느 쪽이든 결론은 같다.** 시스템 파이썬은 이 프로젝트의 환경이 아니다.

### ④ 저장소로 돌아와 `src/`를 이름만 바꿔 본다

**파일 내용은 그대로다. 폴더 이름만 바꾼다.**

```
cd <저장소 절대경로>
mv src source
uv run --no-sync pytest
```

```
tests/test_smoke.py:10: in <module>
    import bbschain
E   ModuleNotFoundError: No module named 'bbschain'
=========================== short test summary info ============================
ERROR tests/test_smoke.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

- [ ] 깨진다

> **`--no-sync`를 붙인 이유**: 이게 없으면 `uv run`이 먼저 환경을 고쳐 버린다.
> 깨진 상태를 보려고 하는 실험인데 고쳐지면 곤란하다.

**`FAILED`가 아니라 `ERROR`다.** 테스트가 시작도 못 한 것이다
(→ [테스트 실행법 — failed와 error는 다르다](../테스트-실행법.md#실패-메시지-읽는-순서)).

**📝 네가 본 것을 여기 적어라**

```
① 루트에서:
② 다른 디렉터리 + uv run:
③ 시스템 python3 -m pytest:
④ src -> source:

(코드는 한 글자도 안 바뀌었다. 무엇이 바뀌어서 결과가 갈렸나?)


```

**되돌린다.**

```
mv source src
uv run --no-sync pytest
```

```
============================== 2 passed in 0.01s ===============================
```

- [ ] `2 passed`로 돌아왔다

**📝 랩의 질문**

> ②에서는 되고 ④에서는 안 됐다면, 파이썬은 `bbschain`을 **어디서** 찾고 있었나?

```


```

---

## 2. 사전지식 — 답을 먼저 적고 나서 튜토리얼을 연다

> **못 답해도 괜찮다. 모른다고 적는 것도 답이다.**
> 적고 나서 읽어야 무엇을 몰랐는지가 남는다.

**Q1. src 레이아웃(`src/pkg/`)과 flat 레이아웃(`pkg/`)의 차이는? src 레이아웃이 막아 주는 사고는?**

```


```

**Q2. editable install(`-e`)은 일반 설치와 무엇이 다른가?**

```


```

**Q3. 락 파일(`uv.lock`)은 왜 커밋해야 하나? `pyproject.toml`의 버전 범위만으로는 왜 부족한가?**

```


```

- [ ] 답을 적었다 → 이제 [튜토리얼 Lab 0.2](../../docs/tutorial/phase-0.md#lab-02--uv-프로젝트와-src-레이아웃)를 읽는다
- [ ] 읽고 나서 위 답을 **고쳐 적었다** (틀린 답을 지우지 말고 옆에 정정하라)

### 손으로도 확인한다

**같은 한 줄을 여러 방식으로 실행하면 파이썬이 뒤지는 폴더가 매번 달라진다.**
그 차이를 한 화면에 보여 주는 스크립트다.

```
uv run python workbook/phase-0/experiments/02_sys_path.py
```

출력 중 이 부분이 이 랩의 핵심이다.

```
==============================================================================
② 이 저장소의 bbschain 은 어디 있는 파일인가
==============================================================================
    bbschain.__file__ = /home/<너>/…/src/bbschain/__init__.py
    저장소 루트에 bbschain/ 디렉터리가 있나? -> False
```

**저장소 루트에 `bbschain/` 폴더는 없다. 그런데도 import는 된다.**
그 연결을 만드는 물건이 바로 아래에 출력된다.

- [ ] 같은 한 줄이 실행 방식에 따라 다른 결과를 내는 것을 봤다
- [ ] `.pth` 파일 **한 줄**이 `src/`를 가리키는 것을 직접 봤다 — ④가 깨진 이유가 이 줄이다

**📝 예상과 달랐던 것**

```


```

---

## 3. 과제 — 무엇을, 어떤 순서로 쓰나

**만드는 파일**: `pyproject.toml` (그리고 그 결과로 `uv.lock`)
**정본은 랩 문서다** → [Lab 0.2 과제](../../docs/labs/phase-0-setup.md#lab-02--uv-프로젝트와-src-레이아웃)

> 이 시트에 과제 내용을 옮겨 적지 않는다.
> **저장소의 `pyproject.toml`을 열어 보는 것은 정답을 보는 것이다.**
> 직접 하려면 맨 위 박스대로 `/tmp/lab02` 사본에서 시작하라.

### 코드를 쓰는 순서

이번 산출물은 코드가 아니라 **설정 파일**이다. 그래도 순서는 같다.

**1단계 — 무엇이 이걸 검사하는지 먼저 확인한다.**
이 랩의 판정기는 `tests/test_smoke.py`다. `import bbschain`이 되는지를 본다.
**그러니 목표는 하나다.** "이 import가 성공하게 만드는 설정을 쓴다."

**2단계 — 만족해야 할 불변식을 확인한다.**
랩 3절에 세 줄이 있다. 한 줄씩 한국어로 다시 써 본다.
예: "새로 받은 사람이 두 명령만으로 초록을 본다."

**3단계 — 가장 단순한 것부터 채운다.**
절을 한꺼번에 다 쓰지 마라. **순서를 권하면 이렇다.**

```
[project]            먼저. 이름과 파이썬 버전만
[build-system]       그다음. src/ 를 알려 주는 설정까지
   → 여기서 uv sync 를 돌려 본다. import 가 되면 절반은 끝이다
[dependency-groups]  dev 의존성 (uv add --dev 로 넣으면 자동으로 적힌다)
[project.scripts]    진입점
[tool.ruff] [tool.mypy]   도구 설정은 마지막
```

각 절이 무슨 말인지는 → [설정 가이드 — pyproject.toml 읽기](설정-가이드.md#pyprojecttoml-읽기)

**4단계 — 한 절 쓸 때마다 돌린다.**

```
uv sync
uv run pytest
```

**전부 쓰고 한 번에 돌리면 어느 절이 문제인지 못 찾는다.**

**5단계 — 실패 메시지를 읽고 고친다.**
`ModuleNotFoundError`가 났다면 확인 순서가 정해져 있다.
→ [설정 가이드 — ModuleNotFoundError가 났을 때](설정-가이드.md#modulenotfounderror가-났을-때)

### 체크

- [ ] 포함해야 할 항목 목록과 **불변식**만 보고 `pyproject.toml`을 직접 썼다
- [ ] `[project.scripts]`의 진입점을 어떻게 처리할지 **스스로 판단했다** (랩 L2 힌트가 두 선택지를 준다)
- [ ] `uv.lock`이 생성되는지 확인했다

---

## 4. 막히면

규칙은 [학습계획서 5절](../../docs/03-학습계획서.md#5-막혔을-때-에스컬레이션-규칙)이 정본이다.

```
0~30분  자력 (에러 메시지를 끝까지 읽었나?)
  30분  L1 힌트 — 방향
  1시간  L2 힌트 — 구조
  2시간  L3 힌트 — 의사코드
그 이후  code-reviewer 에이전트에 리뷰 요청 (정답 요청 금지)
```

| | 연 시각 | 그때 막혀 있던 것 |
|---|---|---|
| L1 | | |
| L2 | | |
| L3 | | |
| 리뷰 요청 | | |

- [ ] 30분 넘게 막혔다면 [PROGRESS.md 막힌 지점 로그](../../docs/PROGRESS.md#막힌-지점-로그)에 **지금** 한 줄 적었다

---

## 5. 검증

**네 명령을 순서대로 돌린다.** 각각 무엇을 보는지 옆에 적었다.

```
uv sync                 # 환경을 pyproject/lock 상태로 맞춘다
uv run pytest -v        # 판정기가 초록인가
uv run ruff check       # 스타일 검사
uv run mypy src/        # 타입 검사
```

이렇게 나와야 한다.

```
tests/test_smoke.py::test_package_imports PASSED                         [ 50%]
tests/test_smoke.py::test_version_is_declared PASSED                     [100%]
============================== 2 passed in 0.01s ===============================

All checks passed!

Success: no issues found in 2 source files
```

- [ ] 네 명령 전부 확인했다
- [ ] **어느 디렉터리에서 `uv run` 해도 같은 결과**가 나오는지 1절 ②로 다시 확인했다
- [ ] `uv.lock`이 만들어졌고, `.gitignore`에 들어가 있지 **않다**

---

## 6. 눈으로 확인

**첫째 — import되는 파일이 복사본이 아니라 내가 고치는 그 파일인지 본다.**

```
uv run python -c "import bbschain; print(bbschain.__file__)"
```

```
/home/<너>/…/block_chain_bbs/src/bbschain/__init__.py
```

- [ ] `site-packages/...`가 아니라 **이 저장소의 `src/bbschain/__init__.py`** 를 가리킨다

**둘째 — 그 연결을 만드는 파일을 직접 열어 본다.**

```
cat .venv/lib/python3.12/site-packages/_editable_impl_bbschain.pth
```

```
/home/<너>/…/block_chain_bbs/src
```

- [ ] **한 줄짜리 파일**이다. 마법이 아니라 경로 하나가 적힌 텍스트 파일이다

**셋째 — 콘솔 스크립트가 설치됐는지 본다.**

```
uv run bbschain --help
```

```
bbschain CLI 는 아직 구현되지 않았다. Lab 1.5 (docs/labs/phase-1-chain.md) 를 보라.
이 파일(src/bbschain/cli.py)은 콘솔 스크립트 진입점을 살려 두기 위한 Phase 0 스텁이다.
```

- [ ] 안내 문구가 나온다

> Phase 0 스텁이라 안내를 내고 **종료 코드 2**로 끝난다. **그게 정상이다.**
> 실제 CLI는 Lab 1.5에서 직접 만든다.

**📝 `.pth` 파일을 직접 보고 든 생각**

```


```

---

## 7. 회고 3줄

```
배운 것:

헛짚은 것:

다음에 확인할 것:
```

---

## 8. 기록

- [ ] 위 회고 3줄을 [PROGRESS.md 회고 기록](../../docs/PROGRESS.md#회고-기록)에 옮긴다 (**정본은 PROGRESS.md다**)
- [ ] `docs/PROGRESS.md`의 `Lab 0.2` 체크박스를 켠다 (이미 켜져 있다 — 🤖를 떼고 직접 했다고 고쳐 적어라)
- [ ] 커밋한다

```
git status                 # *.key, .env, keystore/ 가 없는지 먼저 확인
git add pyproject.toml uv.lock src/bbschain/cli.py docs/PROGRESS.md
git commit -m "Lab 0.2: uv project with src layout and locked dev deps"
```

> ⚠️ **`uv.lock`을 빼먹지 마라.**
> 이 프로젝트는 라이브러리가 아니라 노드 소프트웨어다. **락을 커밋하는 쪽이다.**
> 다음 랩(CI)이 `--locked`로 그걸 강제한다.

---

다음 → [Lab 0.3 따라하기](lab-0.3.md)
