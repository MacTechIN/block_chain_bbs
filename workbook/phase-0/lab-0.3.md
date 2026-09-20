# Lab 0.3 따라하기 — CI를 초록으로

| 대응 랩 | 이론 | 예상 소요 |
|---|---|---|
| [docs/labs/phase-0-setup.md#Lab 0.3](../../docs/labs/phase-0-setup.md#lab-03--ci를-초록으로) | [튜토리얼 Lab 0.3](../../docs/tutorial/phase-0.md#lab-03--ci를-초록으로) | 1시간 |

**이 랩이 만드는 것**: **빈 컴퓨터에서도** 초록인지 매번 자동으로 확인하는 장치다.

CI가 뭔가. **GitHub이 빌려주는 깨끗한 컴퓨터 한 대**다.
코드를 올리면 그 컴퓨터가 저장소를 새로 받아 내가 적어 둔 명령을 돌리고 결과를 알려 준다.

> 참고 문서 — 막히면 여기로.
> [설정 가이드](설정-가이드.md) · [테스트 실행법](../테스트-실행법.md)

> ## 이 랩은 이미 완료된 상태다
>
> `.github/workflows/ci.yml`, `.gitignore`, `LICENSE`, `README.md`가 전부 **에이전트 대행**으로 이미 있다
> ([PROGRESS.md 기록](../../docs/PROGRESS.md#phase-0--기반-세팅)).
>
> **직접 해보고 싶으면 — 무엇을 지우면 출발 상태가 되나**
>
> 이 랩의 산출물은 사실상 **파일 하나**다: `.github/workflows/ci.yml`.
> 지우는 대신 **확장자를 바꿔 치워 두면** 된다.
> GitHub Actions는 `.yml`과 `.yaml`만 워크플로로 인식하기 때문이다.
>
> ```
> mv .github/workflows/ci.yml .github/workflows/ci.yml.bak
> ```
>
> 이 상태에서도 로컬 명령은 **전부 그대로 돈다.**
> 달라지는 것은 하나뿐이다. **아무도 대신 돌려 주지 않는다.**
> 그게 이 랩이 채우는 빈칸이다.
>
> 되돌리려면 `mv .github/workflows/ci.yml.bak .github/workflows/ci.yml`.
>
> **`.gitignore`는 지우지 마라.** Phase 3에서 개인키가 생기기 전에 있어야 하는 파일이다.
> 이 랩에서 할 일은 새로 쓰는 것이 아니라 **확인하는 것**이다 (3절 참고).

---

## 0. 준비

- [ ] 터미널을 **저장소 루트**에서 연다

**CI가 돌릴 것과 똑같은 명령을 로컬에서 먼저 돌려 본다.**
여기서 실패하면 CI도 반드시 실패한다.

```
uv sync --locked --all-groups
uv run ruff check
uv run pytest -v
```

`uv sync`는 성공하면 거의 아무 말도 하지 않는다. 나머지 둘은 이렇게 나온다.

```
All checks passed!

tests/test_smoke.py::test_package_imports PASSED                         [ 50%]
tests/test_smoke.py::test_version_is_declared PASSED                     [100%]
============================== 2 passed in 0.01s ===============================
```

- [ ] 세 명령이 전부 성공했다

---

## 1. 먼저 깨져보기 ⚔

**보려는 것**: **"내 컴퓨터에서는 되는데요"의 실물.**
내 폴더에서는 초록인데 **새로 받은 곳에서는 안 되는 상태**를 손으로 만든다.

### ① 내 폴더에 있고 커밋본에는 없는 것이 무엇인지 본다

```
git status --ignored
git ls-files --others --exclude-standard
```

여기 나오는 것들이 곧 **"나만 가진 것"의 목록**이다.
`.venv/`, 캐시 폴더, 아직 커밋 안 한 파일이 보일 것이다.

- [ ] 목록을 봤다

**테스트가 이 목록 중 뭔가를 읽고 있다면 CI에서 터진다.** 지금은 그렇지 않다.

### ② 임시 디렉터리에 복사해서 CI와 같은 순서로 돌려 본다

```
git clone <저장소 절대경로> /tmp/lab03-clone
cd /tmp/lab03-clone
uv sync --locked --all-groups
uv run pytest
```

```
============================== 2 passed in 0.01s ===============================
```

- [ ] 사본에서도 초록이다 = **지금은 깨끗하다**

> **git 없이 해보려면**: 추적되는 파일만 손으로 복사해도 같은 실험이 된다.
> ```
> mkdir -p /tmp/lab03-copy && cd /tmp/lab03-copy
> cp -r <저장소>/src <저장소>/tests <저장소>/pyproject.toml <저장소>/uv.lock .
> uv sync --locked --all-groups && uv run pytest
> ```

### ③ 일부러 깨뜨린다

**락 파일과 `pyproject.toml`을 어긋나게 만든다.** 백업부터 한다.

```
cp pyproject.toml /tmp/pyproject_backup.toml
```

이제 `pyproject.toml`을 열어 `[dependency-groups]`의 **`"hypothesis>=6.100",` 줄을 지운다.**
그리고 CI와 같은 명령을 돌린다.

```
uv sync --locked --all-groups
```

실제로 나오는 출력이다.

```
Resolved 14 packages in 63ms
error: The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.

hint: To update the lockfile, run `uv lock`.
```

- [ ] 실패하는 것을 봤다

**`--locked`가 없으면 어떻게 될까.** 직접 해 봐라. 같은 명령에서 플래그만 뺀다.

```
uv sync --all-groups
```

이번에는 **조용히 성공한다.** 락 파일을 알아서 다시 계산했기 때문이다.
**로컬에서는 편하고, CI에서는 재앙이다.**
CI가 검증한 의존성 집합과 남들이 받는 집합이 달라지기 때문이다.

**📝 네가 본 것을 여기 적어라**

```
① 추적 안 되는 파일 목록에 뭐가 있었나:
② 사본에서의 결과:
③ 락과 pyproject 를 어긋나게 했을 때 `--locked` 가 뭐라고 했나:
   `--locked` 를 뺐을 때는 어떻게 달랐나:


```

**되돌린다.**

```
cp /tmp/pyproject_backup.toml pyproject.toml
uv sync --locked --all-groups
```

- [ ] 되돌렸다. `uv sync --locked`가 이제 성공한다

**📝 랩의 질문**

> ②에서 실패했다면, 내 작업 디렉터리에 있고 사본에 없는 것은 무엇인가?

```


```

---

## 2. 사전지식 — 답을 먼저 적고 나서 튜토리얼을 연다

> **못 답해도 괜찮다. 모른다고 적는 것도 답이다.**

**Q1. GitHub Actions에서 워크플로가 언제 돌게 되어 있나? (트리거 이벤트)**

```


```

**Q2. CI 러너에는 uv가 설치돼 있나? 없다면 어떻게 넣나?**

```


```

**Q3. 테스트가 CI에서만 실패하고 로컬에서 통과한다면, 가장 먼저 의심할 것 3가지는?**

```
1.
2.
3.
```

- [ ] 답을 적었다 → 이제 [튜토리얼 Lab 0.3](../../docs/tutorial/phase-0.md#lab-03--ci를-초록으로)을 읽는다
- [ ] 읽고 나서 위 답을 **고쳐 적었다** (틀린 답을 지우지 말고 옆에 정정하라)

### 손으로도 확인한다

**내 로컬 판정기와 CI 판정기가 같은 물건인지 대조한다.**

```
uv run python -V
```

```
Python 3.12.13
```

- [ ] 파이썬 버전이 워크플로에 못 박힌 `3.12`와 맞는다

**그리고 추적되지 않는 파일 중에 테스트가 읽는 것이 없는지 본다.**

```
git ls-files --others --exclude-standard
```

- [ ] 목록에 **테스트가 읽는 것이 없다**

**📝 예상과 달랐던 것**

```


```

---

## 3. 과제 — 무엇을, 어떤 순서로 쓰나

**만드는 파일**: `.github/workflows/ci.yml`
**정본은 랩 문서다** → [Lab 0.3 과제](../../docs/labs/phase-0-setup.md#lab-03--ci를-초록으로)

> 이 시트에 과제 내용을 옮겨 적지 않는다. 정본은 한 곳이어야 한다.

### 코드를 쓰는 순서

이번 산출물은 YAML 파일이다. **테스트가 아니라 사람이 검증한다.** 그래도 순서는 같다.

**1단계 — 무엇이 이걸 검사하는지 확인한다.**
이 랩의 판정기는 **GitHub Actions 탭**이다.
초록 체크가 뜨면 통과, 빨간 X가 뜨면 실패다.
**그러니 로컬에서 먼저 같은 명령을 돌려 보는 것이 1단계의 실질이다.**

**2단계 — 만족해야 할 불변식을 확인한다.**
랩 3절에 네 줄이 있다. 한 줄씩 한국어로 다시 써 본다.
예: "로컬에서 실패하는 커밋은 CI에서도 실패한다."

**3단계 — 가장 단순한 것부터 채운다.**
워크플로는 세 덩어리뿐이다. **이 순서로 쓴다.**

```
on:        언제 돌릴까    (push, pull_request)
runs-on:   어디서 돌릴까  (ubuntu-latest)
steps:     무엇을 돌릴까  (체크아웃 → uv 설치 → 설치 → 린트 → 테스트)
```

`steps:`도 한꺼번에 쓰지 마라. **체크아웃과 uv 설치까지만 쓰고 한 번 올려 본다.**
거기까지 초록이면 나머지는 명령을 한 줄씩 더하는 일이다.

**4단계 — 돌린다. 단, push로 돌리지 마라.**
CI는 한 번 돌리는 데 몇 분이 걸린다.
**워크플로가 돌릴 명령을 로컬에서 그대로 돌리는 쪽이 항상 빠르다.**

```
uv sync --locked --all-groups
uv run ruff check
uv run pytest -v
```

**5단계 — 실패 메시지를 읽고 고친다.**
CI 로그는 단계별로 접혀 있다. **빨간 X가 붙은 단계를 펼쳐서** 거기만 읽는다.
그 안의 메시지는 로컬과 똑같이 읽으면 된다
(→ [테스트 실행법 — 실패 메시지 읽는 순서](../테스트-실행법.md#실패-메시지-읽는-순서)).

### `.gitignore` 확인

**이 랩에는 확인 항목이 하나 더 있다.** Phase 3에서 개인키가 실제로 생긴다.

```
grep -nE '^\*\.key|^keystore/|^\.env' .gitignore
```

```
3:*.key
5:keystore/
6:.env
7:.env.*
```

- [ ] 세 가지가 모두 있다

> **그때 가서 추가하면 늦을 수 있다.**
> 이미 추적 중이던 파일은 `.gitignore`를 고쳐도 계속 올라간다.

### 체크

- [ ] **불변식**만 보고 `.github/workflows/ci.yml`을 직접 썼다
- [ ] `--locked`를 쓰는 이유를 **스스로 설명할 수 있다** (랩 L2 힌트가 이걸 묻는다)
- [ ] `.gitignore`에 `*.key`, `keystore/`, `.env`가 들어 있는지 확인했다

---

## 4. 막히면

규칙은 [학습계획서 5절](../../docs/03-학습계획서.md#5-막혔을-때-에스컬레이션-규칙)이 정본이다.

```
0~30분  자력 (워크플로가 아예 안 돌면 파일 경로와 YAML 들여쓰기부터)
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

> **push해서 기다리는 것으로 디버깅하지 마라.**
> 한 번에 몇 분씩 날아간다. 로컬에서 같은 명령을 돌리는 쪽이 항상 빠르다.

---

## 5. 검증

**로컬 검증 먼저.**

```
uv run ruff check
uv run pytest
```

```
All checks passed!
============================== 2 passed in 0.01s ===============================
```

**그다음 push하고 GitHub의 Actions 탭을 본다.**

**통과해야 할 것**

- 로컬 두 명령이 성공한다
- 워크플로가 `main` push와 PR에서 **실제로 트리거된다**
- `uv sync --locked` → `ruff` → `pytest` 순서로 돌고, **하나라도 실패하면 빨강**이다

- [ ] 로컬 확인
- [ ] push 후 Actions 탭에서 초록 확인

---

## 6. 눈으로 확인

- [ ] GitHub 커밋 목록에서 내 커밋 옆에 **초록 체크 ✓**
- [ ] 일부러 테스트 하나를 깨뜨려 push하면 **빨간 ✗** 가 뜬다
- [ ] 되돌려 push하면 다시 초록이 된다

> **둘 다 봐야 판정기를 믿을 수 있다.**
> 초록만 본 판정기는 Lab 0.1에서 본 "한 번도 실패해 본 적 없는 테스트"와 같다.

- [ ] 초록 체크 스크린샷을 남긴다 → [PROGRESS.md의 "보여줄 수 있는 한 장면"](../../docs/PROGRESS.md#phase-0--기반-세팅)

**📝 빨강 → 초록을 실제로 본 시각과 커밋**

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
- [ ] `docs/PROGRESS.md`의 `Lab 0.3` 체크박스를 켠다 (이미 켜져 있다 — 🤖를 떼고 직접 했다고 고쳐 적어라)
- [ ] Phase 0의 **DoD 5개**도 여기서 점검한다 (랩을 다 했어도 DoD 확인이 안 됐으면 켜지 않는다)
- [ ] 커밋하고 push한다

```
git status                 # *.key, .env, keystore/ 가 없는지 먼저 확인
git add .github/workflows/ci.yml .gitignore docs/PROGRESS.md
git commit -m "Lab 0.3: CI workflow running ruff and pytest on locked deps"
git push origin main
```

---

**Phase 0 끝.** [Phase 0 워크북 README](README.md)로 돌아가 마무리 점검을 한다.
Phase 1 시트는 곧 `workbook/phase-1/`에 추가된다.
