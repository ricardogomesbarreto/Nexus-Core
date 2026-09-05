import logging
from threading import Event, RLock, Thread, current_thread

from nexus.core.connectivity import ConnectivityManager
from nexus.core.runtime import RuntimeMode
from nexus.core.runtime_state import RuntimeStateController
from nexus.events import EventBus, EventType
from nexus.monitoring.health import HealthStatus


class ConnectivityMonitor:
    """
    Monitora continuamente a conectividade externa do Nexus Core.

    O monitor utiliza uma worker thread dedicada para executar
    verificações periódicas sem bloquear a thread principal.

    RuntimeStateController é a fonte autoritativa do estado.
    HealthStatus recebe apenas uma projeção para observabilidade.
    """

    WORKER_NAME = "Nexus-ConnectivityMonitor"

    def __init__(
        self,
        connectivity_manager: ConnectivityManager,
        runtime_state: RuntimeStateController,
        event_bus: EventBus,
        health: HealthStatus,
        interval: float = 10.0,
        logger=None,
    ):
        if interval <= 0:
            raise ValueError(
                "O intervalo de monitoramento deve ser maior que zero"
            )

        self.connectivity_manager = connectivity_manager
        self.runtime_state = runtime_state
        self.event_bus = event_bus
        self.health = health
        self.interval = interval

        self.logger = (
            logger
            if logger is not None
            else logging.getLogger(__name__)
        )

        self._stop_event = Event()
        self._lifecycle_lock = RLock()
        self._thread: Thread | None = None

    @property
    def is_running(self) -> bool:
        """
        Indica se a worker thread está atualmente em execução.
        """
        with self._lifecycle_lock:
            return (
                self._thread is not None
                and self._thread.is_alive()
            )

    def check_once(self) -> bool:
        """
        Executa uma única verificação de conectividade.

        Retorna True somente quando ocorre uma transição efetiva
        entre ONLINE e OFFLINE.

        Repetições do estado atual não geram eventos.
        """
        try:
            connectivity = self.connectivity_manager.check()
        except Exception:
            self.logger.exception(
                "Falha inesperada durante a verificação "
                "de conectividade"
            )
            return False

        target_mode = (
            RuntimeMode.ONLINE
            if connectivity.online
            else RuntimeMode.OFFLINE
        )

        reason = (
            "Conectividade externa disponível"
            if connectivity.online
            else "Conectividade externa indisponível"
        )

        result = self.runtime_state.transition_if_changed_result(
            target_mode,
            reason,
        )

        self.health.update_runtime(
            network_online=connectivity.online,
            runtime_mode=result.mode,
            runtime_reason=result.reason,
        )

        if not result.changed:
            return False

        network_event = (
            EventType.NETWORK_ONLINE
            if connectivity.online
            else EventType.NETWORK_OFFLINE
        )

        network_publish_error = None

        try:
            self.event_bus.publish(
                network_event,
                {
                    "endpoint": connectivity.endpoint,
                    "latency_ms": connectivity.latency_ms,
                },
            )
        except Exception as exc:
            network_publish_error = exc

        try:
            self.event_bus.publish(
                EventType.RUNTIME_MODE_CHANGED,
                {
                    "mode": result.mode.value,
                    "reason": result.reason,
                },
            )
        except Exception:
            if network_publish_error is None:
                raise

            self.logger.exception(
                "Falha adicional ao publicar "
                "RUNTIME_MODE_CHANGED"
            )

        if network_publish_error is not None:
            raise network_publish_error

        return True

    def start(self) -> None:
        """
        Inicia o monitoramento contínuo.

        Chamadas repetidas enquanto o worker está ativo
        não criam threads adicionais.
        """
        with self._lifecycle_lock:
            if (
                self._thread is not None
                and self._thread.is_alive()
            ):
                return

            self._stop_event.clear()

            self._thread = Thread(
                target=self._run,
                name=self.WORKER_NAME,
                daemon=True,
            )

            self._thread.start()

    def stop(
        self,
        timeout: float | None = 5.0,
    ) -> None:
        """
        Solicita encerramento gracioso do worker.

        É seguro chamar stop() antes de start() e também
        executar stop() repetidamente.

        Levanta TimeoutError quando o worker permanece ativo
        após o tempo máximo de espera solicitado.
        """
        with self._lifecycle_lock:
            thread = self._thread

            if thread is None:
                self._stop_event.set()
                return

            self._stop_event.set()

        if thread is current_thread():
            return

        if thread.is_alive():
            thread.join(timeout=timeout)

        if thread.is_alive():
            raise TimeoutError(
                "ConnectivityMonitor não encerrou "
                "dentro do tempo limite"
            )

        with self._lifecycle_lock:
            if self._thread is thread:
                self._thread = None

    def _run(self) -> None:
        """
        Loop interno do worker.

        Event.wait() permite que stop() interrompa imediatamente
        a espera entre verificações.
        """
        while not self._stop_event.wait(self.interval):
            try:
                self.check_once()
            except Exception:
                self.logger.exception(
                    "Falha inesperada no worker de conectividade"
                )
