"""Tests for the paa-parse CLI tool."""

import json
import sys

import pytest


class TestCliMain:
    @pytest.fixture
    def sample_zip_file(self, tmp_path, sample_zip_bytes):
        """Write sample ZIP to a temp file and return its path."""
        zip_path = tmp_path / "test_bundle.zip"
        zip_path.write_bytes(sample_zip_bytes)
        return zip_path

    def test_parses_zip_to_output(self, sample_zip_file, tmp_path, monkeypatch):
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, "argv", ["paa-parse", str(sample_zip_file), str(output_dir)])
        from paa_analyzer.cli import main

        main()
        assert output_dir.exists()

    def test_creates_manifest(self, sample_zip_file, tmp_path, monkeypatch):
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, "argv", ["paa-parse", str(sample_zip_file), str(output_dir)])
        from paa_analyzer.cli import main

        main()
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert manifest["parsed_state"] > 0
        assert manifest["parsed_logs"] > 0
        assert manifest["total_log_entries"] > 0

    def test_creates_state_files(self, sample_zip_file, tmp_path, monkeypatch):
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, "argv", ["paa-parse", str(sample_zip_file), str(output_dir)])
        from paa_analyzer.cli import main

        main()
        state_dir = output_dir / "state"
        assert state_dir.exists()
        state_files = list(state_dir.glob("*.json"))
        assert len(state_files) > 0

    def test_creates_log_files(self, sample_zip_file, tmp_path, monkeypatch):
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, "argv", ["paa-parse", str(sample_zip_file), str(output_dir)])
        from paa_analyzer.cli import main

        main()
        logs_dir = output_dir / "logs"
        assert logs_dir.exists()
        log_files = list(logs_dir.glob("*.json"))
        assert len(log_files) > 0

    def test_missing_file_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["paa-parse", str(tmp_path / "nonexistent.zip")])
        from paa_analyzer.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_no_args_exits(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["paa-parse"])
        from paa_analyzer.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_state_file_content_valid(self, sample_zip_file, tmp_path, monkeypatch):
        output_dir = tmp_path / "output"
        monkeypatch.setattr(sys, "argv", ["paa-parse", str(sample_zip_file), str(output_dir)])
        from paa_analyzer.cli import main

        main()
        # Verify a state file is valid JSON with expected structure
        status_file = output_dir / "state" / "Agent.Core.status.json"
        assert status_file.exists()
        data = json.loads(status_file.read_text())
        assert "_meta" in data
        assert "data" in data
        assert data["_meta"]["type"] == "state"
