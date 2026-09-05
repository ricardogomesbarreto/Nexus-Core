from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock

from nexus.core.runtime import RuntimeMode


@dataclass(frozen=True)
class RuntimeStateSnapshot:
    """
    Snapshot imutável e consistente do estado de runtime.
    """

    mode: RuntimeMode
    reason: str | None
    changed_at: datetime | None


@dataclass(frozen=True)
class RuntimeTransitionResult:
    """
    Resultado imutável de uma tentativa de transição condicional.

    O resultado é capturado sob o mesmo lock utilizado para
    comparar e, quando necessário, alterar o estado.
    """

    changed: bool
    mode: RuntimeMode
    reason: str | None
    changed_at: datetime | None


@dataclass
class RuntimeStateController:
    """
    Controla o estado autoritativo de runtime do Nexus Core.

    Responsabilidades:
    - armazenar mode, reason e changed_at;
    - validar transições permitidas;
    - preservar o contrato histórico de transition();
    - oferecer transições condicionais atômicas;
    - disponibilizar snapshots consistentes.
    """

    initial_mode: RuntimeMode = RuntimeMode.OFFLINE
    initial_reason: str | None = None

    def __post_init__(self):
        self._lock = RLock()

        self._mode = self.initial_mode
        self._reason = self.initial_reason
        self._changed_at: datetime | None = None

    @property
    def mode(self) -> RuntimeMode:
        """
        Retorna o modo atual de execução.
        """
        with self._lock:
            return self._mode

    @property
    def reason(self) -> str | None:
        """
        Retorna o motivo associado ao estado atual.
        """
        with self._lock:
            return self._reason

    @property
    def changed_at(self) -> datetime | None:
        """
        Retorna o momento da última mudança de estado.
        """
        with self._lock:
            return self._changed_at

    def snapshot(self) -> RuntimeStateSnapshot:
        """
        Retorna uma fotografia imutável e consistente
        do estado atual.
        """
        with self._lock:
            return RuntimeStateSnapshot(
                mode=self._mode,
                reason=self._reason,
                changed_at=self._changed_at,
            )

    def transition(
        self,
        target_mode: RuntimeMode,
        reason: str,
    ) -> bool:
        """
        Realiza uma transição válida de estado.

        Contrato preservado da v0.2.1:
        - retorna True quando a transição é realizada;
        - levanta ValueError para o mesmo estado;
        - levanta ValueError para transições inválidas.
        """
        with self._lock:
            if target_mode == self._mode:
                raise ValueError(
                    "Transição para o mesmo estado não é permitida"
                )

            self._transition_locked(
                target_mode,
                reason,
            )

            return True

    def transition_if_changed(
        self,
        target_mode: RuntimeMode,
        reason: str,
    ) -> bool:
        """
        Transiciona atomicamente somente quando o estado mudou.

        Retorna False quando o target_mode já é o estado atual.
        """
        result = self.transition_if_changed_result(
            target_mode,
            reason,
        )

        return result.changed

    def transition_if_changed_result(
        self,
        target_mode: RuntimeMode,
        reason: str,
    ) -> RuntimeTransitionResult:
        """
        Compara, transiciona e captura o resultado sob um único lock.

        Isso evita a janela de concorrência existente quando um
        consumidor precisa executar transition_if_changed() e depois
        realizar uma leitura separada com snapshot().
        """
        with self._lock:
            if target_mode == self._mode:
                return RuntimeTransitionResult(
                    changed=False,
                    mode=self._mode,
                    reason=self._reason,
                    changed_at=self._changed_at,
                )

            self._transition_locked(
                target_mode,
                reason,
            )

            return RuntimeTransitionResult(
                changed=True,
                mode=self._mode,
                reason=self._reason,
                changed_at=self._changed_at,
            )

    def _transition_locked(
        self,
        target_mode: RuntimeMode,
        reason: str,
    ) -> None:
        """
        Valida e executa uma mudança de estado.

        Deve ser chamado apenas enquanto self._lock
        estiver adquirido.
        """
        valid_transitions = {
            RuntimeMode.OFFLINE: {
                RuntimeMode.ONLINE,
            },
            RuntimeMode.ONLINE: {
                RuntimeMode.OFFLINE,
            },
            RuntimeMode.DEGRADED: set(),
        }

        allowed_targets = valid_transitions.get(
            self._mode,
            set(),
        )

        if target_mode not in allowed_targets:
            raise ValueError(
                f"Transição inválida: "
                f"{self._mode.value} → {target_mode.value}"
            )

        self._mode = target_mode
        self._reason = reason
        self._changed_at = datetime.now(timezone.utc)
