"""실험 1 — 해시는 얼마나 민감한가.

무엇을 보여주나:
    (A) 같은 입력을 1000번 해시하면 결과가 하나뿐이다        — 결정성
    (B) 한 글자만 바꾸면 출력 256비트 중 **절반쯤이 뒤집힌다** — 눈사태 효과
    (C) 입력 길이가 1바이트든 1MB든 출력은 언제나 64자다
    (D) 앞자리 몇 글자만 맞는 값을 찾는 데 시도가 몇 번 드는지 직접 센다
    한 번에 몇 비트가 뒤집혔는지 **숫자로** 센다. 말로만 듣는 것과 다르다.

실행 방법:
    uv run python workbook/phase-1/experiments/01_hash_avalanche.py

더 읽을 곳:
    docs/tutorial/phase-1.md — Lab 1.1 배경
    workbook/phase-1/lab-1.1.md — 따라하기 시트

🔴 이 스크립트에는 bbschain 구현이 한 줄도 없다. 랩 과제의 답이 아니다.
"""

from __future__ import annotations

import hashlib

SAMPLE = "오늘 점심 뭐 먹지"


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bits(hex_digest: str) -> str:
    """64자 hex 를 256자 비트 문자열로."""
    return bin(int(hex_digest, 16))[2:].zfill(256)


def flipped(a: str, b: str) -> int:
    """두 해시에서 서로 다른 비트의 개수."""
    return sum(x != y for x, y in zip(bits(a), bits(b), strict=True))


def main() -> int:
    banner("(A) 같은 입력을 1000번 해시한다")
    seen = {sha(SAMPLE) for _ in range(1000)}
    print(f"    입력      : {SAMPLE!r}")
    print(f"    서로 다른 결과의 개수 : {len(seen)}")
    print(f"    그 값     : {seen.pop()}")
    print()
    print("👀 볼 것: 1000번을 돌렸는데 결과는 **한 종류**다.")
    print("   해시에는 난수도 시각도 안 섞인다. 같은 바이트열이면 언제 어디서나 같은 값이다.")
    print("   이것이 없으면 '내 블록의 지문'이라는 말 자체가 성립하지 않는다.")

    banner("(B) 한 글자만 바꾼다 — 몇 비트가 뒤집히나")
    base = sha(SAMPLE)
    variants = [
        (f"{SAMPLE} ", "끝에 공백 하나"),
        (SAMPLE.replace("점심", "저녁"), "두 글자 교체"),
        (SAMPLE + ".", "마침표 하나"),
        (SAMPLE.upper(), "대문자로 (한글은 안 바뀐다)"),
    ]
    print(f"    기준 : {SAMPLE!r}")
    print(f"           {base}")
    print()
    for text, label in variants:
        other = sha(text)
        if other == base:
            print(f"      (변화 없음)   {label}")
            continue
        n = flipped(base, other)
        print(f"      {n:>3}/256 비트 뒤집힘 ({n / 256:.0%})   {label}")
        print(f"                {other}")
    print()
    print("👀 볼 것: 입력을 아주 조금 바꿨는데 **절반 가까운 비트가 뒤집힌다.**")
    print("   '조금 바꾸면 조금 달라진다'가 아니다. 완전히 다른 값이 된다.")
    print("   그래서 해시 두 개를 볼 때 앞 몇 글자만 비교해도 다름을 알 수 있다.")

    banner("(C) 입력이 아무리 길어도 출력은 64자")
    for size, label in [(1, "1바이트"), (1_000, "1KB"), (1_000_000, "1MB")]:
        digest = hashlib.sha256(b"a" * size).hexdigest()
        print(f"    {label:<8} -> {digest}  (길이 {len(digest)})")
    print()
    print("👀 볼 것: 입력 길이가 백만 배 차이 나는데 출력 길이는 같다.")
    print("   블록에 글이 몇 개든 지문은 64자 하나라는 뜻이다.")
    print("   대신 '입력은 무한, 출력은 유한'이므로 같은 값을 내는 입력 쌍은 반드시 존재한다.")
    print("   존재하는 것과 찾을 수 있는 것은 다른 이야기다. 다음 실험이 그 감각이다.")

    banner("(D) 앞자리가 0 인 해시는 얼마나 드문가")
    trials = 200_000
    print(f"    'sam의 글 #<숫자>' 의 숫자를 1부터 {trials:,} 까지 바꿔 가며 해시한다.")
    print("    그중 앞자리가 0 으로 시작하는 것이 몇 개인지 센다.")
    print("    Phase 4 의 채굴이 정확히 이 짓이다. (여기서는 아주 쉬운 난이도만 본다)")
    print()
    counts = dict.fromkeys(range(1, 6), 0)
    for i in range(1, trials + 1):
        digest = sha(f"sam의 글 #{i}")
        for zeros in range(1, 6):
            if digest.startswith("0" * zeros):
                counts[zeros] += 1
            else:
                break
    print("    앞자리       찾은 개수      평균 몇 번에 하나")
    print("    " + "-" * 48)
    for zeros, hits in counts.items():
        rate = f"{trials / hits:>12,.0f}번" if hits else "            —"
        print(f"    {'0' * zeros:<10} {hits:>8,}개   {rate}")
    print()
    print("👀 볼 것: 0 이 하나 늘 때마다 '평균 몇 번에 하나'가 대략 **16배**로 뛴다.")
    print("   hex 한 자리는 16가지이기 때문이다.")
    print("   앞자리를 원하는 값으로 맞추는 지름길이 없다 — 전부 해 보는 수밖에 없다.")
    print("   '해시는 되돌릴 수 없다'는 말의 실물이 이 표다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
