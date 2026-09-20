"""정규 직렬화 — 해시 입력을 만드는 유일한 통로.

이 파일은 **시작 파일**이다. 여기서 바로 고치지 말고 아래 위치로 복사해서 쓴다.

    복사 위치 : src/bbschain/core/serialize.py
    대응 과제 : Lab 1.3 과제 (1)번
                docs/labs/phase-1-chain.md#lab-13--블록과-체인
    판정 테스트:
        uv run pytest tests/unit/test_serialize.py -v

    통과해야 할 이름
        test_canonical_bytes_key_order_independent
        test_canonical_bytes_key_order_independent_property
        test_canonical_bytes_is_utf8
        test_canonical_bytes_rejects_unserializable
        test_canonical_bytes_int_and_float_are_not_confused

여기서 정한 규칙은 **Phase 1에서 고정하고 끝까지 바꾸지 않는다.**
정한 내용은 docs/decisions/ADR-0001-canonical-serialization.md 에 적는다.
"""

from __future__ import annotations

from typing import Any


def canonical_bytes(obj: Any) -> bytes:
    """해시 입력을 만드는 유일한 함수. 모든 해시는 이걸 통과한다."""
    # 만족해야 할 불변식 (Lab 1.3 §3(1))
    #   · 논리적으로 같은 객체는 언제나 같은 bytes 를 낸다 — 키 삽입 순서와 무관하다
    #   · 결과는 UTF-8 바이트열이다
    #   · JSON 으로 표현할 수 없는 값(set, datetime, bytes, 임의 객체)은
    #     조용히 문자열로 바꾸지 말고 **예외로 거부한다**
    #   · 정수 1 과 실수 1.0 이 같은 바이트열이 되면 안 된다
    raise NotImplementedError("Lab 1.3 과제 (1)번 — 여기를 채워라")
