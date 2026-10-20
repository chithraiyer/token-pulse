"""/api/meta — app + config metadata. Drives the demo banner and the version footer."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from tokenpulse import __version__
from tokenpulse.api.deps import get_settings
from tokenpulse.api.schemas import Meta
from tokenpulse.config import Settings
from tokenpulse.services import effective_spike_multiple, load_pricing, load_rules

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta", response_model=Meta)
def read_meta(settings: Settings = Depends(get_settings)) -> Meta:
    return Meta(
        mode=settings.mode,
        is_demo_data=settings.is_demo,
        tool_version=__version__,
        pricing_table_versions=load_pricing(settings).versions(),
        rule_catalog_version=load_rules(settings).version,
        retention_days=settings.retention_days,
        spike_multiple=effective_spike_multiple(settings),
    )
