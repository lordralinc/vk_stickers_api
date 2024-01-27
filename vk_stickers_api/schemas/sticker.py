import typing

import pydantic


class ImagePydantic(pydantic.BaseModel):
    url: str = pydantic.Field(..., title='Ссылка')
    width: int = pydantic.Field(..., title='Ширина')
    height: int = pydantic.Field(..., title='Высота')


class StickerPack(pydantic.BaseModel):
    id: int = pydantic.Field(..., title='ID пака')
    free: bool = pydantic.Field(False, title='Бесплатный')
    can_purchase: bool = pydantic.Field(False, title='Можно купить')
    has_animation: bool = pydantic.Field(False, title='Анимированный')
    can_gift: bool = pydantic.Field(False, title='Можно подарить')
    title: str = pydantic.Field(..., title='Название')
    author: str = pydantic.Field(..., title='Автор')
    description: str = pydantic.Field(..., title='Описание')
    price_buy: typing.Optional[int] = pydantic.Field(None, title='Цена за покупку')
    price_gift: typing.Optional[int] = pydantic.Field(None, title='Цена за подарок')
    url: str = pydantic.Field(..., title='Ссылка')
    icon_base_url: str = pydantic.Field(..., title='icon_base_url')

    photo_35: typing.Optional[str] = None
    photo_70: typing.Optional[str] = None
    photo_140: typing.Optional[str] = None
    photo_296: typing.Optional[str] = None
    photo_592: typing.Optional[str] = None
    background: typing.Optional[str] = None

    previews: list[ImagePydantic] = []


class Sticker(pydantic.BaseModel):
    id: int
    is_allowed: bool = False
    keywords: list[str] = []
    images: list[ImagePydantic] = []
    images_with_background: list[ImagePydantic] = []
    sticker_pack_id: int


class UserStickerPacksCounter(pydantic.BaseModel):
    free: int
    common: int
    animated: int
    all: int


class UserStickerPacks(pydantic.BaseModel):
    count: UserStickerPacksCounter
    cost: UserStickerPacksCounter

    free: list[StickerPack]
    common: list[StickerPack]
    animated: list[StickerPack]
