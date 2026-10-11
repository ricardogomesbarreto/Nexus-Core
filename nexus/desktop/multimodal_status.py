"""Pure, local-only state presentation for the native multimodal interface.

v0.9.0: report *software state*, never assert that physical hardware works.
Only an explicit user-authorized visual request may set vision_busy/source.
No network, capture, audio, persistence or Tk imports in this module.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class MultimodalStatus:
    listening_allowed: bool
    listening_requested: bool
    speech_enabled: bool
    speech_requested: bool
    vision_busy: bool = False
    vision_source: str | None = None
    cancellation_requested: bool = False
    closing: bool = False

    def labels(self) -> tuple[str, str, str]:
        """Three bounded, readable labels; never disclose image/path content."""
        if self.closing:
            return ("Escuta: encerrando", "Voz: encerrando", "Visão: encerrando")
        if not self.listening_allowed:
            microphone = "Escuta: pausada"
        elif self.listening_requested:
            microphone = "Escuta: solicitada"
        else:
            microphone = "Escuta: aguardando"
        if not self.speech_enabled:
            speech = "Voz: desativada"
        elif self.speech_requested:
            speech = "Voz: saída solicitada"
        else:
            speech = "Voz: habilitada"
        if self.vision_busy:
            if self.cancellation_requested:
                vision = "Visão: cancelamento solicitado"
            else:
                source = {
                    "file": "imagem",
                    "screen": "tela",
                    "camera": "câmera",
                }.get(self.vision_source, "visual")
                vision = f"Visão: processando {source}"
        else:
            vision = "Visão: sem captura"
        return microphone, speech, vision
