from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from pydantic import BaseModel, Field

import auth
from microsoft_access.account_lifecycle_service import AccountLifecycleService
from models import (
    AccountCredentials,
    AccountHealthResponse,
    AccountProbeResponse,
    CapabilitySnapshotResponse,
    DeliveryStrategyOverrideResponse,
    DeliveryStrategyResponse,
    StrategyMode,
)


router = APIRouter(prefix="/accounts", tags=["API v2 / 账户"])
default_account_lifecycle_service = AccountLifecycleService()


class DeliveryStrategyOverrideRequest(BaseModel):
    provider: Literal["auto", "graph", "imap"] = Field(default="auto")
    strategy_mode: Optional[StrategyMode] = None
    skip_cache: bool = False
    ttl_seconds: Optional[int] = Field(default=None, ge=1)


def get_account_lifecycle_service(request: Request) -> AccountLifecycleService:
    service = getattr(request.app.state, "v2_account_lifecycle_service", None)
    return service or default_account_lifecycle_service


@router.post(
    "/probe",
    response_model=AccountProbeResponse,
    response_model_exclude_unset=True,
)
async def probe_account(
    credentials: AccountCredentials,
    user: dict = Depends(auth.get_current_user),
    service: AccountLifecycleService = Depends(get_account_lifecycle_service),
):
    auth.require_admin(user)
    return await service.probe_account(credentials, persist=False)


@router.get(
    "/{email}/health",
    response_model=AccountHealthResponse,
    response_model_exclude_unset=True,
)
async def get_account_health(
    email: str,
    user: dict = Depends(auth.get_current_user),
    service: AccountLifecycleService = Depends(get_account_lifecycle_service),
):
    if not auth.check_account_access(user, email):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=f"无权访问账户 {email}")
    return await service.get_account_health(email)


@router.post(
    "/{email}/capability-detection",
    response_model=CapabilitySnapshotResponse,
    response_model_exclude_unset=True,
)
async def detect_account_capability(
    email: str,
    user: dict = Depends(auth.get_current_user),
    service: AccountLifecycleService = Depends(get_account_lifecycle_service),
):
    auth.require_admin(user)
    return await service.detect_capability(email, persist=True)


@router.get(
    "/{email}/delivery-strategy",
    response_model=DeliveryStrategyResponse,
    response_model_exclude_unset=True,
)
async def get_delivery_strategy(
    email: str,
    override_provider: Optional[Literal["auto", "graph", "imap"]] = Query(None),
    strategy_mode: Optional[StrategyMode] = Query(None),
    skip_cache: bool = False,
    user: dict = Depends(auth.get_current_user),
    service: AccountLifecycleService = Depends(get_account_lifecycle_service),
):
    if not auth.check_account_access(user, email):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=f"无权访问账户 {email}")
    return await service.resolve_delivery_strategy(
        email,
        strategy_mode=strategy_mode,
        override_provider=override_provider,
        skip_cache=skip_cache,
    )


@router.post(
    "/{email}/delivery-strategy/override",
    response_model=DeliveryStrategyOverrideResponse,
    response_model_exclude_unset=True,
)
async def override_delivery_strategy(
    email: str,
    request: DeliveryStrategyOverrideRequest = Body(default_factory=DeliveryStrategyOverrideRequest),
    user: dict = Depends(auth.get_current_user),
    service: AccountLifecycleService = Depends(get_account_lifecycle_service),
):
    auth.require_admin(user)
    return await service.override_delivery_strategy(
        email,
        provider=request.provider,
        strategy_mode=request.strategy_mode,
        skip_cache=request.skip_cache,
        ttl_seconds=request.ttl_seconds,
    )
