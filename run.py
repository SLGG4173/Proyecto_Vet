print("--- EJECUTANDO EL RUN.PY CORREGIDO ---")
import os
from app import create_app, db # Importa create_app y db

# Configura la variable de entorno FLASK_APP antes de ejecutar este script
# En terminal: export FLASK_APP=run.py
# O en Windows CMD: set FLASK_APP=run.py
# Luego: flask run O python run.py si tienes el entry point configurado en flask (__init__.py)
# Con este run.py explícito: python run.py

# Asegúrate de que la configuración cargue la DB desde .env/config
app = create_app()

@app.shell_context_processor
def make_shell_context():
    from app.models import Dueno, Mascota, Veterinario, Consulta, DetalleConsultaServicio, Servicio, Usuario
    return {'db': db,
            'Dueno': Dueno,
            'Mascota': Mascota,
            'Veterinario': Veterinario,
            'Consulta': Consulta,
            'DetalleConsultaServicio': DetalleConsultaServicio,
            'Servicio': Servicio,
            'Usuario': Usuario # Incluir el modelo Usuario para crear personal
           }

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False') == 'True') # Lee debug desde .env