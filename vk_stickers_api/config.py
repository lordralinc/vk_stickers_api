import typing

from pydantic import BaseSettings, root_validator


class Config(BaseSettings):
    ACCESS_TOKEN: typing.Optional[str] = None
    LOGIN: typing.Optional[str] = None
    PASSWORD: typing.Optional[str] = None
    DB_URL: typing.Optional[str] = None
    VK_API_VERSION: typing.Optional[str] = '5.137'
    VK_API_CLIENT_ID: int = 2274003
    VK_API_CLIENT_SECRET: str = 'hHbZxrka2uZ6jB1inYsH'

    @root_validator
    def validate_root(cls, values: dict):
        if not values.get('ACCESS_TOKEN') and not (values.get('LOGIN') and values.get('PASSWORD')):
            raise ValueError('Need access_token or login and password')
        return values

    class Config:
        env_prefix = 'VSA_'
        env_file = '.env'
