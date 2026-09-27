"""Panneau d'échange intégré au centre du plateau."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from monopoly.player import Player
from monopoly.properties import OwnableSpace
from monopoly.trade import TradeOffer, TradeResult

if TYPE_CHECKING:
    from monopoly.game import Game


class TradeOverlay(ttk.Frame):
    """Permet de composer et exécuter un échange sans ouvrir de fenêtre secondaire.

    Entrées:
        master (tk.Misc): Vue du plateau sur laquelle le panneau est superposé.

    Sortie:
        TradeOverlay: Panneau masqué jusqu'à l'appel de ``show``.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit les sélecteurs d'argent, biens et cartes des deux joueurs.

        Entrées:
            master (tk.Misc): Conteneur parent.

        Sortie:
            None: Le panneau est créé puis immédiatement masqué.
        """
        super().__init__(
            master,
            padding=0,
            relief="solid",
            borderwidth=2,
        )
        self.game: Game | None = None
        self.initiator: Player | None = None
        self.partner: Player | None = None
        self.on_finished: Callable[[TradeResult], None] | None = None
        self.on_cancel: Callable[[], None] | None = None

        self.partner_var = tk.StringVar()
        self.left_cash_var = tk.StringVar(value="0")
        self.right_cash_var = tk.StringVar(value="0")

        header = tk.Frame(self, background="#455A64", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="ÉCHANGE ENTRE JOUEURS",
            background="#455A64",
            foreground="#FFFFFF",
            font=("Arial", 16, "bold"),
        ).pack(pady=(10, 0))
        self.subtitle_label = tk.Label(
            header,
            text="",
            background="#455A64",
            foreground="#DDE5E8",
            font=("Arial", 9),
        )
        self.subtitle_label.pack()

        body = tk.Frame(self, background="#FFFFFF", padx=14, pady=12)
        body.pack(fill="both", expand=True)

        partner_row = tk.Frame(body, background="#FFFFFF")
        partner_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            partner_row,
            text="Partenaire :",
            background="#FFFFFF",
            foreground="#34434D",
            font=("Arial", 10, "bold"),
        ).pack(side="left")
        self.partner_combo = ttk.Combobox(
            partner_row,
            textvariable=self.partner_var,
            state="readonly",
            width=22,
        )
        self.partner_combo.pack(side="left", padx=(8, 0))
        self.partner_combo.bind("<<ComboboxSelected>>", self._partner_changed)

        columns = tk.Frame(body, background="#FFFFFF")
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=1)
        columns.columnconfigure(1, weight=1)

        self.left_frame = self._build_side(columns, 0)
        self.right_frame = self._build_side(columns, 1)

        self.error_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#B13B3B",
            wraplength=680,
            justify="center",
            font=("Arial", 9, "bold"),
        )
        self.error_label.pack(fill="x", pady=(8, 2))

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(8, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        ttk.Button(
            buttons,
            text="Annuler",
            command=self._cancel,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(
            buttons,
            text="Effectuer l'échange",
            style="Primary.TButton",
            command=self._execute,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.place_forget()

    def _build_side(self, parent: tk.Misc, column: int) -> ttk.Frame:
        """Construit une colonne d'actifs proposée par l'un des deux joueurs.

        Entrées:
            parent (tk.Misc): Conteneur des deux colonnes.
            column (int): Colonne de grille, zéro pour l'initiateur ou un pour le partenaire.

        Sortie:
            ttk.Frame: Colonne contenant argent, propriétés et cartes sélectionnables.
        """
        frame = ttk.Frame(parent, padding=8)
        frame.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0, 6) if column == 0 else (6, 0),
        )

        title = ttk.Label(frame, text="", font=("Arial", 12, "bold"))
        title.pack(anchor="w")

        cash_row = ttk.Frame(frame)
        cash_row.pack(fill="x", pady=(7, 5))
        ttk.Label(cash_row, text="Argent offert :").pack(side="left")
        cash_var = self.left_cash_var if column == 0 else self.right_cash_var
        cash_entry = ttk.Entry(cash_row, textvariable=cash_var, width=10, justify="right")
        cash_entry.pack(side="right")

        ttk.Label(frame, text="Propriétés :").pack(anchor="w", pady=(5, 2))
        property_list = tk.Listbox(
            frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=7,
            background="#F8FAFB",
        )
        property_list.pack(fill="both", expand=True)

        ttk.Label(frame, text="Cartes conservées :").pack(anchor="w", pady=(7, 2))
        card_list = tk.Listbox(
            frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=3,
            background="#F8FAFB",
        )
        card_list.pack(fill="x")

        if column == 0:
            self.left_title = title
            self.left_property_list = property_list
            self.left_card_list = card_list
        else:
            self.right_title = title
            self.right_property_list = property_list
            self.right_card_list = card_list

        return frame

    def show(
        self,
        game: "Game",
        initiator: Player,
        on_finished: Callable[[TradeResult], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Affiche le panneau et sélectionne le premier partenaire actif disponible.

        Entrées:
            game (Game): Partie courante.
            initiator (Player): Joueur dont c'est le tour et qui ouvre l'échange.
            on_finished (Callable[[TradeResult], None]): Callback après échange réussi.
            on_cancel (Callable[[], None]): Callback lorsque le panneau est annulé.

        Sortie:
            None: Le panneau devient visible et ses listes sont remplies.
        """
        self.game = game
        self.initiator = initiator
        self.on_finished = on_finished
        self.on_cancel = on_cancel
        self.left_cash_var.set("0")
        self.right_cash_var.set("0")
        self.error_label.configure(text="")

        partners = [
            player
            for player in game.active_players
            if player is not initiator
        ]
        self.partner_combo["values"] = [player.name for player in partners]

        if partners:
            self.partner = partners[0]
            self.partner_var.set(partners[0].name)
        else:
            self.partner = None
            self.partner_var.set("")

        self.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.76, relheight=0.72)
        self.lift()
        self._refresh_lists()

    def hide(self) -> None:
        """Masque le panneau et oublie l'échange en cours.

        Entrées:
            Aucune.

        Sortie:
            None: Les références temporaires et sélections sont réinitialisées.
        """
        self.place_forget()
        self.game = None
        self.initiator = None
        self.partner = None
        self.on_finished = None
        self.on_cancel = None
        self.partner_var.set("")
        self.left_cash_var.set("0")
        self.right_cash_var.set("0")

    def _partner_changed(self, event: tk.Event) -> None:
        """Change le partenaire selon la sélection du menu déroulant.

        Entrées:
            event (tk.Event): Événement de sélection du ``Combobox``.

        Sortie:
            None: Le partenaire et les listes de droite sont actualisés.
        """
        if self.game is None:
            return

        name = self.partner_var.get()
        self.partner = next(
            (
                player
                for player in self.game.active_players
                if player.name == name and player is not self.initiator
            ),
            None,
        )
        self.right_cash_var.set("0")
        self.error_label.configure(text="")
        self._refresh_lists()

    @staticmethod
    def _asset_label(space: OwnableSpace) -> str:
        """Construit le texte affiché pour un bien dans une liste d'échange.

        Entrées:
            space (OwnableSpace): Bien à décrire.

        Sortie:
            str: Nom accompagné de son état hypothécaire éventuel.
        """
        suffix = " [HYP.]" if space.mortgaged else ""
        return f"{space.name}{suffix}"

    @staticmethod
    def _card_label(card: object) -> str:
        """Construit un libellé court pour une carte conservée.

        Entrées:
            card (object): Carte détenue par le joueur.

        Sortie:
            str: Texte lisible utilisé dans la liste.
        """
        deck_name = getattr(card, "deck_name", "")
        if deck_name == "chance":
            return "Sortie de prison — Chance"
        if deck_name == "community_chest":
            return "Sortie de prison — Caisse"
        return getattr(card, "text", type(card).__name__)

    def _fill_player_assets(
        self,
        player: Player | None,
        title: ttk.Label,
        property_list: tk.Listbox,
        card_list: tk.Listbox,
    ) -> None:
        """Remplit une colonne avec le patrimoine sélectionnable d'un joueur.

        Entrées:
            player (Player | None): Joueur affiché ou ``None``.
            title (ttk.Label): Titre de la colonne.
            property_list (tk.Listbox): Liste des biens.
            card_list (tk.Listbox): Liste des cartes.

        Sortie:
            None: Les widgets sont vidés puis reconstruits.
        """
        property_list.delete(0, tk.END)
        card_list.delete(0, tk.END)

        if player is None:
            title.configure(text="Aucun joueur")
            return

        title.configure(text=f"{player.name} • {player.cash} $")

        for space in sorted(player.properties, key=lambda item: item.index):
            property_list.insert(tk.END, self._asset_label(space))

        for card in player.held_cards:
            card_list.insert(tk.END, self._card_label(card))

    def _refresh_lists(self) -> None:
        """Actualise les deux colonnes à partir des joueurs sélectionnés.

        Entrées:
            Aucune autre que l'état du panneau.

        Sortie:
            None: Titres, propriétés et cartes sont synchronisés.
        """
        self._fill_player_assets(
            self.initiator,
            self.left_title,
            self.left_property_list,
            self.left_card_list,
        )
        self._fill_player_assets(
            self.partner,
            self.right_title,
            self.right_property_list,
            self.right_card_list,
        )

        if self.initiator is not None and self.partner is not None:
            self.subtitle_label.configure(
                text=f"{self.initiator.name} ↔ {self.partner.name}"
            )
        else:
            self.subtitle_label.configure(text="Aucun partenaire disponible")

    @staticmethod
    def _selected_items(items: list[object], listbox: tk.Listbox) -> list[object]:
        """Traduit les index sélectionnés d'une liste graphique vers les objets réels.

        Entrées:
            items (list[object]): Objets dans le même ordre que le ``Listbox``.
            listbox (tk.Listbox): Liste contenant les sélections utilisateur.

        Sortie:
            list[object]: Sous-ensemble sélectionné dans l'ordre d'origine.
        """
        return [
            items[index]
            for index in listbox.curselection()
            if 0 <= index < len(items)
        ]

    @staticmethod
    def _parse_cash(value: str) -> int | None:
        """Convertit une saisie d'argent en entier positif ou nul.

        Entrées:
            value (str): Texte saisi dans un champ d'argent.

        Sortie:
            int | None: Entier valide ou ``None`` en cas de saisie incorrecte.
        """
        try:
            parsed = int(value.strip() or "0")
        except ValueError:
            return None
        return parsed if parsed >= 0 else None

    def _execute(self) -> None:
        """Construit l'offre depuis l'interface puis demande au moteur de l'exécuter.

        Entrées:
            Aucune autre que les contrôles du panneau.

        Sortie:
            None: Une erreur est affichée ou le résultat réussi est transmis au parent.
        """
        if self.game is None or self.initiator is None or self.partner is None:
            self.error_label.configure(text="Aucun partenaire disponible.")
            return

        left_cash = self._parse_cash(self.left_cash_var.get())
        right_cash = self._parse_cash(self.right_cash_var.get())
        if left_cash is None or right_cash is None:
            self.error_label.configure(
                text="Les montants doivent être des entiers positifs ou nuls."
            )
            return

        offer: TradeOffer = self.game.create_trade(self.initiator, self.partner)
        offer.cash_from_initiator = left_cash
        offer.cash_from_recipient = right_cash
        offer.properties_from_initiator = list(
            self._selected_items(
                sorted(self.initiator.properties, key=lambda item: item.index),
                self.left_property_list,
            )
        )
        offer.properties_from_recipient = list(
            self._selected_items(
                sorted(self.partner.properties, key=lambda item: item.index),
                self.right_property_list,
            )
        )
        offer.cards_from_initiator = list(
            self._selected_items(
                list(self.initiator.held_cards),
                self.left_card_list,
            )
        )
        offer.cards_from_recipient = list(
            self._selected_items(
                list(self.partner.held_cards),
                self.right_card_list,
            )
        )

        result = offer.execute()
        if not result.success:
            self.error_label.configure(text=result.message)
            return

        callback = self.on_finished
        self.hide()
        if callback is not None:
            callback(result)

    def _cancel(self) -> None:
        """Annule la composition de l'échange sans modifier la partie.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau est masqué et le callback d'annulation est appelé.
        """
        callback = self.on_cancel
        self.hide()
        if callback is not None:
            callback()
