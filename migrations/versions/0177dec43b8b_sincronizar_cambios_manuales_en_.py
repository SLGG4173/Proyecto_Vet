"""Sincronizar cambios manuales en Servicios

Revision ID: 0177dec43b8b
Revises: 
Create Date: 2025-06-11 08:51:45.677057

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0177dec43b8b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Duenos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre_dueno', sa.String(length=100), nullable=False),
    sa.Column('apellido_dueno', sa.String(length=100), nullable=False),
    sa.Column('telefono_dueno', sa.String(length=20), nullable=True),
    sa.Column('email_dueno', sa.String(length=100), nullable=False),
    sa.Column('direccion_dueno', sa.String(length=255), nullable=True),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email_dueno')
    )
    op.create_table('Servicios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre_servicio', sa.String(length=100), nullable=False),
    sa.Column('descripcion_servicio', sa.Text(), nullable=True),
    sa.Column('categoria', sa.String(length=100), nullable=False),
    sa.Column('precio_base', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('duracion_estimada', sa.Integer(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre_servicio')
    )
    op.create_table('Veterinarios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre_veterinario', sa.String(length=100), nullable=False),
    sa.Column('apellido_veterinario', sa.String(length=100), nullable=False),
    sa.Column('telefono_veterinario', sa.String(length=20), nullable=True),
    sa.Column('email_veterinario', sa.String(length=100), nullable=True),
    sa.Column('licencia_veterinario', sa.String(length=50), nullable=True),
    sa.Column('fecha_contratacion', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email_veterinario'),
    sa.UniqueConstraint('licencia_veterinario')
    )
    op.create_table('Mascotas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre_mascota', sa.String(length=100), nullable=False),
    sa.Column('especie', sa.String(length=50), nullable=True),
    sa.Column('raza', sa.String(length=50), nullable=True),
    sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
    sa.Column('id_dueno', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id_dueno'], ['Duenos.id'], onupdate='CASCADE', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('Usuarios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('nombre_completo', sa.String(length=150), nullable=True),
    sa.Column('rol', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('id_veterinario_profile', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id_veterinario_profile'], ['Veterinarios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id_veterinario_profile'),
    sa.UniqueConstraint('username')
    )
    op.create_table('Consultas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_mascota', sa.Integer(), nullable=True),
    sa.Column('id_veterinario', sa.Integer(), nullable=True),
    sa.Column('fecha_hora', sa.DateTime(), nullable=False),
    sa.Column('motivo_consulta', sa.Text(), nullable=True),
    sa.Column('diagnostico', sa.Text(), nullable=True),
    sa.Column('tratamiento', sa.Text(), nullable=True),
    sa.Column('notas_adicionales', sa.Text(), nullable=True),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
    sa.Column('estado_pago', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['id_mascota'], ['Mascotas.id'], onupdate='CASCADE', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['id_veterinario'], ['Veterinarios.id'], onupdate='CASCADE', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('DetalleConsultaServicio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_consulta', sa.Integer(), nullable=False),
    sa.Column('id_servicio', sa.Integer(), nullable=False),
    sa.Column('cantidad', sa.Integer(), nullable=False),
    sa.Column('precio_final_aplicado', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('descuento_aplicado', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('notas_servicio', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['id_consulta'], ['Consultas.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['id_servicio'], ['Servicios.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('mascotas')
    with op.batch_alter_table('veterinarios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('email_veterinario'))
        batch_op.drop_index(batch_op.f('uk_veterinario_licencia'))

    op.drop_table('veterinarios')
    op.drop_table('consultas')
    op.drop_table('detalleconsultaservicio')
    with op.batch_alter_table('duenos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('email_dueno'))

    op.drop_table('duenos')
    with op.batch_alter_table('servicios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('nombre_servicio'))

    op.drop_table('servicios')
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('fk_usuario_veterinario'))
        batch_op.drop_index(batch_op.f('username'))

    op.drop_table('usuarios')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('usuarios',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', mysql.VARCHAR(length=50), nullable=False),
    sa.Column('password_hash', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('nombre_completo', mysql.VARCHAR(length=150), nullable=True),
    sa.Column('rol', mysql.ENUM('admin', 'veterinario', 'recepcionista'), server_default=sa.text("'recepcionista'"), nullable=True),
    sa.Column('is_active', mysql.TINYINT(display_width=1), server_default=sa.text("'1'"), autoincrement=False, nullable=True),
    sa.Column('id_veterinario_profile', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('username'), ['username'], unique=True)
        batch_op.create_index(batch_op.f('fk_usuario_veterinario'), ['id_veterinario_profile'], unique=False)

    op.create_table('servicios',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre_servicio', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('descripcion_servicio', mysql.TEXT(), nullable=True),
    sa.Column('categoria', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('precio_base', mysql.DECIMAL(precision=10, scale=2), server_default=sa.text("'0.00'"), nullable=False),
    sa.Column('duracion_estimada', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('activo', mysql.TINYINT(display_width=1), server_default=sa.text("'1'"), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    with op.batch_alter_table('servicios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('nombre_servicio'), ['nombre_servicio'], unique=True)

    op.create_table('duenos',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre_dueno', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('apellido_dueno', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('telefono_dueno', mysql.VARCHAR(length=20), nullable=True),
    sa.Column('email_dueno', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('direccion_dueno', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('fecha_creacion', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.Column('password_hash', mysql.VARCHAR(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    with op.batch_alter_table('duenos', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('email_dueno'), ['email_dueno'], unique=True)

    op.create_table('detalleconsultaservicio',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('id_consulta', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('id_servicio', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('cantidad', mysql.INTEGER(), server_default=sa.text("'1'"), autoincrement=False, nullable=False),
    sa.Column('precio_final_aplicado', mysql.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('descuento_aplicado', mysql.DECIMAL(precision=10, scale=2), server_default=sa.text("'0.00'"), nullable=True),
    sa.Column('notas_servicio', mysql.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    op.create_table('consultas',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('id_mascota', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('id_veterinario', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('fecha_hora', mysql.DATETIME(), nullable=False),
    sa.Column('motivo_consulta', mysql.TEXT(), nullable=True),
    sa.Column('diagnostico', mysql.TEXT(), nullable=True),
    sa.Column('tratamiento', mysql.TEXT(), nullable=True),
    sa.Column('notas_adicionales', mysql.TEXT(), nullable=True),
    sa.Column('fecha_creacion', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.Column('estado_pago', mysql.VARCHAR(length=50), server_default=sa.text("'Pendiente'"), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    op.create_table('veterinarios',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre_veterinario', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('apellido_veterinario', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('telefono_veterinario', mysql.VARCHAR(length=20), nullable=True),
    sa.Column('email_veterinario', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('licencia_veterinario', mysql.VARCHAR(length=50), nullable=True),
    sa.Column('fecha_contratacion', sa.DATE(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    with op.batch_alter_table('veterinarios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('uk_veterinario_licencia'), ['licencia_veterinario'], unique=True)
        batch_op.create_index(batch_op.f('email_veterinario'), ['email_veterinario'], unique=True)

    op.create_table('mascotas',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre_mascota', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('especie', mysql.VARCHAR(length=50), nullable=True),
    sa.Column('raza', mysql.VARCHAR(length=50), nullable=True),
    sa.Column('fecha_nacimiento', sa.DATE(), nullable=True),
    sa.Column('id_dueno', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    op.drop_table('DetalleConsultaServicio')
    op.drop_table('Consultas')
    op.drop_table('Usuarios')
    op.drop_table('Mascotas')
    op.drop_table('Veterinarios')
    op.drop_table('Servicios')
    op.drop_table('Duenos')
    # ### end Alembic commands ###
