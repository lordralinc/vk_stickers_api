import typing

from fastapi import APIRouter

from vk_stickers_api import models, const
from vk_stickers_api.schemas import sticker as schemas

router = APIRouter(
    tags=['users']
)


@router.get(
    '/userStickerPacks/{user_id}',
    response_model=schemas.UserStickerPacks,
    description='Получить информацию о стикерах пользователя'
)
async def get_user_sticker_packs(user_id: int) -> schemas.UserStickerPacks:
    gifts = await const.API.method(
        "gifts.getCatalog",
        no_inapp=0,
        user_id=user_id,
        force_payment=1
    )
    stickers_gifts = [s for s in gifts if s['name'] in {'stickers_popular', 'stickers'}]
    stickers = []
    for sticker_gift in stickers_gifts:
        stickers += [item for item in sticker_gift['items'] if item.get('disabled', False)]
    stickers_ids = set([s['gift']['stickers_product_id'] for s in stickers])
    stickers = [await sticker_pack.pydantic() async for sticker_pack in models.StickerPack.filter(id__in=stickers_ids)]

    free_stickers = list(filter(lambda x: x.free, stickers))
    common_stickers = list(filter(lambda x: not x.has_animation and not x.free, stickers))
    animated_stickers = list(filter(lambda x: x.has_animation, stickers))

    return schemas.UserStickerPacks(
        cost=schemas.UserStickerPacksCounter(
            common=sum(map(lambda x: x.price_buy if x.price_buy else 0, common_stickers)),
            animated=sum(map(lambda x: x.price_buy if x.price_buy else 0, animated_stickers)),
            free=0,
            all=sum(map(lambda x: x.price_buy if x.price_buy else 0, stickers)),
        ),
        count=schemas.UserStickerPacksCounter(
            common=len(common_stickers),
            animated=len(animated_stickers),
            free=len(free_stickers),
            all=len(stickers)
        ),
        free=free_stickers,
        common=common_stickers,
        animated=animated_stickers
    )
