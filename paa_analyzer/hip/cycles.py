"""Segment a stream of parsed log entries into HIP cycles, and pair them.

A "cycle" is one HIP report generation run by the Prisma Access Agent. It is
recognized purely by message content and timestamp — never by which log
rotation file an entry came from, since that information isn't available
once entries from PACompliance*.log / PAComplianceMp*.log rotations have
been collapsed and sorted into a single chronological entry stream.
"""

from __future__ import annotations

from typing import Any, TypedDict


class Cycle(TypedDict):
    start_ts: float | None
    entries: list[dict[str, Any]]
    partial: bool


_POLICY_LINE_PREFIX = "Try to parse hip policy"


def split_cycles(entries: list[dict[str, Any]]) -> list[Cycle]:
    """Split a chronological list of log entries into HIP cycles.

    A cycle starts at an entry whose `message` starts with
    "Try to parse hip policy" and runs up to (but not including) the next
    such entry. Its `start_ts` is that boundary entry's own `timestamp`.

    Entries appearing before the first policy-line boundary (e.g. a log that
    was truncated mid-cycle by rotation) form a single leading cycle with
    `partial=True`; its `start_ts` is the first entry's own timestamp, since
    there is no policy-line marker to anchor it.

    Returns [] for an empty `entries` list.
    """
    cycles: list[Cycle] = []
    current: list[dict[str, Any]] = []
    start_ts: float | None = None
    partial = True

    for entry in entries:
        message = entry.get("message") or ""
        if message.startswith(_POLICY_LINE_PREFIX):
            if current:
                cycles.append({"start_ts": start_ts, "entries": current, "partial": partial})
            current = [entry]
            start_ts = entry.get("timestamp")
            partial = False
        else:
            if not current:
                start_ts = entry.get("timestamp")
            current.append(entry)

    if current:
        cycles.append({"start_ts": start_ts, "entries": current, "partial": partial})

    return cycles


def pair_cycles(
    compliance_cycles: list[Cycle],
    mp_cycles: list[Cycle],
    tolerance_s: float = 5.0,
) -> tuple[list[tuple[Cycle, Cycle | None]], list[Cycle]]:
    """Pair each Mp cycle to its matching compliance cycle by start_ts.

    Returns `(pairs, unpaired_mp)`:

    - `pairs` has exactly one entry per `compliance_cycle`, in the same
      order as `compliance_cycles`: `(compliance_cycle, mp_cycle)` if a
      matching Mp cycle was found, else `(compliance_cycle, None)`.
    - `unpaired_mp` lists every Mp cycle that could not be matched — either
      no compliance cycle's `start_ts` was within `tolerance_s` seconds, or
      the closest one had already been claimed by an earlier Mp cycle, or
      the Mp cycle itself is `partial` (see below). Mp cycles are never
      silently dropped; every one lands in exactly one of `pairs` (as the
      matched half) or `unpaired_mp`.

    Mp cycles are processed in the order given. For each, the nearest
    not-yet-claimed compliance cycle within `tolerance_s` is claimed —
    ties broken by whichever compliance cycle comes first in
    `compliance_cycles`. Each compliance cycle takes at most one Mp cycle.
    A `start_ts` of None never matches (it can't be compared by distance).

    A `partial` Mp cycle (a rotation-truncated leading fragment with no
    policy-line boundary of its own -- see `split_cycles`) is never eligible
    to claim a pairing: its `start_ts` is just its first surviving entry's
    own timestamp, not a genuine cycle boundary, so it would otherwise
    compete for pairing on equal footing with a real cycle and could win it
    on proximity alone -- silently misattributing patches to the wrong
    compliance cycle while pushing the genuine Mp cycle into `unpaired_mp`
    with no signal that anything went wrong. It always lands in
    `unpaired_mp` instead.
    """
    unclaimed = {i for i, c in enumerate(compliance_cycles) if c.get("start_ts") is not None}
    assigned: dict[int, Cycle] = {}
    unpaired_mp: list[Cycle] = []

    for mp in mp_cycles:
        mp_ts = mp.get("start_ts")
        best_idx: int | None = None
        best_delta: float | None = None
        if mp_ts is not None and not mp.get("partial"):
            for idx in sorted(unclaimed):
                compliance_ts = compliance_cycles[idx]["start_ts"]
                if compliance_ts is None:
                    continue
                delta = abs(compliance_ts - mp_ts)
                if delta <= tolerance_s and (best_delta is None or delta < best_delta):
                    best_delta = delta
                    best_idx = idx
        if best_idx is not None:
            assigned[best_idx] = mp
            unclaimed.discard(best_idx)
        else:
            unpaired_mp.append(mp)

    pairs = [(c, assigned.get(idx)) for idx, c in enumerate(compliance_cycles)]
    return pairs, unpaired_mp
