"""실험 2 — 같은 데이터, 다른 바이트열.

무엇을 보여주나:
    (A) 논리적으로 같은 글 하나가 **몇 가지 바이트열**이 될 수 있는지 세어 본다
    (B) 무엇을 고정하면 그 가짓수가 1이 되는지 하나씩 켜 본다
    (C) 그래도 안 잡히는 것 — JSON 왕복에서 조용히 바뀌는 타입들
    해시 함수는 결백하다. 문제는 해시에 **넣기 전에** 만들어진 바이트열이다.

실행 방법:
    uv run python workbook/phase-1/experiments/02_json_bytes.py

더 읽을 곳:
    docs/tutorial/phase-1.md — Lab 1.1 배경, Lab 1.5 배경
    docs/decisions/ADR-0001-canonical-serialization.md
    workbook/phase-1/lab-1.1.md — 따라하기 시트

🔴 이 스크립트에는 bbschain 구현이 한 줄도 없다. canonical_bytes 의 답도 아니다.
   무엇을 고정해야 하는지를 **보여줄 뿐** 고정하는 코드는 네가 쓴다.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

# 논리적으로 **완전히 같은 글** 하나를, 사람이 쓸 법한 여러 방식으로 만든 것
SAME_POST: list[tuple[str, dict[str, Any]]] = [
    ("키 순서 A", {"author": "sam", "body": "오늘 점심", "ts": 1700000000}),
    ("키 순서 B", {"ts": 1700000000, "body": "오늘 점심", "author": "sam"}),
    ("키 순서 C", {"body": "오늘 점심", "author": "sam", "ts": 1700000000}),
]


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    banner("(A) 같은 글 하나가 몇 가지 바이트열이 되나")
    made: dict[bytes, str] = {}
    rows: list[tuple[str, bytes]] = []
    for label, post in SAME_POST:
        rows.append((f"{label} · dumps 기본", json.dumps(post).encode("utf-8")))
        rows.append((f"{label} · indent=2", json.dumps(post, indent=2).encode("utf-8")))
        rows.append(
            (
                f"{label} · ensure_ascii=False",
                json.dumps(post, ensure_ascii=False).encode("utf-8"),
            )
        )
        rows.append((f"{label} · UTF-16", json.dumps(post).encode("utf-16")))

    for label, data in rows:
        made.setdefault(data, label)
        print(f"    {digest(data)[:16]}…  {len(data):>4}바이트  {label}")
    print()
    print(f"👀 볼 것: 같은 글 하나인데 서로 다른 바이트열이 **{len(made)}가지** 나왔다.")
    print("   바이트열이 다르면 해시가 다르다. 해시가 다르면 다른 글로 취급된다.")
    print("   내 노드는 A 방식으로, 네 노드는 B 방식으로 직렬화하면")
    print("   같은 글을 두고 두 노드가 영원히 합의하지 못한다.")

    banner("(B) 무엇을 고정하면 가짓수가 1이 되나")
    knobs = [
        ("아무것도 안 고정", {}),
        ("키 정렬만", {"sort_keys": True}),
        ("키 정렬 + 구분자", {"sort_keys": True, "separators": (",", ":")}),
        (
            "키 정렬 + 구분자 + 비ASCII 처리",
            {"sort_keys": True, "separators": (",", ":"), "ensure_ascii": False},
        ),
    ]
    for label, kwargs in knobs:
        variants = {json.dumps(post, **kwargs).encode("utf-8") for _, post in SAME_POST}
        verdict = "✅ 하나로 모였다" if len(variants) == 1 else "❌ 아직 여러 개다"
        print(f"    {len(variants)}가지  {verdict}   {label}")
    print()
    print("👀 볼 것: **키 정렬 하나만으로도** 위 세 글은 같은 바이트열이 된다.")
    print("   구분자와 비ASCII 처리는 이 예에서는 결과를 안 바꾼다.")
    print("   그래도 고정해야 한다 — 파이썬 버전이나 다른 언어의 JSON 구현이")
    print("   기본값을 다르게 쓰면 그때 갈린다. **기본값에 기대지 않는 것**이 규칙의 요점이다.")
    print()
    print("   여기 안 나온 것이 하나 더 있다: **인코딩**.")
    print("   같은 문자열이라도 UTF-8 과 UTF-16 은 다른 바이트열이다. (A)의 마지막 줄들이 그것이다.")

    banner("(C) 고정해도 안 잡히는 것 — 타입이 조용히 바뀐다")
    cases: list[tuple[str, Any]] = [
        ("tuple 이 list 가 된다", {"txs": ("a", "b")}),
        ("int 키가 문자열이 된다", {1: "a"}),
        ("왕복은 되는데 — 정수 1", {"ts": 1}),
        ("…같은 값의 실수 1.0 은 다른 JSON 문자열이다", {"ts": 1.0}),
    ]
    for label, obj in cases:
        text = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        back = json.loads(text)
        same = "왕복 OK" if back == obj else "🔴 왕복 실패"
        print(f"    {text:<24} -> {back!r:<24} {same}   {label}")
    print()
    print("    직렬화 자체가 안 되는 값도 있다:")
    for label, value in [("set", {1, 2}), ("datetime", dt.datetime(2023, 11, 14))]:  # noqa: DTZ001
        try:
            json.dumps({"x": value})
        except TypeError as exc:
            print(f"        {label:<10} -> TypeError: {exc}")
    print()
    print("👀 볼 것: 앞의 둘은 **경고도 예외도 없이** 타입이 바뀐다.")
    print("   tuple 로 넣었는데 list 로 돌아오면, 저장했다 읽은 것만으로 해시가 달라진다.")
    print("   아무도 변조하지 않았는데 체인이 깨졌다고 나오는 사고가 이것이다 (Lab 1.5).")
    print("   반대로 set 과 datetime 은 예외가 난다 — 이쪽이 오히려 안전하다.")
    print("   모르는 타입을 만나면 **조용히 문자열로 바꾸지 말고 예외를 던져야 하는** 이유다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
