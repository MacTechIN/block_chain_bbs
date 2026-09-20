"""JSON 파일 저장소 — 프로세스가 죽어도 체인이 남게 한다.

이 파일은 **시작 파일**이다. 여기서 바로 고치지 말고 아래 위치로 복사해서 쓴다.

    복사 위치 : src/bbschain/storage/jsonfile.py
    대응 과제 : Lab 1.5 과제 (2)번
                docs/labs/phase-1-chain.md#lab-15--영속화와-검증-cli
    판정 테스트:
        uv run pytest tests/unit/test_storage_jsonfile.py -v
        uv run pytest tests/unit/test_serialize.py -k roundtrip -v
        uv run pytest tests/integration/test_restart_roundtrip.py -v

    통과해야 할 이름
        test_append_and_read_back
        test_empty_storage_is_empty
        test_get_block_by_hash_and_index
        test_atomic_write_survives_interruption
        test_block_dict_roundtrip          (tests/unit/test_serialize.py)
        test_restart_preserves_chain       (tests/integration/)
        test_restart_preserves_korean_bodies
        test_restart_preserves_arbitrary_chains

선행 : storage/base.py, core/block.py.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from bbschain.core.block import Block


class JsonFileStorage:
    """체인을 파일 하나에 담는 저장소.

    만족해야 할 불변식 (Lab 1.5 §3(2))
      · append_block → 프로세스 재시작 → iter_blocks 가 **완전히 같은 블록**을 준다.
        모든 필드의 타입까지 같아야 한다 (tuple 이 list 로 돌아오면 실패다)
      · 쓰기 도중 죽어도 파일이 **읽을 수 없는 상태가 되지 않는다** (원자적 쓰기)
      · 파일이 없으면 빈 체인에서 시작한다 (예외를 던지지 않는다)
      · 🔴 수정·삭제 메서드를 만들지 않는다. append-only 다
    """

    def __init__(self, path: str | Path) -> None:
        raise NotImplementedError("Lab 1.5 과제 (2)번 — 여기를 채워라")

    def append_block(self, block: Block) -> None:
        raise NotImplementedError("Lab 1.5 과제 (2)번 — 여기를 채워라")

    def get_block(self, key: str | int) -> Block | None:
        # 없는 인덱스·없는 해시는 예외가 아니라 None 이다
        raise NotImplementedError("Lab 1.5 과제 (2)번 — 여기를 채워라")

    def tip(self) -> Block | None:
        # 빈 저장소의 tip() 은 None 이다
        raise NotImplementedError("Lab 1.5 과제 (2)번 — 여기를 채워라")

    def iter_blocks(self, start: int = 0, end: int | None = None) -> Iterator[Block]:
        raise NotImplementedError("Lab 1.5 과제 (2)번 — 여기를 채워라")

    def height(self) -> int:
        raise NotImplementedError("Lab 1.5 과제 (2)번 — 여기를 채워라")


# Lab 1.5 메모 —
#   Block ↔ dict 변환 한 쌍(to_dict / from_dict)을 어디에 둘지는 **네 결정**이다
#   (Lab 1.5 §4 L2 힌트가 묻는다). 판정기는 Block.to_dict()/Block.from_dict(d) 와
#   모듈 레벨 block_to_dict()/block_from_dict() 를 모두 받아 준다.
#   저장 포맷(들여쓰기·ensure_ascii)과 canonical_bytes 의 규칙은 **별개 결정**이다.
