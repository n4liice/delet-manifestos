import os

from dotenv import load_dotenv

load_dotenv()


def _bool(valor, default):
    if valor is None:
        return default
    return valor.strip().lower() != "false"


URL_BASE = os.getenv("ESL_URL_BASE", "https://mandalog.eslcloud.com.br")
EMAIL = os.getenv("ESL_EMAIL")
SENHA = os.getenv("ESL_SENHA")

PORT = int(os.getenv("PORT", "3000"))
HEADLESS = _bool(os.getenv("HEADLESS"), True)
TIMEOUT_PADRAO = int(os.getenv("TIMEOUT_PADRAO", "15000"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "./screenshots")
