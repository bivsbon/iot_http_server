from pydantic import BaseModel, BeforeValidator, Field
from typing import Optional, Annotated

from datetime import datetime

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class CommonModel(BaseModel):
    create_time: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)
    deleted: bool = False


class Device(CommonModel):
    # The primary key for the UserEvent, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB,
    # but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    device_id: str
    # type_id: str
    data: dict = {}


class DeviceType(CommonModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = "Movement Sensor"
    default_attributes: dict = {
        "light": False,
        "movement": False
    }


class User(CommonModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    password: str
    home_id: str = ""
    role: str = ""


class Home(CommonModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    owner: str
    members: list[str] = []
    devices: list[str] = []


class Event(CommonModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    commands: list[str]


class Command(CommonModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)


class UserResponse(BaseModel):
    status: int
    message: str


# ------------------------- Request models ---------------------------------


class DeviceUpdate(BaseModel):
    device_id: int
    time: int
    data: dict