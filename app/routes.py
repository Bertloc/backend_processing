from flask import Blueprint, request, jsonify
from sqlalchemy import func, case
import pandas as pd
import uuid
from app import db
from app.models import User,Pedido
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()  # Inicializar bcrypt

api = Blueprint('api', __name__)
data_store = {}  # Almacén temporal para clientes y sus datos procesados
# Almacén temporal para los enlaces generados (por ahora sin base de datos)
published_dashboards = {}

@api.route('/api/publish-data', methods=['POST'])
def publish_data():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se recibió archivo en la solicitud'}), 400

        file = request.files['file']
        df = pd.read_excel(file)  # Cargar el archivo completo
        batch_size = 100  # Reducido de 250 a 100 para evitar timeout

        print("✅ Archivo recibido y procesado en modo optimizado.")
        print(f"� Total de filas en el archivo: {len(df)}")

        pedidos_data = []

        for start in range(0, len(df), batch_size):
            end = start + batch_size
            chunk = df.iloc[start:end]  # Dividir DataFrame en lotes manualmente

            for _, row in chunk.iterrows():
                try:
                    pedidos_data.append({
                        'fecha_entrega': pd.to_datetime(row['Fecha Entrega'], errors='coerce').date() if pd.notna(row['Fecha Entrega']) else None,
                        'fecha_creacion': pd.to_datetime(row['Fecha Creación'], errors='coerce').date() if pd.notna(row['Fecha Creación']) else None,
                        'cantidad_entrega': int(row['Cantidad entrega']) if pd.notna(row['Cantidad entrega']) else 0,
                        'cantidad_pedido': int(row['Cantida Pedido']) if pd.notna(row['Cantida Pedido']) else 0,
                        'cantidad_confirmada': int(row['Cantidad confirmada']) if pd.notna(row['Cantidad confirmada']) else 0,
                        'estatus_pedido': row['Estatus Pedido'] if pd.notna(row['Estatus Pedido']) else None,
                        'centro': row['Centro'] if pd.notna(row['Centro']) else None,
                        'material': row['Material'] if pd.notna(row['Material']) else None,
                        'texto_breve_material': row['Texto breve de material'] if pd.notna(row['Texto breve de material']) else None,
                        'num_transporte': row['Nº de transporte'] if pd.notna(row['Nº de transporte']) else None,
                        'solicitante': row['Solicitante'] if pd.notna(row['Solicitante']) else None,
                        'nombre_solicitante': row['Nombre Solicitante'] if pd.notna(row['Nombre Solicitante']) else None,
                    })
                except Exception as row_error:
                    print(f"⚠️ Error en fila {row.get('Pedido', 'Desconocido')}: {row_error}")
                    continue  # Evita que una fila con error bloquee la inserción

            # Insertar el bloque en la base de datos de manera eficiente
            if pedidos_data:
                db.session.bulk_insert_mappings(Pedido, pedidos_data)
                db.session.flush()  # Forzar la escritura antes del commit
                db.session.commit()
                print(f"✅ Insertado un lote de {len(pedidos_data)} filas correctamente.")
                pedidos_data.clear()  # Liberar memoria

        return jsonify({'message': 'Datos publicados exitosamente'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al procesar la solicitud: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint para obtener el rol de un usuario por ID
@api.route('/get-user-role', methods=['GET'])
def get_user_role():
    user_id = request.args.get('user_id')  # Obtener el ID del usuario desde la URL

    # Buscar al usuario en la base de datos
    user = User.query.filter_by(id=user_id).first()

    if user:
        return jsonify({"role": user.rol})
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    contraseña = data.get('contraseña')

    # Buscar usuario en la base de datos
    user = User.query.filter_by(username=username).first()

    if user and user.contraseña == contraseña:
        return jsonify({"mensaje": "Inicio de sesión exitoso", "usuario": user.username, "rol": user.rol}), 200
    else:
        return jsonify({"mensaje": "Usuario o contraseña incorrectos"}), 401

@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Verificar si el usuario ya existe
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({"error": "El usuario ya existe"}), 400


    # Crear nuevo usuario
    new_user = User(
        username=data['username'],
        correo=data['correo'],
        contraseña = data.get('contraseña'),
        rol='cliente'
    )

    # Guardar en la base de datos
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"mensaje": "Usuario registrado exitosamente"}), 201


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

# ✅ Cumplimiento General
@api.route('/api/compliance-summary', methods=['GET'])
def compliance_summary():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Optimizar la consulta sumando directamente en la base de datos
        compliance_data = db.session.query(
            func.sum(case((Pedido.estatus_pedido == 'Despachado', Pedido.cantidad_pedido), else_=0)).label("Despachado"),
            func.sum(case((Pedido.estatus_pedido == 'Programado', Pedido.cantidad_pedido), else_=0)).label("Programado"),
            func.sum(case((Pedido.estatus_pedido == 'Confirmado', Pedido.cantidad_pedido), else_=0)).label("Confirmado"),
            func.sum(case((Pedido.estatus_pedido == 'No confirmado', Pedido.cantidad_pedido), else_=0)).label("No_confirmado")
        ).filter(
            Pedido.solicitante == client_id
        ).first()

        if not compliance_data:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        # Convertir los resultados en JSON
        result = {
            "Despachado": compliance_data.Despachado or 0,
            "Programado": compliance_data.Programado or 0,
            "Confirmado": compliance_data.Confirmado or 0,
            "No confirmado": compliance_data.No_confirmado or 0
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

# ✅ Tendencia Diaria
@api.route('/api/daily-trend', methods=['GET'])
def daily_trend():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            fecha = p.fecha_entrega.strftime('%Y-%m-%d') if p.fecha_entrega else "Desconocido"
            summary[fecha] = summary.get(fecha, 0) + p.cantidad_entrega

        result = [{"Fecha Entrega": k, "Cantidad entrega": v} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Asignación Mensual de Producto
@api.route('/api/monthly-product-allocation', methods=['GET'])
def monthly_product_allocation():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            mes = p.fecha_creacion.strftime('%Y-%m') if p.fecha_creacion else "Desconocido"
            clave = (mes, p.texto_breve_material)
            summary[clave] = summary.get(clave, 0) + p.cantidad_pedido

        result = [{"Mes": k[0], "Texto Breve Material": k[1], "Cantida Pedido": v} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Tendencias de Entrega
@api.route('/api/report-delivery-trends', methods=['GET'])
def report_delivery_trends():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            fecha = p.fecha_entrega.strftime('%Y-%m-%d') if p.fecha_entrega else "Desconocido"
            summary[fecha] = summary.get(fecha, 0) + p.cantidad_entrega

        result = [{"Fecha Entrega": k, "Cantidad entrega": v} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Reporte de Entrega
@api.route('/api/delivery-report', methods=['GET'])
def delivery_report():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            fecha = p.fecha_entrega.strftime('%Y-%m-%d') if p.fecha_entrega else "Desconocido"
            clave = (fecha, p.material)
            summary[clave] = summary.get(clave, 0) + p.cantidad_entrega

        result = [{"Fecha Entrega": k[0], "Material": k[1], "Cantidad entrega": v} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Distribución por Centro
@api.route('/api/distribution-by-center', methods=['GET'])
def distribution_by_center():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            centro = p.centro if p.centro else "Desconocido"
            summary[centro] = summary.get(centro, 0) + p.cantidad_entrega

        result = [{"Centro": k, "Cantidad entrega": v} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Resumen Diario
@api.route('/api/daily-summary', methods=['GET'])
def daily_summary():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            fecha = p.fecha_entrega.strftime('%Y-%m-%d') if p.fecha_entrega else "Desconocido"
            if fecha not in summary:
                summary[fecha] = {"Cantida Pedido": 0, "Cantidad entrega": 0}
            summary[fecha]["Cantida Pedido"] += p.cantidad_pedido
            summary[fecha]["Cantidad entrega"] += p.cantidad_entrega

        result = [{"Fecha Entrega": k, "Cantida Pedido": v["Cantida Pedido"], "Cantidad entrega": v["Cantidad entrega"], "% Aprovechamiento": round((v["Cantidad entrega"] / v["Cantida Pedido"] * 100) if v["Cantida Pedido"] else 0, 2)} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Pedidos Pendientes
@api.route('/api/pending-orders', methods=['GET'])
def pending_orders():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        # Agrupar pedidos pendientes por Material y sumar la Cantidad Confirmada
        pedidos = db.session.query(
            Pedido.material,
            func.sum(Pedido.cantidad_confirmada).label("Cantidad_confirmada")
        ).filter(
            Pedido.solicitante == client_id,
            Pedido.estatus_pedido == 'Pendiente'
        ).group_by(Pedido.material).all()

        if not pedidos:
            return jsonify({"error": "No hay pedidos pendientes para este cliente"}), 404

        # Convertir los resultados en un JSON válido
        result = [{"Material": p.material, "Cantidad confirmada": p.Cantidad_confirmada} for p in pedidos]
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Resumen por Categoría de Producto
@api.route('/api/product-category-summary', methods=['GET'])
def product_category_summary():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            categoria = p.texto_breve_material if p.texto_breve_material else "Desconocido"
            summary[categoria] = summary.get(categoria, 0) + p.cantidad_pedido

        result = [{"Texto breve de material": k, "Cantida Pedido": v} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

        
# ✅ Reporte Diario de Entregas
@api.route('/api/daily-delivery-report', methods=['GET'])
def daily_delivery_report():
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "El client_id es requerido"}), 400

        pedidos = Pedido.query.filter_by(solicitante=client_id).all()
        if not pedidos:
            return jsonify({"error": "No hay datos para este cliente"}), 404

        summary = {}
        for p in pedidos:
            fecha = p.fecha_entrega.strftime('%Y-%m-%d') if p.fecha_entrega else "Desconocido"
            clave = (fecha, p.texto_breve_material)
            if clave not in summary:
                summary[clave] = {"Total Entregado": 0, "Total Viajes": 0}
            summary[clave]["Total Entregado"] += p.cantidad_entrega
            summary[clave]["Total Viajes"] += 1  # Contar viajes

        result = [{"Fecha": k[0], "Producto": k[1], "Total Entregado": v["Total Entregado"], "Total Viajes": v["Total Viajes"]} for k, v in summary.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/get-client-orders/<solicitante>', methods=['GET'])
def get_client_orders(solicitante):
    try:
        # Consulta la base de datos para obtener los datos del cliente
        pedidos = Pedido.query.filter_by(solicitante=solicitante).all()

        if not pedidos:
            return jsonify({'error': 'No se encontraron datos para este cliente'}), 404

        # Convertir datos a formato JSON
        data = []
        for pedido in pedidos:
            data.append({
                'fecha_entrega': pedido.fecha_entrega.strftime('%Y-%m-%d') if pedido.fecha_entrega else None,
                'fecha_creacion': pedido.fecha_creacion.strftime('%Y-%m-%d') if pedido.fecha_creacion else None,
                'cantidad_entrega': pedido.cantidad_entrega,
                'cantidad_pedido': pedido.cantidad_pedido,
                'cantidad_confirmada': pedido.cantidad_confirmada,
                'estatus_pedido': pedido.estatus_pedido,
                'centro': pedido.centro,
                'material': pedido.material,
                'texto_breve_material': pedido.texto_breve_material,
                'num_transporte': pedido.num_transporte,
                'solicitante': pedido.solicitante,
                'nombre_solicitante': pedido.nombre_solicitante
            })

        return jsonify(data), 200

    except Exception as e:
        print(f"❌ Error al obtener datos del cliente {solicitante}: {str(e)}")
        return jsonify({'error': 'Error al obtener datos del cliente'}), 500


@api.route('/api/get-all-clients', methods=['GET'])
def get_all_clients():
    try:
        clientes = Pedido.query.with_entities(Pedido.solicitante, Pedido.nombre_solicitante).distinct().all()
        return jsonify([{'solicitante': c.solicitante, 'nombre_solicitante': c.nombre_solicitante} for c in clientes]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500