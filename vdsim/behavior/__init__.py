"""Behavior planning layer: rule-based state machine (lane keeping/change, merging, overtaking, junctions, parking)."""

from ..framework.plugins import component
from .params import RuleBasedParams
from .rule_based import RuleBasedBehavior

component(RuleBasedBehavior)

__all__ = ["RuleBasedBehavior", "RuleBasedParams"]
