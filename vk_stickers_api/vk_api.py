import logging
import typing
from hashlib import md5

import httpx

logger = logging.getLogger("VKAPI")


class ClientInfo(typing.TypedDict):
    id: int
    secret: str


class APIException(Exception):
    def __init__(self, data: dict):
        self.data = data


class VKAPI:
    _client: ClientInfo

    headers: typing.ClassVar[dict[str, str]] = {
        "User-Agent": "VKAndroidApp/4.38-849 (Android 6.0; SDK 23; x86; Google Nexus 5X; ru)"
    }

    def __init__(
        self,
        access_token: str,
        version: str = "5.137",
        lang: str = "ru",
        client_id: int = 2274003,
        client_secret: str = "hHbZxrka2uZ6jB1inYsH",  # noqa: S107
    ):
        self._client = {"id": client_id, "secret": client_secret}
        self._access_token = access_token
        self.version = version
        self.lang = lang
        self._session = None

    @property
    def session(self):
        if not self._session:
            self._session = httpx.AsyncClient(headers=self.headers)
        return self._session

    def calculate_signature(
        self, method: str, optional_params: dict, required_params: dict
    ) -> str:
        to_hash = [f"{k}={v}" for k, v in optional_params.items()]
        to_hash += [f"{k}={v}" for k, v in required_params.items()]
        to_hash = "&".join(to_hash) + self._client["secret"]
        to_hash = f"/method/{method}?" + to_hash
        return md5(to_hash.encode()).hexdigest()  # noqa: S324

    @classmethod
    async def authorize(
        cls,
        login: str,
        password: str,
        version: str = "5.137",
        lang: str = "ru",
        client_id: int = 2274003,
        client_secret: str = "hHbZxrka2uZ6jB1inYsH",  # noqa: S107
    ) -> "VKAPI":
        async with httpx.AsyncClient() as session:
            response = await session.get(
                "https://oauth.vk.com/token",
                params={
                    "grant_type": "password",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": login,
                    "password": password,
                    "v": version,
                },
            )
        return cls(response.json()["access_token"], version, lang, client_id, client_secret)

    async def method(self, method: str, **kwargs) -> dict:
        required_params = {
            "v": self.version,
            "https": 1,
            "lang": self.lang,
            "access_token": self._access_token,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        required_params = {k: v for k, v in required_params.items() if v is not None}
        required_params["sig"] = self.calculate_signature(method, kwargs, required_params)
        logger.info(f"Make request to API {method} with data {kwargs!r}")  # noqa: G004
        response = await self.session.get(
            f"https://api.vk.com/method/{method}",
            params={k: v for k, v in {**kwargs, **required_params}.items() if v is not None},
        )
        data = response.json()
        if "error" in data:
            raise APIException(data)
        return data["response"]
