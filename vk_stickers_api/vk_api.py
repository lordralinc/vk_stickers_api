import logging
import typing
from hashlib import md5

import aiohttp

logger = logging.getLogger('VKAPI')


class ClientInfo(typing.TypedDict):
    id: int
    secret: str


class APIException(Exception):

    def __init__(self, data: dict):
        self.data = data


class VKAPI:
    _client: ClientInfo

    headers: dict = {
        'User-Agent': 'VKAndroidApp/4.38-849 (Android 6.0; SDK 23; x86; Google Nexus 5X; ru)'
    }

    def __init__(
            self,
            access_token: str,
            version: str = '5.137',
            lang: str = 'ru',
            client_id: int = 2274003,
            client_secret: str = 'hHbZxrka2uZ6jB1inYsH'
    ):
        self._client = {
            'id': client_id,
            'secret': client_secret
        }
        self._access_token = access_token
        self.version = version
        self.lang = lang
        self._session = None

    @property
    def session(self):
        if not self._session:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self._session

    def calculate_signature(
            self,
            method: str,
            optional_params: dict,
            required_params: dict
    ) -> str:
        to_hash = [f"{k}={v}" for k, v in optional_params.items()]
        to_hash += [f"{k}={v}" for k, v in required_params.items()]
        to_hash = "&".join(to_hash) + self._client['secret']
        to_hash = f"/method/{method}?" + to_hash
        return md5(to_hash.encode()).hexdigest()

    @classmethod
    async def authorize(
            cls,
            login: str,
            password: str,
            version: str = '5.137',
            lang: str = 'ru',
            client_id: int = 2274003,
            client_secret: str = 'hHbZxrka2uZ6jB1inYsH'
    ) -> "VKAPI":
        async with aiohttp.ClientSession(headers=cls.headers) as session:
            async with session.get(
                    f'https://oauth.vk.com/token',
                    params={
                        'grant_type': 'password',
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'username': login,
                        'password': password,
                        'v': version
                    }
            ) as response:
                access_token = (await response.json())['access_token']
        return cls(
            access_token,
            version,
            lang,
            client_id,
            client_secret
        )

    async def method(
            self,
            method: str,
            **kwargs
    ) -> dict:
        required_params = {
            'v': self.version,
            'https': 1,
            'lang': self.lang,
            'access_token': self._access_token
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        required_params = {k: v for k, v in required_params.items() if v is not None}
        required_params['sig'] = self.calculate_signature(method, kwargs, required_params)
        logger.info(f'Make request to API {method} with data {kwargs!r}')
        async with self.session.get(
                f'https://api.vk.com/method/{method}',
                params={k: v for k, v in {**kwargs, **required_params}.items() if v is not None}
        ) as response:
            data = await response.json()
            logger.info(f'Response is {data!r}')
        if 'error' in data:
            raise APIException(data)
        return data['response']
