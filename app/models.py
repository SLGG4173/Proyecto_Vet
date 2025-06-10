from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import ENUM # Para el mapeo específico del ENUM si fuera necesario

# Importante: Aunque Usuario tiene set_password/check_password y UserMixin,
# en este diseño simplificado Dueno es el primary user de Flask-Login.
# Implementaremos el login de Usuario por separado (ej: con sesiones manuales).

class Dueno(UserMixin, db.Model):
    __tablename__ = 'Duenos'
    id = db.Column(db.Integer, primary_key=True)
    nombre_dueno = db.Column(db.String(100), nullable=False)
    apellido_dueno = db.Column(db.String(100), nullable=False)
    telefono_dueno = db.Column(db.String(20), nullable=True)
    email_dueno = db.Column(db.String(100), unique=True, nullable=False)
    direccion_dueno = db.Column(db.String(255), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    password_hash = db.Column(db.String(255), nullable=True)

    mascotas = db.relationship('Mascota', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Este get_id es CRUCIAL para Flask-Login si Dueno es el user loggeable
    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<Dueno {self.nombre_dueno} {self.apellido_dueno}>'

class Mascota(db.Model):
    __tablename__ = 'Mascotas'
    id = db.Column(db.Integer, primary_key=True)
    nombre_mascota = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50), nullable=True)
    raza = db.Column(db.String(50), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    id_dueno = db.Column(db.Integer, db.ForeignKey('Duenos.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    consultas = db.relationship('Consulta', backref='pet', lazy='dynamic')

    def __repr__(self):
        return f'<Mascota {self.nombre_mascota}>'

class Veterinario(db.Model):
    __tablename__ = 'Veterinarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_veterinario = db.Column(db.String(100), nullable=False)
    apellido_veterinario = db.Column(db.String(100), nullable=False)
    telefono_veterinario = db.Column(db.String(20), nullable=True)
    email_veterinario = db.Column(db.String(100), unique=True, nullable=True)
    licencia_veterinario = db.Column(db.String(50), nullable=True, unique=True) # Hacer licencia única si no lo estaba antes, es buena práctica
    fecha_contratacion = db.Column(db.Date, nullable=True)
    user_account = db.relationship('Usuario', backref='veterinario_profile', uselist=False, lazy='joined')
    
    consultas_atendidas = db.relationship('Consulta', backref='vet', lazy='dynamic')

    def __repr__(self):
        return f'<Veterinario {self.nombre_veterinario} {self.apellido_veterinario}>'

class Servicio(db.Model):
    __tablename__ = 'Servicios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_servicio = db.Column(db.String(100), nullable=False, unique=True)
    descripcion_servicio = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=True)

    def __repr__(self):
        return f'<Servicio {self.nombre_servicio}>'


class Consulta(db.Model):
    __tablename__ = 'Consultas'
    id = db.Column(db.Integer, primary_key=True)
    id_mascota = db.Column(db.Integer, db.ForeignKey('Mascotas.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    id_veterinario = db.Column(db.Integer, db.ForeignKey('Veterinarios.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    motivo_consulta = db.Column(db.Text, nullable=True)
    diagnostico = db.Column(db.Text, nullable=True) # Estos campos los llena el vet post-visita
    tratamiento = db.Column(db.Text, nullable=True)
    notas_adicionales = db.Column(db.Text, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    servicio_detalles = db.relationship('DetalleConsultaServicio', backref='consulta_relacionada', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        pet_name = self.pet.nombre_mascota if self.pet else 'N/A'
        vet_name = f'{self.vet.nombre_veterinario} {self.vet.apellido_veterinario}' if self.vet else 'N/A'
        return f'<Consulta {self.fecha_hora} | Mascota: {pet_name} | Vet: {vet_name}>'


class DetalleConsultaServicio(db.Model):
    __tablename__ = 'DetalleConsultaServicio'
    id_consulta = db.Column(db.Integer, db.ForeignKey('Consultas.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    id_servicio = db.Column(db.Integer, db.ForeignKey('Servicios.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    precio_cobrado = db.Column(db.Numeric(10, 2), nullable=True)

    def __repr__(self):
         return f'<DetalleConsulta id_consulta={self.id_consulta}, id_servicio={self.id_servicio}>'

# **Modelo USUARIO para Personal (ACTUALIZADO con FK)**
class Usuario(db.Model, UserMixin):
    __tablename__ = 'Usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) # Ahora nullable=False si siempre se crea con password
    nombre_completo = db.Column(db.String(150), nullable=True)
    rol = db.Column(db.String(50), default='recepcionista', nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=True) # Para activar/desactivar cuentas
    id_veterinario_profile = db.Column(db.Integer, db.ForeignKey('Veterinarios.id'), unique=True, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    
    def __repr__(self):
        return f'<Usuario {self.username} ({self.rol})>'