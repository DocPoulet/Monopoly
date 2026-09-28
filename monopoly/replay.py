"""Snapshots immuables utilisés pour le replay en lecture seule d'une partie."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from .properties import OwnableSpace, Property

if TYPE_CHECKING:
    from .game import Game


@dataclass(frozen=True)
class ReplayPlayerState:
    """Capture l'état pertinent d'un joueur pour un instant du replay.

    Entrées:
        player_id (int): Identifiant stable du joueur.
        name (str): Nom affiché.
        cash (int): Liquidités au moment du snapshot.
        position (int): Case occupée.
        bankrupt (bool): État de faillite.
        in_jail (bool): Présence en prison.
        properties_count (int): Nombre de biens possédés.
        net_worth (int): Patrimoine estimé par le moteur.

    Sortie:
        ReplayPlayerState: État individuel immuable et sérialisable.
    """

    player_id: int
    name: str
    cash: int
    position: int
    bankrupt: bool
    in_jail: bool
    properties_count: int
    net_worth: int

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'état du joueur.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Données JSON du joueur.
        """
        return {
            "player_id": self.player_id,
            "name": self.name,
            "cash": self.cash,
            "position": self.position,
            "bankrupt": self.bankrupt,
            "in_jail": self.in_jail,
            "properties_count": self.properties_count,
            "net_worth": self.net_worth,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplayPlayerState":
        """Reconstruit un état joueur depuis du JSON.

        Entrées:
            data (dict[str, Any]): Valeurs sérialisées.

        Sortie:
            ReplayPlayerState: État restauré.
        """
        return cls(
            player_id=int(data["player_id"]),
            name=str(data.get("name", "?")),
            cash=int(data.get("cash", 0)),
            position=int(data.get("position", 0)),
            bankrupt=bool(data.get("bankrupt", False)),
            in_jail=bool(data.get("in_jail", False)),
            properties_count=int(data.get("properties_count", 0)),
            net_worth=int(data.get("net_worth", 0)),
        )


@dataclass(frozen=True)
class ReplayPropertyState:
    """Capture propriété, hypothèque et bâtiments d'un bien achetable.

    Entrées:
        index (int): Position du bien sur le plateau.
        name (str): Nom du bien au moment du snapshot.
        owner_id (int | None): Propriétaire ou ``None``.
        mortgaged (bool): État hypothécaire.
        houses (int): Nombre de maisons.
        hotel (bool): Présence d'un hôtel.

    Sortie:
        ReplayPropertyState: État immuable du bien.
    """

    index: int
    name: str
    owner_id: int | None
    mortgaged: bool
    houses: int = 0
    hotel: bool = False

    @property
    def development_label(self) -> str:
        """Produit le libellé compact du développement.

        Entrées:
            Aucune.

        Sortie:
            str: Hôtel, nombre de maisons, hypothèque ou chaîne vide.
        """
        if self.hotel:
            return "Hôtel"
        if self.houses:
            return f"{self.houses} maison(s)"
        if self.mortgaged:
            return "Hypothéqué"
        return ""

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'état du bien.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Données JSON du bien.
        """
        return {
            "index": self.index,
            "name": self.name,
            "owner_id": self.owner_id,
            "mortgaged": self.mortgaged,
            "houses": self.houses,
            "hotel": self.hotel,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplayPropertyState":
        """Reconstruit un état de bien depuis du JSON.

        Entrées:
            data (dict[str, Any]): Valeurs sérialisées.

        Sortie:
            ReplayPropertyState: État restauré.
        """
        owner = data.get("owner_id")
        return cls(
            index=int(data["index"]),
            name=str(data.get("name", "?")),
            owner_id=None if owner is None else int(owner),
            mortgaged=bool(data.get("mortgaged", False)),
            houses=int(data.get("houses", 0)),
            hotel=bool(data.get("hotel", False)),
        )


@dataclass(frozen=True)
class ReplaySnapshot:
    """Capture complète en lecture seule d'un état de partie.

    Entrées:
        round_number (int): Tour de table associé ; zéro représente le départ.
        label (str): Libellé visible dans l'interface.
        event_sequence (int): Dernier événement inclus dans l'état.
        current_player_id (int | None): Joueur qui agirait ensuite.
        free_parking_pot (int): Cagnotte au moment du snapshot.
        houses_available (int | None): Maisons restantes, ``None`` pour illimité.
        hotels_available (int | None): Hôtels restants, ``None`` pour illimité.
        players (tuple[ReplayPlayerState, ...]): États individuels.
        properties (tuple[ReplayPropertyState, ...]): États des biens achetables.

    Sortie:
        ReplaySnapshot: Image immuable et sérialisable de la partie.
    """

    round_number: int
    label: str
    event_sequence: int
    current_player_id: int | None
    free_parking_pot: int
    houses_available: int | None
    hotels_available: int | None
    players: tuple[ReplayPlayerState, ...] = field(default_factory=tuple)
    properties: tuple[ReplayPropertyState, ...] = field(default_factory=tuple)

    @classmethod
    def from_game(
        cls,
        game: "Game",
        round_number: int,
        label: str,
    ) -> "ReplaySnapshot":
        """Capture l'état courant sans modifier la partie.

        Entrées:
            game (Game): Partie source.
            round_number (int): Tour de table à associer au snapshot.
            label (str): Libellé visible.

        Sortie:
            ReplaySnapshot: Copie immuable des données utiles au replay.
        """
        last_sequence = max(
            (event.sequence for event in game.history.events),
            default=0,
        )
        player_states = tuple(
            ReplayPlayerState(
                player_id=player.player_id,
                name=player.name,
                cash=player.cash,
                position=player.position,
                bankrupt=player.bankrupt,
                in_jail=player.in_jail,
                properties_count=len(player.properties),
                net_worth=game.player_net_worth(player),
            )
            for player in game.players
        )
        property_states: list[ReplayPropertyState] = []
        for space in game.board.spaces:
            if not isinstance(space, OwnableSpace):
                continue
            property_states.append(
                ReplayPropertyState(
                    index=space.index,
                    name=space.name,
                    owner_id=None if space.owner is None else space.owner.player_id,
                    mortgaged=space.mortgaged,
                    houses=space.houses if isinstance(space, Property) else 0,
                    hotel=space.hotel if isinstance(space, Property) else False,
                )
            )

        current_id = None
        if game.players and not game.is_over:
            current_id = game.current_player.player_id

        return cls(
            round_number=max(0, int(round_number)),
            label=label,
            event_sequence=last_sequence,
            current_player_id=current_id,
            free_parking_pot=game.free_parking_pot,
            houses_available=game.bank.houses_available,
            hotels_available=game.bank.hotels_available,
            players=player_states,
            properties=tuple(property_states),
        )

    def state_signature(self) -> tuple[Any, ...]:
        """Construit une signature comparable ignorant le libellé du snapshot.

        Entrées:
            Aucune.

        Sortie:
            tuple[Any, ...]: Valeurs suffisantes pour détecter un état identique.
        """
        return (
            self.current_player_id,
            self.free_parking_pot,
            self.houses_available,
            self.hotels_available,
            self.players,
            self.properties,
        )

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le snapshot pour les sauvegardes.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Structure JSON du snapshot.
        """
        return {
            "round_number": self.round_number,
            "label": self.label,
            "event_sequence": self.event_sequence,
            "current_player_id": self.current_player_id,
            "free_parking_pot": self.free_parking_pot,
            "houses_available": self.houses_available,
            "hotels_available": self.hotels_available,
            "players": [player.to_dict() for player in self.players],
            "properties": [space.to_dict() for space in self.properties],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplaySnapshot":
        """Reconstruit un snapshot depuis une sauvegarde.

        Entrées:
            data (dict[str, Any]): Structure sérialisée.

        Sortie:
            ReplaySnapshot: Snapshot restauré.
        """
        current = data.get("current_player_id")
        houses = data.get("houses_available")
        hotels = data.get("hotels_available")
        return cls(
            round_number=int(data.get("round_number", 0)),
            label=str(data.get("label", "Snapshot")),
            event_sequence=int(data.get("event_sequence", 0)),
            current_player_id=None if current is None else int(current),
            free_parking_pot=int(data.get("free_parking_pot", 0)),
            houses_available=None if houses is None else int(houses),
            hotels_available=None if hotels is None else int(hotels),
            players=tuple(
                ReplayPlayerState.from_dict(dict(item))
                for item in data.get("players", [])
            ),
            properties=tuple(
                ReplayPropertyState.from_dict(dict(item))
                for item in data.get("properties", [])
            ),
        )


class ReplayTimeline:
    """Conserve les snapshots persistants de fin de tour de table.

    Entrées:
        snapshots (list[ReplaySnapshot] | None): Snapshots déjà connus.

    Sortie:
        ReplayTimeline: Timeline prête à capturer de nouveaux tours.
    """

    def __init__(self, snapshots: list[ReplaySnapshot] | None = None) -> None:
        """Initialise la timeline dans l'ordre fourni.

        Entrées:
            snapshots (list[ReplaySnapshot] | None): États persistés facultatifs.

        Sortie:
            None: Les snapshots sont copiés.
        """
        self.snapshots = list(snapshots or [])

    def capture(
        self,
        game: "Game",
        round_number: int,
        label: str | None = None,
    ) -> ReplaySnapshot:
        """Ajoute ou remplace le snapshot persistant d'un tour de table.

        Entrées:
            game (Game): Partie à capturer.
            round_number (int): Tour associé.
            label (str | None): Libellé facultatif.

        Sortie:
            ReplaySnapshot: Snapshot effectivement stocké.
        """
        snapshot = ReplaySnapshot.from_game(
            game,
            round_number,
            label or ("Début de partie" if round_number == 0 else f"Fin du tour {round_number}"),
        )
        self.snapshots = [
            item for item in self.snapshots
            if item.round_number != snapshot.round_number
        ]
        self.snapshots.append(snapshot)
        self.snapshots.sort(key=lambda item: (item.round_number, item.event_sequence))
        return snapshot

    def display_snapshots(self, game: "Game") -> list[ReplaySnapshot]:
        """Retourne les snapshots persistés complétés par l'état courant si nécessaire.

        Entrées:
            game (Game): Partie courante utilisée pour l'aperçu vivant.

        Sortie:
            list[ReplaySnapshot]: États chronologiques destinés à l'interface.
        """
        result = list(self.snapshots)
        current_round = game.turn_number
        label = (
            f"État final — tour {current_round}"
            if game.is_over
            else f"Tour {game.upcoming_turn_number} — état actuel"
        )
        current = ReplaySnapshot.from_game(game, current_round, label)
        if not result or result[-1].state_signature() != current.state_signature():
            result.append(current)
        elif result:
            result[-1] = ReplaySnapshot(
                round_number=result[-1].round_number,
                label=result[-1].label,
                event_sequence=current.event_sequence,
                current_player_id=result[-1].current_player_id,
                free_parking_pot=result[-1].free_parking_pot,
                houses_available=result[-1].houses_available,
                hotels_available=result[-1].hotels_available,
                players=result[-1].players,
                properties=result[-1].properties,
            )
        return result

    def to_dict(self) -> dict[str, Any]:
        """Sérialise les snapshots persistants.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Timeline JSON.
        """
        return {"snapshots": [snapshot.to_dict() for snapshot in self.snapshots]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplayTimeline":
        """Reconstruit une timeline depuis une sauvegarde.

        Entrées:
            data (dict[str, Any]): Structure JSON éventuellement vide.

        Sortie:
            ReplayTimeline: Timeline restaurée.
        """
        return cls(
            [
                ReplaySnapshot.from_dict(dict(item))
                for item in data.get("snapshots", [])
            ]
        )
