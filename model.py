from pydantic import BaseModel, BeforeValidator, Field
from typing import Optional, Annotated

from datetime import datetime

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class Device(BaseModel):
    # The primary key for the UserEvent, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB,
    # but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    device_id: str
    # type_id: str
    data: dict = {}
    create_time: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)


class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    password: str
    create_time: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)


class Home(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    owner: str
    members: list[str] = []
    devices: list[str] = []
    create_time: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)


class UserResponse(BaseModel):
    status: int
    message: str


# ------------------------- Request models ---------------------------------


class DeviceUpdate(BaseModel):
    device_id: int
    time: int
    data: dict