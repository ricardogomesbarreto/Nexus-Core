from dataclasses import dataclass, field
from threading import RLock

from nexus.core.runtime import RuntimeMode


@dataclass(frozen=True)
class HealthRuntimeSnapshot:
    """
    Snapshot imutável e consistente da representação
    de runtime mantida pelo HealthStatus.
    """

    network_online: bool
    runtime_mode: RuntimeMode
    runtime_reason: str | None


@dataclass
class HealthStatus:
    """
    Representa o estado de saúde dos principais
    componentes do Nexus Core.

    RuntimeStateController permanece como fonte autoritativa
    do estado de runtime.

    HealthStatus mantém uma representação voltada à
    observabilidade e oferece operações sincronizadas para
    atualização e leitura consistente dos campos de runtime.
    """

    core: bool = False
    configuration: bool = False
    database: bool = False
    logger: bool = False
    event_bus: bool = False
    security_gate: bool = False
    tool_registry: bool = False
    terminal_sandbox: bool = False
    local_model_layer: bool = False

    network_online: bool = False
    runtime_mode: RuntimeMode = RuntimeMode.OFFLINE
    runtime_reason: str | None = None

    _runtime_lock: RLock = field(
        default_factory=RLock,
        init=False,
        repr=False,
        compare=False,
    )

    @property
    def model_layer(self) -> bool:
        """
        Estado provider-agnostic da Model Layer.

        Mantém compatibilidade com local_model_layer,
        introduzido na v0.3.0, sem criar estado duplicado.
        """

        return self.local_model_layer

    @model_layer.setter
    def model_layer(
        self,
        value: bool,
    ) -> None:
        self.local_model_layer = value

    @property
    def ready(self) -> bool:
        """
        Indica se todos os componentes essenciais
        estão operacionais.

        A conectividade externa não é considerada
        um requisito para o Nexus operar localmente.
        """

        return all(
            [
                self.core,
                self.configuration,
                self.database,
                self.logger,
                self.event_bus,
                self.security_gate,
                self.tool_registry,
                self.terminal_sandbox,
                self.local_model_layer,
            ]
        )

    def update_runtime(
        self,
        *,
        network_online: bool,
        runtime_mode: RuntimeMode,
        runtime_reason: str | None,
    ) -> None:
        """
        Atualiza atomicamente a representação de runtime.

        Componentes concorrentes que atualizam o HealthStatus
        devem utilizar esta operação em vez de modificar os três
        campos individualmente.
        """

        with self._runtime_lock:
            self.network_online = network_online
            self.runtime_mode = runtime_mode
            self.runtime_reason = runtime_reason

    def runtime_snapshot(self) -> HealthRuntimeSnapshot:
        """
        Retorna uma fotografia imutável e consistente
        da representação atual de runtime.

        Consumidores concorrentes devem preferir esta operação
        quando precisam observar os três campos como uma única
        unidade lógica.
        """

        with self._runtime_lock:
            return HealthRuntimeSnapshot(
                network_online=self.network_online,
                runtime_mode=self.runtime_mode,
                runtime_reason=self.runtime_reason,
            )
