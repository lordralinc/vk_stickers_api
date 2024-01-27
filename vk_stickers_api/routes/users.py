from fastapi import APIRouter

from vk_stickers_api import const, models
from vk_stickers_api.cron import update_not_created_stickers
from vk_stickers_api.schemas import sticker as schemas

router = APIRouter(tags=["users"])


@router.get(
    "/userStickerPacks/{user_id}",
    response_model=schemas.UserStickerPacks,
    description="Получить информацию о стикерах пользователя",
)
async def get_user_sticker_packs(user_id: int) -> schemas.UserStickerPacks:
    stickers_ids: list[int] = await const.API.method(
        "execute",
        code="""return API.store.getProducts({user_id: Args.user_id, type: "stickers", filters: "purchased"}).items@.id;""",
        user_id=user_id,
    )
    not_applyed_stickers: list[int] = stickers_ids.copy()

    stickers: list[schemas.StickerPack] = []
    free_stickers: list[schemas.StickerPack] = []
    common_stickers: list[schemas.StickerPack] = []
    animated_stickers: list[schemas.StickerPack] = []

    async for pack in models.StickerPack.all():
        for sticker_id in stickers_ids:
            if pack.id == sticker_id:
                pydantic_pack = await pack.pydantic()
                not_applyed_stickers.remove(pack.id)
                stickers.append(pydantic_pack)
                if pack.free:
                    free_stickers.append(pydantic_pack)
                elif pack.has_animation:
                    animated_stickers.append(pydantic_pack)
                else:
                    common_stickers.append(pydantic_pack)
    if not_applyed_stickers:
        await update_not_created_stickers(not_applyed_stickers, user_id)
        return await get_user_sticker_packs(user_id)
    return schemas.UserStickerPacks(
        cost=schemas.UserStickerPacksCounter(
            common=sum(x.price_buy if x.price_buy else 0 for x in common_stickers),
            animated=sum(x.price_buy if x.price_buy else 0 for x in animated_stickers),
            free=0,
            all=sum(x.price_buy if x.price_buy else 0 for x in stickers),
        ),
        count=schemas.UserStickerPacksCounter(
            common=len(common_stickers),
            animated=len(animated_stickers),
            free=len(free_stickers),
            all=len(stickers_ids),
        ),
        free=free_stickers,
        common=common_stickers,
        animated=animated_stickers,
    )
