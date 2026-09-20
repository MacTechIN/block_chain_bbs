"""Lab 1.3 — 블록 (`core/block.py`)
+ Lab 1.4 에서 초록이 되는 두 개(`test_block_hash_input_excludes_txs`,
  `test_tampering_a_post_still_changes_block_hash`).

계약: 개발계획서 6절 "Phase 1에 고정할 핵심 계약" 2번·5번
    Block(index, prev_hash, timestamp, merkle_root, nonce, difficulty, txs).hash
    Post(author, body, ts, nonce=0, sig=None)
    `hash` 의 **최종** 입력은 헤더 6개 필드다. txs 는 merkle_root 를 통해 간접 커밋된다.
"""

from __future__ import annotations

import dataclasses

import pytest
from conftest import (
    FIXED_TS,
    block_cls,
    describe,
    genesis_prev_hash,
    make_block,
    make_chain_blocks,
    make_post,
    post_cls,
    posts_merkle_root,
    st_block,
    validate_blocks,
)
from hypothesis import given

HEADER_FIELDS = ("index", "prev_hash", "timestamp", "merkle_root", "nonce", "difficulty")


def test_block_and_post_field_names_are_fixed():
    """필드 **이름과 집합**은 Phase 1 에서 고정한다 (ADR-0001 마지막 절).

    `author` 를 `from` 으로 바꾸기만 해도 쌓아 둔 모든 블록의 해시가 바뀐다.
    `nonce`/`difficulty`/`sig` 는 Phase 3~4 까지 쓰이지 않지만 **지금** 자리를 잡아 둔다.
    """
    block_fields = tuple(f.name for f in dataclasses.fields(block_cls()))
    assert block_fields == (*HEADER_FIELDS, "txs"), (
        f"Block 의 필드 집합이 계약과 다르다.\n  기대: {(*HEADER_FIELDS, 'txs')}\n  실제: {block_fields}\n"
        "→ 지금 빠뜨린 필드는 Phase 4 에서 추가하는 순간 기존 체인을 전부 무효로 만든다."
    )

    post_fields = tuple(f.name for f in dataclasses.fields(post_cls()))
    assert post_fields == ("author", "body", "ts", "nonce", "sig"), (
        f"Post 의 필드 집합이 계약과 다르다.\n  기대: ('author', 'body', 'ts', 'nonce', 'sig')\n"
        f"  실제: {post_fields}\n"
        "→ Phase 3 에서 nonce/sig 를 '추가'하면 그때까지의 모든 머클 루트와 블록 해시가 바뀐다."
    )

    defaults = {f.name: f.default for f in dataclasses.fields(post_cls())}
    assert defaults["nonce"] == 0, "Post.nonce 의 기본값은 Phase 3 까지 0 이다."
    assert defaults["sig"] is None, "Post.sig 의 기본값은 Phase 3 까지 None 이다."


def test_block_hash_is_deterministic():
    """같은 필드 값이면 언제 몇 번을 계산해도 같은 해시다."""
    a = make_block(index=1, prev_hash="a" * 64, timestamp=FIXED_TS)
    b = make_block(index=1, prev_hash="a" * 64, timestamp=FIXED_TS)

    assert a.hash == a.hash, "같은 객체인데 hash 를 두 번 읽으니 값이 달랐다 (내부에 난수/시각이 섞였다)."
    assert a == b, "같은 값으로 만든 두 블록이 같지 않다 (frozen dataclass 의 __eq__ 를 깨뜨렸다)."
    assert a.hash == b.hash, (
        f"같은 필드 값의 두 블록이 다른 해시를 냈다.\n  {a.hash}\n  {b.hash}\n"
        "→ 해시 입력에 time.time() 이나 id() 같은 비결정적 값이 섞였을 가능성이 높다."
    )
    assert isinstance(a.hash, str) and len(a.hash) == 64, (
        f"블록 해시는 sha256 hex 문자열(64자)이어야 한다. 받은 값: {a.hash!r}"
    )


@given(st_block())
def test_block_hash_is_deterministic_property(block):
    """임의의 블록에 대해서도 결정성이 유지된다."""
    twin = dataclasses.replace(block)
    assert block.hash == twin.hash, f"동일한 값의 블록이 다른 해시를 냈다: {block!r}"


@pytest.mark.parametrize("field", HEADER_FIELDS)
def test_block_hash_changes_when_any_field_changes(field):
    """헤더 6개 필드는 **하나하나 전부** 해시 입력에 들어가야 한다.

    빠진 필드는 변조해도 안 잡힌다. (글 변조가 잡히는지는
    `test_tampering_a_post_still_changes_block_hash` 가 따로 본다.)
    """
    base = make_block(index=3, prev_hash="b" * 64, timestamp=FIXED_TS, nonce=7, difficulty=0x1D00FFFF)
    mutations = {
        "index": 4,
        "prev_hash": "c" * 64,
        "timestamp": FIXED_TS + 1,
        "merkle_root": "d" * 64,
        "nonce": 8,
        "difficulty": 0x1E00FFFF,
    }
    changed = dataclasses.replace(base, **{field: mutations[field]})

    assert changed.hash != base.hash, (
        f"`{field}` 만 바꿨는데 블록 해시가 그대로다 → 이 필드는 해시 입력에서 빠져 있다.\n"
        f"  before {field}={getattr(base, field)!r}\n  after  {field}={mutations[field]!r}\n"
        f"  hash   {base.hash}\n"
        "→ 해시 입력 payload 에 헤더 6개 필드가 전부 들어갔는지 확인하라 (Lab 1.3 §3(3))."
    )


def test_block_is_frozen():
    """`Block` 과 `Post` 는 만든 뒤 바꿀 수 없다.

    가변이면 "해시를 계산한 뒤 내용을 바꾸는" 공격이 코드 안에서 가능해진다.
    """
    block = make_block(index=1)
    for field in (*HEADER_FIELDS, "txs"):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(block, field, None)

    post = make_post()
    for field in ("author", "body", "ts", "nonce", "sig"):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(post, field, None)


def test_genesis_rules():
    """제네시스는 `index == 0` 이고 `prev_hash` 가 고정된 상수다 (Lab 1.3 §3(4))."""
    blocks = make_chain_blocks(3)
    genesis = blocks[0]

    assert genesis.index == 0, f"제네시스의 index 는 0 이어야 한다. 실제: {genesis.index}"
    assert genesis.prev_hash == genesis_prev_hash(), (
        f"제네시스의 prev_hash 가 고정 상수와 다르다.\n  기대: {genesis_prev_hash()}\n"
        f"  실제: {genesis.prev_hash}\n"
        "→ 상수를 core/chain.py 에 GENESIS_PREV 로 노출하면 테스트가 그 값을 쓴다."
    )

    # ① prev_hash 가 상수가 아닌 제네시스
    bad_prev = [dataclasses.replace(genesis, prev_hash="f" * 64), *blocks[1:]]
    result = validate_blocks(bad_prev)
    assert not result.ok, f"제네시스의 prev_hash 를 바꿨는데 유효하다고 답했다. {describe(result)}"
    assert result.first_bad_index == 0, (
        f"제네시스가 깨졌으면 최초 파손 인덱스는 0 이다. {describe(result)}"
    )

    # ② index 가 0 이 아닌 제네시스 (뒤 블록은 정상적으로 이어 붙여 격리한다)
    shifted = dataclasses.replace(genesis, index=5)
    following = dataclasses.replace(blocks[1], prev_hash=shifted.hash)
    result = validate_blocks([shifted, following, *blocks[2:]])
    assert not result.ok, f"제네시스의 index 가 5 인데 유효하다고 답했다. {describe(result)}"
    assert result.first_bad_index == 0, (
        f"제네시스의 index 위반도 인덱스 0 에서 보고돼야 한다. {describe(result)}"
    )


# ── 여기부터 Lab 1.4 ─────────────────────────────────────────────────────
# 아래 두 개는 **쌍이다.** 앞의 것만 통과시키면 Lab 1.2 의 공격이 그대로 다시 통한다.


def test_block_hash_input_excludes_txs():
    """Lab 1.4 §3 2번 — 해시 입력에서 `txs` 를 뺐는가.

    `merkle_root` 가 이미 글 집합을 커밋하므로 `txs` 를 해시 입력에 **또** 넣을 이유가 없다.
    남겨 두면 Phase 4 의 채굴 루프가 nonce 하나 바꿀 때마다 글 전체를 다시 직렬화한다.

    **Lab 1.3 을 막 끝낸 시점에는 이 테스트가 빨간 것이 정상이다.**
    """
    posts_a = (make_post(body="원본 글", ts=FIXED_TS),)
    posts_b = (make_post(body="완전히 다른 글", ts=FIXED_TS),)
    root = "e" * 64  # 헤더가 커밋하는 값은 merkle_root 하나뿐이다

    a = make_block(index=2, prev_hash="a" * 64, timestamp=FIXED_TS, merkle_root=root, txs=posts_a)
    b = make_block(index=2, prev_hash="a" * 64, timestamp=FIXED_TS, merkle_root=root, txs=posts_b)

    assert a.hash == b.hash, (
        "헤더 6개 필드가 같은데 txs 만 다른 두 블록의 해시가 달랐다 → `txs` 가 아직 해시 입력에 남아 있다.\n"
        f"  a.txs={posts_a!r} -> {a.hash}\n  b.txs={posts_b!r} -> {b.hash}\n"
        "→ Lab 1.4 §3 2번: payload 에서 txs 를 빼고 헤더 6개 필드만 남겨라."
    )


def test_tampering_a_post_still_changes_block_hash():
    """Lab 1.4 §6 — `txs` 를 뺐어도 **글을 고치면 블록 해시가 바뀐다.**

    경로가 바뀔 뿐이다: 글 → `merkle_root` → 헤더 해시.
    위 테스트만 통과시키고 이걸 놓치면 Lab 1.2 의 변조 공격이 그대로 다시 통한다.
    """
    posts = (
        make_post(body="오늘 점심 뭐 먹지", ts=FIXED_TS),
        make_post(body="두 번째 글", ts=FIXED_TS + 1),
        make_post(body="세 번째 글", ts=FIXED_TS + 2),
    )
    original = make_block(index=3, prev_hash="a" * 64, timestamp=FIXED_TS, txs=posts)

    tampered_posts = (
        posts[0],
        dataclasses.replace(posts[1], body="sam이 회사 돈을 횡령했다"),
        posts[2],
    )
    tampered_root = posts_merkle_root(tampered_posts)

    assert tampered_root != original.merkle_root, (
        "글 하나를 고쳤는데 머클 루트가 그대로다 → merkle_root 가 글 집합을 커밋하지 못하고 있다."
    )

    tampered = make_block(
        index=3,
        prev_hash="a" * 64,
        timestamp=FIXED_TS,
        merkle_root=tampered_root,
        txs=tampered_posts,
    )
    assert tampered.hash != original.hash, (
        "글을 고쳐 머클 루트가 바뀌었는데 블록 해시가 그대로다 → `merkle_root` 가 해시 입력에서 빠졌다.\n"
        f"  원본   merkle={original.merkle_root} hash={original.hash}\n"
        f"  변조본 merkle={tampered.merkle_root} hash={tampered.hash}"
    )
