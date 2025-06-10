from flask import session, redirect, url_for, flash, current_app, g, request # <--- Añade request aquí
from functools import wraps
from app.models import Usuario
from flask_login import current_user

def load_staff_user_into_g():
    """Carga el usuario de staff desde la sesión a g.staff_user."""
    staff_user_id = session.get('staff_user_id')
    if staff_user_id:
        g.staff_user = Usuario.query.get(staff_user_id)
    else:
        g.staff_user = None

def staff_login_required(f):
    """Decorador para requerir que un usuario de staff esté logueado."""
    @wraps(f) # Preserva el nombre y documentación de la función original
    def decorated_function(*args, **kwargs):
        # Usamos g.staff_user que fue cargado por load_staff_user
        if g.staff_user is None:
            flash('Necesitas iniciar sesión como personal para acceder a esta página.', 'warning')
            # Redirigir a la página de login de staff
            return redirect(url_for('routes.staff_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorador para requerir que el usuario de staff logueado tenga uno de los roles especificados."""
    def decorator(f):
        @wraps(f)
        @staff_login_required # Asegurarse de que esté logueado como staff primero
        def decorated_function(*args, **kwargs):
            # Verificar si el usuario de staff tiene el rol requerido
            if g.staff_user is None or g.staff_user.rol not in roles:
                flash('No tienes permisos suficientes para ver esta página.', 'danger')
                # Redirigir a alguna página de acceso denegado o al dashboard del staff
                return redirect(url_for('routes.staff_dashboard')) # Asumimos que staff_dashboard existe
            return f(*args, **kwargs)
        return decorated_function
    return decorator