from pydantic import BaseModel, BeforeValidator, Field
from typing import Optional, Annotated

from datetime import datetime

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class MailingTask(BaseModel):
    # The primary key for the UserEvent, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB,
    # but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    device_id: str
    # type_id: str
    data: dict
    create_time: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)


class DeviceUpdate(BaseModel):
    device_id: str
    data: dict
