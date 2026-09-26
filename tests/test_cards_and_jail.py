"""Tests des cartes, des déplacements spéciaux et de la prison."""

import unittest

from monopoly import Game
from monopoly.cards import (
    CardDeck,
    GetOutOfJailCard,
    MoneyCard,
    MoveBackCard,
    NearestRailroadCard,
    NearestUtilityCard,
)


class CardsAndJailTests(unittest.TestCase):
    """Vérifie les nouvelles règles de cartes et de prison de la V3.

    Entrées:
        Aucune lors de l'utilisation normale par ``unittest``.

    Sortie:
        CardsAndJailTests: Cas de test exécuté par le framework.
    """

    def test_decks_contain_sixteen_cards(self) -> None:
        """Vérifie que les deux paquets classiques contiennent seize cartes au départ.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent la taille des deux paquets.
        """
        game = Game(["A", "B"], seed=1)
        self.assertEqual(len(game.chance_deck), 16)
        self.assertEqual(len(game.community_chest_deck), 16)

    def test_get_out_of_jail_card_is_held_and_returned(self) -> None:
        """Vérifie qu'une carte sortie de prison quitte le paquet puis y revient après usage.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent main, paquet et sortie de prison.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        card = GetOutOfJailCard("Sortie de prison", "chance")
        game.chance_deck = CardDeck("chance", [card], shuffle=False)

        game.chance_deck.draw(game, player)
        self.assertEqual(len(game.chance_deck), 0)
        self.assertIn(card, player.held_cards)

        game.rules.send_to_jail(player)
        self.assertTrue(game.use_get_out_of_jail_card(player))
        self.assertFalse(player.in_jail)
        self.assertNotIn(card, player.held_cards)
        self.assertEqual(len(game.chance_deck), 1)

    def test_pay_to_leave_jail_before_roll(self) -> None:
        """Vérifie le paiement volontaire de 50 avant un lancer normal.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions vérifient paiement, sortie et déplacement.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        game.rules.send_to_jail(player)
        game.roll_dice = lambda: (1, 2)

        result = game.take_turn(jail_action="pay")
        self.assertEqual(player.cash, 1450)
        self.assertFalse(player.in_jail)
        self.assertEqual(player.position, 13)
        self.assertEqual(result.dice, (1, 2))

    def test_double_releases_jail_without_extra_turn(self) -> None:
        """Vérifie qu'un double de sortie de prison ne donne pas un second lancer.

        Entrées:
            Aucune.

        Sortie:
            None: Le joueur est libéré mais le tour passe à l'adversaire.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        game.rules.send_to_jail(player)
        game.roll_dice = lambda: (2, 2)

        game.take_turn()
        self.assertFalse(player.in_jail)
        self.assertEqual(player.position, 14)
        self.assertIs(game.current_player, game.players[1])

    def test_third_failed_jail_roll_forces_payment_and_move(self) -> None:
        """Vérifie qu'après trois échecs le joueur paie puis avance avec le troisième lancer.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent amende, libération et position finale.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        game.rules.send_to_jail(player)
        player.jail_turns = 2
        game.roll_dice = lambda: (1, 2)

        game.take_turn()
        self.assertEqual(player.cash, 1450)
        self.assertFalse(player.in_jail)
        self.assertEqual(player.position, 13)

    def test_nearest_railroad_card_doubles_rent(self) -> None:
        """Vérifie que la carte prochaine gare facture le double du loyer normal.

        Entrées:
            Aucune.

        Sortie:
            None: Les soldes sont contrôlés après un loyer doublé de 25 à 50.
        """
        game = Game(["A", "B"], seed=1)
        owner, visitor = game.players
        owner.position = 15
        self.assertTrue(game.buy_current_property(owner))
        visitor.position = 7
        cash_before = visitor.cash

        NearestRailroadCard("Prochaine gare").apply(game, visitor)
        self.assertEqual(visitor.position, 15)
        self.assertEqual(visitor.cash, cash_before - 50)
        self.assertEqual(owner.cash, 1300 + 50)

    def test_nearest_utility_card_uses_new_roll_times_ten(self) -> None:
        """Vérifie que la prochaine compagnie utilise un nouveau lancer multiplié par dix.

        Entrées:
            Aucune.

        Sortie:
            None: Le visiteur paie 70 pour un nouveau lancer totalisant 7.
        """
        game = Game(["A", "B"], seed=1)
        owner, visitor = game.players
        owner.position = 12
        self.assertTrue(game.buy_current_property(owner))
        visitor.position = 7
        game.roll_dice = lambda: (3, 4)
        cash_before = visitor.cash

        NearestUtilityCard("Prochaine compagnie").apply(game, visitor)
        self.assertEqual(visitor.position, 12)
        self.assertEqual(visitor.cash, cash_before - 70)

    def test_move_back_three_can_chain_into_community_chest(self) -> None:
        """Vérifie qu'une carte recul de trois cases déclenche la case Caisse atteinte.

        Entrées:
            Aucune.

        Sortie:
            None: Le joueur recule de Chance 36 à Caisse 33 et reçoit la carte suivante.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        player.position = 36
        game.community_chest_deck = CardDeck(
            "community_chest",
            [MoneyCard("Prime", 100)],
            shuffle=False,
        )

        MoveBackCard("Reculez", 3).apply(game, player)
        self.assertEqual(player.position, 33)
        self.assertEqual(player.cash, 1600)

    def test_turn_result_reports_final_jail_space(self) -> None:
        """Vérifie que le résultat d'un tour indique Prison après la case Allez en prison.

        Entrées:
            Aucune.

        Sortie:
            None: La case finale doit être la case 10 et non la case 30 intermédiaire.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        player.position = 28
        game.roll_dice = lambda: (1, 1)

        result = game.take_turn()
        self.assertTrue(player.in_jail)
        self.assertEqual(player.position, 10)
        self.assertEqual(result.landed_space_name, "Prison / Simple visite")

    def test_card_movement_records_passage_over_go(self) -> None:
        """Vérifie qu'un déplacement par carte peut verser 200 et marquer ``passed_go``.

        Entrées:
            Aucune.

        Sortie:
            None: Le tour passant de Chance 36 à une destination basse enregistre Départ.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        player.position = 29
        game.roll_dice = lambda: (3, 4)
        game.chance_deck = CardDeck(
            "chance",
            [NearestRailroadCard("Prochaine gare")],
            shuffle=False,
        )

        result = game.take_turn()
        self.assertEqual(player.position, 5)
        self.assertTrue(result.passed_go)
        self.assertEqual(player.cash, 1700)


if __name__ == "__main__":
    unittest.main()
