"""Console-script stub.

이 파일은 **랩 과제가 아니다.** `pyproject.toml` 의 `[project.scripts]` 가 가리키는
진입점이 없으면 패키지 설치 자체가 깨지므로, Phase 0 에서 에이전트가 자리만 잡아 둔 것이다.

실제 CLI(`post` / `dump` / `verify` / `tamper`)는 **Lab 1.5 에서 사용자가 구현한다.**
그때 이 파일의 내용을 통째로 갈아엎으면 된다.
→ docs/labs/phase-1-chain.md, tests/unit/test_cli.py
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

_NOT_IMPLEMENTED = (
    "bbschain CLI 는 아직 구현되지 않았다. Lab 1.5 (docs/labs/phase-1-chain.md) 를 보라.\n"
    "이 파일(src/bbschain/cli.py)은 콘솔 스크립트 진입점을 살려 두기 위한 Phase 0 스텁이다."
)


def main(argv: Sequence[str] | None = None) -> int:
    """아직 아무것도 하지 않는다. 안내를 stderr 로 내고 종료 코드 2 를 반환한다."""
    _ = argv
    print(_NOT_IMPLEMENTED, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
