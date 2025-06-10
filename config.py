import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_por_defecto_muy_dificil' # Usa una clave robusta en producción
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///tmp/veterinaria.db' # Fallback a SQLite si no está en .env (para pruebas rápidas)
    SQLALCHEMY_TRACK_MODIFICATIONS = False