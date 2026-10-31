"""Roteiro pedagogicamente estruturado para Ollama local, fundamentado em fontes.

Gera somente a PERGUNTA para `answer_from_hits`; não acessa banco, modelo,
arquivos ou rede. Não guarda perfis sensíveis e não promete avaliação pedagógica.
"""
LEVELS = {
    "Iniciante": "linguagem simples, definição dos termos e um exemplo cotidiano",
    "Intermediário": "explicação com relações entre conceitos e um exemplo aplicado",
    "Avançado": "detalhamento técnico, limitações e um exemplo de aplicação",
}


class TutorValidationError(ValueError):
    """Parâmetros inválidos de estudo."""


def tutor_question(topic: str, level: str = "Iniciante") -> str:
    if (not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 65
            or "\x00" in topic):
        raise TutorValidationError("Assunto deve ter entre 1 e 65 caracteres.")
    if level not in LEVELS or not isinstance(level, str):
        raise TutorValidationError("Nível de aprendizagem inválido.")
    # The existing answer_from_hits bounds prompts to <=160 characters.
    description = {
        "Iniciante": "simples",
        "Intermediário": "aplicado",
        "Avançado": "técnico",
    }[level]
    prompt = (
        f"Explique em 3 etapas ({description}) sobre: {topic.strip()}. "
        "Cite fontes; se faltar base, diga."
    )
    if len(prompt) > 160:
        raise TutorValidationError("Tema de estudo muito longo.")
    return prompt
