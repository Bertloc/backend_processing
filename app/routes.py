from flask import Blueprint, request, jsonify
import pandas as pd

api = Blueprint('api', __name__)

@api.route('/upload', methods=['POST'])
def process_file():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Procesar los datos usando la columna correcta
        summary = data.groupby('Estatus Pedido')['Cantida Pedido'].sum()

        # Convertir el resultado a JSON
        result = summary.reset_index().to_dict(orient='records')

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
