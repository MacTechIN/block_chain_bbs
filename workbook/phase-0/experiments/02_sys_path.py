"""실험 2 — 파이썬은 `bbschain` 을 어디서 찾나.

무엇을 보여주나:
    `import` 는 폴더 목록을 앞에서부터 뒤지는 일이다. 그 목록이 `sys.path` 다.
    ① 똑같은 한 줄을 네 가지 방식으로 실행해 그 목록의 맨 앞이 매번 다른 것을 본다.
    ② 이 저장소의 `bbschain` 이 어느 파일에서 오는지, 무엇이 그 연결을 만드는지 본다.
       답은 `.pth` 파일 한 줄이다. 마법이 아니다.
    ③ 폴더를 옮겨도 import 가 되는지 시험한다.
    ④ pytest 가 테스트 파일의 모듈 이름을 어떻게 정하는지 본다.

실행 방법:
    uv run python workbook/phase-0/experiments/02_sys_path.py

더 읽을 곳:
    docs/tutorial/phase-0.md — Lab 0.2 질문 1·2 (src 레이아웃, editable install)
    workbook/phase-0/설정-가이드.md — import 가 어느 파일을 찾아가나
"""

from __future__ import annotations

import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PROBE_SOURCE = '''\
import os
import sys

print(f"    sys.path[0] = {sys.path[0]!r}")
print(f"    os.getcwd() = {os.getcwd()!r}")
'''

PYTEST_PROBE = '''\
import sys
from pathlib import Path


def test_show_import_context():
    here = str(Path(__file__).resolve().parent)
    parent = str(Path(__file__).resolve().parents[1])
    print(f"    [{Path(__file__).parent.name}/{Path(__file__).name}]")
    print(f"        모듈 __name__                  = {__name__!r}")
    print(f"        자기 디렉터리가 sys.path 에 있나? {here in sys.path}")
    print(f"        상위 디렉터리가 sys.path 에 있나? {parent in sys.path}")
'''


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def run(argv: list[str], cwd: Path) -> str:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
    return (result.stdout + result.stderr).rstrip()


def show_execution_modes(tmpdir: Path) -> None:
    probe = tmpdir / "probe.py"
    probe.write_text(PROBE_SOURCE, encoding="utf-8")

    banner("① 같은 코드, 네 가지 실행 방식 — sys.path[0] 이 매번 다르다")
    print(f"    임시 디렉터리: {tmpdir}")
    print(f"    저장소 루트  : {REPO_ROOT}")

    print()
    print(f"[A] python {probe.name}          (cwd = 저장소 루트)")
    print(run([sys.executable, str(probe)], cwd=REPO_ROOT))

    print()
    print(f"[B] python {probe.name}          (cwd = 임시 디렉터리)")
    print(run([sys.executable, str(probe)], cwd=tmpdir))

    print()
    print("[C] python -m probe               (cwd = 임시 디렉터리)")
    print(run([sys.executable, "-m", "probe"], cwd=tmpdir))

    print()
    print("[D] python -c '...'               (cwd = 임시 디렉터리)")
    print(run([sys.executable, "-c", PROBE_SOURCE], cwd=tmpdir))

    print()
    print("👀 볼 것: 네 줄의 sys.path[0] 이 전부 같지는 않다.")
    print("   · [A]와 [B]는 지금 폴더가 달라도 결과가 같다.")
    print("     스크립트가 **놓여 있는** 디렉터리가 들어가기 때문이다.")
    print("   · [C]와 [D]는 지금 폴더를 따라간다.")
    print("     `-c` 는 빈 문자열 '' 로 나오는데, 이건 '경로 없음'이 아니라 **'지금 폴더'** 라는 뜻이다.")
    print("   · 정리하면 `import` 가 무엇을 찾을지는 코드가 아니라")
    print("     **어떻게 실행했느냐**가 절반을 정한다.")


def show_editable_install() -> None:
    banner("② 이 저장소의 bbschain 은 어디 있는 파일인가")
    import bbschain

    print(f"    bbschain.__file__ = {bbschain.__file__}")
    print(f"    저장소 루트에 bbschain/ 디렉터리가 있나? -> {(REPO_ROOT / 'bbschain').exists()}")
    print("    (src 레이아웃이므로 저장소 루트에는 없다. 그런데도 import 는 된다.)")

    site_packages = Path(sysconfig.get_paths()["purelib"])
    print()
    print(f"    site-packages: {site_packages}")
    pth_files = sorted(site_packages.glob("*bbschain*"))
    if not pth_files:
        print("    ⚠️ bbschain 관련 파일을 site-packages 에서 못 찾았다. `uv sync` 를 먼저 돌렸나?")
        return

    for path in pth_files:
        print(f"    └─ {path.name}")
        if path.suffix == ".pth":
            content = path.read_text(encoding="utf-8").strip()
            for line in content.splitlines():
                print(f"         내용: {line}")

    print()
    print("👀 볼 것: `.pth` 파일 한 줄에 적힌 경로가 곧 `src/` 다.")
    print("   파이썬은 site-packages 를 읽을 때 `.pth` 의 각 줄을 sys.path 에 추가한다.")
    print("   editable install 은 마법이 아니라 **그 파일 하나**다.")
    print("   그래서 `src/` 를 다른 이름으로 바꾸면 이 줄이 가리키는 곳이 사라지고 import 가 깨진다.")


def show_cwd_independence(tmpdir: Path) -> None:
    banner("③ 작업 디렉터리를 옮겨도 import 가 되나")
    snippet = "import bbschain; print('    bbschain.__file__ =', bbschain.__file__)"

    print("[A] cwd = 저장소 루트")
    print(run([sys.executable, "-c", snippet], cwd=REPO_ROOT))

    print()
    print(f"[B] cwd = {tmpdir}")
    print(run([sys.executable, "-c", snippet], cwd=tmpdir))

    print()
    print("👀 볼 것: 둘 다 같은 파일을 가리킨다. 지금 폴더가 어디든 상관없다.")
    print("   ①에서 `-c` 의 sys.path[0] 은 지금 폴더를 따라간다고 했는데도 결과가 같다.")
    print("   `bbschain` 은 지금 폴더가 아니라 ②의 `.pth` 가 넣어 준 경로에서 오기 때문이다.")
    print("   **이게 '어디서 실행해도 같은 결과'의 정체다.**")


def show_pytest_import_mode(tmpdir: Path) -> None:
    banner("④ pytest 의 prepend 모드 — 테스트 파일에서는 무엇이 sys.path[0] 이 되나")
    pkg_dir = tmpdir / "as_package"
    plain_dir = tmpdir / "as_plain_dir"
    pkg_dir.mkdir()
    plain_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "test_in_package.py").write_text(PYTEST_PROBE, encoding="utf-8")
    (plain_dir / "test_in_plain_dir.py").write_text(PYTEST_PROBE, encoding="utf-8")

    print(f"    {pkg_dir.name}/   __init__.py 있음")
    print(f"    {plain_dir.name}/ __init__.py 없음")
    print()
    print("명령: pytest -s -q .   (임시 디렉터리 안에서)")
    print()
    print(
        run(
            [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-s", "-q", "."],
            cwd=tmpdir,
        )
    )
    print()
    print("👀 볼 것: 두 테스트의 **모듈 이름**이 다르다.")
    print("   pytest(기본 prepend 모드)는 테스트 파일에서 위로 올라가며")
    print("   **`__init__.py` 가 없는 첫 디렉터리**를 찾아 그곳을 sys.path 에 넣고,")
    print("   거기서부터의 경로로 모듈 이름을 만든다.")
    print(f"   · {plain_dir.name}/ 은 패키지가 아니라서 자기 자신이 기준점이 된다 -> 모듈 이름이 짧다.")
    print(f"   · {pkg_dir.name}/ 은 패키지라서 한 칸 위가 기준점이 된다 -> 모듈 이름에 패키지가 붙는다.")
    print("   그래서 서로 다른 디렉터리에 같은 이름의 테스트 파일이 있으면,")
    print("   `__init__.py` 유무에 따라 '모듈 이름 충돌'이 났다 안 났다 한다.")
    print("   (sys.path[0] 하나만 보면 안 된다 — pytest 는 파일마다 경로를 앞에 끼워 넣으므로")
    print("    테스트가 도는 시점의 [0] 은 마지막에 끼워진 것이다.)")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bbschain-exp02-") as tmp:
        tmpdir = Path(tmp)
        show_execution_modes(tmpdir)
        show_editable_install()
        show_cwd_independence(tmpdir)
        show_pytest_import_mode(tmpdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
