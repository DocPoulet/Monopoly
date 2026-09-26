"""Tests unitaires du moteur Monopoly et de ses règles immobilières."""

import unittest

from monopoly import Game
from monopoly.properties import Property


class GameTests(unittest.TestCase):
    """Vérifie les comportements principaux du moteur de jeu.

    Entrées:
        Aucune lors de l'utilisation normale par ``unittest``.

    Sortie:
        GameTests: Cas de test chargé et exécuté par ``unittest``.
    """

    def _buy_group(self, game: Game, player_index: int, indexes: tuple[int, ...]) -> None:
        """Achète plusieurs terrains pour un joueur afin de préparer un test.

        Entrées:
            game (Game): Partie de test.
            player_index (int): Index du joueur qui achète les biens.
            indexes (tuple[int, ...]): Index des cases à acheter.

        Sortie:
            None: Le joueur devient propriétaire de chaque case demandée.
        """
        player = game.players[player_index]
        for index in indexes:
            player.position = index
            self.assertTrue(game.buy_current_property(player))

    def test_board_has_40_spaces(self) -> None:
        """Vérifie que le plateau standard contient exactement 40 cases.

        Entrées:
            Aucune.

        Sortie:
            None: Une assertion échoue si le plateau n'a pas 40 cases.
        """
        game = Game(["A", "B"], seed=1)
        self.assertEqual(len(game.board), 40)

    def test_buy_property(self) -> None:
        """Vérifie l'achat direct d'un terrain et la diminution du solde.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent propriétaire et argent restant.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        player.position = 1

        success = game.buy_current_property(player)

        self.assertTrue(success)
        self.assertEqual(player.cash, 1440)
        self.assertIs(game.board[1].owner, player)

    def test_monopoly_doubles_base_rent(self) -> None:
        """Vérifie que le monopole double le loyer de base sans bâtiment.

        Entrées:
            Aucune.

        Sortie:
            None: Une assertion valide que le loyer de 2 devient 4.
        """
        game = Game(["A", "B"], seed=1)
        self._buy_group(game, 0, (1, 3))
        self.assertEqual(game.board[1].calculate_rent(game, 7), 4)

    def test_railroad_rent_scales(self) -> None:
        """Vérifie que deux gares appartenant au même joueur produisent 50 de loyer.

        Entrées:
            Aucune.

        Sortie:
            None: Une assertion contrôle le barème des gares.
        """
        game = Game(["A", "B"], seed=1)
        self._buy_group(game, 0, (5, 15))
        self.assertEqual(game.board[5].calculate_rent(game, 7), 50)

    def test_utility_rent(self) -> None:
        """Vérifie qu'une compagnie unique facture quatre fois le total des dés.

        Entrées:
            Aucune.

        Sortie:
            None: Une assertion vérifie un loyer de 32 pour un lancer total de 8.
        """
        game = Game(["A", "B"], seed=1)
        self._buy_group(game, 0, (12,))
        self.assertEqual(game.board[12].calculate_rent(game, 8), 32)

    def test_houses_must_be_built_evenly(self) -> None:
        """Vérifie qu'une seconde maison ne peut pas précéder la première sur l'autre terrain.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent le développement uniforme du groupe marron.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        self._buy_group(game, 0, (1, 3))

        first = game.board[1]
        second = game.board[3]
        self.assertIsInstance(first, Property)
        self.assertIsInstance(second, Property)

        self.assertTrue(game.rules.build_house(player, first))
        self.assertFalse(game.rules.build_house(player, first))
        self.assertTrue(game.rules.build_house(player, second))
        self.assertTrue(game.rules.build_house(player, first))

    def test_build_hotel_requires_four_houses_across_group(self) -> None:
        """Vérifie qu'un hôtel exige un développement suffisant sur tout le groupe.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions valident les quatre maisons puis l'hôtel.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        player.cash = 5000
        self._buy_group(game, 0, (1, 3))
        first = game.board[1]
        second = game.board[3]
        self.assertIsInstance(first, Property)
        self.assertIsInstance(second, Property)

        for _ in range(4):
            self.assertTrue(game.rules.build_house(player, first))
            self.assertTrue(game.rules.build_house(player, second))

        self.assertTrue(game.rules.build_hotel(player, first))
        self.assertTrue(first.hotel)
        self.assertEqual(first.houses, 0)

    def test_sell_building_is_even(self) -> None:
        """Vérifie que les bâtiments sont vendus en sens inverse de manière uniforme.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions empêchent de dépouiller d'abord le terrain moins développé.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        self._buy_group(game, 0, (1, 3))
        first = game.board[1]
        second = game.board[3]
        self.assertIsInstance(first, Property)
        self.assertIsInstance(second, Property)

        self.assertTrue(game.rules.build_house(player, first))
        self.assertTrue(game.rules.build_house(player, second))
        self.assertTrue(game.rules.build_house(player, first))

        self.assertFalse(game.rules.sell_building(player, second))
        self.assertTrue(game.rules.sell_building(player, first))

    def test_mortgage_and_unmortgage(self) -> None:
        """Vérifie le versement d'hypothèque puis le paiement avec 10 % d'intérêts.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent état hypothéqué et variations de trésorerie.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        self._buy_group(game, 0, (5,))
        railroad = game.board[5]

        cash_before = player.cash
        self.assertTrue(game.rules.mortgage_property(player, railroad))
        self.assertEqual(player.cash, cash_before + 100)
        self.assertTrue(railroad.mortgaged)

        cost = railroad.unmortgage_cost
        cash_before = player.cash
        self.assertTrue(game.rules.unmortgage_property(player, railroad))
        self.assertEqual(player.cash, cash_before - cost)
        self.assertFalse(railroad.mortgaged)

    def test_cannot_mortgage_color_group_with_buildings(self) -> None:
        """Vérifie qu'un terrain ne peut être hypothéqué tant que le groupe a un bâtiment.

        Entrées:
            Aucune.

        Sortie:
            None: Une assertion confirme que l'hypothèque est refusée.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        self._buy_group(game, 0, (1, 3))
        first = game.board[1]
        second = game.board[3]
        self.assertIsInstance(first, Property)
        self.assertIsInstance(second, Property)

        self.assertTrue(game.rules.build_house(player, first))
        self.assertFalse(game.rules.mortgage_property(player, second))

    def test_auction_awards_property_to_highest_bidder(self) -> None:
        """Vérifie qu'une enchère attribue le bien au dernier enchérisseur actif.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent gagnant, prix, propriétaire et trésorerie.
        """
        game = Game(["A", "B", "C"], seed=1)
        space = game.board[1]
        auction = game.start_auction(space)
        a, b, c = game.players

        self.assertTrue(auction.place_bid(a, 20))
        self.assertTrue(auction.place_bid(b, 30))
        self.assertTrue(auction.withdraw(a))
        self.assertTrue(auction.withdraw(c))
        result = auction.finish()

        self.assertTrue(result.sold)
        self.assertIs(result.winner, b)
        self.assertEqual(result.amount, 30)
        self.assertIs(space.owner, b)
        self.assertEqual(b.cash, 1470)

    def test_property_returned_to_bank_loses_buildings(self) -> None:
        """Vérifie qu'un terrain rendu à la banque ne conserve aucun bâtiment.

        Entrées:
            Aucune.

        Sortie:
            None: Les assertions contrôlent la remise à zéro du développement.
        """
        game = Game(["A", "B"], seed=1)
        player = game.players[0]
        self._buy_group(game, 0, (1, 3))
        first = game.board[1]
        self.assertIsInstance(first, Property)
        self.assertTrue(game.rules.build_house(player, first))

        first.reset_ownership()
        self.assertIsNone(first.owner)
        self.assertEqual(first.houses, 0)
        self.assertFalse(first.hotel)


if __name__ == "__main__":
    unittest.main()
