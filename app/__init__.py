from flask import Flask
from flask_cors import CORS  # Importa CORS

def create_app():
    app = Flask(__name__)
    
    # Habilitar CORS para toda la aplicación
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

    # Registrar las rutas
    from app.routes import api
    app.register_blueprint(api, url_prefix="/api")

    return app
