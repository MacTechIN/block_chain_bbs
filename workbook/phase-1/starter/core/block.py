"""글(Post)과 블록(Block) — 필드 집합을 Phase 1에서 고정한다.

이 파일은 **시작 파일**이다. 여기서 바로 고치지 말고 아래 위치로 복사해서 쓴다.

    복사 위치 : src/bbschain/core/block.py
    대응 과제 : Lab 1.3 과제 (3)번  (그리고 Lab 1.4 과제 추가분 2번에서 다시 손댄다)
                docs/labs/phase-1-chain.md#lab-13--블록과-체인
    판정 테스트:
        uv run pytest tests/unit/test_block.py -v

    Lab 1.3 에서 통과해야 할 이름
        test_block_and_post_field_names_are_fixed
        test_block_hash_is_deterministic
        test_block_hash_is_deterministic_property
        test_block_hash_changes_when_any_field_changes
        test_block_is_frozen
        test_genesis_rules
    Lab 1.4 에서 초록이 되는 이름 (Lab 1.3 시점에는 빨간 것이 정상이다)
        test_block_hash_input_excludes_txs
        test_tampering_a_post_still_changes_block_hash

선행 : core/hashing.py 의 hash_object.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Post:
    """게시판 글 하나. Phase 3 의 Transaction 과 같은 자리다."""

    author: str
    body: str
    ts: int
    nonce: int = 0  # Phase 3 까지 항상 0. 그래도 지금 넣는다
    sig: str | None = None  # Phase 3 까지 항상 None. 그래도 지금 넣는다


@dataclass(frozen=True)
class Block:
    """글을 담은 상자. 헤더 6개 필드 + txs."""

    index: int
    prev_hash: str
    timestamp: int
    merkle_root: str  # Lab 1.4 까지는 자리만. 임시로 txs 전체 해시를 넣어도 된다
    nonce: int  # Phase 4 까지 항상 0. 그래도 지금 넣는다
    difficulty: int  # compact target(nBits). Phase 4 까지 항상 0. 그래도 지금 넣는다
    txs: tuple[Post, ...]

    @property
    def hash(self) -> str:
        """이 블록의 지문. 저장하지 않고 필요할 때마다 다시 계산한다."""
        # 만족해야 할 불변식 (Lab 1.3 §3(3))
        #   · 같은 필드 값이면 몇 번을 계산해도 같은 값이다 (난수·현재시각 금지)
        #   · 결과는 sha256 hex 문자열 64자다
        #   · 해시 입력은 canonical_bytes 를 거친다 — 직접 encode 하지 않는다
        #   · **Lab 1.3 시점**: 입력에 7개 필드가 전부 들어간다.
        #     하나라도 빠지면 그 필드는 변조해도 안 잡힌다
        #   · **Lab 1.4 에서**: 입력에서 txs 를 빼고 헤더 6개 필드만 남긴다.
        #     글 집합은 merkle_root 를 통해 간접적으로 커밋된다 (= 헤더 해시)
        raise NotImplementedError("Lab 1.3 과제 (3)번 — 여기를 채워라")


# Lab 1.5 메모 —
#   저장 왕복을 위해 dict 변환 한 쌍(to_dict / from_dict)이 필요해진다.
#   그걸 이 파일에 둘지 storage/jsonfile.py 에 둘지는 **랩이 네게 맡긴 결정**이다
#   (Lab 1.5 §4 L2 힌트). 그래서 시작 파일에 자리를 만들어 두지 않았다.
