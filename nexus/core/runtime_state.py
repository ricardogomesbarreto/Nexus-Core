from dataclasses import dataclass
from datetime import datetime, timezone

from nexus.core.runtime import RuntimeMode


@dataclass
class RuntimeStateController:
    """
    Controla o estado de runtime do Nexus Core.

    O controlador centraliza o estado atual, o motivo
    da última transição e o momento em que ela ocorreu.
    """

    initial_mode: RuntimeMode = RuntimeMode.OFFLINE
    initial_reason: str | None = None

    def __post_init__(self):
        self._mode = self.initial_mode
        self._reason = self.initial_reason
        self._changed_at: datetime | None = None

    @property
    def mode(self) -> RuntimeMode:
        """
        Retorna o modo atual de execução.
        """

        return self._mode

    @property
    def reason(self) -> str | None:
        """
        Retorna o motivo associado ao estado atual.
        """

        return self._reason

    @property
    def changed_at(self) -> datetime | None:
        """
        Retorna o momento da última mudança de estado.
        """

        return self._changed_at

    def transition(
        self,
        target_mode: RuntimeMode,
        reason: str,
    ) -> bool:
        """
        Realiza uma transição válida de estado.

        Retorna True quando a transição é realizada.

        Levanta ValueError quando a transição não é permitida.
        """

        if target_mode == self._mode:
            raise ValueError(
                "Transição para o mesmo estado não é permitida"
            )

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

        return True
