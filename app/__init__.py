from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # Configuración CORS para permitir ambos entornos
    CORS(app, resources={r"/*": {"origins": ["https://cefront.vercel.app","http://localhost:3000", "https://backend-processing.onrender.com"]}}, supports_credentials=True)

    # Registrar rutas
    from app.routes import api
    app.register_blueprint(api, url_prefix="/api")

    return app
