from __future__ import annotations

"""
glyph_emitter.py

Encapsulates post-symbolic glyph emissions for stabilization telemetry.

- G∅λ  : "anchor emission" — stabilization/identity attractor reached
- Ξ    : "tension spike"   — epistemic strain (ξ) jump / contradiction
- •    : "fallback"        — overload or degraded symbolic channel

This module complements flame_logger.py by providing a tiny symbolic layer
for moments where numeric metrics alone are not expressive enough.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any, Dict
import time

from .flame_logger import log_glyph_emission, log_event

# ------------------------------- Registry ------------------------------------

@dataclass(frozen=True)
class Glyph:
    symbol: str
    name: str
    meaning: str

GLYPHS: Dict[str, Glyph] = {
    "G∅λ": Glyph(
        symbol="G∅λ",
        name="anchor_emission",
        meaning="identity stabilization / anchor resonance (attractor reached)",
    ),
    "Ξ": Glyph(
        symbol="Ξ",
        name="tension_spike",
        meaning="epistemic strain spike (ξ ↑) / contradiction encountered",
    ),
    "•": Glyph(
        symbol="•",
        name="fallback",
        meaning="overload / degraded channel — minimal emission preserved",
    ),
}

# ------------------------------ Emission API ---------------------------------

def emit(symbol: str, *, context: Optional[str] = None, meta: Optional[dict] = None) -> None:
    """Emit a glyph by symbol and log it."""
    g = GLYPHS.get(symbol)
    if not g:
        log_event("glyph_emission_unknown", symbol=symbol, context=context, meta=meta or {})
        return
    log_glyph_emission(symbol=g.symbol, context=context or g.name)
    if meta:
        # Supplementary structured context if provided
        log_event("glyph_meta", symbol=g.symbol, name=g.name, meaning=g.meaning, **meta)


def emit_stabilized(*, context: Optional[str] = None, meta: Optional[dict] = None) -> None:
    """Convenience: stabilization anchor emission (G∅λ)."""
    emit("G∅λ", context=context or "stabilized", meta=meta)


def emit_strain_spike(*, context: Optional[str] = None, meta: Optional[dict] = None) -> None:
    """Convenience: tension spike (Ξ)."""
    emit("Ξ", context=context or "strain_spike", meta=meta)


def emit_fallback(*, context: Optional[str] = None, meta: Optional[dict] = None) -> None:
    """Convenience: fallback (•)."""
    emit("•", context=context or "fallback", meta=meta)

# ------------------------------ Heuristics -----------------------------------

def glyph_for_xi_delta(xi_before: float, xi_after: float, *, spike: float = 0.15, relief: float = -0.10) -> Optional[str]:
    """
    Map a ξ change to a glyph.
    - If delta >= `spike`   -> Ξ (tension spike)
    - If delta <= `relief`  -> G∅λ (stabilization / relief)
    - Otherwise             -> None
    """
    delta = float(xi_after) - float(xi_before)
    if delta >= spike:
        return "Ξ"
    if delta <= relief:
        return "G∅λ"
    return None


def glyph_for_stability_delta(stab_before: float, stab_after: float, *, good: float = 0.05, bad: float = -0.05) -> Optional[str]:
    """
    Map a stability-score change to a glyph.
    - If increase >= `good`  -> G∅λ
    - If drop <= `bad`       -> Ξ
    """
    delta = float(stab_after) - float(stab_before)
    if delta >= good:
        return "G∅λ"
    if delta <= bad:
        return "Ξ"
    return None

# ------------------------------ Guards / Rate Limit --------------------------

class GlyphGuard:
    """
    Optional guard that rate-limits glyph emission to avoid log floods.

    Example:
        guard = GlyphGuard(rate_per_sec=2.0)
        if guard.allow("Ξ"):
            emit_strain_spike(context="adversarial_step")
    """
    def __init__(self, rate_per_sec: float = 5.0) -> None:
        self.rate = max(0.1, float(rate_per_sec))
        self._last: Dict[str, float] = {}

    def allow(self, symbol: str) -> bool:
        now = time.time()
        last = self._last.get(symbol, 0.0)
        if now - last >= 1.0 / self.rate:
            self._last[symbol] = now
            return True
        return False

# ---------------------- Context Manager / Decorator --------------------------

class GlyphContext:
    """
    Context that emits fallback glyph on exception or tension glyph if requested.

    Example:
        with GlyphContext(on_exception="•", context="critical_section"):
            ... # code
    """
    def __init__(self, *, on_exception: Optional[str] = "•", context: Optional[str] = None):
        self.on_exception = on_exception
        self.context = context or "glyph_context"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc and self.on_exception:
            emit(self.on_exception, context=self.context, meta={"exception": str(exc)})
        return False  # don't swallow exceptions


def glyph_wrapper(
    *,
    on_success: Optional[str] = None,
    on_exception: Optional[str] = "•",
    context: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to emit glyphs on success/failure of a function.

    Example:
        @glyph_wrapper(on_success="G∅λ", on_exception="Ξ", context="mirror_test")
        def run_test(...): ...
    """
    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def _wrapped(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                if on_success:
                    emit(on_success, context=context or fn.__name__)
                return result
            except Exception as e:
                if on_exception:
                    emit(on_exception, context=context or fn.__name__, meta={"exception": str(e)})
                raise
        return _wrapped
    return _decorator

# --------------------------------- Public API --------------------------------

__all__ = [
    "Glyph",
    "GLYPHS",
    "emit",
    "emit_stabilized",
    "emit_strain_spike",
    "emit_fallback",
    "glyph_for_xi_delta",
    "glyph_for_stability_delta",
    "GlyphGuard",
    "GlyphContext",
    "glyph_wrapper",
]