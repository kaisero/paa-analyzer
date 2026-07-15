"""ZIP upload → parse → store pipeline. Reuses paa_analyzer parsers directly."""

from __future__ import annotations

import re
import time
import zipfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

from paa_analyzer import parsers, parsers_win
from paa_analyzer.taxonomy import (
    LOG_SOURCES,
    PACLI_FILES,
    SKIP_EXTENSIONS,
    SKIP_PREFIXES,
    SPECIAL_FILES,
    SYSTEM_INFO_FILES,
)

# Type alias for progress callbacks
ProgressCallback = Callable[[str, int, str], None]

# System info files that need raw text preserved alongside parsed data
_SYSTEM_RAW_TEXT_FILES = {"routing.txt", "launchctl_list.txt", "system_extension_list.txt"}


def _noop_progress(_stage: str, _pct: int, _detail: str) -> None:
    pass


def parse_zip(data: bytes, on_progress: ProgressCallback | None = None) -> dict:
    """Parse a troubleshooting ZIP from raw bytes. Returns {state: {}, logs: {}, manifest: {}}."""
    progress = on_progress or _noop_progress
    start = time.monotonic()
    all_state: dict[str, dict] = {}
    all_logs: dict[str, dict] = {}
    skipped: list[str] = []
    errors: list[dict] = []

    progress("extracting", 0, "Opening ZIP...")

    with zipfile.ZipFile(BytesIO(data), "r") as zf:
        # Count parseable files
        all_entries = [i for i in zf.infolist() if not i.is_dir() and i.file_size > 0]
        total_files = len(all_entries)
        progress("extracting", 2, f"Found {total_files} files")

        # First pass: find timezone from pacli_status and detect platform
        tz_offset = None
        platform = "unknown"
        for info in all_entries:
            if info.filename.endswith("pacli_status.log"):
                text = zf.read(info).decode("utf-8", errors="replace")
                tz_offset = parsers.extract_tz_offset(text)
            if "Machine Info/" in info.filename:
                platform = "windows"
            elif info.filename.endswith("sw_vers.txt") or info.filename.endswith("launchctl_list.txt"):
                platform = "macos"

        # Second pass: parse everything
        for idx, info in enumerate(all_entries):
            path = info.filename.replace("\\", "/")
            filename = Path(path).name

            # Report progress: 5% → 88% linearly across files
            pct = 5 + int(83 * idx / max(total_files, 1))
            progress("parsing", pct, f"Parsing file {idx + 1} of {total_files}: {filename}")

            try:
                text = zf.read(info).decode("utf-8", errors="replace")
            except Exception as e:
                errors.append({"path": path, "error": str(e)})
                continue

            result = _parse_file(path, filename, text, tz_offset)
            if result is None:
                skipped.append(path)
                continue

            data_type, module, component, name, parsed, raw_text = result

            if data_type == "state":
                key = f"{module}.{component}.{name}"
                entry: dict = {
                    "_meta": {
                        "type": "state",
                        "module": module,
                        "component": component,
                        "source_file": path,
                        "name": name,
                    },
                    "data": parsed,
                }
                if raw_text is not None:
                    entry["raw_text"] = raw_text
                all_state[key] = entry
            elif data_type == "log":
                key = f"{module}.{component}.{name}"
                if key not in all_logs:
                    all_logs[key] = {
                        "_meta": {
                            "type": "log",
                            "module": module,
                            "component": component,
                            "source_file": path,
                            "name": name,
                        },
                        "entries": [],
                    }
                if isinstance(parsed, list):
                    all_logs[key]["entries"].extend(parsed)

    # Sort log entries by timestamp
    total_entries = sum(len(lg["entries"]) for lg in all_logs.values())
    progress("sorting", 90, f"Sorting {total_entries:,} entries...")
    for key in all_logs:
        all_logs[key]["entries"].sort(key=lambda e: e.get("timestamp") or 0)
        all_logs[key]["_meta"]["entry_count"] = len(all_logs[key]["entries"])

    progress("storing", 95, "Building session...")

    elapsed_ms = int((time.monotonic() - start) * 1000)
    manifest = {
        "parse_time_ms": elapsed_ms,
        "timezone_offset": tz_offset,
        "platform": platform,
        "total_log_sources": len(all_logs),
        "total_log_entries": total_entries,
        "total_state_files": len(all_state),
        "skipped": len(skipped),
        "errors": len(errors),
    }

    return {"state": all_state, "logs": all_logs, "manifest": manifest}


def _parse_file(path: str, filename: str, text: str, tz: str | None):
    """Route a file to its parser. Returns (data_type, module, component, name, parsed, raw_text) or None."""

    # Pacli Output files
    if "Pacli Output/" in path:
        meta = PACLI_FILES.get(filename)
        if not meta:
            return None
        name = filename.replace(".log", "").replace("pacli_", "")
        parsed = _run_parser(meta.parser, text, filename=filename, tz=tz, source=name, source_file=path)
        # Store raw text for pacli state files (used by CLI simulator)
        raw_text = text if meta.data_type == "state" else None
        return meta.data_type, meta.module, meta.component, name, parsed, raw_text

    # Machine Info files (Windows) — check before SYSTEM_INFO_FILES so raw_text is preserved
    if "Machine Info/" in path:
        if any(filename.endswith(ext) for ext in SKIP_EXTENSIONS) or any(filename.startswith(p) for p in SKIP_PREFIXES):
            return None
        meta = SYSTEM_INFO_FILES.get(filename)
        if meta:
            name = filename.replace(".log", "").replace(".json", "").replace(".xml", "")
            parsed = _run_parser(meta.parser, text, filename=filename, tz=tz)
            return meta.data_type, meta.module, meta.component, name, parsed, text
        return None

    # System info text files (macOS)
    if filename in SYSTEM_INFO_FILES:
        meta = SYSTEM_INFO_FILES[filename]
        name = filename.replace(".txt", "").replace(".log", "")
        parsed = _run_parser(meta.parser, text, filename=filename, tz=tz)
        raw_text = text if filename in _SYSTEM_RAW_TEXT_FILES else None
        return meta.data_type, meta.module, meta.component, name, parsed, raw_text

    # Special files
    if filename in SPECIAL_FILES:
        meta = SPECIAL_FILES[filename]
        if meta.parser == "skip_large":
            return None
        name = filename.replace(".txt", "").replace(".log", "")
        parsed = _run_parser(meta.parser, text, source=name, source_file=path, tz=tz)
        return meta.data_type, meta.module, meta.component, name, parsed, None

    # Skip binary/installer files (Windows)
    if any(filename.endswith(ext) for ext in SKIP_EXTENSIONS) or any(filename.startswith(p) for p in SKIP_PREFIXES):
        return None

    # Skip 0-byte PAUI GUID files (Windows)
    if re.match(r"^[0-9a-f]{8}-.*PAUI_", filename):
        return None

    # Windows PAUI logs (Logs/<user>/PAUI_*.log) — US date format, separate parser
    if (
        "PAUI_" in filename
        and filename.endswith(".log")
        and "Logs/" in path
        and not filename.startswith(("PAS", "PAC", "PAD"))
    ):
        return (
            "log",
            "Agent",
            "Core",
            "PAUI",
            parsers_win.win_paui_log(text, tz=tz, source="PAUI", source_file=path),
            None,
        )

    # PABrowser.log (Chromium log format)
    if filename == "PABrowser.log":
        return (
            "log",
            "Agent",
            "Core",
            "PABrowser",
            parsers_win.chromium_log(text, source="PABrowser", source_file=path),
            None,
        )

    # DLP logs
    if "DLP/" in path:
        if filename == "PrismaAccessDLP.log":
            return (
                "log",
                "Agent",
                "DLP",
                "PrismaAccessDLP",
                parsers.dlp_log(text, source="DLP.PrismaAccess", source_file=path, tz=tz),
                None,
            )
        if filename == "netfilterdlp.log":
            return (
                "log",
                "Agent",
                "DLP",
                "netfilterdlp",
                parsers.dlp_netfilter(text, source="DLP.NetFilter", source_file=path, tz=tz),
                None,
            )

    # Windows DEM logs — MUST be checked before generic DEM
    if "Logs/DEM/" in path and filename.startswith("palo_alto_networks_dem_") and filename.endswith(".log"):
        service = filename.replace("palo_alto_networks_dem_", "").replace(".log", "")
        service = re.sub(r"_\d{3}$", "", service)
        return (
            "log",
            "Agent",
            "ADEM",
            service,
            parsers_win.win_dem_log(text, source=f"DEM.{service}", source_file=path),
            None,
        )

    # macOS DEM logs
    if "Logs/DEM/" in path and filename.endswith(".log"):
        service = re.sub(r"\s+\d{4}.*$", "", filename.replace(".log", ""))
        service = re.sub(r"^com\.paloaltonetworks\.", "", service).replace(" ", "")
        return "log", "Agent", "ADEM", service, parsers.dem_log(text, source=f"DEM.{service}", source_file=path), None

    # Structured system/user logs
    if (
        path.endswith(".log")
        and ("Logs/System/" in path or "Logs/" in path)
        and "DLP/" not in path
        and "DEM/" not in path
    ):
        stem = Path(filename).stem
        source = stem.split(".")[0]
        if source in LOG_SOURCES:
            module, component = LOG_SOURCES[source]
            return "log", module, component, source, parsers.structured_log(text, source=source, source_file=path), None

    return None


def _run_parser(parser_name: str, text: str, **kwargs):
    fn = getattr(parsers, parser_name, None) or getattr(parsers_win, parser_name, None)
    if fn is None:
        return text
    return fn(text, **kwargs)
