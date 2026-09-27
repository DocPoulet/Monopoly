"""Panneau de gestion du patrimoine intégré directement au plateau."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property, Railroad

from .property_card import PropertyCardOverlay

if TYPE_CHECKING:
    from monopoly.game import Game


class PropertyManagerOverlay(tk.Frame):
    """Gère les propriétés d'un joueur sans ouvrir de fenêtre secondaire.

    Entrées:
        master (tk.Misc): Vue du plateau sur laquelle le panneau est superposé.

    Sortie:
        PropertyManagerOverlay: Panneau masqué jusqu'à l'appel de ``show``.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit la liste des biens, leur fiche et les actions immobilières.

        Entrées:
            master (tk.Misc): Conteneur parent, généralement ``BoardView``.

        Sortie:
            None: Le panneau est construit puis masqué.
        """
        super().__init__(
            master,
            background="#E6ECEF",
            highlightbackground="#81909A",
            highlightthickness=2,
            padx=10,
            pady=10,
        )
        self.game: Game | None = None
        self.player: Player | None = None
        self.on_close: Callable[[bool], None] | None = None
        self.on_changed: Callable[[], None] | None = None
        self.on_building_auction: Callable[[str, Property], None] | None = None
        self.changed = False

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)

        self.title_label = ttk.Label(
            self,
            text="Patrimoine",
            font=("Arial", 16, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.summary_label = ttk.Label(self, text="", style="Muted.TLabel")
        self.summary_label.grid(row=1, column=0, sticky="w", pady=(2, 8))

        self.bank_label = ttk.Label(self, text="", style="Muted.TLabel")
        self.bank_label.grid(row=0, column=1, rowspan=2, sticky="e")

        self._build_property_list()
        self._build_detail_panel()
        self._build_footer()
        self.place_forget()

    def _build_property_list(self) -> None:
        """Construit le tableau des biens dans la colonne gauche.

        Entrées:
            Aucune.

        Sortie:
            None: Le ``Treeview`` et son ascenseur sont créés.
        """
        panel = ttk.LabelFrame(self, text="Mes biens", padding=7)
        panel.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)

        columns = ("group", "state", "mortgage")
        self.tree = ttk.Treeview(
            panel,
            columns=columns,
            show="tree headings",
            selectmode="browse",
            height=13,
        )
        self.tree.heading("#0", text="Bien")
        self.tree.heading("group", text="Groupe")
        self.tree.heading("state", text="État")
        self.tree.heading("mortgage", text="Hypothèque")

        self.tree.column("#0", width=165)
        self.tree.column("group", width=90, anchor="center")
        self.tree.column("state", width=100, anchor="center")
        self.tree.column("mortgage", width=85, anchor="center")

        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("mortgaged", foreground="#9B3F3F")
        self.tree.tag_configure("developed", background="#EDF6EE")
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

    def _build_detail_panel(self) -> None:
        """Construit la fiche détaillée et ses boutons d'action.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau droit est prêt à afficher le bien sélectionné.
        """
        panel = ttk.LabelFrame(self, text="Bien sélectionné", padding=8)
        panel.grid(row=2, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        self.detail_header = tk.Frame(panel, background="#546E7A", height=64)
        self.detail_header.grid(row=0, column=0, sticky="ew")
        self.detail_header.grid_propagate(False)

        self.detail_type = tk.Label(
            self.detail_header,
            text="",
            background="#546E7A",
            foreground="#FFFFFF",
            font=("Arial", 8, "bold"),
        )
        self.detail_type.pack(pady=(7, 0))

        self.detail_name = tk.Label(
            self.detail_header,
            text="SÉLECTIONNEZ UN BIEN",
            background="#546E7A",
            foreground="#FFFFFF",
            font=("Arial", 14, "bold"),
        )
        self.detail_name.pack(pady=(1, 6))

        body = ttk.Frame(panel, padding=(4, 7))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)

        self.detail_status = ttk.Label(
            body,
            text="",
            font=("Arial", 10, "bold"),
            justify="center",
        )
        self.detail_status.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.detail_rows = ttk.Frame(body)
        self.detail_rows.grid(row=1, column=0, sticky="ew")

        self.note_label = ttk.Label(
            body,
            text="",
            style="Muted.TLabel",
            wraplength=285,
            justify="center",
        )
        self.note_label.grid(row=2, column=0, sticky="ew", pady=(7, 3))

        self.feedback_label = ttk.Label(
            body,
            text="",
            wraplength=285,
            justify="center",
            font=("Arial", 9, "bold"),
        )
        self.feedback_label.grid(row=3, column=0, sticky="ew", pady=(3, 6))

        actions = ttk.Frame(body)
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        self.build_button = ttk.Button(
            actions,
            text="Construire",
            style="Primary.TButton",
            command=self._build,
        )
        self.build_button.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=2)

        self.sell_button = ttk.Button(
            actions,
            text="Vendre bâtiment",
            command=self._sell,
        )
        self.sell_button.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=2)

        self.mortgage_button = ttk.Button(
            actions,
            text="Hypothéquer",
            command=self._mortgage,
        )
        self.mortgage_button.grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=2)

        self.unmortgage_button = ttk.Button(
            actions,
            text="Déshypothéquer",
            command=self._unmortgage,
        )
        self.unmortgage_button.grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=2)

    def _build_footer(self) -> None:
        """Construit la ligne de fermeture du panneau.

        Entrées:
            Aucune.

        Sortie:
            None: Le bouton Fermer est placé sous le contenu.
        """
        footer = ttk.Frame(self)
        footer.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(
            footer,
            text="Fermer la gestion",
            command=self._close,
        ).pack(side="right")

    def show(
        self,
        game: "Game",
        player: Player,
        on_close: Callable[[bool], None],
        on_changed: Callable[[], None],
        on_building_auction: Callable[[str, Property], None],
    ) -> None:
        """Affiche le patrimoine du joueur dans le centre du plateau.

        Entrées:
            game (Game): Partie contenant les règles et la banque.
            player (Player): Joueur dont les biens sont gérés.
            on_close (Callable[[bool], None]): Callback recevant l'indicateur de modification.
            on_changed (Callable[[], None]): Callback après chaque modification réussie.

        Sortie:
            None: Le panneau devient visible et sélectionne le premier bien.
        """
        self.game = game
        self.player = player
        self.on_close = on_close
        self.on_changed = on_changed
        self.on_building_auction = on_building_auction
        self.changed = False
        self.feedback_label.configure(text="")
        self.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.88,
            relheight=0.76,
        )
        self.lift()
        self._refresh()

    def hide(self) -> None:
        """Masque le panneau et libère ses références temporaires.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît du plateau.
        """
        self.place_forget()
        self.game = None
        self.player = None
        self.on_close = None
        self.on_changed = None
        self.on_building_auction = None
        self.changed = False

    @staticmethod
    def _group_name(space: OwnableSpace) -> str:
        """Retourne le groupe lisible du bien.

        Entrées:
            space (OwnableSpace): Bien à décrire.

        Sortie:
            str: Couleur, ``Gares`` ou ``Compagnies``.
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
        """Construit l'état synthétique affiché dans la liste.

        Entrées:
            space (OwnableSpace): Bien à décrire.

        Sortie:
            str: État d'hypothèque ou de développement.
        """
        if space.mortgaged:
            return "Hypothéqué"
        if isinstance(space, Property):
            if space.hotel:
                return "Hôtel"
            if space.houses:
                return f"{space.houses} maison(s)"
            return "Nu"
        return "Actif"

    def _selected_space(self) -> OwnableSpace | None:
        """Retourne le bien correspondant à la ligne sélectionnée.

        Entrées:
            Aucune autre que la sélection du tableau.

        Sortie:
            OwnableSpace | None: Bien courant ou ``None``.
        """
        if self.player is None:
            return None
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
        """Actualise la fiche lorsque l'utilisateur change de bien.

        Entrées:
            event (tk.Event): Événement Tkinter de sélection.

        Sortie:
            None: Le panneau de droite est reconstruit.
        """
        self.feedback_label.configure(text="")
        self._refresh_details()

    def _refresh(self, select_index: int | None = None) -> None:
        """Synchronise résumé, stock bancaire, liste et fiche détaillée.

        Entrées:
            select_index (int | None): Bien à conserver comme sélection.

        Sortie:
            None: Tous les widgets reflètent l'état courant du moteur.
        """
        if self.game is None or self.player is None:
            return

        if select_index is None and self.tree.selection():
            try:
                select_index = int(self.tree.selection()[0])
            except ValueError:
                select_index = None

        mortgages = sum(1 for space in self.player.properties if space.mortgaged)
        self.title_label.configure(text=f"Patrimoine de {self.player.name}")
        self.summary_label.configure(
            text=(
                f"{self.player.cash} $ disponibles • "
                f"{len(self.player.properties)} bien(s) • "
                f"{mortgages} hypothèque(s)"
            )
        )
        self.bank_label.configure(text=f"Banque : {self.game.bank.stock_text()}")

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
                    self._group_name(space),
                    self._state_text(space),
                    f"{space.mortgage_value} $",
                ),
                tags=tags,
            )

        if select_index is not None and self.tree.exists(str(select_index)):
            selected = str(select_index)
        elif self.tree.get_children():
            selected = self.tree.get_children()[0]
        else:
            selected = None

        if selected is not None:
            self.tree.selection_set(selected)
            self.tree.focus(selected)
            self.tree.see(selected)

        self._refresh_details()

    def _refresh_details(self) -> None:
        """Affiche les informations et actions légales du bien sélectionné.

        Entrées:
            Aucune.

        Sortie:
            None: La fiche et les boutons sont recalculés.
        """
        if self.game is None or self.player is None:
            return

        space = self._selected_space()
        for child in self.detail_rows.winfo_children():
            child.destroy()

        if space is None:
            self.detail_name.configure(text="SÉLECTIONNEZ UN BIEN")
            self.detail_type.configure(text="")
            self.detail_status.configure(text="")
            self.note_label.configure(text="")
            self._set_action_states(None)
            return

        color = PropertyCardOverlay._header_color(space)
        self.detail_header.configure(background=color)
        self.detail_type.configure(
            text=PropertyCardOverlay._type_title(space),
            background=color,
        )
        self.detail_name.configure(text=space.name.upper(), background=color)

        status = self._state_text(space)
        if space.mortgaged:
            status += f" • levée : {self.game.rules.unmortgage_cost(space)} $"
        self.detail_status.configure(text=status)

        rows: list[tuple[str, str, bool]] = [
            ("Prix d'achat", f"{space.price} $", True),
            ("Hypothèque", f"{space.mortgage_value} $", True),
            ("Déshypothèque", f"{self.game.rules.unmortgage_cost(space)} $", False),
        ]
        if isinstance(space, Property):
            rows.extend([
                ("Loyer", f"{self.game.rules.scale_rent(space.base_rent)} $", True),
                ("Avec 1 maison", f"{self.game.rules.scale_rent(space.house_rents[0])} $", False),
                ("Avec 2 maisons", f"{self.game.rules.scale_rent(space.house_rents[1])} $", False),
                ("Avec 3 maisons", f"{self.game.rules.scale_rent(space.house_rents[2])} $", False),
                ("Avec 4 maisons", f"{self.game.rules.scale_rent(space.house_rents[3])} $", False),
                ("Avec hôtel", f"{self.game.rules.scale_rent(space.hotel_rent)} $", True),
                ("Prix d'une maison", f"{space.house_cost} $", False),
            ])
        elif isinstance(space, Railroad):
            rows.extend([
                ("1 gare", f"{self.game.rules.scale_rent(25)} $", False),
                ("2 gares", f"{self.game.rules.scale_rent(50)} $", False),
                ("3 gares", f"{self.game.rules.scale_rent(100)} $", False),
                ("4 gares", f"{self.game.rules.scale_rent(200)} $", True),
            ])
        elif isinstance(space, Utility):
            suffix = "" if self.game.options.rent_percent == 100 else f" × {self.game.options.rent_percent} %"
            rows.extend([
                ("1 compagnie", f"4 × le total des dés{suffix}", False),
                ("2 compagnies", f"10 × le total des dés{suffix}", True),
            ])

        for label, value, bold in rows:
            row = ttk.Frame(self.detail_rows)
            row.pack(fill="x", pady=1)
            ttk.Label(
                row,
                text=label,
                font=("Arial", 8, "bold" if bold else "normal"),
            ).pack(side="left")
            ttk.Label(
                row,
                text=value,
                font=("Arial", 8, "bold" if bold else "normal"),
            ).pack(side="right")

        notes: list[str] = []
        if isinstance(space, Property):
            group = self.game.board.spaces_in_group(space.color_group)
            if not self.game.options.construction_anywhere:
                notes.append("Construction possible uniquement via le menu affiché juste après avoir atterri sur cette propriété.")
            if not self.game.options.monopoly_required_for_building:
                notes.append("Le monopole complet n'est pas requis pour construire.")
            if self.game.board.player_owns_group(self.player, space.color_group):
                notes.append("Groupe complet possédé.")
            if any(item.mortgaged for item in group):
                notes.append("Une hypothèque du groupe bloque les constructions.")
        if space.mortgaged:
            notes.append("Aucun loyer tant que le bien reste hypothéqué.")

        self.note_label.configure(text=" ".join(notes))
        self._set_action_states(space)

    def _set_action_states(self, space: OwnableSpace | None) -> None:
        """Active uniquement les actions autorisées sur le bien courant.

        Entrées:
            space (OwnableSpace | None): Bien sélectionné ou ``None``.

        Sortie:
            None: Libellés et états des quatre boutons sont actualisés.
        """
        if self.game is None or self.player is None:
            return

        build_enabled = False
        sell_enabled = False
        mortgage_enabled = False
        unmortgage_enabled = False

        self.build_button.configure(text="Construire")
        self.mortgage_button.configure(text="Hypothéquer")
        self.unmortgage_button.configure(text="Déshypothéquer")

        if isinstance(space, Property):
            if space.houses < 4 and not space.hotel:
                shortage = self.game.building_shortage_requires_auction("house")
                if shortage:
                    build_enabled = (
                        self.game.rules.can_request_house(self.player, space)
                        and self.game.bank.can_supply_houses(1)
                        and self.player.cash > 0
                    )
                    self.build_button.configure(text="Enchère maison")
                else:
                    build_enabled = self.game.rules.can_build_house(self.player, space)
                    self.build_button.configure(text=f"Maison • {space.house_cost} $")
            elif space.houses == 4 and not space.hotel:
                shortage = self.game.building_shortage_requires_auction("hotel")
                if shortage:
                    build_enabled = (
                        self.game.rules.can_request_hotel(self.player, space)
                        and self.game.bank.can_supply_hotels(1)
                        and self.player.cash > 0
                    )
                    self.build_button.configure(text="Enchère hôtel")
                else:
                    build_enabled = self.game.rules.can_build_hotel(self.player, space)
                    self.build_button.configure(text=f"Hôtel • {space.house_cost} $")
            else:
                self.build_button.configure(text="Construction maximale")
            sell_enabled = self.game.rules.can_sell_building(self.player, space)

        if space is not None:
            mortgage_enabled = self.game.rules.can_mortgage(self.player, space)
            unmortgage_enabled = self.game.rules.can_unmortgage(self.player, space)
            self.mortgage_button.configure(
                text=f"Hypothéquer +{space.mortgage_value} $"
            )
            self.unmortgage_button.configure(
                text=f"Lever -{self.game.rules.unmortgage_cost(space)} $"
            )

        for button, enabled in (
            (self.build_button, build_enabled),
            (self.sell_button, sell_enabled),
            (self.mortgage_button, mortgage_enabled),
            (self.unmortgage_button, unmortgage_enabled),
        ):
            button.state(["!disabled"] if enabled else ["disabled"])

    def _success(self, message: str, space: OwnableSpace) -> None:
        """Signale une modification réussie puis actualise le panneau et le plateau.

        Entrées:
            message (str): Confirmation à afficher.
            space (OwnableSpace): Bien à conserver comme sélection.

        Sortie:
            None: Le panneau est rafraîchi et le callback parent est appelé.
        """
        self.changed = True
        self.feedback_label.configure(text=message, foreground="#287A43")
        self._refresh(select_index=space.index)
        self.feedback_label.configure(text=message, foreground="#287A43")
        if self.on_changed is not None:
            self.on_changed()

    def _error(self, message: str) -> None:
        """Affiche un refus d'action directement dans le panneau.

        Entrées:
            message (str): Motif ou conseil à afficher.

        Sortie:
            None: Aucun dialogue secondaire n'est ouvert.
        """
        self.feedback_label.configure(text=message, foreground="#A13C3C")

    def _build(self) -> None:
        """Construit normalement ou déclenche une enchère en cas de pénurie.

        Entrées:
            Aucune.

        Sortie:
            None: Le bâtiment est acheté au prix normal, une enchère intégrée est
            demandée, ou un message local explique l'impossibilité.
        """
        if self.game is None or self.player is None:
            return

        space = self._selected_space()
        if not isinstance(space, Property):
            self._error("Sélectionnez un terrain de couleur.")
            return

        if space.houses < 4 and not space.hotel:
            if not self.game.rules.can_request_house(self.player, space):
                self._error(
                    "Maison impossible : vérifiez le monopole, les hypothèques "
                    "et l'équilibre des constructions."
                )
                return

            if not self.game.bank.can_supply_houses(1):
                self._error(
                    "La banque n'a plus de maisons. Il faut attendre qu'une maison "
                    "soit vendue ou rendue à la banque."
                )
                return

            if self.game.building_shortage_requires_auction("house"):
                if self.on_building_auction is not None:
                    self.on_building_auction("house", space)
                return

            if not self.game.rules.build_house(self.player, space):
                self._error("Construction impossible : argent insuffisant.")
                return

            self._success("Maison construite.", space)
            return

        if space.houses == 4 and not space.hotel:
            if not self.game.rules.can_request_hotel(self.player, space):
                self._error(
                    "Hôtel impossible : le groupe doit être uniformément développé."
                )
                return

            if not self.game.bank.can_supply_hotels(1):
                self._error(
                    "La banque n'a plus d'hôtels. Il faut attendre qu'un hôtel "
                    "revienne à la banque."
                )
                return

            if self.game.building_shortage_requires_auction("hotel"):
                if self.on_building_auction is not None:
                    self.on_building_auction("hotel", space)
                return

            if not self.game.rules.build_hotel(self.player, space):
                self._error("Construction impossible : argent insuffisant.")
                return

            self._success("Hôtel construit.", space)
            return

        self._error("Ce terrain a déjà atteint son développement maximal.")

    def _sell(self) -> None:
        """Vend un niveau de bâtiment si la vente reste légale.

        Entrées:
            Aucune.

        Sortie:
            None: Le résultat est affiché directement dans le panneau.
        """
        if self.game is None or self.player is None:
            return
        space = self._selected_space()
        if not isinstance(space, Property):
            self._error("Sélectionnez un terrain développé.")
            return
        if not self.game.rules.sell_building(self.player, space):
            self._error(
                "Vente impossible : équilibre du groupe ou stock de maisons insuffisant."
            )
            return
        self._success("Bâtiment vendu à la banque.", space)

    def _mortgage(self) -> None:
        """Hypothèque le bien sélectionné.

        Entrées:
            Aucune.

        Sortie:
            None: La valeur hypothécaire est ajoutée au solde ou un message local apparaît.
        """
        if self.game is None or self.player is None:
            return
        space = self._selected_space()
        if space is None:
            return
        if not self.game.rules.mortgage_property(self.player, space):
            self._error(
                "Hypothèque impossible. Les bâtiments du groupe doivent d'abord être vendus."
            )
            return
        self._success(f"{space.name} hypothéqué.", space)

    def _unmortgage(self) -> None:
        """Lève l'hypothèque du bien sélectionné.

        Entrées:
            Aucune.

        Sortie:
            None: Le coût est payé ou un message local indique l'impossibilité.
        """
        if self.game is None or self.player is None:
            return
        space = self._selected_space()
        if space is None:
            return
        if not self.game.rules.unmortgage_property(self.player, space):
            self._error("Déshypothèque impossible : argent insuffisant ou bien actif.")
            return
        self._success(f"Hypothèque levée sur {space.name}.", space)

    def _close(self) -> None:
        """Ferme le panneau de patrimoine et informe la fenêtre de jeu.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau est masqué puis le callback reçoit ``changed``.
        """
        callback = self.on_close
        changed = self.changed
        self.hide()
        if callback is not None:
            callback(changed)
