# Lab 1.3 따라하기 — 블록과 체인

| 대응 랩 | 이론 | 시작 파일 | 예상 소요 |
|---|---|---|---|
| [Lab 1.3](../../docs/labs/phase-1-chain.md#lab-13--블록과-체인) | [튜토리얼 Lab 1.3](../../docs/tutorial/phase-1.md#lab-13--블록과-체인) | [`starter/core/`](starter/README.md) 네 개 | 3~5시간 |

> 참고 문서 — 막히면 여기로.
> [테스트 실행법](../테스트-실행법.md) · [설정 가이드](../phase-0/설정-가이드.md) · [시작 파일 안내](starter/README.md)

## 이 시트로 뭘 하나

**여기가 Phase 1의 본체다.** Lab 1.2에서 조용히 통했던 공격을 이번엔 잡아낸다.
파일 네 개를 만든다 — 정규 직렬화, 해시, 블록, 체인 검증.
여기서 정한 것 세 가지(`canonical_bytes`, `Block` 필드, `Post` 필드)는
**나중에 바꾸면 그때까지 쌓은 체인이 전부 무효가 된다.**

---

## 0. 준비

- [ ] 터미널을 **저장소 루트**에서 연다
- [ ] Lab 1.2를 끝냈다 (변조가 통하는 화면을 봤다)

**출발점이 초록인지 확인한다.**

```
uv run pytest
```

```
============================== 2 passed in 0.01s ===============================
```

- [ ] `2 passed`를 봤다

**이 랩이 만들 것을 테스트가 이미 알고 있다.** 먼저 물어보자.

```
uv run pytest tests/unit/test_serialize.py 2>&1 | head -20
```

```
E        대상 : bbschain.core.serialize
E        랩   : Lab 1.3 — 블록과 체인   (docs/labs/phase-1-chain.md)
E        필요 : canonical_bytes(obj) -> bytes
```

- [ ] 안내 배너를 봤다. **에러가 아니라 할 일 목록이다**
      (→ [테스트 실행법 — 안내 배너](../테스트-실행법.md#아직-구현이-없을-때-뜨는-안내-배너))

---

## 1. 먼저 깨져보기 ⚔

**보려는 것**: 글마다 해시를 붙여도 **막히지 않는 공격**이 남아 있다는 것.

Lab 1.2의 게시판에 **글마다 해시만** 붙인 중간 버전을 만든다. 5분이면 된다.
`labs/` 아래 아무 이름으로나 만들어라.

```
{"id": 3, "author": "sam", "body": "...", "hash": sha256(body)}
```

검증은 "각 글의 `hash`가 그 글의 `body`를 다시 해시한 값과 같은가"만 보면 된다.

네 가지를 차례로 해 본다.

| | 공격 | 잡히나 |
|---|---|---|
| ① | 3번 글의 `body`만 바꾼다 | |
| ② | `body`를 바꾸고 **`hash`도 새로 계산해서** 같이 바꾼다 | |
| ③ | 5번 글을 **글과 해시를 세트로** 통째로 삭제한다 | |
| ④ | 5번과 6번의 **순서를 바꾼다** (해시는 그대로) | |

직접 돌려 보고 채워라. 나와야 하는 결과는 이렇다.

```
① INVALID: post 3 hash mismatch      ← 잡힌다
② (아무 일 없음)                      ← 안 잡힌다
③ (아무 일 없음)                      ← 안 잡힌다
④ (아무 일 없음)                      ← 안 잡힌다
```

- [ ] ①만 잡히고 ②③④는 전부 통과하는 것을 봤다

**📝 네가 본 것을 여기 적어라**

```
① body 변조:
② body + hash 동시 변조:
③ 세트로 삭제:
④ 순서 바꾸기:

(②가 가능한 이유는 각 글의 해시가 ______ 만으로 계산되기 때문이다)


```

**📝 랩의 질문**

> 개별 해시가 막아 주는 것과 막지 못하는 것의 경계는 어디인가?
> 해시 입력에 **무엇을 더 넣어야** ③·④까지 막히겠는가?
> **답을 보기 전에 30초만 생각하라.**

```


```

---

## 2. 사전지식 — 답을 먼저 적고 튜토리얼을 연다

> **못 답해도 괜찮다. 모른다고 적는 것도 답이다.**

**Q1. 블록 N의 해시 입력에 블록 N-1의 해시가 들어가면, 블록 3을 고쳤을 때 블록 4·5·6은 왜 같이 깨지나?**

```


```

**Q2. 제네시스 블록의 `prev_hash`에는 무엇을 넣나? 왜 그 값이어야 하나(또는 아무 값이어도 되나)?**

```


```

**Q3. `validate_chain()`이 `bool` 대신 파손 인덱스를 반환해야 하는 이유는? (→ Phase 2에서 쓰인다)**

```


```

- [ ] 적었다 → [튜토리얼 Lab 1.3](../../docs/tutorial/phase-1.md#lab-13--블록과-체인)을 읽는다
- [ ] 읽고 답을 **고쳐 적었다**

**📝 예상과 달랐던 것**

```


```

---

## 3. 코드를 어디에 쓰나

**만들 파일 네 개.** 이름은 이미 정해져 있다 — 테스트가 그 이름을 import한다.

| 과제 | 만들 파일 | 시작 파일 |
|---|---|---|
| (1) 정규 직렬화 | `src/bbschain/core/serialize.py` | [`starter/core/serialize.py`](starter/core/serialize.py) |
| (2) 해시 | `src/bbschain/core/hashing.py` | [`starter/core/hashing.py`](starter/core/hashing.py) |
| (3) 블록 | `src/bbschain/core/block.py` | [`starter/core/block.py`](starter/core/block.py) |
| (4) 체인과 검증 | `src/bbschain/core/chain.py` | [`starter/core/chain.py`](starter/core/chain.py) |

### 새 폴더가 필요하다

`src/bbschain/core/`는 **아직 없다.** 폴더와 `__init__.py`를 만든다.

```
mkdir -p src/bbschain/core
touch src/bbschain/core/__init__.py
```

- [ ] 만들었다

**`__init__.py`를 빼먹지 마라.** 없어도 import가 되는 경우가 있지만,
이 프로젝트는 항상 만드는 쪽이다
(→ [설정 가이드 — 새 모듈을 만들 때](../phase-0/설정-가이드.md#새-모듈을-만들-때-하는-일)).

### 시작 파일을 복사한다 — 🔴 **한 번에 하나씩**

**지금은 첫 번째 것만 복사한다.** 나머지는 4절에서 순서대로 시킨다.

```
cp workbook/phase-1/starter/core/serialize.py src/bbschain/core/serialize.py
```

- [ ] 복사했다

네 개를 한꺼번에 복사하면 안내 배너가 전부 사라지고, 실패가 네 군데에서 동시에 터진다.
**남은 할 일 목록을 잃는 것**이다 (→ [시작 파일 안내](starter/README.md)).

### import는 어떻게 해석되나

`src/bbschain/core/serialize.py`를 만들면 `bbschain.core.serialize`로 import된다.
**`uv sync`를 다시 돌릴 필요는 없다.** editable 설치가 `src/` 안을 그때그때 읽는다.

```
uv run python -c "import bbschain.core.serialize; print('ok')"
```

```
ok
```

- [ ] `ok`가 나온다

안 되면 → [설정 가이드 — ModuleNotFoundError가 났을 때](../phase-0/설정-가이드.md#modulenotfounderror가-났을-때)

---

## 4. 코드를 어떤 순서로 쓰나

**과제 번호 순서가 곧 의존 순서다.** (1)이 없으면 (2)가 안 되고, (2)가 없으면 (3)이 안 된다.
**한 파일씩 초록을 보고 다음으로 간다.**

### 1단계 — 판정할 테스트를 먼저 읽는다

코드를 쓰기 전에 **무엇을 요구하는지** 본다. 테스트 파일은 고치지 않는다. 읽기만 한다.

```
uv run pytest tests/unit/test_serialize.py -v
```

실패 메시지 안에 요구사항이 한국어로 적혀 있다. 그게 이 랩의 사양이다.
읽기 어려우면 파일을 직접 열어도 된다: `tests/unit/test_serialize.py`

- [ ] 어떤 테스트 이름들이 있는지 봤다

### 2단계 — 만족해야 할 불변식을 확인한다

정본은 [랩 §3](../../docs/labs/phase-1-chain.md#lab-13--블록과-체인)이다.
시작 파일에도 주석으로 요점이 들어 있다. **한국어로 다시 써 보면 머리에 남는다.**

```
canonical_bytes 가 지켜야 할 것 (네 줄):
1)
2)
3)
4)
```

### 3단계 — 가장 단순한 경우부터 채운다

**(1) `serialize.py` — 딕셔너리 하나부터.**

```
uv run python -c "
from bbschain.core.serialize import canonical_bytes
print(canonical_bytes({'b': 2, 'a': 1}))
print(canonical_bytes({'a': 1, 'b': 2}))
"
```

두 줄이 **같은 바이트열**이면 절반은 끝났다.

**(2) `hashing.py` — 두 함수, 세 줄.**
`sha256_hex`부터 채우고, `hash_object`는 그 위에 얹는다.

**(3) `block.py` — 필드는 이미 선언돼 있다. `hash` 프로퍼티 하나만 채운다.**
글 **한 개**짜리 블록 하나로 먼저 확인한다.

```
uv run python -c "
from bbschain.core.block import Post, Block
b = Block(index=0, prev_hash='0'*64, timestamp=1700000000,
          merkle_root='7'*64, nonce=0, difficulty=0,
          txs=(Post('sam', '첫 글', 1700000000),))
print(b.hash)
print(b.hash == b.hash)
"
```

두 번 읽었는데 값이 다르면 입력에 **현재 시각이나 난수**가 섞인 것이다.

**(4) `chain.py` — 블록 **하나**짜리 체인부터.**
제네시스 하나만 있는 체인이 `ok=True`를 내는 것을 먼저 확인한다.
그다음 두 개, 그다음 깨뜨려 본다.

### 4단계 — 한 파일 쓸 때마다 테스트를 돌린다

좁은 범위부터. 아래 순서대로다.

```
uv run pytest tests/unit/test_serialize.py -v
```
```
uv run pytest tests/unit/test_block.py -v
```
```
uv run pytest tests/unit/test_chain_validation.py -v
```

**전부 쓰고 한 번에 돌리지 마라.** 어느 파일이 문제인지 못 찾는다.

> 🔴 **`test_block.py`의 뒤쪽 두 개는 지금 빨간 것이 정상이다.**
> `test_block_hash_input_excludes_txs`와 `test_tampering_a_post_still_changes_block_hash`는
> **Lab 1.4에서** 초록이 된다. 지금 통과시키려 하면 Lab 1.2의 공격이 그대로 다시 통한다.

### 5단계 — 실패 메시지를 읽고 고친다

읽는 순서가 정해져 있다 → [테스트 실행법 — 실패 메시지 읽는 순서](../테스트-실행법.md#실패-메시지-읽는-순서)

자주 나오는 것 세 가지만 미리 짚는다.

| 화면 | 먼저 볼 곳 |
|---|---|
| 안내 배너(`아직 구현이 없다`) | 파일을 안 만들었거나 이름이 틀렸다. `대상` 줄을 그대로 읽어라 |
| `NotImplementedError` | 시작 파일은 복사했고 본문을 아직 안 썼다. **정상이다** |
| `first_bad_index`가 기대와 다름 | 검증 순서 문제다. 랩 5절 표의 네 번째 줄을 보라 |

---

## 5. 과제

**정본은 랩 문서다** → [Lab 1.3 §3 과제](../../docs/labs/phase-1-chain.md#lab-13--블록과-체인)

**만들 파일**

- `src/bbschain/core/serialize.py` — 과제 (1)
- `src/bbschain/core/hashing.py` — 과제 (2)
- `src/bbschain/core/block.py` — 과제 (3)
- `src/bbschain/core/chain.py` — 과제 (4)
- (선택) `src/bbschain/core/validation.py` — `ValidationResult`와 검증 함수를 나눠 둘 곳.
  `chain.py`에 그대로 둬도 된다. **판정기는 두 배치를 모두 받아 준다**

**이 시트에 과제 내용을 옮겨 적지 않는다.** 시그니처·불변식은 전부 랩 3절에 있다.

- [ ] [ADR-0001](../../docs/decisions/ADR-0001-canonical-serialization.md)을 읽고, 내가 고른 직렬화 규칙을 거기에 맞춰 확인했다

---

## 6. 막히면

규칙은 [학습계획서 5절](../../docs/03-학습계획서.md#5-막혔을-때-에스컬레이션-규칙)이 정본이다.

```
0~30분  자력 (에러 메시지를 끝까지 읽었나?)
  30분  L1 힌트 — 방향
  1시간  L2 힌트 — 구조
  2시간  L3 힌트 — 의사코드
그 이후  code-reviewer 에이전트에 리뷰 요청 (정답 요청 금지)
```

힌트는 랩 문서 4절에 접혀 있다 → [Lab 1.3 §4](../../docs/labs/phase-1-chain.md#lab-13--블록과-체인)

| | 연 시각 | 그때 막혀 있던 것 |
|---|---|---|
| L1 | | |
| L2 | | |
| L3 | | |
| 리뷰 요청 | | |

- [ ] 30분 넘게 막혔다면 [PROGRESS.md 막힌 지점 로그](../../docs/PROGRESS.md#막힌-지점-로그)에 **지금** 한 줄 적었다

> **네 파일짜리 랩이다.** 한 파일에서 막혔으면 **그 파일만** 막힌 것이다.
> 랩 전체가 막혔다고 적지 말고 "`Block.hash`가 결정적이지 않다" 같이 좁혀서 적어라.

---

## 7. 테스트하기

**좁은 범위부터 넓혀 간다.** 순서대로 체크해라.

- [ ] (1) 정규 직렬화

```
uv run pytest tests/unit/test_serialize.py -v
```

- [ ] (2)(3) 블록

```
uv run pytest tests/unit/test_block.py -v
```

- [ ] (4) 체인 검증

```
uv run pytest tests/unit/test_chain_validation.py -v
```

- [ ] 셋을 한 번에

```
uv run pytest tests/unit/test_serialize.py tests/unit/test_block.py tests/unit/test_chain_validation.py
```

- [ ] 린터와 타입 검사

```
uv run ruff check
```
```
uv run mypy src/
```

### 통과해야 할 테스트 이름

`tests/unit/test_serialize.py`
- `test_canonical_bytes_key_order_independent`
- `test_canonical_bytes_key_order_independent_property`
- `test_canonical_bytes_is_utf8`
- `test_canonical_bytes_rejects_unserializable`
- `test_canonical_bytes_int_and_float_are_not_confused`
- `test_hash_object_goes_through_canonical_bytes`

`tests/unit/test_block.py`
- `test_block_and_post_field_names_are_fixed`
- `test_block_hash_is_deterministic`
- `test_block_hash_is_deterministic_property`
- `test_block_hash_changes_when_any_field_changes` (6개 필드 각각 돈다)
- `test_block_is_frozen`
- `test_genesis_rules`

`tests/unit/test_chain_validation.py`
- `test_valid_chain_passes`
- `test_valid_chain_passes_property`
- `test_validate_does_not_mutate_the_chain`
- `test_tampered_body_reports_first_bad_index`
- `test_tampered_body_reports_first_bad_index_property`
- `test_first_bad_index_is_the_earliest_break`
- `test_tampered_body_with_recomputed_merkle_root_breaks_the_next_link`
- `test_recomputed_chain_passes_validation`
- `test_deleted_block_is_detected`
- `test_prefix_of_a_valid_chain_is_still_valid`
- `test_reordered_blocks_are_detected`

### 아직 빨간 게 정상인 것

- `test_block_hash_input_excludes_txs` → **Lab 1.4**
- `test_tampering_a_post_still_changes_block_hash` → **Lab 1.4**
- `tests/unit/test_merkle.py` 전부 → **Lab 1.4**
- `tests/unit/test_storage_jsonfile.py`, `test_cli.py`, `tests/integration/` → **Lab 1.5**
- `tests/unit/test_serialize.py::test_block_dict_roundtrip` → **Lab 1.5** (`to_dict`/`from_dict`가 필요하다)

### 실패하면

**어디를 먼저 보나.**

1. `FAILED`인가 `ERROR`인가 — 다른 말이다
   (→ [테스트 실행법 — failed와 error는 다르다](../테스트-실행법.md#failed와-error는-다르다))
2. 마지막 `E` 줄의 한국어 설명 — 이 저장소의 테스트는 **왜 틀렸는지**를 적어 둔다
3. `>` 줄의 단언문 — 무엇을 기대했는지
4. 그래도 모르겠으면 → [테스트 실행법 — 막혔을 때 확인 순서](../테스트-실행법.md#막혔을-때-확인-순서)

**속성 테스트(`_property`로 끝나는 것)가 실패했다면** 화면이 다르다.
`Failing test case:` 블록에 **규칙을 깨는 최소 입력**이 찍힌다.
읽는 법 → [테스트 실행법 — 속성 기반 테스트의 반례 읽는 법](../테스트-실행법.md#속성-기반-테스트의-반례-읽는-법)

---

## 8. 눈으로 확인

**④ 재공격 — 이 랩의 결승선이다.**

`03` 실험이 네 블록을 직접 찔러 준다.

```
uv run python workbook/phase-1/experiments/03_block_hash_probe.py
```

- [ ] (A)의 헤더 6줄이 **전부 ✅** 다 — 빠진 필드가 없다
- [ ] (A)의 마지막 줄 `txs (글 본문)`이 **"바뀐다"** 다 (Lab 1.3 시점에는 이게 맞다)
- [ ] (B)에서 **#0 하나를 고쳤는데 #1의 연결이 끊기는 것**을 봤다

그리고 Lab 1.2에서 했던 것과 **똑같은 공격**을 다시 한다.
체인을 dump한 파일에서 3번 블록의 글자 하나를 바꾸고 검증하면 이렇게 나와야 한다.

```
INVALID: block #3 hash mismatch
         reason: block hash does not match its contents
         blocks #4..#10 are unreachable from a valid ancestor
```

- [ ] **Lab 1.2의 화면과 나란히 놓고 봤다.** 같은 공격, 다른 결과

**📝 스스로 답하라 — 왜 #3만이 아니라 #4 이후가 전부 무효인가?**

```


```

**📝 그리고 이건 꼭 적어 둬라 (랩 §8 4번)**

> 공격자가 블록 3부터 끝까지 전부 재계산하면 이 검증을 통과한다.
> **지금 그걸 막는 것이 있나?**

```


```

- [ ] 위 답을 [PROGRESS.md](../../docs/PROGRESS.md#phase-1--단일-노드-체인--게시판-코어)에 적었다
      (없다. 그게 Phase 4가 존재하는 이유다)

---

## 9. 회고 3줄

```
배운 것:

헛짚은 것:

다음에 확인할 것:
```

---

## 10. 기록

- [ ] 회고 3줄을 [PROGRESS.md 회고 기록](../../docs/PROGRESS.md#회고-기록)에 옮긴다 (**정본은 PROGRESS.md다**)
- [ ] [PROGRESS.md](../../docs/PROGRESS.md#phase-1--단일-노드-체인--게시판-코어)의 `Lab 1.3` 체크박스를 켠다
- [ ] [ADR-0001](../../docs/decisions/ADR-0001-canonical-serialization.md)에 내가 고른 규칙이 반영돼 있다
- [ ] 커밋한다

```
git status                 # *.key, .env, chain.json 이 없는지 먼저 확인
git add src/bbschain/core docs/PROGRESS.md docs/decisions/ADR-0001-canonical-serialization.md
git commit -m "Lab 1.3: canonical serialization, block hashing, and chain validation"
```

---

다음 → [Lab 1.4 따라하기](lab-1.4.md)
