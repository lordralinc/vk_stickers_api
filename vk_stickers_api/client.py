import typing

import requests
import vk_stickers_api.schemas.sticker


class APIException(Exception):
    ...


class APIClient:

    def __init__(self, base_url: str):
        self.base_url = base_url

    def make_get_request(self, url: str, params: dict = None) -> dict:
        try:
            data = requests.get(self.base_url + url, params=params)
            if data.status_code == 200:
                return data.json()
            else:
                raise APIException(data.json())

        except:
            raise APIException()

    def get_sticker_packs(self) -> typing.List[vk_stickers_api.schemas.sticker.StickerPack]:
        return [
            vk_stickers_api.schemas.sticker.StickerPack.parse_obj(pack)
            for pack in self.make_get_request(f'/stickerPacks')
        ]

    def get_sticker_pack_by_id(self, pack_id: int) -> vk_stickers_api.schemas.sticker.StickerPack:
        return vk_stickers_api.schemas.sticker.StickerPack.parse_obj(
            self.make_get_request(f'/stickerPacks/{pack_id}')
        )

    def get_sticker_by_id(self, sticker_id: int) -> vk_stickers_api.schemas.sticker.Sticker:
        return vk_stickers_api.schemas.sticker.Sticker.parse_obj(
            self.make_get_request(f'/sticker/{sticker_id}')
        )

    def get_stickers_by_pack_by_id(self, pack_id: int) -> typing.List[vk_stickers_api.schemas.sticker.Sticker]:
        return [
            vk_stickers_api.schemas.sticker.Sticker.parse_obj(pack)
            for pack in self.make_get_request(f'/stickersByPack/{pack_id}')
        ]

    def get_user_sticker_packs(self, user_id: int) -> vk_stickers_api.schemas.sticker.UserStickerPacks:
        return vk_stickers_api.schemas.sticker.UserStickerPacks.parse_obj(
            self.make_get_request(f'/userStickerPacks/{user_id}')
        )
