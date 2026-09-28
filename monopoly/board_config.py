"""Définit un plateau éditable et ses deux paquets de cartes personnalisables."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Any

from .board import Board
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
    create_chance_deck,
    create_community_chest_deck,
)
from .properties import OwnableSpace, Property, Railroad, Utility
from .spaces import (
    ChanceSpace,
    CommunityChestSpace,
    FreeParkingSpace,
    GoSpace,
    GoToJailSpace,
    JailSpace,
    Space,
    TaxSpace,
)


SPACE_TYPES = (
    "go",
    "property",
    "community_chest",
    "tax",
    "railroad",
    "chance",
    "jail",
    "utility",
    "free_parking",
    "go_to_jail",
)

CARD_TYPES = (
    "MoneyCard",
    "MoveToCard",
    "MoveBackCard",
    "GoToJailCard",
    "GetOutOfJailCard",
    "NearestRailroadCard",
    "NearestUtilityCard",
    "RepairsCard",
    "PerPlayerCard",
)


@dataclass
class SpaceConfig:
    """Décrit une case éditable du plateau.

    Entrées:
        index (int): Position fixe de la case, entre 0 et 39.
        space_type (str): Type structurel de la case.
        name (str): Nom visible.
        price (int): Prix pour les biens achetables.
        color_group (str): Groupe de couleur des terrains.
        base_rent (int): Loyer sans bâtiment.
        house_rents (tuple[int, int, int, int]): Loyers avec une à quatre maisons.
        hotel_rent (int): Loyer avec hôtel.
        house_cost (int): Prix d'une maison ou d'un hôtel.
        tax_amount (int): Montant payé sur une case Taxe.
        railroad_rents (tuple[int, int, int, int]): Loyers d'une gare selon le nombre possédé.
        utility_multipliers (tuple[int, int]): Multiplicateurs de dés d'une compagnie.

    Sortie:
        SpaceConfig: Description sérialisable d'une case.
    """

    index: int
    space_type: str
    name: str
    price: int = 0
    color_group: str = ""
    base_rent: int = 0
    house_rents: tuple[int, int, int, int] = (0, 0, 0, 0)
    hotel_rent: int = 0
    house_cost: int = 0
    tax_amount: int = 0
    railroad_rents: tuple[int, int, int, int] = (25, 50, 100, 200)
    utility_multipliers: tuple[int, int] = (4, 10)

    def validate(self) -> None:
        """Valide les données numériques et le type de la case.

        Entrées:
            Aucune.

        Sortie:
            None: La configuration reste inchangée si elle est valide.

        Lève:
            ValueError: Si un index, un type ou une valeur économique est invalide.
        """
        if not 0 <= self.index < Board.SIZE:
            raise ValueError("L'index d'une case doit être compris entre 0 et 39.")
        if self.space_type not in SPACE_TYPES:
            raise ValueError(f"Type de case inconnu : {self.space_type}.")
        if not self.name.strip():
            raise ValueError(f"La case {self.index} doit avoir un nom.")
        for value in (
            self.price,
            self.base_rent,
            self.hotel_rent,
            self.house_cost,
            self.tax_amount,
            *self.house_rents,
            *self.railroad_rents,
            *self.utility_multipliers,
        ):
            if value < 0:
                raise ValueError("Les valeurs économiques du plateau ne peuvent pas être négatives.")
        if len(self.house_rents) != 4:
            raise ValueError("Un terrain doit définir quatre loyers de maisons.")
        if len(self.railroad_rents) != 4:
            raise ValueError("Une gare doit définir quatre niveaux de loyer.")
        if len(self.utility_multipliers) != 2:
            raise ValueError("Une compagnie doit définir deux multiplicateurs.")
        if self.space_type == "property" and not self.color_group.strip():
            raise ValueError(f"Le terrain {self.index} doit appartenir à un groupe de couleur.")

    def to_dict(self) -> dict[str, Any]:
        """Sérialise une case en valeurs JSON primitives.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Dictionnaire complet de la case.
        """
        return {
            "index": self.index,
            "space_type": self.space_type,
            "name": self.name,
            "price": self.price,
            "color_group": self.color_group,
            "base_rent": self.base_rent,
            "house_rents": list(self.house_rents),
            "hotel_rent": self.hotel_rent,
            "house_cost": self.house_cost,
            "tax_amount": self.tax_amount,
            "railroad_rents": list(self.railroad_rents),
            "utility_multipliers": list(self.utility_multipliers),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpaceConfig":
        """Reconstruit une case depuis un dictionnaire JSON.

        Entrées:
            data (dict[str, Any]): Valeurs sérialisées d'une case.

        Sortie:
            SpaceConfig: Configuration validée.
        """
        rents = tuple(int(value) for value in data.get("house_rents", (0, 0, 0, 0)))
        railroad_rents = tuple(int(value) for value in data.get("railroad_rents", (25, 50, 100, 200)))
        utility_multipliers = tuple(int(value) for value in data.get("utility_multipliers", (4, 10)))
        if len(rents) != 4:
            raise ValueError("Un terrain doit définir exactement quatre loyers de maisons.")
        if len(railroad_rents) != 4:
            raise ValueError("Une gare doit définir quatre niveaux de loyer.")
        if len(utility_multipliers) != 2:
            raise ValueError("Une compagnie doit définir deux multiplicateurs.")
        result = cls(
            index=int(data["index"]),
            space_type=str(data["space_type"]),
            name=str(data["name"]),
            price=int(data.get("price", 0)),
            color_group=str(data.get("color_group", "")),
            base_rent=int(data.get("base_rent", 0)),
            house_rents=rents,  # type: ignore[arg-type]
            hotel_rent=int(data.get("hotel_rent", 0)),
            house_cost=int(data.get("house_cost", 0)),
            tax_amount=int(data.get("tax_amount", 0)),
            railroad_rents=railroad_rents,  # type: ignore[arg-type]
            utility_multipliers=utility_multipliers,  # type: ignore[arg-type]
        )
        result.validate()
        return result


@dataclass
class CardConfig:
    """Décrit une carte Chance ou Communauté éditable.

    Entrées:
        card_type (str): Classe concrète de carte à créer.
        text (str): Texte affiché lors de la pioche.
        amount (int): Montant pour MoneyCard ou PerPlayerCard.
        destination (int): Destination pour MoveToCard.
        collect_go (bool): Autorise le salaire de Départ pendant MoveToCard.
        steps (int): Nombre de cases reculées par MoveBackCard.
        house_cost (int): Coût par maison pour RepairsCard.
        hotel_cost (int): Coût par hôtel pour RepairsCard.

    Sortie:
        CardConfig: Carte portable pouvant être convertie en objet moteur.
    """

    card_type: str
    text: str
    amount: int = 0
    destination: int = 0
    collect_go: bool = True
    steps: int = 3
    house_cost: int = 0
    hotel_cost: int = 0

    def validate(self) -> None:
        """Vérifie le type et les paramètres essentiels de la carte.

        Entrées:
            Aucune.

        Sortie:
            None: La carte est utilisable par le moteur.

        Lève:
            ValueError: Si le type, la destination ou une valeur de réparation est invalide.
        """
        if self.card_type not in CARD_TYPES:
            raise ValueError(f"Type de carte inconnu : {self.card_type}.")
        if not self.text.strip():
            raise ValueError("Une carte doit contenir un texte.")
        if self.card_type == "MoveToCard" and not 0 <= self.destination < Board.SIZE:
            raise ValueError("La destination d'une carte doit être comprise entre 0 et 39.")
        if self.card_type == "MoveBackCard" and self.steps <= 0:
            raise ValueError("Le recul d'une carte doit être strictement positif.")
        if self.card_type == "RepairsCard" and (self.house_cost < 0 or self.hotel_cost < 0):
            raise ValueError("Les coûts de réparation ne peuvent pas être négatifs.")

    def to_dict(self) -> dict[str, Any]:
        """Sérialise la carte en valeurs JSON primitives.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Représentation complète de la carte.
        """
        return {
            "card_type": self.card_type,
            "text": self.text,
            "amount": self.amount,
            "destination": self.destination,
            "collect_go": self.collect_go,
            "steps": self.steps,
            "house_cost": self.house_cost,
            "hotel_cost": self.hotel_cost,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CardConfig":
        """Reconstruit une carte éditable depuis un dictionnaire JSON.

        Entrées:
            data (dict[str, Any]): Paramètres sérialisés.

        Sortie:
            CardConfig: Carte validée.
        """
        result = cls(
            card_type=str(data["card_type"]),
            text=str(data["text"]),
            amount=int(data.get("amount", 0)),
            destination=int(data.get("destination", 0)),
            collect_go=bool(data.get("collect_go", True)),
            steps=int(data.get("steps", 3)),
            house_cost=int(data.get("house_cost", 0)),
            hotel_cost=int(data.get("hotel_cost", 0)),
        )
        result.validate()
        return result

    @classmethod
    def from_card(cls, card: Card) -> "CardConfig":
        """Convertit une carte moteur existante en configuration éditable.

        Entrées:
            card (Card): Carte concrète d'un paquet.

        Sortie:
            CardConfig: Copie des paramètres utiles de la carte.
        """
        return cls(
            card_type=type(card).__name__,
            text=str(getattr(card, "text", type(card).__name__)),
            amount=int(getattr(card, "amount", 0)),
            destination=int(getattr(card, "destination", 0)),
            collect_go=bool(getattr(card, "collect_go", True)),
            steps=int(getattr(card, "steps", 3)),
            house_cost=int(getattr(card, "house_cost", 0)),
            hotel_cost=int(getattr(card, "hotel_cost", 0)),
        )

    def build_card(self, deck_name: str) -> Card:
        """Crée la carte moteur concrète correspondant à la configuration.

        Entrées:
            deck_name (str): ``chance`` ou ``community_chest`` pour les cartes conservables.

        Sortie:
            Card: Nouvelle carte indépendante prête à rejoindre un paquet.
        """
        self.validate()
        if self.card_type == "MoneyCard":
            return MoneyCard(self.text, self.amount)
        if self.card_type == "MoveToCard":
            return MoveToCard(self.text, self.destination, self.collect_go)
        if self.card_type == "MoveBackCard":
            return MoveBackCard(self.text, self.steps)
        if self.card_type == "GoToJailCard":
            return GoToJailCard(self.text)
        if self.card_type == "GetOutOfJailCard":
            return GetOutOfJailCard(self.text, deck_name)
        if self.card_type == "NearestRailroadCard":
            return NearestRailroadCard(self.text)
        if self.card_type == "NearestUtilityCard":
            return NearestUtilityCard(self.text)
        if self.card_type == "RepairsCard":
            return RepairsCard(self.text, self.house_cost, self.hotel_cost)
        if self.card_type == "PerPlayerCard":
            return PerPlayerCard(self.text, self.amount)
        raise ValueError(f"Type de carte non pris en charge : {self.card_type}.")


@dataclass(frozen=True)
class BoardValidationIssue:
    """Décrit une erreur ou un avertissement détecté dans un plateau.

    Entrées:
        severity (str): ``"error"`` ou ``"warning"``.
        location_type (str): ``"board"``, ``"space"``, ``"chance`` ou ``"community_chest"``.
        index (int | None): Index de case ou de carte lorsque pertinent.
        message (str): Explication lisible de l'anomalie.

    Sortie:
        BoardValidationIssue: Élément structuré utilisable par l'éditeur.
    """

    severity: str
    location_type: str
    index: int | None
    message: str

    @property
    def label(self) -> str:
        """Retourne le libellé français du niveau de validation.

        Entrées:
            Aucune.

        Sortie:
            str: ``Erreur`` ou ``Avertissement``.
        """
        return "Erreur" if self.severity == "error" else "Avertissement"


@dataclass
class BoardConfig:
    """Regroupe le contenu éditable du plateau et des deux paquets.

    Entrées:
        name (str): Nom descriptif du plateau.
        spaces (list[SpaceConfig]): Quarante cases dans l'ordre du plateau.
        chance_cards (list[CardConfig]): Cartes du paquet Chance.
        community_chest_cards (list[CardConfig]): Cartes du paquet Communauté.

    Sortie:
        BoardConfig: Définition indépendante de l'état d'une partie.
    """

    name: str = "Plateau standard"
    spaces: list[SpaceConfig] = field(default_factory=list)
    chance_cards: list[CardConfig] = field(default_factory=list)
    community_chest_cards: list[CardConfig] = field(default_factory=list)

    def validate(self) -> None:
        """Valide la structure fixe, les cases et les paquets de cartes.

        Entrées:
            Aucune.

        Sortie:
            None: La définition est cohérente avec le moteur.

        Lève:
            ValueError: Si le plateau n'a pas 40 cases, si les positions structurelles
                sont modifiées ou si un paquet est vide/invalide.
        """
        if len(self.spaces) != Board.SIZE:
            raise ValueError("Un plateau doit contenir exactement 40 cases.")
        if [space.index for space in self.spaces] != list(range(Board.SIZE)):
            raise ValueError("Les cases du plateau doivent être ordonnées de 0 à 39.")
        required = {0: "go", 10: "jail", 20: "free_parking", 30: "go_to_jail"}
        for index, expected in required.items():
            if self.spaces[index].space_type != expected:
                raise ValueError(f"La case {index} doit rester de type {expected}.")
        for space in self.spaces:
            space.validate()
        if not self.chance_cards or not self.community_chest_cards:
            raise ValueError("Les deux paquets doivent contenir au moins une carte.")
        for card in self.chance_cards + self.community_chest_cards:
            card.validate()
        all_cards = self.chance_cards + self.community_chest_cards
        if (
            any(card.card_type == "NearestRailroadCard" for card in all_cards)
            and not any(space.space_type == "railroad" for space in self.spaces)
        ):
            raise ValueError("Une carte 'prochaine gare' nécessite au moins une gare sur le plateau.")
        if (
            any(card.card_type == "NearestUtilityCard" for card in all_cards)
            and not any(space.space_type == "utility" for space in self.spaces)
        ):
            raise ValueError("Une carte 'prochaine compagnie' nécessite au moins une compagnie sur le plateau.")
        if any(space.space_type == "chance" for space in self.spaces) and not self.chance_cards:
            raise ValueError("Une case Chance nécessite un paquet Chance.")
        if any(space.space_type == "community_chest" for space in self.spaces) and not self.community_chest_cards:
            raise ValueError("Une case Communauté nécessite un paquet Communauté.")

    def validation_issues(self) -> list[BoardValidationIssue]:
        """Retourne toutes les erreurs et alertes sans interrompre au premier problème.

        Entrées:
            Aucune.

        Sortie:
            list[BoardValidationIssue]: Problèmes structurés triés dans l'ordre du plateau.
        """
        issues: list[BoardValidationIssue] = []

        if len(self.spaces) != Board.SIZE:
            issues.append(
                BoardValidationIssue(
                    "error",
                    "board",
                    None,
                    f"Le plateau contient {len(self.spaces)} cases au lieu de 40.",
                )
            )
            return issues

        expected_indices = list(range(Board.SIZE))
        actual_indices = [space.index for space in self.spaces]
        if actual_indices != expected_indices:
            issues.append(
                BoardValidationIssue(
                    "error",
                    "board",
                    None,
                    "Les index de cases doivent suivre exactement 0 à 39.",
                )
            )

        required = {0: "go", 10: "jail", 20: "free_parking", 30: "go_to_jail"}
        for index, expected in required.items():
            if index < len(self.spaces) and self.spaces[index].space_type != expected:
                issues.append(
                    BoardValidationIssue(
                        "error",
                        "space",
                        index,
                        f"La case {index} doit rester de type {expected}.",
                    )
                )

        names: dict[str, list[int]] = {}
        color_groups: dict[str, list[int]] = {}
        for position, space in enumerate(self.spaces):
            try:
                space.validate()
            except ValueError as error:
                issues.append(
                    BoardValidationIssue("error", "space", position, str(error))
                )
                continue

            if space.space_type in {"property", "railroad", "utility", "tax"}:
                names.setdefault(space.name.strip().casefold(), []).append(position)
            if space.space_type == "property":
                color_groups.setdefault(space.color_group.strip().casefold(), []).append(position)
                progression = [space.base_rent, *space.house_rents, space.hotel_rent]
                if any(right < left for left, right in zip(progression, progression[1:])):
                    issues.append(
                        BoardValidationIssue(
                            "warning",
                            "space",
                            position,
                            "Le barème de loyer diminue à un niveau de construction supérieur.",
                        )
                    )
                if space.price == 0:
                    issues.append(
                        BoardValidationIssue(
                            "warning",
                            "space",
                            position,
                            "Ce terrain est achetable gratuitement.",
                        )
                    )

        for duplicated, indexes in names.items():
            if duplicated and len(indexes) > 1:
                for index in indexes:
                    issues.append(
                        BoardValidationIssue(
                            "warning",
                            "space",
                            index,
                            "Ce nom de case est utilisé plusieurs fois sur le plateau.",
                        )
                    )

        for group, indexes in color_groups.items():
            if group and len(indexes) == 1:
                issues.append(
                    BoardValidationIssue(
                        "warning",
                        "space",
                        indexes[0],
                        "Ce groupe de couleur ne contient qu'un seul terrain.",
                    )
                )

        decks = (
            ("chance", self.chance_cards),
            ("community_chest", self.community_chest_cards),
        )
        for deck_name, cards in decks:
            if not cards:
                issues.append(
                    BoardValidationIssue(
                        "error",
                        deck_name,
                        None,
                        "Le paquet doit contenir au moins une carte.",
                    )
                )
                continue
            for index, card in enumerate(cards):
                try:
                    card.validate()
                except ValueError as error:
                    issues.append(
                        BoardValidationIssue("error", deck_name, index, str(error))
                    )

        all_cards = self.chance_cards + self.community_chest_cards
        if (
            any(card.card_type == "NearestRailroadCard" for card in all_cards)
            and not any(space.space_type == "railroad" for space in self.spaces)
        ):
            issues.append(
                BoardValidationIssue(
                    "error",
                    "board",
                    None,
                    "Une carte 'prochaine gare' nécessite au moins une gare.",
                )
            )
        if (
            any(card.card_type == "NearestUtilityCard" for card in all_cards)
            and not any(space.space_type == "utility" for space in self.spaces)
        ):
            issues.append(
                BoardValidationIssue(
                    "error",
                    "board",
                    None,
                    "Une carte 'prochaine compagnie' nécessite au moins une compagnie.",
                )
            )
        if not any(space.space_type == "railroad" for space in self.spaces):
            issues.append(
                BoardValidationIssue(
                    "warning",
                    "board",
                    None,
                    "Le plateau ne contient aucune gare.",
                )
            )
        if not any(space.space_type == "utility" for space in self.spaces):
            issues.append(
                BoardValidationIssue(
                    "warning",
                    "board",
                    None,
                    "Le plateau ne contient aucune compagnie.",
                )
            )
        return issues

    def duplicate_space(self, source_index: int, target_index: int) -> None:
        """Copie le contenu d'une case vers une autre position non structurelle.

        Entrées:
            source_index (int): Index de la case modèle.
            target_index (int): Position qui recevra la copie.

        Sortie:
            None: La case cible garde son index mais reçoit les autres paramètres.

        Lève:
            ValueError: Si un index est invalide ou si la cible est structurelle.
        """
        if not 0 <= source_index < Board.SIZE or not 0 <= target_index < Board.SIZE:
            raise ValueError("Les index de duplication doivent être compris entre 0 et 39.")
        if target_index in {0, 10, 20, 30}:
            raise ValueError("Une case structurelle ne peut pas être remplacée par duplication.")
        source = self.spaces[source_index].to_dict()
        source["index"] = target_index
        source["name"] = f"{source['name']} copie"
        self.spaces[target_index] = SpaceConfig.from_dict(source)

    def duplicate_card(self, deck_name: str, index: int) -> int:
        """Duplique une carte à la suite du paquet demandé.

        Entrées:
            deck_name (str): ``chance`` ou ``community_chest``.
            index (int): Position de la carte modèle.

        Sortie:
            int: Index de la nouvelle carte.

        Lève:
            ValueError: Si le paquet ou l'index est invalide.
        """
        cards = self.chance_cards if deck_name == "chance" else self.community_chest_cards
        if deck_name not in {"chance", "community_chest"}:
            raise ValueError("Paquet inconnu.")
        if not 0 <= index < len(cards):
            raise ValueError("Carte à dupliquer introuvable.")
        cards.append(CardConfig.from_dict(cards[index].to_dict()))
        return len(cards) - 1

    @property
    def is_standard(self) -> bool:
        """Indique si cette définition est identique au plateau standard.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` si les données sont égales à la définition standard.
        """
        return self.to_dict(include_name=False) == self.standard().to_dict(include_name=False)

    def summary(self) -> str:
        """Construit un résumé court pour l'écran de préparation.

        Entrées:
            Aucune.

        Sortie:
            str: Nom et caractère standard/personnalisé du plateau.
        """
        kind = "standard" if self.is_standard else "personnalisé"
        return f"Plateau : {self.name} ({kind})"

    def clone(self) -> "BoardConfig":
        """Crée une copie profonde sérialisable de la définition.

        Entrées:
            Aucune.

        Sortie:
            BoardConfig: Copie indépendante.
        """
        return self.from_dict(self.to_dict())

    def to_dict(self, include_name: bool = True) -> dict[str, Any]:
        """Sérialise la définition du plateau.

        Entrées:
            include_name (bool): Inclut ou non le nom descriptif dans la comparaison.

        Sortie:
            dict[str, Any]: Cases et cartes sous forme JSON.
        """
        result: dict[str, Any] = {
            "spaces": [space.to_dict() for space in self.spaces],
            "chance_cards": [card.to_dict() for card in self.chance_cards],
            "community_chest_cards": [card.to_dict() for card in self.community_chest_cards],
        }
        if include_name:
            result["name"] = self.name
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BoardConfig":
        """Reconstruit une définition de plateau depuis un dictionnaire.

        Entrées:
            data (dict[str, Any]): Données JSON du plateau.

        Sortie:
            BoardConfig: Définition validée et prête à construire le moteur.
        """
        result = cls(
            name=str(data.get("name", "Plateau personnalisé")),
            spaces=[SpaceConfig.from_dict(item) for item in data.get("spaces", [])],
            chance_cards=[CardConfig.from_dict(item) for item in data.get("chance_cards", [])],
            community_chest_cards=[
                CardConfig.from_dict(item)
                for item in data.get("community_chest_cards", [])
            ],
        )
        result.validate()
        return result

    @classmethod
    def standard(cls) -> "BoardConfig":
        """Construit la définition éditable correspondant au plateau standard.

        Entrées:
            Aucune.

        Sortie:
            BoardConfig: Copie complète du plateau et des paquets standard.
        """
        board = Board.standard()
        chance = create_chance_deck(shuffle=False)
        community = create_community_chest_deck(shuffle=False)
        return cls(
            name="Plateau standard",
            spaces=[cls._space_config_from_space(space) for space in board.spaces],
            chance_cards=[CardConfig.from_card(card) for card in chance.cards],
            community_chest_cards=[CardConfig.from_card(card) for card in community.cards],
        )

    @classmethod
    def blank_template(cls, name: str = "Plateau vierge") -> "BoardConfig":
        """Crée une base jouable volontairement neutre pour un plateau conçu de zéro.

        Entrées:
            name (str): Nom attribué à la nouvelle définition.

        Sortie:
            BoardConfig: Structure standard avec noms génériques, économie simple et cartes neutres.
        """
        standard = cls.standard()
        spaces: list[SpaceConfig] = []
        for item in standard.spaces:
            if item.space_type == "property":
                spaces.append(
                    SpaceConfig(
                        index=item.index,
                        space_type="property",
                        name=f"Terrain {item.index}",
                        price=100,
                        color_group=item.color_group or f"Groupe {item.index}",
                        base_rent=5,
                        house_rents=(10, 20, 30, 40),
                        hotel_rent=50,
                        house_cost=50,
                    )
                )
            elif item.space_type == "railroad":
                spaces.append(
                    SpaceConfig(
                        item.index,
                        "railroad",
                        f"Gare {item.index}",
                        price=200,
                        railroad_rents=(25, 50, 100, 200),
                    )
                )
            elif item.space_type == "utility":
                spaces.append(
                    SpaceConfig(
                        item.index,
                        "utility",
                        f"Compagnie {item.index}",
                        price=150,
                        utility_multipliers=(4, 10),
                    )
                )
            elif item.space_type == "tax":
                spaces.append(SpaceConfig(item.index, "tax", f"Taxe {item.index}", tax_amount=0))
            elif item.space_type == "chance":
                spaces.append(SpaceConfig(item.index, "chance", "Chance"))
            elif item.space_type == "community_chest":
                spaces.append(SpaceConfig(item.index, "community_chest", "Communauté"))
            else:
                spaces.append(SpaceConfig(item.index, item.space_type, item.name))
        result = cls(
            name=name.strip() or "Plateau vierge",
            spaces=spaces,
            chance_cards=[CardConfig("MoneyCard", "Carte Chance à personnaliser", amount=0)],
            community_chest_cards=[
                CardConfig("MoneyCard", "Carte Communauté à personnaliser", amount=0)
            ],
        )
        result.validate()
        return result

    @classmethod
    def from_board(cls, board: Board, name: str = "Plateau personnalisé") -> "BoardConfig":
        """Capture un plateau moteur existant avec les paquets standard.

        Entrées:
            board (Board): Plateau dont les cases doivent être copiées.
            name (str): Nom descriptif attribué à la définition.

        Sortie:
            BoardConfig: Plateau éditable conservant les types et valeurs observés.
        """
        standard = cls.standard()
        return cls(
            name=name,
            spaces=[cls._space_config_from_space(space) for space in board.spaces],
            chance_cards=[CardConfig.from_dict(card.to_dict()) for card in standard.chance_cards],
            community_chest_cards=[
                CardConfig.from_dict(card.to_dict()) for card in standard.community_chest_cards
            ],
        )

    @staticmethod
    def _space_config_from_space(space: Space | OwnableSpace) -> SpaceConfig:
        """Convertit une case moteur en configuration éditable.

        Entrées:
            space (Space | OwnableSpace): Case concrète du plateau.

        Sortie:
            SpaceConfig: Valeurs économiques et structurelles copiées.
        """
        if isinstance(space, Property):
            return SpaceConfig(
                space.index,
                "property",
                space.name,
                price=space.price,
                color_group=space.color_group,
                base_rent=space.base_rent,
                house_rents=space.house_rents,
                hotel_rent=space.hotel_rent,
                house_cost=space.house_cost,
            )
        if isinstance(space, Railroad):
            return SpaceConfig(
                space.index,
                "railroad",
                space.name,
                price=space.price,
                railroad_rents=space.rent_values,
            )
        if isinstance(space, Utility):
            return SpaceConfig(
                space.index,
                "utility",
                space.name,
                price=space.price,
                utility_multipliers=space.multipliers,
            )
        if isinstance(space, TaxSpace):
            return SpaceConfig(space.index, "tax", space.name, tax_amount=space.amount)
        type_map = {
            GoSpace: "go",
            CommunityChestSpace: "community_chest",
            ChanceSpace: "chance",
            JailSpace: "jail",
            FreeParkingSpace: "free_parking",
            GoToJailSpace: "go_to_jail",
        }
        for cls, type_name in type_map.items():
            if isinstance(space, cls):
                return SpaceConfig(space.index, type_name, space.name)
        raise ValueError(f"Type de case non pris en charge : {type(space).__name__}.")

    def build_board(self) -> Board:
        """Construit un plateau moteur neuf à partir des configurations de cases.

        Entrées:
            Aucune.

        Sortie:
            Board: Plateau sans propriétaires ni bâtiments.
        """
        self.validate()
        spaces: list[Space | OwnableSpace] = []
        for item in self.spaces:
            if item.space_type == "property":
                spaces.append(
                    Property(
                        index=item.index,
                        name=item.name,
                        price=item.price,
                        color_group=item.color_group,
                        base_rent=item.base_rent,
                        house_rents=item.house_rents,
                        hotel_rent=item.hotel_rent,
                        house_cost=item.house_cost,
                    )
                )
            elif item.space_type == "railroad":
                spaces.append(
                    Railroad(
                        item.index,
                        item.name,
                        item.price,
                        rent_values=item.railroad_rents,
                    )
                )
            elif item.space_type == "utility":
                spaces.append(
                    Utility(
                        item.index,
                        item.name,
                        item.price,
                        multipliers=item.utility_multipliers,
                    )
                )
            elif item.space_type == "tax":
                spaces.append(TaxSpace(item.index, item.name, item.tax_amount))
            elif item.space_type == "go":
                spaces.append(GoSpace(item.index, item.name))
            elif item.space_type == "community_chest":
                spaces.append(CommunityChestSpace(item.index, item.name))
            elif item.space_type == "chance":
                spaces.append(ChanceSpace(item.index, item.name))
            elif item.space_type == "jail":
                spaces.append(JailSpace(item.index, item.name))
            elif item.space_type == "free_parking":
                spaces.append(FreeParkingSpace(item.index, item.name))
            elif item.space_type == "go_to_jail":
                spaces.append(GoToJailSpace(item.index, item.name))
            else:
                raise ValueError(f"Type de case non pris en charge : {item.space_type}.")
        return Board(spaces)

    def build_chance_deck(self, rng: Random | None = None, shuffle: bool = True) -> CardDeck:
        """Construit le paquet Chance défini par le plateau.

        Entrées:
            rng (Random | None): Générateur de la partie pour un mélange reproductible.
            shuffle (bool): Active le mélange initial.

        Sortie:
            CardDeck: Paquet Chance neuf.
        """
        return CardDeck(
            "chance",
            [card.build_card("chance") for card in self.chance_cards],
            rng=rng,
            shuffle=shuffle,
        )

    def build_community_chest_deck(
        self,
        rng: Random | None = None,
        shuffle: bool = True,
    ) -> CardDeck:
        """Construit le paquet Caisse de communauté défini par le plateau.

        Entrées:
            rng (Random | None): Générateur de la partie pour un mélange reproductible.
            shuffle (bool): Active le mélange initial.

        Sortie:
            CardDeck: Paquet Communauté neuf.
        """
        return CardDeck(
            "community_chest",
            [card.build_card("community_chest") for card in self.community_chest_cards],
            rng=rng,
            shuffle=shuffle,
        )
