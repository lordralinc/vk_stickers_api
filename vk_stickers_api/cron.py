import datetime

import aiohttp
import apscheduler.schedulers.asyncio
import typing

import tortoise.exceptions

from vk_stickers_api import const, models
from vk_stickers_api.schemas.callback import CallbackTypes
from vk_stickers_api.schemas.sticker import ImagePydantic

shc = apscheduler.schedulers.asyncio.AsyncIOScheduler()


class StickerPacksGenerator:

    def __init__(self, section_id: str):
        self.section_id = section_id
        self.next_from = None

    async def __aiter__(self):
        while True:
            data = await const.API.method("catalog.getSection", section_id=self.section_id, start_from=self.next_from)
            for key, value in data['stickers_packs'].items():
                yield value
            if 'next_from' in data['section'] and data['section']['next_from']:
                self.next_from = data['section']['next_from']
            else:
                break


async def send_callbacks(
        session: aiohttp.ClientSession,
        callback_type: CallbackTypes,
        data: dict
):
    async for callback in models.CallbackHost.all():
        if callback_type in CallbackTypes(callback.methods):
            try:
                async with session.post(callback.url, data=data):
                    pass
            except:
                pass


async def update_or_create(sticker_pack: dict):
    session = aiohttp.ClientSession(
        headers={'User-Agent': 'VKStickersAPI'},
        timeout=5
    )
    is_created = False
    try:
        old_pack = await models.StickerPack.get(id=sticker_pack['product']['id'])
    except tortoise.exceptions.DoesNotExist:
        is_created = True
        old_pack = await models.StickerPack.create(
            id=sticker_pack['product']['id'],
            free=sticker_pack.get('free', False),
            has_animation=sticker_pack['product'].get('has_animation', False),
            can_purchase=sticker_pack.get('can_purchase', False),
            can_gift=sticker_pack.get('can_gift', False),

            photo_35=sticker_pack.get('photo_35'),
            photo_70=sticker_pack.get('photo_70'),
            photo_140=sticker_pack.get('photo_140'),
            photo_296=sticker_pack.get('photo_296'),
            photo_592=sticker_pack.get('photo_592'),
            background=sticker_pack.get('background'),

            title=sticker_pack['product']['title'],
            author=sticker_pack['author'],
            description=sticker_pack['description'],
            price_buy=sticker_pack.get('price_buy'),
            price_gift=sticker_pack.get('price_gift'),
            url=sticker_pack['product']['url'],
            icon_base_url=sticker_pack['product']['icon']['base_url'],
            previews=[ImagePydantic.parse_obj(x) for x in sticker_pack['product']['previews']]
        )

    if is_created:
        await send_callbacks(
            session,
            CallbackTypes.CREATED,
            {
                'type': 'new_sticker',
                'object': await old_pack.dict(),
                'date': datetime.datetime.now().timestamp()
            }
        )
    else:
        new_pack = models.StickerPack(
            id=sticker_pack['product']['id'],
            free=sticker_pack.get('free', False),
            has_animation=sticker_pack['product'].get('has_animation', False),
            can_purchase=sticker_pack.get('can_purchase', False),
            can_gift=sticker_pack.get('can_gift', False),

            photo_35=sticker_pack.get('photo_35'),
            photo_70=sticker_pack.get('photo_70'),
            photo_140=sticker_pack.get('photo_140'),
            photo_296=sticker_pack.get('photo_296'),
            photo_592=sticker_pack.get('photo_592'),
            background=sticker_pack.get('background'),

            title=sticker_pack['product']['title'],
            author=sticker_pack['author'],
            description=sticker_pack['description'],
            price_buy=sticker_pack.get('price_buy'),
            price_gift=sticker_pack.get('price_gift'),
            url=sticker_pack['product']['url'],
            icon_base_url=sticker_pack['product']['icon']['base_url'],
            previews=[ImagePydantic.parse_obj(x) for x in sticker_pack['product']['previews']]
        )
        update_fields = old_pack.show_diff(new_pack)
        if not update_fields:
            return
        for field in update_fields:
            setattr(old_pack, field, getattr(new_pack, field))
        await old_pack.save()
        await send_callbacks(
            session,
            CallbackTypes.MODIFIED,
            {
                'type': 'update_sticker',
                'object': {
                    'fields': update_fields,
                    'sticker_data': await old_pack.dict()
                },
                'date': datetime.datetime.now().timestamp()
            }
        )


async def collect_stickers():
    keywords = await const.API.method(
        "store.getStickersKeywords",
        aliases=1,
        all_products=1,
        need_stickers=0
    )
    sections = await const.API.method(
        'catalog.getStickers', need_blocks=0
    )
    for section in sections['catalog']['sections']:
        async for sticker_pack in StickerPacksGenerator(section['id']):
            await update_or_create(sticker_pack)
            for sticker in sticker_pack['product']['stickers']:
                for dictionary in keywords['dictionary']:
                    for dict_sticker in dictionary['stickers']:
                        if dict_sticker['sticker_id'] == sticker['sticker_id']:
                            sticker['keywords'] = dictionary['words']
                try:
                    await models.Sticker.create(
                        id=sticker['sticker_id'],
                        is_allowed=sticker.get('is_allowed', False),
                        images=[ImagePydantic.parse_obj(x) for x in sticker['images']],
                        images_with_background=[
                            ImagePydantic.parse_obj(x) for x in
                            sticker['images_with_background']
                        ],
                        sticker_pack_id=sticker_pack['product']['id'],
                        keywords=sticker.get('keywords', [])
                    )
                except tortoise.exceptions.IntegrityError:
                    pass


shc.add_job(collect_stickers, trigger='interval', hours=2)
