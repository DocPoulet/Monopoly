"""Représente les ressources matérielles détenues par la banque."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Bank:
    """Conserve le stock de maisons et d'hôtels disponible à la construction.

    Entrées:
        house_limit (int): Stock maximal de maisons ; zéro signifie illimité.
        hotel_limit (int): Stock maximal d'hôtels ; zéro signifie illimité.
        houses_available (int | None): Stock courant optionnel de maisons.
        hotels_available (int | None): Stock courant optionnel d'hôtels.

    Sortie:
        Bank: Gestionnaire configurable du stock de bâtiments de la partie.
    """

    MAX_HOUSES: ClassVar[int] = 32
    MAX_HOTELS: ClassVar[int] = 12

    house_limit: int = MAX_HOUSES
    hotel_limit: int = MAX_HOTELS
    houses_available: int | None = field(default=None)
    hotels_available: int | None = field(default=None)

    def __post_init__(self) -> None:
        """Initialise les stocks courants à partir des limites configurées.

        Entrées:
            Aucune autre que les champs du dataclass.

        Sortie:
            None: Les stocks ``None`` prennent la valeur de leur limite, ou zéro en illimité.
        """
        if self.house_limit < 0 or self.hotel_limit < 0:
            raise ValueError("Les limites de bâtiments ne peuvent pas être négatives.")
        if self.houses_available is None:
            self.houses_available = self.house_limit if self.house_limit > 0 else 0
        if self.hotels_available is None:
            self.hotels_available = self.hotel_limit if self.hotel_limit > 0 else 0

    @property
    def houses_unlimited(self) -> bool:
        """Indique si les maisons sont disponibles sans limite de stock.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsque ``house_limit`` vaut zéro.
        """
        return self.house_limit == 0

    @property
    def hotels_unlimited(self) -> bool:
        """Indique si les hôtels sont disponibles sans limite de stock.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsque ``hotel_limit`` vaut zéro.
        """
        return self.hotel_limit == 0

    def can_supply_houses(self, count: int = 1) -> bool:
        """Vérifie que la banque peut fournir le nombre de maisons demandé.

        Entrées:
            count (int): Nombre de maisons demandées.

        Sortie:
            bool: ``True`` en stock suffisant ou lorsque le stock est illimité.
        """
        return count >= 0 and (self.houses_unlimited or int(self.houses_available) >= count)

    def can_supply_hotels(self, count: int = 1) -> bool:
        """Vérifie que la banque peut fournir le nombre d'hôtels demandé.

        Entrées:
            count (int): Nombre d'hôtels demandés.

        Sortie:
            bool: ``True`` en stock suffisant ou lorsque le stock est illimité.
        """
        return count >= 0 and (self.hotels_unlimited or int(self.hotels_available) >= count)

    def take_houses(self, count: int = 1) -> bool:
        """Retire des maisons du stock lorsqu'elles sont placées sur le plateau.

        Entrées:
            count (int): Nombre de maisons à sortir de la banque.

        Sortie:
            bool: ``True`` si l'opération est autorisée.
        """
        if count < 0 or not self.can_supply_houses(count):
            return False
        if not self.houses_unlimited:
            self.houses_available = int(self.houses_available) - count
        return True

    def return_houses(self, count: int = 1) -> None:
        """Rend des maisons à la banque après vente ou conversion.

        Entrées:
            count (int): Nombre de maisons retournées.

        Sortie:
            None: Le stock limité est augmenté ; le stock illimité reste symbolique.

        Lève:
            ValueError: Si le nombre est négatif ou dépasse la limite configurée.
        """
        if count < 0:
            raise ValueError("Le nombre de maisons rendues ne peut pas être négatif.")
        if self.houses_unlimited:
            return
        if int(self.houses_available) + count > self.house_limit:
            raise ValueError("Le stock de maisons dépasserait sa limite configurée.")
        self.houses_available = int(self.houses_available) + count

    def take_hotels(self, count: int = 1) -> bool:
        """Retire des hôtels du stock lorsqu'ils sont placés sur le plateau.

        Entrées:
            count (int): Nombre d'hôtels à sortir de la banque.

        Sortie:
            bool: ``True`` si l'opération est autorisée.
        """
        if count < 0 or not self.can_supply_hotels(count):
            return False
        if not self.hotels_unlimited:
            self.hotels_available = int(self.hotels_available) - count
        return True

    def return_hotels(self, count: int = 1) -> None:
        """Rend des hôtels à la banque après vente ou retrait.

        Entrées:
            count (int): Nombre d'hôtels retournés.

        Sortie:
            None: Le stock limité est augmenté ; le stock illimité reste symbolique.

        Lève:
            ValueError: Si le nombre est négatif ou dépasse la limite configurée.
        """
        if count < 0:
            raise ValueError("Le nombre d'hôtels rendus ne peut pas être négatif.")
        if self.hotels_unlimited:
            return
        if int(self.hotels_available) + count > self.hotel_limit:
            raise ValueError("Le stock d'hôtels dépasserait sa limite configurée.")
        self.hotels_available = int(self.hotels_available) + count

    def stock_text(self) -> str:
        """Construit un résumé court du stock de bâtiments.

        Entrées:
            Aucune autre que l'état de la banque.

        Sortie:
            str: Texte lisible donnant les stocks restants ou leur caractère illimité.
        """
        houses = (
            "maisons illimitées"
            if self.houses_unlimited
            else f"{self.houses_available}/{self.house_limit} maisons"
        )
        hotels = (
            "hôtels illimités"
            if self.hotels_unlimited
            else f"{self.hotels_available}/{self.hotel_limit} hôtels"
        )
        return f"{houses} • {hotels}"
