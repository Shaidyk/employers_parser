import os
from dotenv import load_dotenv

load_dotenv()

CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")

BASE_URL_ROBOTA = 'https://robota.ua/candidates/'
