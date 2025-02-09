from sqlalchemy import CheckConstraint
from app import db

class User(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(50), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='Cliente')

    __table_args__ = (
        CheckConstraint("LOWER(rol) IN ('admin', 'cliente')", name="usuarios_rol_check"),
    )

class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    centro = db.Column(db.String(50), nullable=False)
    desc_planta = db.Column(db.String(255), nullable=False)
    solicitante = db.Column(db.String(50), nullable=False)
    nombre_solicitante = db.Column(db.String(255), nullable=False)
    destinatario_mcia = db.Column(db.String(50), nullable=False)
    nombre_destinatario = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.Date, nullable=False)
    pedido = db.Column(db.String(50), nullable=False)
    estatus_pedido = db.Column(db.String(100), nullable=False)
    entrega = db.Column(db.String(50), nullable=False)
    fecha_entrega = db.Column(db.Date, nullable=False)
    material = db.Column(db.String(100), nullable=False)
    texto_breve_material = db.Column(db.String(255), nullable=False)
    cantidad_pedido = db.Column(db.Integer, nullable=False)
    cantidad_confirmada = db.Column(db.Integer, nullable=False)
    cantidad_entrega = db.Column(db.Integer, nullable=False)
    unidad_medida_base = db.Column(db.String(20), nullable=False)
    hora_act_desp_exp = db.Column(db.Time, nullable=True)
    sector = db.Column(db.String(100), nullable=False)
    fecha_requerida = db.Column(db.Date, nullable=True)
    hora_requerida = db.Column(db.Time, nullable=True)
    placa_vehiculo = db.Column(db.String(50), nullable=True)
    identif_un_manip = db.Column(db.String(50), nullable=True)
    fecha_mov_mcia_real = db.Column(db.Date, nullable=True)
    num_transporte = db.Column(db.String(50), nullable=True)
    inicio_actual_carga = db.Column(db.Date, nullable=True)
    hora_act_inic_carga = db.Column(db.Time, nullable=True)
    fecha_act_desp_exped = db.Column(db.Date, nullable=True)
