# Phase 0 관찰 실험

튜토리얼 [phase-0.md](../../../docs/tutorial/phase-0.md)의 **"손으로 확인하기"** 를
바로 돌아가는 파일로 옮긴 것이다.

읽고 고개를 끄덕이는 것과, **같은 코드가 조건에 따라 다르게 출력되는 것을 화면에서 보는 것**은
다른 일이다.

**전부 저장소 루트에서 실행한다.** 세 스크립트는 서로 의존하지 않는다. 순서도 상관없다.

```
uv run python workbook/phase-0/experiments/01_pytest_collection.py
uv run python workbook/phase-0/experiments/02_sys_path.py
uv run python workbook/phase-0/experiments/03_assert_rewrite.py
```

| 스크립트 | 무엇을 보여주나 | 어느 랩에서 |
|---|---|---|
| [`01_pytest_collection.py`](01_pytest_collection.py) | 이름만 다른 후보 7개 중 **무엇이 수집되고 무엇이 조용히 빠지는가.** 경로를 직접 지정하면 규칙이 어떻게 달라지는가. 이 저장소에서 `pytest`가 왜 2개만 도는가 | [Lab 0.1](../lab-0.1.md) |
| [`02_sys_path.py`](02_sys_path.py) | 같은 한 줄을 **네 가지로 실행하면 파이썬이 뒤지는 폴더가 매번 다르다.** `bbschain`을 연결하는 `.pth` 파일 한 줄. 폴더를 옮겨도 import가 되는 이유 | [Lab 0.2](../lab-0.2.md) |
| [`03_assert_rewrite.py`](03_assert_rewrite.py) | **똑같은 `assert` 한 줄**의 실패 출력이 조건마다 어떻게 달라지는가. 친절한 진단이 어디서 나오고 어디서 사라지는가 | [Lab 0.1](../lab-0.1.md) |

## 읽는 법

각 출력에는 `👀 볼 것:` 줄이 붙어 있다. **숫자나 목록보다 그 줄이 본체다.**
출력만 보고 "그렇구나" 하고 넘어가면 실험을 안 한 것과 같다.

- 돌리기 **전에** 결과를 예상해 봐라. `01`은 아예 예상 목록을 먼저 출력해 준다
- **예상과 다르면 그게 이 실험의 수확이다.** 시트의 `📝` 칸이나 [`notes/`](../../notes/)에 적어라

명령과 출력을 읽는 법 전반은 → [테스트 실행법](../../테스트-실행법.md)

## 주의

- 🔴 **이 스크립트에는 랩 과제의 답이 없다.** 관찰 도구일 뿐이고, `bbschain` 구현은 한 줄도 없다
- 임시 파일은 전부 시스템 임시 폴더에 만들고 **끝나면 지운다.** 저장소를 더럽히지 않는다
- pytest를 부를 때 `-p no:cacheprovider`를 붙여 `.pytest_cache`도 건드리지 않는다
- 출력에 찍히는 pytest·파이썬 버전은 지금 `.venv`의 것이다. 버전이 올라가면 문구가 조금 달라질 수 있다
