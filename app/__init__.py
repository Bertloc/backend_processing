from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Inicializar SQLAlchemy y Bcrypt
db = SQLAlchemy()
bcrypt = Bcrypt()

# Lista de orígenes permitidos (Render y Vercel)
ALLOWED_ORIGINS = [
    "https://cefront.vercel.app",
    "http://localhost:3000",
]

def create_app():
    app = Flask(__name__)

    # Configuración de la base de datos en Neotec
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://neondb_owner:npg_5DNYgZpAkf3J@ep-calm-thunder-a8qjumkh-pooler.eastus2.azure.neon.tech/neondb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar la base de datos con la app
    db.init_app(app)
    bcrypt.init_app(app)  # Inicialización de bcrypt

    # Configuración CORS (Aplica reglas específicas)
    CORS(app, resources={
        r"/*": {
            "origins": ALLOWED_ORIGINS,
            "supports_credentials": True,
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })

    # Importar modelos antes de usar la BD
    from app import models

    # Registrar rutas
    from app.routes import api
    app.register_blueprint(api, url_prefix="/api")

    # Middleware para aplicar encabezados CORS dinámicamente
    @app.after_request
    def apply_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    # Manejador de solicitudes preflight OPTIONS
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        response = jsonify({"message": "OK"})
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, 204

    return app

# Ejecutar aplicación
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
