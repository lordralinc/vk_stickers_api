from vk_stickers_api.routes import sticker, callback, users

routers = [
    callback.router,
    sticker.router,
    users.router
]
