"""Fenêtres de gestion du patrimoine et de choix d'hypothèque."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property, Railroad, Utility

from .property_card import PROPERTY_COLORS, PropertyCardOverlay

if TYPE_CHECKING:
    from monopoly.game import Game


class PropertyManagerDialog(tk.Toplevel):
    """Présente le patrimoine d'un joueur dans une vue détaillée à deux colonnes.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        game (Game): Partie contenant les règles immobilières.
        player (Player): Joueur dont les biens doivent être gérés.

    Sortie:
        PropertyManagerDialog: Fenêtre modale de construction, vente et hypothèque.
    """

    def __init__(self, master: tk.Misc, game: Game, player: Player) -> None:
        """Construit le tableau de patrimoine, la fiche détaillée et les actions.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            game (Game): Partie à modifier.
            player (Player): Propriétaire dont les biens sont affichés.

        Sortie:
            None: La fenêtre est prête à gérer les propriétés du joueur.
        """
        super().__init__(master)
        self.title(f"Patrimoine — {player.name}")
        self.geometry("1000x610")
        self.minsize(900, 540)
        self.game = game
        self.player = player
        self.changed = False

        self.transient(master)
        self.grab_set()

        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(2, weight=1)

        ttk.Label(
            root,
            text=f"Patrimoine de {player.name}",
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")

        self.summary_label = ttk.Label(root, text="", style="Muted.TLabel")
        self.summary_label.grid(row=1, column=0, sticky="w", pady=(2, 10))

        self.bank_label = ttk.Label(root, text="", style="Muted.TLabel")
        self.bank_label.grid(row=0, column=1, rowspan=2, sticky="e")

        self._build_property_list(root)
        self._build_detail_panel(root)
        self._build_footer(root)

        self._refresh()
        if self.tree.get_children():
            first = self.tree.get_children()[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
            self._refresh_details()

    def _build_property_list(self, parent: ttk.Frame) -> None:
        """Construit le tableau principal des biens du joueur.

        Entrées:
            parent (ttk.Frame): Conteneur racine de la fenêtre.

        Sortie:
            None: Le tableau et sa barre de défilement sont placés à gauche.
        """
        panel = ttk.LabelFrame(parent, text="Mes biens", padding=8)
        panel.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)

        columns = ("type", "group", "state", "mortgage", "lift")
        self.tree = ttk.Treeview(
            panel,
            columns=columns,
            show="tree headings",
            selectmode="browse",
            height=16,
        )
        self.tree.heading("#0", text="Bien")
        self.tree.heading("type", text="Type")
        self.tree.heading("group", text="Groupe")
        self.tree.heading("state", text="État")
        self.tree.heading("mortgage", text="Hypothèque")
        self.tree.heading("lift", text="Levée")

        self.tree.column("#0", width=190)
        self.tree.column("type", width=90, anchor="center")
        self.tree.column("group", width=95, anchor="center")
        self.tree.column("state", width=120, anchor="center")
        self.tree.column("mortgage", width=90, anchor="center")
        self.tree.column("lift", width=85, anchor="center")

        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("mortgaged", foreground="#8B3E3E")
        self.tree.tag_configure("developed", background="#EEF7EF")
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        """Construit la fiche détaillée et les boutons contextuels à droite.

        Entrées:
            parent (ttk.Frame): Conteneur racine de la fenêtre.

        Sortie:
            None: Le panneau de détail est placé à droite du tableau.
        """
        self.detail_outer = ttk.LabelFrame(parent, text="Détail du bien", padding=10)
        self.detail_outer.grid(row=2, column=1, sticky="nsew")
        self.detail_outer.columnconfigure(0, weight=1)
        self.detail_outer.rowconfigure(1, weight=1)

        self.detail_header = tk.Frame(
            self.detail_outer,
            background="#546E7A",
            height=76,
        )
        self.detail_header.grid(row=0, column=0, sticky="ew")
        self.detail_header.grid_propagate(False)

        self.detail_type = tk.Label(
            self.detail_header,
            text="",
            background="#546E7A",
            foreground="#FFFFFF",
            font=("Arial", 9, "bold"),
        )
        self.detail_type.pack(pady=(9, 0))

        self.detail_name = tk.Label(
            self.detail_header,
            text="Sélectionnez un bien",
            background="#546E7A",
            foreground="#FFFFFF",
            font=("Arial", 16, "bold"),
        )
        self.detail_name.pack(pady=(2, 8))

        body = ttk.Frame(self.detail_outer, padding=(4, 10))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)

        self.detail_status = ttk.Label(
            body,
            text="",
            font=("Arial", 11, "bold"),
            justify="center",
        )
        self.detail_status.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.detail_rows = ttk.Frame(body)
        self.detail_rows.grid(row=1, column=0, sticky="nsew")

        self.action_note = ttk.Label(
            body,
            text="",
            style="Muted.TLabel",
            wraplength=330,
            justify="center",
        )
        self.action_note.grid(row=2, column=0, sticky="ew", pady=(10, 6))

        actions = ttk.Frame(body)
        actions.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        self.build_button = ttk.Button(
            actions,
            text="Construire",
            style="Primary.TButton",
            command=self._build,
        )
        self.build_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)

        self.sell_button = ttk.Button(
            actions,
            text="Vendre bâtiment",
            command=self._sell,
        )
        self.sell_button.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)

        self.mortgage_button = ttk.Button(
            actions,
            text="Hypothéquer",
            command=self._mortgage,
        )
        self.mortgage_button.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)

        self.unmortgage_button = ttk.Button(
            actions,
            text="Déshypothéquer",
            command=self._unmortgage,
        )
        self.unmortgage_button.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)

    def _build_footer(self, parent: ttk.Frame) -> None:
        """Construit le pied de fenêtre et son bouton de fermeture.

        Entrées:
            parent (ttk.Frame): Conteneur racine de la fenêtre.

        Sortie:
            None: Le bouton Fermer est placé sous les deux panneaux.
        """
        footer = ttk.Frame(parent)
        footer.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Fermer", command=self.destroy).pack(side="right")

    @staticmethod
    def _space_type(space: OwnableSpace) -> str:
        """Retourne le type lisible d'un bien.

        Entrées:
            space (OwnableSpace): Bien à décrire.

        Sortie:
            str: ``Terrain``, ``Gare`` ou ``Compagnie``.
        """
        if isinstance(space, Property):
            return "Terrain"
        if isinstance(space, Railroad):
            return "Gare"
        return "Compagnie"

    @staticmethod
    def _group_name(space: OwnableSpace) -> str:
        """Retourne le nom de groupe affiché dans le tableau.

        Entrées:
            space (OwnableSpace): Bien à décrire.

        Sortie:
            str: Groupe de couleur, ``Gares`` ou ``Compagnies``.
        """
        names = {
            "brown": "Marron",
            "light_blue": "Bleu clair",
            "pink": "Rose",
            "orange": "Orange",
            "red": "Rouge",
            "yellow": "Jaune",
            "green": "Vert",
            "dark_blue": "Bleu foncé",
        }
        if isinstance(space, Property):
            return names.get(space.color_group, space.color_group)
        if isinstance(space, Railroad):
            return "Gares"
        return "Compagnies"

    @staticmethod
    def _state_text(space: OwnableSpace) -> str:
        """Construit un résumé court de l'état actuel du bien.

        Entrées:
            space (OwnableSpace): Bien à décrire.

        Sortie:
            str: État financier et niveau de développement éventuel.
        """
        if space.mortgaged:
            return "Hypothéqué"
        if isinstance(space, Property):
            if space.hotel:
                return "Hôtel"
            if space.houses:
                return f"{space.houses} maison(s)"
            return "Terrain nu"
        return "Actif"

    def _selected_space(self) -> OwnableSpace | None:
        """Retourne le bien actuellement sélectionné dans le tableau.

        Entrées:
            Aucune autre que la sélection du ``Treeview``.

        Sortie:
            OwnableSpace | None: Bien sélectionné ou ``None``.
        """
        selection = self.tree.selection()
        if not selection:
            return None

        try:
            index = int(selection[0])
        except ValueError:
            return None

        return next(
            (space for space in self.player.properties if space.index == index),
            None,
        )

    def _selection_changed(self, event: tk.Event) -> None:
        """Actualise la fiche détaillée après un changement de sélection.

        Entrées:
            event (tk.Event): Événement Tkinter de sélection.

        Sortie:
            None: Le panneau de droite est synchronisé avec la nouvelle ligne.
        """
        self._refresh_details()

    def _refresh_details(self) -> None:
        """Reconstruit le panneau de détail du bien sélectionné.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: En-tête, barème, état et boutons sont mis à jour.
        """
        space = self._selected_space()

        for child in self.detail_rows.winfo_children():
            child.destroy()

        if space is None:
            self.detail_name.configure(text="SÉLECTIONNEZ UN BIEN")
            self.detail_type.configure(text="")
            self.detail_status.configure(text="")
            self.action_note.configure(text="")
            self._set_action_states(None)
            return

        color = PropertyCardOverlay._header_color(space)
        self.detail_header.configure(background=color)
        self.detail_type.configure(
            text=PropertyCardOverlay._type_title(space),
            background=color,
        )
        self.detail_name.configure(
            text=space.name.upper(),
            background=color,
        )

        status = self._state_text(space)
        if space.mortgaged:
            status += f" • levée : {self.game.rules.unmortgage_cost(space)} $"
        self.detail_status.configure(text=status)

        rows: list[tuple[str, str, bool]] = [
            ("Prix d'achat", f"{space.price} $", True),
            ("Valeur hypothécaire", f"{space.mortgage_value} $", True),
            ("Coût de levée", f"{self.game.rules.unmortgage_cost(space)} $", False),
        ]
        rows.extend(PropertyCardOverlay._detail_rows(space))

        for label, value, bold in rows:
            row = ttk.Frame(self.detail_rows)
            row.pack(fill="x", pady=2)
            ttk.Label(
                row,
                text=label,
                font=("Arial", 9, "bold" if bold else "normal"),
            ).pack(side="left")
            ttk.Label(
                row,
                text=value,
                font=("Arial", 9, "bold" if bold else "normal"),
            ).pack(side="right")

        notes: list[str] = []
        if isinstance(space, Property):
            group = self.game.board.spaces_in_group(space.color_group)
            if self.game.board.player_owns_group(self.player, space.color_group):
                notes.append("Groupe complet possédé.")
            if any(item.mortgaged for item in group):
                notes.append("Une hypothèque du groupe bloque les constructions.")
        if space.mortgaged:
            notes.append("Aucun loyer n'est perçu tant que le bien reste hypothéqué.")

        self.action_note.configure(text=" ".join(notes))
        self._set_action_states(space)

    def _set_action_states(self, space: OwnableSpace | None) -> None:
        """Active uniquement les actions réellement légales pour le bien sélectionné.

        Entrées:
            space (OwnableSpace | None): Bien courant ou ``None``.

        Sortie:
            None: Les quatre boutons contextuels changent d'état et de libellé.
        """
        build_enabled = False
        sell_enabled = False
        mortgage_enabled = False
        unmortgage_enabled = False

        if isinstance(space, Property):
            if space.houses < 4 and not space.hotel:
                build_enabled = self.game.rules.can_build_house(self.player, space)
                self.build_button.configure(
                    text=f"Construire • {space.house_cost} $"
                )
            elif space.houses == 4 and not space.hotel:
                build_enabled = self.game.rules.can_build_hotel(self.player, space)
                self.build_button.configure(
                    text=f"Construire hôtel • {space.house_cost} $"
                )
            else:
                self.build_button.configure(text="Construction maximale")

            sell_enabled = self.game.rules.can_sell_building(self.player, space)
        else:
            self.build_button.configure(text="Construire")

        if space is not None:
            mortgage_enabled = self.game.rules.can_mortgage(self.player, space)
            unmortgage_enabled = self.game.rules.can_unmortgage(self.player, space)

            self.mortgage_button.configure(
                text=f"Hypothéquer • +{space.mortgage_value} $"
            )
            self.unmortgage_button.configure(
                text=f"Déshypothéquer • -{self.game.rules.unmortgage_cost(space)} $"
            )
        else:
            self.mortgage_button.configure(text="Hypothéquer")
            self.unmortgage_button.configure(text="Déshypothéquer")

        for button, enabled in (
            (self.build_button, build_enabled),
            (self.sell_button, sell_enabled),
            (self.mortgage_button, mortgage_enabled),
            (self.unmortgage_button, unmortgage_enabled),
        ):
            button.state(["!disabled"] if enabled else ["disabled"])

    def _build(self) -> None:
        """Construit une maison ou un hôtel sur le terrain sélectionné.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: Le bâtiment est ajouté si les règles l'autorisent.
        """
        space = self._selected_space()
        if not isinstance(space, Property):
            return

        if space.houses < 4 and not space.hotel:
            success = self.game.rules.build_house(self.player, space)
        elif space.houses == 4 and not space.hotel:
            success = self.game.rules.build_hotel(self.player, space)
        else:
            success = False

        if not success:
            messagebox.showwarning(
                "Construction impossible",
                (
                    "La construction n'est pas autorisée : vérifiez le monopole, "
                    "l'équilibre du groupe, les hypothèques, votre argent et le stock "
                    "de bâtiments de la banque."
                ),
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _sell(self) -> None:
        """Vend un niveau de bâtiment sur le terrain sélectionné.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: Le bâtiment est vendu si l'équilibre inverse le permet.
        """
        space = self._selected_space()
        if not isinstance(space, Property):
            return

        if not self.game.rules.sell_building(self.player, space):
            messagebox.showwarning(
                "Vente impossible",
                (
                    "Cette vente violerait l'équilibre du groupe ou la banque "
                    "ne possède pas les maisons nécessaires à la conversion d'un hôtel."
                ),
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _mortgage(self) -> None:
        """Hypothèque le bien sélectionné et verse sa valeur au joueur.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: Le bien devient hypothéqué si l'action est légale.
        """
        space = self._selected_space()
        if space is None:
            return

        if not self.game.rules.mortgage_property(self.player, space):
            messagebox.showwarning(
                "Hypothèque impossible",
                (
                    "Le bien ne peut pas être hypothéqué. Pour un groupe de couleur, "
                    "tous les bâtiments du groupe doivent d'abord être vendus."
                ),
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _unmortgage(self) -> None:
        """Lève l'hypothèque du bien sélectionné après paiement du coût complet.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: L'hypothèque est retirée si le joueur peut payer.
        """
        space = self._selected_space()
        if space is None:
            return

        if not self.game.rules.unmortgage_property(self.player, space):
            messagebox.showwarning(
                "Déshypothèque impossible",
                "Votre argent est insuffisant ou le bien n'est pas hypothéqué.",
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _refresh(self, select_index: int | None = None) -> None:
        """Reconstruit le résumé, le tableau et la fiche après une modification.

        Entrées:
            select_index (int | None): Bien à resélectionner après actualisation.

        Sortie:
            None: Tous les éléments reflètent l'état actuel du patrimoine.
        """
        portfolio_value = sum(space.price for space in self.player.properties)
        mortgages = sum(
            1 for space in self.player.properties if space.mortgaged
        )

        self.summary_label.configure(
            text=(
                f"{self.player.cash} $ disponibles • "
                f"{len(self.player.properties)} bien(s) • "
                f"valeur d'achat {portfolio_value} $ • "
                f"{mortgages} hypothèque(s)"
            )
        )
        self.bank_label.configure(text=f"Banque : {self.game.bank.stock_text()}")

        current_selection = select_index
        if current_selection is None and self.tree.selection():
            try:
                current_selection = int(self.tree.selection()[0])
            except ValueError:
                current_selection = None

        for item in self.tree.get_children():
            self.tree.delete(item)

        for space in sorted(self.player.properties, key=lambda item: item.index):
            tags: tuple[str, ...] = ()
            if space.mortgaged:
                tags = ("mortgaged",)
            elif isinstance(space, Property) and space.development_level > 0:
                tags = ("developed",)

            self.tree.insert(
                "",
                "end",
                iid=str(space.index),
                text=space.name,
                values=(
                    self._space_type(space),
                    self._group_name(space),
                    self._state_text(space),
                    f"{space.mortgage_value} $",
                    f"{self.game.rules.unmortgage_cost(space)} $",
                ),
                tags=tags,
            )

        if current_selection is not None and self.tree.exists(str(current_selection)):
            self.tree.selection_set(str(current_selection))
            self.tree.focus(str(current_selection))
            self.tree.see(str(current_selection))
        elif self.tree.get_children():
            first = self.tree.get_children()[0]
            self.tree.selection_set(first)
            self.tree.focus(first)

        self._refresh_details()


class DebtMortgageDialog(tk.Toplevel):
    """Demande explicitement quels biens hypothéquer pour couvrir une dette.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        player (Player): Joueur devant réunir des liquidités.
        mortgageable (list[OwnableSpace]): Biens actuellement hypothécables.
        target_cash (int): Solde liquide nécessaire pour régler la dette.

    Sortie:
        DebtMortgageDialog: Dialogue dont ``result`` contient les biens choisis.
    """

    def __init__(
        self,
        master: tk.Misc,
        player: Player,
        mortgageable: list[OwnableSpace],
        target_cash: int,
    ) -> None:
        """Construit la sélection multiple et le résumé du manque de liquidités.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            player (Player): Joueur concerné.
            mortgageable (list[OwnableSpace]): Biens légalement hypothécables.
            target_cash (int): Argent total que le joueur doit atteindre.

        Sortie:
            None: Le dialogue devient modal avec ``result`` initialisé à ``None``.
        """
        super().__init__(master)
        self.title("Liquidités nécessaires")
        self.geometry("720x500")
        self.minsize(660, 450)

        self.player = player
        self.mortgageable = list(mortgageable)
        self.target_cash = target_cash
        self.result: list[OwnableSpace] | None = None

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._decline)

        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        shortfall = max(0, target_cash - player.cash)

        ttk.Label(
            root,
            text=f"{player.name} doit réunir des liquidités",
            font=("Arial", 17, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            root,
            text=(
                f"Argent disponible : {player.cash} $   •   "
                f"Montant à atteindre : {target_cash} $   •   "
                f"Il manque : {shortfall} $"
            ),
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        table_frame = ttk.LabelFrame(
            root,
            text="Choisissez le ou les biens à hypothéquer",
            padding=8,
        )
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("type", "mortgage", "after")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="tree headings",
            selectmode="extended",
        )
        self.tree.heading("#0", text="Bien")
        self.tree.heading("type", text="Type")
        self.tree.heading("mortgage", text="Rapporte")
        self.tree.heading("after", text="Solde si seul")

        self.tree.column("#0", width=280)
        self.tree.column("type", width=110, anchor="center")
        self.tree.column("mortgage", width=100, anchor="center")
        self.tree.column("after", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        for space in sorted(
            self.mortgageable,
            key=lambda item: (-item.mortgage_value, item.index),
        ):
            self.tree.insert(
                "",
                "end",
                iid=str(space.index),
                text=space.name,
                values=(
                    PropertyManagerDialog._space_type(space),
                    f"+{space.mortgage_value} $",
                    f"{player.cash + space.mortgage_value} $",
                ),
            )

        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

        self.selection_label = ttk.Label(
            root,
            text="Sélection : 0 $",
            font=("Arial", 10, "bold"),
        )
        self.selection_label.grid(row=3, column=0, sticky="ew", pady=(10, 4))

        self.help_label = ttk.Label(
            root,
            text=(
                "Sélectionnez un ou plusieurs biens. Les bâtiments ont déjà été vendus "
                "automatiquement lorsqu'une vente légale était possible."
            ),
            style="Muted.TLabel",
            wraplength=650,
        )
        self.help_label.grid(row=4, column=0, sticky="ew")

        buttons = ttk.Frame(root)
        buttons.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=2)

        ttk.Button(
            buttons,
            text="Ne pas hypothéquer",
            command=self._decline,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.confirm_button = ttk.Button(
            buttons,
            text="Hypothéquer la sélection",
            style="Primary.TButton",
            command=self._confirm,
        )
        self.confirm_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.confirm_button.state(["disabled"])

    def _selected_spaces(self) -> list[OwnableSpace]:
        """Traduit la sélection graphique en objets de propriétés.

        Entrées:
            Aucune autre que les lignes sélectionnées.

        Sortie:
            list[OwnableSpace]: Biens sélectionnés dans l'ordre du tableau.
        """
        indexes = {
            int(item_id)
            for item_id in self.tree.selection()
            if item_id.isdigit()
        }
        return [
            space
            for space in self.mortgageable
            if space.index in indexes
        ]

    def _selection_changed(self, event: tk.Event) -> None:
        """Met à jour le total d'hypothèques après chaque changement de sélection.

        Entrées:
            event (tk.Event): Événement de sélection du tableau.

        Sortie:
            None: Le total et l'état du bouton de confirmation sont actualisés.
        """
        selected = self._selected_spaces()
        total = sum(space.mortgage_value for space in selected)
        resulting_cash = self.player.cash + total
        missing = max(0, self.target_cash - resulting_cash)

        if selected:
            text = (
                f"Sélection : +{total} $  →  solde estimé : {resulting_cash} $"
            )
            if missing:
                text += f"  •  il manquera encore {missing} $"
            else:
                text += "  •  dette couverte"
        else:
            text = "Sélection : 0 $"

        self.selection_label.configure(text=text)
        self.confirm_button.state(
            ["!disabled"] if selected else ["disabled"]
        )

    def _confirm(self) -> None:
        """Valide la liste de biens choisie et ferme le dialogue.

        Entrées:
            Aucune autre que la sélection du tableau.

        Sortie:
            None: ``result`` reçoit les biens choisis puis la fenêtre est détruite.
        """
        selected = self._selected_spaces()
        if not selected:
            return
        self.result = selected
        self.destroy()

    def _decline(self) -> None:
        """Permet au joueur de refuser toute hypothèque supplémentaire.

        Entrées:
            Aucune.

        Sortie:
            None: Après confirmation, ``result`` devient une liste vide.
        """
        confirmed = messagebox.askyesno(
            "Ne pas hypothéquer",
            (
                "Sans hypothèque supplémentaire, le paiement peut provoquer la faillite. "
                "Continuer ?"
            ),
            parent=self,
        )
        if not confirmed:
            return
        self.result = []
        self.destroy()
