
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, SelectField, TextAreaField, DecimalField, HiddenField, FormField, FieldList, BooleanField # Importamos FormField y FieldList si se usan subformularios
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, Optional, AnyOf
from app.models import Dueno, Mascota, Veterinario, Servicio, Usuario # Importar modelos

# Existing forms (LoginForm, ClientRegistrationForm, MascotaForm) ...
class LoginForm(FlaskForm):
    # Para Dueños
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Ingresar')

class ClientRegistrationForm(FlaskForm):
    # Para Dueños
    nombre_dueno = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido_dueno = StringField('Apellido', validators=[DataRequired(), Length(max=100)])
    email_dueno = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repetir Password', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')])
    telefono_dueno = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    direccion_dueno = StringField('Dirección', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Registrarse')

    def validate_email_dueno(self, email_dueno):
        dueno = Dueno.query.filter_by(email_dueno=email_dueno.data).first()
        if dueno is not None:
            raise ValidationError('Este email ya está registrado. Por favor, usa uno diferente.')

class MascotaForm(FlaskForm):
    # Para agregar/editar Mascotas por Dueño
    nombre_mascota = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    especie = StringField('Especie', validators=[Optional(), Length(max=50)])
    raza = StringField('Raza', validators=[Optional(), Length(max=50)])
    fecha_nacimiento = DateField('Fecha de Nacimiento (YYYY-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Guardar Mascota')


# --- NUEVOS FORMULARIOS PARA STAFF ---

class StaffLoginForm(FlaskForm):
    # Para usuarios de la tabla Usuarios
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar (Personal)')


class ConsultaForm(FlaskForm):
    # id_mascota: SelectField poblado dinámicamente en la ruta
    id_mascota = SelectField('Mascota', coerce=int, validators=[DataRequired()]) # coerce=int convierte la selección a entero

    # id_veterinario: SelectField poblado dinámicamente en la ruta
    # Optional=True para permitir consultas sin vet asignado inicialmente si tu DB lo permite
    id_veterinario = SelectField('Veterinario', coerce=int, validators=[Optional()])

    # Fecha y Hora: Separamos para simplificar la entrada
    fecha = DateField('Fecha (YYYY-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    hora = StringField('Hora (HH:MM)', validators=[DataRequired(), Length(min=5, max=5)]) # Puedes añadir Regex para validar HH:MM formato

    motivo_consulta = TextAreaField('Motivo', validators=[Optional()])

    # Campos para el Veterinario (serán opcionales y solo mostrados/editables para ciertos roles)
    diagnostico = TextAreaField('Diagnóstico', validators=[Optional()])
    tratamiento = TextAreaField('Tratamiento', validators=[Optional()])
    notas_adicionales = TextAreaField('Notas Adicionales', validators=[Optional()])

    submit = SubmitField('Guardar Consulta')

# Formulario simple para Añadir Detalle de Servicio a una Consulta (podría ser más complejo)
# Este podría ser parte del formulario de edición de Consulta o uno separado
class DetalleConsultaServicioForm(FlaskForm):
    # id_servicio: SelectField poblado dinámicamente con servicios disponibles
    id_servicio = SelectField('Servicio', coerce=int, validators=[DataRequired()])
    # Precio: Puede tener un valor predeterminado del servicio, pero permitir cambio
    precio_cobrado = DecimalField('Precio Cobrado', validators=[Optional()])
    submit = SubmitField('Agregar Servicio')


# --- NUEVO FORMULARIO PARA GESTIONAR VETERINARIOS (ADMIN/STAFF) ---

# Campo Roles permitidos (puede usarse para validación o select)
STAFF_ROLES = [('recepcionista', 'Recepcionista'), ('veterinario', 'Veterinario'), ('admin', 'Administrador')]


# Formulario para añadir/editar Perfil de Veterinario Y potencialmente vincular Cuenta de Usuario Staff
class VeterinarioFormStaff(FlaskForm):
    # Campos del Perfil de Veterinario
    nombre_veterinario = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido_veterinario = StringField('Apellido', validators=[DataRequired(), Length(max=100)])
    telefono_veterinario = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    email_veterinario = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    licencia_veterinario = StringField('Licencia', validators=[Optional(), Length(max=50)]) # Optional si no todos tienen licencia (aunque raro) - O DataRequired si es obligatorio. Añade UniqueValidator si es obligatorio y único.
    fecha_contratacion = DateField('Fecha de Contratación (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])

    # --- Campos para crear/vincular una Cuenta de Usuario Staff ---
    # Opción para decidir si se creará o vinculará una cuenta
    create_user_account = BooleanField('Crear/Vincular cuenta de usuario de Staff (rol: Veterinario)') # Checkbox

    # Campos de la Cuenta de Usuario (solo mostrados si el checkbox anterior está marcado, lógicamente)
    username = StringField('Nombre de Usuario', validators=[Optional(), Length(min=2, max=50)]) # Opcional AQUI, DataRequired en validacion si create_user_account es True
    user_password = PasswordField('Contraseña de Usuario', validators=[Optional()]) # Opcional AQUI
    user_password2 = PasswordField('Repetir Contraseña', validators=[Optional(), EqualTo('user_password', message='Las contraseñas deben coincidir')]) # Opcional AQUI
    is_active = BooleanField('Cuenta activa', default=True) # Para activar/desactivar la cuenta

    submit = SubmitField('Guardar Veterinario')


    # **Validación Condicional y Adicional**
    def validate(self, extra_validators=None):
        # Ejecutar validaciones estándar de WTForms primero
        initial_validation = super().validate(extra_validators=extra_validators)
        if not initial_validation:
            return False # Si hay errores básicos, parar

        # Validación campos UNIQUE (licencia_veterinario, email_veterinario)
        # Esto debe hacerse manualmente si se edita un registro existente
        # y se necesita que sea único EXCEPT el propio registro que se edita.
        # Para Añadir (sin vet_id), checkeamos si existe ya uno con esa licencia/email.
        # Para Editar (con vet_id), checkeamos si existe otro con esa licencia/email y id != vet_id.

        # Contexto: check if this form is for editing (has object) or creating (new object)
        vet_id = getattr(self, '_obj', None) and getattr(self._obj, 'id', None) # Get id if obj is populated


        # Validación UNIQUE Licencia (si el campo tiene valor y NO es Optional)
        if self.licencia_veterinario.data and DataRequired in [v.__class__ for v in getattr(self.licencia_veterinario, 'validators', [])]: # Check if license is provided AND required
             query = Veterinario.query.filter_by(licencia_veterinario=self.licencia_veterinario.data)
             if vet_id: # If editing, exclude the current vet
                  query = query.filter(Veterinario.id != vet_id)
             if query.first(): # If any matching vet found
                  self.licencia_veterinario.errors.append('Esta licencia ya está registrada.')
                  initial_validation = False # Indicate validation failure

         # Validación UNIQUE Email (si el campo tiene valor y NO es Optional y es único)
         # Asume que email_veterinario en el modelo es unique=True
        if self.email_veterinario.data and self.email_veterinario.validators and any(isinstance(v, Email) for v in self.email_veterinario.validators): # Check if email is provided AND Email validated
            # Assuming email_veterinario in models is unique=True
            query = Veterinario.query.filter_by(email_veterinario=self.email_veterinario.data)
            if vet_id:
                 query = query.filter(Veterinario.id != vet_id)
            if query.first():
                 self.email_veterinario.errors.append('Este email ya está registrado para otro veterinario.')
                 initial_validation = False

        # Validación Condicional: Campos de Usuario si 'create_user_account' está marcado
        if self.create_user_account.data:
            # Si se quiere crear una cuenta, el username y password son MANDATORIOS
            if not self.username.data:
                self.username.errors.append('Nombre de usuario es requerido para la cuenta de Staff.')
                initial_validation = False
            elif len(self.username.data) < 2 or len(self.username.data) > 50:
                 self.username.errors.append('Nombre de usuario debe tener entre 2 y 50 caracteres.')
                 initial_validation = False

            # Contraseña es mandatoria y requiere repetición coincidente (Equal To validator ya ayuda)
            if not self.user_password.data:
                 self.user_password.errors.append('Contraseña de usuario es requerida.')
                 initial_validation = False
            # EqualTo('user_password') en user_password2 ya maneja la coincidencia


            # Validación UNIQUE Username
            query = Usuario.query.filter_by(username=self.username.data)
             # Si estamos editando y YA HAY una cuenta de usuario vinculada a ESTE vet
            if vet_id and getattr(self._obj, 'user_account', None): # Check if editing AND this vet already has a user account
                # Excluir la cuenta de usuario QUE YA TIENE ESTE VETERINARIO
                query = query.filter(Usuario.id != self._obj.user_account.id)
            # else: If creating or editing a vet WITHOUT existing account: Check if username exists AT ALL

            if query.first(): # Si se encuentra algún usuario con ese username
                 self.username.errors.append('Este nombre de usuario ya está en uso.')
                 initial_validation = False


        # Si estamos EDITANDO un veterinario (vet_id exists),
        # Y ya tiene una cuenta de usuario (self._obj.user_account),
        # PERO la checkbox 'create_user_account' NO está marcada:
        # Esto indica que se quiere desvincular la cuenta o no hacerle cambios.
        # No hay validacion de requerimiento de password aqui, eso es solo para CREACION o CAMBIO (si implementas cambio de password separado).
        # Si implementaras cambio de password: deberias añadir campos old_password, new_password, new_password2
        # y validar condicionalmente si new_password se llena y old_password coincide.

        # Consideraciones adicionales: Email UNIQUE para Vets, Username UNIQUE para Usuarios ya están manejados en la validación estándar y la DB level constraint

        return initial_validation


    # Método para validar condicionalmente en el template si mostrar campos de usuario
    def should_show_user_fields(self):
        # Muestra campos de usuario si es GET (añadir/editar)
        # O si es POST y la casilla 'create_user_account' está marcada (aunque fallara validacion)
        # Esto es más complejo, quizás mejor manejar display con JS/CSS basado en el checkbox en el template.
        # Simplemente validar 'create_user_account.data' en el template HTML es más fácil para mostrar/ocultar.
        pass