"""Operações locais e limitadas com texto fornecido explicitamente pelo usuário."""
import base64
import binascii
import hashlib
import json
import codecs
import re
from urllib.parse import quote, unquote_to_bytes


OPERATIONS = ("sha256", "sha512", "sha3-256", "blake2b-256",
              "base64-encode", "base64-decode", "base32-encode", "base32-decode",
              "hex-encode", "hex-decode", "url-encode", "url-decode",
              "rot13", "json-pretty", "json-minify")
MAX_BYTES = 64 * 1024
MAX_STEPS = 8


def transform_text(operation: str, payload: bytes) -> str:
    if operation not in OPERATIONS or not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ValueError("Operação ou tamanho de entrada inválido (máximo 64 KiB).")
    try:
        if operation in {"sha256", "sha512", "sha3-256", "blake2b-256"}:
            algorithms = {"sha256": hashlib.sha256, "sha512": hashlib.sha512,
                          "sha3-256": hashlib.sha3_256,
                          "blake2b-256": lambda data: hashlib.blake2b(data, digest_size=32)}
            return algorithms[operation](payload).hexdigest()
        if operation == "base64-encode":
            result = base64.b64encode(payload).decode("ascii")
            if len(result) > MAX_BYTES:
                raise ValueError("Saída acima de 64 KiB.")
            return result
        if operation == "base32-encode":
            result = base64.b32encode(payload).decode("ascii")
            if len(result) > MAX_BYTES:
                raise ValueError("Saída acima de 64 KiB.")
            return result
        if operation == "hex-encode":
            result = payload.hex()
            if len(result) > MAX_BYTES:
                raise ValueError("Saída acima de 64 KiB.")
            return result
        text = payload.decode("utf-8")
        if operation == "base64-decode":
            output = base64.b64decode(text.strip(), validate=True)
        elif operation == "base32-decode":
            output = base64.b32decode(text.strip(), casefold=True)
        elif operation == "hex-decode":
            output = bytes.fromhex(text.strip())
        elif operation == "url-encode":
            result = quote(text, safe="")
            if len(result) > MAX_BYTES:
                raise ValueError("Saída acima de 64 KiB.")
            return result
        elif operation == "rot13":
            result = codecs.encode(text, "rot_13")
            if len(result.encode("utf-8")) > MAX_BYTES:
                raise ValueError("Saída acima de 64 KiB.")
            return result
        elif operation in {"json-pretty", "json-minify"}:
            document = json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Constante JSON inválida.")))
            result = json.dumps(document, ensure_ascii=False,
                                indent=2 if operation == "json-pretty" else None,
                                separators=None if operation == "json-pretty" else (",", ":"),
                                allow_nan=False)
            if len(result.encode("utf-8")) > MAX_BYTES:
                raise ValueError("Saída acima de 64 KiB.")
            return result
        else:
            # unquote_to_bytes accepts malformed percent escapes unchanged.
            if re.search(r"%(?![0-9A-Fa-f]{2})", text):
                raise ValueError("Entrada inválida; codificação URL incompleta.")
            output = unquote_to_bytes(text)
        if len(output) > MAX_BYTES:
            raise ValueError("Saída acima de 64 KiB.")
        return output.decode("utf-8")
    except (UnicodeError, binascii.Error, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("Entrada inválida; decodificação exige texto UTF-8 válido.") from exc
    except ValueError as exc:
        if str(exc) in {"Saída acima de 64 KiB.", "Entrada inválida; codificação URL incompleta."}:
            raise
        raise ValueError("Entrada inválida; decodificação exige texto UTF-8 válido.") from exc


def transform_recipe(operations: tuple[str, ...] | list[str], payload: bytes) -> str:
    """Apply a bounded, explicit sequence; intermediate data stays in memory."""
    if (not isinstance(operations, (tuple, list)) or not 1 <= len(operations) <= MAX_STEPS
            or any(op not in OPERATIONS for op in operations)):
        raise ValueError("Receita inválida (1 a 8 operações conhecidas).")
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ValueError("Entrada acima de 64 KiB.")
    current = payload
    for operation in operations:
        current = transform_text(operation, current).encode("utf-8")
    return current.decode("utf-8")
