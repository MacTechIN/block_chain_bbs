"""Lab 1.5 — 저장소 (`storage/base.py`, `storage/jsonfile.py`)

계약 (개발계획서 6절 고정 계약 4번)
    class Storage(Protocol):
        append_block(block) -> None
        get_block(key: str | int) -> Block | None     # 해시와 인덱스를 **둘 다** 받는다
        tip() -> Block | None
        iter_blocks(start=0, end=None) -> Iterator[Block]
        height() -> int

**수정·삭제 메서드가 없다는 것 자체가 설계다.** append-only.
"""

from __future__ import annotations

import ast
import builtins
import inspect
import io
import json

import pytest
from conftest import (
    make_chain_blocks,
    make_storage,
    storage_base,
    storage_cls,
)

REQUIRED_METHODS = ("append_block", "get_block", "tip", "iter_blocks", "height")

FORBIDDEN_METHODS = (
    "update",
    "update_block",
    "set_block",
    "put_block",
    "replace_block",
    "overwrite_block",
    "rewrite",
    "edit",
    "edit_block",
    "modify",
    "modify_block",
    "delete",
    "delete_block",
    "remove",
    "remove_block",
    "pop",
    "pop_block",
    "insert",
    "insert_block",
    "truncate",
    "clear",
    "drop",
    "__setitem__",
    "__delitem__",
)


def test_append_and_read_back(storage):
    """저장했다 읽으면 **완전히 동일한 블록**이 돌아온다 (모든 필드의 타입까지)."""
    blocks = make_chain_blocks(5)
    for block in blocks:
        storage.append_block(block)

    assert storage.height() == len(blocks), (
        f"블록 {len(blocks)} 개를 넣었는데 height()={storage.height()} 다."
    )

    read_back = list(storage.iter_blocks())
    assert read_back == blocks, (
        "읽어 온 블록이 넣은 블록과 다르다.\n"
        f"  넣은 것 : {blocks[0]!r}\n  읽은 것 : {read_back[0]!r}\n"
        "→ 흔한 원인: txs 가 list 로 복원됐다 / ts 가 float 이 됐다 (Lab 1.5 §5)."
    )
    for i, block in enumerate(read_back):
        assert isinstance(block.txs, tuple), (
            f"블록 {i} 의 txs 가 {type(block.txs).__name__} 로 복원됐다. tuple 이어야 한다."
        )
        assert all(isinstance(p.ts, int) and not isinstance(p.ts, bool) for p in block.txs), (
            f"블록 {i} 의 Post.ts 가 int 가 아니다: {[type(p.ts).__name__ for p in block.txs]}"
        )
        assert block.hash == blocks[i].hash, (
            f"블록 {i} 의 해시가 왕복 후 달라졌다. 이 상태로는 아무도 변조하지 않았는데 "
            "validate() 가 파손을 보고한다."
        )

    assert storage.tip() == blocks[-1], f"tip() 이 마지막 블록이 아니다: {storage.tip()!r}"
    assert list(storage.iter_blocks(start=2)) == blocks[2:], (
        "iter_blocks(start=2) 가 2번 블록부터 돌려주지 않았다."
    )


def test_empty_storage_is_empty(storage, chain_path):
    """파일이 없으면 빈 체인에서 시작한다 (예외를 던지지 않는다)."""
    assert not chain_path.exists(), "테스트 시작 시점에는 체인 파일이 없어야 한다."
    assert storage.height() == 0, f"빈 저장소의 height() 는 0 이다. 실제: {storage.height()}"
    assert storage.tip() is None, f"빈 저장소의 tip() 은 None 이다. 실제: {storage.tip()!r}"
    assert list(storage.iter_blocks()) == [], "빈 저장소의 iter_blocks() 는 비어 있어야 한다."


def test_get_block_by_hash_and_index(storage):
    """`get_block` 은 해시 문자열과 정수 인덱스를 **둘 다** 받는다 (탐색기가 둘 다 쓴다)."""
    blocks = make_chain_blocks(4)
    for block in blocks:
        storage.append_block(block)

    for i, block in enumerate(blocks):
        assert storage.get_block(i) == block, f"get_block({i}) 가 {i} 번 블록을 돌려주지 않았다."
        assert storage.get_block(block.hash) == block, (
            f"get_block({block.hash[:12]}...) 가 해시로 조회되지 않았다."
        )

    assert storage.get_block(999) is None, "없는 인덱스는 None 이어야 한다 (예외가 아니라)."
    assert storage.get_block("f" * 64) is None, "없는 해시는 None 이어야 한다 (예외가 아니라)."


def test_storage_has_no_mutation_method():
    """인터페이스에 수정·삭제가 **없다**는 것을 강제한다.

    "정상 경로로는 과거를 바꿀 수 없다"가 설계다. `/admin/tamper` 와 `cli tamper` 는
    이 인터페이스를 **우회해서** 파일을 직접 건드린다 (Lab 1.5 §3).
    """
    protocol = getattr(storage_base(), "Storage", None)
    assert protocol is not None, (
        "bbschain.storage.base 에 Storage 프로토콜이 없다.\n"
        "→ Phase 2 의 SQLite 전환이 코어를 한 줄도 안 건드리게 하려면 인터페이스를 지금 선언해야 한다."
    )

    for name in REQUIRED_METHODS:
        assert hasattr(protocol, name), f"Storage 프로토콜에 {name}() 이 없다."

    for target, label in ((protocol, "Storage 프로토콜"), (storage_cls(), "JsonFileStorage")):
        public = {n for n in dir(target) if not n.startswith("_")} | {"__setitem__", "__delitem__"}
        for name in FORBIDDEN_METHODS:
            if name in ("__setitem__", "__delitem__"):
                assert name not in vars(target), (
                    f"{label} 에 {name} 이 있다. 저장소는 append-only 다 — 항목을 덮어쓸 수 있으면 안 된다."
                )
                continue
            assert name not in public, (
                f"{label} 에 {name}() 이 있다. **append_block 말고 과거를 바꾸는 메서드는 만들지 않는다.**\n"
                "→ tamper 는 이 인터페이스를 쓰지 않고 파일을 직접 건드린다 (Lab 1.5 §5 표 마지막 줄)."
            )


def test_chain_does_not_import_the_json_implementation():
    """`Chain` 은 `Storage` 타입에만 의존한다. `JsonFileStorage` 를 직접 import 하면 실패다."""
    from conftest import MissingImplementation, core_chain

    try:
        source = inspect.getsource(core_chain())
    except (MissingImplementation, OSError):  # pragma: no cover
        pytest.skip("core/chain.py 소스를 읽을 수 없다")

    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported += [f"{node.module or ''}.{a.name}" for a in node.names]

    leaks = [name for name in imported if "jsonfile" in name or "JsonFileStorage" in name]
    assert not leaks, (
        f"core/chain.py 가 구체 저장소 구현을 직접 import 한다: {leaks}\n"
        "→ Phase 2 에서 SQLite 로 갈아끼울 때 코어를 고쳐야 한다. Storage 프로토콜에만 의존하라."
    )


def test_atomic_write_survives_interruption(chain_path, monkeypatch):
    """쓰기 도중에 죽어도 파일이 **읽을 수 없는 상태가 되지 않는다.**

    Lab 1.5 §1 의 3~4번(대용량 저장 중 Ctrl+C → JSONDecodeError → 체인 전체 상실)을
    재현한다. 임시 파일에 쓰고 `os.replace` 로 바꾸면 원본은 절대 반쯤 쓰인 상태가 되지 않는다.
    """
    storage = make_storage(chain_path)
    blocks = make_chain_blocks(4)
    for block in blocks:
        storage.append_block(block)

    assert chain_path.exists(), (
        f"append_block 후에도 {chain_path} 가 없다. 저장소는 생성자가 받은 경로에 써야 한다."
    )
    before = chain_path.read_bytes()

    # ── 쓰기 도중 프로세스가 죽는 상황을 만든다 ────────────────────────────
    real_open = builtins.open
    directory = str(chain_path.parent)

    class _DyingFile:
        """몇 바이트 쓰고 나면 죽는 파일 객체 (디스크 풀 / 강제 종료 흉내)."""

        def __init__(self, wrapped):
            self._wrapped = wrapped
            self._written = 0

        def write(self, data):
            self._written += len(data)
            if self._written > 32:
                raise OSError(28, "simulated crash while writing")
            return self._wrapped.write(data)

        def writelines(self, lines):
            for line in lines:
                self.write(line)

        def __enter__(self):
            self._wrapped.__enter__()
            return self

        def __exit__(self, *exc):
            return self._wrapped.__exit__(*exc)

        def __getattr__(self, name):
            return getattr(self._wrapped, name)

    def dying_open(file, mode="r", *args, **kwargs):
        handle = real_open(file, mode, *args, **kwargs)
        if str(file).startswith(directory) and any(m in mode for m in ("w", "a", "+", "x")):
            return _DyingFile(handle)
        return handle

    monkeypatch.setattr(builtins, "open", dying_open)
    monkeypatch.setattr(io, "open", dying_open)

    with pytest.raises(OSError):
        storage.append_block(make_chain_blocks(5)[4])

    monkeypatch.undo()

    # ── 죽은 뒤 다시 켠다 ────────────────────────────────────────────────
    raw = chain_path.read_bytes()
    try:
        json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        # JSON Lines 라면 줄 단위로 확인한다
        for line in raw.decode("utf-8", errors="replace").splitlines():
            if line.strip():
                json.loads(line)

    restarted = make_storage(chain_path)
    survivors = list(restarted.iter_blocks())
    assert survivors[: len(blocks)] == blocks, (
        "쓰기 도중 죽은 뒤 이미 저장돼 있던 블록이 손상됐다.\n"
        f"  죽기 전 파일 크기: {len(before)} bytes\n  죽은 뒤: {len(raw)} bytes\n"
        "→ 같은 디렉터리의 임시 파일에 쓴 다음 os.replace 로 바꿔라 (이름 바꾸기는 원자적이다)."
    )

    # 죽은 뒤에도 저장소는 계속 쓸 수 있어야 한다.
    next_block = make_chain_blocks(len(survivors) + 1)[-1]
    restarted.append_block(next_block)
    assert list(restarted.iter_blocks())[-1] == next_block, (
        "중단 이후 append_block 이 정상 동작하지 않는다 (임시 파일이 남아 경로를 막고 있을 수 있다)."
    )
