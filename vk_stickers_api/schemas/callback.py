import enum

import pydantic


class CallbackTypes(enum.IntFlag):
    CREATED = 1
    MODIFIED = 2


class CallbackHost(pydantic.BaseModel):
    url: str
    methods: int = pydantic.Field(
        default=int(CallbackTypes.CREATED | CallbackTypes.MODIFIED),
        ge=int(CallbackTypes.CREATED),
        le=int(CallbackTypes.CREATED | CallbackTypes.MODIFIED)
    )
