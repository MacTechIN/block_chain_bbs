"""저장소 인터페이스 — 선언만 있고 구현은 없다.

이 파일은 **시작 파일**이다. 여기서 바로 고치지 말고 아래 위치로 복사해서 쓴다.

    복사 위치 : src/bbschain/storage/base.py
    대응 과제 : Lab 1.5 과제 (1)번
                docs/labs/phase-1-chain.md#lab-15--영속화와-검증-cli
    판정 테스트:
        uv run pytest tests/unit/test_storage_jsonfile.py -k mutation -v

    통과해야 할 이름
        test_storage_has_no_mutation_method

Phase 2 에서 storage/sqlite.py 가 이 프로토콜을 만족시키며 추가된다.
그때 코어를 한 줄도 안 고치려고 **지금** 인터페이스를 선언한다.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from bbschain.core.block import Block


class Storage(Protocol):
    """블록을 보관하는 곳이 지켜야 할 약속.

    만족해야 할 불변식 (Lab 1.5 §3(1))
      · 🔴 **append-only.** 수정·삭제 메서드는 만들지 않는다.
        "정상 경로로는 과거를 바꿀 수 없다"가 설계다
      · get_block 은 해시 문자열과 정수 인덱스를 **둘 다** 받는다
      · Chain 은 이 타입에만 의존한다. 구체 구현을 직접 import 하면 실패다
    """

    # 이 파일의 과제는 "인터페이스를 선언하는 것" 하나뿐이다.
    # 프로토콜 메서드의 본문은 관례상 `...` 로 둔다 — 아래 NotImplementedError 를
    # 그대로 둬도 판정기는 통과한다. 어느 쪽으로 할지는 네 선택이다.

    def append_block(self, block: Block) -> None:
        raise NotImplementedError("Lab 1.5 과제 (1)번 — 여기를 채워라")

    def get_block(self, key: str | int) -> Block | None:
        raise NotImplementedError("Lab 1.5 과제 (1)번 — 여기를 채워라")

    def tip(self) -> Block | None:
        raise NotImplementedError("Lab 1.5 과제 (1)번 — 여기를 채워라")

    def iter_blocks(self, start: int = 0, end: int | None = None) -> Iterator[Block]:
        raise NotImplementedError("Lab 1.5 과제 (1)번 — 여기를 채워라")

    def height(self) -> int:
        raise NotImplementedError("Lab 1.5 과제 (1)번 — 여기를 채워라")
