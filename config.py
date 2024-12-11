import os

from dotenv import load_dotenv


load_dotenv()

MONGODB_URL=os.getenv("MONGODB_URL")
DATABASE = os.getenv("DATABASE")

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

API_KEY = os.getenv("API_KEY")
