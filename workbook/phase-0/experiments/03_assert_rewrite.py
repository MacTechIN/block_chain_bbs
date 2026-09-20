"""실험 3 — 같은 `assert` 한 줄인데 왜 출력이 다른가.

무엇을 보여주나:
    pytest 는 실패한 `assert` 의 양쪽 값을 펼쳐서 보여 준다.
    그 친절한 출력이 **어디서 나오고 어디서 사라지는지**를 네 조건으로 비교한다.
      (A) pytest 기본             — 값을 펼쳐 준다
      (B) pytest --assert=plain   — 같은 pytest 인데 안 펼쳐 준다
      (C) 그냥 python -c          — pytest 가 없을 때
      (D) 테스트가 불러 쓴 일반 모듈 안의 assert — 여기서도 안 펼쳐진다
    **네 조건의 assert 문은 글자까지 똑같다.**
    마지막으로 그 출력을 만드는 캐시 파일 이름에 pytest 버전이 박히는 것까지 본다.

실행 방법:
    uv run python workbook/phase-0/experiments/03_assert_rewrite.py

더 읽을 곳:
    docs/tutorial/phase-0.md — Lab 0.1 질문 2 (AssertionError 와 assertion rewriting)
    workbook/테스트-실행법.md — 실패 메시지 읽는 순서
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

LEFT = '{"a": 1, "b": 2, "c": 3}'
RIGHT = '{"a": 1, "b": 99, "c": 3}'

HELPER_SOURCE = f'''\
def check_same(left, right):
    """평범한 모듈 안의 assert. pytest 의 재작성 대상이 아니다."""
    assert left == right


EXPECTED = {RIGHT}
'''

TEST_SOURCE = f'''\
import assert_helper


def test_assert_written_in_the_test_file():
    assert {LEFT} == {RIGHT}


def test_assert_delegated_to_a_helper_module():
    assert_helper.check_same({LEFT}, assert_helper.EXPECTED)
'''


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def run_pytest(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout + result.stderr).rstrip()


def failure_block(output: str) -> str:
    """FAILURES 구획만 잘라 낸다 — 헤더·플러그인 목록은 이 실험의 관심사가 아니다."""
    lines = output.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if "FAILURES" in line)
    except StopIteration:
        return output
    try:
        end = next(i for i, line in enumerate(lines) if "short test summary" in line)
    except StopIteration:
        end = len(lines)
    return "\n".join(lines[start:end]).rstrip()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bbschain-exp03-") as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "assert_helper.py").write_text(HELPER_SOURCE, encoding="utf-8")
        (tmpdir / "test_assert_demo.py").write_text(TEST_SOURCE, encoding="utf-8")

        print("이 실험이 실패시키는 단언은 네 조건 모두 같다:")
        print(f"    assert {LEFT} == {RIGHT}")

        banner("(A) pytest 기본 — assertion rewriting 켜짐")
        default_run = run_pytest(["test_assert_demo.py"], cwd=tmpdir)
        print(failure_block(default_run))
        print()
        print("👀 볼 것: 두 테스트의 출력이 **서로 다르다.**")
        print("   앞 것은 어느 키가 어떻게 다른지까지 펼쳐 준다.")
        print("   뒤 것은 helper 모듈 안에서 실패했고, 설명이 거의 없다.")
        print("   → (D) 에서 이 차이를 다시 짚는다.")

        banner("(B) pytest --assert=plain — 같은 pytest, 재작성만 끔")
        plain_run = run_pytest(["--assert=plain", "test_assert_demo.py"], cwd=tmpdir)
        print(failure_block(plain_run))
        print()
        print("👀 볼 것: (A)의 첫 테스트에 있던 diff 가 통째로 사라지고 `AssertionError` 한 줄만 남는다.")
        print("   테스트 코드는 한 글자도 안 바뀌었다. 바뀐 것은 **import 시점의 AST 재작성 여부**뿐이다.")

        banner("(C) pytest 없이 순수 파이썬으로 같은 단언")
        bare = subprocess.run(
            [sys.executable, "-c", f"assert {LEFT} == {RIGHT}"],
            capture_output=True,
            text=True,
            check=False,
        )
        print((bare.stdout + bare.stderr).rstrip())
        print(f"    종료 코드: {bare.returncode}")
        print()
        print("👀 볼 것: 파이썬이 던지는 것은 그냥 `AssertionError` 다.")
        print("   pytest 전용 예외 같은 건 없다. (B)의 출력과 내용이 사실상 같다.")
        print("   pytest 가 더 해 주는 일은 예외를 잡는 것이 아니다.")
        print("   **실패하기 전에 양쪽 값을 미리 담아 두는 것**이다.")

        banner("(D) 재작성의 경계 — 테스트가 import 한 일반 모듈")
        print("   (A) 의 두 번째 테스트가 그 경우였다. 다시 그 부분만 본다.")
        print()
        lines = failure_block(default_run).splitlines()
        marker = next(
            (i for i, line in enumerate(lines) if "test_assert_delegated" in line),
            0,
        )
        print("\n".join(lines[marker:]).rstrip())
        print()
        print("👀 볼 것: 같은 실행인데 helper 안의 assert 는 설명이 붙지 않는다.")
        print("   pytest 가 손보는 대상은 **테스트 파일 · conftest.py · 등록된 플러그인**뿐이다.")
        print("   검사를 헬퍼 함수로 빼는 순간 실패 메시지가 가난해진다.")
        print("   → 실용적 결론: **assert 는 테스트 파일 안에 두는 편이 낫다.**")
        print("   꼭 빼야 하면 `pytest.register_assert_rewrite('모듈명')` 으로 알려 줘야 한다.")

        banner("(E) 재작성 결과는 캐시된다 — 파일명에 pytest 버전이 박힌다")
        run_pytest(["test_assert_demo.py"], cwd=tmpdir)
        caches = sorted((tmpdir / "__pycache__").glob("*.pyc"))
        if caches:
            for cache in caches:
                print(f"    {cache.name}")
        else:
            print("    (__pycache__ 가 비어 있다. 이 환경에서는 바이트코드 쓰기가 꺼져 있을 수 있다.)")
        print()
        print("👀 볼 것: 테스트 모듈의 `.pyc` 이름에만 `pytest-<버전>` 이 붙는다.")
        print("   헬퍼 모듈의 `.pyc` 에는 없다 — 재작성을 거치지 않았다는 물증이다.")
        print("   pytest 버전이 올라가면 이 캐시는 자동으로 무효가 된다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
