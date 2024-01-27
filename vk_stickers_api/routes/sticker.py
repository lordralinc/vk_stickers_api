import http

import tortoise.exceptions
from fastapi import APIRouter, HTTPException, Query
from tortoise.expressions import Q

from vk_stickers_api import models
from vk_stickers_api.schemas import sticker as schemas

router = APIRouter(
    tags=['stickers']
)


@router.get(
    '/stickerPacks',
    response_model=list[schemas.StickerPack],
    description='Получить список стикер-паков'
)
async def get_sticker_packs(
        offset: int = Query(0, ge=0),
        has_animation: bool | None = None,
        can_purchase: bool | None = None,
        can_gift: bool | None = None,
        price_gte: int | None = None,
        price_lte: int | None = None,
) -> list[schemas.StickerPack]:
    qs = Q()
    if has_animation is not None:
        qs &= Q(has_animation=has_animation)
    if can_purchase is not None:
        qs &= Q(can_purchase=can_purchase)
    if can_gift is not None:
        qs &= Q(can_gift=can_gift)
    if price_gte is not None:
        qs &= Q(price_buy__gte=price_gte)
    if price_lte is not None:
        qs &= Q(price_buy__lte=price_lte)
    packs = await models.StickerPack.filter(qs).order_by('id').offset(offset).limit(100)
    return [
        await pack.pydantic()
        for pack in packs
    ]


@router.get(
    '/stickerPacks/{pack_id}',
    response_model=schemas.StickerPack,
    description='Получить стикер-пак по ID'
)
async def get_sticker_pack_by_id(
        pack_id: int
) -> schemas.StickerPack:
    try:
        pack = await models.StickerPack.get(id=pack_id)
    except tortoise.exceptions.DoesNotExist as ex:
        raise HTTPException(http.HTTPStatus.NOT_FOUND, detail=f"Sticker pack #{pack_id} not found") from ex

    return await pack.pydantic()


@router.get(
    '/sticker/{sticker_id}',
    response_model=schemas.Sticker,
    description='Получить стикер по ID'
)
async def get_sticker_by_id(
        sticker_id: int
) -> schemas.Sticker:
    try:
        sticker = await models.Sticker.get(id=sticker_id)
    except tortoise.exceptions.DoesNotExist as ex:
        raise HTTPException(http.HTTPStatus.NOT_FOUND, detail=f"Sticker #{sticker_id} not found") from ex
    return await sticker.pydantic()


@router.get(
    '/stickersByPack/{pack_id}',
    response_model=list[schemas.Sticker],
    description='Получить список стикеров по ID стикер-пака'
)
async def get_stickers_by_pack_by_id(
        pack_id: int
) -> list[schemas.Sticker]:
    stickers = await models.Sticker.filter(sticker_pack_id=pack_id)
    return [
        await sticker.pydantic()
        for sticker in stickers
    ]
