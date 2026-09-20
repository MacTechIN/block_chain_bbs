# Lab 1.5 따라하기 — 영속화와 검증 CLI

| 대응 랩 | 이론 | 시작 파일 | 예상 소요 |
|---|---|---|---|
| [Lab 1.5](../../docs/labs/phase-1-chain.md#lab-15--영속화와-검증-cli) | [튜토리얼 Lab 1.5](../../docs/tutorial/phase-1.md#lab-15--영속화와-검증-cli) | [`starter/storage/`](starter/README.md) 두 개 | 2~3시간 |

> 참고 문서 — 막히면 여기로.
> [테스트 실행법](../테스트-실행법.md) · [설정 가이드](../phase-0/설정-가이드.md) · [시작 파일 안내](starter/README.md)

## 이 시트로 뭘 하나

지금까지의 체인은 **프로세스가 죽으면 같이 사라진다.** 파일에 저장한다.
그러면 두 가지 새 문제가 생긴다 — 저장했다 읽으면 정말 **같은 것**이 돌아오나,
저장 중에 죽으면 파일은 어떤 상태가 되나.

그리고 이 랩의 진짜 목적이 하나 더 있다.
**Phase 2에서 저장소를 SQLite로 갈아끼울 때 코어를 한 줄도 안 건드리게** 만드는 것이다.

**Phase 1의 결승선이 이 랩이다.** 끝나면 Lab 1.2의 공격을 다시 해서 거부당하는 화면을 얻는다.

---

## 0. 준비

- [ ] 터미널을 **저장소 루트**에서 연다
- [ ] Lab 1.4가 초록이다

```
uv run pytest tests/unit/test_merkle.py tests/unit/test_block.py tests/unit/test_chain_validation.py
```

- [ ] 전부 통과한다

**이 랩이 만들 것을 테스트에 물어본다.**

```
uv run pytest tests/unit/test_storage_jsonfile.py 2>&1 | head -20
```

```
E        대상 : bbschain.storage.base
E        랩   : Lab 1.5 — 영속화와 검증 CLI   (docs/labs/phase-1-chain.md)
E        필요 : class Storage(Protocol): append_block/get_block/tip/iter_blocks/height
```

- [ ] 안내 배너를 봤다

---

## 1. 먼저 깨져보기 ⚔

**보려는 것**: 아무것도 변조하지 않았는데 **저장했다 읽은 것만으로 체인이 깨지는 것.**

### ① 추상화 없이 대충 저장해 본다

`labs/` 아래에 스크래치로 만든다. `src/`에 넣지 마라. 버릴 코드다.

```
uv run python -c "
import json
from dataclasses import asdict
from bbschain.core.block import Post, Block
b = Block(index=0, prev_hash='0'*64, timestamp=1700000000,
          merkle_root='7'*64, nonce=0, difficulty=0,
          txs=(Post('sam', '첫 글', 1700000000),))
raw = json.dumps(asdict(b))
back = Block(**json.loads(raw))
print('원본 :', b.hash)
print('복원 :', back.hash)
print('같은가:', b.hash == back.hash)
print('txs 타입:', type(back.txs).__name__)
"
```

```
원본 : 6b69fed422e1...
복원 : 2f0c1a44d8e9...
같은가: False
txs 타입: list
```

> 위 해시 값은 네 `canonical_bytes` 규칙에 따라 다르다. **`같은가: False`가 나오는지만 봐라.**
> (`Post` 복원까지 제대로 안 했으니 다른 에러가 날 수도 있다. 그것도 수확이다.)

- [ ] **아무것도 변조하지 않았는데** 해시가 달라졌다
- [ ] `txs`가 `tuple`이 아니라 `list`로 돌아왔다

### ② 체인으로 하면 어떻게 보이나

이 상태로 `validate()`를 돌리면 이렇게 나온다.

```
ValidationResult(ok=False, first_bad_index=1, reason='block hash mismatch')
```

**`first_bad_index=1`이 그 신호다.** 변조가 아니라 **왕복 실패**다.

### ③ 저장 도중에 죽여 본다

글 10000개를 넣고 저장하는 도중에 **Ctrl+C**를 누른다. 그리고 파일을 열어 본다.

```
posts.json 이 JSON 문법 중간에서 잘려 있음
```

### ④ 그 상태에서 다시 로드한다

```
json.decoder.JSONDecodeError: Expecting ',' delimiter: line 1 column 48213
```

- [ ] **체인 전체를 잃었다**

**📝 네가 본 것을 여기 적어라**

```
① 왕복 후 해시:
① txs 타입:
③ 죽은 뒤 파일 상태:
④ 다시 읽었을 때:

(무엇이 왕복(round-trip)하지 않았나?)


```

**📝 랩의 질문 — ③번이 이 랩이 존재하는 이유다**

> ① 아무것도 변조하지 않았는데 왜 해시가 달라졌나?
> ② 파일이 반쯤 쓰인 상태가 된 이유는? 이걸 막는 표준적인 방법의 이름은?
> ③ Phase 2에서 SQLite로 바꾸려면 지금 코드의 **어디어디를** 고쳐야 하나? **몇 군데인가?**

```


```

---

## 2. 사전지식 — 답을 먼저 적고 튜토리얼을 연다

> **못 답해도 괜찮다. 모른다고 적는 것도 답이다.**

**Q1. JSON에서 왕복하지 않는 파이썬 타입을 3개 이상 대라.**

```


```

**Q2. "원자적 쓰기(atomic write)"란 무엇이고 파일 시스템에서 어떻게 구현하나?**

```


```

**Q3. `Protocol`(구조적 서브타이핑)과 ABC(명목적 상속)의 차이는? 여기선 왜 Protocol이 나은가?**

```


```

- [ ] 적었다 → [튜토리얼 Lab 1.5](../../docs/tutorial/phase-1.md#lab-15--영속화와-검증-cli)를 읽는다
- [ ] 읽고 답을 **고쳐 적었다**

### 실험으로도 확인한다

```
uv run python workbook/phase-1/experiments/02_json_bytes.py
```

- [ ] (C) 구획에서 `tuple`이 `list`가 되고 int 키가 문자열이 되는 것을 **다시** 봤다
      — Lab 1.1에서 본 것과 같은 화면인데, 이제 왜 치명적인지 안다

**📝 예상과 달랐던 것**

```


```

---

## 3. 코드를 어디에 쓰나

**만들 파일 셋.**

| 과제 | 만들 파일 | 시작 파일 |
|---|---|---|
| (1) 저장소 인터페이스 | `src/bbschain/storage/base.py` | [`starter/storage/base.py`](starter/storage/base.py) |
| (2) JSON 파일 구현 | `src/bbschain/storage/jsonfile.py` | [`starter/storage/jsonfile.py`](starter/storage/jsonfile.py) |
| (3) CLI | `src/bbschain/cli.py` | **없다** — Phase 0 스텁이 이미 있다. 통째로 갈아엎는다 |

그리고 한 쌍이 더 필요하다: **`Block` ↔ `dict` 변환(`to_dict` / `from_dict`).**
**어디에 둘지는 네가 정한다** (랩 §4 L2가 묻는다). `block.py`냐 `jsonfile.py`냐.
판정기는 `Block.to_dict()`/`Block.from_dict(d)`와 모듈 레벨 함수를 모두 받아 준다.

### 새 폴더가 필요하다

`src/bbschain/storage/`는 **아직 없다.**

```
mkdir -p src/bbschain/storage
touch src/bbschain/storage/__init__.py
```

- [ ] 만들었다

### 시작 파일을 복사한다 — 🔴 **한 번에 하나씩**

**지금은 인터페이스만.**

```
cp workbook/phase-1/starter/storage/base.py src/bbschain/storage/base.py
```

- [ ] 복사했다

### import는 어떻게 해석되나

```
uv run python -c "import bbschain.storage.base; print('ok')"
```

- [ ] `ok`가 나온다

**CLI는 다르다.** `src/bbschain/cli.py`는 이미 있고, `pyproject.toml`의
`[project.scripts]`가 그 파일의 `main`을 가리킨다. 그래서 `bbschain` 명령이 이미 존재한다.

```
uv run bbschain --help
```

```
bbschain CLI 는 아직 구현되지 않았다. Lab 1.5 (docs/labs/phase-1-chain.md) 를 보라.
```

- [ ] 안내가 나온다. **이 파일의 내용을 갈아엎으면 된다.** `uv sync`는 필요 없다

---

## 4. 코드를 어떤 순서로 쓰나

**(1) → (2) → (3) 순서다.** 뒤가 앞에 의존한다.

### 1단계 — 판정할 테스트를 먼저 읽는다

```
uv run pytest tests/unit/test_storage_jsonfile.py -v
```

특히 두 개를 열어 보고 무엇을 요구하는지 확인해라.

- `test_storage_has_no_mutation_method` — 금지된 메서드 이름 목록이 파일 안에 있다
- `test_atomic_write_survives_interruption` — **쓰기 도중에 죽는 상황을 진짜로 만든다**

### 2단계 — 만족해야 할 불변식을 확인한다

정본은 [랩 §3](../../docs/labs/phase-1-chain.md#lab-15--영속화와-검증-cli)이다.
시작 파일 주석에 요점이 있다. **세 줄로 다시 써 보라.**

```
저장했다 읽으면 →

쓰다가 죽으면 →

파일이 없으면 →
```

### 3단계 — 가장 단순한 경우부터 채운다

**(1) `base.py` — 선언만이다. 5분이면 끝난다.**

```
uv run pytest tests/unit/test_storage_jsonfile.py -k mutation -v
```

- [ ] 이거 하나가 초록이 된다

**(2) `jsonfile.py` — 블록 0개 → 1개 → 여러 개.**

```
cp workbook/phase-1/starter/storage/jsonfile.py src/bbschain/storage/jsonfile.py
```

먼저 **빈 저장소**부터. 파일이 없을 때 `height()==0`, `tip() is None`이 되는지 본다.

```
uv run pytest tests/unit/test_storage_jsonfile.py -k empty -v
```

그다음 블록 **하나**를 넣고 읽어 본다. 여기서 `to_dict`/`from_dict` 쌍이 필요해진다.

```
uv run pytest tests/unit/test_serialize.py -k roundtrip -v
```

🔴 **왕복이 안 되면 그 뒤는 전부 실패한다.** 여기를 먼저 초록으로 만들어라.

**(3) `cli.py` — 네 명령. `verify`부터.**

순서를 권하면 이렇다.

```
verify   →  체인을 읽고 validate() 결과를 출력한다. 종료 코드 0 / 1
post     →  글 하나를 넣는다
dump     →  체인을 출력한다
tamper   →  🔴 환경변수 게이트부터. 게이트 없이 도는 코드를 먼저 쓰지 마라
```

> ⚠️ **CLI의 체인 파일 경로는 현재 디렉터리 기준 상대 경로**여야 한다 (예: `./chain.json`).
> 테스트가 작업 디렉터리를 임시 폴더로 옮긴 뒤 부르기 때문이다.
> 절대 경로나 홈 디렉터리를 쓰면 `test_cli.py`가 통째로 실패한다.

### 4단계 — 좁은 범위부터 테스트를 돌린다

```
uv run pytest tests/unit/test_storage_jsonfile.py -v
```
```
uv run pytest tests/integration/test_restart_roundtrip.py -v
```
```
uv run pytest tests/unit/test_cli.py -v
```

### 5단계 — 실패 메시지를 읽고 고친다

| 화면 | 먼저 볼 곳 |
|---|---|
| 재시작 후 `first_bad_index=1` | `tuple` → `list` 왕복 실패. `from_dict`에서 되돌려야 한다 |
| 타임스탬프가 `1700000000.0` | 어딘가에서 float으로 만들었다. `int`로 고정 |
| `test_storage_has_no_mutation_method` 빨강 | 인터페이스나 구현에 금지된 이름의 메서드가 있다 |
| `test_chain_does_not_import_the_json_implementation` 빨강 | `core/chain.py`가 구체 구현을 import했다 |
| `cli_chain_file` 픽스처가 "체인 파일이 안 생겼다" | 경로가 상대 경로가 아니다 |

읽는 순서 → [테스트 실행법 — 실패 메시지 읽는 순서](../테스트-실행법.md#실패-메시지-읽는-순서)

---

## 5. 과제

**정본은 랩 문서다** → [Lab 1.5 §3 과제](../../docs/labs/phase-1-chain.md#lab-15--영속화와-검증-cli)

**만들 파일**

- `src/bbschain/storage/base.py` — 과제 (1)
- `src/bbschain/storage/jsonfile.py` — 과제 (2)
- `src/bbschain/cli.py` — 과제 (3). Phase 0 스텁을 통째로 교체한다
- `Block.to_dict()` / `Block.from_dict()` 쌍 — **어디에 둘지는 네 결정**

**이 시트에 과제 내용을 옮겨 적지 않는다.** CLI 명령 4개의 사양은 랩 3절에 있다.

- [ ] 🔴 `tamper`에 **환경변수 게이트**를 걸었다. 변수가 없으면 아무것도 하지 않고 거부한다 (종료 코드 2)
- [ ] `Storage`에 수정·삭제 메서드를 만들지 않았다
- [ ] `Chain`이 `JsonFileStorage`를 직접 import하지 않는다

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

힌트는 랩 문서 4절에 접혀 있다 → [Lab 1.5 §4](../../docs/labs/phase-1-chain.md#lab-15--영속화와-검증-cli)

| | 연 시각 | 그때 막혀 있던 것 |
|---|---|---|
| L1 | | |
| L2 | | |
| L3 | | |
| 리뷰 요청 | | |

- [ ] 30분 넘게 막혔다면 [PROGRESS.md 막힌 지점 로그](../../docs/PROGRESS.md#막힌-지점-로그)에 **지금** 한 줄 적었다

---

## 7. 테스트하기

**좁은 범위부터 넓혀 간다.**

- [ ] 인터페이스

```
uv run pytest tests/unit/test_storage_jsonfile.py -k mutation -v
```

- [ ] 왕복

```
uv run pytest tests/unit/test_serialize.py -k roundtrip -v
```

- [ ] 저장소 전부

```
uv run pytest tests/unit/test_storage_jsonfile.py -v
```

- [ ] 재시작

```
uv run pytest tests/integration/test_restart_roundtrip.py -v
```

- [ ] CLI

```
uv run pytest tests/unit/test_cli.py -v
```

- [ ] 🔴 **Phase 1 전부** — 이게 이 랩의 결승선이다

```
uv run pytest tests/unit tests/integration -v
```

- [ ] 린터와 타입 검사

```
uv run ruff check
```
```
uv run mypy src/
```

### 통과해야 할 테스트 이름

`tests/unit/test_storage_jsonfile.py`
- `test_append_and_read_back`
- `test_empty_storage_is_empty`
- `test_get_block_by_hash_and_index`
- `test_storage_has_no_mutation_method`
- `test_chain_does_not_import_the_json_implementation`
- `test_atomic_write_survives_interruption`

`tests/unit/test_serialize.py`
- `test_block_dict_roundtrip` (hypothesis property — 임의 블록)

`tests/integration/test_restart_roundtrip.py`
- `test_restart_preserves_chain`
- `test_restart_preserves_korean_bodies`
- `test_restart_preserves_arbitrary_chains` (hypothesis property)

`tests/unit/test_cli.py`
- `test_verify_exit_code_zero_on_valid`
- `test_verify_exit_code_one_on_tampered`
- `test_tamper_refuses_without_env_gate`
- `test_tamper_refusal_exit_code_is_two`
- `test_post_appends_one_block_and_dump_shows_it`

### 실패하면

1. `FAILED`인가 `ERROR`인가
   (→ [테스트 실행법 — failed와 error는 다르다](../테스트-실행법.md#failed와-error는-다르다))
2. 마지막 `E` 줄의 한국어 설명
3. 4절 5단계의 표에서 증상을 찾는다
4. → [테스트 실행법 — 막혔을 때 확인 순서](../테스트-실행법.md#막혔을-때-확인-순서)

**속성 테스트가 실패했다면** `Failing test case:` 블록에 최소 반례가 찍힌다.
`test_block_dict_roundtrip`과 `test_restart_preserves_arbitrary_chains`가 그것이다.
**어떤 필드가 왕복하지 않았는지**를 그 값에서 읽어라 →
[테스트 실행법 — 속성 기반 테스트의 반례 읽는 법](../테스트-실행법.md#속성-기반-테스트의-반례-읽는-법)

---

## 8. 눈으로 확인

**Phase 1의 결승선이다.** 랩 6절이 요구하는 화면을 직접 만든다.

```
uv run bbschain post --author sam --body "첫 글"
```

```
block #1 mined  hash=a3f1...  merkle=7c2e...
```

열 번 반복한 뒤,

```
uv run bbschain verify
```

```
VALID   height=10   tip=8e41c2...
```

```
echo $?
```

```
0
```

이제 **에디터로 `chain.json`을 열고 3번 블록의 `body`에서 글자 하나를 바꾼다.**
Lab 1.2에서 했던 것과 **똑같은 공격**이다.

```
uv run bbschain verify
```

```
INVALID: block #3 hash mismatch
         reason: block hash does not match its contents
         blocks #4..#10 invalidated (chain broken from #3)
```

```
echo $?
```

```
1
```

- [ ] 정상 체인에서 종료 코드 **0**
- [ ] 변조 후 종료 코드 **1**
- [ ] `tamper`를 환경변수 없이 실행하면 **거부**당하고 체인이 그대로다

```
uv run bbschain tamper --index 3 --field body --value "아무거나"
```

```
REFUSED: 이 명령은 실습용 파괴 도구다. 환경변수 게이트 없이는 실행하지 않는다.
```

- [ ] 거부됐고 종료 코드가 0이 아니다

**📝 🔴 이 두 장면을 나란히 남긴다**

- [ ] Lab 1.2의 "변조했는데 아무 일도 안 일어난 화면"
- [ ] 방금의 "같은 공격이 거부당한 화면"
- [ ] 두 장을 [PROGRESS.md](../../docs/PROGRESS.md#phase-1--단일-노드-체인--게시판-코어)의
      "보여줄 수 있는 한 장면"에 남겼다

**같은 공격, 다른 결과. 이게 Phase 1의 전부다.**

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
- [ ] [PROGRESS.md](../../docs/PROGRESS.md#phase-1--단일-노드-체인--게시판-코어)의 `Lab 1.5` 체크박스를 켠다
- [ ] Phase 1 **DoD** 항목을 확인하고 켠다 — **랩을 다 했어도 DoD 확인이 안 됐으면 켜지 않는다**
- [ ] 커밋한다

```
git status                 # chain.json, *.key, .env 가 안 잡히는지 확인
git add src/bbschain docs/PROGRESS.md
git commit -m "Lab 1.5: append-only storage, atomic writes, and the verify CLI"
```

> `chain.json`은 `.gitignore`에 이미 있다. 커밋되면 안 된다 — **체인은 코드가 아니라 데이터다.**

---

다음 → [SQ 1.6 따라하기](sq-1.6.md) (사이드 퀘스트. 건너뛰어도 Phase 2로 갈 수 있다)
