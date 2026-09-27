"""Modélise les échanges directs entre deux joueurs sans dépendre de l'interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .properties import OwnableSpace, Property

if TYPE_CHECKING:
    from .cards import Card
    from .game import Game
    from .player import Player


@dataclass
class TradeResult:
    """Décrit le résultat d'une tentative d'échange.

    Entrées:
        success (bool): Indique si l'échange a été exécuté.
        message (str): Explication du succès ou du refus.
        initiator (Player): Joueur ayant proposé l'échange.
        recipient (Player): Autre joueur impliqué.

    Sortie:
        TradeResult: Résultat exploitable par l'interface et les tests.
    """

    success: bool
    message: str
    initiator: "Player"
    recipient: "Player"


@dataclass
class TradeOffer:
    """Représente une proposition d'échange complète entre deux joueurs.

    Entrées:
        game (Game): Partie contenant le plateau et les règles.
        initiator (Player): Joueur qui construit l'offre.
        recipient (Player): Joueur avec lequel l'échange est réalisé.
        cash_from_initiator (int): Argent donné par l'initiateur.
        cash_from_recipient (int): Argent donné par le destinataire.
        properties_from_initiator (list[OwnableSpace]): Biens cédés par l'initiateur.
        properties_from_recipient (list[OwnableSpace]): Biens cédés par le destinataire.
        cards_from_initiator (list[Card]): Cartes conservées cédées par l'initiateur.
        cards_from_recipient (list[Card]): Cartes conservées cédées par le destinataire.

    Sortie:
        TradeOffer: Objet pouvant être validé puis exécuté atomiquement.
    """

    game: "Game"
    initiator: "Player"
    recipient: "Player"
    cash_from_initiator: int = 0
    cash_from_recipient: int = 0
    properties_from_initiator: list[OwnableSpace] = field(default_factory=list)
    properties_from_recipient: list[OwnableSpace] = field(default_factory=list)
    cards_from_initiator: list["Card"] = field(default_factory=list)
    cards_from_recipient: list["Card"] = field(default_factory=list)

    def mortgage_transfer_interest(self, space: OwnableSpace) -> int:
        """Calcule l'intérêt bancaire immédiat dû à la réception d'un bien hypothéqué.

        Entrées:
            space (OwnableSpace): Bien transféré.

        Sortie:
            int: Dix pour cent de la valeur hypothécaire, arrondis au supérieur,
            ou zéro lorsque le bien n'est pas hypothéqué.
        """
        if not space.mortgaged or not self.game.options.transferred_mortgages:
            return 0
        return self.game.rules.mortgage_interest(space)

    def _group_has_buildings(self, property_: Property) -> bool:
        """Indique si le groupe de couleur d'un terrain contient encore un bâtiment.

        Entrées:
            property_ (Property): Terrain dont le groupe doit être inspecté.

        Sortie:
            bool: ``True`` si au moins une maison ou un hôtel existe dans le groupe.
        """
        return any(
            space.owner is property_.owner and space.development_level > 0
            for space in self.game.board.spaces_in_group(property_.color_group)
        )

    def _properties_are_tradeable(
        self,
        owner: "Player",
        spaces: list[OwnableSpace],
    ) -> tuple[bool, str]:
        """Vérifie la propriété réelle des biens et l'absence de bâtiments bloquants.

        Entrées:
            owner (Player): Joueur censé posséder les biens.
            spaces (list[OwnableSpace]): Biens qu'il souhaite céder.

        Sortie:
            tuple[bool, str]: Validité et explication éventuelle du refus.
        """
        if len({id(space) for space in spaces}) != len(spaces):
            return False, "Un même bien ne peut pas être ajouté plusieurs fois."

        for space in spaces:
            if space.owner is not owner or space not in owner.properties:
                return False, f"{owner.name} ne possède pas {space.name}."

            if isinstance(space, Property) and self._group_has_buildings(space):
                return (
                    False,
                    (
                        f"{space.name} ne peut pas être échangé tant qu'un bâtiment "
                        f"reste sur son groupe de couleur."
                    ),
                )

        return True, ""

    @staticmethod
    def _cards_are_tradeable(owner: "Player", cards: list["Card"]) -> tuple[bool, str]:
        """Vérifie que les cartes proposées sont réellement détenues par le joueur.

        Entrées:
            owner (Player): Joueur censé posséder les cartes.
            cards (list[Card]): Cartes qu'il souhaite céder.

        Sortie:
            tuple[bool, str]: Validité et message d'erreur éventuel.
        """
        if len({id(card) for card in cards}) != len(cards):
            return False, "Une même carte ne peut pas être ajoutée plusieurs fois."

        for card in cards:
            if card not in owner.held_cards:
                return False, f"{owner.name} ne possède plus une des cartes proposées."

        return True, ""

    def _interest_due_by_initiator(self) -> int:
        """Calcule les intérêts dus par l'initiateur sur les hypothèques qu'il reçoit.

        Entrées:
            Aucune autre que l'offre courante.

        Sortie:
            int: Total des intérêts bancaires immédiats.
        """
        return sum(
            self.mortgage_transfer_interest(space)
            for space in self.properties_from_recipient
        )

    def _interest_due_by_recipient(self) -> int:
        """Calcule les intérêts dus par le destinataire sur les hypothèques reçues.

        Entrées:
            Aucune autre que l'offre courante.

        Sortie:
            int: Total des intérêts bancaires immédiats.
        """
        return sum(
            self.mortgage_transfer_interest(space)
            for space in self.properties_from_initiator
        )

    def validate(self) -> tuple[bool, str]:
        """Vérifie intégralement qu'une proposition peut être exécutée.

        Entrées:
            Aucune autre que les données de l'offre.

        Sortie:
            tuple[bool, str]: ``True`` et chaîne vide lorsque l'offre est valide,
            sinon ``False`` accompagné de la première raison du refus.
        """
        if self.initiator is self.recipient:
            return False, "Un joueur ne peut pas échanger avec lui-même."

        if self.initiator.bankrupt or self.recipient.bankrupt:
            return False, "Un joueur en faillite ne peut pas participer à un échange."

        if self.cash_from_initiator < 0 or self.cash_from_recipient < 0:
            return False, "Les montants d'argent doivent être positifs ou nuls."

        valid, message = self._properties_are_tradeable(
            self.initiator,
            self.properties_from_initiator,
        )
        if not valid:
            return valid, message

        valid, message = self._properties_are_tradeable(
            self.recipient,
            self.properties_from_recipient,
        )
        if not valid:
            return valid, message

        valid, message = self._cards_are_tradeable(
            self.initiator,
            self.cards_from_initiator,
        )
        if not valid:
            return valid, message

        valid, message = self._cards_are_tradeable(
            self.recipient,
            self.cards_from_recipient,
        )
        if not valid:
            return valid, message

        initiator_final_cash = (
            self.initiator.cash
            - self.cash_from_initiator
            + self.cash_from_recipient
        )
        recipient_final_cash = (
            self.recipient.cash
            - self.cash_from_recipient
            + self.cash_from_initiator
        )

        if initiator_final_cash < 0:
            return (
                False,
                f"{self.initiator.name} n'a pas assez d'argent pour cet échange.",
            )

        if recipient_final_cash < 0:
            return (
                False,
                f"{self.recipient.name} n'a pas assez d'argent pour cet échange.",
            )

        has_content = any(
            (
                self.cash_from_initiator,
                self.cash_from_recipient,
                self.properties_from_initiator,
                self.properties_from_recipient,
                self.cards_from_initiator,
                self.cards_from_recipient,
            )
        )
        if not has_content:
            return False, "L'échange est vide."

        return True, ""

    def execute(self) -> TradeResult:
        """Exécute simultanément l'échange après validation.

        Entrées:
            Aucune autre que l'offre courante.

        Sortie:
            TradeResult: Résultat détaillant le succès ou le motif de refus.
        """
        valid, message = self.validate()
        if not valid:
            return TradeResult(False, message, self.initiator, self.recipient)

        initiator_interest = self._interest_due_by_initiator()
        recipient_interest = self._interest_due_by_recipient()

        self.initiator.cash = (
            self.initiator.cash
            - self.cash_from_initiator
            + self.cash_from_recipient
        )
        self.recipient.cash = (
            self.recipient.cash
            - self.cash_from_recipient
            + self.cash_from_initiator
        )

        received_by_recipient = [
            space for space in self.properties_from_initiator if space.mortgaged
        ]
        received_by_initiator = [
            space for space in self.properties_from_recipient if space.mortgaged
        ]

        for space in list(self.properties_from_initiator):
            space.assign_to(self.recipient)

        for space in list(self.properties_from_recipient):
            space.assign_to(self.initiator)

        for card in list(self.cards_from_initiator):
            self.initiator.remove_held_card(card)
            self.recipient.add_held_card(card)

        for card in list(self.cards_from_recipient):
            self.recipient.remove_held_card(card)
            self.initiator.add_held_card(card)

        if received_by_initiator and not self.initiator.bankrupt:
            self.game.settle_received_mortgages(
                self.initiator,
                received_by_initiator,
            )
        if received_by_recipient and not self.recipient.bankrupt:
            self.game.settle_received_mortgages(
                self.recipient,
                received_by_recipient,
            )

        details: list[str] = [
            f"Échange conclu entre {self.initiator.name} et {self.recipient.name}."
        ]
        if initiator_interest:
            details.append(
                f"{self.initiator.name} règle le traitement bancaire des hypothèques reçues."
            )
        if recipient_interest:
            details.append(
                f"{self.recipient.name} règle le traitement bancaire des hypothèques reçues."
            )

        message = " ".join(details)
        self.game.record_event(
            "trade",
            message,
            self.initiator,
            participant_ids=[
                self.initiator.player_id,
                self.recipient.player_id,
            ],
            cash_from_initiator=self.cash_from_initiator,
            cash_from_recipient=self.cash_from_recipient,
            properties_from_initiator=[
                space.index for space in self.properties_from_initiator
            ],
            properties_from_recipient=[
                space.index for space in self.properties_from_recipient
            ],
            cards_from_initiator=len(self.cards_from_initiator),
            cards_from_recipient=len(self.cards_from_recipient),
        )
        return TradeResult(
            True,
            message,
            self.initiator,
            self.recipient,
        )
