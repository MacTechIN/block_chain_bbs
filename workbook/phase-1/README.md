# Phase 1 워크북 — 변조를 탐지하는 체인 만들기

**여기가 이 프로젝트에서 가장 중요한 Phase다.**
Phase 2~7에서 붙는 것들(탐색기·지갑·채굴·P2P·앵커링)은 전부 여기서 만든 것 **위에** 얹힌다.

Phase 0에서는 블록체인이 한 줄도 없었다. 판정기만 만들었다.
**Phase 1부터는 전부 직접 만든다.** 대행은 없다.

> 시작 전에 이 세 문서를 훑어 둬라. 랩이 아니라 참고 문서다.
> - [시작 파일 안내](starter/README.md) — 빈 화면 대신 어디서 출발하나
> - [테스트 실행법](../테스트-실행법.md) — 테스트 명령과 실패 메시지 읽는 법
> - [설정 가이드](../phase-0/설정-가이드.md) — 새 모듈은 어디에 어떻게 만드나

---

## 무엇을 만들게 되나

한 문장으로: **파일을 직접 고쳐도 프로그램이 알아채는 게시판.**

Lab 1.2에서 게시판 파일을 열어 3번 글을 바꿔 본다. 프로그램은 눈치도 못 챈다.
Lab 1.5가 끝나면 **똑같은 공격**을 다시 한다. 이번엔 이렇게 나온다.

```
$ bbschain verify
INVALID: block #3 hash mismatch
         reason: block hash does not match its contents
         blocks #4..#10 invalidated (chain broken from #3)
$ echo $?
1
```

**같은 공격, 다른 결과.** 이 두 화면을 나란히 놓는 것이 Phase 1의 결승선이다.

Phase가 끝나면 `src/bbschain/` 아래에 이것들이 생긴다.

```
src/bbschain/
├─ core/
│  ├─ serialize.py    같은 데이터 → 언제나 같은 바이트열
│  ├─ hashing.py      바이트열 → 64자 지문
│  ├─ block.py        글(Post)과 블록(Block), 그리고 블록의 지문
│  ├─ merkle.py       글 집합을 값 하나로 요약 + 포함 증명
│  └─ chain.py        블록을 잇고, 어디서 깨졌는지 지목
├─ storage/
│  ├─ base.py         저장소 인터페이스 (append-only)
│  └─ jsonfile.py     JSON 파일 구현 (원자적 쓰기)
└─ cli.py             post / dump / verify / tamper
```

**전부 네가 만든다.** [시작 파일](starter/README.md)이 시그니처와 불변식까지만 준다.

---

## Phase 1의 4박자

이 Phase는 네 박자로 굴러간다. **문제를 먼저 겪고, 그다음에 방어를 붙인다.**

| | 무엇 | 어느 랩 |
|---|---|---|
| ① 취약 버전 | 해시 없는 JSON 글 목록 | Lab 1.2 |
| ② 직접 공격 | 파일을 열어 3번 글을 바꾼다 — **앱은 눈치도 못 챈다** | Lab 1.2 |
| ③ 방어 도입 | `prev_hash` 체인 + `validate_chain()` | Lab 1.3 |
| ④ 재공격 | 똑같이 변조 → **파손 지점을 지목당한다** | Lab 1.3 §6, Lab 1.5 |

Lab 1.1은 ① 이전의 준비 운동이고, Lab 1.4~1.5는 ④ 이후의 확장이다.

---

## 순서

```
lab-1.1.md   해시 감각 잡기           (1시간)    같은 내용인데 해시가 달라지는 사고
    ▼                                            없으면 → 두 노드가 영원히 합의 못 한다
lab-1.2.md   취약한 게시판과 변조 ⚔   (1~2시간)  무결성이 없다는 것의 실물
    ▼                                            없으면 → 왜 방어가 필요한지 영영 모른다
lab-1.3.md   블록과 체인              (3~5시간)  canonical_bytes, prev_hash, 파손 전파
    ▼                                            ← Phase 1의 본체. 파일 네 개
lab-1.4.md   머클 루트 ⚔             (3~4시간)  머클 트리, CVE-2012-2459, 헤더 해시
    ▼                                            ← 가장 교육적인 실패 장면이 여기 있다
lab-1.5.md   영속화와 검증 CLI        (2~3시간)  Storage 프로토콜, 재시작 복원
    ▼                                            ← Phase 1의 결승선
sq-1.6.md    Sepolia 맛보기 🌐        (0.5일)    내 장난감 체인 vs 실제 체인 (선택)
```

- [ ] [Lab 1.1 따라하기](lab-1.1.md) — 해시 감각 잡기
- [ ] [Lab 1.2 따라하기](lab-1.2.md) — 취약한 게시판과 변조
- [ ] [Lab 1.3 따라하기](lab-1.3.md) — 블록과 체인
- [ ] [Lab 1.4 따라하기](lab-1.4.md) — 머클 루트
- [ ] [Lab 1.5 따라하기](lab-1.5.md) — 영속화와 검증 CLI
- [ ] [SQ 1.6 따라하기](sq-1.6.md) — Sepolia 맛보기 (**선택. DoD가 아니다**)

**순서를 지켜라.** 뒤 랩이 앞 랩의 산출물을 쓴다.
그리고 **앞 랩에서 겪은 아픔이 뒤 랩의 존재 이유다.**

### 🔴 Lab 1.4는 순서가 특별하다

다른 랩은 "읽고 만들고 통과"지만 1.4는 다르다.

> **일부러 취약하게 먼저 만든다 → 속성 테스트가 반례를 들이민다 → 그걸 보고 고친다.**

튜토리얼도 그래서 **읽기 A / 읽기 B**로 갈라져 있다.
**읽기 B를 미리 열면 그 장면이 사라진다.** [시트](lab-1.4.md)가 언제 어느 쪽을 열지 알려 준다.

---

## 시작 파일 — 빈 화면에서 시작하지 않는다

함수 이름, 인자, 타입, 불변식은 이미 랩이 정해 뒀다. 받아 적는 데 시간을 쓰지 마라.
[`starter/`](starter/README.md)에 파일 일곱 개가 있다.

들어 있는 것: 시그니처 · 독스트링 · 불변식 주석 · 판정 명령 · `raise NotImplementedError`
들어 있지 않은 것: **힌트와 구현.** 힌트는 랩 문서 4절에 L1/L2/L3로 있다.

🔴 **한 번에 다 복사하지 마라. 랩이 시킬 때 하나씩.**
이유는 [starter/README.md](starter/README.md)에 있다 — 요약하면 **안내 배너를 잃지 않기 위해서**다.

---

## 관찰 실험

읽고 고개를 끄덕이는 것과, 숫자를 직접 세는 것은 다른 일이다.

```
uv run python workbook/phase-1/experiments/01_hash_avalanche.py
uv run python workbook/phase-1/experiments/02_json_bytes.py
uv run python workbook/phase-1/experiments/03_block_hash_probe.py
```

`03`은 **네가 만든 `Block`을 불러다 찔러 본다.** 구현이 아직 없으면 친절하게 안내하고 끝난다.
그리고 **Lab 1.3 직후와 Lab 1.4 직후에 출력이 달라진다** — 그 차이가 이 실험의 핵심이다.

각각 무엇을 보여주는지는 [experiments/README.md](experiments/README.md)에 표로 있다.

**돌리기 전에 결과를 예상하고 나서 실행하라.** 예상과 다른 지점이 수확이다.

---

## 테스트는 이미 다 쓰여 있다

🔴 **`tests/`를 고치지 마라.** Phase 1용 테스트 8개 파일이 이미 저장소에 있다.
지금 돌리면 전부 실패한다. **그게 정상이다.**

실패 화면이 "어느 모듈의 어떤 함수를 만들면 되는지"를 직접 말해 준다.

```
uv run pytest tests/unit/test_merkle.py
```

```
E        대상 : bbschain.core.merkle
E        랩   : Lab 1.4 — 머클 루트   (docs/labs/phase-1-chain.md)
E        필요 : merkle_root(leaves), merkle_proof(leaves, index), verify_proof(leaf, proof, root)
```

**이건 고장이 아니라 할 일 목록이다.**
→ [테스트 실행법 — 안내 배너](../테스트-실행법.md#아직-구현이-없을-때-뜨는-안내-배너)

| 랩 | 초록으로 만들 테스트 파일 |
|---|---|
| Lab 1.3 | `tests/unit/test_serialize.py`, `test_block.py`(앞쪽), `test_chain_validation.py` |
| Lab 1.4 | `tests/unit/test_merkle.py`, `test_block.py`(뒤쪽 두 개) |
| Lab 1.5 | `tests/unit/test_storage_jsonfile.py`, `test_cli.py`, `tests/integration/` |

> `uv run pytest`를 인자 없이 부르면 스모크 2개만 돈다. Phase 1 테스트는 **경로를 명시해야** 돈다.
> 왜 그런지는 → [테스트 실행법 — 이 저장소에만 있는 규칙](../테스트-실행법.md#이-저장소에만-있는-규칙--왜-2개만-도나)

---

## 여기서 정하면 끝까지 못 바꾸는 것

Phase 1에서 고정하는 계약이 다섯 개다. **나중에 바꾸면 쌓아 둔 체인이 전부 무효가 된다.**

| | 무엇 | 어느 랩 |
|---|---|---|
| 1 | `canonical_bytes(obj) -> bytes` — 해시 입력의 유일한 통로 | 1.3 |
| 2 | `Block`의 필드 집합과 `hash`의 입력 | 1.3 → 1.4에서 최종형 |
| 3 | `validate()`가 `bool`이 아니라 `ValidationResult`를 낸다 | 1.3 |
| 4 | `Storage` 프로토콜 (append-only) | 1.5 |
| 5 | `Post`의 필드 집합 `(author, body, ts, nonce, sig)` | 1.3 |

정본은 → [개발계획서 6절](../../docs/01-개발계획서.md#phase-1에-고정할-핵심-계약)
직렬화 규칙의 결정 기록은 → [ADR-0001](../../docs/decisions/ADR-0001-canonical-serialization.md)

**쓰지도 않을 `nonce`와 `difficulty`를 지금 넣는 이유**가 이 표에 있다.
Phase 4에서 추가하면 그때까지 쌓은 모든 블록 해시가 바뀐다. **보험이지 낭비가 아니다.**

---

## Phase 1을 닫기 전에

마무리 점검 — 전부 [PROGRESS.md](../../docs/PROGRESS.md#phase-1--단일-노드-체인--게시판-코어)에서 켠다.

- [ ] 랩 체크박스 5개
- [ ] DoD 항목 — **랩을 다 했어도 DoD 확인이 안 됐으면 켜지 않는다**
- [ ] 회고 3줄 × 랩 수 → [회고 기록](../../docs/PROGRESS.md#회고-기록)
- [ ] 🔴 "보여줄 수 있는 한 장면" — **Lab 1.2의 변조 성공 화면과 Lab 1.5의 변조 탐지 화면, 두 장 나란히**

**그리고 자가 점검.** 다음 질문에 막힘없이 답할 수 있나.
정본은 [랩 문서의 Phase 1 마무리](../../docs/labs/phase-1-chain.md#phase-1-마무리)에 7개가 있다.
그중 두 개만 여기 옮긴다 — **이 둘에 막히면 Phase 2로 가지 마라.**

1. 공격자가 3번 블록부터 끝까지 전부 재계산하면 지금 내 검증을 통과하는가? 그걸 막는 게 있나?
2. 내 체인이 진짜로 안전하지 않은 이유를 **두 가지** 대라.
   (힌트: 하나는 Phase 4가, 하나는 Phase 5가 푼다)

---

다음 → Phase 2 (랩 문서는 Phase 2에 진입할 때 작성한다.
[개발계획서 Phase 2](../../docs/01-개발계획서.md#phase-2--블록-탐색기-v1--저장소-교체-35일) 참고)
