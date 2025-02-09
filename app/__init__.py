from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Inicializar la base de datos y bcrypt
db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    # Configuración de la base de datos en Neotec
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://neondb_owner:npg_5DNYgZpAkf3J@ep-calm-thunder-a8qjumkh-pooler.eastus2.azure.neon.tech/neondb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar la base de datos con la app
    db.init_app(app)
    bcrypt.init_app(app)  # Inicialización de bcrypt

    # Importar modelos para que Flask los reconozca
    from app import models

    # Configuración CORS más permisiva para pruebas
    ALLOWED_ORIGINS = [
        "https://cefront.vercel.app",
        "http://localhost:3000",
    ]
    
    # Aplica CORS a toda la app, asegurando compatibilidad con credenciales
    CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS, "supports_credentials": True, "allow_headers": ["Content-Type", "Authorization"], "methods": ["GET", "POST", "OPTIONS"]}})

    # Registrar rutas
    from app.routes import api
    app.register_blueprint(api, url_prefix="/api")

    return app
