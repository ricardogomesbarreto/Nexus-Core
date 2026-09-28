class DatabaseError(RuntimeError):
    """
    Erro base do subsistema de database do Nexus Core.
    """


class DatabaseConfigurationError(DatabaseError):
    """
    Configuração de database inválida ou incompleta.
    """


class DatabaseConnectionError(DatabaseError):
    """
    Falha ao estabelecer ou validar conexão com o database.
    """


class DatabaseOperationError(DatabaseError):
    """
    Falha durante uma operação de persistência.
    """


class DatabaseLifecycleError(DatabaseError):
    """
    Operação incompatível com o estado atual do database.
    """
