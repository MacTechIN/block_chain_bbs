"""머클 트리 — 글 집합을 값 하나로 요약하고, 일부만으로 포함을 증명한다.

이 파일은 **시작 파일**이다. 여기서 바로 고치지 말고 아래 위치로 복사해서 쓴다.

    복사 위치 : src/bbschain/core/merkle.py
    대응 과제 : Lab 1.4 과제
                docs/labs/phase-1-chain.md#lab-14--머클-루트
    판정 테스트:
        uv run pytest tests/unit/test_merkle.py -v

    통과해야 할 이름
        test_merkle_root_is_deterministic
        test_merkle_root_is_deterministic_property
        test_merkle_root_changes_on_leaf_change
        test_merkle_root_changes_on_reorder
        test_merkle_root_single_leaf
        test_merkle_root_odd_leaves
        test_merkle_root_does_not_duplicate_last_leaf
        test_no_two_leaf_lists_share_a_root          ← 홀수 리프 처리가 걸리는 곳
        test_proof_roundtrip_all_indices
        test_proof_fails_for_wrong_leaf
        test_leaf_and_node_hashes_are_domain_separated
        test_merkle_root_empty_leaves_is_defined
        test_proof_length_is_logarithmic

🔴 랩은 **일부러 취약한 방식으로 먼저 구현하라**고 한다. 순서를 지켜라
   (workbook/phase-1/lab-1.4.md 의 1절).
"""

from __future__ import annotations

from collections.abc import Sequence


def merkle_root(leaves: Sequence[bytes]) -> str:
    """리프 해시들로부터 머클 루트를 계산한다."""
    # 만족해야 할 불변식 (Lab 1.4 §3)
    #   · 🔴 서로 다른 리프 목록은 절대 같은 루트를 갖지 않는다 — 이 랩의 핵심이다
    #   · 리프 하나라도 바뀌면 루트가 바뀐다
    #   · 리프 **순서**가 바뀌면 루트가 바뀐다 (정렬하지 마라)
    #   · 리프가 1개일 때의 규칙을 정한다
    #   · 리프가 0개일 때의 동작을 **명시적으로** 정한다 (예외인가, 고정된 빈 루트인가).
    #     정했으면 ADR-0001 에 덧붙인다
    #   · 리프 해시와 내부 노드 해시를 구분한다 (2차 역상 공격 방어).
    #     구분 방법은 네가 정하고 기록한다
    raise NotImplementedError("Lab 1.4 과제 (1)번 — 여기를 채워라")


def merkle_proof(leaves: Sequence[bytes], index: int) -> list[tuple[str, str]]:
    """index 리프가 루트에 포함됨을 증명하는 형제 해시 경로.

    각 원소는 (형제해시, 'L'|'R') — 형제가 왼쪽인지 오른쪽인지.
    """
    # 만족해야 할 불변식 (Lab 1.4 §3)
    #   · merkle_root 와 **같은 규칙**으로 층을 접어야 한다.
    #     루트 계산만 고치고 여기를 안 고치면 verify_proof 가 조용히 실패한다
    #   · 형제가 없는 층에서는 경로에 아무것도 추가하지 않는다
    #   · 리프가 2의 거듭제곱 개면 경로 길이는 log2(N) 이다
    raise NotImplementedError("Lab 1.4 과제 (2)번 — 여기를 채워라")


def verify_proof(leaf: bytes, proof: list[tuple[str, str]], root: str) -> bool:
    """리프와 증명 경로만으로 루트를 재구성해 대조한다."""
    # 만족해야 할 불변식 (Lab 1.4 §3)
    #   · verify_proof(leaf, merkle_proof(leaves, i), merkle_root(leaves)) 는
    #     모든 i 에 대해 True 다
    #   · 잘못된 리프나 잘못된 경로로는 False 가 나온다 (예외가 아니라 False)
    raise NotImplementedError("Lab 1.4 과제 (3)번 — 여기를 채워라")
