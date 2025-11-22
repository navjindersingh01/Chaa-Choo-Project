
import os
from datetime import timedelta

def _bool(env, default=False):
    return os.getenv(env, str(default)).lower() in ('1','true','yes')

class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-for-local')
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', str(60*60*24*7)))
    )
    SESSION_COOKIE_SECURE = _bool('SESSION_COOKIE_SECURE', True)
    DEBUG = _bool('DEBUG', False)

class DevelopmentConfig(BaseConfig):
    SESSION_COOKIE_SECURE = False
    DEBUG = True

class ProductionConfig(BaseConfig):
    pass
# ...existing code...# config.py - do NOT commit this file to public repo if it contains real passwords
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "11111111"
DB_NAME = "cafe_ca3"
SECRET_KEY = "699ca732aee1c3b289137ffa3841fe11921c6dd36a515a473024ca059ab32fec"
