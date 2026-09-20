# Phase 1 랩 — 단일 노드 체인 + 게시판 코어

> 랩 템플릿·힌트 규칙·에스컬레이션은 [학습계획서](../03-학습계획서.md)에 있다.
> Phase 1의 목표와 DoD는 [개발계획서 Phase 1](../01-개발계획서.md#phase-1--단일-노드-체인--게시판-코어-24일)에 있다.
> 체크와 회고는 [PROGRESS.md](../PROGRESS.md)에 기록한다.

**여기가 이 프로젝트에서 가장 중요한 Phase다.**
Phase 2~7에서 붙는 것들(탐색기·지갑·채굴·P2P·앵커링)은 전부 여기서 만든 것 **위에** 얹힌다.
그리고 여기서 정한 세 가지(`canonical_bytes`, `Block` 필드 집합, `Post` 필드 집합)는 **나중에 바꾸면 기존 체인이 전부 무효가 된다.**
→ [개발계획서 6절 "Phase 1에 고정할 핵심 계약"](../01-개발계획서.md#phase-1에-고정할-핵심-계약)

### Phase 1의 4박자

| | 무엇 | 어느 랩 |
|---|---|---|
| ① 취약 버전 | 해시 없는 JSON 글 목록 | Lab 1.2 |
| ② 직접 공격 | 파일을 열어 3번 글을 바꾼다 — **앱은 눈치도 못 챈다** | Lab 1.2 |
| ③ 방어 도입 | `prev_hash` 체인 + `validate_chain()` | Lab 1.3 |
| ④ 재공격 | 똑같이 변조 → **파손 지점을 지목당한다** | Lab 1.3 §6, Lab 1.5 |

Lab 1.1은 ① 이전의 준비 운동(해시 자체의 성질), Lab 1.4~1.5는 ④ 이후의 확장이다.

### 랩 목록

| 랩 | 제목 | 소요 | 핵심 |
|---|---|---|---|
| [1.1](#lab-11--해시-감각-잡기) | 해시 감각 잡기 | 1시간 | 결정성, 눈사태 효과, **같은 내용인데 해시가 달라지는 사고** |
| [1.2](#lab-12--취약한-게시판과-변조) | 취약한 게시판과 변조 ⚔ | 1~2시간 | 무결성이 없다는 것의 실물 |
| [1.3](#lab-13--블록과-체인) | 블록과 체인 | 3~5시간 | `canonical_bytes`, `prev_hash`, 파손 전파 |
| [1.4](#lab-14--머클-루트) | 머클 루트 ⚔ | 3~4시간 | 머클 트리, 왜 루트 하나로 충분한가, **CVE-2012-2459**, **해시 입력을 헤더만으로 줄이기** |
| [1.5](#lab-15--영속화와-검증-cli) | 영속화와 검증 CLI | 2~3시간 | `Storage` 프로토콜, 재시작 복원 |
| [SQ 1.6](#sq-16--sepolia-맛보기-사이드-퀘스트) | Sepolia 맛보기 🌐 | 0.5일 | 내 장난감 체인 vs 실제 체인 |

---

## Lab 1.1 — 해시 감각 잡기

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 1시간 | Phase 0 완료 | `labs/hash_play.py` (스크래치), 관찰 메모 | ★★☆☆☆ |

### 0. 왜 이게 필요한가

블록체인의 거의 모든 성질은 "해시"라는 한 도구에서 나온다.
그런데 해시를 **함수로만** 아는 사람은 다음 랩에서 반드시 한 번 넘어진다.
같은 글을 저장했는데 해시가 매번 달라지거나, 다른 글인데 같은 해시가 나오길 기대하거나 한다.
30분만 손으로 만져 보면 그 감각이 생긴다. 이건 읽어서는 안 생긴다.

### 1. 먼저 깨져보기 ⚔

방어 없는 상태 = **직렬화 규칙 없이 해시를 계산하는 상태**다.

해볼 것 (`labs/hash_play.py`에서 자유롭게):

1. 같은 문자열을 100번 해시해 본다. 결과가 매번 같은지 확인한다.
2. 문자열 끝에 **공백 하나**만 추가하고 해시한다. 앞의 결과와 몇 글자나 비슷한가?
3. 아래 두 파이썬 딕셔너리를 각각 `json.dumps()` 한 뒤 해시한다.
   ```
   a = {"author": "sam", "body": "hello"}
   b = {"body": "hello", "author": "sam"}
   ```
   **논리적으로 완전히 같은 글**이다. 해시도 같은가?
4. 같은 딕셔너리를 `json.dumps(a)`와 `json.dumps(a, indent=2)`로 각각 해시한다.
5. 한글이 든 글을 `.encode("utf-8")`과 `.encode("utf-16")`으로 각각 해시한다.

네가 봐야 할 것:
```
1) 항상 동일  ← 결정성
2) 한 글자 차이인데 완전히 다른 해시  ← 눈사태 효과
3) 다른 해시  ← ★ 문제
4) 다른 해시  ← ★ 문제
5) 다른 해시  ← ★ 문제
```

3·4·5번이 이 랩의 핵심이다. **내용은 같은데 해시가 다르다.**
이게 블록체인에서 일어나면 어떻게 되는지 생각해 보라. 내 노드는 블록을 A 방식으로 직렬화해 해시하고,
네 노드는 B 방식으로 한다. 같은 블록인데 해시가 다르다. **두 노드는 영원히 합의하지 못한다.**

> **질문 (PROGRESS.md에 3줄로)**:
> 3번에서 왜 해시가 달라졌나? 해시 함수가 이상한 건가, 아니면 내가 넘긴 입력이 달랐던 건가?
> "같은 데이터"라는 말이 컴퓨터에게는 왜 충분하지 않은가?

### 2. 사전지식 체크

1. SHA-256의 출력은 항상 몇 비트인가? 입력 길이와 관계가 있나?
2. "충돌(collision)"과 "역상(preimage)"은 각각 무엇을 못 하게 만드는 성질인가?
3. `hashlib.sha256()`에 str을 그냥 넣으면 왜 `TypeError`가 나나? 이 에러가 사실은 무엇을 강제하고 있는 건가?

→ [기술리서치 #해시함수](../02-기술리서치.md#해시함수)

### 3. 과제

이 랩은 **구현보다 관찰이 목적**이다. 결과물은 코드가 아니라 메모다.

다음 표를 직접 채운다 (PROGRESS.md 또는 `labs/hash_play.py` 주석에):

| 실험 | 입력 A | 입력 B | 해시 같음? | 내 해석 |
|---|---|---|---|---|
| 결정성 | `"hello"` | `"hello"` | | |
| 눈사태 | `"hello"` | `"hello "` | | |
| 키 순서 | `{"a":1,"b":2}` | `{"b":2,"a":1}` | | |
| 들여쓰기 | `dumps(x)` | `dumps(x, indent=2)` | | |
| 인코딩 | UTF-8 | UTF-16 | | |
| 타입 | `{"n": 1}` | `{"n": "1"}` | | |
| float | `{"n": 1.0}` | `{"n": 1}` | | |

**만족해야 할 불변식** (다음 랩에서 코드로 강제할 것)
- 논리적으로 같은 데이터는 **항상** 같은 바이트열로 직렬화되어야 한다.
- 직렬화 결과는 파이썬 딕셔너리의 삽입 순서에 의존하면 안 된다.
- 인코딩은 하나로 고정되어야 한다.

### 4. 힌트

<details><summary>L1 — 방향</summary>

해시 함수는 잘못이 없다. 문제는 **같은 것을 같은 바이트로 만드는 규칙**이 없다는 것이다.
그 규칙에 이름을 붙이면 "정규 직렬화(canonical serialization)"다.
</details>

<details><summary>L2 — 구조</summary>

`json.dumps`에는 이 문제를 풀 수 있는 인자들이 있다. 무엇을 고정해야 하는지 목록으로 적어 보라:
- 키 순서
- 구분자(콤마·콜론 뒤 공백)
- 비ASCII 처리
- 들여쓰기
- 인코딩

각각을 고정하지 않으면 무슨 일이 생기는지 4번 표에서 이미 봤다.
</details>

<details><summary>L3 — 의사코드</summary>

```
canonical_bytes(obj):
    문자열로 직렬화한다. 이때
        - 키를 정렬한다
        - 구분자를 공백 없이 고정한다
        - 비ASCII를 이스케이프하지 않는다 (또는 항상 이스케이프한다 — 하나로 정한다)
        - 들여쓰기 없음
    그 문자열을 UTF-8로 인코딩해 bytes 를 반환한다
```
이 함수는 Lab 1.3에서 실제로 만든다. 여기서는 "무엇을 고정해야 하는가"를 아는 것까지가 목표다.
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| `TypeError: Strings must be encoded before hashing` | str을 그대로 넣음. 인코딩을 명시하라는 신호다 |
| 매 실행마다 해시가 다름 | 입력에 타임스탬프나 `id()`, `set` 순서 같은 비결정적 값이 섞임 |
| 딕셔너리 순서가 같아서 "문제 없네"로 결론 | 파이썬 3.7+는 **삽입 순서**를 유지할 뿐이다. 다른 순서로 만들면 다른 JSON이 나온다 |
| `1`과 `1.0`이 같을 거라 가정 | JSON에서 `1`과 `1.0`은 다른 문자열이다 |

### 6. 검증

이 랩에는 통과시킬 테스트가 없다. 대신:

**눈으로 확인**: 위 7행 표가 전부 채워져 있고, 각 행의 "내 해석"이 한 줄 이상 적혀 있다.
특히 **키 순서 행에서 "달라진다"는 것을 직접 본 화면**이 있어야 한다.

### 7. 실제 체인에서는

비트코인은 JSON을 쓰지 않는다. 블록 헤더는 **고정 길이 필드의 리틀엔디언 바이트열**이다 —
애초에 "직렬화 방식이 여러 개일 수 없게" 만든 설계다.
이더리움은 RLP라는 별도 인코딩을 쓰고, 서명 대상 구조화 데이터는 EIP-712로 정규화 규칙을 따로 못 박았다.
**세 프로젝트 모두 이 문제를 사양 수준에서 고정했다는 점이 핵심이다.**
→ [기술리서치 #직렬화](../02-기술리서치.md#직렬화)

### 8. 더 파보기

1. `hashlib.sha256` 대신 `blake2b`, `sha3_256`을 써 보고 속도를 비교한다. 비트코인이 SHA-256을 **두 번** 거는 이유를 찾아본다.
2. 길이 확장 공격(length extension attack)이 무엇인지 찾아보고, 그게 1번의 "두 번 거는" 이유와 관련 있는지 판단한다.
3. 해시 충돌을 실제로 찾으려면 얼마나 걸리는지 계산해 본다 (생일 문제).

### 9. 회고 3줄

---

## Lab 1.2 — 취약한 게시판과 변조

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 1~2시간 | Lab 1.1 | `labs/naive_board.py`, 변조 스크린샷 | ★★☆☆☆ |

### 0. 왜 이게 필요한가

"블록체인은 변조가 불가능하다"는 말을 백 번 들어도, **변조가 가능한 게시판을 직접 만들어서
직접 변조해 보기 전에는** 그 말이 무슨 뜻인지 모른다.
이 랩은 **일부러 취약한 것을 만드는 랩**이다. 여기서 만드는 코드는 Phase 2로 넘어가지 않는다. 버려질 코드다.
그래도 만든다. **깨뜨릴 대상이 있어야 깨뜨릴 수 있기 때문이다.**

### 1. 먼저 깨져보기 ⚔

**이 랩은 전체가 "먼저 깨져보기"다.**

해볼 것:

1. `labs/naive_board.py`에 아주 단순한 게시판을 만든다.
   - 글 = `{"id": 1, "author": "sam", "body": "첫 글", "ts": 1700000000}`
   - 저장 = 리스트를 통째로 `posts.json`에 `json.dump`
   - 기능 = `add(author, body)`, `list_all()` 두 개면 충분하다
2. 글을 10개 넣는다. 내용은 아무거나. `posts.json`이 생긴 걸 확인한다.
3. `list_all()`로 10개를 출력해 본다. 잘 나온다.
4. **에디터로 `posts.json`을 연다.** 3번 글의 `body`를 완전히 다른 내용으로 바꾼다.
   예: `"오늘 점심 뭐 먹지"` → `"sam이 회사 돈을 횡령했다"`
5. 저장하고, 다시 `list_all()`을 실행한다.

네가 봐야 할 것:
```
[1] sam: 첫 글
[2] sam: 두 번째 글
[3] sam: sam이 회사 돈을 횡령했다      ← 내가 방금 심은 글
[4] sam: 네 번째 글
...
```

**아무 일도 일어나지 않는다.** 경고 없음. 에러 없음. 로그 없음.
프로그램은 3번 글이 원래 그랬다고 믿고, 앞으로도 영원히 그렇게 믿는다.

6. 더 해 본다: 글 하나를 **통째로 지운다.** 다시 출력한다. 역시 아무 일도 없다.
7. 더 해 본다: 5번과 6번 글의 **순서를 바꾼다.** 역시 아무 일도 없다.
8. 더 해 본다: `author`를 남의 이름으로 바꾼다. 역시 아무 일도 없다.

> **질문 (PROGRESS.md에 3줄로)**:
> ① 왜 이게 가능했나? 프로그램이 "원래 내용"을 어디에 기록해 두지 않았기 때문인가,
>    아니면 기록해 뒀는데 확인을 안 한 건가?
> ② 이 게시판에 "관리자만 수정 가능" 같은 권한 체크를 붙이면 4번 공격을 막을 수 있나?
>    (막을 수 없다면 왜인가? 공격자는 어디를 통해 들어왔나?)
> ③ 그렇다면 무엇을 저장해 뒀어야 4번을 탐지할 수 있었을까?

②번 질문이 특히 중요하다. **여기서 일어난 일은 "인증 실패"가 아니라 "무결성 부재"다.**
로그인, 권한, HTTPS를 아무리 붙여도 **파일을 직접 만질 수 있는 사람**은 못 막는다.
그리고 Phase 7에서 서버를 운영하게 되면, 그 "파일을 직접 만질 수 있는 사람"은 바로 나 자신이다.

### 2. 사전지식 체크

1. 이 게시판에서 "데이터가 바뀌었다"를 판단하려면, 원본에 대한 **무엇**을 미리 갖고 있어야 하나?
2. 원본 전체를 복사해 두는 것과 원본의 해시를 저장해 두는 것 — 둘 다 변조를 탐지한다. 차이는?
3. 각 글의 해시를 따로따로 저장해 두면 4번 공격은 막힌다. 그런데 6번(글 삭제)과 7번(순서 바꾸기)은 막히나?

3번 질문의 답이 Lab 1.3의 존재 이유다.

### 3. 과제

`labs/naive_board.py` — **일부러 취약하게** 만든다. 요구사항은 단 두 개다.

```python
def add(author: str, body: str) -> dict:
    """글을 추가하고 저장한다. 무결성 보호는 하지 않는다."""
    ...

def list_all() -> list[dict]:
    """저장된 글을 순서대로 반환한다. 검증하지 않는다."""
    ...
```

**만족해야 할 불변식** (이 랩에서는 "지켜지지 않아야 할" 것들이다)
- 파일을 외부에서 수정해도 프로그램이 알아채지 못한다. ← **의도된 결함**
- 글을 지워도, 순서를 바꿔도 알아채지 못한다. ← **의도된 결함**

**하지 말 것**: 여기서 해시를 붙이고 싶은 충동이 들 것이다. 참아라.
방어는 Lab 1.3에서 한다. 지금 방어를 붙이면 "왜 필요한지"를 영영 못 느낀다.

### 4. 힌트

<details><summary>L1 — 방향</summary>

힌트가 필요 없는 랩이다. 30줄이면 된다. 예쁘게 만들려고 하지 마라. 버릴 코드다.
</details>

<details><summary>L2 — 구조</summary>

- 모듈 레벨 상수로 파일 경로 하나
- `_load()` / `_save(posts)` 내부 함수 두 개
- `add`는 `_load` → append → `_save`
- id는 `len(posts) + 1`이면 충분하다 (이것도 나중에 문제가 되는데, 그건 그때 겪는다)
</details>

<details><summary>L3 — 의사코드</summary>

```
_load():  파일이 없으면 빈 리스트, 있으면 json.load
_save(posts):  json.dump 로 통째로 덮어쓰기

add(author, body):
    posts = _load()
    새 글 dict 생성 (id, author, body, ts)
    posts 에 append
    _save(posts)
    새 글 반환

list_all():
    return _load()
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| 한글이 `\uXXXX`로 깨져 보임 | `json.dump(..., ensure_ascii=False)` 미사용. **Lab 1.1의 인코딩 실험과 같은 이야기다** |
| 글을 추가할 때마다 파일이 초기화됨 | `_load()` 없이 새 리스트에 append 후 저장 |
| 변조했는데 프로그램이 에러를 냄 | JSON 문법을 깨뜨린 것(쉼표·따옴표). 문법은 맞게 유지하면서 **값만** 바꿔야 진짜 공격이다 |
| 나도 모르게 해시를 붙였다 | 이 랩의 목적을 놓친 것. 지우고 다시 |

### 6. 검증

이 랩에는 통과시킬 테스트가 없다. **깨지는 것을 확인하는 랩**이다.

**눈으로 확인**:
- `posts.json`을 에디터로 연 스크린샷 (변조 전 / 후)
- 변조 후 `list_all()` 출력이 **아무 경고 없이** 조작된 내용을 보여주는 화면

이 두 장을 PROGRESS.md의 "보여줄 수 있는 한 장면"에 남긴다.
Lab 1.3이 끝나면 **똑같은 공격을 다시 해서** 이번엔 거부당하는 화면과 나란히 놓을 것이다.

### 7. 실제 체인에서는

이 랩에서 만든 게 바로 **일반적인 중앙화 서비스의 데이터 모델**이다.
DB를 가진 쪽이 과거를 바꿀 수 있고, 사용자는 그걸 확인할 방법이 없다.
"블록체인이 필요한가"라는 질문은 결국 **"데이터를 가진 쪽을 신뢰할 수 있는가"**라는 질문이다.
신뢰할 수 있으면 이 랩의 게시판으로 충분하다. 실제로 대부분의 서비스가 그렇다.
→ [기술리서치 #언제-블록체인이-필요한가](../02-기술리서치.md#언제-블록체인이-필요한가)

### 8. 더 파보기

1. 8번 실험(author 바꾸기)을 막으려면 무엇이 필요한가? 해시로 되나? (→ Phase 3의 서명이 필요하다)
2. 파일 대신 SQLite에 넣으면 4번 공격이 막히나? `sqlite3` CLI로 UPDATE를 날려 본다. (→ Phase 2의 ② 공격이다)
3. 파일 권한을 `chmod 400`으로 바꾸면 막히나? root라면?

### 9. 회고 3줄

---

## Lab 1.3 — 블록과 체인

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 3~5시간 | Lab 1.2 | `core/serialize.py`, `core/hashing.py`, `core/block.py`, `core/chain.py`, `core/validation.py`, ADR-0001 | ★★★★☆ |

### 0. 왜 이게 필요한가

Lab 1.2에서 글 내용이 조용히 바뀌는 걸 봤다.
글마다 해시를 붙이면 그 공격은 막힌다 — 하지만 **글을 통째로 지우거나 순서를 바꾸는 것**은 여전히 안 막힌다.
각 글이 자기 해시만 갖고 있으면, 공격자는 글과 해시를 **세트로** 지우면 그만이다.
필요한 건 "각 글이 올바른가"가 아니라 **"이 목록 전체가 내가 알던 그 목록인가"**다.

### 1. 먼저 깨져보기 ⚔

Lab 1.2의 게시판에 **글마다 해시만** 붙인 중간 버전을 만든다 (5분이면 된다).
`{"id":3, "body":"...", "hash": sha256(body)}` 정도면 충분하다.

해볼 것:
1. 3번 글의 `body`만 바꾼다 → 검증하면 **잡힌다.** (해시 불일치) 좋다.
2. 3번 글의 `body`를 바꾸고 **`hash` 필드도 새로 계산해서 같이 바꾼다** → **안 잡힌다.**
3. 5번 글을 **글과 해시를 세트로 통째로 삭제**한다 → **안 잡힌다.**
4. 5번과 6번 글의 **순서를 바꾼다** (해시는 그대로) → **안 잡힌다.**

네가 봐야 할 것: 1번만 잡히고 2·3·4번은 전부 통과한다.

> **질문**: 개별 해시가 막아 주는 것과 막지 못하는 것의 경계는 어디인가?
> 2번이 가능한 이유는 각 글의 해시가 **그 글 자신만으로** 계산되기 때문이다.
> 그렇다면 해시 입력에 **무엇을 더 넣어야** 3·4번까지 막히겠는가? 답을 보기 전에 30초만 생각하라.

### 2. 사전지식 체크

1. 블록 N의 해시 입력에 블록 N-1의 해시가 들어가면, 블록 3을 고쳤을 때 블록 4·5·6은 왜 같이 깨지나?
2. 제네시스 블록의 `prev_hash`에는 무엇을 넣나? 왜 그 값이어야 하나(또는 아무 값이어도 되나)?
3. `validate_chain()`이 `bool` 대신 파손 인덱스를 반환해야 하는 이유는? (→ Phase 2에서 쓰인다)

→ [기술리서치 #체인구조](../02-기술리서치.md#체인구조)

### 3. 과제

**이 랩이 Phase 1의 본체다.** 네 개를 만든다.

#### (1) 정규 직렬화 — `src/bbschain/core/serialize.py`

```python
def canonical_bytes(obj: Any) -> bytes:
    """해시 입력을 만드는 유일한 함수. 모든 해시는 이걸 통과한다."""
    ...
```

**불변식**
- 논리적으로 같은 객체는 **항상** 같은 bytes를 낸다 (키 삽입 순서 무관).
- 결과는 UTF-8 바이트열이다.
- 직렬화할 수 없는 타입(예: `set`, `datetime`)은 **조용히 넘어가지 않고 예외를 던진다.**
- 이 규칙은 **Phase 1에서 고정하고 끝까지 바꾸지 않는다** →
  [ADR-0001](../decisions/ADR-0001-canonical-serialization.md)을 이 랩에서 쓴다.

#### (2) 해시 — `src/bbschain/core/hashing.py`

```python
def sha256_hex(data: bytes) -> str: ...
def hash_object(obj: Any) -> str:
    """canonical_bytes 를 거쳐 해시한다. 직접 encode 하지 않는다."""
    ...
```

**불변식**: `hash_object`는 `canonical_bytes` 외의 경로로 바이트를 만들지 않는다.

#### (3) 블록 — `src/bbschain/core/block.py`

```python
@dataclass(frozen=True)
class Post:
    author: str
    body: str
    ts: int
    nonce: int = 0            # Phase 3 까지 항상 0. 그래도 지금 넣는다
    sig: str | None = None    # Phase 3 까지 항상 None. 그래도 지금 넣는다

@dataclass(frozen=True)
class Block:
    index: int
    prev_hash: str
    timestamp: int
    merkle_root: str      # Lab 1.4 까지는 자리만. 임시로 txs 전체 해시를 넣어도 된다
    nonce: int            # Phase 4 까지 항상 0. 그래도 지금 넣는다
    difficulty: int       # compact target(nBits). Phase 4 까지 항상 0. 그래도 지금 넣는다
    txs: tuple[Post, ...]

    @property
    def hash(self) -> str: ...
```

**불변식**
- `Block`은 **불변(frozen)**이다. 만든 뒤 필드를 바꿀 수 없다.
- **최종형에서 `hash`의 입력은 헤더 6개 필드**(`index`, `prev_hash`, `timestamp`, `merkle_root`, `nonce`, `difficulty`)**다.**
  `txs`는 **`merkle_root`를 통해 간접적으로** 커밋된다 (= 헤더 해시).
  **이 랩에서는 아직 머클이 없으므로 `txs`를 직접 넣는다 — 7개 필드 전부다.**
  그리고 **Lab 1.4에서 `txs`를 빼고 `merkle_root`만 남기는 것이 의도된 순서**다.
  지금 `txs`를 빼면 글을 아무리 고쳐도 안 잡히고(머클이 없으니 커밋하는 값이 없다), Lab 1.2의 공격이 그대로 통한다.
  → 왜 이 교체가 [ADR-0001](../decisions/ADR-0001-canonical-serialization.md)이 금지한 "직렬화 규칙 변경"이 **아닌지**는 [Lab 1.4 §3](#lab-14--머클-루트)에서 설명한다.
- 하나라도 빠지면 그 필드는 변조해도 안 잡힌다. **지금은 7개 전부 들어가야 한다.**
- `nonce`와 `difficulty`는 지금 쓰이지 않지만 **반드시 지금 넣는다.**
  Phase 4에서 추가하면 그때까지 쌓은 모든 블록의 해시가 바뀐다 = 기존 체인 전부 무효.
  **`difficulty`의 의미는 "선행 0비트 개수"가 아니라 compact target(nBits)이다** — Phase 4의 ASERT가 내놓는 값이
  연속적인 target이라 비트 수로는 담기지 않는다. ("선행 0이 몇 개" 는 설명용 어휘로만 쓴다.)
- **`Post`의 필드 집합도 같은 이유로 지금 고정한다.** `nonce`와 `sig`는 Phase 3까지 각각 `0`과 `None`이지만
  **지금 자리를 잡아 두지 않으면 Phase 3에서 모든 블록의 머클 루트와 해시가 바뀐다** (`validate()`가 `first_bad_index=1`을 반환한다).
  `Block.nonce`를 미리 넣는 것과 **정확히 같은 사고**다.
  **키 이름도 지금 고정한다** — `canonical_bytes`는 딕셔너리 키를 그대로 직렬화하므로 `author`를 `from`으로 바꾸기만 해도 해시가 전부 바뀐다.

#### (4) 체인과 검증 — `core/chain.py`, `core/validation.py`

```python
@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    first_bad_index: int | None
    reason: str | None

class Chain:
    def add_post(self, author: str, body: str) -> Block: ...
    def tip(self) -> Block: ...
    def validate(self) -> ValidationResult: ...
```

**불변식**
- 제네시스 블록은 `index == 0`이고 `prev_hash`가 고정된 상수다.
- 모든 i > 0에 대해 `chain[i].prev_hash == chain[i-1].hash`.
- 모든 i에 대해 `chain[i].index == i`.
- 모든 i에 대해 저장된 해시가 재계산한 해시와 같다.
- 하나라도 깨지면 `ok=False`, `first_bad_index=최초로 깨진 인덱스`, `reason=사람이 읽을 수 있는 이유`.
- **`first_bad_index`는 "최초"여야 한다.** 3번이 깨져 4·5·6이 연쇄로 깨져도 답은 3이다.
- `validate()`는 체인을 **변경하지 않는다** (순수 조회).

### 4. 힌트

<details><summary>L1 — 방향</summary>

- `canonical_bytes`: `json.dumps`의 인자들을 다시 봐라. Lab 1.1에서 고정해야 한다고 적었던 것들이 전부 인자로 있다.
- `Block.hash`: dataclass를 dict로 바꾸는 표준 함수가 있다. 그 결과를 `hash_object`에 넘기면 된다.
- `validate`: 앞에서부터 한 번 훑으면서 **처음 깨진 곳에서 즉시 반환**하면 "최초"가 저절로 보장된다.
</details>

<details><summary>L2 — 구조</summary>

- `serialize.py`는 함수 하나만 export 한다. 다른 모듈이 `json`을 직접 import 하면 규칙이 새는 것이다.
- `Block.hash`를 `@property`로 매번 계산할지, `@cached_property`로 캐시할지 결정해야 한다.
  **frozen dataclass에서 캐시는 까다롭다.** 그리고 지금은 블록이 몇 개 안 되니 매번 계산해도 된다.
  성능이 문제가 되는 건 Phase 4다. 그때 다시 온다.
- 검증은 세 종류로 나뉜다. 함수를 쪼개면 테스트가 쉬워진다:
  1. 블록 **하나**가 자체적으로 말이 되는가 (해시 일치, index 범위)
  2. 인접한 **두 블록**의 연결이 맞는가 (`prev_hash`, index+1, timestamp 단조 — **단조 규칙은 Phase 4에서 MTP 하한으로 교체될 임시 규칙이다**, §8 1번 참고)
  3. 체인 **전체**를 앞에서부터 훑는다
- `add_post`는 "새 블록을 만들어 tip 뒤에 붙인다". 블록 만드는 책임과 붙이는 책임을 나눌지 생각해 보라.
</details>

<details><summary>L3 — 의사코드</summary>

```
canonical_bytes(obj):
    s = json 직렬화(obj, 키정렬=on, 구분자=(",", ":"), ensure_ascii=고정값, indent=없음)
    return s.encode("utf-8")

hash_object(obj):
    return sha256_hex(canonical_bytes(obj))

Block.hash:
    payload = {index, prev_hash, timestamp, merkle_root, nonce, difficulty, txs}
              (txs 는 각 Post 를 dict 로 변환한 리스트)
              # Lab 1.4 에서 txs 를 payload 에서 빼고 merkle_root 만 남긴다 (= 헤더 해시).
              # 지금은 merkle_root 가 임시값이라 txs 를 직접 넣어야 변조가 잡힌다.
    return hash_object(payload)

validate_block_self(b):
    b.index 가 0 이상인가
        # ⚠ Lab 1.4 에서 "b.merkle_root == merkle_root(b.txs) 인가" 검사가 여기에 추가된다.
        # 거기서 txs 를 해시 입력에서 빼면 글을 커밋하는 고리가 merkle_root 하나뿐이라,
        # 이 재계산 대조가 없으면 본문 변조가 아무 데서도 안 잡힌다 (Lab 1.4 §3 3번).
    (Phase 4 이후) 해시가 난이도를 충족하는가

validate_link(prev, cur):
    cur.index == prev.index + 1 인가
    cur.prev_hash == prev.hash 인가
    cur.timestamp >= prev.timestamp 인가
        # ⚠ Phase 4 에서 MTP(중앙값) 하한으로 "교체"될 임시 규칙이다. 병행이 아니라 교체다.
        # MTP 규칙의 요점은 "개별 블록은 부모보다 과거일 수 있다" 이므로 단조 증가와 양립하지 않는다.
        # 이 줄을 남겨 두면 Phase 6 의 timewarp 공격이 재현되지 않는다 (§8 1번 참고).

Chain.validate():
    제네시스 검사: chain[0].index == 0, prev_hash == GENESIS_PREV
    for i in 1..len-1:
        self 검사 실패 → return (False, i, 이유)
        link(chain[i-1], chain[i]) 검사 실패 → return (False, i, 이유)
    return (True, None, None)

Chain.add_post(author, body):
    post = Post(author, body, 현재시각)
    새 Block 생성(index=height, prev_hash=tip().hash, timestamp=현재시각,
                  merkle_root=(Lab 1.4 전까지는 임시), nonce=0, difficulty=0,
                  txs=(post,))
    체인에 append
    return 새 블록
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| 같은 글을 넣었는데 실행할 때마다 체인 해시가 다름 | `timestamp`에 현재 시각이 들어감. **정상이다.** 재현 테스트에서는 시각을 주입해야 한다 |
| `TypeError: Object of type Post is not JSON serializable` | dataclass를 그대로 dumps에 넘김. dict로 변환해야 한다 |
| `tuple`이 직렬화 후 `list`가 되어 해시가 어긋남 | JSON에는 tuple이 없다. **한쪽으로 고정**하고 ADR에 적어라 |
| 블록 3을 고쳤는데 `first_bad_index`가 4로 나옴 | 검증 순서가 "링크 먼저, 자기검사 나중"이라 생긴 일. 무엇이 "최초"인지 정의를 다시 보라 |
| 블록 3을 고쳤는데 아무것도 안 잡힘 | 고친 필드가 `hash` 입력에 없음. **이 랩 시점에는 7개 필드 전부** 들어갔는지 확인 (Lab 1.4 이후에는 헤더 6개 + `merkle_root` 경유). **Lab 1.4 이후라면 원인이 다르다 → [Lab 1.4 §5](#lab-14--머클-루트)를 보라** |
| `merkle_root`를 아직 안 만들었다고 필드에서 뺌 | Phase 4의 `nonce`와 같은 사고. **지금 넣어라** |
| frozen dataclass인데 `__post_init__`에서 필드를 씀 | `object.__setattr__` 없이는 안 된다. 애초에 안 쓰는 설계가 낫다 |

### 6. 검증

```
uv run pytest tests/unit/test_serialize.py -v
uv run pytest tests/unit/test_block.py -v
uv run pytest tests/unit/test_chain_validation.py -v
```

통과해야 할 테스트 (에이전트가 미리 제공):
- `test_canonical_bytes_key_order_independent`
- `test_canonical_bytes_is_utf8`
- `test_canonical_bytes_rejects_unserializable`
- `test_block_hash_is_deterministic`
- `test_block_hash_changes_when_any_field_changes` (**Lab 1.3 시점: 7개 필드 각각.** Lab 1.4 이후에는 헤더 6개 필드 각각 + 글 변경이 `merkle_root`를 통해 전파되는지)
- `test_block_is_frozen`
- `test_valid_chain_passes`
- `test_tampered_body_reports_first_bad_index`
- `test_deleted_block_is_detected`
- `test_reordered_blocks_are_detected`
- `test_genesis_rules`

**눈으로 확인 — ④ 재공격**:
Lab 1.2에서 했던 것과 **똑같은 공격**을 다시 한다. 체인을 dump한 파일에서 3번 블록의 글자 하나를 바꾸고 검증하면:
```
INVALID: block #3 hash mismatch
         expected 4c81a2... (stored)
         actual   9f2ae7... (recomputed)
         reason: block hash does not match its contents
         blocks #4..#10 are unreachable from a valid ancestor
```
**Lab 1.2의 화면과 나란히 놓고 본다.** 같은 공격, 다른 결과. 이게 Phase 1의 전부다.

그리고 스스로 답하라: **왜 #3만이 아니라 #4 이후가 전부 무효인가?**
(#4의 `prev_hash`는 #3의 **원래** 해시를 가리키는데, #3의 해시가 바뀌었으니 더 이상 이어지지 않는다.
공격자가 #4를 고치면 #5가 깨지고, #5를 고치면... 결국 **끝까지 전부 다시 계산**해야 한다.
Phase 4에서 그 "다시 계산"에 비용이 붙으면 이게 방어가 된다.)

### 7. 실제 체인에서는

- 비트코인 블록 헤더는 정확히 80바이트이고 `prev_block_hash`가 그 안에 들어 있다. 우리 `Block`과 구조가 같다.
- 이더리움 블록 헤더에는 `parentHash` 외에 상태 트리 루트(`stateRoot`)가 더 있다 —
  "글 목록"이 아니라 "계정 상태 전체"를 해시로 요약한다는 차이다.
- **우리가 "체인이 깨졌다"고 부르는 상태를 실제 네트워크는 "그냥 유효하지 않은 블록"으로 취급하고 버린다.**
  깨진 체인을 보관하지 않는다. Phase 5에서 이 차이가 드러난다.
→ [기술리서치 #블록헤더](../02-기술리서치.md#블록헤더)

### 8. 더 파보기

1. `timestamp`가 뒤로 가는 블록(이전 블록보다 과거)을 허용해야 하나? 실제 체인은 어떻게 하나?
   (힌트: 비트코인의 median-time-past 규칙. Phase 4에서 다시 온다)
   **답을 미리 말해 두면: 허용한다.** 위 L3의 `cur.timestamp >= prev.timestamp`는 **Phase 4에서 MTP 하한으로 교체되어 사라진다.**
   MTP는 "직전 N블록 타임스탬프의 중앙값보다 크기만 하면 된다"이므로 **개별 블록은 부모보다 과거일 수 있다.**
   왜 그래야 하는지는 → [개발계획서 Phase 4](../01-개발계획서.md#phase-4--작업증명pow과-채굴-35일)의 "타임스탬프 검증 3종" 절.
   (단조 규칙을 남겨 두면 Phase 6의 timewarp 공격이 **토글 대상이 아닌 규칙에 막혀** 재현되지 않는다.)
2. 한 블록에 글을 **여러 개** 넣도록 바꿔 본다. `txs`가 이미 튜플인 이유가 여기 있다.
3. `first_bad_index`를 찾을 때 앞에서부터 훑는 대신 이분 탐색을 쓸 수 있나? 쓸 수 있다면 조건은?
4. 공격자가 블록 3부터 끝까지 전부 재계산하면 이 검증을 통과한다. **지금 그걸 막는 것이 있나?**
   (없다. 그게 Phase 4가 존재하는 이유다. 이 사실을 PROGRESS.md에 적어 둬라)

### 9. 회고 3줄

---

## Lab 1.4 — 머클 루트

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 3~4시간 | Lab 1.3 | `core/merkle.py` | ★★★★☆ |

### 0. 왜 이게 필요한가

Lab 1.3의 블록은 글을 몇 개 담을 수 있다. 그런데 `hash` 입력에 **글 전체**를 통째로 넣고 있다.
글이 1000개인 블록이면 해시를 한 번 계산할 때마다 1000개를 전부 직렬화한다.
Phase 4에서 채굴을 시작하면 이 계산을 **초당 수만 번** 하게 된다. 그때 이게 목을 조른다.

더 중요한 이유가 있다. 나중에 누군가 **"내 글 #742가 블록 #58에 들어 있다"는 것만 증명**받고 싶어 한다고 하자.
지금 구조로는 블록의 글 1000개를 전부 내려받아야 확인이 된다.
머클 트리는 **10개 해시만으로** 그걸 증명한다. 휴대폰이 비트코인을 검증할 수 있는 이유가 이것이다.

### 1. 먼저 깨져보기 ⚔

Lab 1.3의 `merkle_root` 자리에 임시로 "글 전체를 이어붙인 해시"를 넣었을 것이다.
그 임시 구현의 한계를 본다.

해볼 것:
1. 글 4개짜리 블록을 만든다. `merkle_root`를 기록한다.
2. **글 2번만** 바꾼다. 루트가 바뀌는가? (바뀐다. 여기까지는 문제없다)
3. 이제 질문: **"글 2번이 이 블록에 들어 있다"를 제3자에게 증명하려면 무엇을 줘야 하나?**
   지금 구현으로는 → 글 1·2·3·4를 **전부** 줘야 한다. 블록에 글이 10만 개면 10만 개를 다 줘야 한다.
4. 한 술 더: 글 목록을 `["A","B"]`와 `["AB"]`로 각각 만들어 임시 루트를 계산해 본다.
   이어붙이기 방식이라면 **두 결과가 같아질 수 있다.** 다른 블록인데 같은 루트다.

네가 봐야 할 것: 3번에서 "전부 줘야 한다"는 것, 4번에서 **구분자 없이 이어붙이면 충돌이 생긴다**는 것.

> **질문**: 4번의 충돌을 막으려면 무엇이 필요한가?
> 그리고 3번에서 "전부"가 아니라 일부만 주고도 증명이 되려면, 해시를 어떤 **모양**으로 쌓아야 하겠는가?

#### 그리고 한 번 더 깨진다 — 홀수 리프 ⚔⚔

트리 모양까지 떠올렸으면 곧바로 벽에 부딪힌다. **리프가 홀수 개면 마지막 하나가 짝이 없다.**
여기서 거의 모든 사람이 **"마지막 해시를 하나 더 복제해서 짝을 맞춘다"**를 고른다. 비트코인이 그렇게 한다.

**먼저 그 방식으로 구현해라.** 일부러다.

그다음 이 테스트를 돌린다 (테스트는 이미 주어져 있다):

```
uv run pytest tests/unit/test_merkle.py -k no_two_leaf_lists_share_a_root
```

네가 봐야 할 것 — **hypothesis가 반례를 찾아내고 최소 형태로 줄여서 보여준다**:

```
Falsifying example: test_no_two_leaf_lists_share_a_root(
    a=[b'\x00', b'\x01', b'\x02'],
    b=[b'\x00', b'\x01', b'\x02', b'\x02'],
)
  merkle_root(a) == merkle_root(b) == '9d1e...'
  ← 서로 다른 글 목록인데 루트가 같다
```

**글 3개짜리 블록과, 마지막 글을 한 번 더 복사해 붙인 글 4개짜리 블록의 머클 루트가 완전히 같다.**
루트가 같으면 블록 해시도 같다. **변조된 블록과 원본 블록이 구분되지 않는다.**

> **질문 (PROGRESS.md에 3줄로 답해라)**
> ① `[1,2,3]`과 `[1,2,3,3]`의 루트가 같아진 이유를 트리 그림으로 그려서 설명하라.
> ② 이걸 아는 공격자는 무엇을 할 수 있나? (힌트: 노드가 "이 블록 해시는 영구 무효"라고 마킹한다면?)
> ③ 이 성질을 없애려면 홀수 리프를 **복제하지 않고** 어떻게 처리하면 되겠는가?

이건 실제 취약점이고 이름이 있다 — **CVE-2012-2459**. Bitcoin Core는 이걸 못 고치고(호환성 때문에) 대신
`src/consensus/merkle.cpp` **L16~49에 "블록체인을 배우려고 이 코드를 읽고 있다면 주의하라"는 대문자 경고**를 박아 뒀다.
→ [기술리서치 #머클트리](../02-기술리서치.md#머클트리)

**이 실패 테스트가 Phase 1 전체에서 가장 교육적인 장면이다.** 여기서 멈추고 3번 질문에 답한 다음 과제로 넘어가라.

### 2. 사전지식 체크

1. 리프가 N개일 때 머클 트리의 높이는? 증명에 필요한 해시 개수는?
2. 리프 개수가 홀수면 어떻게 처리하나? **복제(duplicate)**와 **승격(promote)** 두 가지가 있는데, 각각 무엇을 잃고 무엇을 얻나?
3. CVE-2012-2459(중복 리프 취약점)는 무엇이고, **왜 비트코인은 그걸 알면서도 못 고쳤나?** 우리는 왜 고칠 수 있나?

→ [기술리서치 #머클트리](../02-기술리서치.md#머클트리)

### 3. 과제

`src/bbschain/core/merkle.py`

```python
def merkle_root(leaves: Sequence[bytes]) -> str:
    """리프 해시들로부터 머클 루트를 계산한다."""
    ...

def merkle_proof(leaves: Sequence[bytes], index: int) -> list[tuple[str, str]]:
    """index 리프가 루트에 포함됨을 증명하는 형제 해시 경로.
    각 원소는 (형제해시, 'L'|'R') — 형제가 왼쪽인지 오른쪽인지."""
    ...

def verify_proof(leaf: bytes, proof: list[tuple[str, str]], root: str) -> bool:
    """리프와 증명 경로만으로 루트를 재구성해 대조한다."""
    ...
```

**홀수 리프 처리 — 이건 네가 고르는 게 아니라 정해져 있다**

**홀수 노드는 복제하지 말고 그대로 위 레벨로 올려보낸다(promote).**
짝이 없는 마지막 해시는 **아무것도 하지 않고 다음 레벨에 그대로 내려놓는다.**

왜 이게 정답인가: 1절에서 본 CVE-2012-2459가 **성립 자체를 안 한다.**
복제하지 않으므로 "리프를 복제한 목록"이 같은 루트를 만들 방법이 없다.
비트코인이 복제 방식을 쓰는 건 **2009년에 그렇게 정해졌고 이제 와서 못 바꾸기 때문**이지, 그게 더 나아서가 아니다.
**우리 체인은 비트코인과 블록을 주고받지 않는다. 호환성 제약이 없으니 안전한 쪽을 고른다.**

(비트코인과 값을 맞춰야 하는 상황이라면 선택지가 하나 더 있다 — 복제하되 `mutated` 플래그를 **모든 레벨에서** 검사하는 방식.
우리는 그럴 이유가 없다. 두 방식의 비교는 → [기술리서치 #머클트리](../02-기술리서치.md#머클트리))

**불변식**
- **🔴 서로 다른 tx 리스트는 절대 같은 머클 루트를 갖지 않는다.**
  이게 이 랩의 핵심 불변식이고, 1절에서 깨뜨려 본 바로 그것이다. hypothesis가 길이 1~20을 흔들며 반례를 찾는다.
- 리프가 0개일 때의 동작을 **명시적으로 정한다** (예외인가, 고정된 빈 루트인가). 정하고 ADR-0001에 덧붙여라.
- 리프가 1개면 루트는 그 리프의 해시다 (또는 정의한 규칙대로 — 일관성이 전부다).
- 리프 하나라도 바뀌면 루트가 바뀐다.
- **리프의 순서가 바뀌면 루트가 바뀐다.** (순서도 커밋되는 정보다)
- `verify_proof(leaf, merkle_proof(leaves, i), merkle_root(leaves))`는 모든 `i`에 대해 True다.
- 잘못된 리프나 잘못된 경로로는 False가 나온다.
- 리프 해시와 내부 노드 해시를 **구분**한다 (2차 역상 공격 방어). 어떻게 구분할지는 네가 정하고 기록한다.
- **`merkle_proof` / `verify_proof`도 promote 규칙과 일관돼야 한다.** 홀수 레벨에서 승격된 노드는 **형제가 없으므로 경로에 아무것도 추가하지 않는다.**
  루트 계산만 고치고 증명 쪽을 안 고치면 `verify_proof`가 조용히 실패한다.

**그리고 이 랩에는 과제가 하나 더 있다 — 세 개를 같이 해야 끝난다.**

1. `Block.merkle_root`를 임시 구현(글 전체를 이어붙인 해시)에서 위 `merkle_root()` 함수로 교체한다.
2. 🔴 **`Block.hash`의 입력에서 `txs`를 제거한다.** 이제 `merkle_root`가 글 집합을 커밋하므로
   `txs`를 해시 입력에 **또** 넣을 이유가 없다. 해시 입력은 **헤더 6개 필드**
   (`index`, `prev_hash`, `timestamp`, `merkle_root`, `nonce`, `difficulty`)**만** 남는다. 이게 "헤더 해시"다.
3. 🔴 **`validate`가 `merkle_root`를 `txs`로부터 재계산해 대조한다.** 블록 자기검사(Lab 1.3 §4 L3의
   `validate_block_self`)에 한 줄이 늘어난다 — 블록에 적힌 `merkle_root`가 그 블록의 `txs`로 다시 계산한 값과 같은가.

**2번을 빼먹으면 이 랩의 0절이 말한 이유가 통째로 사라진다.** Phase 4의 채굴 루프는 nonce를 바꿀 때마다 해시를 다시 계산하는데,
`txs`가 입력에 남아 있으면 **nonce 하나 바꿀 때마다 글 1000개를 다시 직렬화**한다. 그게 목을 조른다고 0절에서 말한 그 상황이다.
그리고 **뒤늦게 Phase 4에서 빼면 그때까지 쌓인 모든 블록 해시가 바뀐다** —
[ADR-0001](../decisions/ADR-0001-canonical-serialization.md)이 "절대 하지 말라"고 못 박은 바로 그 상황이다.

**3번을 빼먹으면 이 랩의, 그리고 Phase 1 전체의 목적이 무너진다.** 2번을 하는 순간 `txs`는 더 이상 해시 입력이 아니다.
즉 **글 본문을 고쳐도 `merkle_root` 필드값은 그대로이므로 헤더 해시가 바뀌지 않는다.**
재계산 대조가 없으면 **본문 변조가 전혀 탐지되지 않는다** — Lab 1.2에서 직접 겪은 "파일을 고쳐도 앱이 눈치 못 챈다"로 그대로 되돌아간다.
**글 집합을 커밋하는 고리가 `merkle_root` 하나뿐이므로, 그 고리를 검증이 확인하지 않으면 끊긴 것과 같다.**

**교체하는 순간(1번·2번·3번 전부) 기존에 쌓아 둔 체인은 전부 무효가 된다.** 이게 정상이고, 왜 정상인지 설명할 수 있어야 한다.

> **이게 ADR-0001 위반이 아닌 이유**: ADR-0001이 금지한 것은 **체인을 이어서 쓰면서** 해시 입력 규칙을 바꾸는 것이다.
> 여기서는 **Phase 1 안이고, 쌓인 블록이 10개뿐이며, 체인을 버리고 제네시스부터 다시 만든다.**
> ADR-0001이 말한 "규칙 변경은 설정 바꾸기가 아니라 새 체인 시작하기다. Phase 1에서는 이 비용이 싸다. **그래서 지금 고정한다**"가
> 정확히 이 순간을 가리킨다. **Lab 1.4를 끝낸 시점의 `Block.hash` 정의가 최종형이고, 그 뒤로는 안 바꾼다.**
> (Phase 5에서 이 짓을 하면 네트워크가 갈라진다.)

### 4. 힌트

<details><summary>L1 — 방향</summary>

한 층씩 올라가면서 둘씩 짝지어 해시한다. 층의 노드가 1개가 되면 그게 루트다.
증명은 "올라가는 길에서 내가 쓰지 않은 반대쪽 형제"를 모으는 것이다.
</details>

<details><summary>L2 — 구조</summary>

- `merkle_root`: 현재 층(해시 리스트)을 while로 접어 올린다. **홀수면 마지막 하나는 건드리지 않고 다음 층에 그대로 넣는다(promote).**
- `merkle_proof`: 같은 루프를 돌되, 매 층에서 `index`가 짝수면 오른쪽 형제를, 홀수면 왼쪽 형제를 모으고
  `index //= 2`로 다음 층의 위치를 갱신한다. **형제가 없는 경우(= 승격된 노드)는 경로에 아무것도 추가하지 않고 넘어간다.**
- `verify_proof`: 리프 해시에서 시작해 경로를 순서대로 접으면서 올라간다. 좌우 순서를 틀리면 다른 루트가 나온다.
- 리프/내부 구분은 접두 바이트(예: `0x00` / `0x01`)를 붙이는 방식이 흔하다.
</details>

<details><summary>L3 — 의사코드</summary>

```
merkle_root(leaves):
    if leaves 비었으면  →  정한 규칙대로 (예외 또는 고정값)
    level = [leaf_hash(x) for x in leaves]
    while len(level) > 1:
        next = []
        for i in 0, 2, 4, ... :
            left = level[i]
            if level[i+1] 없으면:  next.append(left); break   # promote — 복제하지 않는다
            next.append(node_hash(left + level[i+1]))
        level = next
    return level[0]

merkle_proof(leaves, index):
    level = [leaf_hash(x) for x in leaves]
    path = []
    idx = index
    while len(level) > 1:
        sibling_idx = idx + 1 if idx 짝수 else idx - 1
        if sibling_idx 가 범위 밖이면:  # 승격된 노드 — 형제가 없다
            level = 한 층 접기; idx = idx // 2; continue
        path.append( (level[sibling_idx], 'R' if idx 짝수 else 'L') )
        level = 한 층 접기
        idx = idx // 2
    return path

verify_proof(leaf, proof, root):
    h = leaf_hash(leaf)
    for (sib, side) in proof:
        h = node_hash(sib + h) if side == 'L' else node_hash(h + sib)
    return h == root
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| 리프 순서를 바꿨는데 루트가 같음 | 접기 전에 정렬을 해버림. **순서도 커밋되는 정보다.** 정렬하지 마라 |
| `verify_proof`가 항상 False | 좌우 순서(`L`/`R`)를 반대로 접음. 경로에 방향을 안 담은 경우 흔하다 |
| 리프가 1개일 때 IndexError | while 조건과 홀수 처리의 경계. 리프 1개는 별도로 생각하라 |
| 홀수 리프에서 마지막을 복제했더니 서로 다른 목록이 같은 루트를 냄 | **CVE-2012-2459.** 복제하지 말고 promote 하라. 1절의 실패 테스트가 바로 이것이다 |
| **참고하려던 `jamesob/tinychain`을 그대로 옮겼더니 같은 반례가 나옴** | **tinychain의 `get_merkle_root()`(L917)에도 이 방어가 없다.** 주교재라고 머클만큼은 그대로 베끼면 안 된다 → [기술리서치 #머클트리](../02-기술리서치.md#머클트리) |
| 루트는 고쳤는데 `verify_proof`가 실패 | 증명 생성 쪽을 promote 규칙에 맞춰 안 고쳤다. **승격된 노드는 형제가 없어 경로에 넣을 것이 없다** |
| `str`과 `bytes`를 섞어서 접음 | 한쪽으로 고정하라. 함수 시그니처가 `bytes`를 받는 이유다 |
| 블록 해시가 바뀌어 기존 테스트가 전부 실패 | **정상이다.** `merkle_root` 정의를 바꿨으니 당연하다. 테스트 픽스처를 갱신하라 |
| **이 랩을 끝낸 뒤 글 본문을 고쳤는데 `validate()`가 통과함** (또는 `test_tampered_body_reports_first_bad_index`가 실패) | `txs`를 해시 입력에서 뺐는데 `validate`가 `merkle_root`를 재계산하지 않는다. **이제 글을 커밋하는 고리는 `merkle_root` 하나뿐이고, 그 고리를 확인하는 곳이 없다.** §3의 3번이다 |

### 6. 검증

```
uv run pytest tests/unit/test_merkle.py -v
uv run pytest tests/unit/test_block.py -v
uv run pytest tests/unit/test_chain_validation.py -v
```

통과해야 할 테스트:
- `test_merkle_root_is_deterministic`
- `test_merkle_root_changes_on_leaf_change`
- `test_merkle_root_changes_on_reorder`
- `test_merkle_root_single_leaf`
- `test_merkle_root_odd_leaves`
- **`test_no_two_leaf_lists_share_a_root`** (hypothesis property) — **1절에서 일부러 깨뜨린 그 테스트. promote로 고치면 초록이 된다**
- `test_merkle_root_does_not_duplicate_last_leaf` — `[a,b,c]`와 `[a,b,c,c]`의 루트가 **달라야** 한다
- `test_proof_roundtrip_all_indices` (hypothesis property)
- `test_proof_fails_for_wrong_leaf`
- `test_leaf_and_node_hashes_are_domain_separated`
- **`test_block_hash_input_excludes_txs`** — `txs`를 해시 입력에서 뺐는지. `merkle_root`가 같고 `txs`만 다른 두 블록은 **같은 해시**여야 한다
  (그런 블록은 머클 루트 정의상 만들 수 없으므로, 테스트는 직렬화 payload를 직접 들여다본다)
- **`test_tampering_a_post_still_changes_block_hash`** — `txs`를 뺐어도 글을 고치면 `merkle_root`가 바뀌고 따라서 블록 해시가 바뀐다.
  **이 두 테스트가 쌍이다.** 앞의 것만 통과시키면 Lab 1.2의 공격이 다시 통한다
- **`test_tampered_body_reports_first_bad_index`** (`tests/unit/test_chain_validation.py`, Lab 1.3부터 있던 테스트) —
  **§3의 3번(`validate`의 머클 재계산 대조)을 강제하는 테스트다.** 블록에 적힌 `merkle_root`는 그대로 두고 글 본문만 고치면
  헤더 해시가 바뀌지 않으므로, `validate`가 `txs`로부터 재계산해 대조하지 않는 한 이 테스트는 빨갛게 남는다

**눈으로 확인**: 글 4개짜리 블록에서 글 하나의 증명 경로를 출력해 본다. **해시 2개**만 있으면 된다.
글 1024개짜리로 늘려도 **10개**뿐이다. 글 수는 **256배**(4 → 1024)인데 증명은 **5배**(2 → 10)다.
이 숫자를 직접 보는 것이 이 랩의 목적이다.

### 7. 실제 체인에서는

- 비트코인 블록 헤더의 `merkleRoot`가 정확히 이것이다. SPV 지갑은 헤더(80바이트)와 머클 증명만으로
  "내 거래가 저 블록에 있다"를 검증한다 — **전체 블록을 받지 않는다.**
- 이더리움은 한 발 더 나가 트랜잭션·영수증·상태를 각각 머클 패트리샤 트라이로 요약한다.
- 우리는 Phase 7에서 **블록 하나를 32바이트로 요약해 Sepolia에 올린다.** 다만 올리는 값은 **머클 루트가 아니라 블록 해시**다 —
  머클 루트는 **그 블록의 글 집합만** 커밋해서, 과거를 고치고 뒤를 재채굴하는 공격을 탐지하지 못한다
  (→ [ADR-0003](../decisions/ADR-0003-anchor-target.md)).
  **그래도 Lab 1.4는 Phase 7의 준비물이 맞다.** 블록 해시의 입력에 `merkle_root`가 들어가기 때문이다 —
  머클 루트가 없으면 올릴 블록 해시도 없다.
→ [기술리서치 #머클트리](../02-기술리서치.md#머클트리)

### 8. 더 파보기

1. Phase 8의 SPV 라이트 클라이언트를 미리 맛본다 — 블록 본문 없이 헤더와 증명만으로 글 포함을 확인하는 스크립트.
2. 머클 트리 대신 리프를 전부 정렬해 해시하면 어떤 성질을 잃는가?
3. 리프가 2의 거듭제곱이 아닐 때의 처리 방식을 비트코인 / 이더리움 / certificate transparency가 각각 어떻게 하는지 비교한다.

### 9. 회고 3줄

---

## Lab 1.5 — 영속화와 검증 CLI

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 2~3시간 | Lab 1.4 | `storage/base.py`, `storage/jsonfile.py`, `cli.py` | ★★★☆☆ |

### 0. 왜 이게 필요한가

지금까지의 체인은 **프로세스가 죽으면 같이 사라진다.** 테스트 안에서만 사는 체인이다.
파일에 저장하는 순간 두 가지 새 문제가 생긴다:
① 저장했다 읽으면 정말 **같은 것**이 돌아오나? (Lab 1.1의 직렬화 문제가 여기서 다시 나온다)
② 저장 중에 프로그램이 죽으면 파일은 어떤 상태가 되나?

그리고 이 랩의 진짜 목적이 하나 더 있다. **Phase 2에서 저장소를 SQLite로 갈아끼울 때
코어 코드를 한 줄도 안 건드리게** 만드는 것이다. 그러려면 지금 인터페이스를 선언해 둬야 한다.

### 1. 먼저 깨져보기 ⚔

해볼 것:
1. `Chain`이 `json.dump`로 직접 파일을 쓰게 **대충** 만든다 (추상화 없이).
2. 글 10개를 넣고 저장 → 프로세스 종료 → 다시 로드 → `validate()`를 돌린다.
   **통과하는가?** 통과하지 않는다면 왜인가?
   (흔한 원인: `tuple`이 `list`로 돌아옴, `int` 타임스탬프가 `float`이 됨, 필드 순서)
3. 글 10000개를 넣고 저장하는 도중에 **Ctrl+C로 강제 종료**한다. 파일을 열어 본다.
4. 이 상태에서 다시 로드해 본다.

네가 봐야 할 것:
```
2) ValidationResult(ok=False, first_bad_index=1, reason='block hash mismatch')
   ← 저장하고 읽었을 뿐인데 체인이 깨졌다
3) posts.json 이 JSON 문법 중간에서 잘려 있음
4) json.decoder.JSONDecodeError: Expecting ',' delimiter: line 1 column 48213
   ← 체인 전체를 잃었다
```

> **질문**:
> ① 2번에서 아무것도 변조하지 않았는데 왜 해시가 달라졌나? **무엇이 왕복(round-trip)하지 않았나?**
> ② 3번에서 파일이 반쯤 쓰인 상태가 된 이유는? 이걸 막는 표준적인 방법의 이름은?
> ③ Phase 2에서 SQLite로 바꾸려면 지금 코드의 어디어디를 고쳐야 하나? 몇 군데인가?

③번이 이 랩이 존재하는 이유다. 대충 만들면 **코어 전체**를 고쳐야 한다.

### 2. 사전지식 체크

1. JSON에서 왕복하지 않는 파이썬 타입을 3개 이상 대라. (`tuple`, `bytes`, `datetime`, ...)
2. "원자적 쓰기(atomic write)"란 무엇이고 파일 시스템에서 어떻게 구현하나?
3. `Protocol`(구조적 서브타이핑)과 ABC(명목적 상속)의 차이는? 여기선 왜 Protocol이 나은가?

→ [기술리서치 #영속화](../02-기술리서치.md#영속화)

### 3. 과제

#### (1) 저장소 인터페이스 — `src/bbschain/storage/base.py`

```python
class Storage(Protocol):
    def append_block(self, block: Block) -> None: ...
    def get_block(self, key: str | int) -> Block | None: ...
    def tip(self) -> Block | None: ...
    def iter_blocks(self, start: int = 0, end: int | None = None) -> Iterator[Block]: ...
    def height(self) -> int: ...
```

**불변식**
- **인터페이스만 선언한다.** 구현은 `jsonfile.py`에 있고, Phase 2에서 `sqlite.py`가 추가된다.
- `Chain`은 `Storage` 타입에만 의존한다. `JsonFileStorage`를 직접 import 하면 실패다.
- `get_block`은 해시 문자열과 정수 인덱스를 **둘 다** 받는다 (탐색기가 둘 다 쓴다).
- `append_block`은 **append-only**다. 수정·삭제 메서드는 **만들지 않는다.**
  (`/admin/tamper`는 Phase 2에서 이 인터페이스를 우회해 파일을 직접 건드리는 식으로 만든다.
   "정상 경로로는 불가능하다"는 것 자체가 설계다.)

#### (2) JSON 파일 구현 — `src/bbschain/storage/jsonfile.py`

**불변식**
- `append_block` → 프로세스 재시작 → `iter_blocks`가 **완전히 동일한 블록**을 돌려준다
  (모든 필드의 타입까지 동일. `tuple`이 `list`로 돌아오면 실패다).
- 쓰기 도중 죽어도 파일이 **읽을 수 없는 상태가 되지 않는다** (원자적 쓰기).
- 파일이 없으면 제네시스부터 시작한다.

#### (3) CLI — `src/bbschain/cli.py`

```
bbschain post   --author <name> --body <text>    # 글 작성 → 새 블록
bbschain dump   [--from N] [--to M]              # 체인 출력
bbschain verify                                  # 검증 결과 + 파손 지점
bbschain tamper --index N --field body --value X # 실습용 변조 (환경변수 게이트 + 경고 필수)
```

**불변식**
- `verify`는 정상이면 종료 코드 **0**, 파손이면 **1**을 반환한다 (스크립트에서 쓸 수 있어야 한다).
- `tamper`는 **실행 시 경고를 출력**한다. **그리고 경고만으로는 부족하다.**
  Phase 7에서 이게 배포판에 들어가면 사고다 — `/admin/tamper`는 환경변수로 꺼지는데 CLI는 그냥 도는 상황이 된다.
  **`/admin/tamper`와 같은 환경변수 게이트를 붙이고, 변수가 없으면 아무것도 하지 않고 거부한다**(종료 코드 2).
  [Phase 7 DoD](../01-개발계획서.md#phase-7--배포--공개-테스트넷-앵커링-47일)에 이 항목이 있다.
- `tamper`는 `Storage` 인터페이스를 쓰지 않는다 (쓸 수가 없다 — append만 있으니까). 파일을 직접 건드린다.

### 4. 힌트

<details><summary>L1 — 방향</summary>

- 왕복 문제: 블록을 dict로 바꾸는 함수와 dict에서 블록을 복원하는 함수를 **쌍으로** 만들고,
  "아무 블록이나 넣어도 `from_dict(to_dict(b)) == b`"를 property 테스트로 강제하라.
- 원자적 쓰기: 같은 디렉터리에 임시 파일로 쓴 다음 이름을 바꾼다. 이름 바꾸기는 원자적이다.
</details>

<details><summary>L2 — 구조</summary>

- `Block.to_dict()` / `Block.from_dict()`를 `block.py`에 둘지 `jsonfile.py`에 둘지 결정하라.
  **힌트: Phase 2의 SQLite도, Phase 5의 네트워크 전송도 같은 변환이 필요하다.** 어디 두는 게 맞겠나?
- 매번 파일 전체를 다시 쓰는 것과 줄 단위로 append 하는 것(JSON Lines) 중 하나를 고른다.
  체인은 append-only인데 왜 전체를 다시 쓰겠나?
- CLI는 표준 `argparse`로 충분하다. Typer를 쓰고 싶으면 써도 되지만 의존성 하나가 는다.
</details>

<details><summary>L3 — 의사코드</summary>

```
atomic_write(path, data):
    tmp = path 와 같은 디렉터리에 임시 파일
    tmp 에 쓰고 flush + fsync
    os.replace(tmp, path)        # 원자적 교체

JsonFileStorage:
    append_block(b):
        blocks = 로드
        blocks.append(b.to_dict())
        atomic_write(path, 직렬화(blocks))
        # 또는 JSON Lines 라면: 파일 끝에 한 줄 append (원자성 고려)

    iter_blocks(start, end):
        로드한 dict 들을 from_dict 로 복원해 하나씩 yield

cli.verify:
    chain = Chain(storage)
    r = chain.validate()
    if r.ok:  "VALID: height=N tip=hash" 출력; exit 0
    else:     "INVALID: block #{r.first_bad_index} {r.reason}" 출력
              "blocks #{i+1}..#{N} invalidated" 출력; exit 1
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| 재시작 후 `first_bad_index=1` | `tuple` → `list` 왕복 실패. `from_dict`에서 tuple로 되돌려야 한다 |
| 타임스탬프가 `1700000000.0`이 됨 | JSON은 int/float 구분을 보존하지만 코드 어딘가에서 float으로 만든 것. `int`로 고정 |
| 한글이 `사`로 저장됨 | `ensure_ascii` 설정. **`canonical_bytes`와 저장 포맷은 별개 결정이다.** 헷갈리지 마라 |
| 대용량에서 느림 | 매번 전체를 다시 씀. Phase 2에서 SQLite가 푸는 문제. 지금은 넘어가도 된다 |
| `Chain`이 `JsonFileStorage`를 직접 import | 추상화 실패. Phase 2에서 그대로 비용을 치른다 |
| `tamper`가 storage 인터페이스로 구현됨 | 인터페이스에 수정 메서드를 추가한 것. **되돌려라.** append-only가 설계의 핵심이다 |
| `tamper`가 경고만 찍고 그냥 실행됨 | 환경변수 게이트가 없다. **이대로 Phase 7에 가면 배포된 노드에서 아무나 체인을 깨뜨린다** |

### 6. 검증

```
uv run pytest tests/unit/test_storage_jsonfile.py -v
uv run pytest tests/integration/test_restart_roundtrip.py -v
uv run pytest tests/unit/test_cli.py -v
```

통과해야 할 테스트:
- `test_block_dict_roundtrip` (hypothesis property — 임의 블록)
- `test_append_and_read_back`
- `test_restart_preserves_chain`
- `test_atomic_write_survives_interruption`
- `test_get_block_by_hash_and_index`
- `test_storage_has_no_mutation_method` (인터페이스에 update/delete가 없음을 강제)
- `test_verify_exit_code_zero_on_valid`
- `test_verify_exit_code_one_on_tampered`
- `test_tamper_refuses_without_env_gate` (환경변수 없이 실행하면 체인이 그대로이고 종료 코드가 0이 아님)

**눈으로 확인 — Phase 1의 결승선**:
```
$ bbschain post --author sam --body "첫 글"
block #1 mined  hash=a3f1...  merkle=7c2e...

... (10개 반복) ...

$ bbschain verify
VALID   height=10   tip=8e41c2...

$ vim chain.json          # ← 3번 블록의 body 에서 글자 하나 수정

$ bbschain verify
INVALID: block #3 hash mismatch
         reason: block hash does not match its contents
         blocks #4..#10 invalidated (chain broken from #3)
$ echo $?
1
```

**이 화면을 Lab 1.2의 스크린샷 옆에 놓는다.** 같은 공격, 다른 결과.
[PROGRESS.md](../PROGRESS.md)의 Phase 1 "보여줄 수 있는 한 장면"에 이 두 장을 남긴다.

### 7. 실제 체인에서는

- 비트코인 코어는 블록을 `blk*.dat` 파일에 순차 append 하고, 조회용 인덱스는 LevelDB에 따로 둔다.
  **"저장"과 "인덱싱"을 분리한 구조** — 우리가 Phase 2에서 SQLite로 하려는 것과 같은 발상이다.
- 어느 노드 소프트웨어도 "블록을 수정하는 API"를 갖고 있지 않다. 우리 `Storage`에 수정 메서드가 없는 것과 같다.
- 재시작 시 체인 무결성을 다시 검증하는지 여부는 구현마다 다르다 (전체 재검증은 비싸다).
  우리는 블록이 몇 개 안 되니 매번 검증한다. Phase 7에서 이 결정이 다시 온다.
→ [기술리서치 #노드-저장구조](../02-기술리서치.md#노드-저장구조)

### 8. 더 파보기

1. `chain.json` 대신 JSON Lines(`chain.jsonl`)로 바꿔 본다. append가 진짜 append가 되는가? 원자성은?
2. 체인 파일을 읽기 전용(`chmod 444`)으로 만들면 `tamper`가 막히나? root면? 이게 Phase 7의 ② 공격이다.
3. `validate()`를 매 조회마다 돌리면 블록 1만 개에서 얼마나 걸리나? 측정해 보고 Phase 2의 배지 설계에 반영한다.

### 9. 회고 3줄

---

## SQ 1.6 — Sepolia 맛보기 (사이드 퀘스트)

| 소요 | 선행 | 산출물 | 난이도 |
|---|---|---|---|
| 0.5일 | Lab 1.5 | Etherscan 링크 1개, 비교 메모 | ★★☆☆☆ |

> **사이드 퀘스트다.** Phase 1 DoD에 들어가지 않는다. 건너뛰어도 Phase 2로 갈 수 있다.
> 하지만 **하는 걸 강력히 권한다.** 여기서 얻는 건 기술이 아니라 **기준선**이다.

### 0. 왜 이게 필요한가

지금 네 손에는 **네가 만든 체인**이 있다. 글을 쓰면 즉시 블록이 생기고, 파일을 지우면 없어진다.
이게 블록체인인가? 맞기도 하고 아니기도 하다. 비교 대상이 없으면 그 차이를 영영 모른다.
Phase 7에서 앵커링을 붙일 때 "실제 체인이 뭔지" 처음 배우면 늦다. 지금 30분 투자해서 기준선을 만든다.

### 1. 먼저 깨져보기 ⚔

이 퀘스트의 "깨짐"은 **네 체인의 한계를 보는 것**이다.

해볼 것:
1. Lab 1.5에서 만든 `chain.json`을 **삭제한다.**
2. `bbschain verify`를 돌린다.

네가 봐야 할 것: 체인이 사라졌다. 아무도 모른다. 아무도 복구해 주지 않았다.
**네 체인의 모든 역사는 네 노트북의 파일 하나에 있었다.**

> **질문**: 네 체인은 변조에 강한가? Lab 1.3에서 변조는 탐지됐다. 그런데 **삭제**는?
> 탐지할 사람이 너 하나뿐이면, 변조 탐지는 무슨 의미가 있나?
> (이 질문의 답이 Phase 5가 존재하는 이유이자, 이 사이드 퀘스트의 요점이다)

### 2. 사전지식 체크

1. 테스트넷의 ETH는 왜 공짜인가? 그게 메인넷과 무엇이 다른가?
2. 이더리움 트랜잭션의 `data` 필드에는 아무 바이트나 넣을 수 있나? 비용은 어떻게 매겨지나?
3. "확정(finality)"이 되려면 몇 블록을 기다려야 하나? Sepolia와 메인넷이 다른가?

→ [기술리서치 #테스트넷](../02-기술리서치.md#테스트넷)

### 3. 과제

**목표: 내 게시판 글 하나의 해시를 Sepolia에 트랜잭션 1건으로 올리고 Etherscan에서 본다.**

순서:
1. 지갑 하나 생성 (MetaMask 또는 `eth_account`로 직접). **이 키는 테스트 전용이다. 메인넷에서 절대 쓰지 마라.**
2. RPC 엔드포인트 확보 (Alchemy / Infura 무료 티어). URL은 `.env`에 넣는다 — **`.gitignore`에 있는지 확인.**
3. faucet에서 Sepolia ETH 받기.
4. `labs/sepolia_hello.py` — web3.py로 트랜잭션 1건 전송:
   - `to`: 자기 자신 주소
   - `value`: 0
   - `data`: **Lab 1.5에서 만든 블록 #1의 해시** (bytes로)
5. tx 해시를 받아 Etherscan(sepolia.etherscan.io)에서 조회.
6. **Input Data 탭**을 눌러 내 해시가 그대로 들어 있는지 확인.

**만족해야 할 불변식**
- 개인키와 RPC URL은 **절대 커밋되지 않는다.** 커밋 전에 `git status`로 확인한다.
- `labs/sepolia_hello.py`는 `src/bbschain/`에 들어가지 않는다. 본선 코드가 아니다.

**그리고 이 표를 직접 채운다.** 이게 이 퀘스트의 진짜 산출물이다.

| 항목 | 내 체인 | Sepolia |
|---|---|---|
| 블록 생성 간격 | | |
| 블록 하나를 만드는 비용 | | |
| 내 글이 저장된 컴퓨터 수 | | |
| 내가 파일을 지우면 | | |
| 변조를 탐지할 수 있는 사람 | | |
| 글을 쓰는 데 드는 돈 | | |
| 확정까지 기다려야 하는 시간 | | |
| 누가 규칙을 바꿀 수 있나 | | |

### 4. 힌트

<details><summary>L1 — 방향</summary>

web3.py의 "트랜잭션 서명해서 보내기" 예제 하나면 된다. 컨트랙트는 필요 없다.
`data` 필드에 임의 바이트를 넣는 트랜잭션은 가장 단순한 형태의 "온체인 기록"이다.
</details>

<details><summary>L2 — 구조</summary>

- `Web3(HTTPProvider(RPC_URL))`로 연결
- `nonce = w3.eth.get_transaction_count(내주소)` ← **이 nonce가 Phase 3에서 우리가 만들 nonce와 같은 개념이다**
- 트랜잭션 dict 구성: `to`, `value`, `gas`, `maxFeePerGas`, `maxPriorityFeePerGas`, `nonce`, `chainId`, `data`
- `w3.eth.account.sign_transaction(tx, 개인키)` → `w3.eth.send_raw_transaction(...)`
- `w3.eth.wait_for_transaction_receipt(tx_hash)`로 확정 대기
</details>

<details><summary>L3 — 의사코드</summary>

```
1. .env 에서 RPC_URL, PRIVATE_KEY 읽기
2. w3 연결, 체인 ID 확인 (Sepolia 인지)
3. 잔액 확인 — 0 이면 faucet 먼저
4. block1_hash = 내 체인에서 블록 1의 해시 (hex str)
5. tx = {to: 내주소, value: 0, data: bytes.fromhex(block1_hash),
         nonce: ..., gas: 추정치, chainId: 11155111, 수수료 필드들}
6. signed = 서명
7. tx_hash = send_raw_transaction
8. receipt = wait_for_transaction_receipt   ← 여기서 몇 초 기다린다. 그 시간을 재라
9. print(f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
```
</details>

### 5. 흔한 실수

| 증상 | 원인 |
|---|---|
| `insufficient funds for gas` | faucet ETH가 아직 안 들어옴. 잔액을 먼저 확인 |
| faucet이 거부함 | 메인넷 잔액 요구, 계정 연동 요구 등 정책이 자주 바뀐다. 다른 faucet을 찾는다 |
| `nonce too low` | 이전 tx가 아직 pending. **Phase 3에서 우리가 만들 nonce 리플레이 방지와 같은 메커니즘이다** |
| 개인키를 코드에 하드코딩 | 커밋되면 끝. `.env` + `.gitignore`. 이미 커밋했다면 그 키는 버려라 |
| Etherscan에서 Input Data가 안 보임 | "Click to see More" → Input Data 탭. 기본 화면에는 접혀 있다 |
| 메인넷 키를 재사용 | **절대 금지.** 테스트용 키는 따로 만든다 |

### 6. 검증

이 퀘스트에는 pytest가 없다.

**눈으로 확인**:
- `https://sepolia.etherscan.io/tx/0x...` 링크를 열었을 때 **Input Data에 내 블록 해시가 보인다.**
- 비교 표 8행이 전부 채워져 있다.

가장 중요한 것: **그 페이지는 내 컴퓨터가 아니라 전 세계 어디서나 보인다.**
내 노트북을 포맷해도 저 기록은 남는다. Lab 1.5에서 `chain.json`을 지웠을 때와 정반대다.
→ 이 문장이 Phase 7 앵커링의 동기 전부다.

### 7. 실제 체인에서는

이게 실제 체인이다. 우리가 만들 것과 다른 점:
- 블록을 만드는 데 **전 세계의 검증자가 경쟁**한다 (우리는 나 혼자)
- 규칙을 바꾸려면 **모두가 동의**해야 한다 (우리는 내가 코드를 고치면 끝)
- 기록은 **수천 대에 복제**되어 있다 (우리는 파일 하나)

Phase 5가 끝나면 두 번째·세 번째 차이가 줄어든다. 첫 번째는 끝까지 안 줄어든다 —
그래서 Phase 7에서 **앵커링**으로 "실제 체인의 힘을 빌린다."
→ [기술리서치 #앵커링](../02-기술리서치.md#앵커링)

### 8. 더 파보기

1. 같은 해시를 두 번 올려 본다. 두 tx는 다른가? 왜 다른가? (nonce)
2. `data`에 1KB를 넣어 보고 가스비를 비교한다. **"본문 전체를 온체인에 올리면 얼마인가"**를 계산해 본다.
   → 이 계산이 [ADR-0002](../decisions/ADR-0002-on-chain-post-body.md)와 Phase 8의 IPFS 트랙의 배경이다.
3. Etherscan에서 아무 블록이나 열어 머클 루트(트랜잭션 루트)를 찾아본다. Lab 1.4에서 만든 것과 같은 물건이다.

### 9. 회고 3줄

---

## Phase 1 마무리

랩 5개 + 사이드 퀘스트를 끝냈으면 [PROGRESS.md](../PROGRESS.md)에서 Phase 1의 랩과 DoD를 켠다.

**"보여줄 수 있는 한 장면"에 반드시 남길 것**: Lab 1.2의 변조 성공 화면과 Lab 1.5의 변조 탐지 화면, **두 장 나란히.**

**Phase 2로 넘어가기 전 자가 점검 — 다음 질문에 막힘없이 답할 수 있나?**

1. 블록 3을 고치면 왜 4·5·6이 전부 무효가 되나?
2. 공격자가 3번부터 끝까지 전부 재계산하면 지금 내 검증을 통과하는가? 그걸 막는 게 있나?
3. `canonical_bytes`를 지금 바꾸면 무슨 일이 일어나나? 왜 그런가?
4. `Block`에 `nonce`·`difficulty`를, `Post`에 `nonce`·`sig`를 쓰지도 않으면서 지금 넣은 이유는?
   (`Post` 쪽을 안 넣었으면 Phase 3에서 무슨 일이 일어나나?)
5. `validate()`가 bool 대신 `first_bad_index`를 반환하는 이유는?
6. 머클 루트가 있으면 글 1024개짜리 블록에서 글 하나의 포함 증명에 해시가 몇 개 필요한가?
   그리고 `Block.hash`의 입력에서 `txs`를 뺐는데도 글 변조가 잡히는 이유는?
7. 내 체인이 진짜로 안전하지 않은 이유를 **두 가지** 대라. (힌트: 하나는 Phase 4가, 하나는 Phase 5가 푼다)

2번과 7번에 답이 막힌다면 Lab 1.3 §8의 4번 항목을 다시 읽어라.

다음 → Phase 2 (랩 문서는 Phase 2에 진입할 때 작성한다. [개발계획서 Phase 2](../01-개발계획서.md#phase-2--블록-탐색기-v1--저장소-교체-35일) 참고)
