"""Conversa efêmera: um pedido e no máximo uma ação por turno."""

import json
from dataclasses import dataclass
from threading import Event, Lock

from nexus.agent import AgentOutcome


@dataclass(frozen=True)
class ChatReply:
    text: str
    outcome: AgentOutcome


class ChatSession:
    """Conserva um contexto curto na memória do processo, sem persistência."""

    MAX_TURNS = 6
    MAX_MESSAGE = 4000
    MAX_CONTEXT_ITEM = 1200
    MAX_DISPLAY = 4000

    def __init__(self, agent):
        self.agent = agent
        self.history: list[tuple[str, str]] = []
        self._closed = Event()
        self._lock = Lock()

    def close(self) -> None:
        self._closed.set()

    def ask(self, message: str) -> ChatReply:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Escreva uma mensagem antes de enviar.")
        if len(message) > self.MAX_MESSAGE:
            raise ValueError("A mensagem excede o limite de 4000 caracteres.")
        with self._lock:
            if self._closed.is_set():
                raise RuntimeError("A conversa foi encerrada.")
            context = [
                {"usuario": user, "assistente": assistant}
                for user, assistant in self.history[-self.MAX_TURNS:]
            ]
            prompt = json.dumps(
                {"historico": context, "mensagem_atual": message},
                ensure_ascii=False,
            )
            outcome = self.agent.run(prompt, is_cancelled=self._closed.is_set)
            reply = self._describe(outcome)
            if not self._closed.is_set():
                self.history.append((
                    message[:self.MAX_CONTEXT_ITEM],
                    reply[:self.MAX_CONTEXT_ITEM],
                ))
                self.history = self.history[-self.MAX_TURNS:]
            return ChatReply(reply, outcome)

    def note_visual(self, question: str, description: str) -> None:
        """Keep only bounded ephemeral text from a user-authorized vision reply.

        Image bytes are never retained; this text permits follow-up questions.
        """
        if not isinstance(question, str) or not isinstance(description, str):
            raise ValueError("Contexto visual inválido.")
        with self._lock:
            if self._closed.is_set():
                return
            self.history.append((
                ("[Análise visual autorizada] " + question)[:self.MAX_CONTEXT_ITEM],
                ("[Descrição visual local, não verificada] " + description)[:self.MAX_CONTEXT_ITEM],
            ))
            self.history = self.history[-self.MAX_TURNS:]

    @classmethod
    def _describe(cls, outcome: AgentOutcome) -> str:
        if outcome.content:
            return outcome.content
        result = outcome.tool_result
        if result is None:
            return outcome.error or "Não foi possível concluir a solicitação."
        if not result.success:
            return f"{result.tool_name}: {result.error}"
        data = result.data
        if result.tool_name == "terminal_sandbox" and isinstance(data, dict):
            output = "".join(str(data.get(key) or "") for key in ("stdout", "stderr"))
        else:
            output = json.dumps(data, ensure_ascii=False, default=str)
        if len(output) > cls.MAX_DISPLAY:
            output = output[:cls.MAX_DISPLAY] + "\n… saída abreviada."
        return f"{result.tool_name} executada.\n{output}" if output else (
            f"{result.tool_name} executada."
        )
