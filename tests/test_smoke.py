"""Lab 0.1 — 판정기가 살아 있는지 확인하는 스모크 테스트.

여기서 검증하는 것은 블록체인이 아니라 **개발 루프 자체**다.
패키지가 설치되어 import 되는가, 버전이 선언되어 있는가 — 이 두 가지가 깨지면
이후 모든 Phase 의 DoD("테스트 통과")를 판정할 수 없다.
"""

from __future__ import annotations

import bbschain


def test_package_imports() -> None:
    """`import bbschain` 이 예외 없이 성공한다 (src 레이아웃 + editable install)."""
    assert bbschain is not None


def test_version_is_declared() -> None:
    """`bbschain.__version__` 이 비어 있지 않은 문자열로 존재한다."""
    version = getattr(bbschain, "__version__", None)
    assert isinstance(version, str), f"__version__ 이 str 이 아니다: {version!r}"
    assert version, "__version__ 이 빈 문자열이다."
