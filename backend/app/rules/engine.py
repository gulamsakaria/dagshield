"""Rule registry and audit runner. Same input always gives the same output."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from . import r1_overlap, r2_entitlement, r3_reconcile, r4_lineage, r5_rapid
from .findings import Finding
from .models import Dataset, RuleParams


@dataclass(frozen=True)
class RuleInfo:
    rule_id: str
    version: str
    title: str
    priority: str
    run: Callable[[Dataset, RuleParams], list[Finding]]


REGISTRY: tuple[RuleInfo, ...] = (
    RuleInfo(r1_overlap.RULE_ID, r1_overlap.VERSION, r1_overlap.TITLE, "P0", r1_overlap.run),
    RuleInfo(r2_entitlement.RULE_ID, r2_entitlement.VERSION, r2_entitlement.TITLE, "P0", r2_entitlement.run),
    RuleInfo(r3_reconcile.RULE_ID, r3_reconcile.VERSION, r3_reconcile.TITLE, "P0", r3_reconcile.run),
    RuleInfo(r4_lineage.RULE_ID, r4_lineage.VERSION, r4_lineage.TITLE, "P0", r4_lineage.run),
    RuleInfo(r5_rapid.RULE_ID, r5_rapid.VERSION, r5_rapid.TITLE, "P1", r5_rapid.run),
)


def run_audit(ds: Dataset, params: RuleParams | None = None) -> list[Finding]:
    """Run every enabled rule and return findings in a deterministic order."""
    params = params or RuleParams()
    findings: list[Finding] = []
    for rule in REGISTRY:
        if rule.rule_id == "R5" and not params.enable_r5:
            continue
        findings.extend(rule.run(ds, params))
    return sorted(findings, key=lambda f: (f.rule_id, f.key, f.outcome))
