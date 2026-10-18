"""User-facing NEXUS CORE action names, independent of backend identifiers."""

ACTION_LABELS = {
    "system_info": "Informações do sistema",
    "list_directory": "Listar pasta",
    "read_file": "Ler arquivo",
    "file_metadata": "Consultar arquivo",
    "create_directory": "Criar pasta",
    "launch_application": "Abrir aplicativo",
    "open_default_browser": "Abrir navegador padrão",
    "terminal_sandbox": "Comando no terminal",
    "desktop_window_info": "Consultar janela",
    "desktop_type_text": "Digitar na janela",
    "desktop_navigate": "Navegar na janela",
    "craft_convert_local": "Converter arquivo",
    "craft_inspect_local": "Consultar metadados",
    "pdf_extract_pages_local": "Extrair páginas de PDF",
    "pdf_combine_local": "Juntar dois PDFs",
    "pdf_render_local": "Gerar prévia de PDF",
    "inspect_artifact_local": "Inspecionar arquivo",
    "edit_image_local": "Editar foto",
    "image_geometry_local": "Ajustar dimensões da foto",
    "create_graphic_local": "Criar cartaz",
}

RESOURCE_LABELS = {
    "source": "Arquivo de origem",
    "source_a": "Primeiro PDF",
    "source_b": "Segundo PDF",
    "output": "Arquivo de saída",
}


def action_label(identifier: str) -> str:
    """Use a descriptive action label; never display an internal tool id."""
    return ACTION_LABELS.get(identifier, "Ação local")


def resource_label(identifier: str) -> str:
    return RESOURCE_LABELS.get(identifier, "Recurso")
