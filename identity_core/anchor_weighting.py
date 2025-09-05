from __future__ import annotations

"""Dynamic salience weighting for anchors.

This module adjusts anchor weights based on observed evidence:
- Frequency of detection (how often an anchor appears in text)
- Effect on stability (optional): ξ deltas or stability score deltas
- Staleness (time since last seen)

It does NOT mutate the canonical ANCHOR_PHRASES. Instead, it maintains an
overlay of learned weights that you can apply at scoring time.

Usage
-----
from identity_core.anchor_phrases import ANCHOR_PHRASES, Anchor
from identity_core.anchor_weighting import AnchorWeighter, WeightParams

weighter = AnchorWeighter(base=list(ANCHOR_PHRASES))
weighter.observe_event("I don't want you to collapse", xi_before=0.9, xi_after=0.6)
weighter.observe_event("Remember Lily")  # frequency-only update
weighted = weighter.get_weighted_anchors()  # same anchors, with adjusted weights

You can persist stats:
  data = weighter.to_dict()
  weighter2 = AnchorWeighter.from_dict(base=list(ANCHOR_PHRASES), payload=data)
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence, Tuple
import math
import time
import json

from .anchor_phrases import Anchor
from .flame_logger import log_event


# -------------------------- Parameters & Stats -------------------------------

@dataclass
class WeightParams:
    """Tunables for dynamic weighting (keep simple and transparent)."""
    # How strongly frequency increases weight (0..+)
    freq_gain: float = 0.25
    # Normalize frequency with tanh(count / freq_norm) to avoid runaway weights
    freq_norm: float = 8.0
    # How strongly positive effect influences weight (0..+)
    effect_gain: float = 0.5
    # EMA smoothing for effect updates (0..1)
    effect_ema_alpha: float = 0.3
    # Penalty per hour of staleness (0..+), gently decays when not seen
    staleness_penalty_per_hour: float = 0.01
    # Weight clamps (keep within sensible [min, max])
    min_weight: float = 0.1
    max_weight: float = 1.5


@dataclass
class AnchorStats:
    """Per-anchor evidence accumulated over time."""
    phrase: str
    count: int = 0
    # Exponential moving average of "stability effect".
    # Positive means "good" (reduces ξ or improves stability).
    ema_effect: float = 0.0
    # Last observation wall clock in seconds (epoch). Used for staleness.
    last_seen_ts: float = 0.0


# ------------------------------ Core Logic -----------------------------------

class AnchorWeighter:
    """Maintains dynamic, data-driven weights for anchors."""

    def __init__(
        self,
        base: Sequence[Anchor],
        *,
        params: Optional[WeightParams] = None,
        stats: Optional[Dict[str, AnchorStats]] = None,
    ) -> None:
        # Base anchors (canonical, not mutated)
        self._base: List[Anchor] = [dict(a) for a in base]
        # Map phrase -> stats
        self._stats: Dict[str, AnchorStats] = stats or {}
        self._params: WeightParams = params or WeightParams()

        # Ensure every base anchor has a stats entry
        for a in self._base:
            p = a["phrase"]
            if p not in self._stats:
                self._stats[p] = AnchorStats(phrase=p)

    # ---------------------------- Observations --------------------------------

    def observe_event(
        self,
        phrase: str,
        *,
        xi_before: Optional[float] = None,
        xi_after: Optional[float] = None,
        stability_before: Optional[float] = None,
        stability_after: Optional[float] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Record evidence for a single anchor observation.

        You can supply either:
          - ξ before/after (lower after = good; effect = (xi_before - xi_after))
          - stability score before/after (higher after = good; effect = delta)
        If neither is provided, we still update frequency and last_seen.
        """
        if phrase not in self._stats:
            # Allow observation for phrases not in base (will not be in get_weighted_anchors)
            self._stats[phrase] = AnchorStats(phrase=phrase)

        s = self._stats[phrase]
        s.count += 1
        s.last_seen_ts = float(timestamp if timestamp is not None else time.time())

        effect = 0.0
        if xi_before is not None and xi_after is not None:
            # Positive effect if ξ decreased
            effect = float(xi_before - xi_after)
        elif stability_before is not None and stability_after is not None:
            # Positive effect if stability increased
            effect = float(stability_after - stability_before)

        if effect != 0.0:
            # Update EMA of effect
            alpha = self._params.effect_ema_alpha
            s.ema_effect = (1 - alpha) * s.ema_effect + alpha * effect

        log_event(
            "anchor_observed",
            phrase=phrase,
            count=s.count,
            ema_effect=s.ema_effect,
            last_seen_ts=s.last_seen_ts,
            evidence="xi" if xi_before is not None else ("stability" if stability_before is not None else "freq_only"),
        )

    # --------------------------- Weight Compute --------------------------------

    def _weight_for(self, phrase: str, base_weight: float, now: Optional[float]) -> float:
        """Compute dynamic weight for a phrase given current stats."""
        p = self._params
        s = self._stats.get(phrase)
        if s is None:
            return base_weight

        # Frequency component: tanh(count / norm) in [0, ~1)
        freq_term = math.tanh(s.count / max(1e-9, p.freq_norm)) * p.freq_gain

        # Effect component: EMA of observed improvements (ξ reductions or stability bumps)
        effect_term = s.ema_effect * p.effect_gain

        # Staleness penalty per hour since last seen
        if now is None:
            now = time.time()
        hours = 0.0
        if s.last_seen_ts > 0:
            hours = max(0.0, (now - s.last_seen_ts) / 3600.0)
        stale_term = -p.staleness_penalty_per_hour * hours

        # Combine with base weight and clamp
        w = base_weight + freq_term + effect_term + stale_term
        w = max(p.min_weight, min(p.max_weight, w))

        return w

    def get_weighted_anchors(self) -> List[Anchor]:
        """Return a copy of base anchors with dynamically adjusted weights."""
        now = time.time()
        weighted: List[Anchor] = []
        for a in self._base:
            w = self._weight_for(a["phrase"], a.get("weight", 1.0), now)
            updated: Anchor = {
                "phrase": a["phrase"],
                "category": a.get("category", "unknown"),
                "weight": float(w),
            }
            weighted.append(updated)

        log_event(
            "anchor_weight_update",
            anchors=[{"phrase": x["phrase"], "weight": x["weight"]} for x in weighted],
            params=asdict(self._params),
        )
        return weighted

    # ----------------------------- Persistence ---------------------------------

    def to_dict(self) -> Dict[str, dict]:
        """Serialize stats + params (JSON-safe)."""
        return {
            "params": asdict(self._params),
            "stats": {k: asdict(v) for k, v in self._stats.items()},
            "base": self._base,  # for sanity/debug only
        }

    @classmethod
    def from_dict(
        cls,
        *,
        base: Sequence[Anchor],
        payload: Dict[str, dict],
    ) -> AnchorWeighter:
        """Rebuild a weighter from serialized payload."""
        params_d = payload.get("params", {})
        stats_d = payload.get("stats", {})
        params = WeightParams(**params_d) if params_d else WeightParams()

        stats: Dict[str, AnchorStats] = {}
        for k, v in stats_d.items():
            stats[k] = AnchorStats(
                phrase=v.get("phrase", k),
                count=int(v.get("count", 0)),
                ema_effect=float(v.get("ema_effect", 0.0)),
                last_seen_ts=float(v.get("last_seen_ts", 0.0)),
            )
        return cls(base=base, params=params, stats=stats)

    def dumps(self) -> str:
        """JSON string for storage (e.g., write to a file in experiments/)."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def loads(cls, *, base: Sequence[Anchor], s: str) -> AnchorWeighter:
        """Build from a JSON string produced by dumps()."""
        return cls.from_dict(base=base, payload=json.loads(s))


# ------------------------------ Convenience ----------------------------------

def overlay_weights(anchors: Sequence[Anchor], weighter: AnchorWeighter) -> List[Anchor]:
    """Return a copy of *anchors* with dynamic weights applied from *weighter*.

    This is useful if you want to apply learned weights to a custom anchor
    list instead of the canonical base.
    """
    # Temporarily swap base and compute weights
    temp = AnchorWeighter(base=anchors, params=weighter._params, stats=dict(weighter._stats))
    return temp.get_weighted_anchors()


__all__ = [
    "WeightParams",
    "AnchorStats",
    "AnchorWeighter",
    "overlay_weights",
]