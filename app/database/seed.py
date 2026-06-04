import logging

from sqlalchemy.orm import Session

from app.database.config import settings
from app.usuarios.models import DatosPersonales, Rol, Usuario
from app.usuarios.security import hash_password

logger = logging.getLogger(__name__)

# ─── Datos semilla ────────────────────────────────────────────────────────────
_ROLES_INICIALES = [
    {"nombre": "usuario", "descripcion": "Usuario regular"},
    {"nombre": "administrador", "descripcion": "Usuario con privilegios de administrador"},
]


# ─── Funciones públicas ───────────────────────────────────────────────────────
def create_default_roles_and_admin(db: Session) -> None:
    """
    Crea los roles base y el usuario administrador inicial si no existen.
    Es seguro llamar esta función múltiples veces (idempotente).
    """
    _create_roles(db)
    _create_admin_user(db)


# ─── Funciones internas ───────────────────────────────────────────────────────
def _create_roles(db: Session) -> None:
    """
    Inserta los roles iniciales que no existan en la base de datos.
    Usa un único commit para todos los roles nuevos.
    """
    roles_nuevos = []

    for rol_data in _ROLES_INICIALES:
        existe = db.query(Rol).filter(Rol.nombre == rol_data["nombre"]).first()

        if existe:
            logger.info("Rol '%s' ya existe, se omite.", rol_data["nombre"])
            continue

        roles_nuevos.append(Rol(nombre=rol_data["nombre"], descripcion=rol_data["descripcion"]))

    if not roles_nuevos:
        return

    try:
        db.add_all(roles_nuevos)
        db.commit()
        for rol in roles_nuevos:
            db.refresh(rol)
            logger.info("Rol '%s' creado con id %d.", rol.nombre, rol.id)
    except Exception as exc:
        db.rollback()
        logger.error("Error al crear roles: %s", exc)
        raise


def _create_admin_user(db: Session) -> None:
    """
    Crea el usuario administrador inicial usando las credenciales
    definidas en las variables de entorno ADMIN_EMAIL y ADMIN_PASSWORD.
    """
    rol_admin = db.query(Rol).filter(Rol.nombre == "administrador").first()

    if not rol_admin:
        raise RuntimeError(
            "Rol 'administrador' no encontrado. "
            "Ejecuta _create_roles() antes de _create_admin_user()."
        )

    admin_existente = db.query(Usuario).filter(
        Usuario.usuario == settings.admin_email
    ).first()

    if admin_existente:
        logger.info("Usuario administrador '%s' ya existe.", settings.admin_email)
        return

    try:
        datos_admin = DatosPersonales(nombre="Admin", apellido="Principal")
        db.add(datos_admin)
        db.flush()  # Obtiene el ID sin commitear aún

        nuevo_admin = Usuario(
            usuario=settings.admin_email,
            contrasenia=hash_password(settings.admin_password),
            rol_id=rol_admin.id,
            datos_personales_id=datos_admin.id,
            activo=True,
        )
        db.add(nuevo_admin)
        db.commit()
        db.refresh(nuevo_admin)

        logger.info(
            "Usuario administrador '%s' creado con id %d.",
            settings.admin_email,
            nuevo_admin.id,
        )
    except Exception as exc:
        db.rollback()
        logger.error("Error al crear usuario administrador: %s", exc)
        raise