from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate # Importa Migrate si lo usas

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'routes.login'
login_manager.login_message_category = 'info'

# Inicializar Migrate (si lo usas)
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Inicializar Migrate CON app Y db (si lo usas)
    migrate.init_app(app, db)

    from app import models # Importar modelos después de inicializar db

    @login_manager.user_loader
    def load_user(dueno_id):
        from app.models import Dueno # Importa aquí para evitar circularidad potencial en este punto
        return Dueno.query.get(int(dueno_id))

    # --- REGISTRAR EL BLUEPRINT ---
    # Importa el blueprint 'bp' desde el módulo routes
    from app.routes import bp # Asegúrate de que 'bp' está definido y exportado en app/routes.py
    # Registra el blueprint con la aplicación
    print(f"--- Intentando registrar blueprint '{bp.name}' ---")
    app.register_blueprint(bp) # <--- ¡Añade esta línea!
    print(f"--- Blueprint '{bp.name}' registrado ---")
    # ... (código para crear tablas si no usas migraciones, comentado) ...

    return app