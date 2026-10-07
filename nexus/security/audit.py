from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from nexus.config.settings import settings


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
            log_path = settings.logs_dir / "security.log"

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
        def safe(value: str | None) -> str:
            return (
                str(value if value is not None else "-")
                .replace("\\", "\\\\")
                .replace("\r", "\\r")
                .replace("\n", "\\n")
                .replace("|", "\\|")
            )

        return (
            f"{entry.timestamp.isoformat()} | "
            f"TOOL={safe(entry.tool_name)} | "
            f"ACTION={safe(entry.action)} | "
            f"RISK={safe(entry.risk_level)} | "
            f"DECISION={safe(entry.decision)} | "
            f"OUTCOME={safe(entry.outcome)} | "
            f"PATH={safe(entry.path)} | "
            f"REASON={safe(entry.reason)}"
        )
