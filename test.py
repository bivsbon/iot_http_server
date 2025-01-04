from bson import ObjectId
from motor import motor_asyncio

import config
import asyncio


mongodb_client = motor_asyncio.AsyncIOMotorClient(config.MONGODB_URL)
db = mongodb_client.get_database(config.DATABASE)
device_collection = db.get_collection("devices")
user_collection = db.get_collection("users")
home_collection = db.get_collection("homes")
device_type_collection = db.get_collection("device_types")
command_collection = db.get_collection("commands")
event_collection = db.get_collection("events")


def str_is_number(b: str) -> bool:
    return b.replace(".", "").isdigit()


def str_to_number(b: str) -> int or float:
    return float(b) if "." in b else int(b)


def event_is_triggered(event: dict, device: dict) -> bool:
    condition = event["condition"]
    a, operand, b = event["condition"].split(" ")
    if str_is_number(b):
        b = str_to_number(b)
    if operand == "<":
        return device["attributes"][a] < b
    elif operand == ">":
        return device["attributes"][a] > b
    elif operand == "=":
        return device["attributes"][a] == b
    elif operand == "<=":
        return device["attributes"][a] <= b
    elif operand == ">=":
        return device["attributes"][a] >= b


async def run():
    user = await user_collection.find_one(
            {"_id": ObjectId("6772a99af98ab1b4f1bde149")}
        )

    print(user["username"])

asyncio.run(run())
device = {"attributes": {
    "temperature": 10
}}

event = {"condition": "temperature = 10"}

print(event_is_triggered(event, device))
