"""Operações locais e limitadas com texto fornecido explicitamente pelo usuário."""
import base64
import binascii
import hashlib
from urllib.parse import quote, unquote_to_bytes


OPERATIONS = ("sha256", "base64-encode", "base64-decode", "hex-encode",
              "hex-decode", "url-encode", "url-decode")
MAX_BYTES = 64 * 1024


def transform_text(operation: str, payload: bytes) -> str:
    if operation not in OPERATIONS or not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ValueError("Operação ou tamanho de entrada inválido (máximo 64 KiB).")
    try:
        if operation == "sha256":
            return hashlib.sha256(payload).hexdigest()
        if operation == "base64-encode":
            result = base64.b64encode(payload).decode("ascii")
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
        elif operation == "hex-decode":
            output = bytes.fromhex(text.strip())
        elif operation == "url-encode":
            result = quote(text, safe="")
            if len(result) > MAX_BYTES:
                raise ValueError("Saída acima de 64 KiB.")
            return result
        else:
            output = unquote_to_bytes(text)
        if len(output) > MAX_BYTES:
            raise ValueError("Saída acima de 64 KiB.")
        return output.decode("utf-8")
    except (UnicodeError, binascii.Error) as exc:
        raise ValueError("Entrada inválida; decodificação exige texto UTF-8 válido.") from exc
    except ValueError as exc:
        if str(exc) == "Saída acima de 64 KiB.":
            raise
        raise ValueError("Entrada inválida; decodificação exige texto UTF-8 válido.") from exc
