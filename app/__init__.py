from flask import Flask
from flask_cors import CORS  # Importa CORS

def create_app():
    app = Flask(__name__)
    
    # Permitir CORS desde localhost y Railway
    CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://backendprocessing-production.up.railway.app"]}})

    # Registrar las rutas
    from app.routes import api
    app.register_blueprint(api, url_prefix="/api")

    return app
