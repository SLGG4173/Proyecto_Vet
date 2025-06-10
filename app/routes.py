from flask import render_template, redirect, url_for, flash, request, Blueprint, g, current_app, session, abort
from flask_wtf import FlaskForm
from app import db
from app.models import Dueno, Mascota, Veterinario, Consulta, DetalleConsultaServicio, Servicio, Usuario
from app.forms import (
    LoginForm, ClientRegistrationForm, MascotaForm,
    StaffLoginForm, ConsultaForm, DetalleConsultaServicioForm, # Formularios existentes
    VeterinarioFormStaff
)
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime, date, time
# Importar la función de carga de usuario staff y los decoradores desde app.decorators
# Asegúrate de que 'load_staff_user_into_g', 'staff_login_required', 'role_required' están DEFINIDOS
# en app/decorators.py sin referencias a 'bp'.
from app.decorators import load_staff_user_into_g, staff_login_required, role_required


# Definir el Blueprint. Todas las rutas definidas con @bp.route se adjuntarán a este.
# 'routes' es el nombre que usarás en url_for ('routes.index', 'routes.staff_login', etc.)
bp = Blueprint('routes', __name__)


# --- Aplicar el before_request para cargar g.staff_user DESPUÉS de definir bp ---
# Esta función se ejecutará ANTES de CADA petición manejada por este blueprint.
# Carga el usuario de staff (si está logueado en la sesión) en el objeto 'g'.
# Esto hace que g.staff_user esté disponible en las vistas y decoradores subsiguientes.
@bp.before_request
def before_request_load_staff():
     """Llama a la lógica para cargar el usuario de staff antes de cada request del BP."""
     load_staff_user_into_g() # Llama a la función definida en app.decorators.py


# ------------------ Rutas Públicas y de Dueño ------------------
# Estas rutas están accesibles para cualquiera, o protegidas con @login_required para Dueños.

# Ruta de inicio (Root URL)
@bp.route('/')
@bp.route('/index') # Ruta alternativa para la misma página
def index():
    # Deja este print temporalmente para confirmar si se ejecuta
    # print("--- FUNCION INDEX() EJECUTADA ---")

    # Si un Dueño está logueado, redirige a su dashboard
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    # Si un Staff está logueado, redirige a su dashboard (opcional, depende si index es solo público o tmb punto de entrada para staff)
    if g.staff_user:
         flash('Ya estás logueado como personal.', 'info') # Mensaje opcional
         return redirect(url_for('routes.staff_dashboard'))

    # Si nadie está logueado, muestra la página de inicio pública
    return render_template('index.html', title='Inicio Veterinaria')


# Ruta de Login para Dueños
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya hay un Dueño logueado, redirige
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    # Si un Staff está logueado, redirige al dashboard de Staff (no debe intentar loggearse como Dueño)
    if g.staff_user:
         flash('Ya estás logueado como personal. Cierra sesión de personal primero si deseas ingresar como Dueño.', 'info') # Mensaje más específico
         return redirect(url_for('routes.staff_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        # Busca el Dueño por email (campo del form)
        dueno = Dueno.query.filter_by(email_dueno=form.email.data).first()

        # Verifica si el Dueño existe y si la contraseña es correcta
        if dueno is None or not dueno.check_password(form.password.data):
            flash('Email o contraseña inválida para Dueño.', 'danger')
            return redirect(url_for('routes.login'))

        # Loguea al Dueño usando Flask-Login. 'remember' es la opción de recordarme.
        login_user(dueno, remember=form.remember_me.data)

        # Redirige al usuario a la página que intentaba acceder (si fue redirigido aquí por @login_required)
        # O redirige al dashboard del Dueño por defecto.
        next_page = request.args.get('next')
        # NOTA: En aplicaciones de producción, es crucial validar que 'next_page' es una URL segura
        # dentro de tu aplicación para prevenir ataques de redirección abiertos.
        # from urllib.parse import urlparse
        # if next_page and urlparse(next_page).netloc == '': # Basic check
        #    return redirect(next_page)
        # else:
        #    return redirect(url_for('routes.dashboard'))
        return redirect(next_page) if next_page else redirect(url_for('routes.dashboard'))

    # Renderiza el template de login si es GET o la validación falla
    return render_template('login.html', title='Ingreso de Dueño', form=form)


# Ruta de Logout para Dueños
@bp.route('/logout')
@login_required # Requiere que haya un Dueño logueado (Flask-Login)
def logout():
    logout_user() # Cierra la sesión del Dueño gestionada por Flask-Login
    flash('Has cerrado sesión de Dueño correctamente.', 'info')
    return redirect(url_for('routes.index')) # Redirige a la página de inicio


# Ruta de Registro para Nuevos Dueños (Clientes)
@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Si un Dueño ya está logueado, no puede registrarse de nuevo
    if current_user.is_authenticated:
        flash('Ya estás logueado como Dueño.', 'info')
        return redirect(url_for('routes.dashboard'))
    # Si un Staff está logueado, no puede registrar un Dueño desde aquí
    if g.staff_user:
         flash('Logueado como personal. No se puede registrar un Dueño desde aquí.', 'info')
         return redirect(url_for('routes.staff_dashboard'))

    form = ClientRegistrationForm()
    if form.validate_on_submit():
        # Crea un nuevo objeto Dueno a partir de los datos validados del formulario
        dueno = Dueno(
            nombre_dueno=form.nombre_dueno.data,
            apellido_dueno=form.apellido_dueno.data,
            email_dueno=form.email_dueno.data,
            telefono_dueno=form.telefono_dueno.data,
            direccion_dueno=form.direccion_dueno.data
        )
        dueno.set_password(form.password.data) # Hash la contraseña antes de guardarla

        try:
            db.session.add(dueno) # Añade el nuevo Dueño a la sesión de la DB
            db.session.commit() # Guarda los cambios permanentemente en la DB
            flash('¡Tu cuenta de Dueño ha sido creada exitosamente! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('routes.login')) # Redirige al login

        except Exception as e:
            db.session.rollback() # Deshace la transacción si ocurre algún error
            flash('Ocurrió un error al registrar la cuenta del Dueño.', 'danger')
            # Es bueno loggear el error en el servidor para depuración
            current_app.logger.error(f'Error durante el registro de Dueño: {e}', exc_info=True)


    # Renderiza el template de registro si es GET o la validación falla
    return render_template('register.html', title='Registro de Dueño', form=form)


# Ruta Dashboard para Dueños
@bp.route('/dashboard')
@login_required # Requiere que haya un Dueño logueado
def dashboard():
    # current_user es el objeto Dueño logueado (cargado por load_user de Flask-Login)
    dueno = current_user
    # Pasa el objeto Dueño al template
    return render_template('dashboard.html', title='Dashboard Dueño', dueno=dueno)


# Ruta para listar Mascotas de un Dueño logueado
@bp.route('/mascotas')
@login_required
def list_mascotas():
    # Accede a la relación 'mascotas' del Dueño logueado (objeto current_user)
    mascotas = current_user.mascotas.all()
    # Pasa la lista de mascotas al template
    return render_template('mascotas.html', title='Mis Mascotas', mascotas=mascotas)


# Ruta para agregar una nueva Mascota
@bp.route('/mascota/nueva', methods=['GET', 'POST'])
@login_required
def add_mascota():
    form = MascotaForm()

    if form.validate_on_submit():
        # Crea un objeto Mascota con los datos del formulario
        mascota = Mascota(
            nombre_mascota=form.nombre_mascota.data,
            especie=form.especie.data,
            raza=form.raza.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            # Asigna el Dueño logueado a la relación 'owner' (SQLAlchemy lo mapeará a id_dueno)
            owner=current_user
        )
        db.session.add(mascota)
        try:
            db.session.commit() # Guarda la nueva mascota en la DB
            flash(f'La mascota {mascota.nombre_mascota} ha sido agregada.', 'success')
            return redirect(url_for('routes.list_mascotas')) # Redirige al listado de mascotas

        except Exception as e:
             db.session.rollback()
             flash(f'Ocurrió un error al agregar la mascota {form.nombre_mascota.data}.', 'danger')
             current_app.logger.error(f'Error al agregar mascota: {e}', exc_info=True)


    # Renderiza el template del formulario si es GET o validación falla
    return render_template('mascota_form.html', title='Agregar Mascota', form=form)


# Ruta para ver el detalle de una Mascota específica (asegurando que pertenezca al Dueño)
@bp.route('/mascota/<int:mascota_id>') # El ID de la mascota en la URL
@login_required
def mascota_detail(mascota_id):
    # Busca la Mascota por su ID y que además su id_dueno coincida con el id del Dueño logueado
    # first_or_404() retornará la mascota si existe y pertenece al dueño, o un 404 Not Found si no
    mascota = db.session.query(Mascota)\
                .filter(Mascota.id == mascota_id, Mascota.id_dueno == current_user.id)\
                .first_or_404()

    # Carga las consultas relacionadas a esta mascota, ordenadas por fecha descendente
    # Accede a la relación 'consultas' definida en el modelo Mascota
    consultas = mascota.consultas.order_by(Consulta.fecha_hora.desc()).all()

    # Pasa la mascota encontrada y su lista de consultas al template
    return render_template('mascota_detail.html',
                           title=f'Detalle de {mascota.nombre_mascota}',
                           mascota=mascota,
                           consultas=consultas) # Puedes añadir otros datos como medical_records si implementas eso


# Ruta para listar TODAS las Consultas asociadas a las Mascotas del Dueño logueado
@bp.route('/consultas')
@login_required
def list_consultas():
    # Realiza un JOIN entre Consultas y Mascotas y filtra por el id_dueno del Dueño logueado
    # Esto recupera todas las consultas *para cualquiera de las mascotas* del Dueño.
    consultas = db.session.query(Consulta)\
        .join(Mascota)\
        .filter(Mascota.id_dueno == current_user.id)\
        .order_by(Consulta.fecha_hora.desc())\
        .all()

    # Pasa la lista de consultas (del dueño) al template
    return render_template('consultas.html', title='Mis Consultas', consultas=consultas)


# ------------------ Rutas para el Personal (Staff) ------------------
# Estas rutas están protegidas por @staff_login_required (login de Staff)
# y @role_required (basado en el rol del Staff logueado, usando g.staff_user).

# Ruta de Login para Personal
@bp.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    # Si un Dueño ya está logueado, redirige
    if current_user.is_authenticated:
         flash('Ya estás logueado como Dueño. Cierra sesión de Dueño si deseas ingresar como personal.', 'info')
         return redirect(url_for('routes.dashboard'))
    # Si un Staff ya está logueado (detectado por before_request en g.staff_user), redirige
    if g.staff_user:
         flash('Ya estás logueado como personal.', 'info')
         return redirect(url_for('routes.staff_dashboard')) # Asumiendo que staff_dashboard existe


    form = StaffLoginForm()
    if form.validate_on_submit():
        # Busca el usuario en la tabla Usuarios por username
        usuario = Usuario.query.filter_by(username=form.username.data).first()

        # Verifica si el usuario de Staff existe y si la contraseña es correcta
        if usuario is None or not usuario.check_password(form.password.data):
            flash('Nombre de usuario o contraseña inválida para Personal.', 'danger')
            return redirect(url_for('routes.staff_login'))

        # Verifica si el usuario Staff está activo
        if not usuario.is_active:
             flash('Tu cuenta de personal no está activa.', 'danger')
             return redirect(url_for('routes.staff_login'))

        # Login de Staff: usamos la sesión directamente (session object de Flask)
        session['staff_user_id'] = usuario.id
        session['staff_user_role'] = usuario.rol # Guarda el rol también para fácil acceso en decoradores/templates

        # flash('Inicio de sesión de Personal exitoso.', 'success') # Mensaje opcional de éxito

        # Redirigir al dashboard del staff o a la página 'next' si se guardó
        # El decorador @staff_login_required guarda la URL en 'staff_login_next'
        next_page = session.pop('staff_login_next', None)
         # NOTA: Similar al login de Dueño, valida 'next_page' para seguridad en producción.
        return redirect(next_page) if next_page else redirect(url_for('routes.staff_dashboard'))


    # Renderiza el template de login de staff
    return render_template('staff_login.html', title='Ingreso de Personal', form=form)


# Ruta de Logout para Personal
@bp.route('/staff/logout')
@staff_login_required # Requiere que haya un Staff logueado (chequeado por el decorador usando g.staff_user)
def staff_logout():
    # Cierra la sesión de Staff (limpia los valores que guardamos manualmente)
    session.pop('staff_user_id', None)
    session.pop('staff_user_role', None) # Limpia el rol
    # session.clear() # Opcional: Limpiar toda la sesión si no compartes nada con el login de Dueño
    flash('Has cerrado sesión de Personal correctamente.', 'info')
    # Redirige a la página de login de staff
    return redirect(url_for('routes.staff_login'))


# Ruta Dashboard para Personal
@bp.route('/staff')
@staff_login_required # Requiere que haya un Staff logueado
def staff_dashboard():
    # g.staff_user está disponible gracias al @bp.before_request y load_staff_user_into_g()
    # flash(f'Bienvenido, {g.staff_user.nombre_completo} ({g.staff_user.rol}).', 'success') # Mensaje en dashboard
    return render_template('staff_dashboard.html', title='Dashboard Staff')


# Ruta para listar TODAS las Consultas (vista Staff)
@bp.route('/staff/consultas')
@staff_login_required # Requiere staff logueado
# Solo permite el acceso a los roles de Recepcionista, Veterinario o Administrador
@role_required('recepcionista', 'veterinario', 'admin')
def staff_list_consultas():
    consultas = Consulta.query.order_by(Consulta.fecha_hora.desc()).all()


    return render_template('staff_consultas.html', title='Gestión de Consultas', consultas=consultas)


# Ruta para Agendar (Crear) una Nueva Consulta (vista Staff)
@bp.route('/staff/consultas/nueva', methods=['GET', 'POST'])
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin') # Roles permitidos para crear
def add_consulta():
    form = ConsultaForm() # Usamos el formulario de Consulta

    form.id_mascota.choices = [(0, '--- Seleccionar Mascota ---')] + [(m.id, f'{m.nombre_mascota} (Dueño: {m.owner.nombre_dueno if m.owner else "Sin Dueño"})') for m in Mascota.query.order_by(Mascota.nombre_mascota).all()]
    form.id_veterinario.choices = [(0, '--- Seleccionar Veterinario (Opcional) ---')] + [(v.id, f'Dr. {v.nombre_veterinario} {v.apellido_veterinario}') for v in Veterinario.query.order_by(Veterinario.nombre_veterinario).all()]


    if form.validate_on_submit():
        # Validaciones personalizadas adicionales después de WTForms (como SelectField 0)
        selected_mascota_id = form.id_mascota.data
        if selected_mascota_id == 0: # Chequear si la opción placeholder fue seleccionada
             flash('Por favor, selecciona una Mascota válida.', 'danger')
             # Si hay un error de validación, re-renderizar el formulario con los select fields poblados
             # Los selects ya fueron poblados arriba, y Flask-WTF debería mantener el valor seleccionado por el usuario si es posible
             return render_template('consulta_form.html', title='Agendar Consulta', form=form)

        # Combinar fecha (DateField) y hora (StringField) en un objeto datetime
        try:
            # Parsear la hora como HH:MM string a un objeto time
            time_obj = time(int(form.hora.data.split(':')[0]), int(form.hora.data.split(':')[1]))
            # Combinar la fecha del DateField y el objeto time
            fecha_hora_dt = datetime.combine(form.fecha.data, time_obj)
        except (ValueError, IndexError):
            # Si el formato de hora es incorrecto, mostrar un error y re-renderizar el form
            flash('Formato de hora inválido. Usa HH:MM.', 'danger')
             # Re-renderiza con los select fields poblados
            return render_template('consulta_form.html', title='Agendar Consulta', form=form)

        # Manejar SelectField de Veterinario (0 es válido para opcional)
        selected_vet_id = form.id_veterinario.data if form.id_veterinario.data != 0 else None


        # Crear el objeto Consulta con los datos del formulario
        consulta = Consulta(
            id_mascota=selected_mascota_id, # id ya es entero por coerce=int
            id_veterinario=selected_vet_id,
            fecha_hora=fecha_hora_dt,
            motivo_consulta=form.motivo_consulta.data,
            # Los campos diagnostico, tratamiento, notas_adicionales inician como NULL/None
            diagnostico=None,
            tratamiento=None,
            notas_adicionales=None
            # fecha_creacion se llena por default
        )

        db.session.add(consulta) # Añade a la sesión
        try:
            db.session.commit() # Guarda en la DB
            flash('Consulta agendada correctamente.', 'success')
            return redirect(url_for('routes.staff_list_consultas')) # Redirige al listado

        except Exception as e:
             db.session.rollback() # Si hay error en DB, deshace
             flash('Ocurrió un error al agendar la consulta.', 'danger')
             current_app.logger.error(f'Error al agendar consulta: {e}', exc_info=True)
              # Re-renderiza con los select fields poblados y los datos enviados por el usuario
             return render_template('consulta_form.html', title='Agendar Consulta', form=form)


    return render_template('consulta_form.html', title='Agendar Consulta', form=form)


# Ruta para Editar los detalles de una Consulta existente (vista Staff)
@bp.route('/staff/consultas/<int:consulta_id>/editar', methods=['GET', 'POST'])
@staff_login_required
def edit_consulta(consulta_id):
    # Recuperar la consulta por su ID. Si no existe, 404.
    consulta = Consulta.query.get_or_404(consulta_id)

    # Crear el formulario. En una petición GET, 'obj=consulta' llenará el formulario con los datos existentes.
    form = ConsultaForm(obj=consulta)

    add_service_form = DetalleConsultaServicioForm()
    # **POBLAR SELECT FIELDS DINÁMICAMENTE para el formulario de SERVICIO**
    add_service_form.id_servicio.choices = [(0, '--- Seleccionar Servicio ---')] + [(s.id, s.nombre_servicio) for s in Servicio.query.order_by(Servicio.nombre_servicio).all()]

    form.id_mascota.choices = [(0, '--- Seleccionar Mascota ---')] + [(m.id, f'{m.nombre_mascota} (Dueño: {m.owner.nombre_dueno if m.owner else "Sin Dueño"})') for m in Mascota.query.order_by(Mascota.nombre_mascota).all()]
    form.id_veterinario.choices = [(0, '--- Seleccionar Veterinario (Opcional) ---')] + [(v.id, f'Dr. {v.nombre_veterinario} {v.apellido_veterinario}') for v in Veterinario.query.order_by(Veterinario.nombre_veterinario).all()]

    # En el caso de GET, la fecha_hora de la DB necesita dividirse en Date y Time para el formulario
    # Esto no se hace automáticamente con obj=consulta si los tipos de campos son diferentes.
    if request.method == 'GET' and consulta.fecha_hora:
        form.fecha.data = consulta.fecha_hora.date() # Asigna solo la parte de la fecha al DateField
        form.hora.data = consulta.fecha_hora.time().strftime('%H:%M') # Formatea la hora a HH:MM string


    # **Validación del Formulario Principal de Consulta al hacer POST**
    if form.validate_on_submit():
        # **COMBINAR FECHA Y HORA DEL FORMULARIO - Similares al add**
        try:
            # Parsear la hora (string HH:MM)
            time_obj = time(int(form.hora.data.split(':')[0]), int(form.hora.data.split(':')[1]))
            # Combinar fecha del DateField con el objeto time
            fecha_hora_dt = datetime.combine(form.fecha.data, time_obj)
             # Asigna el datetime combinado al objeto Consulta
            consulta.fecha_hora = fecha_hora_dt
        except (ValueError, IndexError):
             # Si el formato de hora es incorrecto, mostrar un error y re-renderizar
             flash('Formato de hora inválido. Usa HH:MM.', 'danger')
             # Vuelve a rellenar y mantener los select field selections
             form.id_mascota.choices = [(0, '--- Seleccionar Mascota ---')] + [(m.id, f'{m.nombre_mascota} (Dueño: {m.owner.nombre_dueno if m.owner else "Sin Dueño"})') for m in Mascota.query.order_by(Mascota.nombre_mascota).all()]
             form.id_veterinario.choices = [(0, '--- Seleccionar Veterinario (Opcional) ---')] + [(v.id, f'Dr. {v.nombre_veterinario} {v.apellido_veterinario}') for v in Veterinario.query.order_by(Veterinario.nombre_veterinario).all()]
             if form.id_mascota.data != 0: form.id_mascota.data = form.id_mascota.data
             if form.id_veterinario.data != 0: form.id_veterinario.data = form.id_veterinario.data
             # Para campos de texto (hora), WTForms mantiene el valor enviado si validation.fail. Manual para DateField/Time.
             if request.form.get('fecha'): form.fecha.data = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
             if request.form.get('hora'): form.hora.data = request.form['hora']
             return render_template('consulta_form.html', title='Editar Consulta', form=form, consulta=consulta, add_service_form=add_service_form)

        # Validación de SelectField Mascota 0 (placeholder)
        selected_mascota_id = form.id_mascota.data
        if selected_mascota_id == 0:
             flash('Por favor, selecciona una Mascota válida.', 'danger')
             # Re-renderiza con selects y datos poblados
             form.id_mascota.choices = [(0, '--- Seleccionar Mascota ---')] + [(m.id, f'{m.nombre_mascota} (Dueño: {m.owner.nombre_dueno if m.owner else "Sin Dueño"})') for m in Mascota.query.order_by(Mascota.nombre_mascota).all()]
             form.id_veterinario.choices = [(0, '--- Seleccionar Veterinario (Opcional) ---')] + [(v.id, f'Dr. {v.nombre_veterinario} {v.apellido_veterinario}') for v in Veterinario.query.order_by(Veterinario.nombre_veterinario).all()]
             if form.id_mascota.data != 0: form.id_mascota.data = form.id_mascota.data
             if form.id_veterinario.data != 0: form.id_veterinario.data = form.id_veterinario.data
             if request.form.get('fecha'): form.fecha.data = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
             if request.form.get('hora'): form.hora.data = request.form['hora']
             return render_template('consulta_form.html', title='Editar Consulta', form=form, consulta=consulta, add_service_form=add_service_form)

        # Manejar SelectField Veterinario (0 es None si es opcional)
        selected_vet_id = form.id_veterinario.data if form.id_veterinario.data != 0 else None
        consulta.id_veterinario = selected_vet_id # Actualiza el campo


        # Actualizar otros campos DE CONSULTA (Motivo)
        consulta.motivo_consulta = form.motivo_consulta.data
        consulta.id_mascota = selected_mascota_id # Actualiza la mascota si se cambió

        if g.staff_user and (g.staff_user.rol in ['veterinario', 'admin']):
             consulta.diagnostico = form.diagnostico.data # Estos campos se actualizan solo por roles permitidos
             consulta.tratamiento = form.tratamiento.data
             consulta.notas_adicionales = form.notas_adicionales.data
    

        try:
            db.session.commit() # Guarda los cambios del objeto consulta
            flash('Consulta actualizada correctamente.', 'success')
            # Redirige al listado de consultas
            return redirect(url_for('routes.staff_list_consultas'))

        except Exception as e:
            db.session.rollback() # Deshace si hay error en DB
            flash('Ocurrió un error al actualizar la consulta.', 'danger')
            current_app.logger.error(f'Error al actualizar consulta {consulta_id}: {e}', exc_info=True)
             # Si el commit falla, re-renderiza el formulario manteniendo datos y errores
             # Vuelve a poblar selects y mantener selections/datos enviados.
            form.id_mascota.choices = [(0, '--- Seleccionar Mascota ---')] + [(m.id, f'{m.nombre_mascota} (Dueño: {m.owner.nombre_dueno if m.owner else "Sin Dueño"})') for m in Mascota.query.order_by(Mascota.nombre_mascota).all()]
            form.id_veterinario.choices = [(0, '--- Seleccionar Veterinario (Opcional) ---')] + [(v.id, f'Dr. {v.nombre_veterinario} {v.apellido_veterinario}') for v in Veterinario.query.order_by(Veterinario.nombre_veterinario).all()]
            if form.id_mascota.data != 0: form.id_mascota.data = form.id_mascota.data
            if form.id_veterinario.data != 0: form.id_veterinario.data = form.id_veterinario.data
             # Recupera hora/fecha si se enviaron y causaron el fallo en DB commit
            if request.form.get('fecha'): form.fecha.data = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            if request.form.get('hora'): form.hora.data = request.form['hora']
            return render_template('consulta_form.html', title='Editar Consulta', form=form, consulta=consulta, add_service_form=add_service_form) # Pasa consulta y add_service_form

    return render_template('consulta_form.html', title='Editar Consulta', form=form, consulta=consulta, add_service_form=add_service_form) # Asegúrate de pasar consulta y add_service_form siempre


# Ruta para Eliminar una Consulta (vista Staff) - Usamos POST para mayor seguridad con CSRF
@bp.route('/staff/consultas/<int:consulta_id>/eliminar', methods=['POST'])
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin') # Roles permitidos para cancelar
def delete_consulta(consulta_id):
    # Recuperar la consulta. Si no existe, 404.
    consulta = Consulta.query.get_or_404(consulta_id)

    try:
        # Capturar info de la mascota antes de borrar la consulta para el mensaje flash
        pet_name = consulta.pet.nombre_mascota if consulta.pet else "Mascota Desconocida"

        db.session.delete(consulta) # Elimina el objeto de la sesión
        db.session.commit() # Confirma la eliminación en la DB
        # flash(f'Consulta para {pet_name} del {consulta.fecha_hora.strftime("%Y-%m-%d %H:%M")} cancelada.', 'success') # Fecha_hora no accesible después del commit!
        flash(f'Consulta para {pet_name} cancelada correctamente.', 'success')


    except Exception as e:
        db.session.rollback() # Deshace la eliminación si hay error en DB
        flash('Ocurrió un error al cancelar la consulta.', 'danger')
        current_app.logger.error(f'Error al eliminar consulta {consulta_id}: {e}', exc_info=True)


    # Redirige al listado de consultas de staff
    return redirect(url_for('routes.staff_list_consultas'))

@bp.route('/staff/consultas/<int:consulta_id>/agregar-servicio', methods=['POST'])
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin') # Roles permitidos para agregar servicios/cobros
def add_detalle_servicio_to_consulta(consulta_id):
    # Asegurarse de que la consulta a la que se añadirá el servicio existe
    consulta = Consulta.query.get_or_404(consulta_id)

    # Crear y validar el formulario de detalle de servicio (recibe datos del POST)
    add_service_form = DetalleConsultaServicioForm()
    # **POBLAR SELECT FIELDS DINÁMICAMENTE para la validación del formulario de Servicio**
    add_service_form.id_servicio.choices = [(0, '--- Seleccionar Servicio ---')] + [(s.id, s.nombre_servicio) for s in Servicio.query.order_by(Servicio.nombre_servicio).all()]

    if add_service_form.validate_on_submit():
        selected_service_id = add_service_form.id_servicio.data
        # Validación SelectField Servicio 0 (placeholder)
        if selected_service_id == 0:
            flash('Por favor, selecciona un Servicio válido.', 'danger')
             # Redirige de vuelta a la página de edición (se pierden los datos del form, pero el mensaje flash ayuda)
            return redirect(url_for('routes.edit_consulta', consulta_id=consulta.id))


        # Checkear si el servicio ya está vinculado a esta consulta para evitar duplicados
        existing_detail = DetalleConsultaServicio.query.filter_by(
            id_consulta=consulta.id, id_servicio=selected_service_id
        ).first()

        if existing_detail:
             flash('Este servicio ya ha sido agregado a esta consulta.', 'warning')
             # Redirige de vuelta
             return redirect(url_for('routes.edit_consulta', consulta_id=consulta.id))


        # Crear el objeto DetalleConsultaServicio
        detalle = DetalleConsultaServicio(
            id_consulta=consulta.id, # Usa el ID de la consulta de la URL de la ruta
            id_servicio=selected_service_id, # id ya es entero por coerce=int
            precio_cobrado=add_service_form.precio_cobrado.data # Puede ser None si el campo no es DataRequired
        )

        db.session.add(detalle) # Añade a la sesión
        try:
            db.session.commit() # Guarda en la DB
            flash('Servicio agregado a la consulta correctamente.', 'success')
        except Exception as e:
            db.session.rollback() # Deshace si hay error
            # Puedes chequear e.orig.args si quieres verificar violaciones de constraint (ej. clave primaria duplicada si no chequeaste existing_detail)
            flash('Ocurrió un error al agregar el servicio.', 'danger')
            current_app.logger.error(f'Error al agregar servicio a consulta {consulta_id}: {e}', exc_info=True)

    else:
       for field, errors in add_service_form.errors.items():
             for error in errors:
                 flash(f"Error en el campo '{add_service_form[field].label.text}' del Servicio: {error}", 'danger')


    # Siempre redirige de vuelta a la página de edición de la consulta, sin importar el resultado.
    return redirect(url_for('routes.edit_consulta', consulta_id=consulta.id))

# --- NUEVAS RUTAS PARA GESTIONAR VETERINARIOS (Requiere rol 'admin') ---

# Ruta para listar todos los Veterinarios
@bp.route('/staff/veterinarios')
@staff_login_required
@role_required('admin') # Solo administradores pueden ver la lista para gestionarla
def staff_list_veterinarios():
    veterinarios = Veterinario.query.order_by(Veterinario.apellido_veterinario, Veterinario.nombre_veterinario).all()
    csrf_form = FlaskForm() # Solo necesitas un formulario para acceder a {{ csrf_token() }} o {{ form.csrf_token }}
    
    return render_template('staff_veterinarios_list.html',
                           title='Gestionar Veterinarios',
                           veterinarios=veterinarios,
                           csrf_form=csrf_form) # <-- PASA el formulario aquí


# Ruta para Añadir un Nuevo Perfil de Veterinario
@bp.route('/staff/veterinarios/nueva', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin') # Solo administradores pueden añadir veterinarios
def staff_add_veterinario():
    form = VeterinarioFormStaff()

    if form.validate_on_submit():
        # Crear el objeto Veterinario primero
        veterinario = Veterinario(
            nombre_veterinario=form.nombre_veterinario.data,
            apellido_veterinario=form.apellido_veterinario.data,
            telefono_veterinario=form.telefono_veterinario.data,
            email_veterinario=form.email_veterinario.data,
            licencia_veterinario=form.licencia_veterinario.data,
            fecha_contratacion=form.fecha_contratacion.data # Esto es un DateField
        )

        db.session.add(veterinario) # Añadir el veterinario a la sesión para obtener un ID si es necesario inmediatamente


        # Lógica para crear/vincular Cuenta de Usuario Staff si el checkbox está marcado
        if form.create_user_account.data:
            
            usuario = Usuario(
                 username=form.username.data,
                 nombre_completo=f'{form.nombre_veterinario.data} {form.apellido_veterinario.data}', # Usar el nombre del vet como nombre completo por defecto
                 rol='veterinario', # El rol fijo es 'veterinario' para cuentas vinculadas a un perfil de Vet
                 is_active=form.is_active.data, # Desde el checkbox del form
                 veterinario_profile=veterinario # Vincula este Usuario al Veterinario creado arriba (SQLAlchemy se encarga de id_veterinario_profile)
            )
            usuario.set_password(form.user_password.data) # Hash la contraseña

            db.session.add(usuario) # Añadir el usuario a la sesión

        try:
            db.session.commit() # Guarda ambos (Veterinario y Usuario si se creó)
            flash(f'Perfil de Veterinario {veterinario.apellido_veterinario} creado exitosamente' + (' con cuenta de Staff.' if form.create_user_account.data else '.'), 'success')
            # Redirige al listado de veterinarios
            return redirect(url_for('routes.staff_list_veterinarios'))

        except Exception as e:
            db.session.rollback() # Deshace si algo falla
            flash('Ocurrió un error al guardar el Veterinario.', 'danger')
            current_app.logger.error(f'Error al añadir Veterinario: {e}', exc_info=True)

    return render_template('staff_veterinario_form.html', title='Añadir Veterinario', form=form, is_edit=False) # Pasamos un flag


# Ruta para Editar un Perfil de Veterinario Existente
@bp.route('/staff/veterinarios/<int:vet_id>/editar', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin') # Solo administradores pueden editar veterinarios
def staff_edit_veterinario(vet_id):
    # Recuperar el perfil de Veterinario existente. Si no existe, 404.
    veterinario = Veterinario.query.get_or_404(vet_id)
    # Intentar obtener la cuenta de usuario asociada (si existe) usando la relación user_account
    usuario_asociado = veterinario.user_account # Esta es la relación definida en el modelo Veterinario


    form = VeterinarioFormStaff(obj=veterinario)

    # Si es GET, llenamos manualmente los campos de usuario y la checkbox si existe cuenta
    if request.method == 'GET' and usuario_asociado:
        form.create_user_account.data = True # Marca el checkbox si ya hay cuenta asociada
        form.username.data = usuario_asociado.username
        # No se llena el campo user_password por seguridad (requerir cambiarla si se quiere)
        form.is_active.data = usuario_asociado.is_active
        


    if form.validate_on_submit():
        # Actualizar campos del Perfil de Veterinario desde el formulario
        form.populate_obj(veterinario) # Actualiza nombre, tel, email, licencia, fecha_contratacion en 'veterinario' object

        # Lógica para crear/vincular/desvincular Cuenta de Usuario Staff
        if form.create_user_account.data: # Si el checkbox SE MARCO O ESTABA MARCADO y se volvió a enviar
             # Si ya existía una cuenta de usuario asociada, LA ACTUALIZAMOS.
            if usuario_asociado:
                usuario = usuario_asociado # Usar el objeto existente
                
                usuario.is_active = form.is_active.data # Permite cambiar estado activo/inactivo

            elif form.user_password.data: # Requiere password para crearla (validator también checa)
                 # Check para Username ÚNICO - ya hecho en form.validate()
                 usuario = Usuario(
                      username=form.username.data,
                      nombre_completo=f'{veterinario.nombre_veterinario} {veterinario.apellido_veterinario}',
                      rol='veterinario',
                      is_active=form.is_active.data,
                      veterinario_profile=veterinario # Vincula al veterinario
                 )
                 usuario.set_password(form.user_password.data)
                 db.session.add(usuario)
            else:
                # Esto debería ser atrapado por la validación condicional del form si create_user_account.data es True
                 flash("Debe proporcionar Nombre de Usuario y Contraseña si marca la casilla 'Crear cuenta'.", "danger")
                 # Retornar el formulario con errores. Esto ya debería suceder por form.validate()


        elif usuario_asociado: # Si NO se marcó la checkbox PERO existía una cuenta asociada...
             # Esto indica que se desea DESVINCULAR la cuenta.
             # En lugar de borrarla, la deshabilitaremos y desvincularemos.
             usuario_asociado.is_active = False # Deshabilitar la cuenta por seguridad
             usuario_asociado.id_veterinario_profile = None # Romper la clave foránea (desvincular)
             # Opcional: también poner rol a un valor neutral como 'inactivo' o NULL si la columna lo permite


        # Ahora guardamos todo
        try:
            db.session.commit() # Guarda cambios en Veterinario y Usuario(si se actualizó/creó/desvinculó)
            flash(f'Perfil de Veterinario {veterinario.apellido_veterinario} actualizado.', 'success')
            return redirect(url_for('routes.staff_list_veterinarios'))

        except Exception as e:
             db.session.rollback()
             flash('Ocurrió un error al actualizar el Veterinario.', 'danger')
             current_app.logger.error(f'Error al editar Veterinario {vet_id}: {e}', exc_info=True)
             return render_template('staff_veterinario_form.html', title='Editar Veterinario', form=form, is_edit=True, veterinario=veterinario) # Pasa veterinario al template


    # Si es GET, renderiza el formulario llenado por obj=veterinario
    # Los campos de usuario son llenados manualmente si usuario_asociado existe (líneas arriba)
    return render_template('staff_veterinario_form.html', title='Editar Veterinario', form=form, is_edit=True, veterinario=veterinario) # Pasa veterinario al template


# Ruta para Eliminar un Perfil de Veterinario (y deshabilitar su cuenta Staff)
@bp.route('/staff/veterinarios/<int:vet_id>/eliminar', methods=['POST']) # Usamos POST para eliminar de forma segura
@staff_login_required
@role_required('admin') # Solo administradores pueden eliminar veterinarios
def staff_delete_veterinario(vet_id):
    # Recuperar el perfil de Veterinario. Si no existe, 404.
    veterinario = Veterinario.query.get_or_404(vet_id)
    # Obtener la cuenta de usuario Staff asociada (si existe)
    usuario_asociado = veterinario.user_account # Relación user_account del modelo Veterinario
    
    try:
        # Si existe una cuenta de usuario Staff asociada, NO LA BORRES COMPLETAMENTE,
        # mejor deshabilitarla para mantener el historial o evitar recreaciones.
        if usuario_asociado:
             usuario_asociado.is_active = False # Deshabilita la cuenta
             usuario_asociado.id_veterinario_profile = None # Rompe la vinculación
             db.session.add(usuario_asociado) # Asegura que los cambios al usuario se guarden

        # Borra el perfil de Veterinario
        db.session.delete(veterinario)

        db.session.commit() # Guarda los cambios (eliminación de Vet, cambios en Usuario)
        flash(f'Perfil de Veterinario {veterinario.apellido_veterinario} eliminado' + (' y cuenta de Staff deshabilitada.' if usuario_asociado else '.'), 'success')

    except Exception as e:
        db.session.rollback()
        flash('Ocurrió un error al eliminar el Veterinario.', 'danger')
        current_app.logger.error(f'Error al eliminar Veterinario {vet_id}: {e}', exc_info=True)


    # Redirige al listado de veterinarios de staff
    return redirect(url_for('routes.staff_list_veterinarios'))

# --- Rutas de ejemplo adicionales para Staff (Duenos, Servicios, Usuarios) ---
# ... Mantener los ejemplos comentados o implementar rutas reales si es necesario ...