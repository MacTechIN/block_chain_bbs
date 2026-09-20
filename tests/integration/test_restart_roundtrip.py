"""Lab 1.5 — 재시작 왕복 (통합)

"프로세스가 죽으면 같이 사라지는 체인"을 파일에 붙들어 매는 것이 이 랩의 목적이다.
저장 → (재시작) → 복원 → `validate()` 까지 한 번에 본다.

Lab 1.5 §1 2번에서 본 실패가 여기서 초록이 되어야 한다:
    ValidationResult(ok=False, first_bad_index=1, reason='block hash mismatch')
    ← 저장하고 읽었을 뿐인데 체인이 깨졌다
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from conftest import (
    FIXED_TS,
    describe,
    make_block,
    make_chain_blocks,
    make_post,
    make_storage,
    st_chain,
    validate_blocks,
)
from hypothesis import given, settings


def test_restart_preserves_chain(tmp_path):
    """저장 → 재시작 → 복원된 체인이 **같고 유효하다**."""
    path = tmp_path / "chain.json"
    blocks = make_chain_blocks(10)

    writer = make_storage(path)
    for block in blocks:
        writer.append_block(block)
    del writer  # 프로세스 종료에 해당

    reader = make_storage(path)  # 재시작
    restored = list(reader.iter_blocks())

    assert reader.height() == len(blocks), (
        f"재시작 후 높이가 달라졌다: {reader.height()} != {len(blocks)}"
    )
    assert restored == blocks, (
        "재시작 후 복원된 블록이 저장한 블록과 다르다.\n"
        f"  저장: {blocks[1]!r}\n  복원: {restored[1]!r}\n"
        "→ tuple → list, int → float 왕복 실패를 먼저 의심하라 (Lab 1.5 §5)."
    )
    assert reader.tip() == blocks[-1], "재시작 후 tip() 이 마지막 블록이 아니다."

    result = validate_blocks(restored)
    assert result.ok, (
        f"아무도 변조하지 않았는데 복원된 체인이 파손 판정을 받았다. {describe(result)}\n"
        "→ 이것이 Lab 1.5 §1 의 2번 화면이다. **무엇이 왕복하지 않았는가?**"
    )


def test_restart_preserves_korean_bodies(tmp_path):
    """한글 본문도 그대로 돌아온다 (저장 포맷의 ensure_ascii 는 해시와 무관해야 한다)."""
    path = tmp_path / "chain.json"
    posts = (make_post(author="샘", body="첫 글 — 한글 본문 🙂", ts=FIXED_TS),)
    genesis = make_block(index=0, timestamp=FIXED_TS, txs=posts)

    writer = make_storage(path)
    writer.append_block(genesis)

    restored = next(iter(make_storage(path).iter_blocks()))
    assert restored == genesis, (
        f"한글/이모지 본문이 왕복하지 않았다.\n  저장: {genesis.txs[0]!r}\n  복원: {restored.txs[0]!r}"
    )
    assert restored.hash == genesis.hash, (
        "한글 본문 블록의 해시가 왕복 후 달라졌다.\n"
        "→ 해시는 저장된 **텍스트**가 아니라 복원된 **객체**에 대해 canonical_bytes 로 다시 계산한다 (ADR-0001)."
    )


@settings(max_examples=25)
@given(st_chain(min_size=1, max_size=5))
def test_restart_preserves_arbitrary_chains(blocks):
    """임의의 체인에 대해서도 재시작 왕복이 성립한다 (Phase 1 DoD 의 property 항목)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "chain.json"
        writer = make_storage(path)
        for block in blocks:
            writer.append_block(block)

        restored = list(make_storage(path).iter_blocks())
        assert restored == blocks, (
            f"길이 {len(blocks)} 체인의 재시작 왕복이 깨졌다.\n  저장: {blocks!r}\n  복원: {restored!r}"
        )
        result = validate_blocks(restored)
        assert result.ok, f"복원된 체인이 거부됐다. {describe(result)}"
