import os
from app import create_app
from waitress import serve

app = create_app()

if __name__ == "__main__":
    # Usando el puerto de la variable de entorno de Railway
    port = int(os.environ.get("PORT", 5000))  # $PORT dinámico o 5000 por defecto
    serve(app, host="0.0.0.0", port=port)
