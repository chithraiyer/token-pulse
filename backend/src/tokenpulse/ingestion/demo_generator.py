"""Deterministic synthetic dataset for demo mode (FR-003).

Same ``(seed, days, members, end_date)`` -> byte-identical output (SC-010). The generator
emits token buckets only; cost is computed downstream by the pricing catalog.

Planted patterns (so US1's independent test and, later, US3/US4 have something to find):
  * member 0  - week-long Opus-in-a-loop spike
  * member 1  - single-day sharp spike
  * team "product" - Sonnet -> Opus model-mix shift, second half of the window
  * member 2  - low cache-hit ratio on very high input volume
  * member 3  - steady high-volume workload (low day-to-day variance)
  * members 4+ - unremarkable baseline usage
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from random import Random

from tokenpulse.ingestion.pipeline import RawUsageBucket

MODELS = ("claude-opus-4", "claude-sonnet-4", "claude-haiku-4")


@dataclass(frozen=True)
class _MemberSpec:
    id: str
    team_id: str
    base_input_per_day: int
    mix: dict[str, float]  # model -> weight (sums ~1)


def _mix(opus: float, sonnet: float, haiku: float) -> dict[str, float]:
    return {"claude-opus-4": opus, "claude-sonnet-4": sonnet, "claude-haiku-4": haiku}


# Fixed roster; `members` takes the first N. Order is stable for RNG determinism.
_ROSTER: tuple[_MemberSpec, ...] = (
    _MemberSpec("alice", "platform", 600_000, _mix(0.15, 0.60, 0.25)),
    _MemberSpec("bob", "platform", 450_000, _mix(0.10, 0.55, 0.35)),
    _MemberSpec("carol", "platform", 3_000_000, _mix(0.05, 0.70, 0.25)),
    _MemberSpec("dave", "product", 6_000_000, _mix(0.10, 0.60, 0.30)),
    _MemberSpec("erin", "product", 500_000, _mix(0.12, 0.50, 0.38)),
    _MemberSpec("frank", "product", 380_000, _mix(0.08, 0.52, 0.40)),
    _MemberSpec("grace", "platform", 720_000, _mix(0.18, 0.52, 0.30)),
    _MemberSpec("heidi", "product", 540_000, _mix(0.10, 0.60, 0.30)),
)

# Pattern offsets, counted back from the last day of the window.
_OPUS_LOOP_START, _OPUS_LOOP_END = 45, 39   # member 0
_SHARP_SPIKE_OFFSET = 15                     # member 1
_MIX_SHIFT_OFFSET = 25                       # team "product"


def generate(
    *,
    seed: int,
    days: int,
    members: int,
    end_date: date,
) -> list[RawUsageBucket]:
    if not 1 <= members <= len(_ROSTER):
        raise ValueError(f"members must be between 1 and {len(_ROSTER)}")
    rng = Random(seed)
    roster = _ROSTER[:members]
    span = [end_date - timedelta(days=n) for n in range(days - 1, -1, -1)]

    out: list[RawUsageBucket] = []
    for idx, spec in enumerate(roster):
        for day in span:
            offset = (end_date - day).days
            weekend = 0.4 if day.weekday() >= 5 else 1.0
            sigma = 0.12 if idx == 3 else 0.35  # member 3 is deliberately steady
            noise = math.exp(rng.gauss(0.0, sigma))
            day_input = spec.base_input_per_day * weekend * noise

            mix = _mix_for(spec, idx, offset)
            opus_loop = idx == 0 and _OPUS_LOOP_END <= offset <= _OPUS_LOOP_START
            sharp_spike = idx == 1 and offset == _SHARP_SPIKE_OFFSET

            for model in MODELS:
                weight = mix.get(model, 0.0)
                if weight <= 0:
                    continue
                model_input = day_input * weight
                if opus_loop and model == "claude-opus-4":
                    model_input *= 16.0
                if sharp_spike:
                    model_input *= 9.0
                model_input = int(model_input)
                if model_input <= 0:
                    continue
                out.append(_bucket(spec, day, model, model_input, low_cache=(idx == 2), rng=rng))

    out.sort(key=lambda b: (b.member_id, b.date, b.model))
    return out


def roster(members: int) -> list[tuple[str, str, str]]:
    """(member_id, display_name, team_id) for the first ``members`` of the fixed roster."""
    if not 1 <= members <= len(_ROSTER):
        raise ValueError(f"members must be between 1 and {len(_ROSTER)}")
    return [(s.id, s.id.capitalize(), s.team_id) for s in _ROSTER[:members]]


def _mix_for(spec: _MemberSpec, idx: int, offset: int) -> dict[str, float]:
    mix = dict(spec.mix)
    if spec.team_id == "product" and offset <= _MIX_SHIFT_OFFSET:
        # shift ~30 points of weight from Sonnet to Opus in the recent window
        moved = min(0.30, mix.get("claude-sonnet-4", 0.0))
        mix["claude-sonnet-4"] = mix.get("claude-sonnet-4", 0.0) - moved
        mix["claude-opus-4"] = mix.get("claude-opus-4", 0.0) + moved
    return mix


def _bucket(
    spec: _MemberSpec,
    day: date,
    model: str,
    model_input: int,
    *,
    low_cache: bool,
    rng: Random,
) -> RawUsageBucket:
    output = int(model_input * rng.uniform(0.18, 0.4))
    if low_cache:
        cache_read = int(model_input * rng.uniform(0.0, 0.03))
        cache_write = int(model_input * rng.uniform(0.0, 0.02))
    else:
        cache_read = int(model_input * rng.uniform(0.3, 0.6))
        cache_write = int(model_input * rng.uniform(0.03, 0.08))
    return RawUsageBucket(
        member_id=spec.id,
        source="demo",
        source_identity=None,
        date=day,
        model=model,
        input_tokens=model_input,
        output_tokens=output,
        cache_read_tokens=cache_read,
        cache_write_tokens=cache_write,
    )
