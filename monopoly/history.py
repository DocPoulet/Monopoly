"""Historique structuré des événements d'une partie."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import Player


@dataclass
class GameEvent:
    """Représente un événement structuré enregistré pendant une partie.

    Entrées:
        sequence (int): Numéro croissant garantissant l'ordre des événements.
        turn_number (int): Numéro global du tour au moment de l'événement.
        event_type (str): Catégorie stable utilisée par les statistiques.
        message (str): Description lisible par un humain.
        player_id (int | None): Joueur principal concerné, lorsque pertinent.
        data (dict[str, Any]): Données complémentaires sérialisables en JSON.

    Sortie:
        GameEvent: Élément unitaire de l'historique de partie.
    """

    sequence: int
    turn_number: int
    event_type: str
    message: str
    player_id: int | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'événement en dictionnaire sérialisable.

        Entrées:
            Aucune autre que l'instance.

        Sortie:
            dict[str, Any]: Représentation adaptée au JSON de sauvegarde.
        """
        return {
            "sequence": self.sequence,
            "turn_number": self.turn_number,
            "event_type": self.event_type,
            "message": self.message,
            "player_id": self.player_id,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameEvent":
        """Reconstruit un événement depuis une sauvegarde.

        Entrées:
            data (dict[str, Any]): Données sérialisées de l'événement.

        Sortie:
            GameEvent: Événement restauré.
        """
        return cls(
            sequence=int(data["sequence"]),
            turn_number=int(data.get("turn_number", 0)),
            event_type=str(data["event_type"]),
            message=str(data.get("message", "")),
            player_id=(
                None
                if data.get("player_id") is None
                else int(data["player_id"])
            ),
            data=dict(data.get("data", {})),
        )


class GameHistory:
    """Conserve l'ordre complet des événements structurés d'une partie.

    Entrées:
        events (list[GameEvent] | None): Événements initiaux optionnels.

    Sortie:
        GameHistory: Journal structuré prêt à recevoir de nouveaux événements.
    """

    def __init__(self, events: list[GameEvent] | None = None) -> None:
        """Initialise l'historique et son prochain numéro de séquence.

        Entrées:
            events (list[GameEvent] | None): Événements à charger.

        Sortie:
            None: Les événements sont copiés dans l'ordre fourni.
        """
        self.events = list(events or [])
        self._next_sequence = (
            max((event.sequence for event in self.events), default=0) + 1
        )

    def add(
        self,
        turn_number: int,
        event_type: str,
        message: str,
        player: "Player | None" = None,
        **data: Any,
    ) -> GameEvent:
        """Ajoute un événement à l'historique.

        Entrées:
            turn_number (int): Numéro du tour courant.
            event_type (str): Catégorie structurée.
            message (str): Texte descriptif.
            player (Player | None): Joueur principal concerné.
            **data (Any): Données supplémentaires sérialisables.

        Sortie:
            GameEvent: Événement créé et ajouté à la fin de l'historique.
        """
        event = GameEvent(
            sequence=self._next_sequence,
            turn_number=turn_number,
            event_type=event_type,
            message=message.strip(),
            player_id=None if player is None else player.player_id,
            data=dict(data),
        )
        self._next_sequence += 1
        self.events.append(event)
        return event

    def recent(self, limit: int = 100) -> list[GameEvent]:
        """Retourne les derniers événements dans l'ordre chronologique.

        Entrées:
            limit (int): Nombre maximal d'événements souhaités.

        Sortie:
            list[GameEvent]: Sous-liste finale de l'historique.
        """
        if limit <= 0:
            return []
        return self.events[-limit:]

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'historique complet.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Structure JSON contenant tous les événements.
        """
        return {"events": [event.to_dict() for event in self.events]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameHistory":
        """Reconstruit un historique depuis une structure JSON.

        Entrées:
            data (dict[str, Any]): Structure issue de ``to_dict``.

        Sortie:
            GameHistory: Historique restauré avec séquence prête à continuer.
        """
        return cls(
            [
                GameEvent.from_dict(item)
                for item in data.get("events", [])
            ]
        )
