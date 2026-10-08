"""Contratos de ferramentas independentes do modelo e da interface."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from nexus.security import RiskLevel, SensitiveResource


class ContractViolation(ValueError):
    """Uma chamada ou resposta não obedece ao contrato declarado."""


class ValueKind(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


_MISSING = object()
_TYPES = {
    ValueKind.STRING: str,
    ValueKind.INTEGER: int,
    ValueKind.BOOLEAN: bool,
    ValueKind.ARRAY: list,
    ValueKind.OBJECT: dict,
}


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: ValueKind
    required: bool = True
    nullable: bool = False
    default: Any = _MISSING
    nonempty: bool = False
    item_fields: tuple["FieldSpec", ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.isidentifier():
            raise ValueError("Nome de campo inválido")
        if not isinstance(self.kind, ValueKind):
            raise ValueError("Tipo de campo inválido")
        if self.required and self.default is not _MISSING:
            raise ValueError("Campo obrigatório não pode ter valor padrão")
        if self.nonempty and self.kind is not ValueKind.STRING:
            raise ValueError("nonempty exige campo string")
        if not isinstance(self.item_fields, tuple) or (
            self.item_fields and (
                self.kind is not ValueKind.ARRAY
                or not all(isinstance(field, FieldSpec) for field in self.item_fields)
                or len({field.name for field in self.item_fields}) != len(self.item_fields)
            )
        ):
            raise ValueError("Itens estruturados exigem array de objetos")
        if isinstance(self.default, (dict, list, set)):
            raise ValueError("Valor padrão mutável não é permitido")
        if self.default is not _MISSING:
            self.validate(self.default)

    def validate(self, value: Any) -> None:
        if value is None and self.nullable:
            return
        if type(value) is not _TYPES[self.kind]:
            raise ContractViolation(f"Campo '{self.name}' deve ser {self.kind.value}.")
        if self.nonempty and not value.strip():
            raise ContractViolation(f"Campo '{self.name}' não pode ser vazio.")
        if self.item_fields:
            allowed = {field.name for field in self.item_fields}
            for item in value:
                if type(item) is not dict or item.keys() - allowed:
                    raise ContractViolation(f"Item inválido em '{self.name}'.")
                for field in self.item_fields:
                    if field.required and field.name not in item:
                        raise ContractViolation(f"Item incompleto em '{self.name}'.")
                    if field.name in item:
                        field.validate(item[field.name])

    def schema(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.kind.value}
        if self.nullable:
            result["type"] = [self.kind.value, "null"]
        if self.nonempty:
            result["minLength"] = 1
            result["pattern"] = "\\S"
        if self.default is not _MISSING:
            result["default"] = self.default
        if self.item_fields:
            result["items"] = {
                "type": "object",
                "properties": {field.name: field.schema() for field in self.item_fields},
                "required": [field.name for field in self.item_fields if field.required],
                "additionalProperties": False,
            }
        return result


@dataclass(frozen=True)
class ResourceSpec:
    name: str
    input_name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.isidentifier():
            raise ValueError("Nome de recurso inválido")
        if not isinstance(self.input_name, str) or not self.input_name.isidentifier():
            raise ValueError("Entrada do recurso inválida")


@dataclass(frozen=True)
class ToolContract:
    name: str
    description: str
    permission: RiskLevel
    inputs: tuple[FieldSpec, ...] = ()
    resources: tuple[ResourceSpec, ...] = ()
    outputs: tuple[FieldSpec, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.isidentifier():
            raise ValueError("Nome da ferramenta inválido")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("Descrição da ferramenta inválida")
        if not isinstance(self.permission, RiskLevel):
            raise ValueError("Permissão da ferramenta inválida")
        for fields, field_type in (
            (self.inputs, FieldSpec),
            (self.resources, ResourceSpec),
            (self.outputs, FieldSpec),
        ):
            if (
                not isinstance(fields, tuple)
                or not all(isinstance(field, field_type) for field in fields)
                or len({f.name for f in fields}) != len(fields)
            ):
                raise ValueError("Campos duplicados ou inválidos no contrato")
        input_names = {field.name for field in self.inputs}
        for resource in self.resources:
            if resource.input_name not in input_names:
                raise ValueError("Recurso sem entrada correspondente")
            field = next(f for f in self.inputs if f.name == resource.input_name)
            if field.kind is not ValueKind.STRING:
                raise ValueError("Entrada de recurso precisa ser string")
        if any(field.default is not _MISSING for field in self.outputs):
            raise ValueError("Saídas não podem ter valores padrão")

    def validate_inputs(self, values: dict[str, Any]) -> dict[str, Any]:
        fields = {field.name: field for field in self.inputs}
        unknown = values.keys() - fields.keys()
        if unknown:
            raise ContractViolation(f"Entrada desconhecida: {sorted(unknown)[0]}.")
        normalized = {}
        for field in self.inputs:
            if field.name in values:
                value = values[field.name]
            elif field.default is not _MISSING:
                value = field.default
            elif field.required:
                raise ContractViolation(f"Entrada obrigatória ausente: {field.name}.")
            else:
                continue
            field.validate(value)
            normalized[field.name] = value
        return normalized

    def expected_resources(
        self, values: dict[str, Any]
    ) -> tuple[SensitiveResource, ...]:
        return tuple(
            SensitiveResource(spec.name, values[spec.input_name])
            for spec in self.resources
            if values.get(spec.input_name) is not None
        )

    def validate_output(self, data: Any) -> None:
        if data is None and not self.outputs:
            return
        if type(data) is not dict:
            raise ContractViolation("Resultado deve ser um objeto estruturado.")
        fields = {field.name: field for field in self.outputs}
        unknown = data.keys() - fields.keys()
        if unknown:
            raise ContractViolation(f"Saída desconhecida: {sorted(unknown)[0]}.")
        for field in self.outputs:
            if field.name not in data:
                if field.required:
                    raise ContractViolation(f"Saída obrigatória ausente: {field.name}.")
                continue
            field.validate(data[field.name])

    def schema(self) -> dict[str, Any]:
        """Representação JSON compatível com ferramentas de integração."""

        def fields_schema(fields: tuple[FieldSpec, ...]) -> dict[str, Any]:
            return {
                "type": "object",
                "properties": {field.name: field.schema() for field in fields},
                "required": [field.name for field in fields if field.required],
                "additionalProperties": False,
            }

        return {
            "name": self.name,
            "description": self.description,
            "permission": self.permission.name,
            "inputs": fields_schema(self.inputs),
            "resources": [
                {"name": resource.name, "input": resource.input_name}
                for resource in self.resources
            ],
            "outputs": fields_schema(self.outputs),
            "error": {
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                },
                "additionalProperties": False,
            },
        }
