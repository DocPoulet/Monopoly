"""Options et variantes configurables avant le début d'une partie."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GameOptions:
    """Regroupe toutes les règles configurables d'une partie.

    Entrées:
        starting_cash (int): Argent initial donné à chaque joueur.
        go_salary (int): Somme reçue en passant par Départ.
        jail_fine (int): Prix de sortie volontaire ou obligatoire de prison.
        max_jail_turns (int): Nombre maximal de tentatives par les dés en prison.
        doubles_to_jail (int): Nombre de doubles consécutifs envoyant en prison.
        auctions_enabled (bool): Active les enchères des propriétés refusées.
        free_parking_bonus (int): Bonus fixe optionnel du Parc Gratuit.
        free_parking_card_pot (bool): Active la cagnotte alimentée par les paiements de cartes.
        turn_limit (int): Nombre maximal de tours de table, zéro signifiant aucune limite.
        property_price_percent (int): Pourcentage appliqué au prix des biens achetables.
        rent_percent (int): Pourcentage appliqué à tous les loyers.
        monopoly_required_for_building (bool): Exige le groupe complet pour construire.
        house_stock (int): Stock initial de maisons ; zéro signifie illimité.
        hotel_stock (int): Stock initial d'hôtels ; zéro signifie illimité.
        mortgages_enabled (bool): Autorise la création de nouvelles hypothèques.
        unmortgage_tax_percent (int): Intérêt appliqué aux levées et transferts d'hypothèque.
        transferred_mortgages (bool): Fait suivre ou non l'hypothèque lors d'un transfert.
        building_resale_percent (int): Pourcentage du coût rendu lors de la revente d'un bâtiment.
        automatic_rent (bool): Prélève automatiquement les loyers à l'arrivée.
        construction_anywhere (bool): Autorise la construction à tout moment ; sinon seulement juste après l'atterrissage.
        property_debt_payment (bool): Autorise la cession de biens à un joueur créancier pour réduire une dette.
        max_buildings_per_action (int): Nombre maximal de maisons achetables dans une même décision.

    Sortie:
        GameOptions: Profil de règles utilisé par le moteur pendant toute la partie.
    """

    starting_cash: int = 1500
    go_salary: int = 200
    jail_fine: int = 50
    max_jail_turns: int = 3
    doubles_to_jail: int = 3
    auctions_enabled: bool = True
    free_parking_bonus: int = 0
    free_parking_card_pot: bool = False
    turn_limit: int = 0
    property_price_percent: int = 100
    rent_percent: int = 100
    monopoly_required_for_building: bool = True
    house_stock: int = 32
    hotel_stock: int = 12
    mortgages_enabled: bool = True
    unmortgage_tax_percent: int = 10
    transferred_mortgages: bool = True
    building_resale_percent: int = 50
    automatic_rent: bool = True
    construction_anywhere: bool = True
    property_debt_payment: bool = False
    max_buildings_per_action: int = 4

    def validate(self) -> None:
        """Vérifie que toutes les règles personnalisées restent cohérentes.

        Entrées:
            Aucune autre que l'instance.

        Sortie:
            None: La méthode ne modifie pas l'instance.

        Lève:
            ValueError: Si une règle numérique est hors des limites acceptées.
        """
        if self.starting_cash <= 0:
            raise ValueError("L'argent de départ doit être strictement positif.")
        if self.go_salary < 0:
            raise ValueError("Le salaire du Départ ne peut pas être négatif.")
        if self.jail_fine < 0:
            raise ValueError("L'amende de prison ne peut pas être négative.")
        if not 1 <= self.max_jail_turns <= 20:
            raise ValueError("Les tentatives en prison doivent être comprises entre 1 et 20.")
        if not 1 <= self.doubles_to_jail <= 20:
            raise ValueError("Le seuil de doubles doit être compris entre 1 et 20.")
        if self.free_parking_bonus < 0:
            raise ValueError("Le bonus Parc Gratuit ne peut pas être négatif.")
        if self.turn_limit < 0:
            raise ValueError("La limite de tours ne peut pas être négative.")
        if not 1 <= self.property_price_percent <= 1000:
            raise ValueError("Le prix des propriétés doit être compris entre 1 % et 1000 %.")
        if not 0 <= self.rent_percent <= 1000:
            raise ValueError("Le prix des loyers doit être compris entre 0 % et 1000 %.")
        if self.house_stock < 0 or self.hotel_stock < 0:
            raise ValueError("Les stocks de bâtiments ne peuvent pas être négatifs.")
        if not 0 <= self.unmortgage_tax_percent <= 1000:
            raise ValueError("La taxe de déshypothèque doit être comprise entre 0 % et 1000 %.")
        if not 0 <= self.building_resale_percent <= 1000:
            raise ValueError("Le prix de revente doit être compris entre 0 % et 1000 %.")
        if not 1 <= self.max_buildings_per_action <= 4:
            raise ValueError("Le maximum de constructions par décision doit être compris entre 1 et 4.")

    @classmethod
    def classic(cls) -> "GameOptions":
        """Retourne explicitement le profil de règles classiques.

        Entrées:
            Aucune.

        Sortie:
            GameOptions: Profil standard complet.
        """
        return cls()

    @property
    def is_classic(self) -> bool:
        """Indique si toutes les règles correspondent au profil classique.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsque l'instance est identique au profil standard.
        """
        return self.to_dict() == self.classic().to_dict()

    def summary(self) -> str:
        """Construit un résumé compact du profil de règles actif.

        Entrées:
            Aucune.

        Sortie:
            str: Texte destiné à l'écran de préparation de partie.
        """
        if self.is_classic:
            return "Profil : Règles classiques"

        classic = self.classic()
        variants: list[str] = []
        pairs = (
            (self.starting_cash != classic.starting_cash, f"départ {self.starting_cash} $"),
            (self.go_salary != classic.go_salary, f"Départ +{self.go_salary} $"),
            (self.property_price_percent != 100, f"biens {self.property_price_percent} %"),
            (self.rent_percent != 100, f"loyers {self.rent_percent} %"),
            (not self.monopoly_required_for_building, "construction sans monopole"),
            (not self.automatic_rent, "loyer manuel"),
            (not self.construction_anywhere, "construction à l’atterrissage"),
            (not self.mortgages_enabled, "hypothèques désactivées"),
            (self.property_debt_payment, "paiement de dette en biens"),
            (self.max_buildings_per_action != 4, f"max {self.max_buildings_per_action} construction(s)"),
            (self.free_parking_card_pot, "cagnotte Parc Gratuit"),
            (not self.auctions_enabled, "enchères désactivées"),
            (bool(self.turn_limit), f"limite {self.turn_limit} tours"),
        )
        for changed, label in pairs:
            if changed:
                variants.append(label)
        preview = " • ".join(variants[:4])
        if len(variants) > 4:
            preview += f" • +{len(variants) - 4} autre(s)"
        return f"Profil : Personnalisé — {preview}"

    def to_dict(self) -> dict[str, Any]:
        """Sérialise toutes les règles dans un dictionnaire JSON.

        Entrées:
            Aucune.

        Sortie:
            dict[str, Any]: Valeurs primitives des règles.
        """
        return {
            "starting_cash": self.starting_cash,
            "go_salary": self.go_salary,
            "jail_fine": self.jail_fine,
            "max_jail_turns": self.max_jail_turns,
            "doubles_to_jail": self.doubles_to_jail,
            "auctions_enabled": self.auctions_enabled,
            "free_parking_bonus": self.free_parking_bonus,
            "free_parking_card_pot": self.free_parking_card_pot,
            "turn_limit": self.turn_limit,
            "property_price_percent": self.property_price_percent,
            "rent_percent": self.rent_percent,
            "monopoly_required_for_building": self.monopoly_required_for_building,
            "house_stock": self.house_stock,
            "hotel_stock": self.hotel_stock,
            "mortgages_enabled": self.mortgages_enabled,
            "unmortgage_tax_percent": self.unmortgage_tax_percent,
            "transferred_mortgages": self.transferred_mortgages,
            "building_resale_percent": self.building_resale_percent,
            "automatic_rent": self.automatic_rent,
            "construction_anywhere": self.construction_anywhere,
            "property_debt_payment": self.property_debt_payment,
            "max_buildings_per_action": self.max_buildings_per_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "GameOptions":
        """Reconstruit les règles depuis une sauvegarde en restant rétrocompatible.

        Entrées:
            data (dict[str, Any] | None): Données sauvegardées éventuelles.

        Sortie:
            GameOptions: Profil validé avec valeurs classiques pour les champs absents.
        """
        data = data or {}
        options = cls(
            starting_cash=int(data.get("starting_cash", 1500)),
            go_salary=int(data.get("go_salary", 200)),
            jail_fine=int(data.get("jail_fine", 50)),
            max_jail_turns=int(data.get("max_jail_turns", 3)),
            doubles_to_jail=int(data.get("doubles_to_jail", 3)),
            auctions_enabled=bool(data.get("auctions_enabled", True)),
            free_parking_bonus=int(data.get("free_parking_bonus", 0)),
            free_parking_card_pot=bool(data.get("free_parking_card_pot", False)),
            turn_limit=int(data.get("turn_limit", 0)),
            property_price_percent=int(data.get("property_price_percent", 100)),
            rent_percent=int(data.get("rent_percent", 100)),
            monopoly_required_for_building=bool(data.get("monopoly_required_for_building", True)),
            house_stock=int(data.get("house_stock", 32)),
            hotel_stock=int(data.get("hotel_stock", 12)),
            mortgages_enabled=bool(data.get("mortgages_enabled", True)),
            unmortgage_tax_percent=int(data.get("unmortgage_tax_percent", 10)),
            transferred_mortgages=bool(data.get("transferred_mortgages", True)),
            building_resale_percent=int(data.get("building_resale_percent", 50)),
            automatic_rent=bool(data.get("automatic_rent", True)),
            construction_anywhere=bool(data.get("construction_anywhere", True)),
            property_debt_payment=bool(data.get("property_debt_payment", False)),
            max_buildings_per_action=int(data.get("max_buildings_per_action", 4)),
        )
        options.validate()
        return options
