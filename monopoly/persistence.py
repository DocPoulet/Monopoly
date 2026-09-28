"""Sauvegarde et chargement JSON d'une partie complète de Monopoly."""

from __future__ import annotations

import json
from datetime import datetime
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from .cards import (
    Card,
    CardDeck,
    GetOutOfJailCard,
    GoToJailCard,
    MoneyCard,
    MoveBackCard,
    MoveToCard,
    NearestRailroadCard,
    NearestUtilityCard,
    PerPlayerCard,
    RepairsCard,
)
from .game import Game
from .history import GameHistory
from .replay import ReplayTimeline
from .options import GameOptions
from .board_config import BoardConfig
from .properties import OwnableSpace, Property


SAVE_FORMAT = "monopoly-poo"
SAVE_VERSION = 1

_CARD_TYPES: dict[str, type[Card]] = {
    cls.__name__: cls
    for cls in (
        MoneyCard,
        MoveToCard,
        MoveBackCard,
        GoToJailCard,
        GetOutOfJailCard,
        NearestRailroadCard,
        NearestUtilityCard,
        RepairsCard,
        PerPlayerCard,
    )
}


class SaveGameError(ValueError):
    """Signale une sauvegarde absente, corrompue ou incompatible.

    Entrées:
        message (str): Explication destinée à l'appelant.

    Sortie:
        SaveGameError: Exception spécialisée de persistance.
    """


def _card_to_dict(card: Card) -> dict[str, Any]:
    """Sérialise une carte concrète avec ses champs de dataclass.

    Entrées:
        card (Card): Carte Chance ou Caisse de communauté.

    Sortie:
        dict[str, Any]: Type de carte et valeurs nécessaires à sa reconstruction.

    Lève:
        SaveGameError: Si une carte non dataclass ou inconnue est rencontrée.
    """
    if not is_dataclass(card):
        raise SaveGameError(f"Carte non sérialisable : {type(card).__name__}.")

    card_type = type(card).__name__
    if card_type not in _CARD_TYPES:
        raise SaveGameError(f"Type de carte inconnu : {card_type}.")

    return {
        "type": card_type,
        "fields": {
            item.name: getattr(card, item.name)
            for item in fields(card)
        },
    }


def _card_from_dict(data: dict[str, Any]) -> Card:
    """Reconstruit une carte depuis son type et ses champs.

    Entrées:
        data (dict[str, Any]): Carte sérialisée.

    Sortie:
        Card: Nouvelle instance concrète équivalente.

    Lève:
        SaveGameError: Si le type de carte n'est pas reconnu.
    """
    card_type = str(data.get("type", ""))
    cls = _CARD_TYPES.get(card_type)
    if cls is None:
        raise SaveGameError(f"Type de carte non pris en charge : {card_type}.")
    return cls(**dict(data.get("fields", {})))


def _tuple_tree(value: Any) -> Any:
    """Convertit récursivement les listes JSON en tuples pour ``random.setstate``.

    Entrées:
        value (Any): Valeur issue du JSON.

    Sortie:
        Any: Même structure avec toutes les listes converties en tuples.
    """
    if isinstance(value, list):
        return tuple(_tuple_tree(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuple_tree(item) for key, item in value.items()}
    return value


def game_to_dict(game: Game) -> dict[str, Any]:
    """Convertit tout l'état persistant d'une partie en dictionnaire JSON.

    Entrées:
        game (Game): Partie à sauvegarder.

    Sortie:
        dict[str, Any]: État complet du moteur, des paquets et de l'historique.
    """
    spaces: list[dict[str, Any]] = []
    for space in game.board.spaces:
        if not isinstance(space, OwnableSpace):
            continue

        item: dict[str, Any] = {
            "index": space.index,
            "owner_id": None if space.owner is None else space.owner.player_id,
            "mortgaged": space.mortgaged,
        }
        if isinstance(space, Property):
            item["houses"] = space.houses
            item["hotel"] = space.hotel
        spaces.append(item)

    players = [
        {
            "player_id": player.player_id,
            "name": player.name,
            "cash": player.cash,
            "position": player.position,
            "bankrupt": player.bankrupt,
            "in_jail": player.in_jail,
            "jail_turns": player.jail_turns,
            "held_cards": [_card_to_dict(card) for card in player.held_cards],
        }
        for player in game.players
    ]

    return {
        "format": SAVE_FORMAT,
        "version": SAVE_VERSION,
        "metadata": {
            "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "players": [player.name for player in game.players],
            "turn_number": game.upcoming_turn_number,
            "active_players": len(game.active_players),
            "winner": None if game.winner is None else game.winner.name,
            "board_name": game.board_config.name,
        },
        "game": {
            "options": game.options.to_dict(),
            "board_config": game.board_config.to_dict(),
            "players": players,
            "spaces": spaces,
            "bank": {
                "house_limit": game.bank.house_limit,
                "hotel_limit": game.bank.hotel_limit,
                "houses_available": game.bank.houses_available,
                "hotels_available": game.bank.hotels_available,
            },
            "free_parking_pot": game.free_parking_pot,
            "pending_rent_claim": (
                None
                if game.pending_rent_claim is None
                else {
                    "payer_id": game.pending_rent_claim.payer.player_id,
                    "recipient_id": game.pending_rent_claim.recipient.player_id,
                    "amount": game.pending_rent_claim.amount,
                    "property_index": game.pending_rent_claim.property_index,
                }
            ),
            "current_player_index": game.current_player_index,
            "turn_number": game.turn_number,
            "completed_rounds": game.completed_rounds,
            "new_round_pending": game._new_round_pending,
            "turn_semantics": "round",
            "consecutive_doubles": game.consecutive_doubles,
            "pending_bank_auctions": [
                space.index for space in game.pending_bank_auctions
            ],
            "chance_deck": [
                _card_to_dict(card) for card in game.chance_deck.cards
            ],
            "community_chest_deck": [
                _card_to_dict(card) for card in game.community_chest_deck.cards
            ],
            "random_state": game.random.getstate(),
            "history": game.history.to_dict(),
            "replay": game.replay.to_dict(),
        },
    }


def game_from_dict(data: dict[str, Any]) -> Game:
    """Reconstruit une partie jouable depuis une sauvegarde validée.

    Entrées:
        data (dict[str, Any]): Structure JSON de sauvegarde.

    Sortie:
        Game: Nouvelle instance reproduisant l'état sauvegardé.

    Lève:
        SaveGameError: Si le format ou les données essentielles sont invalides.
    """
    if data.get("format") != SAVE_FORMAT:
        raise SaveGameError("Ce fichier n'est pas une sauvegarde Monopoly POO.")
    if int(data.get("version", -1)) != SAVE_VERSION:
        raise SaveGameError(
            "Version de sauvegarde incompatible avec cette version du jeu."
        )

    state = data.get("game")
    if not isinstance(state, dict):
        raise SaveGameError("État de partie manquant.")

    player_data = state.get("players")
    if not isinstance(player_data, list) or len(player_data) < 2:
        raise SaveGameError("La sauvegarde doit contenir au moins deux joueurs.")

    names = [str(item["name"]) for item in player_data]
    board_data = state.get("board_config")
    try:
        board_config = (
            BoardConfig.from_dict(dict(board_data))
            if isinstance(board_data, dict)
            else BoardConfig.standard()
        )
    except (TypeError, ValueError, KeyError) as error:
        raise SaveGameError("Définition de plateau invalide dans la sauvegarde.") from error

    game = Game(
        names,
        seed=0,
        options=GameOptions.from_dict(state.get("options")),
        board_config=board_config,
    )

    if len(game.players) != len(player_data):
        raise SaveGameError("Nombre de joueurs incohérent.")

    for player, item in zip(game.players, player_data):
        player.cash = int(item["cash"])
        player.position = int(item["position"])
        player.bankrupt = bool(item["bankrupt"])
        player.in_jail = bool(item["in_jail"])
        player.jail_turns = int(item["jail_turns"])
        player.properties.clear()
        player.held_cards = [
            _card_from_dict(card)
            for card in item.get("held_cards", [])
        ]

    by_index = {
        space.index: space
        for space in game.board.spaces
        if isinstance(space, OwnableSpace)
    }

    for space in by_index.values():
        space.reset_ownership()

    for item in state.get("spaces", []):
        index = int(item["index"])
        space = by_index.get(index)
        if space is None:
            raise SaveGameError(f"Case achetable inconnue dans la sauvegarde : {index}.")

        owner_id = item.get("owner_id")
        if owner_id is not None:
            owner_index = int(owner_id)
            if owner_index < 0 or owner_index >= len(game.players):
                raise SaveGameError("Identifiant de propriétaire invalide.")
            space.assign_to(game.players[owner_index])

        space.mortgaged = bool(item.get("mortgaged", False))

        if isinstance(space, Property):
            houses = int(item.get("houses", 0))
            hotel = bool(item.get("hotel", False))
            if houses < 0 or houses > 4:
                raise SaveGameError("Nombre de maisons invalide.")
            if hotel and houses:
                raise SaveGameError("Un terrain ne peut pas avoir hôtel et maisons.")
            space.houses = houses
            space.hotel = hotel

    bank = dict(state.get("bank", {}))
    game.bank.houses_available = int(
        bank.get(
            "houses_available",
            game.bank.house_limit if game.bank.house_limit > 0 else 0,
        )
    )
    game.bank.hotels_available = int(
        bank.get(
            "hotels_available",
            game.bank.hotel_limit if game.bank.hotel_limit > 0 else 0,
        )
    )

    if game.bank.house_limit > 0 and not (
        0 <= game.bank.houses_available <= game.bank.house_limit
    ):
        raise SaveGameError("Stock de maisons invalide.")
    if game.bank.hotel_limit > 0 and not (
        0 <= game.bank.hotels_available <= game.bank.hotel_limit
    ):
        raise SaveGameError("Stock d'hôtels invalide.")

    game.free_parking_pot = int(state.get("free_parking_pot", 0))
    if game.free_parking_pot < 0:
        raise SaveGameError("Cagnotte Parc Gratuit invalide.")

    game.current_player_index = int(state.get("current_player_index", 0))
    if not 0 <= game.current_player_index < len(game.players):
        raise SaveGameError("Index du joueur courant invalide.")

    saved_turn_number = int(state.get("turn_number", 1))
    game.turn_number = max(1, saved_turn_number)
    game.completed_rounds = int(state.get("completed_rounds", 0))
    game._new_round_pending = bool(state.get("new_round_pending", False))
    game.consecutive_doubles = int(state.get("consecutive_doubles", 0))

    game.chance_deck = CardDeck(
        "chance",
        [_card_from_dict(card) for card in state.get("chance_deck", [])],
        shuffle=False,
    )
    game.community_chest_deck = CardDeck(
        "community_chest",
        [
            _card_from_dict(card)
            for card in state.get("community_chest_deck", [])
        ],
        shuffle=False,
    )

    if not len(game.chance_deck) and not any(
        isinstance(card, GetOutOfJailCard) and card.deck_name == "chance"
        for player in game.players
        for card in player.held_cards
    ):
        raise SaveGameError("Paquet Chance vide.")
    if not len(game.community_chest_deck) and not any(
        isinstance(card, GetOutOfJailCard) and card.deck_name == "community_chest"
        for player in game.players
        for card in player.held_cards
    ):
        raise SaveGameError("Paquet Caisse de communauté vide.")

    game.pending_bank_auctions = []
    for index in state.get("pending_bank_auctions", []):
        space = by_index.get(int(index))
        if space is None:
            raise SaveGameError("Bien d'enchère bancaire inconnu.")
        game.pending_bank_auctions.append(space)

    try:
        game.random.setstate(_tuple_tree(state["random_state"]))
    except (KeyError, TypeError, ValueError) as error:
        raise SaveGameError("État aléatoire invalide.") from error

    game.history = GameHistory.from_dict(dict(state.get("history", {})))
    replay_data = state.get("replay")
    if isinstance(replay_data, dict):
        game.replay = ReplayTimeline.from_dict(dict(replay_data))
    else:
        game.replay = ReplayTimeline()
        game.replay.capture(game, 0, "État chargé sans historique de replay")

    if state.get("turn_semantics") != "round":
        turn_events = [
            event for event in game.history.events
            if event.event_type == "turn" and event.player_id is not None
        ]
        legacy_to_round: dict[int, int] = {}
        round_number = 1
        previous_player_id: int | None = None
        for event in turn_events:
            player_id = int(event.player_id)
            if previous_player_id is not None and player_id < previous_player_id:
                round_number += 1
            legacy_to_round[event.turn_number] = round_number
            previous_player_id = player_id

        for event in game.history.events:
            if event.turn_number in legacy_to_round:
                event.turn_number = legacy_to_round[event.turn_number]

        if turn_events:
            last_player_id = int(turn_events[-1].player_id)
            pending_wrap = game.current_player_index < last_player_id
            game.turn_number = round_number
            game.completed_rounds = max(0, round_number - 1)
            game._new_round_pending = pending_wrap
            if pending_wrap:
                game.completed_rounds += 1
        else:
            game.turn_number = max(1, saved_turn_number)
            game.completed_rounds = max(0, game.turn_number - 1)
            game._new_round_pending = False

    pending_rent = state.get("pending_rent_claim")
    game.pending_rent_claim = None
    if isinstance(pending_rent, dict):
        try:
            payer = game.players[int(pending_rent["payer_id"])]
            recipient = game.players[int(pending_rent["recipient_id"])]
            amount = int(pending_rent["amount"])
            property_index = int(pending_rent["property_index"])
        except (KeyError, ValueError, IndexError) as error:
            raise SaveGameError("Loyer manuel en attente invalide.") from error
        from .game import PendingRentClaim
        game.pending_rent_claim = PendingRentClaim(
            payer=payer,
            recipient=recipient,
            amount=amount,
            property_index=property_index,
        )

    game.drawn_cards_this_turn = []
    game.financial_events_this_turn = []
    game._turn_passed_go = False
    game.mortgage_selector = None

    return game


def read_save_metadata(path: str | Path) -> dict[str, Any]:
    """Lit uniquement les métadonnées utiles à l'écran de chargement.

    Entrées:
        path (str | Path): Fichier de sauvegarde JSON.

    Sortie:
        dict[str, Any]: Nom de fichier, date, joueurs, tour et état synthétique.

    Lève:
        SaveGameError: Si le fichier ne correspond pas au format attendu.
    """
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SaveGameError("Sauvegarde illisible.") from error

    if not isinstance(data, dict) or data.get("format") != SAVE_FORMAT:
        raise SaveGameError("Format de sauvegarde invalide.")

    metadata = dict(data.get("metadata", {}))
    state = dict(data.get("game", {}))
    players = metadata.get("players")
    if not isinstance(players, list):
        players = [
            str(item.get("name", "?"))
            for item in state.get("players", [])
        ]

    return {
        "path": str(source),
        "filename": source.name,
        "saved_at": str(metadata.get("saved_at", "")),
        "players": [str(name) for name in players],
        "turn_number": int(metadata.get("turn_number", state.get("turn_number", 0))),
        "active_players": int(metadata.get("active_players", 0)),
        "winner": metadata.get("winner"),
        "board_name": str(
            metadata.get(
                "board_name",
                dict(state.get("board_config", {})).get("name", "Plateau standard"),
            )
        ),
    }


def list_save_metadata(directory: str | Path) -> list[dict[str, Any]]:
    """Liste les sauvegardes JSON valides d'un dossier, les plus récentes d'abord.

    Entrées:
        directory (str | Path): Dossier des sauvegardes.

    Sortie:
        list[dict[str, Any]]: Métadonnées des fichiers reconnus ; les fichiers invalides sont ignorés.
    """
    folder = Path(directory)
    if not folder.exists():
        return []

    saves: list[dict[str, Any]] = []
    for path in folder.glob("*.json"):
        try:
            saves.append(read_save_metadata(path))
        except SaveGameError:
            continue
    return sorted(
        saves,
        key=lambda item: (item.get("saved_at", ""), item.get("filename", "")),
        reverse=True,
    )


def save_game(game: Game, path: str | Path) -> Path:
    """Écrit une sauvegarde JSON complète sur disque.

    Entrées:
        game (Game): Partie à sérialiser.
        path (str | Path): Fichier de destination.

    Sortie:
        Path: Chemin final écrit.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            game_to_dict(game),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return destination


def load_game(path: str | Path) -> Game:
    """Charge un fichier JSON et reconstruit une partie.

    Entrées:
        path (str | Path): Fichier de sauvegarde.

    Sortie:
        Game: Partie restaurée.

    Lève:
        SaveGameError: Si le JSON est illisible ou incompatible.
    """
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SaveGameError("Impossible de lire cette sauvegarde.") from error

    if not isinstance(data, dict):
        raise SaveGameError("Structure de sauvegarde invalide.")
    return game_from_dict(data)
