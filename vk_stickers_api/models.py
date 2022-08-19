import json
import typing

from tortoise import Model, fields, Tortoise
from tortoise.fields.data import JsonDumpsFunc, JsonLoadsFunc, JSON_DUMPS, JSON_LOADS

from vk_stickers_api.schemas import sticker as schemas
from vk_stickers_api.schemas.callback import CallbackTypes

T = typing.TypeVar('T')


class PydanticField(fields.JSONField):

    def __init__(
            self,
            pydantic_model: typing.Type[T],
            encoder: "JsonDumpsFunc" = JSON_DUMPS,
            decoder: "JsonLoadsFunc" = JSON_LOADS,
            **kwargs,
    ):
        super().__init__(encoder=encoder, decoder=decoder, **kwargs)
        self._pydantic_model = pydantic_model

    def to_python_value(
            self, value: typing.Optional[typing.Union[str, bytes, dict, list]]
    ) -> typing.Optional[typing.Union[T, typing.List[T]]]:
        typed_value = super(PydanticField, self).to_python_value(value)
        if typed_value is None:
            return None
        if isinstance(typed_value, list):
            return [self._pydantic_model.parse_obj(x) for x in typed_value]
        return self._pydantic_model.parse_obj(typed_value)

    def to_db_value(
            self,
            value: typing.Optional[typing.Union[T, typing.List[T]]],
            instance: "typing.Union[typing.Type[Model], Model]"
    ) -> typing.Optional[str]:
        if value is None:
            return None
        if isinstance(value, list):
            return super(PydanticField, self).to_db_value(
                [json.loads(x.json()) for x in value],
                instance
            )
        return value.json()


class StickerPack(Model):
    id: int = fields.IntField(pk=True, generated=False)
    free: bool = fields.BooleanField(default=False)
    has_animation: bool = fields.BooleanField(default=False)
    can_purchase: bool = fields.BooleanField(default=False)
    can_gift: bool = fields.BooleanField(default=False)
    title: str = fields.CharField(max_length=512)
    author: str = fields.CharField(max_length=512)
    description: str = fields.CharField(max_length=4098)
    price_buy: int = fields.FloatField(null=True)
    price_gift: int = fields.FloatField(null=True)
    url: str = fields.CharField(max_length=4098)
    icon_base_url: str = fields.CharField(max_length=4098)

    photo_35: str = fields.CharField(max_length=4098, null=True)
    photo_70: str = fields.CharField(max_length=4098, null=True)
    photo_140: str = fields.CharField(max_length=4098, null=True)
    photo_296: str = fields.CharField(max_length=4098, null=True)
    photo_592: str = fields.CharField(max_length=4098, null=True)
    background: str = fields.CharField(max_length=4098, null=True)

    previews: typing.List[schemas.ImagePydantic] = PydanticField(schemas.ImagePydantic, default=[])

    async def dict(self) -> dict:
        return dict(
            id=self.id, free=self.free,
            can_purchase=self.can_purchase, has_animation=self.has_animation,
            can_gift=self.can_gift, title=self.title,
            author=self.author, description=self.description,
            price_buy=self.price_buy, price_gift=self.price_gift,
            url=self.url, icon_base_url=self.icon_base_url,
            photo_35=self.photo_35, photo_70=self.photo_70,
            photo_140=self.photo_140, photo_296=self.photo_296,
            photo_592=self.photo_592, background=self.background,
            previews=[img.dict() for img in self.previews],
        )

    async def pydantic(self) -> schemas.StickerPack:
        return schemas.StickerPack.parse_obj(await self.dict())

    def show_diff(self, other: "StickerPack") -> typing.List[str]:
        update_fields = []
        for field, _ in self._meta.fields_map.items():
            if field in {'stickers'}:
                continue
            if getattr(self, field, None) != getattr(other, field, None):
                update_fields.append(field)
        return update_fields


class Sticker(Model):
    sticker_pack_id: int

    id: int = fields.IntField(pk=True, generated=False)
    is_allowed: bool = fields.BooleanField(default=False)
    keywords: typing.List[str] = fields.JSONField(default=[])
    images: typing.List[schemas.ImagePydantic] = PydanticField(schemas.ImagePydantic, default=[])
    images_with_background: typing.List[schemas.ImagePydantic] = PydanticField(schemas.ImagePydantic, default=[])
    sticker_pack: typing.Awaitable['StickerPack'] = fields.ForeignKeyField(
        'models.StickerPack',
        on_delete=fields.CASCADE,
        related_name='stickers'
    )

    async def dict(self) -> dict:
        return dict(
            id=self.id, is_allowed=self.is_allowed,
            keywords=self.keywords, images=[img.dict() for img in self.images],
            images_with_background=[img.dict() for img in self.images_with_background],
            sticker_pack_id=self.sticker_pack_id
        )

    async def pydantic(self) -> schemas.Sticker:
        return schemas.Sticker.parse_obj(await self.dict())


class CallbackHost(Model):
    url: str = fields.CharField(max_length=2048, pk=True)
    methods: int = fields.IntField(default=int(CallbackTypes.CREATED | CallbackTypes.MODIFIED))


async def init_tortoise(db_url: str):
    await Tortoise.init(db_url=db_url, modules={'models': ['vk_stickers_api.models']})
    await Tortoise.generate_schemas()
