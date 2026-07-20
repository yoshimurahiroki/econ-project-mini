from pathlib import Path

from scripts import sync_rules


def test_env_flag_accepts_truthy_value(monkeypatch) -> None:
    monkeypatch.setenv("FEATURE_FLAG", " YES ")

    assert sync_rules.env_flag(name="FEATURE_FLAG")


def test_env_flag_rejects_unset_value(monkeypatch) -> None:
    monkeypatch.delenv("FEATURE_FLAG", raising=False)

    assert not sync_rules.env_flag(name="FEATURE_FLAG")


def test_validate_content_reports_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "pointer.md"
    path.write_text("unexpected\n", encoding="utf-8")

    assert sync_rules.validate_content(path, "expected\n") == [
        f"{path}: content differs from the compact pointer"
    ]


def test_validate_optional_content_accepts_missing_file(tmp_path: Path) -> None:
    assert (
        sync_rules.validate_optional_content(tmp_path / "optional.md", "expected\n")
        == []
    )
