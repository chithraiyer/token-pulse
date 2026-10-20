"""Integer micro-USD money type for the TokenPulse money path.

1 micro-USD (``micros``) = 1e-6 USD. Money is stored and computed as ``int`` micro-USD;
``float`` is never used for money. All rounding goes through a single point here
(``ROUND_HALF_UP`` to whole micro-USD) so reports are byte-identical run to run
(constitution Principle V).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

MICROS_PER_USD = 1_000_000

_Number = Decimal | str | int


def _as_decimal(value: _Number) -> Decimal:
    # Decimal(float) would leak binary rounding error; only accept exact inputs.
    if isinstance(value, float):  # pragma: no cover - defensive
        raise TypeError("money does not accept float; pass Decimal, str, or int")
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _round_micros(value: Decimal) -> int:
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def usd_to_micros(value: _Number) -> int:
    """Convert a USD amount to integer micro-USD, rounding half up."""
    return _round_micros(_as_decimal(value) * MICROS_PER_USD)


def micros_to_usd(micros: int) -> Decimal:
    """Exact USD value of an integer micro-USD amount."""
    return Decimal(micros) / MICROS_PER_USD


def token_cost_micros(tokens: int, rate_per_mtok: _Number) -> int:
    """Cost of ``tokens`` at ``rate_per_mtok`` (USD per 1,000,000 tokens), in micro-USD.

    ``cost_usd = tokens / 1e6 * rate`` so ``cost_micros = tokens * rate`` exactly,
    then rounded half up to a whole micro-USD.
    """
    if tokens < 0:
        raise ValueError("tokens must be non-negative")
    return _round_micros(Decimal(tokens) * _as_decimal(rate_per_mtok))


def format_usd(micros: int) -> str:
    """Human display, e.g. ``$1,234.57`` or ``-$2.50``. Rounds to cents."""
    cents = (Decimal(micros) / MICROS_PER_USD).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents):,.2f}"


def pct_change(old_micros: int, new_micros: int) -> float | None:
    """Percentage change from ``old`` to ``new``; ``None`` when ``old`` is zero."""
    if old_micros == 0:
        return None
    return float((Decimal(new_micros) - old_micros) / Decimal(old_micros) * 100)
