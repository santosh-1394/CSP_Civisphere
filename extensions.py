
import mysql.connector
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."

csrf = CSRFProtect()


def get_db_connection():
    connection_settings = {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "user": Config.MYSQL_USER,
        "password": Config.MYSQL_PASSWORD,
        "database": Config.MYSQL_DATABASE,
        "connection_timeout": 20,
        "ssl_ca": Config.MYSQL_SSL_CA,
        "ssl_verify_cert": True,
        "ssl_verify_identity": True
    }

    return mysql.connector.connect(**connection_settings)
