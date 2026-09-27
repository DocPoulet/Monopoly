"""Analyse les événements structurés d'une partie pour produire des statistiques."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .history import GameHistory


@dataclass
class PlayerStatistics:
    """Regroupe les principaux compteurs historiques d'un joueur.

    Entrées:
        player_id (int): Identifiant du joueur.
        name (str): Nom affiché.
        turns (int): Tours joués.
        doubles (int): Doubles obtenus.
        cards_drawn (int): Cartes piochées.
        properties_bought (int): Biens achetés directement.
        rent_paid (int): Total des loyers versés.
        rent_received (int): Total des loyers reçus.
        buildings_built (int): Maisons et hôtels construits.
        mortgages (int): Hypothèques réalisées.
        trades (int): Échanges conclus impliquant le joueur.
        bankrupt (bool): État actuel de faillite.

    Sortie:
        PlayerStatistics: Compteurs individuels prêts à être affichés.
    """

    player_id: int
    name: str
    turns: int = 0
    doubles: int = 0
    cards_drawn: int = 0
    properties_bought: int = 0
    rent_paid: int = 0
    rent_received: int = 0
    buildings_built: int = 0
    mortgages: int = 0
    trades: int = 0
    bankrupt: bool = False


@dataclass
class GameStatistics:
    """Résumé statistique dérivé de l'historique et de l'état courant.

    Entrées:
        turns (int): Nombre de tours de table représentés dans l'historique.
        cards_drawn (int): Nombre total de cartes piochées.
        purchases (int): Achats directs.
        auctions_won (int): Enchères immobilières remportées.
        building_auctions_won (int): Enchères de bâtiments remportées.
        trades (int): Échanges conclus.
        bankruptcies (int): Faillites enregistrées.
        rent_transferred (int): Total des loyers payés.
        buildings_built (int): Nombre de constructions.
        mortgages (int): Nombre d'hypothèques.
        players (list[PlayerStatistics]): Compteurs individuels.

    Sortie:
        GameStatistics: Vue synthétique destinée à l'interface ou aux simulations.
    """

    turns: int = 0
    cards_drawn: int = 0
    purchases: int = 0
    auctions_won: int = 0
    building_auctions_won: int = 0
    trades: int = 0
    bankruptcies: int = 0
    rent_transferred: int = 0
    buildings_built: int = 0
    mortgages: int = 0
    players: list[PlayerStatistics] = field(default_factory=list)

    @classmethod
    def from_game(cls, game: "Game") -> "GameStatistics":
        """Calcule les statistiques à partir d'une partie et de son historique.

        Entrées:
            game (Game): Partie courante ou terminée.

        Sortie:
            GameStatistics: Compteurs globaux et par joueur.
        """
        stats = cls()
        round_numbers: set[int] = set()
        player_rounds: dict[int, set[int]] = {}
        by_player = {
            player.player_id: PlayerStatistics(
                player_id=player.player_id,
                name=player.name,
                bankrupt=player.bankrupt,
            )
            for player in game.players
        }

        for event in game.history.events:
            player_stats = (
                by_player.get(event.player_id)
                if event.player_id is not None
                else None
            )

            if event.event_type == "turn":
                if event.turn_number > 0:
                    round_numbers.add(event.turn_number)
                if player_stats is not None:
                    player_rounds.setdefault(player_stats.player_id, set()).add(
                        event.turn_number
                    )
                    if bool(event.data.get("rolled_double", False)):
                        player_stats.doubles += 1

            elif event.event_type == "card_draw":
                stats.cards_drawn += 1
                if player_stats is not None:
                    player_stats.cards_drawn += 1

            elif event.event_type == "purchase":
                stats.purchases += 1
                if player_stats is not None:
                    player_stats.properties_bought += 1

            elif event.event_type == "auction_win":
                stats.auctions_won += 1

            elif event.event_type == "building_auction_win":
                stats.building_auctions_won += 1

            elif event.event_type == "building":
                stats.buildings_built += 1
                if player_stats is not None:
                    player_stats.buildings_built += 1

            elif event.event_type == "mortgage":
                stats.mortgages += 1
                if player_stats is not None:
                    player_stats.mortgages += 1

            elif event.event_type == "rent":
                amount = int(event.data.get("amount", 0))
                stats.rent_transferred += amount
                if player_stats is not None:
                    player_stats.rent_paid += amount

                recipient_id = event.data.get("recipient_id")
                if recipient_id is not None and int(recipient_id) in by_player:
                    by_player[int(recipient_id)].rent_received += amount

            elif event.event_type == "trade":
                stats.trades += 1
                participant_ids = {
                    int(item)
                    for item in event.data.get("participant_ids", [])
                }
                for player_id in participant_ids:
                    if player_id in by_player:
                        by_player[player_id].trades += 1

            elif event.event_type == "bankruptcy":
                stats.bankruptcies += 1

        stats.turns = len(round_numbers)
        for player_id, rounds in player_rounds.items():
            if player_id in by_player:
                by_player[player_id].turns = len(rounds)

        stats.players = [
            by_player[player.player_id]
            for player in game.players
        ]
        return stats

    def summary_lines(self) -> list[str]:
        """Produit quelques lignes compactes pour l'interface.

        Entrées:
            Aucune.

        Sortie:
            list[str]: Indicateurs globaux sous forme de textes courts.
        """
        return [
            f"Tours : {self.turns}",
            f"Cartes : {self.cards_drawn}",
            f"Achats : {self.purchases}",
            f"Enchères gagnées : {self.auctions_won + self.building_auctions_won}",
            f"Constructions : {self.buildings_built}",
            f"Hypothèques : {self.mortgages}",
            f"Échanges : {self.trades}",
            f"Loyers versés : {self.rent_transferred} $",
            f"Faillites : {self.bankruptcies}",
        ]
