import os
from dotenv import load_dotenv, find_dotenv

load_dotenv()

download_folder = os.getenv("DL_FOLDER", "/var/chan/downloads/")
favorites_folder = os.getenv("FAVS_FOLDER", "/var/chan/favorites/")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "chan")
db_username = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "postgres")
auth_host = os.getenv("AUTH_HOST", "http://localhost:1234")