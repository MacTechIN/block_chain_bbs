# 시작 파일 — 빈 화면 대신 여기서 출발한다

Phase 1은 **빈 파일에서 시작하지 않는다.** 함수 이름, 인자, 타입, 지켜야 할 불변식은
이미 랩이 정해 뒀다. 그걸 그대로 받아 적는 데 시간을 쓰지 말라고 여기 모아 뒀다.

**각 파일에 들어 있는 것**

- 이 파일이 무엇이고, 어느 랩의 몇 번 과제인지
- 어느 명령이 이걸 판정하는지, 어떤 테스트 이름이 초록이 되어야 하는지
- 랩이 지정한 시그니처 그대로 (타입 힌트 · 독스트링 포함)
- 만족해야 할 불변식 (주석)
- 본문은 `raise NotImplementedError(...)` 하나

**들어 있지 않은 것**: 힌트와 구현. 힌트는 랩 문서 4절에 L1/L2/L3로 있다.

---

## 왜 `src/`에 미리 두지 않았나

지금 상태에서 Phase 1 테스트를 돌리면 이런 화면이 뜬다.

```
uv run pytest tests/unit/test_merkle.py
```

```
E       conftest.MissingImplementation:
E       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
E        아직 구현이 없다 (이 시점에서는 정상이다)
E       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
E        대상 : bbschain.core.merkle
E        랩   : Lab 1.4 — 머클 루트   (docs/labs/phase-1-chain.md)
E        필요 : merkle_root(leaves), merkle_proof(leaves, index), verify_proof(leaf, proof, root)
E       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**이 배너가 "다음에 뭘 만들면 되는지" 목록이다.**
파일이 `src/` 아래 생기는 순간 배너는 사라지고, 대신 `NotImplementedError`가 뜬다.

그러니까 **파일이 생기는 시점을 네가 고르게** 하려고 워크북에 뒀다.
읽는 법은 → [테스트 실행법 — 안내 배너](../../테스트-실행법.md#아직-구현이-없을-때-뜨는-안내-배너)

---

## 🔴 한 번에 다 복사하지 마라

**랩이 시킬 때 하나씩 복사한다.** 이유는 셋이다.

1. 일곱 개를 한꺼번에 복사하면 배너가 전부 사라진다. **남은 할 일 목록을 잃는다.**
2. 실패 화면이 한 번에 일곱 군데에서 터진다. 어디부터 손댈지 알 수 없다.
3. Lab 1.4의 핵심 장면(속성 테스트가 반례를 들이미는 것)은 **Lab 1.3이 초록인 상태에서** 봐야 의미가 있다.

한 파일 복사 → 채운다 → 테스트가 초록 → 다음 파일. 이 리듬을 지켜라.

---

## 어느 랩에서 무엇을 복사하나

| 랩 | 시작 파일 | 복사 위치 | 과제 |
|---|---|---|---|
| [Lab 1.1](../lab-1.1.md) | 없음 | `labs/hash_play.py` (직접 만든다) | 관찰만 한다 |
| [Lab 1.2](../lab-1.2.md) | 없음 | `labs/naive_board.py` (직접 만든다) | 30줄. 버릴 코드다 |
| [Lab 1.3](../lab-1.3.md) | `core/serialize.py` | `src/bbschain/core/serialize.py` | (1) 정규 직렬화 |
| [Lab 1.3](../lab-1.3.md) | `core/hashing.py` | `src/bbschain/core/hashing.py` | (2) 해시 |
| [Lab 1.3](../lab-1.3.md) | `core/block.py` | `src/bbschain/core/block.py` | (3) 블록 |
| [Lab 1.3](../lab-1.3.md) | `core/chain.py` | `src/bbschain/core/chain.py` | (4) 체인과 검증 |
| [Lab 1.4](../lab-1.4.md) | `core/merkle.py` | `src/bbschain/core/merkle.py` | 머클 루트·증명 |
| [Lab 1.5](../lab-1.5.md) | `storage/base.py` | `src/bbschain/storage/base.py` | (1) 저장소 인터페이스 |
| [Lab 1.5](../lab-1.5.md) | `storage/jsonfile.py` | `src/bbschain/storage/jsonfile.py` | (2) JSON 파일 구현 |
| [Lab 1.5](../lab-1.5.md) | 없음 | `src/bbschain/cli.py` (이미 있다 — Phase 0 스텁을 갈아엎는다) | (3) CLI |

`core/validation.py`의 시작 파일은 없다. `ValidationResult`와 검증 함수를
`core/chain.py`에 둘지 `core/validation.py`로 나눌지는 **네가 정하는 부분**이고,
판정기는 두 배치를 모두 받아 준다. 시작 파일 `core/chain.py`에 그 설명이 주석으로 있다.

---

## 복사 명령

**전부 저장소 루트에서 실행한다.** 그대로 복사해 붙여 넣으면 된다.

### 폴더를 먼저 만든다 (처음 한 번)

```
mkdir -p src/bbschain/core src/bbschain/storage
touch src/bbschain/core/__init__.py src/bbschain/storage/__init__.py
```

**`__init__.py`는 꼭 만든다.** 없어도 import가 되는 경우가 있지만,
이 프로젝트는 항상 만드는 쪽이다 (이유는 → [설정 가이드 — 새 모듈을 만들 때](../../phase-0/설정-가이드.md#새-모듈을-만들-때-하는-일)).
내용은 비어 있어도 된다.

`storage/` 폴더는 Lab 1.5에 가서 만들어도 된다. 미리 만들어 둬도 해는 없다.

### Lab 1.3 — 네 파일, 하나씩

```
cp workbook/phase-1/starter/core/serialize.py src/bbschain/core/serialize.py
```
```
cp workbook/phase-1/starter/core/hashing.py   src/bbschain/core/hashing.py
```
```
cp workbook/phase-1/starter/core/block.py     src/bbschain/core/block.py
```
```
cp workbook/phase-1/starter/core/chain.py     src/bbschain/core/chain.py
```

### Lab 1.4 — 한 파일

```
cp workbook/phase-1/starter/core/merkle.py    src/bbschain/core/merkle.py
```

### Lab 1.5 — 두 파일

```
cp workbook/phase-1/starter/storage/base.py     src/bbschain/storage/base.py
```
```
cp workbook/phase-1/starter/storage/jsonfile.py src/bbschain/storage/jsonfile.py
```

---

## 복사한 뒤 무엇이 달라지나

복사 전과 후를 직접 비교해 보는 편이 빠르다.

```
uv run pytest tests/unit/test_serialize.py -x
```

**복사 전** — 모듈이 없다는 안내 배너.

```
E        대상 : bbschain.core.serialize
E        랩   : Lab 1.3 — 블록과 체인   (docs/labs/phase-1-chain.md)
E        필요 : canonical_bytes(obj) -> bytes
```

**복사 후** — 배너가 사라지고 이렇게 바뀐다.

```
E       NotImplementedError: Lab 1.3 과제 (1)번 — 여기를 채워라
```

**이게 정상이다.** 오히려 전진한 신호다.
"모듈이 없다"에서 "모듈은 있는데 안 채웠다"로 바뀐 것이다.
이제 그 줄을 지우고 네 코드를 쓰면 된다.

`FAILED`와 `ERROR`의 차이가 헷갈리면
→ [테스트 실행법 — failed와 error는 다르다](../../테스트-실행법.md#failed와-error는-다르다)

---

## 규칙

- **시작 파일 자체를 고치지 마라.** 복사본(`src/` 아래)에서 작업한다.
  원본은 다시 보러 올 때 깨끗해야 한다.
- 이미 채운 파일 위에 **다시 복사하지 마라.** 네 코드가 통째로 날아간다.
  덮어쓰기 전에 `git status`로 확인하는 습관을 들여라.
- 시그니처를 바꾸고 싶으면 **랩 문서를 먼저 봐라.** 대부분은 이미 고정된 계약이다
  (→ [개발계획서 6절](../../../docs/01-개발계획서.md#phase-1에-고정할-핵심-계약)).
- 주석으로 적힌 불변식은 **요점만** 옮겨 놓은 것이다. 정본은 랩 문서 3절이다.
