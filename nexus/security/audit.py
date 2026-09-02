from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock


@dataclass(frozen=True)
class AuditEntry:
    """
    Representa um registro de auditoria
    de uma operação do Nexus.
    """

    timestamp: datetime
    tool_name: str
    action: str
    risk_level: str
    decision: str
    reason: str
    path: str | None = None
    outcome: str | None = None


class AuditLogger:
    """
    Registra eventos relacionados à segurança
    e à execução das ferramentas do Nexus.
    """

    def __init__(
        self,
        log_path: str | Path | None = None,
    ):
        if log_path is None:
            log_path = (
                Path.home()
                / "Nexus Core"
                / "logs"
                / "security.log"
            )

        self.log_path = Path(log_path).expanduser().resolve()

        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = RLock()

    def record(
        self,
        tool_name: str,
        action: str,
        risk_level: str,
        decision: str,
        reason: str,
        path: str | None = None,
        outcome: str | None = None,
    ) -> AuditEntry:

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            tool_name=tool_name,
            action=action,
            risk_level=risk_level,
            decision=decision,
            reason=reason,
            path=path,
            outcome=outcome,
        )

        line = self._format_entry(entry)

        with self._lock:
            with self.log_path.open(
                "a",
                encoding="utf-8",
            ) as file:
                file.write(line + "\n")

        return entry

    def record_execution(
        self,
        tool_name: str,
        action: str,
        outcome: str,
        reason: str,
        path: str | None = None,
    ) -> AuditEntry:
        """
        Registra o resultado da execução de uma ferramenta.
        """

        return self.record(
            tool_name=tool_name,
            action=action,
            risk_level="EXECUTION",
            decision="EXECUTED",
            reason=reason,
            path=path,
            outcome=outcome,
        )

    @staticmethod
    def _format_entry(
        entry: AuditEntry,
    ) -> str:

        path = entry.path or "-"
        outcome = entry.outcome or "-"

        return (
            f"{entry.timestamp.isoformat()} | "
            f"TOOL={entry.tool_name} | "
            f"ACTION={entry.action} | "
            f"RISK={entry.risk_level} | "
            f"DECISION={entry.decision} | "
            f"OUTCOME={outcome} | "
            f"PATH={path} | "
            f"REASON={entry.reason}"
        )
