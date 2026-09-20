# Lab 1.4 따라하기 — 머클 루트

| 대응 랩 | 이론 | 시작 파일 | 예상 소요 |
|---|---|---|---|
| [Lab 1.4](../../docs/labs/phase-1-chain.md#lab-14--머클-루트) | [튜토리얼 Lab 1.4](../../docs/tutorial/phase-1.md#lab-14--머클-루트) (**읽기 A / 읽기 B로 나뉜다**) | [`starter/core/merkle.py`](starter/core/merkle.py) | 3~4시간 |

> 참고 문서 — 막히면 여기로.
> [테스트 실행법](../테스트-실행법.md) · [설정 가이드](../phase-0/설정-가이드.md) · [시작 파일 안내](starter/README.md)

## 이 시트로 뭘 하나

**이 랩은 순서가 특별하다.** 다른 랩처럼 "읽고 만들고 통과"가 아니다.

> **일부러 취약하게 먼저 만든다 → 속성 테스트가 반례를 들이민다 → 그걸 보고 고친다.**

랩 문서가 직접 이렇게 쓴다: **"이 실패 테스트가 Phase 1 전체에서 가장 교육적인 장면이다."**
그 장면을 보려면 **답을 먼저 읽으면 안 된다.**
튜토리얼도 그래서 읽기 A와 읽기 B로 갈라 놓았다. **이 시트가 언제 어느 쪽을 열지 알려 준다.**

### 이 시트의 진행 순서 — 여기만 먼저 봐라

```
1절 앞부분   임시 루트의 한계를 본다               (증명 크기, 이어붙이기 충돌)
   ▼
2절 Q1       답을 적고  →  튜토리얼 **읽기 A** 를 연다
   ▼
3·4절        시작 파일을 복사하고 merkle_root 만 채운다
             🔴 홀수 리프는 **네가 떠오르는 방식** 그대로 간다. 고민하지 마라
   ▼
1절 뒷부분   속성 테스트를 돌린다  →  **반례를 본다**   ← 이 장면이 이 랩의 본체다
   ▼
2절 Q2·Q3    답을 적고  →  튜토리얼 **읽기 B** 를 연다
   ▼
5절          랩 §3 과제로 간다 (고치기 + 추가 과제 세 개)
```

🔴 **읽기 B를 미리 열지 마라.** 거기에 답이 있다.

---

## 0. 준비

- [ ] 터미널을 **저장소 루트**에서 연다
- [ ] Lab 1.3이 초록이다 — 이게 선행 조건이다

```
uv run pytest tests/unit/test_serialize.py tests/unit/test_chain_validation.py
```

- [ ] 통과한다 (`test_block.py`의 뒤쪽 두 개는 아직 빨간 게 정상이다)

**이 랩이 만들 것을 테스트에 물어본다.**

```
uv run pytest tests/unit/test_merkle.py 2>&1 | head -20
```

```
E        대상 : bbschain.core.merkle
E        랩   : Lab 1.4 — 머클 루트   (docs/labs/phase-1-chain.md)
E        필요 : merkle_root(leaves), merkle_proof(leaves, index), verify_proof(leaf, proof, root)
```

- [ ] 안내 배너를 봤다

---

## 1. 먼저 깨져보기 ⚔ — 앞부분

**보려는 것**: Lab 1.3에서 임시로 채워 둔 `merkle_root`의 두 가지 한계.

### ① 글 4개짜리 블록을 만들고 루트를 기록한다

```
uv run python -c "
from bbschain.core.block import Post
from bbschain.core.hashing import hash_object
from dataclasses import asdict
posts = [Post('sam', f'글 {i}', 1700000000 + i) for i in range(4)]
print(hash_object([asdict(p) for p in posts]))
"
```

> 위는 랩이 허용한 **임시 규칙**("txs 전체 해시")을 그대로 쓴 것이다.
> 네가 Lab 1.3에서 다른 임시 규칙을 썼다면 그쪽으로 바꿔 돌려라. 결론은 같다.

- [ ] 값을 적어 뒀다

### ② 글 2번만 바꾼다. 루트가 바뀌는가

위 명령에서 `f'글 {i}'`를 하나만 다르게 바꿔 다시 돌린다.

- [ ] 바뀐다. **여기까지는 문제없다**

### ③ 질문 — 증명하려면 무엇을 줘야 하나

> **"글 2번이 이 블록에 들어 있다"를 제3자에게 증명하려면 무엇을 줘야 하나?**

```


```

지금 구현으로는 **글 1·2·3·4를 전부** 줘야 한다. 블록에 글이 10만 개면 10만 개를 다 준다.

- [ ] 이걸 확인했다

### ④ 이어붙이기의 충돌

```
uv run python -c "
import hashlib
for leaves in ([b'A', b'B'], [b'AB']):
    joined = b''.join(leaves)
    print(leaves, '->', joined, '->', hashlib.sha256(joined).hexdigest()[:16])
"
```

```
[b'A', b'B'] -> b'AB' -> 38164fbd17603d73
[b'AB'] -> b'AB' -> 38164fbd17603d73
```

- [ ] **다른 글 목록인데 같은 값이 나왔다**

**📝 네가 본 것을 여기 적어라**

```
③ 증명하려면 줘야 하는 것:
④ ["A","B"] 와 ["AB"] 의 결과:

(구분자 없이 이어붙이면 왜 충돌이 생기나?)


```

**📝 랩의 질문**

> ④의 충돌을 막으려면 무엇이 필요한가?
> ③에서 "전부"가 아니라 일부만 주고도 증명이 되려면, 해시를 어떤 **모양**으로 쌓아야 하겠는가?

```


```

---

## 2. 사전지식 — 답을 먼저 적고, 읽기 A만 연다

> **못 답해도 괜찮다. 모른다고 적는 것도 답이다.**

**Q1. 리프가 N개일 때 머클 트리의 높이는? 증명에 필요한 해시 개수는?**

```


```

- [ ] Q1을 적었다 → [튜토리얼 읽기 A](../../docs/tutorial/phase-1.md#읽기-a--과제-전)를 읽는다
- [ ] 읽고 Q1을 **고쳐 적었다**

🔴 **여기서 멈춘다. 읽기 B로 내려가지 마라.**
Q2와 Q3는 아래에 있고, **지금은 추측만 적는다.** 답 맞추기는 반례를 본 다음이다.

**Q2. 리프 개수가 홀수면 어떻게 처리하나? (지금은 추측만 적어라)**

```


```

**Q3. CVE-2012-2459는 무엇이고, 왜 비트코인은 그걸 알면서도 못 고쳤나? (모르면 "모른다")**

```


```

- [ ] Q2·Q3에 **지금 떠오르는 대로** 적었다. 검색하지 않았다

---

## 3. 코드를 어디에 쓰나

| | |
|---|---|
| **만들 파일** | `src/bbschain/core/merkle.py` |
| **시작 파일** | [`starter/core/merkle.py`](starter/core/merkle.py) |
| **같이 고칠 파일** | `src/bbschain/core/block.py`, `core/chain.py` (5절 추가 과제에서) |

`src/bbschain/core/`는 Lab 1.3에서 이미 만들었다. 폴더 작업은 없다.

```
cp workbook/phase-1/starter/core/merkle.py src/bbschain/core/merkle.py
```

- [ ] 복사했다

**import는 어떻게 해석되나.** `bbschain.core.merkle`로 잡힌다. `uv sync`는 필요 없다.

```
uv run python -c "import bbschain.core.merkle; print('ok')"
```

- [ ] `ok`가 나온다

---

## 4. 코드를 어떤 순서로 쓰나

### 🔴 이 랩만의 규칙 — 지금은 `merkle_root` 하나만 채운다

`merkle_proof`와 `verify_proof`는 **아직 건드리지 마라.** 1절 뒷부분을 먼저 봐야 한다.

### 1단계 — 판정할 테스트를 먼저 읽는다

```
uv run pytest tests/unit/test_merkle.py -v
```

이름만 훑어라. 지금은 전부 빨갛다.

### 2단계 — 만족해야 할 불변식을 확인한다

시작 파일 `merkle_root`의 주석에 요점이 있다. 정본은
[랩 §3](../../docs/labs/phase-1-chain.md#lab-14--머클-루트)이다.

**지금은 이 세 줄만 만족시키면 된다.**

```
· 리프 하나라도 바뀌면 루트가 바뀐다
· 리프 순서가 바뀌면 루트가 바뀐다 (정렬하지 마라)
· 리프가 1개면 루트는 정의한 규칙대로
```

### 3단계 — 가장 단순한 경우부터 채운다

**리프 1개 → 2개 → 4개 순서다.**

```
uv run python -c "
from bbschain.core.merkle import merkle_root
print(merkle_root([b'a']))
print(merkle_root([b'a', b'b']))
print(merkle_root([b'a', b'b', b'c', b'd']))
"
```

세 줄이 서로 다른 값이고 에러가 없으면 뼈대는 됐다.

**그다음이 홀수 개다.**

```
uv run python -c "
from bbschain.core.merkle import merkle_root
print(merkle_root([b'a', b'b', b'c']))
"
```

🔴 **여기서 고민하지 마라.** 마지막 하나가 짝이 없다.
**네 머리에 제일 먼저 떠오르는 방식 그대로 가라.** 그게 이 랩의 설계다.

### 4단계 — 좁은 범위부터 테스트를 돌린다

```
uv run pytest tests/unit/test_merkle.py -k "deterministic or single_leaf or reorder" -v
```

- [ ] 이 세 종류가 초록이다

### 5단계 — 그리고 이제, 1절 뒷부분으로 간다

**아래로 내려가라.**

---

## 1. 먼저 깨져보기 ⚔⚔ — 뒷부분 (홀수 리프)

🔴 **이 절은 4단계를 끝낸 뒤에 한다.** `merkle_root`가 돌아가는 상태여야 한다.

### 반례를 부른다

```
uv run pytest tests/unit/test_merkle.py -k no_two_leaf_lists_share_a_root
```

네가 볼 화면은 이런 모양이다.

```
E       Falsifying example: test_no_two_leaf_lists_share_a_root(
E           pair=([b'\x00', b'\x01', b'\x02'],
E                 [b'\x00', b'\x01', b'\x02', b'\x02']),
E       )
E       서로 다른 두 리프 목록이 같은 머클 루트를 냈다
```

> hypothesis 버전에 따라 `Falsifying example:` 대신 `Failing test case:`로 나온다. **같은 것이다.**
> 읽는 법 → [테스트 실행법 — 속성 기반 테스트의 반례 읽는 법](../테스트-실행법.md#속성-기반-테스트의-반례-읽는-법)

- [ ] 반례를 화면에서 봤다

> **초록이 나왔다면?** 두 가지 중 하나다.
> ① 네가 고른 홀수 처리 방식이 우연히 안전한 쪽이었다 — 축하한다. 그래도 아래 질문은 답해라.
> ② 테스트가 안 돌았다 — `tests/unit/test_merkle.py`를 경로로 명시했는지 확인하라
>    (→ [테스트 실행법 — 이 저장소에만 있는 규칙](../테스트-실행법.md#이-저장소에만-있는-규칙--왜-2개만-도나)).

### 무엇을 본 건가

반례의 두 목록을 나란히 놓아라.

```
a = [b'\x00', b'\x01', b'\x02']
b = [b'\x00', b'\x01', b'\x02', b'\x02']
```

**글 3개짜리 블록과, 마지막 글을 한 번 더 복사해 붙인 글 4개짜리 블록.**
이 둘의 머클 루트가 **완전히 같다.**

루트가 같으면 블록 해시도 같다. **변조된 블록과 원본 블록이 구분되지 않는다.**

**📝 랩의 질문 — 세 개 다 답해라 (PROGRESS.md에도 옮긴다)**

> ① `[1,2,3]`과 `[1,2,3,3]`의 루트가 같아진 이유를 **트리 그림으로 그려서** 설명하라.

```
(여기에 그려라 — 텍스트로도 된다)




```

> ② 이걸 아는 공격자는 무엇을 할 수 있나?
>    (힌트: 노드가 "이 블록 해시는 영구 무효"라고 마킹한다면?)

```


```

> ③ 이 성질을 없애려면 홀수 리프를 **복제하지 않고** 어떻게 처리하면 되겠는가?

```


```

- [ ] 세 질문에 답했다. **③에 답하기 전에 읽기 B를 열지 않았다**

이건 실제 취약점이고 이름이 있다 — **CVE-2012-2459.**

---

## 2. 사전지식 — 이제 읽기 B를 연다

- [ ] 위 ①②③에 답을 적었다
- [ ] 2절의 **Q2·Q3를 다시 읽고** 답을 고쳐 적었다
- [ ] 이제 [튜토리얼 읽기 B](../../docs/tutorial/phase-1.md#읽기-b--반례를-본-뒤)를 연다
- [ ] 읽고 Q2·Q3를 **한 번 더** 고쳐 적었다

**📝 내 첫 답과 읽기 B가 갈린 지점**

```


```

---

## 5. 과제

**정본은 랩 문서다** → [Lab 1.4 §3 과제](../../docs/labs/phase-1-chain.md#lab-14--머클-루트)

랩 3절이 **홀수 리프를 어떻게 처리할지 못 박아 준다.** 이제 읽어도 된다.

**만들 파일 / 고칠 파일 — 네 덩어리다. 하나라도 빼면 랩이 안 끝난다.**

| | 무엇 | 어디 |
|---|---|---|
| (1) | `merkle_root` / `merkle_proof` / `verify_proof` | `src/bbschain/core/merkle.py` |
| (2) | `Block.merkle_root`를 임시 구현에서 진짜 머클로 교체 | `src/bbschain/core/block.py` (또는 `chain.py`) |
| (3) | 🔴 `Block.hash`의 입력에서 **`txs`를 제거** | `src/bbschain/core/block.py` |
| (4) | 🔴 `validate`가 `merkle_root`를 `txs`로부터 **재계산해 대조** | `src/bbschain/core/chain.py` |

**(3)과 (4)는 쌍이다.** (3)만 하고 (4)를 빼먹으면
**글 본문을 고쳐도 아무 데서도 안 잡힌다** — Lab 1.2로 그대로 되돌아간다.
왜 그런지는 랩 3절이 길게 설명한다. 그 문단을 꼭 읽어라.

**교체하는 순간 기존에 쌓아 둔 체인은 전부 무효가 된다.** 이게 정상이다.
왜 이게 [ADR-0001](../../docs/decisions/ADR-0001-canonical-serialization.md) 위반이 아닌지는 랩 3절 끝에 있다.

- [ ] 랩 3절을 읽었다
- [ ] 네 덩어리를 전부 했다
- [ ] 빈 리프(0개)의 동작을 정하고 ADR-0001에 덧붙였다
- [ ] 리프 해시와 내부 노드 해시를 **어떻게 구분했는지** 기록했다

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

힌트는 랩 문서 4절에 접혀 있다 → [Lab 1.4 §4](../../docs/labs/phase-1-chain.md#lab-14--머클-루트)

| | 연 시각 | 그때 막혀 있던 것 |
|---|---|---|
| L1 | | |
| L2 | | |
| L3 | | |
| 리뷰 요청 | | |

- [ ] 30분 넘게 막혔다면 [PROGRESS.md 막힌 지점 로그](../../docs/PROGRESS.md#막힌-지점-로그)에 **지금** 한 줄 적었다

> ⚠️ **다른 사람의 머클 구현을 그대로 옮기지 마라.**
> 랩 5절 표가 경고한다 — 널리 쓰이는 학습용 구현에도 이 방어가 빠져 있다.
> 베끼면 방금 본 그 반례가 그대로 다시 나온다.

---

## 7. 테스트하기

**좁은 범위부터 넓혀 간다.**

- [ ] 반례를 냈던 그 테스트부터

```
uv run pytest tests/unit/test_merkle.py -k no_two_leaf_lists_share_a_root -v
```

- [ ] 복제 검사

```
uv run pytest tests/unit/test_merkle.py -k does_not_duplicate -v
```

- [ ] 증명 왕복

```
uv run pytest tests/unit/test_merkle.py -k proof -v
```

- [ ] 머클 전부

```
uv run pytest tests/unit/test_merkle.py -v
```

- [ ] 블록·체인 — **여기서 (3)(4)가 판정된다**

```
uv run pytest tests/unit/test_block.py tests/unit/test_chain_validation.py -v
```

- [ ] 린터와 타입 검사

```
uv run ruff check
```
```
uv run mypy src/
```

### 통과해야 할 테스트 이름

`tests/unit/test_merkle.py`
- `test_merkle_root_is_deterministic`
- `test_merkle_root_is_deterministic_property`
- `test_merkle_root_changes_on_leaf_change`
- `test_merkle_root_changes_on_reorder`
- `test_merkle_root_single_leaf`
- `test_merkle_root_odd_leaves`
- `test_merkle_root_does_not_duplicate_last_leaf`
- **`test_no_two_leaf_lists_share_a_root`** ← 1절 뒷부분에서 일부러 깨뜨린 그것
- `test_proof_roundtrip_all_indices`
- `test_proof_fails_for_wrong_leaf`
- `test_leaf_and_node_hashes_are_domain_separated`
- `test_merkle_root_empty_leaves_is_defined`
- `test_proof_length_is_logarithmic`

`tests/unit/test_block.py` — **여기 두 개가 이 랩에서 초록이 된다**
- **`test_block_hash_input_excludes_txs`** ← 과제 (3)
- **`test_tampering_a_post_still_changes_block_hash`** ← 과제 (3)을 하고도 글 변조가 잡히는가

`tests/unit/test_chain_validation.py` — **Lab 1.3부터 있던 것이 과제 (4)를 강제한다**
- **`test_tampered_body_reports_first_bad_index`**
- `test_tampered_body_with_recomputed_merkle_root_breaks_the_next_link`
- (나머지 Lab 1.3 테스트도 계속 초록이어야 한다)

### 실패하면

| 화면 | 먼저 볼 곳 |
|---|---|
| `test_no_two_leaf_lists_share_a_root`가 여전히 빨갛다 | 홀수 리프 처리가 그대로다. 랩 §3의 규칙을 다시 읽어라 |
| 루트는 고쳤는데 `test_proof_*`가 실패 | 증명 생성 쪽을 같은 규칙으로 안 고쳤다. 랩 §5 표를 보라 |
| `test_block_hash_input_excludes_txs`만 초록, 뒤가 빨갛다 | 🔴 과제 (2)를 안 했다. `merkle_root`가 글을 커밋하지 못한다 |
| `test_tampered_body_reports_first_bad_index`가 빨갛다 | 🔴 과제 (4)를 안 했다. `validate`가 머클을 재계산하지 않는다 |
| Lab 1.3 테스트가 갑자기 전부 빨갛다 | **정상일 수 있다.** 해시 정의를 바꿨다. 픽스처가 아니라 네 코드가 일관적인지 보라 |

속성 테스트 반례 읽는 법 →
[테스트 실행법 — 속성 기반 테스트의 반례 읽는 법](../테스트-실행법.md#속성-기반-테스트의-반례-읽는-법)
`FAILED`와 `ERROR`의 차이 →
[테스트 실행법 — failed와 error는 다르다](../테스트-실행법.md#failed와-error는-다르다)

---

## 8. 눈으로 확인

**이 랩의 목적은 숫자 하나를 직접 보는 것이다.**

```
uv run python -c "
from bbschain.core.merkle import merkle_root, merkle_proof
for n in (4, 1024):
    leaves = [f'post-{i}'.encode() for i in range(n)]
    print(f'글 {n:>5}개 -> 증명에 필요한 해시 {len(merkle_proof(leaves, n // 2))}개')
"
```

```
글     4개 -> 증명에 필요한 해시 2개
글  1024개 -> 증명에 필요한 해시 10개
```

- [ ] **글 수는 256배인데 증명은 5배**다. 이 숫자를 직접 봤다

**그리고 블록이 무엇을 커밋하는지 다시 본다.**

```
uv run python workbook/phase-1/experiments/03_block_hash_probe.py
```

- [ ] (A)의 마지막 줄 `txs (글 본문)`이 이제 **"그대로"** 로 바뀌었다 — 과제 (3)이 됐다는 뜻이다
- [ ] 그런데도 `validate()`는 본문 변조를 잡는다 — 과제 (4)가 됐다는 뜻이다

**📝 스스로 답하라**

> `Block.hash`의 입력에서 `txs`를 뺐는데, 왜 글을 고치면 여전히 잡히나?

```


```

---

## 9. 회고 3줄

```
배운 것:

헛짚은 것:

다음에 확인할 것:
```

**한 줄 더 — 이 랩에만 있는 칸이다.**

```
내가 처음 고른 홀수 리프 처리 방식:
반례를 보고 바꾼 것:
```

---

## 10. 기록

- [ ] 회고 3줄을 [PROGRESS.md 회고 기록](../../docs/PROGRESS.md#회고-기록)에 옮긴다 (**정본은 PROGRESS.md다**)
- [ ] 1절 뒷부분의 ①②③ 답을 [PROGRESS.md](../../docs/PROGRESS.md#phase-1--단일-노드-체인--게시판-코어)에 옮긴다
- [ ] [PROGRESS.md](../../docs/PROGRESS.md#phase-1--단일-노드-체인--게시판-코어)의 `Lab 1.4` 체크박스를 켠다
- [ ] [ADR-0001](../../docs/decisions/ADR-0001-canonical-serialization.md)에 빈 리프 규칙과 도메인 분리 방식을 적었다
- [ ] 커밋한다

```
git status
git add src/bbschain/core docs/PROGRESS.md docs/decisions/ADR-0001-canonical-serialization.md
git commit -m "Lab 1.4: merkle root and inclusion proofs, header-only block hash"
```

---

다음 → [Lab 1.5 따라하기](lab-1.5.md)
