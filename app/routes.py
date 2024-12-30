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


@api.route('/compliance-summary', methods=['POST'])
def compliance_summary():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Filtrar y procesar datos para el gráfico "Cumplimiento General"
        delivered = data[data['Estatus Pedido'] == 'Despachado']['Cantida Pedido'].sum()
        pending = data[data['Estatus Pedido'] == 'Programado']['Cantida Pedido'].sum()
        confirmed = data[data['Estatus Pedido'] == 'Confirmado']['Cantida Pedido'].sum()
        unconfirmed = data[data['Estatus Pedido'] == 'No confirmado']['Cantida Pedido'].sum()

        # Crear un resumen
        result = {
            "Despachado": delivered,
            "Programado": pending,
            "Confirmado": confirmed,
            "No confirmado": unconfirmed
        }

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/daily-trend', methods=['POST'])
def daily_trend():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Renombrar columnas si tienen nombres diferentes
        data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Cantidad entrega']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Procesar los datos agrupados por Fecha Entrega
        summary = data.groupby('Fecha Entrega')['Cantidad entrega'].sum()

        # Convertir el resultado a JSON
        result = summary.reset_index().to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/monthly-product-allocation', methods=['POST'])
def monthly_product_allocation():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Renombrar columnas para alinearlas con los nombres esperados
        data.rename(columns={
            'Fecha Creación': 'Fecha Creación',
            'Texto breve de material': 'Texto Breve Material',
            'Cantida Pedido': 'Cantida Pedido'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Creación', 'Texto Breve Material', 'Cantida Pedido']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Convertir la columna de fecha a formato datetime
        data['Fecha Creación'] = pd.to_datetime(data['Fecha Creación'], errors='coerce')

        # Crear una nueva columna para el mes y año
        data['Mes'] = data['Fecha Creación'].dt.to_period('M').astype(str)

        # Agrupar los datos por Mes y Texto Breve Material, y sumar Cantida Pedido
        summary = data.groupby(['Mes', 'Texto Breve Material'])['Cantida Pedido'].sum().reset_index()

        # Convertir los datos al formato JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/report-delivery-trends', methods=['POST'])
def report_delivery_trends():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Renombrar columnas si tienen nombres diferentes
        data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Cantidad entrega']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Procesar los datos agrupados por Fecha Entrega
        summary = data.groupby('Fecha Entrega')['Cantidad entrega'].sum()

        # Convertir el resultado a JSON
        result = summary.reset_index().to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/delivery-report', methods=['POST'])
def delivery_report():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Renombrar columnas si tienen nombres diferentes
        data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantidad entrega': 'Cantidad entrega',
            'Material': 'Material'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Material', 'Cantidad entrega']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Agrupar los datos por Fecha Entrega y Material
        summary = data.groupby(['Fecha Entrega', 'Material'])['Cantidad entrega'].sum().reset_index()

        # Convertir los datos al formato JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/distribution-by-center', methods=['POST'])
def distribution_by_center():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Renombrar columnas si tienen nombres diferentes
        data.rename(columns={
            'Centro': 'Centro',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Centro', 'Cantidad entrega']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Agrupar los datos por Centro
        summary = data.groupby('Centro')['Cantidad entrega'].sum().reset_index()

        # Convertir los datos al formato JSON
        result = summary.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/daily-summary', methods=['POST'])
def daily_summary():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Renombrar columnas si tienen nombres diferentes
        data.rename(columns={
            'Fecha Entrega': 'Fecha Entrega',
            'Cantida Pedido': 'Cantida Pedido',
            'Cantidad entrega': 'Cantidad entrega'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Cantida Pedido', 'Cantidad entrega']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Agrupar los datos por Fecha Entrega
        grouped = data.groupby('Fecha Entrega').agg({
            'Cantida Pedido': 'sum',
            'Cantidad entrega': 'sum'
        }).reset_index()

        # Calcular el % de aprovechamiento
        grouped['% Aprovechamiento'] = (grouped['Cantidad entrega'] / grouped['Cantida Pedido'] * 100).round(2)

        # Convertir los datos al formato JSON
        result = grouped.to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/pending-orders', methods=['POST'])
def pending_orders():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Renombrar columnas si tienen nombres diferentes
        data.rename(columns={
            'Estatus Pedido': 'Estatus Pedido',
            'Material': 'Material',
            'Cantidad confirmada': 'Cantidad confirmada'
        }, inplace=True)

        # Verificar si las columnas requeridas existen
        required_columns = ['Estatus Pedido', 'Material', 'Cantidad confirmada']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Filtrar pedidos donde Estatus Pedido sea "Pendiente"
        pending_orders = data[data['Estatus Pedido'] == 'Pendiente']

        # Seleccionar las columnas relevantes
        result = pending_orders[['Material', 'Cantidad confirmada']].to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/product-category-summary', methods=['POST'])
def product_category_summary():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Verificar si las columnas requeridas existen
        required_columns = ['Texto breve de material', 'Cantida Pedido']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Procesar los datos agrupados por categoría de producto
        summary = data.groupby('Texto breve de material')['Cantida Pedido'].sum()

        # Convertir el resultado a JSON
        result = summary.reset_index().to_dict(orient='records')

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/api/daily-delivery-report', methods=['POST'])
def daily_delivery_report():
    try:
        # Recibir el archivo subido
        file = request.files['file']
        data = pd.read_excel(file)

        # Verificar si las columnas requeridas existen
        required_columns = ['Fecha Entrega', 'Texto breve de material', 'Cantidad entrega', 'Nº de transporte']
        if not all(column in data.columns for column in required_columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_columns}"
            }), 400

        # Procesar los datos agrupados por fecha y producto
        summary = data.groupby(['Fecha Entrega', 'Texto breve de material']).agg({
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
