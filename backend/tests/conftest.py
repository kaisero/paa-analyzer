"""Shared test fixtures for PAA Analyzer backend tests."""

from __future__ import annotations

import json
import zipfile
from io import BytesIO

import pytest
from starlette.testclient import TestClient

from backend.main import create_app
from backend.pipeline import parse_zip
from backend.store import store as global_store

# ── Sample data ───────────────────────────────────────────────────────────

SAMPLE_PACLI_STATUS = """\
State: Enabled
Mode: Always On
Tunnel: Connected
Captive Portal Status: Not Detected
Device Quarantine: Not Quarantined
EPM Status: Up
Username: testuser@example.com
Local Hostname: TEST-HOST
Current Time: 2026-04-04 22:18:34, GMT+0200
EPM Last Seen: 2026-04-04 22:17:43
Last Successful Configuration: 2026-04-04 20:33:44
GlobalProtect Status: Not Installed
"""

SAMPLE_PACLI_VERSION = """\
Version: 26.1.2.4
Commit SHA1: abc123
Commit Tag: release/26.1.2.4
Prelogin Uninstall Support: True
"""

SAMPLE_PACLI_TUNNEL = """\
Tunnel Status: Connected
"""

SAMPLE_PACLI_EP = """\
Global Explicit Proxy FQDN: pangp.proxy.prismaaccess.com
Global Explicit Proxy Port: 443
"""

SAMPLE_PACLI_ADNS = """\
State: ADNS disabled
"""

SAMPLE_PACLI_ADEM_STATUS = """\
State: Enabled
Version: 5.10.14
Tenant: 24072002
Sub Tenant: 24072002
Domain:
Lifecycle: Install
"""

SAMPLE_PACLI_DLP_STATUS = """\
DLP Status: Disabled
Enforcer Status: Not Running
Enforcer Version: Unknown
DLP Address: Not Available
DLP Token Creation: Not Available
DLP Token Expiry: Not Available
DLP Policies: Not Available
"""

SAMPLE_PACLI_TRAFFIC_SHOW = """\
Forwarding Profile
| Priority | Name                  | Enabled | Source Apps | Destinations          | Connection Type | Connect Through | Hits |
|----------|-----------------------|---------|------------|-----------------------|-----------------|-----------------|------|
| 0        | ImplicitForwardingRule| Yes     | Any        | Any                   | Data and DNS    | Direct          | 5    |
| 1        | Exclude-Video         | Yes     | Any        | Domain: "*.netflix.com"| Data and DNS    | Direct          | 10   |
| 3        | Default               | Yes     | Any        | Any                   | Data and DNS    | Best Available  | 100  |

Flags:
 X - Block outbound LAN when connected to tunnel
 X - Block inbound connections when connected to tunnel
"""

SAMPLE_PACLI_GATEWAYS_LIST = """\
Agent Location: AT

External Gateways
Name                     Priority Address
----                     -------- -------
US Northwest             5        us-northwest.gw.example.com
Austria                  1        austria.gw.example.com
"""

SAMPLE_PACLI_HIP_STATUS = """\
HIP Collection: Enabled
Next HIP Check: 2026-04-04 20:49:25

Gateway              Last HIP Report
-------              ---------------
Austria              2026-04-03 06:57:30
"""

SAMPLE_PACLI_PROTECT = """\
Protection Features
-------------------
Firewall Enabled
AV Enabled
DiskEncryption NotConfigured
"""

SAMPLE_SW_VERS = """\
ProductName: macOS
ProductVersion: 26.2
BuildVersion: 25C56
"""

SAMPLE_UNAME = "Darwin TEST-HOST 25.2.0 Darwin Kernel Version 25.2.0 arm64"

SAMPLE_EXTERNAL_IP = '{"origin": "1.2.3.4"}'

SAMPLE_TRAFFIC_JSON = "Network connection log:\n" + json.dumps(
    [
        {
            "index": 1001,
            "timeAndDate": "2026-04-03 09:24:40",
            "destination": "example.com:443",
            "protocol": "TCP",
            "verdict": "Tunnel",
            "sourceApp": "/Applications/Chrome.app/Contents/MacOS/Google Chrome",
            "reason": "Rule priority 3 matched, setting verdict to Tunnel",
            "trafficType": "kData",
        },
        {
            "index": 1002,
            "timeAndDate": "2026-04-03 09:24:41",
            "destination": "netflix.com:443",
            "protocol": "TCP",
            "verdict": "Direct",
            "sourceApp": "/Applications/Safari.app/Contents/MacOS/Safari",
            "reason": "Rule priority 1 matched, setting verdict to Direct",
            "trafficType": "kData",
        },
        {
            "index": 1003,
            "timeAndDate": "2026-04-03 09:24:42",
            "destination": "google.com:443",
            "protocol": "TCP",
            "verdict": "Tunnel",
            "sourceApp": "/Applications/Chrome.app/Contents/MacOS/Google Chrome",
            "reason": "Rule priority 3 matched, setting verdict to Tunnel",
            "trafficType": "kData",
        },
    ]
)


SAMPLE_ROUTING = """\
Routing tables

Internet:
Destination        Gateway            Flags               Netif Expire
default            198.18.1.1         UGScg                 en0
10.0.0.0/8         198.18.1.1         UGSc                  en0
127.0.0.1          127.0.0.1          UH                    lo0

Internet6:
Destination        Gateway            Flags               Netif Expire
::1                ::1                UHL                   lo0
fe80::%lo0/64      fe80::1%lo0        UcI                   lo0
"""

SAMPLE_LAUNCHCTL_LIST = """\
PID\tStatus\tLabel
-\t0\tcom.apple.Spotlight
1234\t0\tcom.paloaltonetworks.gp.pangps
-\t78\tcom.apple.SafariBookmarksSyncAgent
5678\t0\tcom.paloaltonetworks.gp.pangpa
"""

SAMPLE_SYSTEM_EXTENSIONS = """\
--- com.apple.system_extension.network_extension
enabled\tactive\tteamID\tbundleID (version)\tname\t[state]
*\t*\tPALO_ID\tcom.paloaltonetworks.GlobalProtect.network-extension (26.1.2)\tGlobalProtect Network Extension\t[activated enabled]
*\t*\tAPPLE_ID\tcom.apple.networkextension (1.0)\tNetwork Extension\t[activated enabled]
--- com.apple.system_extension.endpoint_security
enabled\tactive\tteamID\tbundleID (version)\tname\t[state]
*\t-\tPALO_ID\tcom.paloaltonetworks.GlobalProtect.endpoint-security (26.1.2)\tGlobalProtect Endpoint Security\t[terminated]
"""

SAMPLE_DEM_LOG = (
    "2026-04-03 11:08:50.885+0000 - info: shouldPrismaAccessAgentApiBeUsed() "
    "Prisma Access Agent is enabled\n"
    "2026-04-03 11:08:50.886+0000 - warning: Retrieving WiFi snapshot failed\n"
)

SAMPLE_DLP_LOG = "2026/01/08 16:27:19:278  DLPLogger init completed\n2026/01/08 16:27:20:100  DLPLog Logger started\n"

SAMPLE_DLP_NETFILTER = (
    "[2026-01-08 16:27:19] [INFO] [path/to/file.mm:72] IPC Server running\n"
    "[2026-02-09 22:29:39] [DEBUG] [path/to/file.mm:72] Connection established\n"
)

SAMPLE_CONNECTION_HISTORY = """\
Connection History:

Connection #98:
  1. [2026-03-31 09:24:58] Starting connection attempt (best gateway available)
  2. [2026-03-31 09:24:58] Attempting a connection to gateway "Austria"
  3. [2026-03-31 09:25:03] Connected successfully to "Austria" gateway

Connection #99:
  1. [2026-03-31 10:00:00] Starting connection attempt
  2. [2026-03-31 10:00:02] Failed to establish IPSEC tunnel with "US" gateway
  3. [2026-03-31 10:00:03] Could not raise tunnel of any kind with "US" gateway
"""

SAMPLE_EVENT_TABLE = """\
Id          Local Time           Event Type              Details
----------- -------------------- ----------------------- ------
126273      2026-04-02 00:51:26  Tamper Detection        Sprot: blocking read dir event
126274      2026-04-02 00:53:28  Configuration Change    Config updated successfully
"""

SAMPLE_EPM_COMMANDS = """\
ID                                   Command           State     Priority Retry Received            Finished
d59cb947-6969-49ab-a80b-64a647039159 Get Configuration Completed 0        0     2026-03-24 02:51:45 2026-03-24 02:51:47
"""

SAMPLE_TRAFFIC_RDNS = json.dumps(
    {
        "ReverseDnsCache": {
            "cname_record": [{"cname": "sas.apple.com", "hostnames": ["sas.pcms.apple.com"]}],
            "ip_record": [{"ip": "1.2.3.4", "hostnames": ["example.com"]}],
        }
    }
)

SAMPLE_REMOTE_SHELL = (
    "2026-03-18T12:43:10.990+01:00 | INFO     | 63397 | MainThread       "
    "| remote_shell | Starting ZTNA Remote Shell v24.5\n"
    "2026-03-18T12:43:11.100+01:00 | DEBUG    | 63397 | MainThread       "
    "| remote_shell | Configuration loaded\n"
)

SAMPLE_PAS_LOG = (
    "2026-04-03T09:24:40.100+02:00 <info> TEST-HOST [1234:5678] "
    "Plain message without JSON\n"
    "2026-04-03T09:24:41.200+02:00 <info> TEST-HOST [1234:5678] "
    'Received config: {"server":"epm.example.com","port":443,"features":["tunnel","dlp"]}\n'
    "2026-04-03T09:24:42.300+02:00 <error> TEST-HOST [1234:5678] "
    "Connection failed\n"
)


def build_sample_zip() -> bytes:
    """Build a minimal troubleshooting ZIP with representative files."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # Pacli Output files
        zf.writestr("Pacli Output/pacli_status.log", SAMPLE_PACLI_STATUS)
        zf.writestr("Pacli Output/pacli_version.log", SAMPLE_PACLI_VERSION)
        zf.writestr("Pacli Output/pacli_tunnel.log", SAMPLE_PACLI_TUNNEL)
        zf.writestr("Pacli Output/pacli_ep.log", SAMPLE_PACLI_EP)
        zf.writestr("Pacli Output/pacli_adns.log", SAMPLE_PACLI_ADNS)
        zf.writestr("Pacli Output/pacli_adem_status.log", SAMPLE_PACLI_ADEM_STATUS)
        zf.writestr("Pacli Output/pacli_dlp_status.log", SAMPLE_PACLI_DLP_STATUS)
        zf.writestr("Pacli Output/pacli_traffic_show.log", SAMPLE_PACLI_TRAFFIC_SHOW)
        zf.writestr("Pacli Output/pacli_gateways_list.log", SAMPLE_PACLI_GATEWAYS_LIST)
        zf.writestr("Pacli Output/pacli_hip_status.log", SAMPLE_PACLI_HIP_STATUS)
        zf.writestr("Pacli Output/pacli_protect.log", SAMPLE_PACLI_PROTECT)
        # System info files
        zf.writestr("sw_vers.txt", SAMPLE_SW_VERS)
        zf.writestr("uname.txt", SAMPLE_UNAME)
        zf.writestr("external_ip.txt", SAMPLE_EXTERNAL_IP)
        zf.writestr("routing.txt", SAMPLE_ROUTING)
        zf.writestr("launchctl_list.txt", SAMPLE_LAUNCHCTL_LIST)
        zf.writestr("system_extension_list.txt", SAMPLE_SYSTEM_EXTENSIONS)
        # Traffic log (log type, not state)
        zf.writestr("traffic_log_json.txt", SAMPLE_TRAFFIC_JSON)
        # Structured log with embedded JSON
        zf.writestr("Logs/System/PAS.log", SAMPLE_PAS_LOG)
    return buf.getvalue()


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def real_zip_bytes():
    """Load the real macOS example ZIP. Skipped if not present."""
    from pathlib import Path

    zip_path = Path(__file__).parent.parent.parent / "examples" / "paa_macos_example.zip"
    if not zip_path.exists():
        pytest.skip("Real example ZIP not available")
    return zip_path.read_bytes()


@pytest.fixture(scope="module")
def real_parsed_result(real_zip_bytes):
    """Parse the real macOS example ZIP (cached per module)."""
    return parse_zip(real_zip_bytes)


@pytest.fixture(scope="module")
def win_zip_bytes():
    """Load the real Windows example ZIP. Skipped if not present."""
    from pathlib import Path

    zip_path = Path(__file__).parent.parent.parent / "examples" / "pa_windows_example.zip"
    if not zip_path.exists():
        pytest.skip("Windows example ZIP not available")
    return zip_path.read_bytes()


@pytest.fixture(scope="module")
def win_parsed_result(win_zip_bytes):
    """Parse the real Windows example ZIP (cached per module)."""
    return parse_zip(win_zip_bytes)


@pytest.fixture
def sample_zip_bytes() -> bytes:
    return build_sample_zip()


@pytest.fixture
def parsed_result(sample_zip_bytes: bytes) -> dict:
    """Run parse_zip directly and return the result."""
    return parse_zip(sample_zip_bytes)


@pytest.fixture
def app_client() -> TestClient:
    """Fresh FastAPI test client with a clean store."""
    app = create_app()
    yield TestClient(app)
    # Clean up the global store after each test
    global_store._sessions.clear()
    for conn in global_store._dbs.values():
        conn.close()
    global_store._dbs.clear()
    global_store._log_meta.clear()
    global_store._state.clear()


@pytest.fixture
def session_id(app_client: TestClient, sample_zip_bytes: bytes) -> str:
    """Upload a sample ZIP and return the session ID."""
    resp = app_client.post(
        "/api/v1/sessions",
        files={"file": ("test.zip", sample_zip_bytes, "application/zip")},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]
