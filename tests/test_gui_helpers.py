"""Tests sans affichage des fonctions utilitaires de l'interface graphique."""

import unittest

from ui.board_view import board_grid_position


class GuiHelperTests(unittest.TestCase):
    """Vérifie la correspondance entre les index du plateau et la grille graphique.

    Entrées:
        Aucune lors de l'utilisation normale par ``unittest``.

    Sortie:
        GuiHelperTests: Cas de test chargé par le framework de tests.
    """

    def test_board_corners_have_expected_positions(self) -> None:
        """Vérifie les coordonnées des quatre coins du plateau.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si un coin est placé au mauvais endroit.
        """
        self.assertEqual(board_grid_position(0), (10, 10))
        self.assertEqual(board_grid_position(10), (10, 0))
        self.assertEqual(board_grid_position(20), (0, 0))
        self.assertEqual(board_grid_position(30), (0, 10))

    def test_each_space_has_unique_grid_position(self) -> None:
        """Vérifie que les quarante cases occupent quarante cellules distinctes.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si deux cases se superposent.
        """
        positions = [board_grid_position(index) for index in range(40)]
        self.assertEqual(len(set(positions)), 40)

    def test_invalid_board_index_is_rejected(self) -> None:
        """Vérifie qu'un index hors plateau déclenche une erreur explicite.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si les index invalides sont acceptés.
        """
        with self.assertRaises(ValueError):
            board_grid_position(-1)

        with self.assertRaises(ValueError):
            board_grid_position(40)


if __name__ == "__main__":
    unittest.main()
