"""HIP (Host Information Profile) domain model, layered on top of parsers.py.

Turns already-parsed PACompliance*/PAComplianceMp* log entries (plain dicts
from parsers.structured_log()) into a structured HIP-cycle domain model:
policy, per-category OPSWAT results, missing patches, and dispatch status.
"""
