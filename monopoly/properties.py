"""Définit les différents types de cases achetables et leurs états financiers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .player import Player


@dataclass
class OwnableSpace(ABC):
    """Classe abstraite commune à toutes les cases pouvant être achetées.

    Entrées:
        index (int): Position de la case sur le plateau.
        name (str): Nom affiché du bien.
        price (int): Prix d'achat du bien.
        owner (Player | None): Propriétaire actuel, ou ``None`` si le bien est libre.
        mortgaged (bool): Indique si le bien est hypothéqué.

    Sortie:
        OwnableSpace: Base polymorphe utilisée par les terrains, gares et compagnies.
    """

    index: int
    name: str
    price: int
    owner: Player | None = None
    mortgaged: bool = False

    @property
    def is_owned(self) -> bool:
        """Indique si le bien possède actuellement un propriétaire.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            bool: ``True`` si le bien appartient à un joueur, sinon ``False``.
        """
        return self.owner is not None

    @property
    def is_available(self) -> bool:
        """Indique si le bien est actuellement disponible à l'achat.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            bool: ``True`` si aucun joueur ne possède le bien, sinon ``False``.
        """
        return self.owner is None

    @property
    def mortgage_value(self) -> int:
        """Calcule la somme versée par la banque lors d'une hypothèque.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            int: Moitié entière du prix d'achat du bien.
        """
        return self.price // 2

    @property
    def unmortgage_cost(self) -> int:
        """Calcule le coût nécessaire pour lever l'hypothèque du bien.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            int: Valeur de l'hypothèque augmentée de 10 %, arrondie au supérieur.
        """
        return ceil(self.mortgage_value * 110 / 100)

    def buy(self, player: Player) -> bool:
        """Tente de vendre le bien à un joueur au prix indiqué sur la case.

        Entrées:
            player (Player): Joueur qui souhaite acheter le bien.

        Sortie:
            bool: ``True`` si l'achat est effectué, sinon ``False``.
        """
        if self.owner is not None:
            return False
        if not player.can_afford(self.price):
            return False

        player.pay(self.price)
        self.assign_to(player)
        return True

    def assign_to(self, player: Player) -> None:
        """Attribue directement le bien à un joueur sans effectuer de paiement.

        Entrées:
            player (Player): Nouveau propriétaire du bien.

        Sortie:
            None: Le propriétaire et la collection du joueur sont mis à jour.
        """
        if self.owner is not None and self.owner is not player:
            self.owner.remove_property(self)

        self.owner = player
        player.add_property(self)

    def reset_ownership(self) -> None:
        """Rend le bien à la banque et supprime son éventuelle hypothèque.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            None: Le propriétaire est retiré et l'hypothèque est annulée.
        """
        if self.owner is not None:
            self.owner.remove_property(self)
        self.owner = None
        self.mortgaged = False

    @abstractmethod
    def calculate_rent(self, game: Game, dice_total: int) -> int:
        """Calcule le loyer dû lorsqu'un adversaire arrive sur ce bien.

        Entrées:
            game (Game): Partie courante donnant accès au plateau et aux joueurs.
            dice_total (int): Somme des dés, utilisée notamment par les compagnies.

        Sortie:
            int: Montant du loyer calculé par le type concret de bien.
        """
        raise NotImplementedError


@dataclass
class Property(OwnableSpace):
    """Représente un terrain appartenant à un groupe de couleur.

    Entrées:
        index, name, price, owner, mortgaged: Paramètres hérités de ``OwnableSpace``.
        color_group (str): Identifiant du groupe de couleur.
        base_rent (int): Loyer de base sans bâtiment.
        house_rents (tuple[int, int, int, int]): Loyers pour une à quatre maisons.
        hotel_rent (int): Loyer lorsqu'un hôtel est construit.
        house_cost (int): Prix d'une maison ou du passage vers un hôtel.
        houses (int): Nombre actuel de maisons, entre zéro et quatre.
        hotel (bool): Indique si le terrain possède un hôtel.

    Sortie:
        Property: Terrain capable de gérer loyer et niveau de développement.
    """

    color_group: str = ""
    base_rent: int = 0
    house_rents: tuple[int, int, int, int] = (0, 0, 0, 0)
    hotel_rent: int = 0
    house_cost: int = 0
    houses: int = 0
    hotel: bool = False

    @property
    def development_level(self) -> int:
        """Expose le niveau de développement sous forme d'un entier comparable.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            int: 0 à 4 pour les maisons, ou 5 lorsqu'un hôtel est présent.
        """
        return 5 if self.hotel else self.houses

    def reset_development(self) -> None:
        """Supprime toutes les maisons et l'éventuel hôtel du terrain.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            None: Le terrain revient à un niveau de développement nul.
        """
        self.houses = 0
        self.hotel = False

    def reset_ownership(self) -> None:
        """Rend le terrain à la banque et réinitialise aussi ses bâtiments.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            None: Propriétaire, hypothèque, maisons et hôtel sont supprimés.
        """
        super().reset_ownership()
        self.reset_development()

    def calculate_rent(self, game: Game, dice_total: int) -> int:
        """Calcule le loyer d'un terrain selon monopole, maisons ou hôtel.

        Entrées:
            game (Game): Partie utilisée pour vérifier la possession du groupe.
            dice_total (int): Somme des dés, inutilisée pour un terrain classique.

        Sortie:
            int: Loyer courant, ou zéro si le terrain est libre ou hypothéqué.
        """
        if self.owner is None or self.mortgaged:
            return 0

        if self.hotel:
            return self.hotel_rent

        if self.houses > 0:
            return self.house_rents[self.houses - 1]

        rent = self.base_rent

        if game.board.player_owns_group(self.owner, self.color_group):
            rent *= 2

        return rent


@dataclass
class Railroad(OwnableSpace):
    """Représente une gare dont le loyer dépend du nombre de gares possédées.

    Entrées:
        index, name, price, owner, mortgaged: Paramètres hérités de ``OwnableSpace``.

    Sortie:
        Railroad: Gare appliquant automatiquement son barème de loyer.
    """

    def calculate_rent(self, game: Game, dice_total: int) -> int:
        """Calcule le loyer de la gare selon le nombre de gares du propriétaire.

        Entrées:
            game (Game): Partie courante, conservée pour l'interface polymorphe.
            dice_total (int): Somme des dés, inutilisée pour une gare.

        Sortie:
            int: 25, 50, 100 ou 200, ou zéro si la gare est hypothéquée/libre.
        """
        if self.owner is None or self.mortgaged:
            return 0

        count = sum(
            1
            for space in self.owner.properties
            if isinstance(space, Railroad)
        )

        return 25 * (2 ** max(0, count - 1))


@dataclass
class Utility(OwnableSpace):
    """Représente une compagnie dont le loyer dépend du résultat des dés.

    Entrées:
        index, name, price, owner, mortgaged: Paramètres hérités de ``OwnableSpace``.

    Sortie:
        Utility: Compagnie calculant son loyer à partir des dés.
    """

    def calculate_rent(self, game: Game, dice_total: int) -> int:
        """Calcule le loyer d'une compagnie à partir de la somme des dés.

        Entrées:
            game (Game): Partie courante, conservée pour l'interface polymorphe.
            dice_total (int): Somme des deux dés du déplacement courant.

        Sortie:
            int: Quatre ou dix fois les dés selon le nombre de compagnies possédées.
        """
        if self.owner is None or self.mortgaged:
            return 0

        count = sum(
            1
            for space in self.owner.properties
            if isinstance(space, Utility)
        )

        multiplier = 10 if count >= 2 else 4
        return dice_total * multiplier
