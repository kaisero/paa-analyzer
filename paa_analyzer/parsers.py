"""Parsers: each function takes file text and returns structured data."""

from __future__ import annotations

import ast
import json
import re
import sys
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

# Parsed bundle data is heterogeneous (ints, strings, bools, nested lists), so a
# parsed record is a dict of dynamic values and a parsed log/state file is one of
# these records or a list of them.
Record = dict[str, Any]
LogEntry = dict[str, Any]

# ── Timestamp parsing ──────────────────────────────────────────────────────

_ISO_FULL = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3})([+-])(\d{2}):(\d{2})")
_NUMERIC_OFFSET = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)([+-])(\d{2})(\d{2})")
_GMT_OFFSET = re.compile(r"GMT([+-])(\d{2})(\d{2})")
_BARE_DT = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
_BRACKETED = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")
_DLP_DT = re.compile(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}):\d{3}")


def parse_ts(raw: str, default_offset: str | None = None) -> float | None:
    """Parse any known timestamp format → epoch float (UTC seconds)."""
    if not raw:
        return None
    m = _ISO_FULL.search(raw)
    if m:
        dt = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S.%f")
        off = timedelta(hours=int(m.group(3)), minutes=int(m.group(4)))
        if m.group(2) == "-":
            off = -off
        return dt.replace(tzinfo=timezone(off)).timestamp()

    m = _NUMERIC_OFFSET.search(raw)
    if m:
        dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f")
        off = timedelta(hours=int(m.group(3)), minutes=int(m.group(4)))
        if m.group(2) == "-":
            off = -off
        return dt.replace(tzinfo=timezone(off)).timestamp()

    m = _GMT_OFFSET.search(raw)
    if m:
        dt_part = raw.split(", GMT")[0].strip()
        try:
            dt = datetime.strptime(dt_part, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
        off = timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
        if m.group(1) == "-":
            off = -off
        return dt.replace(tzinfo=timezone(off)).timestamp()

    m = _DLP_DT.search(raw)
    if m:
        dt = datetime.strptime(m.group(1), "%Y/%m/%d %H:%M:%S")
        return _apply_offset(dt, default_offset)

    m = _BRACKETED.search(raw)
    if m:
        dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        return _apply_offset(dt, default_offset)

    m = _BARE_DT.search(raw)
    if m:
        dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        return _apply_offset(dt, default_offset)

    return None


def format_ts(epoch: float | None) -> str | None:
    """Format epoch float → ISO-8601 UTC string for API responses."""
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=UTC).isoformat()


def _apply_offset(dt: datetime, offset_str: str | None) -> float:
    if offset_str:
        m = re.match(r"([+-])(\d{2})(\d{2})", offset_str)
        if m:
            off = timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
            if m.group(1) == "-":
                off = -off
            return dt.replace(tzinfo=timezone(off)).timestamp()
    return dt.replace(tzinfo=UTC).timestamp()


def extract_tz_offset(text: str) -> str | None:
    m = _GMT_OFFSET.search(text)
    return f"{m.group(1)}{m.group(2)}{m.group(3)}" if m else None


# ── State parsers ──────────────────────────────────────────────────────────


def key_value(text: str, **_: Any) -> Record:
    """Parse Key: Value lines into a dict."""
    data: Record = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            if not data:
                data["value"] = line
            continue
        key, _sep, val = line.partition(":")
        normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
        data[normalized] = val.strip()
    return data


def forwarding_profile(text: str, **_: Any) -> Record:
    rules: list[Record] = []
    flags: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*\|\s*(.+?)\s*\|\s*$", line)
        if m:
            cells = [c.strip() for c in m.group(1).split("|")]
            if len(cells) >= 8:
                try:
                    int(cells[0])
                except ValueError:
                    continue
                rules.append(
                    {
                        "priority": int(cells[0]),
                        "name": cells[1],
                        "enabled": cells[2].lower() == "yes",
                        "source_apps": cells[3],
                        "destinations": cells[4],
                        "connection_type": cells[5],
                        "connect_through": cells[6],
                        "hits": int(cells[7]) if cells[7].isdigit() else 0,
                    }
                )
        fm = re.match(r"^\s*X\s*-\s*(.+)", line)
        if fm:
            flags.append(fm.group(1).strip())
    return {"rules": rules, "flags": flags}


def gateway_list(text: str, **_: Any) -> Record:
    location = ""
    gateways: list[Record] = []
    m = re.search(r"Agent Location:\s*(\S+)", text)
    if m:
        location = m.group(1)
    for line in text.splitlines():
        if re.match(r"^-{5,}|^Name\s|^$|Agent Location|External Gateways|Internal Gateways", line):
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                prio = (
                    int(parts[-2])
                    if parts[-2].isdigit()
                    else int(parts[-3])
                    if len(parts) >= 4 and parts[-3].isdigit()
                    else None
                )
            except (ValueError, IndexError):
                prio = None
            if prio is not None:
                name = line[:24].strip()
                addr = parts[-1]
                gateways.append({"name": name, "priority": prio, "address": addr})
    return {"agent_location": location, "gateways": gateways}


def hip_status(text: str, tz: str | None = None, **_: Any) -> Record:
    data: Record = {"collection": "", "next_check": None, "gateways": []}
    in_table = False
    for line in text.splitlines():
        if line.startswith("HIP Collection:"):
            data["collection"] = line.split(":", 1)[1].strip()
        elif line.startswith("Next HIP Check:"):
            data["next_check"] = format_ts(parse_ts(line.split(":", 1)[1].strip(), tz))
        elif "Last HIP Report" in line:
            in_table = True
        elif in_table and line.strip() and not line.startswith("-"):
            name = line[:24].strip()
            ts_raw = line[24:].strip()
            if name and ts_raw:
                data["gateways"].append({"gateway": name, "last_report": format_ts(parse_ts(ts_raw, tz))})
    return data


def protection(text: str, **_: Any) -> list[Record]:
    items: list[Record] = []
    for line in text.splitlines():
        if re.match(r"^-{3,}|^Protection|^$", line):
            continue
        parts = line.split()
        if len(parts) >= 2:
            items.append({"name": parts[0], "state": " ".join(parts[1:])})
    return items


def epm_commands(text: str, tz: str | None = None, **_: Any) -> list[Record]:
    cmds: list[Record] = []
    uuid_re = re.compile(r"^[0-9a-f]{8}-")
    for line in text.splitlines():
        if not uuid_re.match(line.strip()):
            continue
        parts = line.split()
        if len(parts) >= 8:
            cmds.append(
                {
                    "id": parts[0],
                    "command": " ".join(parts[1:-5]),
                    "state": parts[-5],
                    "received": format_ts(parse_ts(f"{parts[-4]} {parts[-3]}", tz)),
                    "finished": format_ts(parse_ts(f"{parts[-2]} {parts[-1]}", tz)),
                }
            )
    return cmds


def traffic_rdns(text: str, **_: Any) -> Record:
    try:
        raw = json.loads(text)
        cache = raw.get("ReverseDnsCache", {})
        return {"cname_records": cache.get("cname_record", []), "ip_records": cache.get("ip_record", [])}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}


def system_info(text: str, filename: str = "", **_: Any) -> Record:
    if filename == "sw_vers.txt":
        d: Record = {}
        for line in text.splitlines():
            if ":" in line:
                k, _sep, v = line.partition(":")
                d[k.strip().lower().replace(" ", "_")] = v.strip()
        return d
    if filename == "uname.txt":
        parts = text.split()
        return {"kernel": text.strip(), "architecture": parts[-1] if parts else ""}
    if filename == "external_ip.txt":
        try:
            return {"external_ip": json.loads(text).get("origin", text.strip())}
        except json.JSONDecodeError:
            return {"external_ip": text.strip()}
    if filename == "date_generated.txt":
        return {"date_generated": text.strip()}
    if filename == "PrismaAccessAgent_agent_version.log":
        m = re.search(r"version:\s*(.+)", text, re.IGNORECASE)
        return {"agent_version": m.group(1).strip() if m else text.strip()}
    return {"value": text.strip()}


def system_extensions(text: str, **_: Any) -> list[Record]:
    exts: list[Record] = []
    category = ""
    for line in text.splitlines():
        if "network_extension" in line:
            category = "network_extension"
        elif "endpoint_security" in line:
            category = "endpoint_security"
        elif line.startswith("enabled") or not line.strip():
            continue
        else:
            parts = line.split("\t")
            if len(parts) >= 6:
                m = re.match(r"(.+?)\s+\((.+?)\)", parts[3].strip())
                exts.append(
                    {
                        "enabled": parts[0].strip() == "*",
                        "active": parts[1].strip() == "*",
                        "team_id": parts[2].strip(),
                        "bundle_id": m.group(1) if m else parts[3].strip(),
                        "version": m.group(2) if m else "",
                        "name": parts[4].strip(),
                        "category": category,
                        "state": parts[5].strip().strip("[]"),
                    }
                )
    return exts


def routing_table(text: str, **_: Any) -> Record:
    """Parse netstat -rn style routing table into structured records."""
    result: dict[str, list[Record]] = {"ipv4": [], "ipv6": []}
    current: list[Record] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Internet6"):
            current = result["ipv6"]
            continue
        if stripped.startswith("Internet"):
            current = result["ipv4"]
            continue
        if current is None or stripped.startswith("Destination") or stripped.startswith("---"):
            continue
        parts = stripped.split()
        if len(parts) >= 4:
            current.append(
                {
                    "destination": parts[0],
                    "gateway": parts[1],
                    "flags": parts[2],
                    "netif": parts[3],
                    "expire": parts[4] if len(parts) > 4 else None,
                }
            )
    return result


def launchctl_list(text: str, **_: Any) -> list[Record]:
    """Parse launchctl list output into structured records."""
    items: list[Record] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("PID"):
            continue
        parts = stripped.split("\t")
        if len(parts) >= 3:
            pid_str = parts[0].strip()
            try:
                status = int(parts[1].strip())
            except ValueError:
                status = 0
            items.append(
                {
                    "pid": int(pid_str) if pid_str != "-" else None,
                    "status": status,
                    "label": parts[2].strip(),
                }
            )
    return items


def app_list(text: str, **_: Any) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def raw_text(text: str, **_: Any) -> str:
    return text


# ── Log parsers ────────────────────────────────────────────────────────────

_STRUCT_LOG = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2})\s+<(\w+)>\s+(\S+)\s+\[([^\]]+)\]\s+(.*)"
)


def structured_log(text: str, source: str = "", source_file: str = "", **_: Any) -> list[LogEntry]:
    """Parse ISO-8601 structured log files (PAS, SecurityExtension, etc.)."""
    entries: list[LogEntry] = []
    current: LogEntry | None = None
    for line in text.split("\n"):
        line = line.rstrip("\r")
        m = _STRUCT_LOG.match(line)
        if m:
            if current:
                current["message"] = current["message"].rstrip()
                entries.append(current)
            current = {
                "timestamp": parse_ts(m.group(1)),
                "level": sys.intern(m.group(2).lower()),
                "host": sys.intern(m.group(3)),
                "pid": sys.intern(m.group(4)),
                "message": m.group(5),
            }
        elif current:
            current["message"] += "\n" + line
    if current:
        current["message"] = current["message"].rstrip()
        entries.append(current)
    return entries


_DEM_LOG = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4})\s+-\s+(\w+):\s*(.*)")


def dem_log(text: str, source: str = "", source_file: str = "", **_: Any) -> list[LogEntry]:
    entries: list[LogEntry] = []
    current: LogEntry | None = None
    for line in text.split("\n"):
        line = line.rstrip("\r")
        m = _DEM_LOG.match(line)
        if m:
            if current:
                entries.append(current)
            current = {
                "timestamp": parse_ts(m.group(1)),
                "level": sys.intern(m.group(2).lower()),
                "message": m.group(3),
            }
        elif current:
            current["message"] += "\n" + line
    if current:
        entries.append(current)
    return entries


_DLP_LOG = re.compile(r"^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}:\d{3})\s+(.*)")
_DLP_NETFILTER = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+\[(\w+)\]\s+(?:\[.*?\]\s+)?(.*)")


def dlp_log(text: str, source: str = "DLP", source_file: str = "", tz: str | None = None, **_: Any) -> list[LogEntry]:
    entries: list[LogEntry] = []
    for line in text.splitlines():
        m = _DLP_LOG.match(line)
        if m:
            entries.append({"timestamp": parse_ts(m.group(1), tz), "level": "info", "message": m.group(2)})
    return entries


def dlp_netfilter(
    text: str, source: str = "DLP.NetFilter", source_file: str = "", tz: str | None = None, **_: Any
) -> list[LogEntry]:
    entries: list[LogEntry] = []
    for line in text.splitlines():
        m = _DLP_NETFILTER.match(line)
        if m:
            entries.append(
                {
                    "timestamp": parse_ts(f"[{m.group(1)}]", tz),
                    "level": sys.intern(m.group(2).lower()),
                    "message": m.group(3),
                }
            )
    return entries


def connection_history(
    text: str, tz: str | None = None, source: str = "ConnectionHistory", source_file: str = "", **_: Any
) -> list[LogEntry]:
    """Parse connection history into flat log entries (one per step)."""
    # First pass: group steps by connection
    conns: list[Record] = []
    current: Record | None = None
    for line in text.splitlines():
        m = re.match(r"^Connection #(\d+):", line)
        if m:
            if current:
                conns.append(current)
            current = {"id": int(m.group(1)), "steps": []}
        elif current:
            sm = re.match(r"^\s+\d+\.\s+\[(.+?)\]\s+(.+)", line)
            if sm:
                current["steps"].append({"timestamp": parse_ts(f"[{sm.group(1)}]", tz), "message": sm.group(2).strip()})
    if current:
        conns.append(current)

    # Derive outcome per connection and flatten into log entries
    entries: list[LogEntry] = []
    for c in conns:
        steps = c["steps"]
        if not steps:
            continue
        msgs = " ".join(s["message"].lower() for s in steps)
        if "connected successfully" in msgs:
            outcome = "connected"
        elif "failed to establish" in msgs or "could not raise" in msgs:
            outcome = "failed"
        else:
            outcome = "disconnected"
        # Determine level from outcome
        level = {"connected": "info", "failed": "error", "disconnected": "warning"}.get(outcome, "info")
        # Extract gateway
        gateway = ""
        for s in steps:
            gm = re.search(r'gateway "(.+?)"', s["message"])
            if gm:
                gateway = gm.group(1)
                break
        # Build one entry per step with connection context
        conn_label = f"Connection #{c['id']}"
        if gateway:
            conn_label += f" [{gateway}]"
        conn_label += f" ({outcome})"
        for s in steps:
            entries.append(
                {
                    "timestamp": s["timestamp"],
                    "level": level,
                    "message": f"{conn_label} — {s['message']}",
                }
            )
    return entries


def event_table(text: str, tz: str | None = None, source: str = "", source_file: str = "", **_: Any) -> list[LogEntry]:
    events: list[LogEntry] = []
    data_re = re.compile(r"^(\d+)\s{2,}(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s{2,}(\S.+?\S)\s{2,}(.+)$")
    for line in text.splitlines():
        m = data_re.match(line)
        if m:
            event_type = m.group(3).strip()
            msg = m.group(4).strip()
            events.append(
                {
                    "id": int(m.group(1)),
                    "timestamp": parse_ts(m.group(2), tz),
                    "level": "info",
                    "event_type": event_type,
                    "message": f"[{event_type}] {msg}",
                }
            )
    return events


def traffic_json(text: str, tz: str | None = None, source: str = "", source_file: str = "", **_: Any) -> list[LogEntry]:
    start = text.find("[")
    if start < 0:
        return []
    try:
        raw = json.loads(text[start:])
    except json.JSONDecodeError:
        return []
    entries: list[LogEntry] = []
    for r in raw:
        verdict = r.get("verdict", "")
        protocol = r.get("protocol", "")
        destination = r.get("destination", "")
        source_app = r.get("sourceApp", "")
        reason = r.get("reason", "")
        app_name = source_app.split("/")[-1]
        message = f"{verdict} {protocol} {destination} app={app_name}\nApp: {source_app}\nReason: {reason}"
        entries.append(
            {
                "timestamp": parse_ts(r.get("timeAndDate", ""), tz),
                "level": "info",
                "destination": destination,
                "protocol": protocol,
                "verdict": verdict,
                "source_app": source_app,
                "reason": reason,
                "index": r.get("index"),
                "traffic_type": r.get("trafficType", ""),
                "message": message,
            }
        )
    return entries


def remote_shell(text: str, source_file: str = "", **_: Any) -> list[LogEntry]:
    entries: list[LogEntry] = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) >= 6:
            entries.append(
                {
                    "timestamp": parse_ts(parts[0].strip()),
                    "level": sys.intern(parts[1].strip().lower()),
                    "message": parts[-1].strip(),
                }
            )
    return entries


# ── Message beautification ────────────────────────────────────────────────


def _find_json_spans(text: str) -> list[tuple[int, int]]:
    """Find (start, end) spans of potential JSON objects in text."""
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(text):
        if text[i] == "{":
            depth = 0
            in_string = False
            escape = False
            j = i
            while j < len(text):
                c = text[j]
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"' and not escape:
                    in_string = not in_string
                elif not in_string:
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            spans.append((i, j + 1))
                            break
                j += 1
            # Skip past this span to avoid finding sub-objects
            if spans and spans[-1][0] == i:
                i = spans[-1][1]
                continue
        i += 1
    return spans


def _try_parse_json(text: str) -> dict[str, Any] | list[Any] | None:
    """Try parsing text as JSON, escaped JSON, or Python dict."""
    # Standard JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, (dict, list)):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    # Escaped JSON (\" → ")
    if '\\"' in text:
        try:
            unescaped = text.replace('\\"', '"').replace("\\\\", "\\")
            parsed = json.loads(unescaped)
            if isinstance(parsed, (dict, list)):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
    # Python dict literal ({'key': 'value'})
    if "'" in text:
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, SyntaxError):
            pass
    return None


def beautify_message(message: str) -> str | None:
    """Extract embedded JSON from a log message and pretty-print it.

    Returns the beautified message, or None if no qualifying JSON found.
    Only beautifies JSON objects with 2+ keys to skip trivial objects.
    """
    if "{" not in message:
        return None

    spans = _find_json_spans(message)
    if not spans:
        return None

    # Process spans in reverse to preserve offsets during replacement
    result = message
    replaced = False
    for start, end in reversed(spans):
        candidate = message[start:end]
        parsed = _try_parse_json(candidate)
        if parsed is None:
            continue
        # Skip trivial objects (fewer than 2 keys)
        if isinstance(parsed, dict) and len(parsed) < 2:
            continue
        pretty = json.dumps(parsed, indent=2)
        result = result[:start] + pretty + result[end:]
        replaced = True

    return result if replaced else None
