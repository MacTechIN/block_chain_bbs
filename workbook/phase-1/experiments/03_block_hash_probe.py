"""실험 3 — 내 블록은 무엇을 커밋하고 있나.

무엇을 보여주나:
    **네가 만든 `Block` 을 직접 불러다 찔러 본다.**
    (A) 필드를 하나씩 바꿔 보며 **어느 필드가 해시에 반영되는지** 표로 본다
    (B) 블록 세 개를 이어 붙이고, 맨 앞 블록을 고쳤을 때 뒤가 어떻게 되는지 본다
    빠진 필드가 있으면 그 줄이 "그대로" 로 찍힌다. **그 필드는 변조해도 안 잡힌다.**

    아직 구현이 없으면 친절하게 안내하고 끝난다. 먼저 돌려 봐도 손해가 없다.

실행 방법:
    uv run python workbook/phase-1/experiments/03_block_hash_probe.py

더 읽을 곳:
    docs/tutorial/phase-1.md — Lab 1.3 배경
    workbook/phase-1/lab-1.3.md — 따라하기 시트
    workbook/phase-1/lab-1.4.md — txs 를 해시 입력에서 빼는 이유

🔴 이 스크립트는 관찰 도구다. 머클 루트도 정규 직렬화도 여기서 계산하지 않는다.
   랩 과제의 답이 한 줄도 들어 있지 않다.
"""

from __future__ import annotations

import dataclasses
from typing import Any

HEADER_FIELDS = ("index", "prev_hash", "timestamp", "merkle_root", "nonce", "difficulty")

# 이 실험은 머클 루트를 계산하지 않는다. 헤더 칸에 들어간 값이 무엇이든
# **해시가 그 값에 반응하는지**만 보면 되기 때문이다.
PLACEHOLDER_ROOT = "7" * 64
FIXED_TS = 1_700_000_000


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def advice(lines: list[str]) -> int:
    print()
    print("━" * 78)
    print(" 아직 여기까지 못 왔다 (이 시점에서는 정상이다)")
    print("━" * 78)
    for line in lines:
        print(f" {line}")
    print("━" * 78)
    return 0


def load_block_module() -> Any:
    try:
        import bbschain.core.block as mod
    except ImportError as exc:
        advice(
            [
                f"원인 : {type(exc).__name__}: {exc}",
                "",
                "src/bbschain/core/block.py 가 아직 없다.",
                "Lab 1.3 과제 (3)번을 만들면 이 실험이 돌아간다.",
                "",
                "시작 파일 복사:",
                "  mkdir -p src/bbschain/core && touch src/bbschain/core/__init__.py",
                "  cp workbook/phase-1/starter/core/block.py src/bbschain/core/block.py",
                "",
                "따라하기 시트: workbook/phase-1/lab-1.3.md",
            ]
        )
        return None
    return mod


def make_post(post_cls: Any, body: str, ts: int) -> Any:
    return post_cls(author="sam", body=body, ts=ts)


def make_block(block_cls: Any, post_cls: Any, index: int, prev_hash: str, body: str) -> Any:
    return block_cls(
        index=index,
        prev_hash=prev_hash,
        timestamp=FIXED_TS + index * 60,
        merkle_root=PLACEHOLDER_ROOT,
        nonce=0,
        difficulty=0,
        txs=(make_post(post_cls, body, FIXED_TS + index * 60),),
    )


def probe_fields(block_cls: Any, post_cls: Any, base: Any, base_hash: str) -> None:
    mutations: dict[str, Any] = {
        "index": base.index + 1,
        "prev_hash": "c" * 64,
        "timestamp": base.timestamp + 1,
        "merkle_root": "d" * 64,
        "nonce": base.nonce + 1,
        "difficulty": base.difficulty + 1,
    }
    print("    필드            바꾼 뒤 해시가        뜻")
    print("    " + "-" * 62)
    for field in HEADER_FIELDS:
        changed = dataclasses.replace(base, **{field: mutations[field]})
        moved = changed.hash != base_hash
        verdict = "바뀐다  ✅" if moved else "그대로  🔴"
        note = "해시 입력에 들어 있다" if moved else "해시 입력에서 빠졌다 — 변조해도 안 잡힌다"
        print(f"    {field:<14}  {verdict}          {note}")

    tampered_posts = (dataclasses.replace(base.txs[0], body="sam이 회사 돈을 횡령했다"),)
    tampered = dataclasses.replace(base, txs=tampered_posts)
    moved = tampered.hash != base_hash
    print(f"    {'txs (글 본문)':<12}  {'바뀐다' if moved else '그대로'}")
    print()
    if moved:
        print("👀 볼 것: 헤더 6줄이 전부 ✅ 이고, 글 본문을 고쳐도 해시가 바뀐다.")
        print("   → **Lab 1.3 을 끝낸 상태다.** 해시 입력에 7개 필드가 전부 들어가 있다.")
        print("   Lab 1.4 에서 txs 를 입력에서 빼면 이 마지막 줄이 '그대로' 로 바뀐다.")
        print("   그때는 그게 정상이다 — 글을 커밋하는 경로가 merkle_root 로 옮겨 간다.")
    else:
        print("👀 볼 것: 헤더 6줄은 ✅ 인데 글 본문을 고쳐도 해시가 그대로다.")
        print("   → **Lab 1.4 의 교체를 끝낸 상태다.** 해시 입력은 헤더 6개 필드뿐이다.")
        print("   글은 merkle_root 를 통해서만 커밋된다. 그래서 merkle_root 를 고치면 해시가 바뀐다.")
        print("   🔴 그리고 그것 때문에 validate() 가 merkle_root 를 txs 로부터")
        print("      **재계산해 대조**해야 한다. 안 하면 본문 변조가 아무 데서도 안 잡힌다.")
    if any(
        dataclasses.replace(base, **{f: mutations[f]}).hash == base_hash for f in HEADER_FIELDS
    ):
        print()
        print("🔴 '그대로' 로 찍힌 헤더 필드가 있다. 그 필드는 지금 아무도 지키지 않는다.")
        print("   해시 입력 payload 에 헤더 6개가 전부 들어갔는지 확인하라 (Lab 1.3 §3(3)).")


def show_propagation(block_cls: Any, post_cls: Any, genesis_prev: str) -> None:
    def build(bodies: list[str]) -> list[Any]:
        blocks: list[Any] = []
        prev = genesis_prev
        for i, body in enumerate(bodies):
            block = make_block(block_cls, post_cls, i, prev, body)
            blocks.append(block)
            prev = block.hash
        return blocks

    bodies = ["첫 글", "두 번째 글", "세 번째 글"]
    good = build(bodies)
    print("    정상 체인 — 각 블록의 prev_hash 는 앞 블록의 해시다")
    for block in good:
        print(f"      #{block.index}  prev={block.prev_hash[:12]}…  hash={block.hash[:12]}…")

    print()
    print("    이제 #0 의 timestamp 를 1초만 바꾼다. 뒤 블록은 손대지 않는다.")
    broken = [dataclasses.replace(good[0], timestamp=good[0].timestamp + 1), *good[1:]]
    broken_at: int | None = None
    for i, block in enumerate(broken):
        if i == 0:
            print(f"      #0  hash={block.hash[:12]}…   (바뀌었다)")
            continue
        links = block.prev_hash == broken[i - 1].hash
        if not links and broken_at is None:
            broken_at = i
        if not links:
            mark = "🔴 끊겼다"
        elif broken_at is not None:
            mark = f"연결은 맞다 — 그러나 깨진 #{broken_at} 뒤라 무효다"
        else:
            mark = "이어진다"
        print(
            f"      #{i}  prev={block.prev_hash[:12]}…  "
            f"vs  앞 블록 hash={broken[i - 1].hash[:12]}…  {mark}"
        )
    print()
    print("👀 볼 것: **#0 하나를 고쳤는데 #1 의 연결이 끊긴다.**")
    print("   #2 는 #1 과 잘 이어져 있지만, 그 #1 이 유효한 조상에서 도달할 수 없다.")
    print("   그래서 #1 뒤가 통째로 무효다 — '깨진 블록만 무효'가 아니다.")
    print("   #1 을 고쳐 다시 이으면 #2 가 끊긴다. #2 를 고치면 그다음이 끊긴다.")
    print("   중간 하나를 통과시키려면 **끝까지 전부 다시 계산**해야 한다는 뜻이다.")
    print("   지금은 그 재계산이 공짜다. 비용을 붙이는 것이 Phase 4 다.")


def main() -> int:
    mod = load_block_module()
    if mod is None:
        return 0

    block_cls = getattr(mod, "Block", None)
    post_cls = getattr(mod, "Post", None)
    if block_cls is None or post_cls is None:
        return advice(
            [
                "block.py 는 있는데 Post 또는 Block 클래스가 없다.",
                "랩이 준 필드 집합 그대로 선언하라 (Lab 1.3 §3(3)).",
                "",
                "따라하기 시트: workbook/phase-1/lab-1.3.md",
            ]
        )

    try:
        base = make_block(block_cls, post_cls, 3, "b" * 64, "오늘 점심 뭐 먹지")
    except TypeError as exc:
        return advice(
            [
                f"원인 : TypeError: {exc}",
                "",
                "Block 또는 Post 의 필드 이름·개수가 계약과 다르다.",
                "  Block(index, prev_hash, timestamp, merkle_root, nonce, difficulty, txs)",
                "  Post(author, body, ts, nonce=0, sig=None)",
                "",
                "확인: uv run pytest tests/unit/test_block.py -k field_names -v",
            ]
        )

    try:
        base_hash = base.hash
    except NotImplementedError:
        return advice(
            [
                "Block.hash 가 아직 NotImplementedError 를 던진다.",
                "시작 파일은 복사했고 본문을 아직 안 채운 상태다. **정상이다.**",
                "",
                "채우고 나서 다시 돌려라. 그때 이 실험이 무엇을 보여주는지 알 수 있다.",
                "  uv run pytest tests/unit/test_block.py -v",
                "",
                "따라하기 시트: workbook/phase-1/lab-1.3.md",
            ]
        )

    banner("(A) 어느 필드가 해시에 반영되나")
    print(f"    기준 블록 #{base.index}")
    print(f"      hash = {base_hash}")
    print(f"      (merkle_root 는 이 실험이 넣은 자리표시 값 {PLACEHOLDER_ROOT[:8]}… 이다)")
    print()
    probe_fields(block_cls, post_cls, base, base_hash)

    banner("(B) 하나를 고치면 뒤가 어떻게 되나")
    genesis_prev = "0" * 64
    for dotted, names in (
        ("bbschain.core.chain", ("GENESIS_PREV", "GENESIS_PREV_HASH", "ZERO_HASH")),
        ("bbschain.core.block", ("GENESIS_PREV", "GENESIS_PREV_HASH", "ZERO_HASH")),
    ):
        try:
            found = __import__(dotted, fromlist=["*"])
        except ImportError:
            continue
        for name in names:
            value = getattr(found, name, None)
            if isinstance(value, str) and value:
                genesis_prev = value
                print(f"    제네시스 상수는 {dotted}.{name} 에서 가져왔다.")
                break
    show_propagation(block_cls, post_cls, genesis_prev)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
