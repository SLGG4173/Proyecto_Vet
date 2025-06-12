import csv
import io

from flask import (render_template, redirect, url_for, flash, request,
                   Blueprint, g, current_app, session, abort, make_response)
from flask_wtf import FlaskForm
from app import db
from app.models import (Dueno, Mascota, Veterinario, Consulta,
                      DetalleConsultaServicio, Servicio, Usuario)
from app.forms import (
    LoginForm, ClientRegistrationForm, MascotaForm, StaffLoginForm,
    ConsultaForm, ServicioForm, DetalleConsultaServicioForm,
    VeterinarioFormStaff, ReporteIngresosForm
)
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime, date, time
from app.decorators import load_staff_user_into_g, staff_login_required, role_required
from sqlalchemy import func, extract, case
from calendar import month_name

bp = Blueprint('routes', __name__)


@bp.before_request
def before_request_load_staff():
    """Carga el usuario de staff en g antes de cada request del blueprint."""
    load_staff_user_into_g()


# ==============================================================================
# --- Rutas Públicas y de Dueño (Cliente) ---
# ==============================================================================

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    if g.staff_user:
        return redirect(url_for('routes.staff_dashboard'))
    return render_template('index.html', title='Inicio Veterinaria')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    if g.staff_user:
        flash('Ya estás logueado como personal. Cierra sesión para ingresar como Dueño.', 'info')
        return redirect(url_for('routes.staff_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        dueno = Dueno.query.filter_by(email_dueno=form.email.data).first()
        if dueno is None or not dueno.check_password(form.password.data):
            flash('Email o contraseña inválida para Dueño.', 'danger')
            return redirect(url_for('routes.login'))
        login_user(dueno, remember=form.remember_me.data)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('routes.dashboard'))
    return render_template('login.html', title='Ingreso de Dueño', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión de Dueño correctamente.', 'info')
    return redirect(url_for('routes.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    if g.staff_user:
        return redirect(url_for('routes.staff_dashboard'))

    form = ClientRegistrationForm()
    if form.validate_on_submit():
        dueno = Dueno(nombre_dueno=form.nombre_dueno.data,
                      apellido_dueno=form.apellido_dueno.data,
                      email_dueno=form.email_dueno.data,
                      telefono_dueno=form.telefono_dueno.data,
                      direccion_dueno=form.direccion_dueno.data)
        dueno.set_password(form.password.data)
        try:
            db.session.add(dueno)
            db.session.commit()
            flash('¡Tu cuenta de Dueño ha sido creada! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('routes.login'))
        except Exception as e:
            db.session.rollback()
            flash('Ocurrió un error al registrar la cuenta.', 'danger')
            current_app.logger.error(f'Error durante registro de Dueño: {e}', exc_info=True)
    return render_template('register.html', title='Registro de Dueño', form=form)


@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard Dueño', dueno=current_user)


@bp.route('/mascotas')
@login_required
def list_mascotas():
    mascotas = current_user.mascotas.all()
    csrf_form = FlaskForm()
    return render_template('mascotas.html', title='Mis Mascotas', mascotas=mascotas, csrf_form=csrf_form)


@bp.route('/mascota/nueva', methods=['GET', 'POST'])
@login_required
def add_mascota():
    form = MascotaForm()
    if form.validate_on_submit():
        mascota = Mascota(nombre_mascota=form.nombre_mascota.data,
                          especie=form.especie.data,
                          raza=form.raza.data,
                          fecha_nacimiento=form.fecha_nacimiento.data,
                          owner=current_user)
        try:
            db.session.add(mascota)
            db.session.commit()
            flash(f'La mascota "{mascota.nombre_mascota}" ha sido agregada.', 'success')
            return redirect(url_for('routes.list_mascotas'))
        except Exception as e:
            db.session.rollback()
            flash('Error al agregar la mascota.', 'danger')
            current_app.logger.error(f'Error agregando mascota: {e}', exc_info=True)
    return render_template('mascota_form.html', title='Agregar Mascota', form=form)


@bp.route('/mascota/<int:mascota_id>/editar', methods=['GET', 'POST'])
@login_required
def edit_mascota(mascota_id):
    mascota = Mascota.query.filter_by(id=mascota_id, id_dueno=current_user.id).first_or_404()
    form = MascotaForm(obj=mascota)
    if form.validate_on_submit():
        form.populate_obj(mascota)
        try:
            db.session.commit()
            flash('Datos de la mascota actualizados.', 'success')
            return redirect(url_for('routes.list_mascotas'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la mascota.', 'danger')
            current_app.logger.error(f'Error editando mascota {mascota_id}: {e}', exc_info=True)
    return render_template('mascota_form.html', title='Editar Mascota', form=form)


@bp.route('/mascota/<int:mascota_id>/eliminar', methods=['POST'])
@login_required
def delete_mascota(mascota_id):
    mascota = Mascota.query.filter_by(id=mascota_id, id_dueno=current_user.id).first_or_404()
    try:
        db.session.delete(mascota)
        db.session.commit()
        flash(f'La mascota "{mascota.nombre_mascota}" ha sido eliminada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la mascota.', 'danger')
        current_app.logger.error(f'Error eliminando mascota {mascota_id}: {e}', exc_info=True)
    return redirect(url_for('routes.list_mascotas'))


@bp.route('/mascota/<int:mascota_id>')
@login_required
def mascota_detail(mascota_id):
    mascota = Mascota.query.filter_by(id=mascota_id, id_dueno=current_user.id).first_or_404()
    consultas = mascota.consultas.filter(
        Consulta.estado_pago != 'Cancelado'
    ).order_by(Consulta.fecha_hora.desc()).all()
    return render_template('mascota_detail.html',
                           title=f'Detalle de {mascota.nombre_mascota}',
                           mascota=mascota,
                           consultas=consultas)


@bp.route('/consultas')
@login_required
def list_consultas():
    consultas = db.session.query(Consulta).join(Mascota).filter(
        Mascota.id_dueno == current_user.id,
        Consulta.estado_pago != 'Cancelado'  # <-- Excluye las canceladas
    ).order_by(Consulta.fecha_hora.desc()).all()
    return render_template('consultas.html', title='Mis Consultas', consultas=consultas)


# ==============================================================================
# --- Rutas para el Personal (Staff) ---
# ==============================================================================

@bp.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    if g.staff_user:
        return redirect(url_for('routes.staff_dashboard'))

    form = StaffLoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(username=form.username.data).first()
        if usuario is None or not usuario.check_password(form.password.data):
            flash('Nombre de usuario o contraseña inválida.', 'danger')
            return redirect(url_for('routes.staff_login'))
        if not usuario.is_active:
            flash('Tu cuenta de personal no está activa.', 'danger')
            return redirect(url_for('routes.staff_login'))
        
        session['staff_user_id'] = usuario.id
        session['staff_user_role'] = usuario.rol
        next_page = session.pop('staff_login_next', None) or url_for('routes.staff_dashboard')
        return redirect(next_page)
    return render_template('staff_login.html', title='Ingreso de Personal', form=form)


@bp.route('/staff/logout')
@staff_login_required
def staff_logout():
    session.pop('staff_user_id', None)
    session.pop('staff_user_role', None)
    flash('Has cerrado sesión de Personal.', 'info')
    return redirect(url_for('routes.staff_login'))


@bp.route('/staff')
@staff_login_required
def staff_dashboard():
    return render_template('staff_dashboard.html', title='Dashboard Staff')


# --- Rutas de Gestión de Consultas (Staff) ---

@bp.route('/staff/consultas')
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin')
def staff_list_consultas():
    consultas_pendientes = Consulta.query.filter(Consulta.estado_pago.notin_(['Pagado', 'Cancelado'])).order_by(Consulta.fecha_hora.desc()).all()
    consultas_pagadas = Consulta.query.filter_by(estado_pago='Pagado').order_by(Consulta.fecha_hora.desc()).all()
    consultas_canceladas = Consulta.query.filter_by(estado_pago='Cancelado').order_by(Consulta.fecha_hora.desc()).all()
    csrf_form = FlaskForm()
    return render_template('staff_consultas.html',
                           title='Gestión de Consultas',
                           consultas_pendientes=consultas_pendientes,
                           consultas_pagadas=consultas_pagadas,
                           consultas_canceladas=consultas_canceladas,
                           csrf_form=csrf_form)


@bp.route('/staff/consultas/nueva', methods=['GET', 'POST'])
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin')
def add_consulta():
    form = ConsultaForm()
    form.id_mascota.choices = [(0, '--- Seleccionar Mascota ---')] + [(m.id, f'{m.nombre_mascota} (Dueño: {m.owner.nombre_dueno if m.owner else "N/A"})') for m in Mascota.query.order_by(Mascota.nombre_mascota).all()]
    form.id_veterinario.choices = [(0, '--- Opcional ---')] + [(v.id, f'Dr. {v.nombre_veterinario} {v.apellido_veterinario}') for v in Veterinario.query.order_by(Veterinario.nombre_veterinario).all()]

    if form.validate_on_submit():
        if form.id_mascota.data == 0:
            flash('Por favor, selecciona una Mascota válida.', 'danger')
        else:
            try:
                time_obj = time.fromisoformat(form.hora.data)
                fecha_hora_dt = datetime.combine(form.fecha.data, time_obj)
                
                consulta = Consulta(
                    id_mascota=form.id_mascota.data,
                    id_veterinario=form.id_veterinario.data if form.id_veterinario.data != 0 else None,
                    fecha_hora=fecha_hora_dt,
                    motivo_consulta=form.motivo_consulta.data,
                    estado_pago=form.estado_pago.data
                )
                db.session.add(consulta)
                db.session.commit()
                flash('Consulta agendada correctamente.', 'success')
                return redirect(url_for('routes.staff_list_consultas'))
            except ValueError:
                flash('Formato de hora inválido. Usa HH:MM.', 'danger')
            except Exception as e:
                db.session.rollback()
                flash('Ocurrió un error al agendar la consulta.', 'danger')
                current_app.logger.error(f'Error agendando consulta: {e}', exc_info=True)
    
    return render_template('consulta_form.html', title='Agendar Consulta', form=form)


@bp.route('/staff/consultas/<int:consulta_id>/editar', methods=['GET', 'POST'])
@staff_login_required
def edit_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    form = ConsultaForm(obj=consulta)
    add_service_form = DetalleConsultaServicioForm()
    csrf_form = FlaskForm()
    form.id_mascota.choices = [(m.id, f'{m.nombre_mascota} (Dueño: {m.owner.nombre_dueno if m.owner else "N/A"})')
                               for m in Mascota.query.order_by(Mascota.nombre_mascota).all()]
    form.id_veterinario.choices = [(0, '--- Opcional ---')] + \
                                  [(v.id, f'Dr. {v.nombre_veterinario} {v.apellido_veterinario}')
                                   for v in Veterinario.query.order_by(Veterinario.nombre_veterinario).all()]
    add_service_form.id_servicio.choices = [(0, '--- Seleccionar Servicio ---')] + \
                                           [(s.id, f'{s.nombre_servicio} (${s.precio_base:.2f})')
                                            for s in Servicio.query.filter_by(activo=True).order_by(Servicio.nombre_servicio).all()]

    if form.validate_on_submit():
        try:
            time_obj = time.fromisoformat(form.hora.data)
            consulta.fecha_hora = datetime.combine(form.fecha.data, time_obj)
        except (ValueError, IndexError):
            flash('Formato de hora inválido. Usa HH:MM.', 'danger')

            return render_template('consulta_form.html', title='Editar Consulta', form=form, consulta=consulta, add_service_form=add_service_form, csrf_form=csrf_form)

        # Actualizar campos generales que todos los roles pueden modificar
        consulta.id_mascota = form.id_mascota.data
        consulta.id_veterinario = form.id_veterinario.data if form.id_veterinario.data != 0 else None
        consulta.motivo_consulta = form.motivo_consulta.data
        consulta.estado_pago = form.estado_pago.data

        # Actualizar campos clínicos SOLO si el rol es 'veterinario' o 'admin'
        if g.staff_user.rol in ['veterinario', 'admin']:
            consulta.diagnostico = form.diagnostico.data
            consulta.tratamiento = form.tratamiento.data
            consulta.notas_adicionales = form.notas_adicionales.data
        
        # Guardar los cambios en la base de datos
        try:
            db.session.commit()
            flash('Consulta actualizada correctamente.', 'success')
            return redirect(url_for('routes.staff_list_consultas'))
        except Exception as e:
            db.session.rollback()
            flash('Ocurrió un error al actualizar la consulta.', 'danger')
            current_app.logger.error(f'Error editando consulta {consulta_id}: {e}', exc_info=True)


    if request.method == 'GET' and consulta.fecha_hora:
        form.fecha.data = consulta.fecha_hora.date()
        form.hora.data = consulta.fecha_hora.time().strftime('%H:%M')
    
    return render_template('consulta_form.html',
                           title='Editar Consulta',
                           form=form,
                           consulta=consulta,
                           add_service_form=add_service_form,
                           csrf_form=csrf_form)

@bp.route('/staff/consultas/<int:consulta_id>/eliminar', methods=['POST'])
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin')
def delete_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    pet_name = consulta.pet.nombre_mascota if consulta.pet else "Mascota Desconocida"
    try:
        db.session.delete(consulta)
        db.session.commit()
        flash(f'Consulta para {pet_name} cancelada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al cancelar la consulta.', 'danger')
        current_app.logger.error(f'Error eliminando consulta {consulta_id}: {e}', exc_info=True)
    return redirect(url_for('routes.staff_list_consultas'))


# --- Rutas de Gestión de Servicios en Consultas ---

@bp.route('/staff/consultas/<int:consulta_id>/agregar-servicio', methods=['POST'])
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin')
def add_detalle_servicio_to_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    form = DetalleConsultaServicioForm()
    form.id_servicio.choices = [(0, '--- Seleccionar ---')] + [(s.id, s.nombre_servicio) for s in Servicio.query.filter_by(activo=True).all()]
    
    if form.validate_on_submit():
        if form.id_servicio.data == 0:
            flash('Por favor, selecciona un Servicio válido.', 'danger')
        else:
            detalle = DetalleConsultaServicio(
                id_consulta=consulta.id,
                id_servicio=form.id_servicio.data,
                cantidad=form.cantidad.data,
                precio_final_aplicado=form.precio_final_aplicado.data,
                descuento_aplicado=form.descuento_aplicado.data,
                notas_servicio=form.notas_servicio.data
            )
            try:
                db.session.add(detalle)
                db.session.commit()
                flash('Servicio agregado a la consulta.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error al agregar el servicio.', 'danger')
                current_app.logger.error(f'Error agregando servicio a consulta {consulta_id}: {e}', exc_info=True)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en campo '{getattr(form, field).label.text}': {error}", 'danger')

    return redirect(url_for('routes.edit_consulta', consulta_id=consulta.id))


@bp.route('/staff/detalle_servicio/<int:detalle_id>/eliminar', methods=['POST'])
@staff_login_required
@role_required('recepcionista', 'veterinario', 'admin')
def delete_detalle_servicio(detalle_id):
    detalle = DetalleConsultaServicio.query.get_or_404(detalle_id)
    consulta_id = detalle.id_consulta
    try:
        db.session.delete(detalle)
        db.session.commit()
        flash('Servicio quitado de la consulta.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al quitar el servicio.', 'danger')
        current_app.logger.error(f'Error eliminando detalle servicio {detalle_id}: {e}', exc_info=True)
    return redirect(url_for('routes.edit_consulta', consulta_id=consulta_id))


# --- Rutas de Gestión de Servicios (CRUD) ---

@bp.route('/staff/servicios')
@staff_login_required
@role_required('admin', 'recepcionista', 'veterinario')
def staff_list_servicios():
    servicios = Servicio.query.order_by(Servicio.categoria, Servicio.nombre_servicio).all()
    csrf_form = FlaskForm()
    return render_template('staff_servicios_list.html', title='Gestionar Servicios', servicios=servicios, csrf_form=csrf_form)


@bp.route('/staff/servicios/nuevo', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin', 'veterinario')
def staff_add_servicio():
    form = ServicioForm()
    if form.validate_on_submit():
        nuevo_servicio = Servicio(nombre_servicio=form.nombre_servicio.data,
                                  descripcion_servicio=form.descripcion_servicio.data,
                                  categoria=form.categoria.data,
                                  precio_base=form.precio_base.data,
                                  duracion_estimada=form.duracion_estimada.data,
                                  activo=form.activo.data)
        try:
            db.session.add(nuevo_servicio)
            db.session.commit()
            flash('Servicio creado exitosamente.', 'success')
            return redirect(url_for('routes.staff_list_servicios'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el servicio. El nombre podría ya existir.', 'danger')
            current_app.logger.error(f'Error añadiendo servicio: {e}', exc_info=True)
    return render_template('staff_servicio_form.html', title='Añadir Servicio', form=form)


@bp.route('/staff/servicios/<int:servicio_id>/editar', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin', 'veterinario')
def staff_edit_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    form = ServicioForm(obj=servicio)
    if form.validate_on_submit():
        form.populate_obj(servicio)
        try:
            db.session.commit()
            flash('Servicio actualizado exitosamente.', 'success')
            return redirect(url_for('routes.staff_list_servicios'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el servicio.', 'danger')
            current_app.logger.error(f'Error editando servicio {servicio_id}: {e}', exc_info=True)
    return render_template('staff_servicio_form.html', title='Editar Servicio', form=form)


@bp.route('/staff/servicios/<int:servicio_id>/toggle_activo', methods=['POST'])
@staff_login_required
@role_required('admin', 'veterinario')
def staff_toggle_servicio_activo(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    servicio.activo = not servicio.activo
    try:
        db.session.commit()
        estado = "activado" if servicio.activo else "desactivado"
        flash(f'El servicio "{servicio.nombre_servicio}" ha sido {estado}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al cambiar el estado del servicio.', 'danger')
    return redirect(url_for('routes.staff_list_servicios'))

# ==============================================================================
# --- MÓDULO DE REPORTES ---
# ==============================================================================

# 1. Ruta para el Dashboard de Reportes
@bp.route('/staff/reportes')
@staff_login_required
@role_required('admin')
def staff_reportes_dashboard():
    return render_template('reportes_dashboard.html', title='Panel de Reportes')

# 2. Ruta para el Reporte de Citas (Atendidas vs. No Asistidas)
@bp.route('/staff/reportes/citas', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin', 'recepcionista')
def reporte_citas_mensual():
    form = ReporteIngresosForm(request.form)
    report_data = None
    
    fecha_filtro = form.mes_anio.data if form.validate_on_submit() and form.mes_anio.data else date.today()
    if request.method == 'GET':
        form.mes_anio.data = fecha_filtro

    anio_seleccionado = fecha_filtro.year
    mes_seleccionado = fecha_filtro.month
    titulo_reporte = f"Reporte de Citas para {month_name[mes_seleccionado]} {anio_seleccionado}"
    
    resultados = db.session.query(
        Consulta.estado_pago,
        func.count(Consulta.id).label('cantidad')
    ).filter(
        extract('year', Consulta.fecha_hora) == anio_seleccionado,
        extract('month', Consulta.fecha_hora) == mes_seleccionado
    ).group_by(Consulta.estado_pago).all()
    
    report_data = {'atendidas': 0, 'no_asistidas': 0, 'detalle': {}}
    for estado, cantidad in resultados:
        report_data['detalle'][estado] = cantidad
        if estado in ['Pagado', 'Pendiente']:
            report_data['atendidas'] += cantidad
        elif estado == 'Cancelado':
            report_data['no_asistidas'] += cantidad
            
    return render_template('reporte_citas.html',
                           title=titulo_reporte,
                           form=form,
                           report_data=report_data)

# 3. Ruta para el Reporte de Servicios Más Frecuentes (Top 5)
@bp.route('/staff/reportes/servicios-populares', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin', 'veterinario')
def reporte_servicios_populares():
    form = ReporteIngresosForm(request.form)
    report_data = []
    fecha_filtro = form.mes_anio.data if form.validate_on_submit() and form.mes_anio.data else date.today()
    if request.method == 'GET':
        form.mes_anio.data = fecha_filtro

    anio_seleccionado = fecha_filtro.year
    mes_seleccionado = fecha_filtro.month
    titulo_reporte = f"Top 5 Servicios Más Frecuentes para {month_name[mes_seleccionado]} {anio_seleccionado}"
    
    report_data = db.session.query(
        Servicio.nombre_servicio,
        func.sum(DetalleConsultaServicio.cantidad).label('total_aplicado')
    ).select_from(DetalleConsultaServicio).join(Servicio).join(Consulta).filter(
        extract('year', Consulta.fecha_hora) == anio_seleccionado,
        extract('month', Consulta.fecha_hora) == mes_seleccionado,
        Consulta.estado_pago.in_(['Pagado', 'Pendiente'])
    ).group_by(Servicio.nombre_servicio).order_by(
        db.desc('total_aplicado')
    ).limit(5).all()
            
    return render_template('reporte_servicios_populares.html',
                           title=titulo_reporte,
                           form=form,
                           report_data=report_data)

# 4. Ruta para el Reporte de Ingresos por Categoría de Servicio
@bp.route('/staff/reportes/ingresos-categoria', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin')
def reporte_ingresos_categoria():
    form = ReporteIngresosForm(request.form)
    report_data = []
    total_ingresos = 0
    fecha_filtro = form.mes_anio.data if form.validate_on_submit() and form.mes_anio.data else date.today()
    if request.method == 'GET':
        form.mes_anio.data = fecha_filtro

    anio_seleccionado = fecha_filtro.year
    mes_seleccionado = fecha_filtro.month
    titulo_reporte = f"Ingresos por Categoría para {month_name[mes_seleccionado]} {anio_seleccionado}"

    resultados = db.session.query(
        Servicio.categoria,
        func.sum((DetalleConsultaServicio.cantidad * DetalleConsultaServicio.precio_final_aplicado) - DetalleConsultaServicio.descuento_aplicado).label('ingreso_categoria')
    ).select_from(DetalleConsultaServicio).join(Servicio).join(Consulta).filter(
        extract('year', Consulta.fecha_hora) == anio_seleccionado,
        extract('month', Consulta.fecha_hora) == mes_seleccionado,
        Consulta.estado_pago == 'Pagado'
    ).group_by(Servicio.categoria).order_by(db.desc('ingreso_categoria')).all()
    
    report_data = resultados
    if report_data:
        total_ingresos = sum(ingreso for categoria, ingreso in report_data)

    return render_template('reporte_ingresos_categoria.html',
                           title=titulo_reporte,
                           form=form,
                           report_data=report_data,
                           total_ingresos=total_ingresos)

# 5. Ruta para el Reporte de Consultas por Veterinario
@bp.route('/staff/reportes/consultas-veterinario', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin')
def reporte_consultas_veterinario():
    form = ReporteIngresosForm(request.form)
    report_data = []
    fecha_filtro = form.mes_anio.data if form.validate_on_submit() and form.mes_anio.data else date.today()
    if request.method == 'GET':
        form.mes_anio.data = fecha_filtro

    anio_seleccionado = fecha_filtro.year
    mes_seleccionado = fecha_filtro.month
    titulo_reporte = f"Consultas por Veterinario para {month_name[mes_seleccionado]} {anio_seleccionado}"

    report_data = db.session.query(
        Veterinario.nombre_veterinario,
        Veterinario.apellido_veterinario,
        func.count(Consulta.id).label('total_consultas')
    ).select_from(Consulta).join(Veterinario).filter(
        extract('year', Consulta.fecha_hora) == anio_seleccionado,
        extract('month', Consulta.fecha_hora) == mes_seleccionado,
        Consulta.estado_pago != 'Cancelado'
    ).group_by(Veterinario.id).order_by(db.desc('total_consultas')).all()
            
    return render_template('reporte_consultas_veterinario.html',
                           title=titulo_reporte,
                           form=form,
                           report_data=report_data)

# ==============================================================================
#       --- Rutas de Gestión de Veterinarios (CRUD) ---
# ==============================================================================

@bp.route('/staff/veterinarios')
@staff_login_required
@role_required('admin')
def staff_list_veterinarios():
    veterinarios = Veterinario.query.order_by(Veterinario.apellido_veterinario, Veterinario.nombre_veterinario).all()
    csrf_form = FlaskForm()
    return render_template('staff_veterinarios_list.html', title='Gestionar Veterinarios', veterinarios=veterinarios, csrf_form=csrf_form)


@bp.route('/staff/veterinarios/nueva', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin')
def staff_add_veterinario():
    form = VeterinarioFormStaff()
    if form.validate_on_submit():
        veterinario = Veterinario(nombre_veterinario=form.nombre_veterinario.data,
                                  apellido_veterinario=form.apellido_veterinario.data,
                                  telefono_veterinario=form.telefono_veterinario.data,
                                  email_veterinario=form.email_veterinario.data,
                                  licencia_veterinario=form.licencia_veterinario.data,
                                  fecha_contratacion=form.fecha_contratacion.data)
        db.session.add(veterinario)
        
        if form.create_user_account.data:
            usuario = Usuario(username=form.username.data,
                              nombre_completo=f'{form.nombre_veterinario.data} {form.apellido_veterinario.data}',
                              rol='veterinario',
                              is_active=form.is_active.data,
                              veterinario_profile=veterinario)
            usuario.set_password(form.user_password.data)
            db.session.add(usuario)
        
        try:
            db.session.commit()
            flash(f'Perfil de Veterinario {veterinario.apellido_veterinario} creado exitosamente.', 'success')
            return redirect(url_for('routes.staff_list_veterinarios'))
        except Exception as e:
            db.session.rollback()
            flash('Error al guardar el Veterinario.', 'danger')
            current_app.logger.error(f'Error añadiendo Veterinario: {e}', exc_info=True)
    return render_template('staff_veterinario_form.html', title='Añadir Veterinario', form=form, is_edit=False)


@bp.route('/staff/veterinarios/<int:vet_id>/editar', methods=['GET', 'POST'])
@staff_login_required
@role_required('admin')
def staff_edit_veterinario(vet_id):
    veterinario = Veterinario.query.get_or_404(vet_id)
    usuario_asociado = veterinario.user_account
    form = VeterinarioFormStaff(obj=veterinario)

    if request.method == 'GET' and usuario_asociado:
        form.create_user_account.data = True
        form.username.data = usuario_asociado.username
        form.is_active.data = usuario_asociado.is_active

    if form.validate_on_submit():
        form.populate_obj(veterinario)
        if form.create_user_account.data:
            if usuario_asociado:
                usuario_asociado.is_active = form.is_active.data
            elif form.user_password.data:
                usuario = Usuario(username=form.username.data,
                                  nombre_completo=f'{veterinario.nombre_veterinario} {veterinario.apellido_veterinario}',
                                  rol='veterinario',
                                  is_active=form.is_active.data,
                                  veterinario_profile=veterinario)
                usuario.set_password(form.user_password.data)
                db.session.add(usuario)
            else:
                flash("Debe proporcionar Contraseña para crear una cuenta nueva.", "danger")
                return render_template('staff_veterinario_form.html', title='Editar Veterinario', form=form, is_edit=True, veterinario=veterinario)
        elif usuario_asociado:
            usuario_asociado.is_active = False
            usuario_asociado.id_veterinario_profile = None

        try:
            db.session.commit()
            flash(f'Perfil de Veterinario {veterinario.apellido_veterinario} actualizado.', 'success')
            return redirect(url_for('routes.staff_list_veterinarios'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el Veterinario.', 'danger')
            current_app.logger.error(f'Error editando Veterinario {vet_id}: {e}', exc_info=True)
    
    return render_template('staff_veterinario_form.html', title='Editar Veterinario', form=form, is_edit=True, veterinario=veterinario)


@bp.route('/staff/veterinarios/<int:vet_id>/eliminar', methods=['POST'])
@staff_login_required
@role_required('admin')
def staff_delete_veterinario(vet_id):
    veterinario = Veterinario.query.get_or_404(vet_id)
    usuario_asociado = veterinario.user_account
    try:
        if usuario_asociado:
            usuario_asociado.is_active = False
            usuario_asociado.id_veterinario_profile = None
            db.session.add(usuario_asociado)
        db.session.delete(veterinario)
        db.session.commit()
        flash(f'Perfil de Veterinario {veterinario.apellido_veterinario} eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el Veterinario.', 'danger')
        current_app.logger.error(f'Error eliminando Veterinario {vet_id}: {e}', exc_info=True)
    return redirect(url_for('routes.staff_list_veterinarios'))

# ==============================================================================
#           --- RUTAS DE EXPORTACIÓN DE REPORTES A CSV ---
# ==============================================================================

def generar_respuesta_csv(datos, encabezados, nombre_archivo):
    """Función auxiliar para generar una respuesta HTTP con un archivo CSV."""
    if not datos:
        flash('No hay datos para exportar con los filtros seleccionados.', 'info')
        # Redirigir de vuelta a la página anterior (requiere saber de dónde vino la petición)
        return redirect(request.referrer or url_for('routes.staff_reportes_dashboard'))

    # Usar io.StringIO para crear un archivo en memoria
    proxy = io.StringIO()
    writer = csv.writer(proxy)

    # Escribir encabezados
    writer.writerow(encabezados)
    # Escribir datos
    for fila in datos:
        writer.writerow(fila)

    # Preparar el archivo en memoria para ser leído
    mem_file = io.BytesIO()
    mem_file.write(proxy.getvalue().encode('utf-8'))
    mem_file.seek(0)
    proxy.close()

    # Crear la respuesta HTTP
    response = make_response(mem_file.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    return response


@bp.route('/staff/reportes/citas/exportar')
@staff_login_required
@role_required('admin', 'recepcionista')
def exportar_reporte_citas():
    mes_anio_str = request.args.get('mes_anio')
    fecha_filtro = datetime.strptime(mes_anio_str, '%Y-%m') if mes_anio_str else date.today()
    
    resultados = db.session.query(
        Consulta.estado_pago,
        func.count(Consulta.id)
    ).filter(
        extract('year', Consulta.fecha_hora) == fecha_filtro.year,
        extract('month', Consulta.fecha_hora) == fecha_filtro.month
    ).group_by(Consulta.estado_pago).all()
    
    datos_csv = [[estado, cantidad] for estado, cantidad in resultados]
    encabezados = ['Estado de la Cita', 'Cantidad']
    nombre_archivo = f"reporte_citas_{fecha_filtro.strftime('%Y_%m')}.csv"
    
    return generar_respuesta_csv(datos_csv, encabezados, nombre_archivo)


@bp.route('/staff/reportes/servicios-populares/exportar')
@staff_login_required
@role_required('admin', 'veterinario')
def exportar_reporte_servicios_populares():
    mes_anio_str = request.args.get('mes_anio')
    fecha_filtro = datetime.strptime(mes_anio_str, '%Y-%m') if mes_anio_str else date.today()
    
    resultados = db.session.query(
        Servicio.nombre_servicio,
        func.sum(DetalleConsultaServicio.cantidad)
    ).select_from(DetalleConsultaServicio).join(Servicio).join(Consulta).filter(
        extract('year', Consulta.fecha_hora) == fecha_filtro.year,
        extract('month', Consulta.fecha_hora) == fecha_filtro.month,
        Consulta.estado_pago.in_(['Pagado', 'Pendiente'])
    ).group_by(Servicio.nombre_servicio).order_by(
        db.desc(func.sum(DetalleConsultaServicio.cantidad))
    ).limit(5).all()
    
    datos_csv = [[servicio, cantidad] for servicio, cantidad in resultados]
    encabezados = ['Servicio', 'Cantidad de Veces Aplicado']
    nombre_archivo = f"reporte_top_servicios_{fecha_filtro.strftime('%Y_%m')}.csv"
    
    return generar_respuesta_csv(datos_csv, encabezados, nombre_archivo)


@bp.route('/staff/reportes/ingresos-categoria/exportar')
@staff_login_required
@role_required('admin')
def exportar_reporte_ingresos_categoria():
    mes_anio_str = request.args.get('mes_anio')
    fecha_filtro = datetime.strptime(mes_anio_str, '%Y-%m') if mes_anio_str else date.today()

    resultados = db.session.query(
        Servicio.categoria,
        func.sum((DetalleConsultaServicio.cantidad * DetalleConsultaServicio.precio_final_aplicado) - DetalleConsultaServicio.descuento_aplicado)
    ).select_from(DetalleConsultaServicio).join(Servicio).join(Consulta).filter(
        extract('year', Consulta.fecha_hora) == fecha_filtro.year,
        extract('month', Consulta.fecha_hora) == fecha_filtro.month,
        Consulta.estado_pago == 'Pagado'
    ).group_by(Servicio.categoria).order_by(db.desc(func.sum((DetalleConsultaServicio.cantidad * DetalleConsultaServicio.precio_final_aplicado) - DetalleConsultaServicio.descuento_aplicado))).all()

    datos_csv = [[categoria, f"{ingreso:.2f}"] for categoria, ingreso in resultados]
    encabezados = ['Categoría de Servicio', 'Ingreso Total']
    nombre_archivo = f"reporte_ingresos_categoria_{fecha_filtro.strftime('%Y_%m')}.csv"
    
    return generar_respuesta_csv(datos_csv, encabezados, nombre_archivo)


@bp.route('/staff/reportes/consultas-veterinario/exportar')
@staff_login_required
@role_required('admin')
def exportar_reporte_consultas_veterinario():
    mes_anio_str = request.args.get('mes_anio')
    fecha_filtro = datetime.strptime(mes_anio_str, '%Y-%m') if mes_anio_str else date.today()

    resultados = db.session.query(
        Veterinario.nombre_veterinario,
        Veterinario.apellido_veterinario,
        func.count(Consulta.id)
    ).select_from(Consulta).join(Veterinario).filter(
        extract('year', Consulta.fecha_hora) == fecha_filtro.year,
        extract('month', Consulta.fecha_hora) == fecha_filtro.month,
        Consulta.estado_pago != 'Cancelado'
    ).group_by(Veterinario.id).order_by(db.desc(func.count(Consulta.id))).all()

    datos_csv = [[f"Dr. {nombre} {apellido}", total] for nombre, apellido, total in resultados]
    encabezados = ['Veterinario', 'Total de Consultas']
    nombre_archivo = f"reporte_consultas_vet_{fecha_filtro.strftime('%Y_%m')}.csv"

    return generar_respuesta_csv(datos_csv, encabezados, nombre_archivo)