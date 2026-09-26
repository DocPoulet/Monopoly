"""Vérifie que les classes et fonctions du projet restent documentées."""

import ast
import unittest
from pathlib import Path


class DocumentationTests(unittest.TestCase):
    """Contrôle automatiquement la présence de docstrings sur le code source.

    Entrées:
        Aucune lors de l'utilisation normale par ``unittest``.

    Sortie:
        DocumentationTests: Cas de test chargé par le framework de tests.
    """

    def test_all_classes_and_functions_have_docstrings(self) -> None:
        """Parcourt les fichiers Python et refuse toute classe/fonction sans docstring.

        Entrées:
            Aucune. Le dossier du projet est déduit depuis le fichier de test.

        Sortie:
            None: Le test échoue avec la liste des symboles non documentés.
        """
        root = Path(__file__).resolve().parents[1]
        missing: list[str] = []

        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node) is None:
                        relative = path.relative_to(root)
                        missing.append(f"{relative}:{node.lineno} {node.name}")

        self.assertEqual(missing, [], "Docstrings manquantes:\n" + "\n".join(missing))


if __name__ == "__main__":
    unittest.main()
