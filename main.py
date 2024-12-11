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


@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    print("Connected: ", client, flags, rc, properties)


@fast_mqtt.subscribe("smart_home/device_data", qos=1)
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


@app.get("/test")
async def func():
    print("publishing....")
    fast_mqtt.publish("smart_home/device_data", "Hello from Fastapi")  # publishing mqtt topic
    return {"result": True, "message": "Published"}


@app.post("/device-update")
async def device_update(device_update: model.DeviceUpdate):
    result = await device_collection.find_one_and_update(
        filter={"device_id": device_update.device_id},
        update={
            "$set": {
                "device_id": device_update.device_id,
                "data": device_update.data,
                "last_update": datetime.now()
            }
        },
        upsert=True,
        return_document=True  # Return the updated document, not the original
    )
    msg = {
        "device_id": device_update.device_id,
        "time": time.time(),
        "data": device_update.data
    }
    fast_mqtt.publish(f"smart_home/device/{result['device_id']}", msg)
    return result


@app.post("/user/register",
          response_description="Register",
          response_model=model.User,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def create_user(request: Request, user: model.User = Body(...)):
    if config.API_KEY != request.query_params.get("api_key"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key"
        )

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
async def create_user(request: Request, user: model.User = Body(...)):
    if config.API_KEY != request.query_params.get("api_key"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key"
        )
    found_user = await user_collection.find_one(
        {"username": user.username}
    )

    if found_user is None:
        return model.UserResponse(status=1, message="Wrong username")
    elif found_user["password"] != user.password:
        return model.UserResponse(status=2, message="Wrong password")
    else:
        return model.UserResponse(status=0, message="Success")
