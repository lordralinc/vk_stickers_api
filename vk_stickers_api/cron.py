import contextlib
import logging

import apscheduler.schedulers.asyncio
import tortoise.exceptions

from vk_stickers_api import const, models
from vk_stickers_api.schemas.sticker import ImagePydantic

shc = apscheduler.schedulers.asyncio.AsyncIOScheduler()


callback_logger = logging.getLogger("callback")
sticker_logger = logging.getLogger("stickers")


class StickerPacksGenerator:
    def __init__(self, section_id: str):
        self.section_id = section_id
        self.next_from = None

    async def __aiter__(self):
        while True:
            data = await const.API.method(
                "catalog.getSection", section_id=self.section_id, start_from=self.next_from
            )
            for value in data["stickers_packs"].values():
                yield value
            if "next_from" in data["section"] and data["section"]["next_from"]:
                self.next_from = data["section"]["next_from"]
            else:
                break


async def update_or_create(sticker_pack: dict):
    sticker_logger.info(f"Update sticker: {sticker_pack['product']['id']}")  # noqa: G004
    try:
        old_pack = await models.StickerPack.get(id=sticker_pack["product"]["id"])
    except tortoise.exceptions.DoesNotExist:
        old_pack = await models.StickerPack.create(
            id=sticker_pack["product"]["id"],
            free=sticker_pack.get("free", False),
            has_animation=sticker_pack["product"].get("has_animation", False),
            can_purchase=sticker_pack.get("can_purchase", False),
            can_gift=sticker_pack.get("can_gift", False),
            photo_35=sticker_pack.get("photo_35"),
            photo_70=sticker_pack.get("photo_70"),
            photo_140=sticker_pack.get("photo_140"),
            photo_296=sticker_pack.get("photo_296"),
            photo_592=sticker_pack.get("photo_592"),
            background=sticker_pack.get("background"),
            title=sticker_pack["product"]["title"],
            author=sticker_pack["author"],
            description=sticker_pack["description"],
            price_buy=sticker_pack.get("price_buy"),
            price_gift=sticker_pack.get("price_gift"),
            url=sticker_pack["product"]["url"],
            icon_base_url=sticker_pack["product"]["icon"]["base_url"],
            previews=[
                ImagePydantic.model_validate(x) for x in sticker_pack["product"]["previews"]
            ],
        )

    new_pack = models.StickerPack(
        id=sticker_pack["product"]["id"],
        free=sticker_pack.get("free", False),
        has_animation=sticker_pack["product"].get("has_animation", False),
        can_purchase=sticker_pack.get("can_purchase", False),
        can_gift=sticker_pack.get("can_gift", False),
        photo_35=sticker_pack.get("photo_35"),
        photo_70=sticker_pack.get("photo_70"),
        photo_140=sticker_pack.get("photo_140"),
        photo_296=sticker_pack.get("photo_296"),
        photo_592=sticker_pack.get("photo_592"),
        background=sticker_pack.get("background"),
        title=sticker_pack["product"]["title"],
        author=sticker_pack["author"],
        description=sticker_pack["description"],
        price_buy=sticker_pack.get("price_buy"),
        price_gift=sticker_pack.get("price_gift"),
        url=sticker_pack["product"]["url"],
        icon_base_url=sticker_pack["product"]["icon"]["base_url"],
        previews=[ImagePydantic.model_validate(x) for x in sticker_pack["product"]["previews"]],
    )
    update_fields = old_pack.show_diff(new_pack)
    if not update_fields:
        return
    for field in update_fields:
        setattr(old_pack, field, getattr(new_pack, field))
    await old_pack.save()


async def update_not_created_stickers(sticker_ids: list[int], user_id: int):
    stickers = (
        await const.API.method(
            "store.getStockItems",
            type="stickers",
            product_ids=",".join(str(x) for x in sticker_ids),
            user_id=user_id,
        )
    )["items"]
    for sticker_pack in stickers:
        await update_or_create(sticker_pack)
        with contextlib.suppress(Exception):
            models.Sticker.bulk_create(
                await models.Sticker(
                    id=sticker["sticker_id"],
                    is_allowed=sticker.get("is_allowed", False),
                    images=[ImagePydantic.model_validate(x) for x in sticker["images"]],
                    images_with_background=[
                        ImagePydantic.model_validate(x) for x in sticker["images_with_background"]
                    ],
                    sticker_pack_id=sticker_pack["product"]["id"],
                    keywords=sticker.get("keywords", []),
                )
                for sticker in sticker_pack["product"]["stickers"]
            )


async def collect_stickers():
    keywords = await const.API.method(
        "store.getStickersKeywords", aliases=1, all_products=1, need_stickers=0
    )
    sections = await const.API.method("catalog.getStickers", need_blocks=0)
    for section in sections["catalog"]["sections"]:
        async for sticker_pack in StickerPacksGenerator(section["id"]):
            await update_or_create(sticker_pack)
            _stickers = []
            for sticker in sticker_pack["product"]["stickers"]:
                for dictionary in keywords["dictionary"]:
                    for dict_sticker in dictionary["stickers"]:
                        if dict_sticker["sticker_id"] == sticker["sticker_id"]:
                            sticker["keywords"] = dictionary["words"]
                _stickers.append(
                    models.Sticker(
                        id=sticker["sticker_id"],
                        is_allowed=sticker.get("is_allowed", False),
                        images=[ImagePydantic.model_validate(x) for x in sticker["images"]],
                        images_with_background=[
                            ImagePydantic.model_validate(x)
                            for x in sticker["images_with_background"]
                        ],
                        sticker_pack_id=sticker_pack["product"]["id"],
                        keywords=sticker.get("keywords", []),
                    )
                )
            with contextlib.suppress(Exception):
                await models.Sticker.bulk_create(_stickers)


shc.add_job(collect_stickers, trigger="interval", hours=2)
