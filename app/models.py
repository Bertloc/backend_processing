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
