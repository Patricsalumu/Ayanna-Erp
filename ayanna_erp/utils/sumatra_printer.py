import os
import platform
import shutil
import subprocess


class SumatraPrinter:
    """Printer helper that sends PDF files to SumatraPDF for silent printing."""

    SUMATRA_EXECUTABLE = "SumatraPDF.exe"
    SYSTEM_PATHS = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
    ]

    def __init__(self, executable_path: str | None = None):
        self._executable_path = executable_path or self.find_sumatra_executable()

    def find_sumatra_executable(self) -> str | None:
        if platform.system() != "Windows":
            return None

        candidates = []
        found_in_path = shutil.which(self.SUMATRA_EXECUTABLE)
        if found_in_path:
            candidates.append(found_in_path)

        candidates.extend(self.SYSTEM_PATHS)
        candidates.extend(self._get_embedded_paths())

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return os.path.abspath(candidate)

        return None

    def _get_embedded_paths(self) -> list[str]:
        current_dir = os.path.abspath(os.path.dirname(__file__))
        repo_root = os.path.dirname(os.path.dirname(current_dir))
        embedded_paths = [
            os.path.join(repo_root, "printers", self.SUMATRA_EXECUTABLE),
            os.path.join(repo_root, "Ayanna ERP", "printers", self.SUMATRA_EXECUTABLE),
        ]
        return embedded_paths

    def available(self) -> bool:
        return self._executable_path is not None

    def print_pdf(self, pdf_path: str) -> tuple[bool, str | None]:
        if platform.system() != "Windows":
            return False, "L'impression via SumatraPDF n'est prise en charge que sous Windows."

        if not self.available():
            return False, (
                "SumatraPDF est introuvable.\n"
                "Veuillez installer SumatraPDF ou le fournir dans le dossier `printers` de l'application "
                "afin d'activer l'impression automatique des bons de commande."
            )

        if not os.path.isfile(pdf_path):
            return False, f"Fichier PDF introuvable : {pdf_path}"

        try:
            completed = subprocess.run(
                [
                    self._executable_path,
                    "-print-to-default",
                    "-silent",
                    pdf_path,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                stdout = (completed.stdout or "").strip()
                message = stderr or stdout or f"Code de sortie {completed.returncode}"
                return False, f"SumatraPDF a échoué : {message}"

            return True, None
        except FileNotFoundError:
            return False, "SumatraPDF n'a pas été trouvé lors de l'appel du binaire."
        except subprocess.SubprocessError as exc:
            return False, str(exc)
        except Exception as exc:
            return False, str(exc)
