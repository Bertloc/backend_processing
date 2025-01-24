from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # Configuración CORS para permitir orígenes específicos y móviles
    ALLOWED_ORIGINS = [
        "https://cefront.vercel.app",
        "http://localhost:3000",
    ]

    # En producción, permite solo orígenes específicos
    # En desarrollo, permite todo (*)
    CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS if not app.debug else "*"}}, supports_credentials=True)

    # Registrar rutas
    from app.routes import api
    app.register_blueprint(api, url_prefix="/api")

    return app
