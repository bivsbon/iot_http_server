import json
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Body, Query, HTTPException
from gmqtt import Client as MQTTClient

from fastapi_mqtt import FastMQTT, MQTTConfig
from fastapi.middleware.cors import CORSMiddleware
from motor import motor_asyncio
from datetime import datetime

from starlette import status
from starlette.requests import Request

import config
import model

mqtt_config = MQTTConfig(ssl=True)
mqtt_config.host = config.MQTT_HOST
mqtt_config.port = int(config.MQTT_PORT)
mqtt_config.username = config.MQTT_USERNAME
mqtt_config.password = config.MQTT_PASSWORD

fast_mqtt = FastMQTT(config=mqtt_config)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await fast_mqtt.mqtt_startup()
    yield
    await fast_mqtt.mqtt_shutdown()


app = FastAPI(lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongodb_client = motor_asyncio.AsyncIOMotorClient(config.MONGODB_URL)
db = mongodb_client.get_database(config.DATABASE)
device_collection = db.get_collection("devices")
user_collection = db.get_collection("users")
home_collection = db.get_collection("homes")
device_type_collection = db.get_collection("device_types")
command_collection = db.get_collection("commands")
event_collection = db.get_collection("events")


async def validate_request(request):
    if config.API_KEY != request.query_params.get("api_key"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key"
        )


@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    print("Connected: ", client, flags, rc, properties)


@fast_mqtt.subscribe("device_events", qos=1)
async def home_message(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    payload = json.loads(payload.decode())

    result = await device_collection.find_one_and_update(
        filter={"device_id": payload["device_id"]},
        update={
            "$set": {
                "device_id": payload["device_id"],
                "data": payload["data"],
                "last_update": datetime.now()
            }
        },
        upsert=True,
        return_document=True  # Return the updated document, not the original
    )

    fast_mqtt.publish(f"smart_home/device/{result['device_id']}", json.dumps(payload))


@fast_mqtt.on_message()
async def message(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    print("Received message: ", topic, payload.decode(), qos, properties)


@fast_mqtt.on_disconnect()
def disconnect(client: MQTTClient, packet, exc=None):
    print("Disconnected")


@fast_mqtt.on_subscribe()
def subscribe(client: MQTTClient, mid: int, qos: int, properties: Any):
    print("subscribed", client, mid, qos, properties)


@app.post("/user",
          response_description="Register a user",
          response_model=model.User,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def add_user(request: Request, user: model.User = Body(...)):
    await validate_request(request)

    new_user = await user_collection.insert_one(
        user.model_dump(by_alias=True, exclude=["id"])
    )
    created_user = await user_collection.find_one(
        {"_id": new_user.inserted_id}
    )
    return created_user


@app.post("/user/login",
          response_description="Login",
          response_model=model.UserResponse,
          status_code=status.HTTP_200_OK,
          response_model_by_alias=False)
async def login_user(request: Request, user: model.User = Body(...)):
    await validate_request(request)

    found_user = await user_collection.find_one(
        {"username": user.username}
    )

    if found_user is None:
        return model.UserResponse(status=1, message="Wrong username")
    elif found_user["password"] != user.password:
        return model.UserResponse(status=2, message="Wrong password")
    else:
        return model.UserResponse(status=0, message="Success")


@app.post("/home",
          response_description="Add a home",
          response_model=model.Home,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def add_home(request: Request, home: model.Home = Body(...)):
    await validate_request(request)

    new_home = await home_collection.insert_one(
        home.model_dump(by_alias=True, exclude=["id"])
    )
    created_home = await home_collection.find_one(
        {"_id": new_home.inserted_id}
    )
    return created_home


@app.get("/home/{id}",
         response_description="Get a home",
         response_model=model.Home,
         status_code=status.HTTP_200_OK,
         response_model_by_alias=False)
async def get_home(request: Request, id: str):
    await validate_request(request)

    return home_collection.find_one(
        {"_id": id}
    )


@app.post("/device",
          response_description="Add a device to a home",
          response_model=model.Device,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def add_device(request: Request, device: model.Home = Body(...)):
    await validate_request(request)

    new_device = await device_collection.insert_one(
        device.model_dump(by_alias=True, exclude=["id"])
    )
    created_device = await device_collection.find_one(
        {"_id": new_device.inserted_id}
    )
    return created_device


@app.get("/device/{id}",
         response_description="Get a device",
         response_model=model.Device,
         status_code=status.HTTP_200_OK,
         response_model_by_alias=False)
async def get_device(request: Request, id: str):
    await validate_request(request)

    return device_collection.find_one(
        {"_id": id}
    )


@app.post("/device_type",
          response_description="Add a device type",
          response_model=model.DeviceType,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def add_device(request: Request, device_type: model.DeviceType = Body(...)):
    await validate_request(request)

    new_device_type = await device_type_collection.insert_one(
        device_type.model_dump(by_alias=True, exclude=["id"])
    )
    created_device_type = await device_type_collection.find_one(
        {"_id": new_device_type.inserted_id}
    )
    return created_device_type


@app.get("/device_type/{id}",
         response_description="Get a device",
         response_model=model.Device,
         status_code=status.HTTP_200_OK,
         response_model_by_alias=False)
async def get_device(request: Request, id: str):
    await validate_request(request)

    return device_collection.find_one(
        {"_id": id}
    )


@app.post("/event",
          response_description="Register an event",
          response_model=model.Event,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def add_device(request: Request, event: model.Event = Body(...)):
    await validate_request(request)

    new_event = await event_collection.insert_one(
        event.model_dump(by_alias=True, exclude=["id"])
    )
    created_event = await event_collection.find_one(
        {"_id": new_event.inserted_id}
    )
    return created_event


@app.get("/event/{id}",
         response_description="Get an event",
         response_model=model.Event,
         status_code=status.HTTP_200_OK,
         response_model_by_alias=False)
async def get_device(request: Request, id: str):
    await validate_request(request)

    return device_collection.find_one(
        {"_id": id}
    )


@app.post("/command",
          response_description="Add a command",
          response_model=model.Command,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def add_device(request: Request, command: model.Command = Body(...)):
    await validate_request(request)

    new_command = await command_collection.insert_one(
        command.model_dump(by_alias=True, exclude=["id"])
    )
    created_command = await command_collection.find_one(
        {"_id": new_command.inserted_id}
    )
    return created_command


@app.get("/command/{id}",
         response_description="Get a command",
         response_model=model.Device,
         status_code=status.HTTP_200_OK,
         response_model_by_alias=False)
async def get_device(request: Request, id: str):
    await validate_request(request)

    return device_collection.find_one(
        {"_id": id}
    )
