"""Key checks. Uses a made-up key: no real key is needed or read."""

import base64

from frontline import keys

FAKE = "db-Fake0Key0For0Tests0Only000000"  # 32 characters, like a real key


def test_fake_key_has_the_real_shape():
    assert len(FAKE) == 32
    assert keys.shape_problems(FAKE) == []


def test_stray_line_break_is_reported():
    problems = keys.shape_problems(FAKE + "\n")
    assert problems == ["The key has a space or line break before or after it."]


def test_quotes_are_reported_once():
    problems = keys.shape_problems(f'"{FAKE}"')
    assert problems == ["The key is wrapped in quotes. Paste it without them."]


def test_wrong_prefix_and_length():
    problems = keys.shape_problems("sk-" + "x" * 20)
    assert any("doesn't start with db-" in p for p in problems)
    assert any("23 characters long" in p for p in problems)


def test_missing_key_points_at_a_lookalike_name(monkeypatch, tmp_path):
    monkeypatch.delenv(keys.ENV_NAME, raising=False)
    monkeypatch.setenv("DATABENTO_KEY", FAKE)
    [problem] = keys.shape_problems(None, tmp_path / ".env")
    assert "No API key found" in problem
    assert "DATABENTO_KEY" in problem
    assert FAKE not in problem


def test_clean_removes_spaces_line_breaks_and_quotes():
    assert keys.clean(f' "{FAKE}"\n') == FAKE


def test_env_file_values_come_back_raw(tmp_path):
    env = tmp_path / ".env"
    env.write_text(f"# comment\nDATABENTO_API_KEY= {FAKE}\n", encoding="utf-8-sig")
    assert keys.read_env_file(env)["DATABENTO_API_KEY"] == f" {FAKE}"


def test_environment_wins_over_env_file(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("DATABENTO_API_KEY=db-FromTheFile0000000000000000000\n", encoding="utf-8")
    monkeypatch.setenv(keys.ENV_NAME, FAKE)
    raw, source = keys.find_key(env)
    assert raw == FAKE
    assert "environment variable" in source


def test_scrub_removes_every_form_of_the_key():
    basic = base64.b64encode(f"{FAKE}:".encode()).decode()
    text = f"key={FAKE} header=Basic {basic} again {basic} other=db-SomethingElse12345678"
    cleaned = keys.scrub(text, FAKE)
    assert FAKE not in cleaned
    assert basic not in cleaned
    assert "db-SomethingElse" not in cleaned
