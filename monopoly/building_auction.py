"""Gère les enchères de maisons et d'hôtels en cas de pénurie bancaire."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .player import Player
from .properties import Property

if TYPE_CHECKING:
    from .game import Game


BuildingType = Literal["house", "hotel"]


@dataclass
class BuildingAuctionResult:
    """Décrit le résultat final d'une enchère de bâtiment.

    Entrées:
        building_type (BuildingType): Type de bâtiment vendu.
        winner (Player | None): Joueur gagnant ou ``None`` sans vente.
        property (Property | None): Terrain choisi pour recevoir le bâtiment.
        amount (int): Prix payé au terme de l'enchère.

    Sortie:
        BuildingAuctionResult: Résultat utilisable par l'interface et les tests.
    """

    building_type: BuildingType
    winner: Player | None
    property: Property | None
    amount: int

    @property
    def sold(self) -> bool:
        """Indique si un bâtiment a réellement été attribué.

        Entrées:
            Aucune autre que l'instance.

        Sortie:
            bool: ``True`` si un gagnant et un terrain cible existent.
        """
        return self.winner is not None and self.property is not None


class BuildingAuction:
    """Organise la vente d'une maison ou d'un hôtel lorsque le stock est limité.

    Entrées:
        game (Game): Partie fournissant règles, banque et joueurs.
        building_type (BuildingType): ``house`` ou ``hotel``.
        bidders (list[Player]): Joueurs autorisés à participer.

    Sortie:
        BuildingAuction: Enchère indépendante de Tkinter conservant cible et meilleure offre.
    """

    def __init__(
        self,
        game: "Game",
        building_type: BuildingType,
        bidders: list[Player],
    ) -> None:
        """Initialise une enchère de bâtiment à zéro.

        Entrées:
            game (Game): Partie courante.
            building_type (BuildingType): Type de bâtiment vendu.
            bidders (list[Player]): Participants potentiels.

        Sortie:
            None: Les participants éligibles sont conservés sans meilleure offre.

        Lève:
            ValueError: Si le type est invalide ou si la banque n'a aucun bâtiment du type.
        """
        if building_type not in ("house", "hotel"):
            raise ValueError("Le type de bâtiment doit être 'house' ou 'hotel'.")

        self.game = game
        self.building_type = building_type

        if self.stock_available <= 0:
            raise ValueError("La banque ne possède aucun bâtiment de ce type.")

        self.active_bidders = [
            player
            for player in bidders
            if not player.bankrupt
            and player.cash > 0
            and bool(self.eligible_targets(player))
        ]
        self.highest_bid = 0
        self.highest_bidder: Player | None = None
        self.highest_target: Property | None = None
        self.finished = False

    @property
    def stock_available(self) -> int:
        """Retourne le stock bancaire restant pour le type vendu.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de maisons ou d'hôtels encore disponibles.
        """
        if self.building_type == "house":
            return self.game.bank.houses_available
        return self.game.bank.hotels_available

    @property
    def display_name(self) -> str:
        """Retourne le nom français du bâtiment vendu.

        Entrées:
            Aucune.

        Sortie:
            str: ``maison`` ou ``hôtel``.
        """
        return "maison" if self.building_type == "house" else "hôtel"

    def eligible_targets(self, player: Player) -> list[Property]:
        """Retourne les terrains sur lesquels le joueur peut placer le bâtiment.

        Entrées:
            player (Player): Participant à évaluer.

        Sortie:
            list[Property]: Terrains respectant propriété, monopole et équilibre.
        """
        if self.building_type == "house":
            return self.game.rules.eligible_house_targets(player)
        return self.game.rules.eligible_hotel_targets(player)

    def can_bid(self, player: Player, amount: int, target: Property) -> bool:
        """Vérifie qu'une offre et son terrain cible sont valides.

        Entrées:
            player (Player): Joueur souhaitant enchérir.
            amount (int): Montant proposé.
            target (Property): Terrain où le bâtiment serait placé.

        Sortie:
            bool: ``True`` si l'offre peut devenir la meilleure.
        """
        return (
            not self.finished
            and self.stock_available > 0
            and player in self.active_bidders
            and amount > self.highest_bid
            and player.can_afford(amount)
            and target in self.eligible_targets(player)
        )

    def place_bid(self, player: Player, amount: int, target: Property) -> bool:
        """Enregistre une meilleure offre et le terrain choisi par le joueur.

        Entrées:
            player (Player): Joueur qui enchérit.
            amount (int): Nouvelle offre.
            target (Property): Terrain cible de cette offre.

        Sortie:
            bool: ``True`` si l'offre est acceptée.
        """
        if not self.can_bid(player, amount, target):
            return False

        self.highest_bid = amount
        self.highest_bidder = player
        self.highest_target = target
        return True

    def withdraw(self, player: Player) -> bool:
        """Retire un joueur qui ne souhaite pas acheter le bâtiment.

        Entrées:
            player (Player): Participant qui abandonne.

        Sortie:
            bool: ``True`` si le joueur est retiré de l'enchère.
        """
        if self.finished or player not in self.active_bidders:
            return False
        if player is self.highest_bidder:
            return False

        self.active_bidders.remove(player)
        return True

    @property
    def can_finish(self) -> bool:
        """Indique si l'enchère peut être clôturée.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsqu'aucun joueur ne reste ou lorsque le meilleur
            enchérisseur est le seul participant actif.
        """
        if not self.active_bidders:
            return True

        return (
            self.highest_bidder is not None
            and len(self.active_bidders) == 1
            and self.active_bidders[0] is self.highest_bidder
        )

    def finish(self) -> BuildingAuctionResult:
        """Clôture l'enchère et construit le bâtiment au prix gagnant.

        Entrées:
            Aucune.

        Sortie:
            BuildingAuctionResult: Résultat final avec gagnant, terrain et montant.

        Lève:
            RuntimeError: Si plusieurs participants empêchent encore la clôture
            ou si l'état du plateau ne permet plus d'honorer l'offre gagnante.
        """
        if self.finished:
            return BuildingAuctionResult(
                self.building_type,
                self.highest_bidder,
                self.highest_target,
                self.highest_bid,
            )

        if not self.can_finish:
            raise RuntimeError("L'enchère de bâtiment ne peut pas encore être clôturée.")

        if self.highest_bidder is None or self.highest_target is None:
            self.finished = True
            return BuildingAuctionResult(self.building_type, None, None, 0)

        if self.building_type == "house":
            built = self.game.rules.build_house_at_price(
                self.highest_bidder,
                self.highest_target,
                self.highest_bid,
            )
        else:
            built = self.game.rules.build_hotel_at_price(
                self.highest_bidder,
                self.highest_target,
                self.highest_bid,
            )

        if not built:
            raise RuntimeError(
                "Le bâtiment ne peut plus être placé sur le terrain choisi."
            )

        self.finished = True
        self.game.record_event(
            "building_auction_win",
            (
                f"{self.highest_bidder.name} remporte un {self.display_name} "
                f"pour {self.highest_bid} $ sur {self.highest_target.name}."
            ),
            self.highest_bidder,
            building_type=self.building_type,
            property_index=self.highest_target.index,
            amount=self.highest_bid,
        )
        return BuildingAuctionResult(
            self.building_type,
            self.highest_bidder,
            self.highest_target,
            self.highest_bid,
        )
