from vk_stickers_api.routes import callback, sticker, users

routers = [
    callback.router,
    sticker.router,
    users.router
]
