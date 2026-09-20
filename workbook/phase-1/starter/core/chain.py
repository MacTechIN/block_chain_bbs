"""체인과 검증 — 블록을 이어 붙이고, 어디서 깨졌는지 지목한다.

이 파일은 **시작 파일**이다. 여기서 바로 고치지 말고 아래 위치로 복사해서 쓴다.

    복사 위치 : src/bbschain/core/chain.py
    대응 과제 : Lab 1.3 과제 (4)번  (Lab 1.4 과제 추가분 3번에서 검사가 한 줄 는다)
                docs/labs/phase-1-chain.md#lab-13--블록과-체인
    판정 테스트:
        uv run pytest tests/unit/test_chain_validation.py -v

    통과해야 할 이름
        test_valid_chain_passes
        test_valid_chain_passes_property
        test_validate_does_not_mutate_the_chain
        test_tampered_body_reports_first_bad_index
        test_tampered_body_reports_first_bad_index_property
        test_first_bad_index_is_the_earliest_break
        test_tampered_body_with_recomputed_merkle_root_breaks_the_next_link
        test_recomputed_chain_passes_validation
        test_deleted_block_is_detected
        test_prefix_of_a_valid_chain_is_still_valid
        test_reordered_blocks_are_detected

선행 : core/block.py.

랩은 산출물로 core/chain.py 와 core/validation.py **둘**을 적어 뒀다.
아래 ValidationResult 와 검증 함수를 core/validation.py 로 옮겨도 된다 —
판정기는 두 배치를 모두 받아 준다 (tests/conftest.py 의 validate_blocks 를 보라).
**어느 쪽으로 나눌지는 네 결정이다.**
"""

from __future__ import annotations

from dataclasses import dataclass

from bbschain.core.block import Block

# 제네시스 블록의 prev_hash 로 쓸 고정 상수를 여기에 선언한다.
# 무엇을 넣을지는 Lab 1.3 사전지식 질문 2번이 묻는 것이다 — 네가 정한다.
# 판정기는 GENESIS_PREV / GENESIS_PREV_HASH / ZERO_HASH 같은 이름을 찾는다
# (tests/conftest.py 의 genesis_prev_hash 참고).


@dataclass(frozen=True)
class ValidationResult:
    """검증 결과. **bool 이 아니다** — 어디서 깨졌는지까지 말한다."""

    ok: bool
    first_bad_index: int | None
    reason: str | None


class Chain:
    """블록을 순서대로 담고, 글을 추가하고, 전체를 검증한다."""

    # 판정기가 Chain 을 만들 때 시도하는 형태들 (tests/conftest.py 의 _chain_with_blocks)
    #   Chain(blocks=[...]) / Chain([...]) / Chain(storage=...) / Chain(...) / Chain()
    # 하나만 되면 된다. 생성자 모양은 네가 정한다.
    #
    # 🔴 이 모듈은 storage/jsonfile.py 를 import 하지 않는다.
    #    Storage 프로토콜(타입)에만 의존한다 — Phase 2 에서 SQLite 로 갈아끼우기 위해서다.
    #    test_chain_does_not_import_the_json_implementation 이 이걸 강제한다.

    def add_post(self, author: str, body: str) -> Block:
        """글 하나를 담은 새 블록을 만들어 tip 뒤에 붙이고, 그 블록을 돌려준다."""
        raise NotImplementedError("Lab 1.3 과제 (4)번 — 여기를 채워라")

    def tip(self) -> Block:
        """마지막 블록."""
        raise NotImplementedError("Lab 1.3 과제 (4)번 — 여기를 채워라")

    def validate(self) -> ValidationResult:
        """체인 전체를 앞에서부터 훑어 최초로 깨진 지점을 찾는다."""
        # 만족해야 할 불변식 (Lab 1.3 §3(4))
        #   · 제네시스는 index == 0 이고 prev_hash 가 고정 상수다
        #   · 모든 i > 0 에 대해 chain[i].prev_hash == chain[i-1].hash
        #   · 모든 i 에 대해 chain[i].index == i
        #   · 모든 i 에 대해 저장된 해시가 재계산한 해시와 같다
        #   · 하나라도 깨지면 ok=False, first_bad_index=**최초로** 깨진 인덱스,
        #     reason=사람이 읽을 수 있는 이유.
        #     3번이 깨져 4·5·6 이 연쇄로 깨져도 답은 3이다
        #   · validate() 는 체인을 **변경하지 않는다** (순수 조회)
        #
        # Lab 1.4 에서 한 줄이 는다 (§3 추가분 3번)
        #   · 블록에 적힌 merkle_root 가 그 블록의 txs 로 다시 계산한 값과 같은가.
        #     이 대조가 없으면 본문 변조가 **아무 데서도** 안 잡힌다
        raise NotImplementedError("Lab 1.3 과제 (4)번 — 여기를 채워라")
