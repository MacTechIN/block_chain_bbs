"""Phase 1 랩 공용 픽스처 · hypothesis 전략 · 구현 어댑터.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
이 디렉터리의 테스트는 **아직 없는 구현을 대상으로 미리 작성된 것**이다.
`src/bbschain/` 아래 모듈이 없으면 수집(collection) 단계에서 실패한다. **그게 정상이다.**
실패 메시지에 "어느 랩에서 무엇을 만들면 초록이 되는지"가 적혀 있다.

랩 ↔ 테스트 파일 대응
    Lab 1.3  core/serialize.py, core/hashing.py, core/block.py,
             core/chain.py, core/validation.py
             → tests/unit/test_serialize.py, test_block.py, test_chain_validation.py
    Lab 1.4  core/merkle.py (+ Block.hash 에서 txs 제거)
             → tests/unit/test_merkle.py, test_block.py 의 뒷부분 두 개
    Lab 1.5  storage/base.py, storage/jsonfile.py, cli.py
             → tests/unit/test_storage_jsonfile.py, test_cli.py,
               tests/integration/test_restart_roundtrip.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

테스트가 기대하는 **인터페이스 계약** (랩 문서와 개발계획서 6절에서 나온 것)

    canonical_bytes(obj) -> bytes                      bbschain.core.serialize
    sha256_hex(data) / hash_object(obj) -> str         bbschain.core.hashing
    Post(author, body, ts, nonce=0, sig=None)          bbschain.core.block
    Block(index, prev_hash, timestamp, merkle_root,    bbschain.core.block
          nonce, difficulty, txs).hash -> str
    merkle_root / merkle_proof / verify_proof          bbschain.core.merkle
    ValidationResult{ok, first_bad_index, reason}      bbschain.core.validation
    Chain.add_post / tip / validate                    bbschain.core.chain
    Storage 프로토콜 (append_block/get_block/tip/       bbschain.storage.base
          iter_blocks/height — 수정·삭제 메서드 없음)
    JsonFileStorage(path)                              bbschain.storage.jsonfile
    main(argv)                                         bbschain.cli

**이름이 완전히 고정되지 않은 것들은 아래 어댑터가 여러 형태를 시도한다.**
(예: `validate_chain(blocks)` 와 `Chain(blocks).validate()` 둘 다 허용,
 `Block.to_dict()` 와 모듈 레벨 `block_to_dict()` 둘 다 허용)
시도한 형태가 하나도 없으면 "무엇을 만들면 되는지"를 적은 에러가 난다.

시각은 **절대 `time.time()` 으로 읽지 않는다.** 아래 FIXED_TS 를 주입한다
(Phase 1 DoD: "고정 시각을 주입했을 때 재실행해도 동일하게 재현됨").
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import os
import sys
from collections.abc import Sequence
from typing import Any

import pytest

try:
    from hypothesis import HealthCheck, settings
    from hypothesis import strategies as st
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "\nhypothesis 가 설치돼 있지 않다. Phase 1 의 property 테스트에 필요하다.\n"
        "  uv add --dev hypothesis   (Lab 0.2 에서 pytest/ruff/mypy 와 함께 넣는 그 의존성이다)\n"
        f"원인: {exc}"
    ) from None

# ── hypothesis 프로파일 ────────────────────────────────────────────────────
# 해싱이 섞여 있어 예제 하나가 느릴 수 있다 → deadline 을 끈다.
settings.register_profile(
    "bbschain",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("bbschain")

# ── 고정 시각 (시각 주입용) ────────────────────────────────────────────────
FIXED_TS = 1_700_000_000
"""테스트가 쓰는 유일한 타임스탬프 기준점. 2023-11-14T22:13:20Z."""

TS_STEP = 60
"""블록 사이 간격. `timestamp` 단조 규칙(Lab 1.3 L3)을 만족시키기 위한 값."""


# ══════════════════════════════════════════════════════════════════════════
# 1. 구현 모듈 로더 — 아직 없을 때 "무엇을 만들면 되는지" 알려준다
# ══════════════════════════════════════════════════════════════════════════
class MissingImplementation(ImportError):
    """랩 과제 모듈/함수가 아직 없을 때 던진다. 실패가 아니라 '아직 안 만든 것'."""


def _banner(*, module: str, lab: str, expects: str, cause: str) -> str:
    return (
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        " 아직 구현이 없다 (이 시점에서는 정상이다)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f" 대상 : {module}\n"
        f" 랩   : {lab}   (docs/labs/phase-1-chain.md)\n"
        f" 필요 : {expects}\n"
        "\n"
        " 이 테스트는 위 랩의 과제를 만들면 초록이 된다.\n"
        f" 원인 : {cause}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )


def require_module(dotted: str, *, lab: str, expects: str):
    """구현 모듈을 import 한다. 없으면 안내가 붙은 MissingImplementation."""
    __tracebackhide__ = True
    try:
        return importlib.import_module(dotted)
    except ImportError as exc:  # ModuleNotFoundError 포함
        raise MissingImplementation(
            _banner(module=dotted, lab=lab, expects=expects, cause=f"{type(exc).__name__}: {exc}")
        ) from None


def require_attr(module, names: Sequence[str], *, lab: str, expects: str):
    """모듈에서 후보 이름 중 먼저 찾아지는 속성을 돌려준다."""
    __tracebackhide__ = True
    for name in names:
        obj = getattr(module, name, None)
        if obj is not None:
            return obj
    raise MissingImplementation(
        _banner(
            module=f"{module.__name__}.{{{' | '.join(names)}}}",
            lab=lab,
            expects=expects,
            cause=f"{module.__name__} 안에 {list(names)} 중 아무것도 없다",
        )
    )


# ── 랩별 모듈 접근자 (지연 import — conftest import 시점에 죽지 않게) ───────
def core_serialize():
    __tracebackhide__ = True
    return require_module(
        "bbschain.core.serialize",
        lab="Lab 1.3 — 블록과 체인",
        expects="canonical_bytes(obj) -> bytes",
    )


def core_hashing():
    __tracebackhide__ = True
    return require_module(
        "bbschain.core.hashing",
        lab="Lab 1.3 — 블록과 체인",
        expects="sha256_hex(data) -> str, hash_object(obj) -> str",
    )


def core_block():
    __tracebackhide__ = True
    return require_module(
        "bbschain.core.block",
        lab="Lab 1.3 — 블록과 체인",
        expects="@dataclass(frozen=True) Post, Block(+.hash)",
    )


def core_merkle():
    __tracebackhide__ = True
    return require_module(
        "bbschain.core.merkle",
        lab="Lab 1.4 — 머클 루트",
        expects="merkle_root(leaves), merkle_proof(leaves, index), verify_proof(leaf, proof, root)",
    )


def core_chain():
    __tracebackhide__ = True
    return require_module(
        "bbschain.core.chain",
        lab="Lab 1.3 — 블록과 체인",
        expects="Chain.add_post / Chain.tip / Chain.validate",
    )


def core_validation():
    __tracebackhide__ = True
    return require_module(
        "bbschain.core.validation",
        lab="Lab 1.3 — 블록과 체인",
        expects="ValidationResult{ok, first_bad_index, reason} + 체인 검증 함수",
    )


def storage_base():
    __tracebackhide__ = True
    return require_module(
        "bbschain.storage.base",
        lab="Lab 1.5 — 영속화와 검증 CLI",
        expects="class Storage(Protocol): append_block/get_block/tip/iter_blocks/height",
    )


def storage_jsonfile():
    __tracebackhide__ = True
    return require_module(
        "bbschain.storage.jsonfile",
        lab="Lab 1.5 — 영속화와 검증 CLI",
        expects="class JsonFileStorage(path) — 원자적 쓰기 + append-only",
    )


def cli_module():
    __tracebackhide__ = True
    return require_module(
        "bbschain.cli",
        lab="Lab 1.5 — 영속화와 검증 CLI",
        expects="main(argv) — post / dump / verify / tamper",
    )


# ══════════════════════════════════════════════════════════════════════════
# 2. 자료구조 어댑터
# ══════════════════════════════════════════════════════════════════════════
def post_cls():
    mod = core_block()
    post = getattr(mod, "Post", None)
    if post is None:  # transaction.py 에 두는 배치도 허용한다
        try:
            post = getattr(
                require_module(
                    "bbschain.core.transaction",
                    lab="Lab 1.3 — 블록과 체인",
                    expects="@dataclass(frozen=True) Post(author, body, ts, nonce=0, sig=None)",
                ),
                "Post",
                None,
            )
        except MissingImplementation:
            post = None
    if post is None:
        raise MissingImplementation(
            _banner(
                module="bbschain.core.block.Post",
                lab="Lab 1.3 — 블록과 체인",
                expects="@dataclass(frozen=True) Post(author, body, ts, nonce=0, sig=None)",
                cause="Post 클래스를 찾지 못했다",
            )
        )
    return post


def block_cls():
    return require_attr(
        core_block(),
        ("Block",),
        lab="Lab 1.3 — 블록과 체인",
        expects=(
            "@dataclass(frozen=True) Block(index, prev_hash, timestamp, "
            "merkle_root, nonce, difficulty, txs) + .hash"
        ),
    )


def make_post(
    *,
    author: str = "sam",
    body: str = "첫 글",
    ts: int = FIXED_TS,
    nonce: int = 0,
    sig: str | None = None,
):
    """고정 시각 Post. Phase 3 까지 nonce=0 / sig=None 이 정상값이다."""
    return post_cls()(author=author, body=body, ts=ts, nonce=nonce, sig=sig)


def post_to_dict(post) -> dict:
    """Post → dict. 사용자가 to_dict 를 정의했으면 그걸 쓴다."""
    to_dict = getattr(post, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return dataclasses.asdict(post)


def post_leaf(post) -> bytes:
    """Post 하나의 머클 리프 바이트.

    기본 가정: 리프 = `canonical_bytes(post_dict)`.
    다른 규칙을 쓰고 싶으면 `Post.to_leaf()` / `Post.leaf_bytes()` 를 노출하라.
    테스트는 그쪽을 먼저 쓴다.
    """
    for name in ("to_leaf", "leaf_bytes"):
        hook = getattr(post, name, None)
        if callable(hook):
            return hook()
    return core_serialize().canonical_bytes(post_to_dict(post))


def posts_merkle_root(posts: Sequence[Any]) -> str:
    """글 집합의 머클 루트.

    우선순위
      1. 사용자가 노출한 훅: core.block / core.merkle 의
         merkle_root_of_posts / posts_merkle_root / compute_merkle_root / txs_merkle_root,
         또는 `Block.compute_merkle_root(txs)`
      2. 기본 가정: `merkle_root([post_leaf(p) for p in posts])`
      3. Lab 1.3 시점(아직 core/merkle.py 가 없을 때): `hash_object([post_dict, ...])`
         — 랩이 허용한 "임시로 txs 전체 해시" 규칙

    ※ `Chain` 이 블록을 만들 때 쓰는 규칙과 **여기가 일치해야** 체인 검증 테스트가
      통과한다. 다른 규칙을 쓴다면 위 훅 중 하나를 노출하면 된다.
    """
    posts = tuple(posts)
    hooks = []
    mods = [core_block()]
    try:
        mods.append(core_merkle())
    except MissingImplementation:
        pass  # Lab 1.3 시점: 아직 core/merkle.py 가 없다 — 아래에서 임시 규칙으로 간다
    for mod in mods:
        for name in (
            "merkle_root_of_posts",
            "posts_merkle_root",
            "txs_merkle_root",
            "compute_merkle_root",
        ):
            fn = getattr(mod, name, None)
            if callable(fn):
                hooks.append(fn)
    fn = getattr(block_cls(), "compute_merkle_root", None)
    if callable(fn):
        hooks.append(fn)
    for hook in hooks:
        try:
            value = hook(posts)
        except TypeError:
            continue  # 시그니처가 다르면 다음 후보로
        if isinstance(value, str):
            return value
    try:
        merkle_root = core_merkle().merkle_root
    except MissingImplementation:
        # Lab 1.3 시점 — 아직 core/merkle.py 가 없다.
        # 랩이 허용한 임시 규칙("txs 전체 해시")로 대신한다. Lab 1.4 에서 자동으로 진짜 머클로 바뀐다.
        return core_hashing().hash_object([post_to_dict(p) for p in posts])
    return merkle_root([post_leaf(p) for p in posts])


def make_block(
    *,
    index: int = 0,
    prev_hash: str | None = None,
    timestamp: int = FIXED_TS,
    merkle_root: str | None = None,
    nonce: int = 0,
    difficulty: int = 0,
    txs: Sequence[Any] | None = None,
):
    """헤더 6개 필드 + txs 로 블록을 만든다. merkle_root 는 txs 로부터 계산한다."""
    if txs is None:
        txs = (make_post(body=f"글 #{index}", ts=timestamp),)
    txs = tuple(txs)
    if merkle_root is None:
        merkle_root = posts_merkle_root(txs)
    if prev_hash is None:
        prev_hash = genesis_prev_hash()
    return block_cls()(
        index=index,
        prev_hash=prev_hash,
        timestamp=timestamp,
        merkle_root=merkle_root,
        nonce=nonce,
        difficulty=difficulty,
        txs=txs,
    )


def block_to_dict(block) -> dict:
    """Block → dict (저장 왕복용). Block.to_dict / 모듈 레벨 함수 둘 다 허용."""
    hook = getattr(block, "to_dict", None)
    if callable(hook):
        return hook()
    for mod_getter in (core_block, storage_jsonfile):
        try:
            mod = mod_getter()
        except MissingImplementation:
            continue
        fn = getattr(mod, "block_to_dict", None)
        if callable(fn):
            return fn(block)
    raise MissingImplementation(
        _banner(
            module="Block.to_dict()",
            lab="Lab 1.5 — 영속화와 검증 CLI",
            expects="Block.to_dict()/Block.from_dict(d) 쌍 (또는 block_to_dict/block_from_dict)",
            cause="dict 변환 경로를 찾지 못했다",
        )
    )


def block_from_dict(data: dict):
    """dict → Block. `from_dict(to_dict(b)) == b` 가 성립해야 한다 (Lab 1.5 §4 L1)."""
    hook = getattr(block_cls(), "from_dict", None)
    if callable(hook):
        return hook(data)
    for mod_getter in (core_block, storage_jsonfile):
        try:
            mod = mod_getter()
        except MissingImplementation:
            continue
        fn = getattr(mod, "block_from_dict", None)
        if callable(fn):
            return fn(data)
    raise MissingImplementation(
        _banner(
            module="Block.from_dict()",
            lab="Lab 1.5 — 영속화와 검증 CLI",
            expects="Block.to_dict()/Block.from_dict(d) 쌍 (또는 block_to_dict/block_from_dict)",
            cause="dict → Block 복원 경로를 찾지 못했다",
        )
    )


# ── 제네시스 상수 ──────────────────────────────────────────────────────────
_GENESIS_NAMES = (
    "GENESIS_PREV",
    "GENESIS_PREV_HASH",
    "GENESIS_PREVIOUS_HASH",
    "GENESIS_PARENT_HASH",
    "ZERO_HASH",
)


def genesis_prev_hash() -> str:
    """제네시스 블록의 `prev_hash` 고정 상수.

    core.chain / core.block / core.validation / core.constants 에서
    GENESIS_PREV(_HASH) 류 이름을 찾는다. 못 찾으면 "0"*64 를 가정한다.
    (Lab 1.3 §3(4) 불변식: "제네시스 블록은 index == 0 이고 prev_hash 가 고정된 상수다")
    """
    for dotted in (
        "bbschain.core.chain",
        "bbschain.core.block",
        "bbschain.core.validation",
        "bbschain.core.constants",
    ):
        try:
            mod = importlib.import_module(dotted)
        except ImportError:
            continue
        for name in _GENESIS_NAMES:
            value = getattr(mod, name, None)
            if isinstance(value, str) and value:
                return value
    return "0" * 64


# ── 검증 어댑터 ───────────────────────────────────────────────────────────
def _has_result_shape(obj) -> bool:
    return all(hasattr(obj, f) for f in ("ok", "first_bad_index", "reason"))


class _MemoryStorage:
    """Storage 프로토콜을 만족하는 메모리 구현 — Chain 이 저장소를 요구할 때 쓴다."""

    def __init__(self, blocks):
        self._blocks = list(blocks)

    def append_block(self, block) -> None:
        self._blocks.append(block)

    def get_block(self, key):
        if isinstance(key, int):
            return self._blocks[key] if 0 <= key < len(self._blocks) else None
        return next((b for b in self._blocks if b.hash == key), None)

    def tip(self):
        return self._blocks[-1] if self._blocks else None

    def iter_blocks(self, start: int = 0, end: int | None = None):
        yield from self._blocks[start:end]

    def height(self) -> int:
        return len(self._blocks)


def _chain_holds(chain, blocks) -> bool:
    """만들어진 Chain 이 정말 그 블록들을 담고 있는지 확인한다."""
    if not hasattr(chain, "validate"):
        return False
    try:
        height = chain.height() if callable(getattr(chain, "height", None)) else None
        if height is not None and height != len(blocks):
            return False
        tip = getattr(chain, "tip", None)
        tip = tip() if callable(tip) else tip
        if blocks and tip is not None and tip != blocks[-1]:
            return False
    except Exception:  # noqa: BLE001 - 다른 후보로 넘어간다
        return False
    return True


def _chain_with_blocks(blocks):
    """블록 리스트를 담은 Chain 을 만들어 본다. 어떤 형태로도 안 되면 None."""
    try:
        Chain = getattr(core_chain(), "Chain", None)
    except MissingImplementation:
        return None
    if Chain is None:
        return None
    blocks = list(blocks)
    candidates = (
        lambda: Chain(blocks=blocks),
        lambda: Chain(blocks),
        lambda: Chain(storage=_MemoryStorage(blocks)),
        lambda: Chain(_MemoryStorage(blocks)),
    )
    for build in candidates:
        try:
            chain = build()
        except Exception:  # noqa: BLE001, S112 - 시그니처가 다르면 다음 후보로
            continue
        if _chain_holds(chain, blocks):
            return chain
    try:
        chain = Chain()
    except Exception:  # noqa: BLE001
        return None
    for attr in ("blocks", "_blocks", "chain", "_chain"):
        if hasattr(chain, attr):
            try:
                setattr(chain, attr, blocks)
            except Exception:  # noqa: BLE001, S112
                continue
            if _chain_holds(chain, blocks):
                return chain
    return None


def validate_blocks(blocks) -> Any:
    """블록 리스트를 검증해 ValidationResult 를 돌려준다.

    허용하는 형태 (먼저 찾아지는 것을 쓴다)
      1. `bbschain.core.validation.validate_chain(blocks)`
      2. `bbschain.core.chain.validate_chain(blocks)`
      3. `Chain(blocks).validate()` / `Chain(blocks=blocks).validate()`
    """
    blocks = list(blocks)
    errors: list[str] = []
    for dotted in ("bbschain.core.validation", "bbschain.core.chain"):
        try:
            mod = importlib.import_module(dotted)
        except ImportError as exc:
            errors.append(f"{dotted}: {exc}")
            continue
        fn = getattr(mod, "validate_chain", None)
        if callable(fn):
            result = fn(blocks)
            _assert_result_shape(result)
            return result
    chain = _chain_with_blocks(blocks)
    if chain is not None and hasattr(chain, "validate"):
        result = chain.validate()
        _assert_result_shape(result)
        return result
    raise MissingImplementation(
        _banner(
            module="validate_chain(blocks) / Chain(blocks).validate()",
            lab="Lab 1.3 — 블록과 체인",
            expects=(
                "validate_chain(blocks) -> ValidationResult, 또는 "
                "Chain(blocks) 로 만들 수 있고 .validate() 가 있는 Chain"
            ),
            cause="; ".join(errors) or "검증 진입점을 찾지 못했다",
        )
    )


def _assert_result_shape(result) -> None:
    assert _has_result_shape(result), (
        "validate() 는 bool 이 아니라 ValidationResult{ok, first_bad_index, reason} 를 "
        f"반환해야 한다 (개발계획서 6절 고정 계약 3번). 받은 값: {result!r}\n"
        "이유: Phase 2 탐색기가 '파손 지점부터 빨간 줄'을 그리려면 어디서 깨졌는지를 알아야 한다."
    )


def describe(result) -> str:
    """실패 메시지에 넣을 ValidationResult 요약."""
    return (
        f"ValidationResult(ok={result.ok!r}, "
        f"first_bad_index={result.first_bad_index!r}, reason={result.reason!r})"
    )


def make_chain_blocks(n: int = 4, *, start_ts: int = FIXED_TS, author: str = "sam"):
    """길이 n 의 **유효한** 체인을 만든다 (제네시스 포함, 고정 시각)."""
    blocks = []
    prev = genesis_prev_hash()
    for i in range(n):
        ts = start_ts + i * TS_STEP
        posts = (make_post(author=author, body=f"블록 {i} 의 글", ts=ts),)
        block = make_block(index=i, prev_hash=prev, timestamp=ts, txs=posts)
        blocks.append(block)
        prev = block.hash
    return blocks


def relink(blocks):
    """앞에서부터 prev_hash 를 다시 이어 붙인 새 블록 리스트 (재계산 공격 재현용)."""
    out = []
    prev = genesis_prev_hash()
    for block in blocks:
        fixed = dataclasses.replace(block, prev_hash=prev)
        out.append(fixed)
        prev = fixed.hash
    return out


# ══════════════════════════════════════════════════════════════════════════
# 3. hypothesis 전략
# ══════════════════════════════════════════════════════════════════════════
# 서로게이트가 섞이면 UTF-8 인코딩 자체가 불가능하므로 기본 st.text() 를 쓴다
# (기본값이 이미 surrogate 를 제외한다).
st_author = st.text(min_size=1, max_size=16)
st_body = st.text(min_size=0, max_size=80)
st_hex64 = st.text(alphabet="0123456789abcdef", min_size=64, max_size=64)
st_ts = st.integers(min_value=FIXED_TS, max_value=FIXED_TS + 10_000)
st_leaf = st.binary(min_size=0, max_size=8)


@st.composite
def st_post(draw, ts: int | None = None):
    """임의의 Post. nonce/sig 는 Phase 3 까지 0/None 이지만 왕복 검사를 위해 흔든다."""
    return make_post(
        author=draw(st_author),
        body=draw(st_body),
        ts=draw(st_ts) if ts is None else ts,
        nonce=draw(st.integers(min_value=0, max_value=2**32 - 1)),
        sig=draw(st.none() | st.text(alphabet="0123456789abcdef", min_size=2, max_size=32)),
    )


@st.composite
def st_block(draw, index: int | None = None):
    """임의의 Block. 체인으로 이어지지 않은 단일 블록(컨테이너로서의 성질 검사용)."""
    txs = tuple(draw(st.lists(st_post(), min_size=1, max_size=4)))
    return make_block(
        index=draw(st.integers(min_value=0, max_value=1000)) if index is None else index,
        prev_hash=draw(st_hex64),
        timestamp=draw(st_ts),
        merkle_root=posts_merkle_root(txs),
        nonce=draw(st.integers(min_value=0, max_value=2**32 - 1)),
        difficulty=draw(st.integers(min_value=0, max_value=2**32 - 1)),
        txs=txs,
    )


@st.composite
def st_chain(draw, min_size: int = 1, max_size: int = 6):
    """**유효한** 체인 (제네시스 + 링크). 고정 시각에서 출발해 단조 증가한다."""
    length = draw(st.integers(min_value=min_size, max_value=max_size))
    blocks = []
    prev = genesis_prev_hash()
    ts = FIXED_TS
    for i in range(length):
        ts += draw(st.integers(min_value=0, max_value=600))
        posts = tuple(draw(st.lists(st_post(ts=ts), min_size=1, max_size=3)))
        block = make_block(index=i, prev_hash=prev, timestamp=ts, txs=posts)
        blocks.append(block)
        prev = block.hash
    return blocks


@st.composite
def st_two_distinct_leaf_lists(draw):
    """서로 **다른** 두 리프 리스트.

    무작위 두 리스트만 뽑으면 CVE-2012-2459 반례를 거의 못 만난다.
    그래서 "마지막 리프를 복제한 목록"을 전략에 직접 넣는다 — 복제(duplicate) 방식
    구현이라면 여기서 반드시 충돌이 난다.
    """
    a = draw(st.lists(st.binary(min_size=1, max_size=4), min_size=1, max_size=9))
    mode = draw(
        st.sampled_from(
            ["dup_last", "dup_last", "dup_last", "dup_tail", "swap", "extend", "random"]
        )
    )
    if mode == "dup_last":
        b = a + [a[-1]]
    elif mode == "dup_tail":
        b = a + a[-2:]
    elif mode == "swap" and len(a) >= 2:
        i = draw(st.integers(min_value=0, max_value=len(a) - 2))
        b = list(a)
        b[i], b[i + 1] = b[i + 1], b[i]
    elif mode == "extend":
        b = a + draw(st.lists(st.binary(min_size=1, max_size=4), min_size=1, max_size=2))
    else:
        b = draw(st.lists(st.binary(min_size=1, max_size=4), min_size=1, max_size=9))
    if a == b:  # 같은 목록은 검사 대상이 아니다
        b = a + [b"\x00"]
    return a, b


# ══════════════════════════════════════════════════════════════════════════
# 4. 저장소 / CLI 어댑터와 픽스처
# ══════════════════════════════════════════════════════════════════════════
def storage_cls():
    __tracebackhide__ = True
    return require_attr(
        storage_jsonfile(),
        ("JsonFileStorage", "JSONFileStorage", "JsonStorage", "FileStorage"),
        lab="Lab 1.5 — 영속화와 검증 CLI",
        expects="class JsonFileStorage(path) — append_block/get_block/tip/iter_blocks/height",
    )


def make_storage(path):
    """JsonFileStorage(path) 를 만든다. 경로를 Path/str 어느 쪽으로 받아도 된다."""
    __tracebackhide__ = True
    cls = storage_cls()
    for build in (
        lambda: cls(path),
        lambda: cls(str(path)),
        lambda: cls(path=path),
        lambda: cls(path=str(path)),
    ):
        try:
            return build()
        except TypeError:
            continue
    raise MissingImplementation(
        _banner(
            module=f"{cls.__name__}(path)",
            lab="Lab 1.5 — 영속화와 검증 CLI",
            expects="생성자가 파일 경로 하나를 받아야 한다: JsonFileStorage(path)",
            cause="path 하나로는 생성할 수 없었다",
        )
    )


@pytest.fixture
def chain_path(tmp_path):
    """체인 파일 경로 (tmp_path/chain.json). 파일은 아직 없다."""
    return tmp_path / "chain.json"


@pytest.fixture
def storage(chain_path):
    """빈 JsonFileStorage."""
    return make_storage(chain_path)


@dataclasses.dataclass(frozen=True)
class CliResult:
    code: int
    out: str
    err: str

    def __str__(self) -> str:  # 실패 메시지용
        return f"exit={self.code}\n--- stdout ---\n{self.out}\n--- stderr ---\n{self.err}"


@pytest.fixture
def run_cli(capsys, monkeypatch, tmp_path):
    """`bbschain <args>` 를 **현재 프로세스 안에서** 실행한다.

    - 작업 디렉터리를 tmp_path 로 옮긴 뒤 부른다.
      → CLI 의 체인 파일 기본 경로는 **현재 디렉터리 기준 상대 경로**여야 한다 (예: ./chain.json).
    - `main(argv)` 와 `main()` 두 시그니처를 모두 지원한다.
      `main()` 형태면 `sys.argv` 를 세팅해 준다.
    - 종료 코드는 SystemExit 또는 main() 의 반환값에서 읽는다.
    """
    monkeypatch.chdir(tmp_path)

    def _run(*args: str, env: dict[str, str] | None = None) -> CliResult:
        main = require_attr(
            cli_module(),
            ("main",),
            lab="Lab 1.5 — 영속화와 검증 CLI",
            expects="main(argv=None) -> int | None  (post / dump / verify / tamper)",
        )
        if env is not None:
            for key in list(os.environ):
                if key not in env:
                    monkeypatch.delenv(key, raising=False)
            for key, value in env.items():
                monkeypatch.setenv(key, value)
        monkeypatch.setattr(sys, "argv", ["bbschain", *args])
        capsys.readouterr()  # 이전 출력 비우기
        code = 0
        try:
            params = [
                p
                for p in inspect.signature(main).parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ]
            rv = main(list(args)) if params else main()
            code = 0 if rv is None else int(rv)
        except SystemExit as exc:
            code = 0 if exc.code is None else int(exc.code)
        captured = capsys.readouterr()
        return CliResult(code=code, out=captured.out, err=captured.err)

    return _run


@pytest.fixture
def cli_chain_file(tmp_path):
    """CLI 가 만든 체인 파일을 찾아 준다 (이름/확장자를 고정하지 않는다)."""

    def _find():
        candidates = sorted(
            p
            for p in tmp_path.rglob("*")
            if p.is_file() and p.suffix in {".json", ".jsonl", ".ndjson", ".db"}
        )
        assert candidates, (
            f"CLI 를 실행했는데 {tmp_path} 아래에 체인 파일이 생기지 않았다.\n"
            "체인 파일 경로는 현재 작업 디렉터리 기준 상대 경로여야 한다 (예: ./chain.json)."
        )
        return candidates[0]

    return _find


def strip_gate_env() -> dict[str, str]:
    """tamper 게이트로 쓰일 법한 환경변수를 전부 제거한 환경."""
    return {
        k: v
        for k, v in os.environ.items()
        if not (
            "TAMPER" in k.upper()
            or "ADMIN" in k.upper()
            or k.upper().startswith("BBSCHAIN")
            or k.upper().startswith("BBS_")
        )
    }
