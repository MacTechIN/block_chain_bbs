"""실험 1 — pytest 는 무엇을 테스트로 인식하나.

무엇을 보여주나:
    이름만 조금씩 다른 후보 7개를 임시 디렉터리에 만든다.
    그중 무엇이 수집되고 무엇이 조용히 빠지는지 나란히 보여 준다.
    **코드는 전부 똑같다. 다른 것은 파일 이름·클래스 이름·함수 이름뿐이다.**
    마지막에는 이 저장소에서 `pytest` 가 왜 2 개만 도는지도 같이 본다.

실행 방법:
    uv run python workbook/phase-0/experiments/01_pytest_collection.py

더 읽을 곳:
    docs/tutorial/phase-0.md — Lab 0.1 질문 1 (수집 규칙)
    workbook/테스트-실행법.md — 명령과 출력 읽는 법
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# 이름만 다른 후보들. 본문은 전부 `assert True` 한 줄로 동일하다.
CANDIDATE_FILES: dict[str, str] = {
    "test_named_right.py": '''\
class TestPlainClass:
    def test_method_in_test_class(self):
        assert True


class TestClassWithInit:
    def __init__(self):
        self.value = 1

    def test_method_in_init_class(self):
        assert True


class HelperClass:
    def test_method_in_plain_class(self):
        assert True


def test_plain_function():
    assert True


def check_not_named_test():
    assert True
''',
    "named_right_test.py": '''\
def test_suffix_style_file():
    assert True
''',
    "helper_module.py": '''\
def test_inside_non_test_file():
    assert True
''',
}

# "이건 잡힐까?" 를 먼저 스스로 답해 보고 출력과 대조하라.
CANDIDATE_LABELS: list[tuple[str, str]] = [
    ("test_named_right.py :: test_plain_function", "파일 test_*.py + 함수 test_*"),
    ("test_named_right.py :: check_not_named_test", "함수 이름이 test 로 시작하지 않음"),
    ("test_named_right.py :: TestPlainClass", "클래스 Test* + __init__ 없음"),
    ("test_named_right.py :: TestClassWithInit", "클래스 Test* 이지만 __init__ 이 있음"),
    ("test_named_right.py :: HelperClass", "클래스 이름이 Test 로 시작하지 않음"),
    ("named_right_test.py :: test_suffix_style_file", "파일 *_test.py (이것도 기본 규칙이다)"),
    ("helper_module.py :: test_inside_non_test_file", "파일 이름이 두 규칙 어디에도 안 맞음"),
]


def run_pytest(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """이 저장소의 캐시를 더럽히지 않도록 cacheprovider 를 끄고 pytest 를 돌린다."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bbschain-exp01-") as tmp:
        tmpdir = Path(tmp)
        for name, source in CANDIDATE_FILES.items():
            (tmpdir / name).write_text(source, encoding="utf-8")

        banner("① 디렉터리를 통째로 수집시켰을 때 — 이름 규칙이 여기서 작동한다")
        print("명령: pytest --collect-only -q .   (임시 디렉터리 안에서)")
        print()
        print("먼저 스스로 답하라 — 아래 7개 중 몇 개가 잡힐 것 같나?")
        for label, why in CANDIDATE_LABELS:
            print(f"    · {label:<52} ({why})")

        collected = run_pytest(["--collect-only", "-q", "."], cwd=tmpdir)
        print()
        print("--- pytest 가 실제로 잡은 것 ---")
        print(collected.stdout.strip() or "(stdout 없음)")
        if collected.stderr.strip():
            print("--- stderr ---")
            print(collected.stderr.strip())

        print()
        print("👀 볼 것: 목록에 **없는** 줄이 이 실험의 결과다.")
        print("   빠진 것들은 에러가 아니다. 경고도 대부분 없다. 그냥 조용히 빠진다.")
        print("   즉 '빨간 줄이 없다' 는 '다 돌았다' 와 다른 말이다.")
        print("   `__init__` 이 있는 Test* 클래스만 경고를 남긴다 — 위 출력에서 찾아보라.")

        banner("② 같은 파일을 경로로 직접 지정하면 어떻게 되나")
        print("명령: pytest --collect-only -q helper_module.py")
        print()
        direct = run_pytest(["--collect-only", "-q", "helper_module.py"], cwd=tmpdir)
        print(direct.stdout.strip() or "(stdout 없음)")
        print()
        print("👀 볼 것: ①에서 이름 때문에 빠졌던 파일이 여기서는 잡힌다.")
        print("   파일 이름 규칙은 **pytest 가 스스로 폴더를 뒤질 때만** 쓰는 필터다.")
        print("   내가 경로를 콕 집어 주면 pytest 는 그 파일을 그냥 테스트로 읽는다.")
        print("   → '이름을 바꾸면 무조건 안 돈다' 는 틀린 요약이다.")
        print("     이름과 **부르는 방식**이 같이 정한다.")

    banner("③ 이 저장소에서 인자 없이 부르면 — testpaths 가 범위를 정한다")
    print("명령: pytest --collect-only -q        (저장소 루트에서, 경로 인자 없음)")
    print()
    no_args = run_pytest(["--collect-only", "-q"], cwd=REPO_ROOT)
    print(no_args.stdout.strip() or "(stdout 없음)")

    print()
    print("명령: pytest --collect-only -q tests   (같은 저장소, 경로 인자 있음)")
    print()
    with_args = run_pytest(["--collect-only", "-q", "tests"], cwd=REPO_ROOT)
    tail = with_args.stdout.strip().splitlines()[-6:]
    print("\n".join(tail) or "(stdout 없음)")

    print()
    print("👀 볼 것: 두 숫자가 다르다.")
    print("   경로 인자가 없으면 pyproject.toml 의 testpaths(= 스모크 파일 하나)만 본다.")
    print("   경로를 주면 testpaths 는 비켜선다 — Phase 1 테스트가 여기서 나온다.")
    print("   사라진 게 아니라 **범위 밖**이었을 뿐이다.")
    print("   CI 워크플로도 `uv run pytest -v` 를 인자 없이 부른다.")
    print("   **판정 범위를 워크플로 파일이 아니라 pyproject.toml 이 정하고 있다.**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
