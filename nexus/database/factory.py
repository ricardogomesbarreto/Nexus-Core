from nexus.config.settings import Settings
from nexus.database.contracts import DatabaseProvider
from nexus.database.errors import DatabaseConfigurationError
from nexus.database.postgresql import PostgreSQLProvider


def build_database_provider(
    settings: Settings,
) -> DatabaseProvider:
    """
    Constrói o provider de database configurado para o Nexus Core.

    A factory não realiza I/O nem inicializa a conexão.
    """

    if settings.database_provider != "postgresql":
        raise DatabaseConfigurationError(
            "database provider não suportado: "
            f"{settings.database_provider}"
        )

    if not settings.database_password:
        raise DatabaseConfigurationError(
            "NEXUS_DATABASE_PASSWORD é obrigatório "
            "para o provider PostgreSQL"
        )

    return PostgreSQLProvider(
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
        user=settings.database_user,
        password=settings.database_password,
        connect_timeout=settings.database_connect_timeout,
    )
