"""CLI: parse a troubleshooting ZIP into structured JSON files."""

from __future__ import annotations

import json
import re
import sys
import time
import zipfile
from pathlib import Path

from paa_analyzer import parsers, parsers_win
from paa_analyzer.taxonomy import (
    PACLI_FILES,
    SYSTEM_INFO_FILES,
    LOG_SOURCES,
    SPECIAL_FILES,
    SKIP_EXTENSIONS,
    SKIP_PREFIXES,
)


def main():
    if len(sys.argv) < 2:
        print("Usage: paa-parse <troubleshooting.zip> [output_dir]")
        sys.exit(1)

    zip_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output")

    if not zip_path.exists():
        print(f"Error: {zip_path} not found")
        sys.exit(1)

    print(f"Parsing {zip_path.name} ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")
    start = time.monotonic()

    output_dir.mkdir(parents=True, exist_ok=True)
    state_dir = output_dir / "state"
    logs_dir = output_dir / "logs"
    state_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)

    # Extract and get timezone context
    tz_offset = None
    manifest = []
    all_state = {}
    all_logs = {}
    skipped = []
    errors = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        # First pass: find timezone from pacli_status
        for info in zf.infolist():
            if info.filename.endswith("pacli_status.log"):
                text = zf.read(info).decode("utf-8", errors="replace")
                tz_offset = parsers.extract_tz_offset(text)
                break

        # Second pass: parse everything
        for info in zf.infolist():
            if info.is_dir() or info.file_size == 0:
                continue

            path = info.filename.replace("\\", "/")
            filename = Path(path).name
            manifest.append({"path": path, "size": info.file_size})

            try:
                text = zf.read(info).decode("utf-8", errors="replace")
            except Exception as e:
                errors.append({"path": path, "error": str(e)})
                continue

            result = parse_file(path, filename, text, tz_offset)
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
                    # Update source_file to show all contributing files
                    if path not in all_logs[key]["_meta"]["source_file"]:
                        all_logs[key]["_meta"]["source_file"] += f", {path}"

    # Sort all log entries by timestamp
    for key in all_logs:
        all_logs[key]["entries"].sort(key=lambda e: e.get("timestamp") or 0)
        all_logs[key]["_meta"]["entry_count"] = len(all_logs[key]["entries"])

    # Beautify log messages containing embedded JSON
    for key in all_logs:
        for entry in all_logs[key]["entries"]:
            msg = entry.get("message", "")
            if "{" in msg:
                beautified = parsers.beautify_message(msg)
                if beautified:
                    entry["beautified"] = beautified

    # Write state files
    for key, state in all_state.items():
        out_file = state_dir / f"{key}.json"
        out_file.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")

    # Write log files
    for key, log in all_logs.items():
        out_file = logs_dir / f"{key}.json"
        out_file.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")

    # Write manifest
    summary = {
        "source_file": zip_path.name,
        "parse_time_ms": int((time.monotonic() - start) * 1000),
        "timezone_offset": tz_offset,
        "total_files": len(manifest),
        "parsed_state": len(all_state),
        "parsed_logs": len(all_logs),
        "total_log_entries": sum(lg["_meta"]["entry_count"] for lg in all_logs.values()),
        "skipped_files": skipped,
        "errors": errors,
        "state_files": sorted(all_state.keys()),
        "log_files": sorted(f"{k} ({all_logs[k]['_meta']['entry_count']} entries)" for k in all_logs),
    }
    (output_dir / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    elapsed = time.monotonic() - start
    print(f"\nDone in {elapsed:.1f}s")
    print(f"  State: {len(all_state)} files → {state_dir}/")
    print(f"  Logs:  {len(all_logs)} sources, {summary['total_log_entries']:,} entries → {logs_dir}/")
    print(f"  Skipped: {len(skipped)} files")
    if errors:
        print(f"  Errors: {len(errors)}")
    print(f"  Manifest: {output_dir}/manifest.json")


def parse_file(
    path: str, filename: str, text: str, tz: str | None
) -> tuple[str, str, str, str, object, str | None] | None:
    """Returns (data_type, module, component, name, parsed_data, raw_text) or None if skipped."""

    # Pacli Output files
    if "Pacli Output/" in path:
        meta = PACLI_FILES.get(filename)
        if not meta:
            return None
        name = filename.replace(".log", "").replace("pacli_", "")
        parsed = _run_parser(meta.parser, text, filename=filename, tz=tz, source=name, source_file=path)
        raw_text = text if meta.data_type == "state" else None
        return meta.data_type, meta.module, meta.component, name, parsed, raw_text

    # Machine Info files (Windows)
    if "Machine Info/" in path:
        if any(filename.endswith(ext) for ext in SKIP_EXTENSIONS) or any(filename.startswith(p) for p in SKIP_PREFIXES):
            return None
        meta = SYSTEM_INFO_FILES.get(filename)
        if meta:
            name = filename.replace(".log", "").replace(".json", "").replace(".xml", "")
            parsed = _run_parser(meta.parser, text, filename=filename, tz=tz)
            return meta.data_type, meta.module, meta.component, name, parsed, text
        return None

    # System info text files
    if filename in SYSTEM_INFO_FILES:
        meta = SYSTEM_INFO_FILES[filename]
        name = filename.replace(".txt", "").replace(".log", "")
        parsed = _run_parser(meta.parser, text, filename=filename, tz=tz)
        return meta.data_type, meta.module, meta.component, name, parsed, None

    # Special files (traffic, networkextensions, unified_log, etc.)
    if filename in SPECIAL_FILES:
        meta = SPECIAL_FILES[filename]
        if meta.parser == "skip_large":
            return None
        name = filename.replace(".txt", "").replace(".log", "")
        parsed = _run_parser(meta.parser, text, source=name, source_file=path, tz=tz)
        return meta.data_type, meta.module, meta.component, name, parsed, None

    # Skip binary/installer files
    if any(filename.endswith(ext) for ext in SKIP_EXTENSIONS) or any(filename.startswith(p) for p in SKIP_PREFIXES):
        return None

    # Skip 0-byte PAUI GUID files
    if re.match(r"^[0-9a-f]{8}-.*PAUI_", filename):
        return None

    # Windows PAUI logs
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

    # PABrowser.log
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
        # Derive source from filename: PAS.3.log → PAS
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


if __name__ == "__main__":
    main()
