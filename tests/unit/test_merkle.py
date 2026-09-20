"""Lab 1.4 — 머클 루트 (`core/merkle.py`)

    merkle_root(leaves: Sequence[bytes]) -> str
    merkle_proof(leaves: Sequence[bytes], index: int) -> list[tuple[str, str]]
    verify_proof(leaf: bytes, proof: list[tuple[str, str]], root: str) -> bool

**이 파일의 주인공은 `test_no_two_leaf_lists_share_a_root` 다.**
랩은 일부러 "홀수 리프면 마지막 해시를 복제한다"(비트코인 방식)로 먼저 구현하게 한 뒤
이 테스트를 돌려 hypothesis 가 반례를 찾아내는 것을 보게 한다 — **CVE-2012-2459**.
복제(duplicate) 방식에서는 반드시 실패하고, 승격(promote) 방식에서는 반드시 통과한다.
"""

from __future__ import annotations

import pytest
from conftest import core_merkle, st_two_distinct_leaf_lists
from hypothesis import assume, example, given
from hypothesis import strategies as st

st_leaves = st.lists(st.binary(min_size=1, max_size=8), min_size=1, max_size=20)


def _root(leaves):
    return core_merkle().merkle_root(list(leaves))


def _short(leaves):
    """실패 메시지용 — 리프 목록을 읽기 좋게."""
    return "[" + ", ".join(repr(x) for x in leaves) + "]"


def test_merkle_root_is_deterministic():
    """같은 리프 목록이면 항상 같은 루트."""
    leaves = [b"post-0", b"post-1", b"post-2"]
    first = _root(leaves)
    assert isinstance(first, str), f"merkle_root 는 hex 문자열을 반환해야 한다. 받은 타입: {type(first)}"
    assert first == _root(leaves), "같은 리프 목록인데 호출할 때마다 루트가 달라졌다 (결정성 위반)."
    assert first == _root(list(leaves)), "리스트 객체가 달라졌다고 루트가 달라지면 안 된다."


@given(st_leaves)
def test_merkle_root_is_deterministic_property(leaves):
    assert _root(leaves) == _root(list(leaves)), f"결정성 위반: {_short(leaves)}"


@given(leaves=st_leaves, data=st.data())
def test_merkle_root_changes_on_leaf_change(leaves, data):
    """리프 하나라도 바뀌면 루트가 바뀐다."""
    index = data.draw(st.integers(min_value=0, max_value=len(leaves) - 1))
    replacement = data.draw(st.binary(min_size=1, max_size=8))
    assume(replacement != leaves[index])

    changed = list(leaves)
    changed[index] = replacement

    assert _root(leaves) != _root(changed), (
        f"리프 {index} 를 {leaves[index]!r} → {replacement!r} 로 바꿨는데 루트가 같다.\n"
        f"  before {_short(leaves)}\n  after  {_short(changed)}\n"
        f"  root   {_root(leaves)}"
    )


@given(st_leaves)
def test_merkle_root_changes_on_reorder(leaves):
    """리프의 **순서도 커밋되는 정보**다. 접기 전에 정렬하면 이 테스트가 깨진다."""
    assume(len(leaves) >= 2)
    swapped = list(leaves)
    for i in range(len(leaves) - 1):
        if swapped[i] != swapped[i + 1]:
            swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
            break
    else:
        assume(False)  # 전부 같은 값이면 순서를 바꿔도 같은 목록이다

    assert _root(leaves) != _root(swapped), (
        "두 리프의 순서만 바꿨는데 루트가 같다 → 접기 전에 정렬을 했을 가능성이 높다.\n"
        f"  before {_short(leaves)}\n  after  {_short(swapped)}"
    )


def test_merkle_root_single_leaf():
    """리프가 1개인 경계. IndexError 가 나기 쉬운 자리다."""
    root = _root([b"only"])
    assert isinstance(root, str) and root, "리프 1개의 루트가 문자열이 아니다."
    assert root == _root([b"only"]), "리프 1개에서도 결정적이어야 한다."
    assert root != _root([b"only", b"only"]), (
        "리프 1개짜리와 '같은 리프 2개'짜리의 루트가 같다.\n"
        "→ 이것이 CVE-2012-2459 의 가장 작은 형태다 (test_merkle_root_does_not_duplicate_last_leaf 참고)."
    )


@pytest.mark.parametrize("n", [3, 5, 7, 9])
def test_merkle_root_odd_leaves(n):
    """홀수 개의 리프에서도 예외 없이 동작하고, 짝수 이웃과 다른 루트를 낸다."""
    leaves = [bytes([i]) for i in range(n)]
    root = _root(leaves)
    assert isinstance(root, str) and root, f"리프 {n} 개에서 루트가 비었다."
    assert root == _root(leaves), f"리프 {n} 개에서 결정성 위반."
    assert root != _root(leaves[:-1]), (
        f"리프 {n} 개와 {n - 1} 개의 루트가 같다 — 마지막 리프가 루트에 반영되지 않았다."
    )
    # 승격(promote)된 노드도 증명 경로가 성립해야 한다.
    merkle = core_merkle()
    proof = merkle.merkle_proof(leaves, n - 1)
    assert merkle.verify_proof(leaves[-1], proof, root), (
        f"홀수 리프의 마지막(승격된) 리프 증명이 실패했다. n={n}, proof={proof!r}\n"
        "→ 루트 계산만 promote 로 고치고 merkle_proof 를 안 고치면 여기서 조용히 실패한다 (Lab 1.4 §3)."
    )


def test_merkle_root_does_not_duplicate_last_leaf():
    """🔴 `[a,b,c]` 와 `[a,b,c,c]` 의 루트는 **달라야** 한다 — CVE-2012-2459 직접 검사.

    홀수 리프를 복제(duplicate)해 짝을 맞추면 이 두 목록이 완전히 같은 트리가 된다.
    루트가 같으면 블록 해시도 같아서 **변조된 블록과 원본 블록이 구분되지 않는다.**
    """
    merkle = core_merkle()
    a = [b"\x00", b"\x01", b"\x02"]
    b = [b"\x00", b"\x01", b"\x02", b"\x02"]

    root_a = merkle.merkle_root(a)
    root_b = merkle.merkle_root(b)

    assert root_a != root_b, (
        "서로 다른 글 목록이 같은 머클 루트를 냈다 — CVE-2012-2459.\n"
        f"  a = {_short(a)}\n  b = {_short(b)}\n  root = {root_a}\n"
        "→ 홀수 리프는 **복제하지 말고 그대로 위 레벨로 올려라(promote)**. Lab 1.4 §3."
    )

    longer_a = [b"\x00", b"\x01", b"\x02", b"\x03", b"\x04"]
    longer_b = longer_a + [b"\x04"]
    assert merkle.merkle_root(longer_a) != merkle.merkle_root(longer_b), (
        "리프 5개와 '마지막을 복제한 6개'의 루트가 같다 — 같은 취약점의 다른 크기다.\n"
        f"  a = {_short(longer_a)}\n  b = {_short(longer_b)}"
    )


@given(pair=st_two_distinct_leaf_lists())
@example(pair=([b"\x00", b"\x01", b"\x02"], [b"\x00", b"\x01", b"\x02", b"\x02"]))
@example(pair=([b"\x00"], [b"\x00", b"\x00"]))
def test_no_two_leaf_lists_share_a_root(pair):
    """🔴 **서로 다른 리프 목록은 절대 같은 루트를 갖지 않는다.** 이 랩의 핵심 불변식.

    hypothesis 가 길이 1~20 을 흔들며 반례를 찾는다. 전략에는 "마지막 리프를 복제한 목록"이
    섞여 있어서, 복제 방식으로 구현했다면 **반드시** 반례가 나온다:

        Falsifying example: a=[b'\\x00', b'\\x01', b'\\x02'],
                            b=[b'\\x00', b'\\x01', b'\\x02', b'\\x02']

    그 화면을 본 다음 promote 로 고치는 것이 Lab 1.4 §1 의 순서다.
    """
    a, b = pair
    assume(a != b)

    root_a = _root(a)
    root_b = _root(b)

    assert root_a != root_b, (
        "서로 다른 두 리프 목록이 같은 루트를 냈다 (머클 루트의 충돌).\n"
        f"  a    = {_short(a)}\n"
        f"  b    = {_short(b)}\n"
        f"  root = {root_a}\n"
        "→ 이 상태에서는 '글 3개짜리 블록'과 '마지막 글을 한 번 더 복사한 4개짜리 블록'이\n"
        "  같은 블록 해시를 갖는다. 홀수 리프를 복제하지 말고 promote 하라 (Lab 1.4 §3)."
    )


@given(leaves=st_leaves)
def test_proof_roundtrip_all_indices(leaves):
    """모든 i 에 대해 `verify_proof(leaf_i, merkle_proof(leaves, i), merkle_root(leaves))` 가 True."""
    merkle = core_merkle()
    root = merkle.merkle_root(leaves)
    for i, leaf in enumerate(leaves):
        proof = merkle.merkle_proof(leaves, i)
        assert merkle.verify_proof(leaf, proof, root), (
            f"index {i} 의 증명이 자기 루트를 재구성하지 못했다.\n"
            f"  leaves = {_short(leaves)}\n  leaf   = {leaf!r}\n  proof  = {proof!r}\n  root   = {root}\n"
            "→ 흔한 원인: 좌우(L/R) 방향을 반대로 접었다 / 승격된 노드에서 형제를 넣어 버렸다."
        )


def test_proof_fails_for_wrong_leaf():
    """잘못된 리프나 잘못된 루트로는 증명이 성립하지 않는다."""
    merkle = core_merkle()
    leaves = [b"a", b"b", b"c", b"d", b"e"]
    root = merkle.merkle_root(leaves)
    proof = merkle.merkle_proof(leaves, 1)

    assert not merkle.verify_proof(b"not-in-the-block", proof, root), (
        "블록에 없는 글이 남의 증명 경로로 포함 증명에 성공했다. 증명이 아무것도 보장하지 못한다."
    )
    assert not merkle.verify_proof(leaves[0], proof, root), (
        "index 1 의 증명 경로로 index 0 의 리프가 검증을 통과했다 (경로가 위치를 구분하지 못한다)."
    )
    assert not merkle.verify_proof(leaves[1], proof, "f" * 64), (
        "엉뚱한 루트에 대해서도 증명이 통과했다."
    )
    if proof:
        broken = [(sibling, "L" if side == "R" else "R") for sibling, side in proof]
        assert not merkle.verify_proof(leaves[1], broken, root), (
            "형제의 좌우 방향을 전부 뒤집은 경로가 그대로 통과했다 — 방향이 검증에 쓰이지 않는다."
        )


def test_leaf_and_node_hashes_are_domain_separated():
    """리프 해시와 내부 노드 해시를 구분한다 (2차 역상 공격 방어).

    구분이 없으면 공격자가 **내부 노드 값을 리프인 척** 제시할 수 있다.
    아래는 그 공격을 그대로 재현한다: 두 리프 해시를 이어붙인 바이트열을
    리프 하나로 넣었을 때 원래의 루트가 나오면 안 된다.
    """
    merkle = core_merkle()
    a, b = b"post-a", b"post-b"
    combined_root = merkle.merkle_root([a, b])
    left = merkle.merkle_root([a])
    right = merkle.merkle_root([b])

    try:
        forged_leaf = bytes.fromhex(left) + bytes.fromhex(right)
    except ValueError:  # pragma: no cover - 루트가 hex 문자열이 아닌 경우
        pytest.fail(
            f"merkle_root 가 hex 문자열이 아니다: {left!r}. 블록 해시와 같은 표기(소문자 hex)로 맞춰라."
        )
    assert merkle.merkle_root([forged_leaf]) != combined_root, (
        "내부 노드의 재료(두 리프 해시를 이어붙인 바이트)를 **리프 하나로** 넣었더니 같은 루트가 나왔다.\n"
        f"  merkle_root([a, b])        = {combined_root}\n"
        f"  merkle_root([H(a)||H(b)])  = {merkle.merkle_root([forged_leaf])}\n"
        "→ 리프와 내부 노드에 서로 다른 도메인 접두(예: 0x00 / 0x01)를 붙여라 (Lab 1.4 §3)."
    )


def test_merkle_root_empty_leaves_is_defined():
    """리프 0개의 동작을 **명시적으로** 정했는가 (예외든 고정값이든 하나로).

    정하지 않으면 IndexError 가 나거나, 빈 블록과 다른 블록이 같은 루트를 갖는 사고가 난다.
    """
    merkle = core_merkle()
    try:
        first = merkle.merkle_root([])
    except Exception as exc:  # noqa: BLE001 - 예외로 정하는 것도 정당한 선택이다
        with pytest.raises(type(exc)):
            merkle.merkle_root([])
        assert not isinstance(exc, IndexError), (
            f"빈 리프에서 IndexError 가 났다: {exc!r}\n"
            "→ '정해진 규칙에 따른 거부'가 아니라 경계 처리 실수로 보인다. "
            "명시적으로 거부하거나(고유 예외) 고정된 빈 루트를 정하고 ADR-0001 에 적어라."
        )
        return
    assert isinstance(first, str) and first, f"빈 리프의 루트가 {first!r} 다."
    assert first == merkle.merkle_root([]), "빈 리프의 루트가 호출할 때마다 다르다."
    assert first != merkle.merkle_root([b""]), (
        "빈 목록과 '빈 바이트열 리프 1개'의 루트가 같다 — 두 블록이 구분되지 않는다."
    )


@pytest.mark.parametrize("n, expected", [(4, 2), (8, 3), (1024, 10)])
def test_proof_length_is_logarithmic(n, expected):
    """글 수가 256배(4 → 1024)로 늘어도 증명은 5배(2 → 10)다. 이 숫자가 Lab 1.4 의 목적이다."""
    merkle = core_merkle()
    leaves = [f"post-{i}".encode() for i in range(n)]
    proof = merkle.merkle_proof(leaves, n // 2)
    assert len(proof) == expected, (
        f"리프 {n} 개(2의 거듭제곱)에서 증명 길이는 log2({n}) = {expected} 여야 한다. 실제: {len(proof)}\n"
        f"proof={proof!r}"
    )
    assert merkle.verify_proof(leaves[n // 2], proof, merkle.merkle_root(leaves))
