"""Tests des corrections graphiques de la quatrième version de l'interface."""

import unittest

from monopoly import Game
from ui.board_view import center_deck_rectangles


class GuiV4Tests(unittest.TestCase):
    """Vérifie le placement des cartes centrales et la préparation des enchères.

    Entrées:
        Aucune lors du chargement par ``unittest``.

    Sortie:
        GuiV4Tests: Cas de tests exécutables automatiquement.
    """

    def test_center_cards_stay_inside_center_horizontal_bounds(self) -> None:
        """Vérifie que Chance et Caisse restent dans la zone centrale du plateau.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si une carte dépasse le bord gauche ou droit.
        """
        x1 = 100.0
        x2 = 820.0
        cell = 80.0
        community, chance = center_deck_rectangles(x1, x2, 460.0, cell)

        for x, _y, width, _height in (community, chance):
            self.assertGreaterEqual(x, x1)
            self.assertLessEqual(x + width, x2)

        self.assertLessEqual(community[0] + community[2], chance[0])

    def test_auction_starts_with_all_active_players(self) -> None:
        """Vérifie que le panneau intégré recevra tous les joueurs actifs.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si l'enchère ne contient pas les joueurs attendus.
        """
        game = Game(["A", "B", "C"], seed=1)
        auction = game.start_auction(game.board[1])
        self.assertEqual([p.name for p in auction.active_bidders], ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
