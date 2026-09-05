import logging
from threading import Event, RLock, Thread, current_thread

from nexus.core.connectivity import ConnectivityManager
from nexus.core.connectivity_runtime_evaluator import (
    ConnectivityRuntimeEvaluator,
)
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
        initial_network_online: bool,
        interval: float = 10.0,
        logger=None,
        confirmation_threshold: int = 2,
    ):
        if interval <= 0:
            raise ValueError(
                "O intervalo de monitoramento deve ser maior que zero"
            )

        expected_initial_mode = (
            RuntimeMode.ONLINE
            if initial_network_online
            else RuntimeMode.OFFLINE
        )

        if runtime_state.mode != expected_initial_mode:
            raise ValueError(
                "O estado inicial de runtime é incompatível "
                "com initial_network_online"
            )

        self.connectivity_manager = connectivity_manager
        self.runtime_state = runtime_state
        self.event_bus = event_bus
        self.health = health
        self.interval = interval

        self.runtime_evaluator = ConnectivityRuntimeEvaluator(
            initial_network_online=initial_network_online,
            confirmation_threshold=confirmation_threshold,
        )

        self.logger = (
            logger
            if logger is not None
            else logging.getLogger(__name__)
        )

        self._stop_event = Event()
        self._lifecycle_lock = RLock()
        self._cycle_lock = RLock()
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
        de modo de runtime, incluindo transições por DEGRADED.

        Eventos NETWORK_* representam mudanças na observação bruta.
        RUNTIME_MODE_CHANGED representa mudanças no modo estabilizado.
        """
        with self._cycle_lock:
            try:
                connectivity = self.connectivity_manager.check()
            except Exception:
                self.logger.exception(
                    "Falha inesperada durante a verificação "
                    "de conectividade"
                )
                return False

            evaluation = self.runtime_evaluator.evaluate(
                connectivity.online
            )

            result = self.runtime_state.transition_if_changed_result(
                evaluation.target_mode,
                evaluation.reason,
            )

            self.health.update_runtime(
                network_online=evaluation.network_online,
                runtime_mode=result.mode,
                runtime_reason=result.reason,
            )

            network_publish_error = None

            if evaluation.network_changed:
                network_event = (
                    EventType.NETWORK_ONLINE
                    if evaluation.network_online
                    else EventType.NETWORK_OFFLINE
                )

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

            if result.changed:
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

            return result.changed

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
