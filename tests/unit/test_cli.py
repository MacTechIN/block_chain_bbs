"""Lab 1.5 — 검증 CLI (`cli.py`)

    bbschain post   --author <name> --body <text>
    bbschain dump   [--from N] [--to M]
    bbschain verify                                  # 정상 0 / 파손 1
    bbschain tamper --index N --field body --value X # 환경변수 게이트 없으면 거부(2)

테스트는 `main()` 을 현재 프로세스에서 부른다 (`run_cli` 픽스처).
작업 디렉터리를 tmp_path 로 옮기므로 **체인 파일 경로는 현재 디렉터리 기준 상대 경로**여야 한다.
"""

from __future__ import annotations

from conftest import strip_gate_env

POSTS = [
    ("sam", "lunch-menu-today"),
    ("sam", "second-post"),
    ("sam", "third-post"),
]


def _seed_chain(run_cli):
    for author, body in POSTS:
        result = run_cli("post", "--author", author, "--body", body)
        assert result.code == 0, f"`bbschain post` 가 실패했다.\n{result}"
    return result


def test_verify_exit_code_zero_on_valid(run_cli, cli_chain_file):
    """정상 체인이면 종료 코드 **0**. 스크립트에서 `&&` 로 이어 쓸 수 있어야 한다."""
    _seed_chain(run_cli)
    chain_file = cli_chain_file()
    assert chain_file.stat().st_size > 0, f"{chain_file} 이 비어 있다."

    result = run_cli("verify")
    assert result.code == 0, (
        f"방금 만든 정상 체인인데 verify 가 {result.code} 를 반환했다.\n{result}"
    )
    assert result.out.strip() or result.err.strip(), (
        "verify 가 아무것도 출력하지 않았다. 'VALID   height=N tip=...' 처럼 사람이 볼 줄이 있어야 한다."
    )


def test_verify_exit_code_one_on_tampered(run_cli, cli_chain_file):
    """④ 재공격 — 파일을 직접 고치면 종료 코드 **1** 과 파손 지점을 보고한다.

    Lab 1.2 에서는 같은 공격에 아무 일도 일어나지 않았다.
    """
    _seed_chain(run_cli)
    assert run_cli("verify").code == 0, "변조 전인데 이미 파손 판정이다."

    chain_file = cli_chain_file()
    raw = chain_file.read_text(encoding="utf-8")
    assert "lunch-menu-today" in raw, (
        f"{chain_file} 안에서 글 본문을 찾지 못했다. 본문은 블록 안에 저장된다 (ADR-0002).\n"
        f"파일 앞부분: {raw[:200]!r}"
    )
    # 글자 수를 유지해 JSON 문법은 깨지지 않게 — "값만" 바꾸는 진짜 공격이다.
    chain_file.write_text(raw.replace("lunch-menu-today", "fraud-menu-today"), encoding="utf-8")

    result = run_cli("verify")
    assert result.code == 1, (
        f"체인 파일의 글 본문을 바꿨는데 verify 가 {result.code} 를 반환했다 (1 이어야 한다).\n{result}\n"
        "→ 0 이 나왔다면 Lab 1.2 의 게시판과 같은 상태다."
    )
    combined = (result.out + result.err).lower()
    assert "invalid" in combined, (
        "파손을 알리는 출력이 없다. Lab 1.5 §6 의 화면 형식을 보라:\n"
        "  INVALID: block #3 hash mismatch\n           reason: ...\n"
        f"실제 출력:\n{result}"
    )


def test_tamper_refuses_without_env_gate(run_cli, cli_chain_file):
    """`tamper` 는 환경변수 게이트가 없으면 **아무것도 하지 않고 거부**한다.

    경고 출력만으로는 부족하다. Phase 7 에서 이게 배포판에 들어가면
    배포된 노드에서 아무나 체인을 깨뜨릴 수 있다 (Phase 7 DoD).
    """
    _seed_chain(run_cli)
    chain_file = cli_chain_file()
    before = chain_file.read_bytes()

    result = run_cli(
        "tamper", "--index", "1", "--field", "body", "--value", "hacked",
        env=strip_gate_env(),
    )

    assert result.code != 0, (
        f"게이트 환경변수가 없는데 tamper 가 성공(종료 코드 {result.code})했다.\n{result}\n"
        "→ 변수가 없으면 아무것도 하지 않고 거부해야 한다 (Lab 1.5 §3, 종료 코드 2)."
    )
    assert chain_file.read_bytes() == before, (
        "거부했다면서 체인 파일이 바뀌었다. 게이트는 **쓰기 전에** 걸려야 한다."
    )
    assert run_cli("verify").code == 0, "tamper 거부 후에도 체인은 그대로 유효해야 한다."


def test_tamper_refusal_exit_code_is_two(run_cli, cli_chain_file):
    """거부의 종료 코드는 2 다 — 파손(1)과 구분돼야 스크립트가 둘을 구별할 수 있다."""
    _seed_chain(run_cli)
    result = run_cli(
        "tamper", "--index", "1", "--field", "body", "--value", "hacked",
        env=strip_gate_env(),
    )
    assert result.code == 2, (
        f"게이트 거부는 종료 코드 2 로 약속돼 있다 (Lab 1.5 §3). 실제: {result.code}\n{result}"
    )


def test_post_appends_one_block_and_dump_shows_it(run_cli):
    """`post` 는 블록을 하나 붙이고, `dump` 는 그걸 보여준다."""
    _seed_chain(run_cli)
    result = run_cli("dump")
    assert result.code == 0, f"`bbschain dump` 가 실패했다.\n{result}"
    assert "lunch-menu-today" in result.out or "lunch-menu-today" in result.err, (
        f"dump 출력에 방금 쓴 글이 없다.\n{result}"
    )
