"""Lab 1.3 — 체인 검증 (`core/chain.py`, `core/validation.py`)

계약 (개발계획서 6절 고정 계약 3번)
    ValidationResult{ok, first_bad_index, reason}   ← bool 이 아니다
    · 제네시스: index == 0, prev_hash == 고정 상수
    · 모든 i > 0: chain[i].prev_hash == chain[i-1].hash
    · 모든 i:     chain[i].index == i
    · **first_bad_index 는 "최초"** — 3번이 깨져 4·5·6 이 연쇄로 깨져도 답은 3이다.
    · validate() 는 체인을 **변경하지 않는다** (순수 조회)

여기서 쓰는 `first_bad_index` 는 **리스트 위치**다 (chain[i].index == i 가 불변식이므로
정상 체인에서는 둘이 같다).

테스트는 `validate_chain(blocks)` 또는 `Chain(blocks).validate()` 중 있는 쪽을 호출한다.
"""

from __future__ import annotations

import copy
import dataclasses

from conftest import (
    describe,
    make_chain_blocks,
    posts_merkle_root,
    relink,
    st_chain,
    validate_blocks,
)
from hypothesis import given
from hypothesis import strategies as st


def _tamper_body(block, new_body: str = "sam이 회사 돈을 횡령했다"):
    """블록 안의 첫 글 본문만 바꾼다 — Lab 1.2 에서 에디터로 했던 바로 그 공격."""
    tampered_posts = (dataclasses.replace(block.txs[0], body=new_body), *block.txs[1:])
    return dataclasses.replace(block, txs=tampered_posts)


def test_valid_chain_passes():
    """고정 시각으로 만든 정상 체인은 통과한다."""
    blocks = make_chain_blocks(5)
    result = validate_blocks(blocks)

    assert result.ok, (
        f"변조하지 않은 체인이 파손 판정을 받았다. {describe(result)}\n"
        "→ 흔한 원인: 제네시스 prev_hash 상수 불일치 / merkle_root 재계산 규칙 불일치 / "
        "timestamp 단조 규칙."
    )
    assert result.first_bad_index is None, (
        f"ok=True 인데 first_bad_index 가 채워져 있다. {describe(result)}"
    )
    assert result.reason is None, f"ok=True 인데 reason 이 채워져 있다. {describe(result)}"


@given(st_chain())
def test_valid_chain_passes_property(blocks):
    """임의의 글·길이로 만든 정상 체인도 통과한다."""
    result = validate_blocks(blocks)
    assert result.ok, f"정상 체인(길이 {len(blocks)})이 거부됐다. {describe(result)}"


def test_validate_does_not_mutate_the_chain():
    """`validate()` 는 순수 조회다 (Lab 1.3 §3(4))."""
    blocks = make_chain_blocks(4)
    snapshot = copy.deepcopy(blocks)
    hashes_before = [b.hash for b in blocks]

    validate_blocks(blocks)

    assert blocks == snapshot, "validate() 가 체인을 변경했다. 검증은 아무것도 고치면 안 된다."
    assert [b.hash for b in blocks] == hashes_before, "validate() 후 블록 해시가 달라졌다."


def test_tampered_body_reports_first_bad_index():
    """④ 재공격 — 3번 블록의 글 본문을 바꾸면 **#3** 을 지목한다.

    Lab 1.2 에서는 아무 일도 없었다. 같은 공격, 다른 결과.

    ※ Lab 1.4 에서 `Block.hash` 입력에서 `txs` 를 뺐다면, 이 공격을 계속 잡으려면
      `validate()` 가 **`merkle_root` 를 txs 로부터 재계산해 대조**해야 한다.
      (글은 이제 merkle_root 를 통해서만 커밋되기 때문이다.)
    """
    blocks = make_chain_blocks(6)
    attacked = list(blocks)
    attacked[3] = _tamper_body(attacked[3])

    result = validate_blocks(attacked)

    assert not result.ok, (
        f"3번 블록의 글 본문을 통째로 바꿨는데 유효하다고 답했다. {describe(result)}\n"
        "→ Lab 1.2 의 게시판과 똑같은 상태다. 글이 블록 해시에 커밋되고 있는지 확인하라."
    )
    assert result.first_bad_index == 3, (
        f"최초 파손 인덱스가 3 이 아니다. {describe(result)}\n"
        "→ 4 가 나왔다면 '블록 3 자체의 자기검사'가 없고 '블록 4 의 링크'에서만 걸린 것이다.\n"
        "  (Lab 1.3 §5 표의 그 항목이다. 자기검사를 링크 검사보다 먼저 하라.)"
    )
    assert result.reason, "ok=False 인데 reason 이 비었다. 사람이 읽을 수 있는 이유가 있어야 한다."


@given(st.integers(min_value=1, max_value=5))
def test_tampered_body_reports_first_bad_index_property(index):
    """어느 블록을 고쳐도 최초 파손 인덱스는 그 블록이다."""
    blocks = make_chain_blocks(6)
    attacked = list(blocks)
    attacked[index] = _tamper_body(attacked[index], new_body=f"변조 {index}")

    result = validate_blocks(attacked)
    assert not result.ok, f"블록 {index} 변조가 탐지되지 않았다. {describe(result)}"
    assert result.first_bad_index == index, (
        f"블록 {index} 을 고쳤는데 first_bad_index={result.first_bad_index} 다. {describe(result)}"
    )


def test_first_bad_index_is_the_earliest_break():
    """두 군데를 고쳐도 답은 **앞의 것**이다."""
    blocks = make_chain_blocks(7)
    attacked = list(blocks)
    attacked[2] = _tamper_body(attacked[2], new_body="먼저 깨뜨린 곳")
    attacked[5] = _tamper_body(attacked[5], new_body="나중에 깨뜨린 곳")

    result = validate_blocks(attacked)
    assert not result.ok, f"두 군데를 변조했는데 유효하다고 답했다. {describe(result)}"
    assert result.first_bad_index == 2, (
        f"2 와 5 를 고쳤으면 답은 2 다. {describe(result)}\n"
        "→ 앞에서부터 훑으며 **처음 깨진 곳에서 즉시 반환**하면 저절로 보장된다."
    )


def test_tampered_body_with_recomputed_merkle_root_breaks_the_next_link():
    """공격자가 머클 루트까지 다시 계산하면? 그 블록은 자기모순이 없어지지만
    **다음 블록의 `prev_hash` 가 어긋난다.** 파손 지점은 i+1 로 옮겨간다.
    """
    blocks = make_chain_blocks(5)
    attacked = list(blocks)
    tampered = _tamper_body(attacked[2], new_body="머클까지 고친 변조")
    attacked[2] = dataclasses.replace(tampered, merkle_root=posts_merkle_root(tampered.txs))

    result = validate_blocks(attacked)
    assert not result.ok, (
        f"블록 2 를 고치고 머클 루트만 맞췄는데 체인 전체가 유효하다고 나왔다. {describe(result)}\n"
        "→ prev_hash 링크가 검사되지 않고 있다."
    )
    assert result.first_bad_index == 3, (
        f"블록 2 의 해시가 바뀌었으니 블록 3 의 prev_hash 가 어긋난다. {describe(result)}"
    )


def test_recomputed_chain_passes_validation():
    """⚠ 공격자가 **뒤를 전부 재계산**하면 이 검증은 통과한다. 그걸 막는 것이 지금은 없다.

    이게 Phase 4(작업증명)가 존재하는 이유다 (Lab 1.3 §8 4번).
    이 테스트는 '버그'가 아니라 **한계를 못 박아 두는 기록**이다.
    """
    blocks = make_chain_blocks(5)
    attacked = list(blocks)
    tampered = _tamper_body(attacked[2], new_body="과거를 통째로 다시 쓴다")
    attacked[2] = dataclasses.replace(tampered, merkle_root=posts_merkle_root(tampered.txs))

    result = validate_blocks(relink(attacked))
    assert result.ok, (
        f"재계산된 체인이 거부됐다. {describe(result)}\n"
        "→ 이 테스트는 '통과하는 것이 정상'이다. Phase 1 의 검증은 과거를 전부 다시 쓴 공격자를 막지 못한다."
    )


def test_deleted_block_is_detected():
    """글(블록)을 통째로 지우는 공격 — Lab 1.2 의 6번 실험."""
    blocks = make_chain_blocks(6)
    attacked = [b for i, b in enumerate(blocks) if i != 2]

    result = validate_blocks(attacked)
    assert not result.ok, (
        f"블록 하나를 통째로 삭제했는데 유효하다고 답했다. {describe(result)}\n"
        "→ 개별 해시만으로는 삭제가 안 잡힌다. prev_hash 링크와 index 연속성이 필요하다."
    )
    assert result.first_bad_index == 2, (
        f"삭제된 자리(리스트 위치 2)에서 보고돼야 한다. {describe(result)}\n"
        "→ 위치 2 에는 index=3 인 블록이 와 있다. 불변식 `chain[i].index == i` 가 여기서 깨진다."
    )


def test_prefix_of_a_valid_chain_is_still_valid():
    """맨 뒤를 잘라낸 체인(절단)은 검증만으로는 알 수 없다 — 이것도 한계 기록이다.

    "몇 개가 있었는지"는 체인 안에 없다. 탐지하려면 밖의 기준(앵커·피어)이 필요하다
    (→ Phase 5, Phase 7 / ADR-0003).
    """
    blocks = make_chain_blocks(6)
    result = validate_blocks(blocks[:4])
    assert result.ok, (
        f"정상 체인의 앞부분 4개가 거부됐다. {describe(result)}\n"
        "→ 검증은 '길이'를 기준으로 삼으면 안 된다. 앞에서부터의 연결만 본다."
    )


def test_reordered_blocks_are_detected():
    """글 순서 바꾸기 — Lab 1.2 의 7번 실험."""
    blocks = make_chain_blocks(6)
    attacked = list(blocks)
    attacked[2], attacked[3] = attacked[3], attacked[2]

    result = validate_blocks(attacked)
    assert not result.ok, (
        f"블록 2 와 3 의 순서를 바꿨는데 유효하다고 답했다. {describe(result)}\n"
        "→ 각 블록이 자기 해시만 갖고 있으면 순서 바꾸기는 잡히지 않는다. 링크가 필요하다."
    )
    assert result.first_bad_index == 2, (
        f"순서가 어긋난 첫 위치는 2 다. {describe(result)}"
    )
