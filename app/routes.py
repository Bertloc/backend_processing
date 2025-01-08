from flask import Blueprint, request, jsonify
from flask_cors import CORS
import pandas as pd
import uuid

api = Blueprint('api', __name__)
CORS(api)  # ✅ Agregar CORS al blueprint directamente
data_store = {}
published_dashboards = {}


@api.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado del backend"""
    return jsonify({"status": "ok"}), 200


@api.route('/api/publish-dashboards', methods=['POST'])
def publish_dashboards():
    try:
        # Recibir el archivo y extraer todos los clientes del frontend
        clients_data = request.form.get('clients')  # Espera un JSON string con los clientes
        if not clients_data:
            return jsonify({"error": "La lista de clientes es requerida."}), 400
        
        clients = json.loads(clients_data)  # Convertir el JSON string a lista

        # Crear un diccionario para almacenar múltiples enlaces generados
        generated_links = {}

        for client_id in clients:
            dashboard_uuid = str(uuid.uuid4())
            generated_links[client_id] = f"http://localhost:3000/dashboard/{dashboard_uuid}"
            published_dashboards[client_id] = generated_links[client_id]

        return jsonify({
            "message": "Dashboards publicados exitosamente.",
            "links": generated_links
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/upload', methods=['POST'])
def process_file():
    try:
        file = request.files['file']
        data = pd.read_excel(file)

        # Validación de columnas requeridas
        required_columns = ['Solicitante', 'Nombre Solicitante']
        if not all(column in data.columns for column in required_columns):
            return jsonify({"error": f"El archivo debe contener las columnas: {required_columns}"}), 400

        # Validación de datos vacíos
        if data.empty:
            return jsonify({"error": "El archivo está vacío o no tiene datos válidos."}), 400

        # Extraer clientes únicos y almacenar con Solicitate como clave (int)
        unique_clients = data[required_columns].drop_duplicates().to_dict(orient='records')
        data_store['clientes'] = {int(client['Solicitante']): client for client in unique_clients}

        print("Clientes almacenados:", data_store['clientes'])
        return jsonify({"clientes": unique_clients}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/compliance-summary', methods=['POST'])
def compliance_summary():
    try:
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        data = pd.read_excel(file)

        # ✅ Convertir a int y crear una copia explícita al filtrar
        client_id = int(client_id)
        filtered_data = data[data['Solicitante'] == client_id].copy()  

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ No es necesario cambiar más, ya que la copia fue creada
        delivered = filtered_data[filtered_data['Estatus Pedido'] == 'Despachado']['Cantida Pedido'].sum()
        pending = filtered_data[filtered_data['Estatus Pedido'] == 'Programado']['Cantida Pedido'].sum()
        confirmed = filtered_data[filtered_data['Estatus Pedido'] == 'Confirmado']['Cantida Pedido'].sum()
        unconfirmed = filtered_data[filtered_data['Estatus Pedido'] == 'No confirmado']['Cantida Pedido'].sum()

        result = {
            "Despachado": delivered,
            "Programado": pending,
            "Confirmado": confirmed,
            "No confirmado": unconfirmed
        }

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@api.route('/api/get-client-data/<int:client_id>', methods=['GET'])
def get_client_data(client_id):
    try:
        if client_id not in data_store['clientes']:
            return jsonify({"error": "Cliente no encontrado"}), 404
        return jsonify(data_store['clientes'][client_id]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/daily-trend', methods=['POST'])
def daily_trend():
    try:
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        data = pd.read_excel(file)

        # ✅ Convertir a int y crear una copia explícita al filtrar
        client_id = int(client_id)
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Modificar columnas usando .loc para evitar advertencias
        filtered_data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # ✅ Evitar SettingWithCopyWarning usando .loc
        filtered_data.loc[:, 'Fecha Entrega'] = pd.to_datetime(filtered_data['Fecha Entrega'], errors='coerce')

        # Agrupar los datos por Fecha Entrega
        summary = filtered_data.groupby('Fecha Entrega')['Cantidad entrega'].sum().reset_index()

        # Convertir el resultado a JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/monthly-product-allocation', methods=['POST'])
def monthly_product_allocation():
    try:
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        data = pd.read_excel(file)

        # ✅ Convertir a int y crear una copia explícita al filtrar
        client_id = int(client_id)
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Modificar columnas con .loc para evitar advertencias
        filtered_data.rename(columns={
            'Fecha Creación': 'Fecha Creación',
            'Texto breve de material': 'Texto Breve Material',
            'Cantida Pedido': 'Cantida Pedido'
        }, inplace=True)

        # ✅ Evitar SettingWithCopyWarning usando .loc
        filtered_data.loc[:, 'Fecha Creación'] = pd.to_datetime(filtered_data['Fecha Creación'], errors='coerce')
        filtered_data.loc[:, 'Mes'] = filtered_data['Fecha Creación'].dt.to_period('M').astype(str)

        # Agrupar los datos por Mes y Texto Breve Material
        summary = filtered_data.groupby(['Mes', 'Texto Breve Material'])['Cantida Pedido'].sum().reset_index()

        # Convertir los datos al formato JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/report-delivery-trends', methods=['POST'])
def report_delivery_trends():
    try:
        # Recibir el archivo subido y el client_id
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Leer el archivo y convertir el client_id a entero
        data = pd.read_excel(file)
        client_id = int(client_id)

        # ✅ Crear una copia explícita al filtrar
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Modificar columnas usando .loc para evitar advertencias
        filtered_data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Cantidad entrega']
        if not all(column in filtered_data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # ✅ Evitar advertencias al modificar columnas con .loc
        filtered_data.loc[:, 'Fecha Entrega'] = pd.to_datetime(filtered_data['Fecha Entrega'], errors='coerce')

        # Procesar los datos agrupados por Fecha Entrega
        summary = filtered_data.groupby('Fecha Entrega')['Cantidad entrega'].sum().reset_index()

        # Convertir el resultado a JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/delivery-report', methods=['POST'])
def delivery_report():
    try:
        # Recibir el archivo subido y el client_id
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Leer el archivo y convertir el client_id a entero
        data = pd.read_excel(file)
        client_id = int(client_id)

        # ✅ Crear una copia explícita para evitar el warning
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Modificar columnas usando .loc para evitar advertencias
        filtered_data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantidad entrega': 'Cantidad entrega',
            'Material': 'Material'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Material', 'Cantidad entrega']
        if not all(column in filtered_data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # ✅ Evitar advertencias modificando con .loc
        filtered_data.loc[:, 'Fecha Entrega'] = pd.to_datetime(filtered_data['Fecha Entrega'], errors='coerce')

        # Agrupar los datos por Fecha Entrega y Material
        summary = filtered_data.groupby(['Fecha Entrega', 'Material'])['Cantidad entrega'].sum().reset_index()

        # Convertir los datos al formato JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/distribution-by-center', methods=['POST'])
def distribution_by_center():
    try:
        # Recibir el archivo subido y el client_id
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Leer el archivo y convertir el client_id a entero
        data = pd.read_excel(file)
        client_id = int(client_id)

        # ✅ Crear una copia explícita al filtrar
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Modificar columnas usando .loc para evitar advertencias
        filtered_data.rename(columns={
            'Centro': 'Centro',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Centro', 'Cantidad entrega']
        if not all(column in filtered_data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # ✅ Evitar advertencias modificando con .loc
        filtered_data.loc[:, 'Cantidad entrega'] = filtered_data['Cantidad entrega']

        # Agrupar los datos por Centro
        summary = filtered_data.groupby('Centro')['Cantidad entrega'].sum().reset_index()

        # Convertir los datos al formato JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/daily-summary', methods=['POST'])
def daily_summary():
    try:
        # Recibir el archivo subido y el client_id
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Leer el archivo y convertir el client_id a entero
        data = pd.read_excel(file)
        client_id = int(client_id)

        # ✅ Crear una copia explícita al filtrar
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Modificar columnas usando .loc para evitar advertencias
        filtered_data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantida Pedido': 'Cantida Pedido',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Cantida Pedido', 'Cantidad entrega']
        if not all(column in filtered_data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # ✅ Evitar advertencias modificando con .loc
        filtered_data.loc[:, 'Fecha Entrega'] = pd.to_datetime(filtered_data['Fecha Entrega'], errors='coerce')

        # Agrupar los datos por Fecha Entrega
        grouped = filtered_data.groupby('Fecha Entrega').agg({
            'Cantida Pedido': 'sum',
            'Cantidad entrega': 'sum'
        }).reset_index()

        # ✅ Calcular el % de aprovechamiento sin advertencias
        grouped.loc[:, '% Aprovechamiento'] = (grouped['Cantidad entrega'] / grouped['Cantida Pedido'] * 100).round(2)

        # Convertir los datos al formato JSON
        result = grouped.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@api.route('/api/pending-orders', methods=['POST'])
def pending_orders():
    try:
        # Recibir el archivo subido y el client_id
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Leer el archivo y convertir el client_id a entero
        data = pd.read_excel(file)
        client_id = int(client_id)

        # ✅ Crear una copia explícita al filtrar
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Modificar columnas usando .loc para evitar advertencias
        filtered_data.rename(columns={
            'Estatus Pedido': 'Estatus Pedido',
            'Material': 'Material',
            'Cantidad confirmada': 'Cantidad confirmada'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Estatus Pedido', 'Material', 'Cantidad confirmada']
        if not all(column in filtered_data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # ✅ Aplicar filtro usando .loc para evitar advertencias
        pending_orders = filtered_data.loc[filtered_data['Estatus Pedido'] == 'Pendiente']

        # ✅ Selección segura usando .loc
        result = pending_orders.loc[:, ['Material', 'Cantidad confirmada']].to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@api.route('/api/product-category-summary', methods=['POST'])
def product_category_summary():
    try:
        # Recibir el archivo subido y el client_id
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Leer el archivo y convertir el client_id a entero
        data = pd.read_excel(file)
        client_id = int(client_id)

        # ✅ Crear una copia explícita al filtrar
        filtered_data = data[data['Solicitante'] == client_id].copy()

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # ✅ Validar columnas con una lista explícita
        required_columns = ['Texto breve de material', 'Cantida Pedido']
        if not all(column in filtered_data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # ✅ Procesar los datos de manera segura
        summary = (
            filtered_data
            .groupby('Texto breve de material', as_index=False)['Cantida Pedido']
            .sum()
        )

        # ✅ Convertir a formato JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/daily-delivery-report', methods=['POST'])
def daily_delivery_report():
    try:
        # Recibir el archivo subido y el client_id
        file = request.files['file']
        client_id = request.form.get('client_id')
        
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Leer el archivo y convertir el client_id a entero
        data = pd.read_excel(file)
        client_id = int(client_id)

        # Filtrar los datos por cliente
        filtered_data = data[data['Solicitante'] == client_id]

        if filtered_data.empty:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Texto breve de material', 'Cantidad entrega', 'Nº de transporte']
        if not all(column in filtered_data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Procesar los datos agrupados por fecha y producto
        summary = filtered_data.groupby(['Fecha Entrega', 'Texto breve de material']).agg({
            'Cantidad entrega': 'sum',
            'Nº de transporte': 'count'
        }).reset_index()

        # Renombrar columnas para mayor claridad
        summary.rename(columns={
            'Fecha Entrega': 'Fecha',
            'Texto breve de material': 'Producto',
            'Cantidad entrega': 'Total Entregado',
            'Nº de transporte': 'Total Viajes'
        }, inplace=True)

        # Convertir el resultado a JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
