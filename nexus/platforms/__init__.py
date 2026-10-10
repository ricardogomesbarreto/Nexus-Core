from .doctor import ollama_readiness, postgres_readiness, ubuntu_doctor
from .preflight import ollama_model_probe, postgres_auth_probe, ubuntu_preflight
"""Platform adapters: Ubuntu Desktop first; future distributions stay isolated."""
from .linux import (
    LinuxProfile, UBUNTU_PACKAGES, linux_profile,
    parse_os_release, platform_capabilities,
)
__all__ = [
    "ollama_readiness", "postgres_readiness", "ubuntu_doctor",
    "ollama_model_probe", "postgres_auth_probe", "ubuntu_preflight",
    "LinuxProfile", "UBUNTU_PACKAGES", "linux_profile",
    "parse_os_release", "platform_capabilities",
]
