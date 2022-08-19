import logging

from fastapi import FastAPI
from tortoise import Tortoise

from vk_stickers_api import const
from vk_stickers_api.config import Config
from vk_stickers_api.cron import shc, collect_stickers
from vk_stickers_api import models
from vk_stickers_api.routes import routers
from vk_stickers_api.vk_api import VKAPI


app = FastAPI()

for router in routers:
    app.include_router(router)


@app.on_event('startup')
async def on_startup():
    cfg = Config()
    await models.init_tortoise(cfg.DB_URL)
    if cfg.ACCESS_TOKEN:
        const.API = VKAPI(
            cfg.ACCESS_TOKEN,
            cfg.VK_API_VERSION,
            client_id=cfg.VK_API_CLIENT_ID,
            client_secret=cfg.VK_API_CLIENT_SECRET
        )
    else:
        const.API = await VKAPI.authorize(
            cfg.LOGIN,
            cfg.PASSWORD,
            cfg.VK_API_VERSION,
            client_id=cfg.VK_API_CLIENT_ID,
            client_secret=cfg.VK_API_CLIENT_SECRET
        )
    shc.start()
    if await models.StickerPack.all().count() == 0:
        await collect_stickers()


@app.on_event('shutdown')
async def on_startup():
    await Tortoise.close_connections()
    await const.API.session.close()
