"""Analyse l'historique et le replay pour produire des statistiques avancées."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game


@dataclass
class PlayerStatistics:
    """Regroupe les compteurs historiques et l'état financier d'un joueur.

    Entrées:
        player_id (int): Identifiant du joueur.
        name (str): Nom affiché.
        turns (int): Tours de table auxquels le joueur a participé.
        doubles (int): Doubles obtenus.
        cards_drawn (int): Cartes piochées.
        properties_bought (int): Biens achetés directement.
        rent_paid (int): Total des loyers versés.
        rent_received (int): Total des loyers reçus.
        buildings_built (int): Maisons et hôtels construits.
        mortgages (int): Hypothèques réalisées.
        trades (int): Échanges conclus impliquant le joueur.
        jail_visits (int): Entrées en prison enregistrées.
        biggest_rent_paid (int): Plus gros loyer payé en une fois.
        biggest_rent_received (int): Plus gros loyer encaissé en une fois.
        cash (int): Cash actuel.
        net_worth (int): Patrimoine actuel estimé.
        properties_owned (int): Nombre actuel de biens.
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
    jail_visits: int = 0
    biggest_rent_paid: int = 0
    biggest_rent_received: int = 0
    cash: int = 0
    net_worth: int = 0
    properties_owned: int = 0
    bankrupt: bool = False


@dataclass
class PropertyStatistics:
    """Mesure les loyers réellement générés par une propriété.

    Entrées:
        property_index (int): Index de la case.
        name (str): Nom actuel du bien.
        rent_received (int): Total des loyers encaissés sur ce bien.
        rent_events (int): Nombre de loyers effectivement payés.
        biggest_rent (int): Plus gros loyer unique de ce bien.

    Sortie:
        PropertyStatistics: Rentabilité historique d'un bien.
    """

    property_index: int
    name: str
    rent_received: int = 0
    rent_events: int = 0
    biggest_rent: int = 0


@dataclass(frozen=True)
class RoundStatisticsPoint:
    """Point de série temporelle dérivé d'un snapshot de replay.

    Entrées:
        round_number (int): Tour de table du point.
        label (str): Libellé du snapshot.
        cash_by_player (dict[int, int]): Cash par joueur.
        worth_by_player (dict[int, int]): Patrimoine par joueur.
        properties_by_player (dict[int, int]): Nombre de biens par joueur.
        free_parking_pot (int): Cagnotte Parc Gratuit.

    Sortie:
        RoundStatisticsPoint: Point exploitable par les graphiques de l'interface.
    """

    round_number: int
    label: str
    cash_by_player: dict[int, int]
    worth_by_player: dict[int, int]
    properties_by_player: dict[int, int]
    free_parking_pot: int


@dataclass
class GameStatistics:
    """Résumé statistique avancé dérivé de l'historique et des snapshots.

    Entrées:
        turns (int): Nombre de tours de table représentés.
        cards_drawn (int): Nombre total de cartes piochées.
        purchases (int): Achats directs.
        auctions_won (int): Enchères immobilières remportées.
        building_auctions_won (int): Enchères de bâtiments remportées.
        trades (int): Échanges conclus.
        bankruptcies (int): Faillites enregistrées.
        rent_transferred (int): Total des loyers payés.
        buildings_built (int): Nombre de constructions.
        mortgages (int): Nombre d'hypothèques.
        jail_visits (int): Entrées en prison totales.
        biggest_rent (int): Plus gros loyer unique.
        biggest_rent_property (str): Bien du plus gros loyer.
        free_parking_peak (int): Plus haute cagnotte observée.
        free_parking_collected (int): Total récupéré au Parc Gratuit.
        largest_trade_cash (int): Plus gros montant cash cumulé dans un échange.
        players (list[PlayerStatistics]): Compteurs individuels.
        properties (list[PropertyStatistics]): Rentabilité des biens.
        round_series (list[RoundStatisticsPoint]): Évolution financière par snapshot.

    Sortie:
        GameStatistics: Vue statistique destinée à l'interface ou aux simulations.
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
    jail_visits: int = 0
    biggest_rent: int = 0
    biggest_rent_property: str = "—"
    free_parking_peak: int = 0
    free_parking_collected: int = 0
    largest_trade_cash: int = 0
    players: list[PlayerStatistics] = field(default_factory=list)
    properties: list[PropertyStatistics] = field(default_factory=list)
    round_series: list[RoundStatisticsPoint] = field(default_factory=list)

    @classmethod
    def from_game(
        cls,
        game: "Game",
        include_round_series: bool = True,
    ) -> "GameStatistics":
        """Calcule statistiques historiques, rentabilité et séries temporelles.

        Entrées:
            game (Game): Partie courante ou terminée.
            include_round_series (bool): Construit les points de replay si ``True`` ;
                les simulations peuvent les désactiver pour éviter un travail inutile.

        Sortie:
            GameStatistics: Compteurs globaux, joueurs, biens et évolution par tour.
        """
        stats = cls()
        round_numbers: set[int] = set()
        player_rounds: dict[int, set[int]] = {}
        by_player = {
            player.player_id: PlayerStatistics(
                player_id=player.player_id,
                name=player.name,
                cash=player.cash,
                net_worth=game.player_net_worth(player),
                properties_owned=len(player.properties),
                bankrupt=player.bankrupt,
            )
            for player in game.players
        }
        property_stats: dict[int, PropertyStatistics] = {}
        for space in game.board.spaces:
            if hasattr(space, "owner"):
                property_stats[space.index] = PropertyStatistics(
                    property_index=space.index,
                    name=space.name,
                )

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
                if amount > stats.biggest_rent:
                    stats.biggest_rent = amount
                    index = event.data.get("property_index")
                    if index is not None and int(index) in property_stats:
                        stats.biggest_rent_property = property_stats[int(index)].name

                if player_stats is not None:
                    player_stats.rent_paid += amount
                    player_stats.biggest_rent_paid = max(
                        player_stats.biggest_rent_paid,
                        amount,
                    )

                recipient_id = event.data.get("recipient_id")
                if recipient_id is not None and int(recipient_id) in by_player:
                    receiver = by_player[int(recipient_id)]
                    receiver.rent_received += amount
                    receiver.biggest_rent_received = max(
                        receiver.biggest_rent_received,
                        amount,
                    )

                property_index = event.data.get("property_index")
                if property_index is not None and int(property_index) in property_stats:
                    pstats = property_stats[int(property_index)]
                    pstats.rent_received += amount
                    pstats.rent_events += 1
                    pstats.biggest_rent = max(pstats.biggest_rent, amount)

            elif event.event_type == "trade":
                stats.trades += 1
                participant_ids = {
                    int(item)
                    for item in event.data.get("participant_ids", [])
                }
                for player_id in participant_ids:
                    if player_id in by_player:
                        by_player[player_id].trades += 1
                trade_cash = int(event.data.get("cash_from_initiator", 0)) + int(
                    event.data.get("cash_from_recipient", 0)
                )
                stats.largest_trade_cash = max(
                    stats.largest_trade_cash,
                    trade_cash,
                )

            elif event.event_type == "bankruptcy":
                stats.bankruptcies += 1

            elif event.event_type == "jail_enter":
                stats.jail_visits += 1
                if player_stats is not None:
                    player_stats.jail_visits += 1

            elif event.event_type == "free_parking_pot_add":
                stats.free_parking_peak = max(
                    stats.free_parking_peak,
                    int(event.data.get("pot", 0)),
                )

            elif event.event_type == "free_parking_pot_collect":
                stats.free_parking_collected += int(event.data.get("amount", 0))

        stats.turns = len(round_numbers)
        for player_id, rounds in player_rounds.items():
            if player_id in by_player:
                by_player[player_id].turns = len(rounds)

        stats.players = [by_player[player.player_id] for player in game.players]
        stats.properties = sorted(
            property_stats.values(),
            key=lambda item: (
                item.rent_received,
                item.biggest_rent,
                item.rent_events,
            ),
            reverse=True,
        )

        if include_round_series:
            snapshots = game.replay.display_snapshots(game)
            stats.round_series = [
                RoundStatisticsPoint(
                    round_number=snapshot.round_number,
                    label=snapshot.label,
                    cash_by_player={
                        player.player_id: player.cash
                        for player in snapshot.players
                    },
                    worth_by_player={
                        player.player_id: player.net_worth
                        for player in snapshot.players
                    },
                    properties_by_player={
                        player.player_id: player.properties_count
                        for player in snapshot.players
                    },
                    free_parking_pot=snapshot.free_parking_pot,
                )
                for snapshot in snapshots
            ]
            if snapshots:
                stats.free_parking_peak = max(
                    stats.free_parking_peak,
                    max(snapshot.free_parking_pot for snapshot in snapshots),
                )
        return stats

    @property
    def most_profitable_property(self) -> PropertyStatistics | None:
        """Retourne le bien ayant produit le plus de loyers cumulés.

        Entrées:
            Aucune.

        Sortie:
            PropertyStatistics | None: Premier bien rentable, sinon ``None``.
        """
        return next(
            (item for item in self.properties if item.rent_received > 0),
            None,
        )

    def summary_lines(self) -> list[str]:
        """Produit des indicateurs globaux compacts pour l'interface.

        Entrées:
            Aucune.

        Sortie:
            list[str]: Indicateurs globaux sous forme de textes courts.
        """
        return [
            f"Tours : {self.turns}",
            f"Cartes : {self.cards_drawn}",
            f"Achats : {self.purchases}",
            f"Constructions : {self.buildings_built}",
            f"Échanges : {self.trades}",
            f"Loyers : {self.rent_transferred} $",
            f"Prison : {self.jail_visits}",
            f"Faillites : {self.bankruptcies}",
        ]
