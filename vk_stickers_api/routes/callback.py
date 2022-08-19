import http
import typing

import tortoise.exceptions
from fastapi import APIRouter, HTTPException

from vk_stickers_api import models
from vk_stickers_api.schemas import callback as schemas

router = APIRouter(
    tags=['callback']
)


@router.get(
    '/callback',
    response_model=typing.List[schemas.CallbackHost],
    description='Получает список callback'
)
async def get_callbacks() -> typing.List[schemas.CallbackHost]:
    return [
        schemas.CallbackHost(url=host.url, methods=host.methods)
        async for host in models.CallbackHost.all()
    ]


@router.post(
    '/callback',
    response_model=schemas.CallbackHost,
    description='Устанавливает callback'
)
async def add_callback(host: schemas.CallbackHost) -> schemas.CallbackHost:
    try:
        await models.CallbackHost.create(
            url=host.url,
            methods=host.methods
        )
    except tortoise.exceptions.IntegrityError:
        raise HTTPException(http.HTTPStatus.BAD_REQUEST, detail='???')
    return host


@router.delete(
    '/callback',
    response_model=schemas.CallbackHost,
    description='Удаляет callback'
)
async def delete_callback(url: str) -> schemas.CallbackHost:
    try:
        host = await models.CallbackHost.get(url=url)
        await host.delete()
    except tortoise.exceptions.IntegrityError:
        raise HTTPException(http.HTTPStatus.BAD_REQUEST, detail='???')
    return schemas.CallbackHost(
        url=host.url,
        methods=host.methods
    )
