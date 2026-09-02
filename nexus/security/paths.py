from pathlib import Path


class PathSecurity:
    """
    Controla quais caminhos do sistema o Nexus pode acessar.

    A política é restritiva:
    o Nexus trabalha dentro do diretório HOME do usuário,
    mas diretórios críticos do sistema e áreas sensíveis
    do usuário são protegidos.
    """

    def __init__(self):
        self.home = Path.home().resolve()

        self.protected_paths = [
            # Diretórios críticos do sistema
            Path("/boot").resolve(),
            Path("/etc").resolve(),
            Path("/bin").resolve(),
            Path("/sbin").resolve(),
            Path("/usr").resolve(),
            Path("/var").resolve(),
            Path("/root").resolve(),
            Path("/sys").resolve(),
            Path("/proc").resolve(),
            Path("/dev").resolve(),
            Path("/run").resolve(),
            Path("/lib").resolve(),
            Path("/lib64").resolve(),
            Path("/opt").resolve(),
            Path("/srv").resolve(),
            Path("/snap").resolve(),

            # Diretórios sensíveis do usuário
            self.home / ".ssh",
            self.home / ".gnupg",
            self.home / ".aws",
            self.home / ".docker",
            self.home / ".kube",
            self.home / ".config",
            self.home / ".local" / "share" / "keyrings",
        ]

    def resolve(self, path: str | Path) -> Path:
        """
        Resolve um caminho absoluto de forma segura.
        """
        return Path(path).expanduser().resolve(strict=False)

    def is_protected(self, path: str | Path) -> bool:
        """
        Verifica se o caminho está dentro de uma área protegida.
        """

        target = self.resolve(path)

        for protected in self.protected_paths:
            if self._is_inside(target, protected):
                return True

        return False

    def is_allowed(self, path: str | Path) -> bool:
        """
        Verifica se o caminho está dentro da área autorizada
        e não pertence a uma área protegida.
        """

        target = self.resolve(path)

        if self.is_protected(target):
            return False

        return self._is_inside(
            target,
            self.home,
        )

    @staticmethod
    def _is_inside(
        target: Path,
        parent: Path,
    ) -> bool:
        """
        Verifica se target está dentro de parent.
        """

        try:
            target.relative_to(parent)
            return True

        except ValueError:
            return False
