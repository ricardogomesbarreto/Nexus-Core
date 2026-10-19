"""Conversa efêmera: um pedido e no máximo uma ação por turno."""

import json
from dataclasses import dataclass
from threading import Event, Lock

from nexus.agent import AgentOutcome
from nexus.desktop.local_replies import local_conversation_answer
from nexus.desktop.chat_archive import ChatArchive, ChatArchiveError
from nexus.desktop.tool_labels import action_label


@dataclass(frozen=True)
class ChatReply:
    text: str
    outcome: AgentOutcome


class ChatSession:
    """Keeps six-turn context; optional local archive stores ordinary text only."""

    MAX_TURNS = 6
    MAX_MESSAGE = 4000
    MAX_CONTEXT_ITEM = 1200
    MAX_DISPLAY = 4000

    def __init__(self, agent, archive: ChatArchive | None = None):
        self.agent = agent
        self._archive = archive
        self.history: list[tuple[str, str]] = (
            archive.load()[-self.MAX_TURNS:] if archive is not None else []
        )
        self.last_archive_error: str | None = None
        self._previous_was_advisory = False
        self._closed = Event()
        self._cancelled = Event()
        self._lock = Lock()

    def set_archive(self, archive: ChatArchive | None) -> None:
        """Enable/disable future text storage without replaying old turns."""
        with self._lock:
            self._archive = archive
            self.last_archive_error = None

    def forget_context(self) -> None:
        """Clear volatile LLM context after the user clears stored history."""
        with self._lock:
            self.history.clear()
            self._previous_was_advisory = False

    def close(self) -> None:
        self._closed.set()
        self._cancelled.set()

    def cancel_current(self) -> None:
        """Best effort cancellation; blocks later actions, not actions already begun."""
        self._cancelled.set()

    def prepare_turn(self) -> None:
        """Called by the UI before a new worker starts, never during a live turn."""
        if self._closed.is_set():
            raise RuntimeError("A conversa foi encerrada.")
        self._cancelled.clear()

    def ask(self, message: str, *, advisory_only: bool = False) -> ChatReply:
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
            cancelled = lambda: self._closed.is_set() or self._cancelled.is_set()
            local_reply = None if advisory_only else local_conversation_answer(message)
            if local_reply is not None:
                # Read-only time/date never invoke the model or a system tool.
                outcome = AgentOutcome(True, content=local_reply)
            elif advisory_only:
                # Independent hard authorization gate: even if the model proposes
                # a tool despite the prompt, AgentPlanner must refuse execution.
                prompt = json.dumps({
                    "modo": "sugestao_sem_ferramentas",
                    "historico": context,
                    "mensagem_atual": message,
                    "diretriz": "Responda com sugestões concretas; não use ferramentas.",
                }, ensure_ascii=False)
                outcome = self.agent.run(
                    prompt, is_cancelled=cancelled, allow_tools=False
                )
            else:
                outcome = self.agent.run(prompt, is_cancelled=cancelled)
            if cancelled():
                return ChatReply(
                    "Solicitação cancelada.",
                    AgentOutcome(False, error_code="CANCELLED"),
                )
            reply = self._describe(outcome)
            if (not advisory_only and not self._previous_was_advisory
                    and outcome.success and outcome.content
                    and self.history and 30 <= len(reply) < self.MAX_CONTEXT_ITEM
                    and " " in reply[:100]):
                old_question, old_reply = self.history[-1]
                if (message.casefold() != old_question.casefold()
                        and reply.strip().casefold() == old_reply.strip().casefold()):
                    retry = self.agent.run(
                        json.dumps({"historico": [], "mensagem_atual": message},
                                   ensure_ascii=False),
                        is_cancelled=cancelled, allow_tools=False,
                    )
                    if cancelled():
                        return ChatReply(
                            "Solicitação cancelada.",
                            AgentOutcome(False, error_code="CANCELLED"),
                        )
                    if retry.success and retry.content and (
                            retry.content.strip().casefold()
                            != old_reply.strip().casefold()):
                        outcome = retry
                        reply = self._describe(outcome)
                    else:
                        outcome = AgentOutcome(
                            False, error="O modelo local não produziu uma resposta "
                                         "nova. Tente outra pergunta ou verifique o Ollama.",
                            error_code="STALE_REPLY",
                        )
                        reply = outcome.error
            if (outcome.success and not self._closed.is_set()
                    and not self._cancelled.is_set()):
                self.history.append((
                    message[:self.MAX_CONTEXT_ITEM],
                    reply[:self.MAX_CONTEXT_ITEM],
                ))
                self.history = self.history[-self.MAX_TURNS:]
                self._previous_was_advisory = advisory_only
                if self._archive is not None and outcome.tool_result is None:
                    try:
                        self._archive.append(message, reply)
                        self.last_archive_error = None
                    except ChatArchiveError:
                        # A disk fault must not turn a valid response into
                        # a failure; report the unsaved state in the GUI.
                        self.last_archive_error = (
                            "Não foi possível salvar esta conversa no disco local."
                        )
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
            return f"{action_label(result.tool_name)}: {result.error}"
        data = result.data
        if result.tool_name == "local_note_create" and isinstance(data, dict):
            return f"Nota local criada: {data['path']}"
        if result.tool_name == "local_data_transform" and isinstance(data, dict):
            return f"Transformação local concluída ({data['operation']}): {data['result']}"
        if result.tool_name == "create_directory" and isinstance(data, dict):
            return f"Pasta criada: {data['path']}"
        if result.tool_name == "launch_application" and isinstance(data, dict):
            return f"Solicitei a abertura de {data['application']} no desktop."
        if result.tool_name == "open_default_browser" and isinstance(data, dict):
            return f"Solicitei a abertura do navegador padrão ({data['browser_id']})."
        if result.tool_name in {"edit_image_local", "image_geometry_local", "create_graphic_local", "craft_convert_local", "pdf_extract_pages_local", "pdf_combine_local", "pdf_organize_local", "pdf_render_local"} and isinstance(data, dict):
            return f"Arquivo criado no computador: {data['path']}"
        if result.tool_name == "image_colors_local" and isinstance(data, dict):
            return (f"Imagem com {data['width']} por {data['height']} pixels. "
                    f"Luminosidade média: {data['brightness']} de 255; "
                    f"{data['dark_percent']}% de pixels escuros e "
                    f"{data['light_percent']}% de pixels claros.")
        if result.tool_name == "system_info" and isinstance(data, dict):
            parts = [
                f"Sistema operacional: {data.get('system', 'desconhecido')}",
                f"Kernel: {data.get('release', 'desconhecido')}",
                f"Arquitetura: {data.get('machine', 'desconhecida')}",
                f"Python: {data.get('python', 'desconhecido')}",
            ]
            return "Informações deste computador:\n" + "\n".join(parts)
        if result.tool_name == "terminal_sandbox" and isinstance(data, dict):
            output = "".join(str(data.get(key) or "") for key in ("stdout", "stderr"))
        else:
            output = json.dumps(data, ensure_ascii=False, default=str)
        if len(output) > cls.MAX_DISPLAY:
            output = output[:cls.MAX_DISPLAY] + "\n… saída abreviada."
        return f"Ação concluída: {action_label(result.tool_name)}.\n{output}" if output else (
            f"Ação concluída: {action_label(result.tool_name)}."
        )
