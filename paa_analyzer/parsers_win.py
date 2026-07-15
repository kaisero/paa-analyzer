"""Windows-specific parsers for Machine Info files and Windows log formats."""

from __future__ import annotations

import contextlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from paa_analyzer.parsers import format_ts, parse_ts

# ── Machine Info state parsers ────────────────────────────────────────────


def systeminfo(text: str, **_) -> dict:
    """Parse Windows `systeminfo` output into key-value dict.

    Handles multi-line indented continuations (e.g., Processor(s), Hotfix(s), Network Card(s)).
    """
    data: dict[str, str | list[str]] = {}
    current_key = ""
    list_items: list[str] = []

    for line in text.splitlines():
        if not line.strip():
            continue
        # Check if this is a key: value line (key starts at column 0, value after colon)
        m = re.match(r"^([A-Za-z][A-Za-z0-9 /()]+?):\s+(.*)", line)
        if m:
            # Save previous list if any
            if list_items and current_key:
                data[current_key] = list_items
                list_items = []
            key = re.sub(r"[^a-z0-9]+", "_", m.group(1).lower()).strip("_")
            val = m.group(2).strip()
            current_key = key
            data[key] = val
        elif line.startswith("                               [") or line.startswith("                 "):
            # Continuation/list item
            item = line.strip()
            if item.startswith("["):
                # Numbered list item like [01]: KB5074828
                list_items.append(item)
            elif current_key and isinstance(data.get(current_key), str):
                # Multi-line value continuation (e.g., NIC details)
                data[current_key] = data[current_key] + " " + item if data[current_key] else item

    if list_items and current_key:
        data[current_key] = list_items

    return data


def ipconfig(text: str, **_) -> dict:
    """Parse Windows `ipconfig /all` output into structured sections."""
    result: dict = {"global": {}, "adapters": []}
    current_adapter: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Adapter header (no leading spaces, ends with colon)
        if not line.startswith(" ") and stripped.endswith(":") and ". . ." not in line:
            if "Windows IP Configuration" in stripped:
                continue
            if current_adapter:
                result["adapters"].append(current_adapter)
            current_adapter = {"name": stripped.rstrip(":")}
            continue

        # Key-value with dots separator
        m = re.match(r"^\s+(.+?)\s*\. \.+ :\s*(.*)", line)
        if m:
            key = re.sub(r"[^a-z0-9]+", "_", m.group(1).lower()).strip("_")
            val = m.group(2).strip()
            # Clean up IPv4/IPv6 suffixes like (Preferred)
            val = re.sub(r"\(Preferred\)|\(Deprecated\)", "", val).strip()
            target = current_adapter if current_adapter else result["global"]
            if key in target:
                # Multiple values (e.g., multiple DNS servers, IPv6 addresses)
                existing = target[key]
                if isinstance(existing, list):
                    existing.append(val)
                else:
                    target[key] = [existing, val]
            else:
                target[key] = val
        elif current_adapter and stripped and not stripped.startswith("="):
            # Continuation value (indented line without dots, e.g., additional gateway)
            # Find the last key and append
            pass

    if current_adapter:
        result["adapters"].append(current_adapter)
    return result


def win_routing_table(text: str, **_) -> dict:
    """Parse Windows `route print` output.

    IPv4 format: Network Destination  Netmask  Gateway  Interface  Metric
    IPv6 format: If  Metric  Network Destination  Gateway
    IPv6 entries can span two lines when the destination is long.
    """
    result: dict = {"interfaces": [], "ipv4": [], "ipv6": []}
    section = ""
    # Build interface index → name lookup
    iface_names: dict[int, str] = {}
    # For IPv6 multi-line continuation
    pending_ipv6: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("="):
            # Separator line — flush any pending IPv6 entry
            if pending_ipv6:
                result["ipv6"].append(pending_ipv6)
                pending_ipv6 = None
            continue

        if "Interface List" in stripped:
            section = "interfaces"
            continue
        elif "IPv4 Route Table" in stripped:
            section = "ipv4"
            continue
        elif "IPv6 Route Table" in stripped:
            if pending_ipv6:
                result["ipv6"].append(pending_ipv6)
                pending_ipv6 = None
            section = "ipv6"
            continue
        elif (
            "Active Routes:" in stripped
            or "Persistent Routes:" in stripped
            or stripped.startswith("Network Destination")
            or stripped.startswith("If Metric")
            or stripped == "None"
        ):
            continue

        if section == "interfaces":
            # Format: "  6...bc 24 11 2d ac 0f ......Red Hat VirtIO Ethernet Adapter"
            m = re.match(r"\s*(\d+)\.{3}([0-9a-f ]+)\.{4,}(.+)", stripped)
            if m:
                idx = int(m.group(1))
                name = m.group(3).strip()
                iface_names[idx] = name
                result["interfaces"].append(
                    {
                        "index": idx,
                        "mac": m.group(2).strip().replace(" ", ":") if m.group(2).strip() else None,
                        "name": name,
                    }
                )
            elif re.match(r"\s*\d+\.\.\.", stripped):
                m2 = re.match(r"\s*(\d+)\.+(.+)", stripped)
                if m2:
                    idx = int(m2.group(1))
                    name = m2.group(2).strip()
                    iface_names[idx] = name
                    result["interfaces"].append(
                        {
                            "index": idx,
                            "mac": None,
                            "name": name,
                        }
                    )

        elif section == "ipv4":
            parts = stripped.split()
            if len(parts) >= 5:
                try:
                    metric = int(parts[-1])
                    result["ipv4"].append(
                        {
                            "destination": parts[0],
                            "netmask": parts[1],
                            "gateway": parts[2],
                            "interface": parts[3],
                            "metric": metric,
                        }
                    )
                except ValueError:
                    pass

        elif section == "ipv6":
            # IPv6 format: "  If  Metric  Network Destination  Gateway"
            # Example:     "  6     31 ::/0                     fe80::602b:33ff:fefd:aa08"
            # Multi-line:  "  6    271 2001:4bc9:b003:b117:5f90:91c:fff:186d/128"
            #              "                                    On-link"
            parts = line.split()

            # Check if this is a continuation line (gateway for the previous entry)
            # Continuation lines are heavily indented and contain only the gateway
            if pending_ipv6 and len(parts) == 1 and not parts[0][0].isdigit():
                pending_ipv6["gateway"] = parts[0]
                result["ipv6"].append(pending_ipv6)
                pending_ipv6 = None
                continue

            # Flush any pending entry without a gateway continuation
            if pending_ipv6:
                result["ipv6"].append(pending_ipv6)
                pending_ipv6 = None

            # Parse new IPv6 route line
            if len(parts) >= 3:
                try:
                    if_idx = int(parts[0])
                    metric = int(parts[1])
                except ValueError:
                    continue
                destination = parts[2]
                gateway = parts[3] if len(parts) > 3 else ""
                iface_name = iface_names.get(if_idx, str(if_idx))

                entry = {
                    "destination": destination,
                    "gateway": gateway,
                    "interface": iface_name,
                    "metric": metric,
                }

                if gateway:
                    # Complete entry on one line
                    result["ipv6"].append(entry)
                else:
                    # Gateway will be on the next line
                    pending_ipv6 = entry

    # Flush any remaining pending entry
    if pending_ipv6:
        result["ipv6"].append(pending_ipv6)

    return result


def win_firewall_rules(text: str, **_) -> dict:
    """Parse Windows firewall rules JSON export."""
    try:
        data = json.loads(text)
        if isinstance(data, list):
            rules = data
        elif isinstance(data, dict):
            rules = data.get("rules", [])
        else:
            rules = []
        return {"rules": rules, "total": len(rules)}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON", "rules": []}


def win_installed_apps(text: str, **_) -> list[dict]:
    """Parse PowerShell Get-Package table output."""
    apps = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("Name") or stripped.startswith("----"):
            continue
        # Fixed-width: Name (28 chars), Version
        parts = re.split(r"\s{2,}", stripped)
        if len(parts) >= 2:
            apps.append({"name": parts[0].strip(), "version": parts[1].strip()})
    return apps


def win_installed_drivers(text: str, **_) -> list[dict]:
    """Parse `driverquery /v` fixed-width output using separator line for column positions."""
    drivers = []
    col_positions: list[tuple[int, int]] = []

    for line in text.splitlines():
        # Find separator line (=====) to determine column positions
        if line.startswith("=") and " " in line:
            pos = 0
            for col in line.split(" "):
                if col:
                    col_positions.append((pos, pos + len(col)))
                    pos += len(col) + 1
                else:
                    pos += 1
            continue

        if not line.strip() or line.strip().startswith("Module Name"):
            continue

        if col_positions and len(col_positions) >= 7:

            def _col(idx: int, line: str = line) -> str:
                if idx < len(col_positions):
                    start, end = col_positions[idx]
                    return line[start:end].strip() if start < len(line) else ""
                return ""

            module = _col(0)
            if module:
                drivers.append(
                    {
                        "module": module,
                        "display_name": _col(1),
                        "driver_type": _col(3),
                        "start_mode": _col(4),
                        "state": _col(5),
                        "status": _col(6),
                    }
                )
    return drivers


def win_netstat(text: str, **_) -> dict:
    """Parse Windows `netstat -ab` output with process names."""
    connections: list[dict] = []
    current: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or "Active Connections" in stripped:
            continue
        if stripped.startswith("Proto") or stripped.startswith("---"):
            continue

        # Connection line: "  TCP    0.0.0.0:135    0.0.0.0:0    LISTENING"
        m = re.match(r"\s+(TCP|UDP)\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if m:
            if current:
                connections.append(current)
            current = {
                "proto": m.group(1),
                "local_address": m.group(2),
                "foreign_address": m.group(3),
                "state": m.group(4),
                "process": "",
            }
        elif current and stripped.startswith("["):
            # Process name line: " [svchost.exe]"
            current["process"] = stripped.strip("[]")
        elif current and not stripped.startswith("Can not"):
            # Service name line (no brackets)
            if current["process"]:
                current["process"] += f" ({stripped})"
            else:
                current["process"] = stripped

    if current:
        connections.append(current)
    return {"connections": connections}


def win_dns_cache(text: str, **_) -> list[dict]:
    """Parse `ipconfig /displaydns` output into DNS record entries."""
    records: list[dict] = []
    current: dict = {}

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or "Windows IP Configuration" in stripped:
            continue
        if stripped.startswith("---"):
            if current and "record_name" in current:
                records.append(current)
            current = {}
            continue

        m = re.match(r"(.+?)\s*\.\s*\.+ :\s*(.*)", stripped)
        if m:
            key = re.sub(r"[^a-z0-9]+", "_", m.group(1).lower()).strip("_")
            current[key] = m.group(2).strip()
        elif not stripped.startswith("=") and "record_name" not in current and stripped:
            # Hostname header line
            current["hostname"] = stripped

    if current and "record_name" in current:
        records.append(current)
    return records


def win_user_groups(text: str, **_) -> list[dict]:
    """Parse `whoami /groups` table output."""
    groups: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("GROUP") or stripped.startswith("=") or stripped.startswith("---"):
            continue
        if stripped.startswith("Group Name"):
            continue
        parts = re.split(r"\s{2,}", stripped)
        if len(parts) >= 3:
            groups.append(
                {
                    "group_name": parts[0].strip(),
                    "type": parts[1].strip(),
                    "sid": parts[2].strip(),
                    "attributes": parts[3].strip() if len(parts) > 3 else "",
                }
            )
    return groups


def win_user_sessions(text: str, **_) -> list[dict]:
    """Parse `query session` output."""
    sessions: list[dict] = []
    for line in text.splitlines():
        stripped = line.lstrip(">").strip()
        if not stripped or stripped.startswith("SESSIONNAME"):
            continue
        # Fixed-width columns
        parts = stripped.split()
        if len(parts) >= 3:
            # Try to find the numeric ID
            id_idx = next((i for i, p in enumerate(parts) if p.isdigit()), -1)
            if id_idx >= 0:
                sessions.append(
                    {
                        "session_name": parts[0] if id_idx > 0 else "",
                        "username": parts[1] if id_idx > 1 else "",
                        "id": int(parts[id_idx]),
                        "state": parts[id_idx + 1] if id_idx + 1 < len(parts) else "",
                    }
                )
    return sessions


def win_powercfg(text: str, **_) -> dict:
    """Parse `powercfg /availablesleepstates` output."""
    states: list[dict] = []
    current_state = ""
    reasons: list[str] = []

    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("The following"):
            continue
        # State header (4 spaces indent)
        m = re.match(r"    (\w.+?)$", line)
        if m and not line.startswith("\t"):
            if current_state:
                states.append({"state": current_state, "reasons": reasons})
            current_state = m.group(1).strip()
            reasons = []
        elif line.startswith("\t") and current_state:
            reasons.append(line.strip())

    if current_state:
        states.append({"state": current_state, "reasons": reasons})
    return {"sleep_states": states}


def win_powercfg_query(text: str, **_) -> dict:
    """Parse `powercfg /query` power scheme output."""
    result: dict = {"scheme_name": "", "scheme_guid": "", "subgroups": []}
    current_subgroup: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()
        m = re.match(r"Power Scheme GUID:\s+(\S+)\s+\((.+)\)", stripped)
        if m:
            result["scheme_guid"] = m.group(1)
            result["scheme_name"] = m.group(2)
            continue
        m = re.match(r"Subgroup GUID:\s+(\S+)\s+\((.+)\)", stripped)
        if m:
            if current_subgroup:
                result["subgroups"].append(current_subgroup)
            current_subgroup = {"guid": m.group(1), "name": m.group(2), "settings": []}
            continue
        m = re.match(r"Power Setting GUID:\s+(\S+)\s+\((.+)\)", stripped)
        if m and current_subgroup is not None:
            current_subgroup["settings"].append({"guid": m.group(1), "name": m.group(2)})

    if current_subgroup:
        result["subgroups"].append(current_subgroup)
    return result


def win_power_history(text: str, **_) -> list[dict]:
    """Parse PowerShell event log export (Get-WinEvent style)."""
    events: list[dict] = []
    current_provider = ""

    for line in text.splitlines():
        stripped = line.strip()
        m = re.match(r"ProviderName:\s+(.+)", stripped)
        if m:
            current_provider = m.group(1).strip()
            continue
        if stripped.startswith("TimeCreated") or stripped.startswith("---"):
            continue
        if not stripped:
            continue
        # Event line: "4/8/2026 10:39:29 AM 16 Information      The access history..."
        m = re.match(r"(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)\s+(\d+)\s+(\S+)\s+(.*)", stripped)
        if m:
            ts_str = m.group(1)
            try:
                dt = datetime.strptime(ts_str, "%m/%d/%Y %I:%M:%S %p")
                ts = dt.replace(tzinfo=UTC).timestamp()
            except ValueError:
                ts = None
            events.append(
                {
                    "provider": current_provider,
                    "timestamp": format_ts(ts),
                    "event_id": int(m.group(2)),
                    "level": m.group(3).lower(),
                    "message": m.group(4).strip(),
                }
            )
    return events


def win_nslookup(text: str, **_) -> dict:
    """Parse nslookup output."""
    result: dict = {"server": "", "server_address": "", "name": "", "addresses": []}
    in_answer = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Server:"):
            result["server"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Address:") and not in_answer:
            result["server_address"] = stripped.split(":", 1)[1].strip()
            continue
        elif stripped.startswith("Name:"):
            result["name"] = stripped.split(":", 1)[1].strip()
            in_answer = True
        elif stripped.startswith("Addresses:"):
            addr = stripped.split(":", 1)[1].strip()
            if addr:
                result["addresses"].append(addr)
        elif in_answer and stripped and not stripped.startswith("Aliases"):
            result["addresses"].append(stripped)
    return result


def win_ping(text: str, **_) -> dict:
    """Parse Windows ping output."""
    result: dict = {"target": "", "replies": [], "stats": {}}

    for line in text.splitlines():
        stripped = line.strip()
        m = re.match(r"Pinging (\S+)", stripped)
        if m:
            result["target"] = m.group(1)
        m = re.match(r"Reply from (\S+):\s+bytes=(\d+)\s+time[=<](\d+)ms\s+TTL=(\d+)", stripped)
        if m:
            result["replies"].append(
                {
                    "from": m.group(1).rstrip(":"),
                    "bytes": int(m.group(2)),
                    "time_ms": int(m.group(3)),
                    "ttl": int(m.group(4)),
                }
            )
        m = re.match(r"Packets: Sent = (\d+), Received = (\d+), Lost = (\d+)", stripped)
        if m:
            result["stats"]["sent"] = int(m.group(1))
            result["stats"]["received"] = int(m.group(2))
            result["stats"]["lost"] = int(m.group(3))
        m = re.match(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", stripped)
        if m:
            result["stats"]["min_ms"] = int(m.group(1))
            result["stats"]["max_ms"] = int(m.group(2))
            result["stats"]["avg_ms"] = int(m.group(3))
    return result


def win_event_viewer(text: str, **_) -> list[dict]:
    """Parse PowerShell XML event log export (CLIXML Objects format)."""
    events: list[dict] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return events

    for obj in root.iter("Object"):
        event: dict = {}
        for prop in obj.findall("Property"):
            name = prop.get("Name", "")
            value = prop.text or ""
            if name == "Message":
                event["message"] = value.strip()
            elif name == "Id":
                with contextlib.suppress(ValueError):
                    event["event_id"] = int(value)
            elif name == "Level":
                # Level is numeric in XML: 1=Critical, 2=Error, 3=Warning, 4=Information
                try:
                    level_num = int(value)
                    event["level"] = {1: "critical", 2: "error", 3: "warning", 4: "information"}.get(
                        level_num, str(level_num)
                    )
                except ValueError:
                    pass
            elif name == "ProviderName":
                event["provider"] = value
            elif name == "LogName":
                event["log_name"] = value
            elif name == "TimeCreated":
                event["time_created"] = value
        if event:
            events.append(event)
    return events


# ── Windows log parsers ───────────────────────────────────────────────────

_WIN_PAUI = re.compile(r"^PAUI\s+(\w+):\s+\d+\s+:\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})\s+(.*)")


def win_paui_log(text: str, tz=None, source: str = "", source_file: str = "", **_) -> list[dict]:
    """Parse Windows PAUI log format: 'PAUI Level: N : MM/DD/YYYY HH:MM:SS message'."""
    entries: list[dict] = []
    for line in text.splitlines():
        m = _WIN_PAUI.match(line)
        if m:
            level = m.group(1).lower()
            ts_str = m.group(2)
            msg = m.group(3)
            # Parse US date format MM/DD/YYYY HH:MM:SS
            try:
                dt = datetime.strptime(ts_str, "%m/%d/%Y %H:%M:%S")
                # Apply timezone from pacli_status if available
                if tz:
                    tz_m = re.match(r"([+-])(\d{2})(\d{2})", tz)
                    if tz_m:
                        from datetime import timedelta

                        off = timedelta(hours=int(tz_m.group(2)), minutes=int(tz_m.group(3)))
                        if tz_m.group(1) == "-":
                            off = -off
                        from datetime import timezone as tz_cls

                        ts = dt.replace(tzinfo=tz_cls(off)).timestamp()
                    else:
                        ts = dt.replace(tzinfo=UTC).timestamp()
                else:
                    ts = dt.replace(tzinfo=UTC).timestamp()
            except ValueError:
                ts = None
            entries.append({"timestamp": ts, "level": sys.intern(level), "message": msg})
    return entries


_WIN_DEM = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]\s+\[(\w+)\]\s+\[(\w+)\]\s+(.*)")


def win_dem_log(text: str, source: str = "", source_file: str = "", **_) -> list[dict]:
    """Parse Windows DEM log: '[YYYY-MM-DD HH:MM:SS.mmm] [source] [level] message'."""
    entries: list[dict] = []
    current: dict | None = None
    for line in text.split("\n"):
        line = line.rstrip("\r")
        m = _WIN_DEM.match(line)
        if m:
            if current:
                entries.append(current)
            current = {
                "timestamp": parse_ts(f"[{m.group(1)}]"),
                "level": sys.intern(m.group(3).lower()),
                "message": m.group(4),
            }
        elif current and line and not line.startswith("["):
            # Continuation line (e.g., stack traces)
            current["message"] += "\n" + line
    if current:
        entries.append(current)
    return entries


_CHROMIUM_LOG = re.compile(r"^\[(\d+:\d+:(\d{4})/(\d{6}\.\d{3})):(\w+\d?):(.+?)\]\s*(.*)")


def chromium_log(text: str, source: str = "", source_file: str = "", **_) -> list[dict]:
    """Parse Chromium log: '[pid:tid:MMDD/HHMMSS.ms:LEVEL:file.cc(line)] message'."""
    entries: list[dict] = []
    for line in text.splitlines():
        m = _CHROMIUM_LOG.match(line)
        if m:
            date_part = m.group(2)  # MMDD
            time_part = m.group(3)  # HHMMSS.mmm
            level_raw = m.group(4)  # WARNING, VERBOSE1, ERROR, etc.
            source_loc = m.group(5)  # file.cc(line)
            msg = m.group(6)

            # Parse timestamp (no year — use current year context)
            try:
                month = int(date_part[:2])
                day = int(date_part[2:])
                hour = int(time_part[:2])
                minute = int(time_part[2:4])
                sec = int(time_part[4:6])
                ms = int(time_part[7:10]) if len(time_part) > 6 else 0
                # Use 2026 as reasonable default
                dt = datetime(2026, month, day, hour, minute, sec, ms * 1000, tzinfo=UTC)
                ts = dt.timestamp()
            except (ValueError, IndexError):  # fmt: skip  # ruff@0.15 py314 miscompiles tuple-except
                ts = None

            # Normalize level
            level = level_raw.lower()
            if level.startswith("verbose"):
                level = "debug"

            entries.append(
                {
                    "timestamp": ts,
                    "level": sys.intern(level),
                    "message": f"[{source_loc}] {msg}",
                }
            )
    return entries
