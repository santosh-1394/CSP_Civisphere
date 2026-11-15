
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "4000"))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

    MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA", "")

    if MYSQL_SSL_CA and not Path(MYSQL_SSL_CA).is_absolute():
        MYSQL_SSL_CA = str(BASE_DIR / MYSQL_SSL_CA)

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
