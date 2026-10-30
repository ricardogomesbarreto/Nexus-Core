from .doctor import ollama_readiness, postgres_readiness, ubuntu_doctor
from .preflight import ollama_model_probe, postgres_auth_probe, ubuntu_preflight
"""Platform adapters: Ubuntu and Fedora adapters remain isolated and safety-first."""
from .linux import (
    LinuxProfile, UBUNTU_PACKAGES, FEDORA_PACKAGES, linux_profile,
    parse_os_release, platform_capabilities,
)
__all__ = [
    "ollama_readiness", "postgres_readiness", "ubuntu_doctor",
    "ollama_model_probe", "postgres_auth_probe", "ubuntu_preflight",
    "LinuxProfile", "UBUNTU_PACKAGES", "FEDORA_PACKAGES", "linux_profile",
    "parse_os_release", "platform_capabilities",
]
