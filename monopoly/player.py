"""Définit la classe représentant un joueur et son état pendant une partie."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cards import Card
    from .properties import OwnableSpace


@dataclass
class Player:
    """Représente un joueur et toutes ses données individuelles.

    Entrées:
        player_id (int): Identifiant unique du joueur dans la partie.
        name (str): Nom affiché du joueur.
        cash (int): Argent disponible au départ. Valeur par défaut : 1500.
        position (int): Index de la case occupée sur le plateau.
        bankrupt (bool): Indique si le joueur est en faillite.
        in_jail (bool): Indique si le joueur est actuellement en prison.
        jail_turns (int): Nombre de tentatives déjà passées en prison.
        properties (list[OwnableSpace]): Biens possédés par le joueur.
        held_cards (list[Card]): Cartes conservées par le joueur, notamment les
            cartes permettant de sortir de prison.

    Sortie:
        Player: Une instance contenant l'état mutable du joueur pendant la partie.
    """

    player_id: int
    name: str
    cash: int = 1500
    position: int = 0
    bankrupt: bool = False
    in_jail: bool = False
    jail_turns: int = 0
    properties: list[OwnableSpace] = field(default_factory=list)
    held_cards: list[Card] = field(default_factory=list)

    def can_afford(self, amount: int) -> bool:
        """Indique si le joueur peut payer une somme donnée immédiatement.

        Entrées:
            amount (int): Somme que le joueur doit pouvoir payer.

        Sortie:
            bool: ``True`` si le joueur n'est pas en faillite et possède au
            moins cette somme, sinon ``False``.
        """
        return not self.bankrupt and self.cash >= amount

    def pay(self, amount: int) -> int:
        """Retire de l'argent au joueur dans la limite de son solde disponible.

        Entrées:
            amount (int): Somme demandée au joueur.

        Sortie:
            int: Somme réellement payée. Elle peut être inférieure à ``amount``
            si le joueur ne possède pas assez d'argent.
        """
        if amount <= 0 or self.bankrupt:
            return 0

        paid = min(self.cash, amount)
        self.cash -= paid
        return paid

    def receive(self, amount: int) -> None:
        """Ajoute une somme positive au solde du joueur.

        Entrées:
            amount (int): Somme à créditer. Une valeur nulle ou négative est ignorée.

        Sortie:
            None: Le solde du joueur est modifié directement.
        """
        if amount > 0 and not self.bankrupt:
            self.cash += amount

    def move_to(self, position: int) -> None:
        """Place directement le joueur sur une position donnée du plateau.

        Entrées:
            position (int): Index de la nouvelle case du joueur.

        Sortie:
            None: La position du joueur est modifiée directement.
        """
        self.position = position

    def add_property(self, property_: OwnableSpace) -> None:
        """Ajoute un bien à la collection du joueur s'il n'y figure pas déjà.

        Entrées:
            property_ (OwnableSpace): Propriété, gare ou compagnie acquise.

        Sortie:
            None: La liste ``properties`` du joueur est mise à jour.
        """
        if property_ not in self.properties:
            self.properties.append(property_)

    def remove_property(self, property_: OwnableSpace) -> None:
        """Retire un bien de la collection du joueur s'il le possède.

        Entrées:
            property_ (OwnableSpace): Bien à retirer de la collection.

        Sortie:
            None: La liste ``properties`` du joueur est mise à jour.
        """
        if property_ in self.properties:
            self.properties.remove(property_)

    def add_held_card(self, card: Card) -> None:
        """Ajoute une carte conservable à la main du joueur.

        Entrées:
            card (Card): Carte à conserver jusqu'à son utilisation.

        Sortie:
            None: La carte est ajoutée à ``held_cards`` si elle n'y figure pas déjà.
        """
        if card not in self.held_cards:
            self.held_cards.append(card)

    def remove_held_card(self, card: Card) -> None:
        """Retire une carte conservée de la main du joueur.

        Entrées:
            card (Card): Carte à retirer après utilisation ou faillite.

        Sortie:
            None: La carte est retirée de ``held_cards`` si elle est présente.
        """
        if card in self.held_cards:
            self.held_cards.remove(card)

    def declare_bankruptcy(self) -> None:
        """Place définitivement le joueur en état de faillite.

        Entrées:
            Aucune.

        Sortie:
            None: Le joueur est marqué en faillite et son argent est ramené à zéro.
        """
        self.bankrupt = True
        self.cash = 0
        self.in_jail = False
        self.jail_turns = 0

    def __str__(self) -> str:
        """Construit une représentation textuelle courte de l'état du joueur.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            str: Texte contenant le nom, l'argent, la position et le nombre de biens.
        """
        return (
            f"{self.name} | argent={self.cash} | position={self.position} | "
            f"propriétés={len(self.properties)} | cartes={len(self.held_cards)}"
        )
