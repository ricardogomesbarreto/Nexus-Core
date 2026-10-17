"""Bounded WebAssembly structural triage, without running or decoding code.

Only section envelopes are inspected. Import/export names and binary payloads
are never returned to the assistant or to the conversation history.
"""

SECTION_NAMES = {
    0: "personalizadas", 1: "tipos", 2: "imports", 3: "funções",
    4: "tabelas", 5: "memórias", 6: "globais", 7: "exports",
    8: "início", 9: "elementos", 10: "código", 11: "dados",
    12: "contagem_dados",
}
MAX_SECTIONS = 512


def _read_uleb32(data: bytes, start: int) -> tuple[int, int]:
    """Decode at most five bytes, rejecting truncated and overflowing sizes."""
    value = 0
    for count in range(5):
        offset = start + count
        if offset >= len(data):
            raise ValueError("Tamanho de seção WASM truncado.")
        octet = data[offset]
        if count == 4 and octet & 0xF0:
            raise ValueError("Tamanho de seção WASM fora de u32.")
        value |= (octet & 0x7F) << (count * 7)
        if octet < 0x80:
            return value, offset + 1
    raise ValueError("Tamanho de seção WASM inválido.")


def summarize_wasm(data: bytes, *, total_size: int) -> str:
    """Count section envelopes in a bounded prefix (never claim semantic validity).

    The caller supplies the *actual* file length: a 128-KiB prefix may end in
    the middle of a valid large section. Report this as partial, not failure.
    """
    if len(data) < 8 or data[:4] != b"\x00asm":
        raise ValueError("Cabeçalho WASM ausente.")
    if total_size < len(data):
        raise ValueError("Tamanho total inconsistente.")
    counts: dict[int, int] = {}
    position = 8
    partial = False
    while position < len(data):
        if sum(counts.values()) >= MAX_SECTIONS:
            raise ValueError("Número de seções WASM excedeu o limite local.")
        section = data[position]
        position += 1
        if section > 12:
            raise ValueError("Identificador de seção WASM desconhecido.")
        try:
            length, position = _read_uleb32(data, position)
        except ValueError:
            if len(data) < total_size:
                partial = True
                break
            raise
        counts[section] = counts.get(section, 0) + 1
        if length > len(data) - position:
            if len(data) < total_size:
                partial = True
                break
            raise ValueError("Seção WASM truncada no arquivo.")
        position += length
    if len(data) < total_size:
        partial = True
    detail = ", ".join(
        f"{SECTION_NAMES[number]}={quantity}"
        for number, quantity in sorted(counts.items())
    ) or "nenhuma seção observada"
    state = "prefixo parcial" if partial else "envelopes completos"
    return (
        f"Índice WASM ({state}): {detail}; "
        "nomes, código e conteúdo das seções não foram examinados."
    )
