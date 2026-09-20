"""Lab 1.3 — 정규 직렬화 (`core/serialize.py`, `core/hashing.py`)
+ Lab 1.5 의 왕복 property 하나 (`test_block_dict_roundtrip`).

이 파일이 강제하는 것: [ADR-0001](../../docs/decisions/ADR-0001-canonical-serialization.md)
    키 정렬 / 구분자 고정 / 들여쓰기 없음 / UTF-8 / 미지원 타입은 예외.

아직 `src/bbschain/core/serialize.py` 가 없으면 전부 빨갛다. **그게 정상이다.**
실패 메시지가 무엇을 만들어야 하는지 알려 준다.
"""

from __future__ import annotations

import datetime as dt
import json

import pytest
from conftest import (
    block_from_dict,
    block_to_dict,
    core_hashing,
    core_serialize,
    st_block,
)
from hypothesis import given
from hypothesis import strategies as st

# JSON 으로 표현 가능한 값 (float 은 제외한다 — ADR-0001 "정수/실수" 행)
st_jsonable = st.recursive(
    st.none() | st.booleans() | st.integers(min_value=-(10**6), max_value=10**6) | st.text(max_size=8),
    lambda children: st.lists(children, max_size=3)
    | st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3),
    max_leaves=6,
)


def _reordered(obj):
    """모든 딕셔너리의 키 삽입 순서를 뒤집은 **논리적으로 같은** 객체."""
    if isinstance(obj, dict):
        return {k: _reordered(v) for k, v in reversed(list(obj.items()))}
    if isinstance(obj, list):
        return [_reordered(v) for v in obj]
    return obj


def test_canonical_bytes_key_order_independent():
    """논리적으로 같은 객체는 딕셔너리 삽입 순서와 무관하게 같은 bytes 를 낸다.

    Lab 1.1 의 3번 실험(`{"a":1,"b":2}` vs `{"b":2,"a":1}`)을 코드로 못 박은 것.
    """
    canonical_bytes = core_serialize().canonical_bytes

    a = {"author": "sam", "body": "hello", "ts": 1700000000}
    b = {"ts": 1700000000, "body": "hello", "author": "sam"}
    assert canonical_bytes(a) == canonical_bytes(b), (
        "키 삽입 순서만 다른 두 딕셔너리가 다른 바이트열을 냈다.\n"
        "→ json.dumps 의 sort_keys 를 고정하지 않았다 (ADR-0001 '키 순서' 행).\n"
        "이게 새면 Phase 5 에서 두 노드가 같은 블록에 다른 해시를 매긴다."
    )

    nested_a = {"outer": {"z": 1, "a": [{"y": 2, "x": 3}]}, "n": 0}
    nested_b = {"n": 0, "outer": {"a": [{"x": 3, "y": 2}], "z": 1}}
    assert canonical_bytes(nested_a) == canonical_bytes(nested_b), (
        "중첩된 딕셔너리의 키 순서가 결과에 반영됐다. 정렬은 **재귀적으로** 적용돼야 한다."
    )


@given(st_jsonable)
def test_canonical_bytes_key_order_independent_property(obj):
    """임의의 JSON 객체에 대해서도 같은 성질이 유지된다."""
    canonical_bytes = core_serialize().canonical_bytes
    assert canonical_bytes(obj) == canonical_bytes(_reordered(obj)), (
        f"키 순서만 뒤집었는데 바이트열이 달라졌다: {obj!r}"
    )


def test_canonical_bytes_is_utf8():
    """결과는 UTF-8 바이트열이고, 구분자에 공백이 없다."""
    canonical_bytes = core_serialize().canonical_bytes

    raw = canonical_bytes({"b": 2, "a": 1})
    assert isinstance(raw, bytes), f"canonical_bytes 는 bytes 를 반환해야 한다. 받은 타입: {type(raw)}"
    expected = b'{"a":1,"b":2}'
    assert raw == expected, (
        f"정규형이 ADR-0001 과 다르다.\n  기대: {expected!r}\n  실제: {raw!r}\n"
        "→ 키 정렬(sort_keys=True), 구분자 (',', ':') 공백 없음, 들여쓰기 없음을 전부 고정했는지 확인하라."
    )

    korean = canonical_bytes({"body": "한글 글"})
    decoded = korean.decode("utf-8")  # UTF-16 이면 여기서 깨진다
    assert json.loads(decoded) == {"body": "한글 글"}, (
        f"UTF-8 로 디코드한 결과가 원본 객체로 돌아오지 않는다: {decoded!r}"
    )
    assert korean == canonical_bytes({"body": "한글 글"}), (
        "같은 입력인데 호출할 때마다 결과가 다르다 (결정성 위반)."
    )
    # ensure_ascii 는 True/False 중 무엇으로 정해도 된다 (ADR-0001 '비ASCII 처리' 행).
    # 이 테스트가 강제하는 것은 "UTF-8 로 디코드되고 왕복하며, 매번 같다" 까지다.


@pytest.mark.parametrize(
    "value, why",
    [
        ({1, 2, 3}, "set 은 JSON 에 없다"),
        (dt.datetime(2023, 11, 14, 22, 13, 20), "datetime 은 표현 방식이 여러 개다"),  # noqa: DTZ001
        (b"raw bytes", "bytes 는 해시 입력에 직접 담지 않는다 (hex 문자열로 다룬다)"),
        (object(), "임의 객체는 직렬화 규칙이 없다"),
    ],
)
def test_canonical_bytes_rejects_unserializable(value, why):
    """직렬화할 수 없는 타입은 **조용히 넘어가지 않고 예외를 던진다.**

    조용히 `str()` 로 바꿔 버리면 그 순간 규칙이 하나 더 생기고, 나중에 그 규칙이
    바뀌면 기존 체인이 전부 무효가 된다 (ADR-0001 '미지원 타입' 행).
    """
    canonical_bytes = core_serialize().canonical_bytes
    try:
        result = canonical_bytes({"x": value})
    except Exception:  # noqa: BLE001 - TypeError / ValueError / 자체 예외 전부 허용
        return
    pytest.fail(
        f"{type(value).__name__} 을 담았는데 예외 없이 {result!r} 를 반환했다 — {why}.\n"
        "미지원 타입은 반드시 예외로 거부해야 한다 (default= 로 문자열화하면 안 된다)."
    )


def test_canonical_bytes_int_and_float_are_not_confused():
    """`1` 과 `1.0` 은 같은 것으로 취급되면 안 된다.

    float 을 아예 거부하는 구현도, `1` 과 다른 바이트열을 내는 구현도 통과한다.
    금지되는 것은 **둘이 같은 바이트열이 되는 것**뿐이다.
    """
    canonical_bytes = core_serialize().canonical_bytes
    as_int = canonical_bytes({"n": 1})
    try:
        as_float = canonical_bytes({"n": 1.0})
    except Exception:  # noqa: BLE001 - float 을 거부하는 것도 정당한 선택이다
        return
    assert as_int != as_float, (
        "정수 1 과 실수 1.0 이 같은 바이트열이 됐다. JSON 에서 `1` 과 `1.0` 은 다른 문자열이다.\n"
        "타임스탬프를 int 로 고정하는 규칙(ADR-0001)이 무너지는 지점이다."
    )


def test_hash_object_goes_through_canonical_bytes():
    """`hash_object` 는 `canonical_bytes` 외의 경로로 바이트를 만들지 않는다 (Lab 1.3 §3(2))."""
    serialize = core_serialize()
    hashing = core_hashing()
    obj = {"author": "sam", "body": "한글", "ts": 1700000000}
    assert hashing.hash_object(obj) == hashing.sha256_hex(serialize.canonical_bytes(obj)), (
        "hash_object(obj) != sha256_hex(canonical_bytes(obj)).\n"
        "→ 어딘가에서 str.encode() 나 json.dumps 를 직접 부르고 있다. 해시 입력 경로는 하나여야 한다."
    )


@given(st_block())
def test_block_dict_roundtrip(block):
    """Lab 1.5 — `from_dict(to_dict(b)) == b` 가 임의의 블록에 대해 성립한다.

    **JSON 파일을 한 번 거친다.** 저장 왕복에서 `tuple` 이 `list` 로 바뀌는 것이
    "변조하지 않았는데 체인이 깨졌다"의 진짜 원인이기 때문이다 (Lab 1.5 §1 2번).
    """
    data = block_to_dict(block)
    through_json = json.loads(json.dumps(data, ensure_ascii=False))
    restored = block_from_dict(through_json)

    assert restored == block, (
        "저장했다 읽으면 같은 블록이 나와야 한다.\n"
        f"원본  : {block!r}\n복원본: {restored!r}\n"
        "→ 흔한 원인: txs 가 tuple 이 아니라 list 로 복원됐다 / ts 가 float 이 됐다."
    )
    assert isinstance(restored.txs, tuple), (
        f"txs 가 {type(restored.txs).__name__} 으로 복원됐다. tuple 이어야 한다 — "
        "JSON 에는 tuple 이 없으므로 from_dict 가 되돌려 놓아야 한다."
    )
    assert restored.hash == block.hash, (
        "복원된 블록의 해시가 원본과 다르다. 이 상태로 저장/복원하면 "
        "아무도 변조하지 않았는데 validate() 가 first_bad_index=1 을 반환한다."
    )
