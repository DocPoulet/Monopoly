"""Menu intégré d'achat de bâtiments disponible uniquement après un atterrissage."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from monopoly.player import Player
from monopoly.properties import Property

if TYPE_CHECKING:
    from monopoly.game import Game


class LandingBuildOverlay(tk.Frame):
    """Propose maisons ou hôtel après l'atterrissage sur son propre terrain.

    Entrées:
        master (tk.Misc): Conteneur parent, généralement ``BoardView``.

    Sortie:
        LandingBuildOverlay: Menu superposé inspiré de la fiche d'achat d'une propriété.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit la fiche, la quantité de maisons et les boutons de décision.

        Entrées:
            master (tk.Misc): Conteneur graphique parent.

        Sortie:
            None: Le menu est créé puis masqué.
        """
        super().__init__(
            master,
            background="#DCE3E7",
            highlightbackground="#88969F",
            highlightthickness=2,
            padx=9,
            pady=9,
        )
        self.game: Game | None = None
        self.player: Player | None = None
        self.property: Property | None = None
        self.on_buy_houses: Callable[[int], None] | None = None
        self.on_buy_hotel: Callable[[], None] | None = None
        self.on_pass: Callable[[], None] | None = None

        self.card = tk.Frame(
            self,
            background="#FFFFFF",
            highlightbackground="#29323A",
            highlightthickness=2,
        )
        self.card.pack(fill="both", expand=True)

        self.header = tk.Frame(self.card, background="#2F7D52", height=70)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        tk.Label(
            self.header,
            text="CONSTRUCTION APRÈS ATTERRISSAGE",
            background="#2F7D52",
            foreground="#FFFFFF",
            font=("Arial", 9, "bold"),
        ).pack(pady=(9, 0))

        self.name_label = tk.Label(
            self.header,
            text="",
            background="#2F7D52",
            foreground="#FFFFFF",
            font=("Arial", 16, "bold"),
        )
        self.name_label.pack(pady=(2, 7))

        body = tk.Frame(self.card, background="#FFFFFF", padx=18, pady=14)
        body.pack(fill="both", expand=True)

        self.state_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#27313A",
            font=("Arial", 10, "bold"),
            justify="center",
        )
        self.state_label.pack(fill="x", pady=(0, 8))

        self.rent_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#55616A",
            font=("Arial", 9),
            justify="center",
        )
        self.rent_label.pack(fill="x", pady=(0, 10))

        self.house_frame = ttk.LabelFrame(body, text="Maisons", padding=8)
        self.house_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            self.house_frame,
            text="Nombre de maisons à acheter maintenant :",
        ).grid(row=0, column=0, sticky="w")

        self.quantity_var = tk.StringVar(value="1")
        self.quantity_combo = ttk.Combobox(
            self.house_frame,
            textvariable=self.quantity_var,
            state="readonly",
            width=8,
        )
        self.quantity_combo.grid(row=0, column=1, sticky="e", padx=(10, 0))
        self.house_frame.columnconfigure(0, weight=1)

        self.house_cost_label = ttk.Label(
            self.house_frame,
            text="",
            style="Muted.TLabel",
        )
        self.house_cost_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        self.quantity_combo.bind("<<ComboboxSelected>>", self._quantity_changed)

        self.buy_houses_button = ttk.Button(
            body,
            text="Acheter",
            style="Primary.TButton",
            command=self._buy_houses,
        )
        self.buy_houses_button.pack(fill="x", pady=(0, 6))

        self.buy_hotel_button = ttk.Button(
            body,
            text="Acheter 1 hôtel",
            style="Primary.TButton",
            command=self._buy_hotel,
        )
        self.buy_hotel_button.pack(fill="x", pady=(0, 6))

        ttk.Button(
            body,
            text="Passer",
            command=self._pass,
        ).pack(fill="x")

        self.place_forget()

    def show(
        self,
        game: "Game",
        player: Player,
        property_: Property,
        on_buy_houses: Callable[[int], None],
        on_buy_hotel: Callable[[], None],
        on_pass: Callable[[], None],
    ) -> None:
        """Affiche les achats légalement disponibles pour cet atterrissage précis.

        Entrées:
            game (Game): Partie contenant règles, banque et argent.
            player (Player): Joueur ayant atterri.
            property_ (Property): Terrain atteint et possédé.
            on_buy_houses (Callable[[int], None]): Callback d'achat groupé de maisons.
            on_buy_hotel (Callable[[], None]): Callback d'achat d'un hôtel.
            on_pass (Callable[[], None]): Callback permettant de ne rien construire.

        Sortie:
            None: Le menu apparaît avec uniquement les choix légaux.
        """
        self.game = game
        self.player = player
        self.property = property_
        self.on_buy_houses = on_buy_houses
        self.on_buy_hotel = on_buy_hotel
        self.on_pass = on_pass

        self.name_label.configure(text=property_.name.upper())

        if property_.hotel:
            development = "Hôtel"
        elif property_.houses:
            development = f"{property_.houses} maison(s)"
        else:
            development = "Aucun bâtiment"

        self.state_label.configure(
            text=(
                f"{player.name} vient de tomber sur cette propriété\n"
                f"État actuel : {development} • argent : {player.cash} $"
            )
        )
        self.rent_label.configure(
            text=f"Loyer actuel : {game.rules.calculate_rent(property_, 0)} $"
        )

        max_houses = game.rules.max_landing_house_purchase(player, property_)
        can_hotel = game.rules.can_build_hotel(player, property_)

        if max_houses > 0:
            values = [str(number) for number in range(1, max_houses + 1)]
            self.quantity_combo.configure(values=values)
            self.quantity_var.set(values[0])
            self.house_frame.pack(fill="x", pady=(0, 8))
            self.buy_houses_button.pack(fill="x", pady=(0, 6))
            self.buy_hotel_button.pack_forget()
            self._quantity_changed(None)
        elif can_hotel:
            self.house_frame.pack_forget()
            self.buy_houses_button.pack_forget()
            self.buy_hotel_button.configure(
                text=f"Acheter 1 hôtel • {property_.house_cost} $"
            )
            self.buy_hotel_button.pack(fill="x", pady=(0, 6))
        else:
            self.house_frame.pack_forget()
            self.buy_houses_button.pack_forget()
            self.buy_hotel_button.pack_forget()

        self.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=430,
        )
        self.lift()

    def hide(self) -> None:
        """Masque le menu et efface les références de décision.

        Entrées:
            Aucune.

        Sortie:
            None: Le menu disparaît du plateau.
        """
        self.place_forget()
        self.game = None
        self.player = None
        self.property = None
        self.on_buy_houses = None
        self.on_buy_hotel = None
        self.on_pass = None

    def _quantity_changed(self, event: tk.Event | None) -> None:
        """Met à jour le coût total affiché pour la quantité choisie.

        Entrées:
            event (tk.Event | None): Événement de combobox, facultatif en test.

        Sortie:
            None: Le coût et le libellé du bouton sont recalculés.
        """
        if self.property is None:
            return
        try:
            quantity = int(self.quantity_var.get())
        except ValueError:
            quantity = 1
        total = quantity * self.property.house_cost
        self.house_cost_label.configure(
            text=(
                f"{self.property.house_cost} $ par maison • "
                f"total : {total} $ • maximum configuré : "
                f"{self.game.options.max_buildings_per_action if self.game is not None else 4} maison(s)"
            )
        )
        label = "maison" if quantity == 1 else "maisons"
        self.buy_houses_button.configure(
            text=f"Acheter {quantity} {label} • {total} $"
        )

    def _buy_houses(self) -> None:
        """Transmet la quantité de maisons sélectionnée au contrôleur.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit une quantité respectant le maximum configuré.
        """
        if self.on_buy_houses is None:
            return
        try:
            quantity = int(self.quantity_var.get())
        except ValueError:
            return
        self.on_buy_houses(quantity)

    def _buy_hotel(self) -> None:
        """Demande l'achat d'un unique hôtel.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback hôtel est exécuté.
        """
        if self.on_buy_hotel is not None:
            self.on_buy_hotel()

    def _pass(self) -> None:
        """Renonce à construire pendant cet atterrissage.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback de passage est exécuté.
        """
        if self.on_pass is not None:
            self.on_pass()
