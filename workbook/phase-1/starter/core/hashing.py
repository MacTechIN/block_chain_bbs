"""해시 — 바이트열을 64자 hex 문자열로.

이 파일은 **시작 파일**이다. 여기서 바로 고치지 말고 아래 위치로 복사해서 쓴다.

    복사 위치 : src/bbschain/core/hashing.py
    대응 과제 : Lab 1.3 과제 (2)번
                docs/labs/phase-1-chain.md#lab-13--블록과-체인
    판정 테스트:
        uv run pytest tests/unit/test_serialize.py -k hash_object -v

    통과해야 할 이름
        test_hash_object_goes_through_canonical_bytes

선행 : core/serialize.py 의 canonical_bytes 가 먼저 있어야 한다.
"""

from __future__ import annotations

from typing import Any


def sha256_hex(data: bytes) -> str:
    """바이트열의 SHA-256 을 소문자 hex 문자열(64자)로 돌려준다."""
    raise NotImplementedError("Lab 1.3 과제 (2)번 — 여기를 채워라")


def hash_object(obj: Any) -> str:
    """canonical_bytes 를 거쳐 해시한다. 직접 encode 하지 않는다."""
    # 만족해야 할 불변식 (Lab 1.3 §3(2))
    #   · hash_object 는 canonical_bytes 외의 경로로 바이트를 만들지 않는다
    #     (str.encode() 나 json.dumps 를 여기서 직접 부르면 규칙이 새는 것이다)
    #   · 즉 hash_object(obj) == sha256_hex(canonical_bytes(obj)) 가 항상 성립한다
    raise NotImplementedError("Lab 1.3 과제 (2)번 — 여기를 채워라")
