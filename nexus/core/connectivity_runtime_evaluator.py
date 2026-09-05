from dataclasses import dataclass

from nexus.core.runtime import RuntimeMode


@dataclass(frozen=True)
class ConnectivityRuntimeEvaluation:
    """
    Resultado imutável de uma avaliação de conectividade.
    """

    target_mode: RuntimeMode
    reason: str
    network_online: bool
    network_changed: bool


class ConnectivityRuntimeEvaluator:
    """
    Converte observações brutas de conectividade em modo de runtime.

    Uma mudança de conectividade precisa ser observada por
    confirmation_threshold ciclos consecutivos antes de ser
    considerada estável.

    Enquanto a mudança ainda não foi confirmada, o modo alvo
    é DEGRADED.
    """

    def __init__(
        self,
        *,
        initial_network_online: bool,
        confirmation_threshold: int = 2,
    ):
        if confirmation_threshold < 2:
            raise ValueError(
                "confirmation_threshold deve ser maior ou igual a 2"
            )

        self.confirmation_threshold = confirmation_threshold

        self._confirmed_network_online = initial_network_online
        self._last_network_online = initial_network_online

        self._pending_network_online: bool | None = None
        self._pending_count = 0

    def evaluate(
        self,
        network_online: bool,
    ) -> ConnectivityRuntimeEvaluation:
        """
        Avalia uma nova observação bruta de conectividade.
        """

        network_changed = (
            network_online != self._last_network_online
        )

        self._last_network_online = network_online

        if network_online == self._confirmed_network_online:
            self._pending_network_online = None
            self._pending_count = 0

            return ConnectivityRuntimeEvaluation(
                target_mode=self._stable_mode(
                    network_online
                ),
                reason=self._stable_reason(
                    network_online
                ),
                network_online=network_online,
                network_changed=network_changed,
            )

        if self._pending_network_online == network_online:
            self._pending_count += 1
        else:
            self._pending_network_online = network_online
            self._pending_count = 1

        if self._pending_count < self.confirmation_threshold:
            return ConnectivityRuntimeEvaluation(
                target_mode=RuntimeMode.DEGRADED,
                reason=self._degraded_reason(
                    network_online
                ),
                network_online=network_online,
                network_changed=network_changed,
            )

        self._confirmed_network_online = network_online
        self._pending_network_online = None
        self._pending_count = 0

        return ConnectivityRuntimeEvaluation(
            target_mode=self._stable_mode(
                network_online
            ),
            reason=self._stable_reason(
                network_online
            ),
            network_online=network_online,
            network_changed=network_changed,
        )

    @staticmethod
    def _stable_mode(
        network_online: bool,
    ) -> RuntimeMode:
        return (
            RuntimeMode.ONLINE
            if network_online
            else RuntimeMode.OFFLINE
        )

    @staticmethod
    def _stable_reason(
        network_online: bool,
    ) -> str:
        return (
            "Conectividade externa disponível"
            if network_online
            else "Conectividade externa indisponível"
        )

    @staticmethod
    def _degraded_reason(
        network_online: bool,
    ) -> str:
        return (
            "Conectividade externa detectada; aguardando confirmação"
            if network_online
            else "Perda de conectividade aguardando confirmação"
        )
