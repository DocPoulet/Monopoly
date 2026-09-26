"""Tests des données et helpers de la nouvelle interface intégrée."""

import unittest

from monopoly import Game
from monopoly.cards import MoneyCard
from monopoly.properties import Property, Railroad, Utility
from ui.property_card import PropertyCardOverlay
from ui.widgets import DiceFace


class UiV2Tests(unittest.TestCase):
    """Vérifie les helpers des cartes de propriété et des dés cliquables.

    Entrées:
        Aucune lors du chargement par ``unittest``.

    Sortie:
        UiV2Tests: Ensemble de tests automatisés sans interaction utilisateur.
    """

    def test_property_card_rows_for_property(self) -> None:
        """Vérifie que la fiche terrain contient le barème complet des loyers.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si les sept lignes attendues sont absentes.
        """
        game = Game(["A", "B"], seed=1)
        space = game.board[1]
        self.assertIsInstance(space, Property)
        rows = PropertyCardOverlay._detail_rows(space)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[0][0], "Loyer")
        self.assertEqual(rows[-1][0], "Prix d'une maison")

    def test_property_card_rows_for_railroad(self) -> None:
        """Vérifie le barème 25/50/100/200 d'une gare.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si les quatre niveaux de gare sont incorrects.
        """
        game = Game(["A", "B"], seed=1)
        space = game.board[5]
        self.assertIsInstance(space, Railroad)
        rows = PropertyCardOverlay._detail_rows(space)
        self.assertEqual([value for _, value, _ in rows], ["25 $", "50 $", "100 $", "200 $"])

    def test_property_card_rows_for_utility(self) -> None:
        """Vérifie que la compagnie affiche les multiplicateurs 4× et 10×.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si l'une des deux formules est absente.
        """
        game = Game(["A", "B"], seed=1)
        space = game.board[12]
        self.assertIsInstance(space, Utility)
        rows = PropertyCardOverlay._detail_rows(space)
        self.assertIn("4 ×", rows[0][1])
        self.assertIn("10 ×", rows[1][1])

    def test_drawn_card_event_is_recorded(self) -> None:
        """Vérifie qu'une pioche est exposée par le moteur pour le plateau.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si aucune trace structurée de la carte n'est conservée.
        """
        game = Game(["A", "B"], seed=1)
        game.drawn_cards_this_turn = []
        card = MoneyCard("Test", 10)
        game.chance_deck.cards.clear()
        game.chance_deck.cards.append(card)
        message = game.chance_deck.draw(game, game.players[0])
        self.assertEqual(len(game.drawn_cards_this_turn), 1)
        event = game.drawn_cards_this_turn[0]
        self.assertIs(event.card, card)
        self.assertEqual(event.deck_name, "chance")
        self.assertEqual(event.message, message)

    def test_dice_layouts_cover_six_faces(self) -> None:
        """Vérifie que chaque face de dé de 1 à 6 possède une disposition de points.

        Entrées:
            Aucune.

        Sortie:
            None: Le test échoue si une face de dé manque.
        """
        self.assertEqual(set(DiceFace.PIP_LAYOUTS), {1, 2, 3, 4, 5, 6})


if __name__ == "__main__":
    unittest.main()
