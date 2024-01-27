import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise

from vk_stickers_api import const, models
from vk_stickers_api.config import Config
from vk_stickers_api.cron import collect_stickers, shc
from vk_stickers_api.routes import routers
from vk_stickers_api.vk_api import VKAPI

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.basicConfig(level=logging.INFO)
    cfg = Config()
    await models.init_tortoise(cfg.DB_URL)
    if cfg.ACCESS_TOKEN:
        const.API = VKAPI(
            cfg.ACCESS_TOKEN,
            cfg.VK_API_VERSION,
            client_id=cfg.VK_API_CLIENT_ID,
            client_secret=cfg.VK_API_CLIENT_SECRET,
        )
    else:
        const.API = await VKAPI.authorize(
            cfg.LOGIN,
            cfg.PASSWORD,
            cfg.VK_API_VERSION,
            client_id=cfg.VK_API_CLIENT_ID,
            client_secret=cfg.VK_API_CLIENT_SECRET,
        )
    shc.start()
    if await models.StickerPack.all().count() == 0:
        await collect_stickers()

    yield

    await Tortoise.close_connections()
    await const.API.session.aclose()


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)
