"""Fiche de propriété intégrée directement au plateau graphique."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property, Railroad, Utility


PROPERTY_COLORS = {
    "brown": "#8B5A2B",
    "light_blue": "#79CFE8",
    "pink": "#D95FA6",
    "orange": "#F39C12",
    "red": "#E74C3C",
    "yellow": "#F4D03F",
    "green": "#27AE60",
    "dark_blue": "#3156A6",
}


class PropertyCardOverlay(tk.Frame):
    """Affiche une fiche de bien au-dessus du plateau sans créer de nouvelle fenêtre.

    Entrées:
        master (tk.Misc): Widget parent, généralement ``BoardView``.

    Sortie:
        PropertyCardOverlay: Panneau cachable pouvant proposer Achat et Enchères.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit la structure fixe de la fiche et ses boutons de décision.

        Entrées:
            master (tk.Misc): Conteneur graphique qui recevra la fiche.

        Sortie:
            None: La fiche est créée mais reste cachée jusqu'à ``show``.
        """
        super().__init__(
            master,
            background="#DCE3E7",
            highlightbackground="#9AA7B0",
            highlightthickness=1,
            padx=8,
            pady=8,
        )
        self.player: Player | None = None
        self.space: OwnableSpace | None = None
        self.on_buy: Callable[[], None] | None = None
        self.on_auction: Callable[[], None] | None = None

        self.card = tk.Frame(
            self,
            background="#FFFFFF",
            highlightbackground="#29323A",
            highlightthickness=2,
        )
        self.card.pack(fill="both", expand=True)

        self.header = tk.Frame(self.card, background="#546E7A", height=70)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.type_label = tk.Label(
            self.header,
            text="",
            background="#546E7A",
            foreground="#FFFFFF",
            font=("Arial", 9, "bold"),
        )
        self.type_label.pack(pady=(8, 0))

        self.name_label = tk.Label(
            self.header,
            text="",
            background="#546E7A",
            foreground="#FFFFFF",
            font=("Arial", 16, "bold"),
        )
        self.name_label.pack(pady=(1, 7))

        self.body = tk.Frame(self.card, background="#FFFFFF", padx=18, pady=12)
        self.body.pack(fill="both", expand=True)

        self.price_label = tk.Label(
            self.body,
            text="",
            background="#FFFFFF",
            foreground="#1F2933",
            font=("Arial", 11, "bold"),
        )
        self.price_label.pack(pady=(0, 7))

        self.details_frame = tk.Frame(self.body, background="#FFFFFF")
        self.details_frame.pack(fill="x")

        self.mortgage_label = tk.Label(
            self.body,
            text="",
            background="#FFFFFF",
            foreground="#65717A",
            font=("Arial", 8),
        )
        self.mortgage_label.pack(pady=(8, 2))

        self.cash_label = tk.Label(
            self.body,
            text="",
            background="#FFFFFF",
            foreground="#27313A",
            font=("Arial", 9, "bold"),
        )
        self.cash_label.pack(pady=(2, 8))

        self.button_row = ttk.Frame(self.body)
        self.button_row.pack(fill="x", pady=(4, 0))
        self.button_row.columnconfigure(0, weight=1)
        self.button_row.columnconfigure(1, weight=1)

        self.buy_button = ttk.Button(
            self.button_row,
            text="Acheter",
            style="Primary.TButton",
            command=self._buy,
        )
        self.buy_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.auction_button = ttk.Button(
            self.button_row,
            text="Enchères",
            command=self._auction,
        )
        self.auction_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.close_button = ttk.Button(
            self.button_row,
            text="Fermer",
            command=self._close_info,
        )
        self.close_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.close_button.grid_remove()
        self.on_close: Callable[[], None] | None = None

    def _populate_space(self, space: OwnableSpace) -> None:
        """Remplit la fiche avec les informations financières d'un bien.

        Entrées:
            space (OwnableSpace): Terrain, gare ou compagnie à représenter.

        Sortie:
            None: L'en-tête, le prix, l'hypothèque et le barème sont actualisés.
        """
        header_color = self._header_color(space)
        self.header.configure(background=header_color)
        self.type_label.configure(
            text=self._type_title(space),
            background=header_color,
        )
        self.name_label.configure(
            text=space.name.upper(),
            background=header_color,
        )
        self.price_label.configure(text=f"PRIX D'ACHAT : {space.price} $")
        self.mortgage_label.configure(
            text=f"Valeur hypothécaire : {space.mortgage_value} $"
        )

        for child in self.details_frame.winfo_children():
            child.destroy()

        for label, value, bold in self._display_detail_rows(space):
            row = tk.Frame(self.details_frame, background="#FFFFFF")
            row.pack(fill="x", pady=1)
            font = ("Arial", 8, "bold" if bold else "normal")
            tk.Label(
                row,
                text=label,
                background="#FFFFFF",
                foreground="#46515C",
                font=font,
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                background="#FFFFFF",
                foreground="#1F2933",
                font=font,
            ).pack(side="right")

    def show(
        self,
        player: Player,
        space: OwnableSpace,
        on_buy: Callable[[], None],
        on_auction: Callable[[], None],
    ) -> None:
        """Charge un bien et affiche sa fiche au centre du plateau.

        Entrées:
            player (Player): Joueur qui doit prendre la décision d'achat.
            space (OwnableSpace): Bien libre concerné.
            on_buy (Callable[[], None]): Action exécutée au clic sur Acheter.
            on_auction (Callable[[], None]): Action exécutée au clic sur Enchères.

        Sortie:
            None: La fiche devient visible et interactive.
        """
        self.player = player
        self.space = space
        self.on_buy = on_buy
        self.on_auction = on_auction

        self._populate_space(space)
        self.cash_label.configure(text=f"{player.name} possède {player.cash} $")
        self.buy_button.configure(text=f"Acheter • {space.price} $")
        self.buy_button.state(
            ["!disabled"] if player.can_afford(space.price) else ["disabled"]
        )
        self.buy_button.grid()
        self.auction_button.grid()
        self.close_button.grid_remove()
        self.button_row.pack(fill="x", pady=(4, 0))

        self.place(relx=0.5, rely=0.50, anchor="center", width=390)
        self.lift()

    def show_info(
        self,
        space: OwnableSpace,
        on_close: Callable[[], None],
    ) -> None:
        """Affiche une fiche en lecture seule après un clic direct sur le plateau.

        Entrées:
            space (OwnableSpace): Bien à consulter.
            on_close (Callable[[], None]): Callback appelé lorsque la fiche est fermée.

        Sortie:
            None: La fiche apparaît avec propriétaire, état et loyer courant.
        """
        self.player = None
        self.space = space
        self.on_buy = None
        self.on_auction = None
        self.on_close = on_close
        self._populate_space(space)

        if space.owner is None:
            status = f"Bien libre • prix : {space.price} $"
        elif space.mortgaged:
            status = (
                f"Propriétaire : {space.owner.name} • HYPOTHÉQUÉ • "
                f"levée : {self.master.game.rules.unmortgage_cost(space)} $"
            )
        else:
            if isinstance(space, Utility):
                count = sum(
                    1
                    for item in space.owner.properties
                    if isinstance(item, Utility)
                )
                current_multiplier = space.multipliers[1] if count >= 2 else space.multipliers[0]
                current_rent = (
                    f"{current_multiplier}× dés"
                    + (
                        ""
                        if self.master.game.options.rent_percent == 100
                        else f" × {self.master.game.options.rent_percent} %"
                    )
                )
            else:
                current_rent = f"{self.master.game.rules.calculate_rent(space, 0)} $"
            status = (
                f"Propriétaire : {space.owner.name} • loyer actuel : {current_rent}"
            )

        if isinstance(space, Property):
            if space.hotel:
                status += " • hôtel"
            elif space.houses:
                status += f" • {space.houses} maison(s)"

        self.cash_label.configure(text=status)
        self.buy_button.grid_remove()
        self.auction_button.grid_remove()
        self.close_button.grid()
        self.button_row.pack(fill="x", pady=(4, 0))
        self.place(relx=0.5, rely=0.50, anchor="center", width=410)
        self.lift()

    def show_for_auction(
        self,
        space: OwnableSpace,
        relx: float = 0.30,
        width: int = 300,
    ) -> None:
        """Affiche la même fiche en lecture seule à côté d'une enchère.

        Entrées:
            space (OwnableSpace): Bien actuellement mis aux enchères.
            relx (float): Position horizontale relative du centre de la fiche.
            width (int): Largeur de la fiche en pixels pendant l'enchère.

        Sortie:
            None: La fiche apparaît sans boutons Achat/Enchères ni joueur acheteur.
        """
        self.player = None
        self.space = space
        self.on_buy = None
        self.on_auction = None
        self._populate_space(space)
        self.cash_label.configure(text="PROPRIÉTÉ AUX ENCHÈRES")
        self.close_button.grid_remove()
        self.button_row.pack_forget()
        self.place(relx=relx, rely=0.50, anchor="center", width=width)
        self.lift()

    def hide(self) -> None:
        """Masque la fiche et oublie les callbacks associés à l'ancienne décision.

        Entrées:
            Aucune.

        Sortie:
            None: La fiche disparaît du plateau et ses références sont réinitialisées.
        """
        self.place_forget()
        self.player = None
        self.space = None
        self.on_buy = None
        self.on_auction = None
        self.on_close = None

    def _close_info(self) -> None:
        """Ferme une fiche de consultation ouverte depuis le plateau.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback de fermeture est exécuté s'il existe.
        """
        callback = self.on_close
        self.hide()
        if callback is not None:
            callback()

    def _buy(self) -> None:
        """Déclenche le callback d'achat fourni par la fenêtre de jeu.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback d'achat est exécuté s'il existe.
        """
        if self.on_buy is not None:
            self.on_buy()

    def _auction(self) -> None:
        """Déclenche le callback d'enchère fourni par la fenêtre de jeu.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback d'enchère est exécuté s'il existe.
        """
        if self.on_auction is not None:
            self.on_auction()

    @staticmethod
    def _header_color(space: OwnableSpace) -> str:
        """Retourne la couleur d'en-tête correspondant au type du bien.

        Entrées:
            space (OwnableSpace): Bien à représenter.

        Sortie:
            str: Couleur hexadécimale de l'en-tête.
        """
        if isinstance(space, Property):
            return PROPERTY_COLORS.get(space.color_group, "#546E7A")
        if isinstance(space, Railroad):
            return "#454B50"
        return "#2F7D8C"

    @staticmethod
    def _type_title(space: OwnableSpace) -> str:
        """Retourne le nom de catégorie affiché au-dessus du nom du bien.

        Entrées:
            space (OwnableSpace): Bien à identifier.

        Sortie:
            str: ``TERRAIN``, ``GARE`` ou ``COMPAGNIE``.
        """
        if isinstance(space, Property):
            return "TERRAIN"
        if isinstance(space, Railroad):
            return "GARE"
        return "COMPAGNIE"



    def _display_detail_rows(self, space: OwnableSpace) -> list[tuple[str, str, bool]]:
        """Produit le barème visible après application du pourcentage de loyer.

        Entrées:
            space (OwnableSpace): Bien dont le barème doit être affiché.

        Sortie:
            list[tuple[str, str, bool]]: Lignes ajustées aux règles de la partie.
        """
        game = self.master.game
        if isinstance(space, Property):
            rows: list[tuple[str, str, bool]] = []
            if space.owner is not None:
                current_rent = game.rules.calculate_rent(space, 0)
                current_suffix = " • HYPOTHÉQUÉ" if space.mortgaged else ""
                rows.append(
                    (
                        "LOYER ACTUEL",
                        f"{current_rent} ${current_suffix}",
                        True,
                    )
                )

            current_level = space.development_level
            rows.extend(
                [
                    ("Loyer sans maison", f"{game.rules.scale_rent(space.base_rent)} $", current_level == 0),
                    ("Avec 1 maison", f"{game.rules.scale_rent(space.house_rents[0])} $", current_level == 1),
                    ("Avec 2 maisons", f"{game.rules.scale_rent(space.house_rents[1])} $", current_level == 2),
                    ("Avec 3 maisons", f"{game.rules.scale_rent(space.house_rents[2])} $", current_level == 3),
                    ("Avec 4 maisons", f"{game.rules.scale_rent(space.house_rents[3])} $", current_level == 4),
                    ("Avec hôtel", f"{game.rules.scale_rent(space.hotel_rent)} $", current_level == 5),
                    ("Prix d'une maison", f"{space.house_cost} $", False),
                ]
            )
            return rows
        if isinstance(space, Railroad):
            return [
                (f"{index} gare" if index == 1 else f"{index} gares", f"{game.rules.scale_rent(value)} $", index == 4)
                for index, value in enumerate(space.rent_values, start=1)
            ]
        if isinstance(space, Utility):
            suffix = "" if game.options.rent_percent == 100 else f" × {game.options.rent_percent} %"
            return [
                ("1 compagnie", f"{space.multipliers[0]} × le total des dés{suffix}", False),
                ("2 compagnies", f"{space.multipliers[1]} × le total des dés{suffix}", True),
            ]
        return []

    @staticmethod
    def _detail_rows(space: OwnableSpace) -> list[tuple[str, str, bool]]:
        """Produit les lignes financières classiques utilisées par les tests et helpers.

        Entrées:
            space (OwnableSpace): Terrain, gare ou compagnie.

        Sortie:
            list[tuple[str, str, bool]]: Libellé, valeur classique et indicateur de gras.
        """
        if isinstance(space, Property):
            return [
                ("Loyer", f"{space.base_rent} $", True),
                ("Avec 1 maison", f"{space.house_rents[0]} $", False),
                ("Avec 2 maisons", f"{space.house_rents[1]} $", False),
                ("Avec 3 maisons", f"{space.house_rents[2]} $", False),
                ("Avec 4 maisons", f"{space.house_rents[3]} $", False),
                ("Avec hôtel", f"{space.hotel_rent} $", True),
                ("Prix d'une maison", f"{space.house_cost} $", False),
            ]
        if isinstance(space, Railroad):
            return [
                (f"{index} gare" if index == 1 else f"{index} gares", f"{value} $", index == 4)
                for index, value in enumerate(space.rent_values, start=1)
            ]
        if isinstance(space, Utility):
            return [
                ("1 compagnie", f"{space.multipliers[0]} × le total des dés", False),
                ("2 compagnies", f"{space.multipliers[1]} × le total des dés", True),
            ]
        return []

