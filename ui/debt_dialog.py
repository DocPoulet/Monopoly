"""Dialogue de gestion manuelle d'une dette, y compris cession directe de biens."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from monopoly.debt import DebtManagementResult
from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property

if TYPE_CHECKING:
    from monopoly.game import Game


class DebtManagementDialog(tk.Toplevel):
    """Permet de vendre, hypothéquer ou céder des biens pour régler une dette.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        game (Game): Partie contenant les règles.
        player (Player): Joueur débiteur.
        target_cash (int): Montant total de la dette.
        creditor (Player | None): Joueur créancier, ou ``None`` pour la banque.

    Sortie:
        DebtManagementDialog: Dialogue modal dont ``result`` décrit le règlement préparé.
    """

    def __init__(
        self,
        master: tk.Misc,
        game: "Game",
        player: Player,
        target_cash: int,
        creditor: Player | None = None,
    ) -> None:
        """Construit les listes de liquidation, cession et solvabilité maximale.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            game (Game): Partie courante.
            player (Player): Débiteur.
            target_cash (int): Dette totale à couvrir.
            creditor (Player | None): Joueur pouvant recevoir directement des biens.

        Sortie:
            None: Le dialogue devient modal et attend une décision.
        """
        super().__init__(master)
        self.title("Régler une dette")
        self.geometry("1180x650")
        self.minsize(1040, 570)
        self.game = game
        self.player = player
        self.target_cash = max(0, target_cash)
        self.creditor = creditor
        self.property_credit = 0
        self.result = DebtManagementResult(False, 0, False)

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._attempt_close)

        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        for column in range(3):
            root.columnconfigure(column, weight=1)
        root.rowconfigure(2, weight=1)

        title = f"{player.name} doit régler {self.target_cash} $"
        if creditor is not None:
            title += f" à {creditor.name}"
        ttk.Label(
            root,
            text=title,
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        self.summary_label = ttk.Label(
            root,
            text="",
            style="Muted.TLabel",
            wraplength=1080,
        )
        self.summary_label.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(3, 12),
        )

        self._build_buildings_panel(root)
        self._build_mortgages_panel(root)
        self._build_transfer_panel(root)

        self.feedback_label = ttk.Label(
            root,
            text="",
            wraplength=1060,
            justify="center",
            font=("Arial", 9, "bold"),
        )
        self.feedback_label.grid(
            row=3,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(10, 4),
        )

        buttons = ttk.Frame(root)
        buttons.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        buttons.columnconfigure(0, weight=2)
        buttons.columnconfigure(1, weight=1)

        self.pay_button = ttk.Button(
            buttons,
            text="Continuer vers le paiement",
            style="Primary.TButton",
            command=self._confirm_payment,
        )
        self.pay_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.bankruptcy_button = ttk.Button(
            buttons,
            text="Faillite",
            command=self._accept_bankruptcy,
        )
        self.bankruptcy_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self._refresh()

    @property
    def remaining_due(self) -> int:
        """Retourne la part de dette qui n'a pas encore été éteinte par des biens.

        Entrées:
            Aucune.

        Sortie:
            int: Dette restante après déduction de ``property_credit``.
        """
        return max(0, self.target_cash - self.property_credit)

    def _build_buildings_panel(self, parent: ttk.Frame) -> None:
        """Construit la liste des bâtiments revendables au taux configuré.

        Entrées:
            parent (ttk.Frame): Conteneur principal.

        Sortie:
            None: Le tableau et le bouton de vente sont ajoutés à gauche.
        """
        frame = ttk.LabelFrame(
            parent,
            text="1. Revendre des bâtiments",
            padding=8,
        )
        frame.grid(row=2, column=0, sticky="nsew", padx=(0, 5))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.building_tree = ttk.Treeview(
            frame,
            columns=("level", "refund"),
            show="tree headings",
            selectmode="browse",
        )
        self.building_tree.heading("#0", text="Terrain")
        self.building_tree.heading("level", text="État")
        self.building_tree.heading("refund", text="Rapporte")
        self.building_tree.column("#0", width=165)
        self.building_tree.column("level", width=90, anchor="center")
        self.building_tree.column("refund", width=90, anchor="center")
        self.building_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.building_tree.yview,
        )
        self.building_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.sell_button = ttk.Button(
            frame,
            text="Revendre le bâtiment sélectionné",
            command=self._sell_selected_building,
        )
        self.sell_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _build_mortgages_panel(self, parent: ttk.Frame) -> None:
        """Construit la liste des biens encore hypothécables.

        Entrées:
            parent (ttk.Frame): Conteneur principal.

        Sortie:
            None: Le tableau d'hypothèques est ajouté au centre.
        """
        frame = ttk.LabelFrame(
            parent,
            text="2. Hypothéquer",
            padding=8,
        )
        frame.grid(row=2, column=1, sticky="nsew", padx=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.mortgage_tree = ttk.Treeview(
            frame,
            columns=("value",),
            show="tree headings",
            selectmode="browse",
        )
        self.mortgage_tree.heading("#0", text="Bien")
        self.mortgage_tree.heading("value", text="Rapporte")
        self.mortgage_tree.column("#0", width=175)
        self.mortgage_tree.column("value", width=90, anchor="center")
        self.mortgage_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.mortgage_tree.yview,
        )
        self.mortgage_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.mortgage_button = ttk.Button(
            frame,
            text="Hypothéquer le bien sélectionné",
            command=self._mortgage_selected_property,
        )
        self.mortgage_button.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

    def _build_transfer_panel(self, parent: ttk.Frame) -> None:
        """Construit la liste des biens cessibles directement au joueur créancier.

        Entrées:
            parent (ttk.Frame): Conteneur principal.

        Sortie:
            None: Une troisième colonne explique et permet le paiement en biens.
        """
        frame = ttk.LabelFrame(
            parent,
            text="3. Céder au créancier à 100 %",
            padding=8,
        )
        frame.grid(row=2, column=2, sticky="nsew", padx=(5, 0))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        self.transfer_hint = ttk.Label(
            frame,
            text="",
            style="Muted.TLabel",
            wraplength=310,
        )
        self.transfer_hint.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 7))

        self.transfer_tree = ttk.Treeview(
            frame,
            columns=("state", "value"),
            show="tree headings",
            selectmode="browse",
        )
        self.transfer_tree.heading("#0", text="Bien")
        self.transfer_tree.heading("state", text="Bâtiments")
        self.transfer_tree.heading("value", text="Crédit dette")
        self.transfer_tree.column("#0", width=145)
        self.transfer_tree.column("state", width=80, anchor="center")
        self.transfer_tree.column("value", width=95, anchor="center")
        self.transfer_tree.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.transfer_tree.yview,
        )
        self.transfer_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.transfer_button = ttk.Button(
            frame,
            text="Céder le bien sélectionné",
            command=self._transfer_selected_property,
        )
        self.transfer_button.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

    def _sellable_buildings(self) -> list[Property]:
        """Retourne les terrains dont un niveau peut être vendu immédiatement.

        Entrées:
            Aucune.

        Sortie:
            list[Property]: Terrains respectant les règles de revente.
        """
        return [
            space
            for space in self.player.properties
            if isinstance(space, Property)
            and self.game.rules.can_sell_building(self.player, space)
        ]

    def _mortgageable_spaces(self) -> list[OwnableSpace]:
        """Retourne les biens actuellement hypothécables.

        Entrées:
            Aucune.

        Sortie:
            list[OwnableSpace]: Biens légalement hypothécables.
        """
        return [
            space
            for space in self.player.properties
            if self.game.rules.can_mortgage(self.player, space)
        ]

    def _transferable_spaces(self) -> list[OwnableSpace]:
        """Retourne les biens pouvant être cédés directement au créancier.

        Entrées:
            Aucune.

        Sortie:
            list[OwnableSpace]: Biens non hypothéqués éligibles à la variante.
        """
        if self.creditor is None:
            return []
        return [
            space
            for space in self.player.properties
            if self.game.rules.can_transfer_property_for_debt(
                self.player,
                self.creditor,
                space,
            )
        ]

    def _selected_from_tree(
        self,
        tree: ttk.Treeview,
    ) -> OwnableSpace | None:
        """Résout l'index sélectionné d'un tableau vers un bien du débiteur.

        Entrées:
            tree (ttk.Treeview): Tableau contenant des ``iid`` égaux aux index de cases.

        Sortie:
            OwnableSpace | None: Bien correspondant, sinon ``None``.
        """
        selection = tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        return next(
            (space for space in self.player.properties if space.index == index),
            None,
        )

    def _selected_building(self) -> Property | None:
        """Retourne le terrain sélectionné dans la liste des bâtiments.

        Entrées:
            Aucune.

        Sortie:
            Property | None: Terrain sélectionné.
        """
        space = self._selected_from_tree(self.building_tree)
        return space if isinstance(space, Property) else None

    def _selected_mortgage(self) -> OwnableSpace | None:
        """Retourne le bien sélectionné dans la liste des hypothèques.

        Entrées:
            Aucune.

        Sortie:
            OwnableSpace | None: Bien sélectionné.
        """
        return self._selected_from_tree(self.mortgage_tree)

    def _selected_transfer(self) -> OwnableSpace | None:
        """Retourne le bien sélectionné dans la liste de cession.

        Entrées:
            Aucune.

        Sortie:
            OwnableSpace | None: Bien sélectionné.
        """
        return self._selected_from_tree(self.transfer_tree)

    def _is_definitely_insolvent(self) -> bool:
        """Indique si même la meilleure liquidation restante ne couvre pas la dette.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsque la capacité maximale est inférieure au solde dû.
        """
        capacity = self.game.rules.maximum_debt_capacity(
            self.player,
            self.creditor,
        )
        return capacity < self.remaining_due

    def _refresh(self) -> None:
        """Actualise dette, listes d'actions, capacité maximale et bouton Faillite.

        Entrées:
            Aucune.

        Sortie:
            None: Tous les contrôles reflètent l'état financier courant.
        """
        remaining = self.remaining_due
        capacity = self.game.rules.maximum_debt_capacity(
            self.player,
            self.creditor,
        )
        missing_cash = max(0, remaining - self.player.cash)

        self.summary_label.configure(
            text=(
                f"Dette initiale : {self.target_cash} $ • "
                f"réglée par biens : {self.property_credit} $ • "
                f"reste dû : {remaining} $ • cash : {self.player.cash} $ • "
                f"manque en cash : {missing_cash} $ • "
                f"capacité maximale restante : {capacity} $"
            )
        )

        for item in self.building_tree.get_children():
            self.building_tree.delete(item)
        sellable = self._sellable_buildings()
        for space in sorted(sellable, key=lambda item: item.index):
            level = "Hôtel" if space.hotel else f"{space.houses} maison(s)"
            self.building_tree.insert(
                "",
                "end",
                iid=str(space.index),
                text=space.name,
                values=(
                    level,
                    f"+{self.game.rules.building_resale_value(space)} $",
                ),
            )

        for item in self.mortgage_tree.get_children():
            self.mortgage_tree.delete(item)
        mortgageable = self._mortgageable_spaces()
        for space in sorted(mortgageable, key=lambda item: item.index):
            self.mortgage_tree.insert(
                "",
                "end",
                iid=str(space.index),
                text=space.name,
                values=(f"+{space.mortgage_value} $",),
            )

        for item in self.transfer_tree.get_children():
            self.transfer_tree.delete(item)
        transferable = self._transferable_spaces()
        for space in sorted(transferable, key=lambda item: item.index):
            if isinstance(space, Property):
                if space.hotel:
                    state = "Hôtel"
                elif space.houses:
                    state = f"{space.houses} maison(s)"
                else:
                    state = "Aucun"
            else:
                state = "—"

            self.transfer_tree.insert(
                "",
                "end",
                iid=str(space.index),
                text=space.name,
                values=(
                    state,
                    f"{self.game.rules.debt_transfer_value(space)} $",
                ),
            )

        enabled_transfer = (
            self.creditor is not None
            and self.game.options.property_debt_payment
        )
        if not enabled_transfer:
            self.transfer_hint.configure(
                text=(
                    "Indisponible : cette dette est envers la banque ou l'option "
                    "« paiement de dette en propriétés » est désactivée."
                )
            )
        else:
            self.transfer_hint.configure(
                text=(
                    "Un bien non hypothéqué compte pour 100 % de son prix actuel "
                    "+ 100 % du coût des bâtiments encore dessus. Vous pouvez vendre "
                    "des bâtiments avant de le céder au taux de revente normal."
                )
            )

        self.sell_button.state(["!disabled"] if sellable else ["disabled"])
        self.mortgage_button.state(
            ["!disabled"] if mortgageable else ["disabled"]
        )
        self.transfer_button.state(
            ["!disabled"] if transferable else ["disabled"]
        )

        cash_ready = self.player.cash >= remaining
        self.pay_button.state(["!disabled"] if cash_ready else ["disabled"])

        no_actions = not sellable and not mortgageable and not transferable
        insolvent = capacity < remaining
        bankruptcy_available = not cash_ready and (insolvent or no_actions)
        self.bankruptcy_button.state(
            ["!disabled"] if bankruptcy_available else ["disabled"]
        )

        if cash_ready:
            self.feedback_label.configure(
                text=(
                    "La partie restante de la dette peut maintenant être payée en cash."
                ),
                foreground="#287A43",
            )
        elif insolvent:
            self.feedback_label.configure(
                text=(
                    f"Faillite certaine : même en utilisant tout ce qui reste, "
                    f"{self.player.name} ne peut mobiliser que {capacity} $ pour "
                    f"{remaining} $ encore dus. Le bouton Faillite est disponible immédiatement."
                ),
                foreground="#A13C3C",
            )
        elif no_actions:
            self.feedback_label.configure(
                text="Aucune action supplémentaire ne permet de couvrir le solde restant.",
                foreground="#A13C3C",
            )
        else:
            self.feedback_label.configure(
                text=(
                    "Choisissez quoi revendre, hypothéquer ou céder. "
                    "Une cession de bien réduit directement la dette envers le créancier."
                ),
                foreground="#44535C",
            )

    def _sell_selected_building(self) -> None:
        """Vend le niveau de bâtiment choisi puis recalcule toutes les options.

        Entrées:
            Aucune.

        Sortie:
            None: Le moteur applique la revente si elle reste légale.
        """
        space = self._selected_building()
        if space is None:
            return

        previous = "hôtel" if space.hotel else "maison"
        value = self.game.rules.building_resale_value(space)
        if not self.game.rules.sell_building(self.player, space):
            self._refresh()
            return

        self.game.record_financial_event(
            f"{self.player.name} revend un {previous} sur {space.name} "
            f"pour {value} $ afin de régler sa dette."
        )
        self._refresh()

    def _mortgage_selected_property(self) -> None:
        """Hypothèque le bien choisi puis recalcule les ressources disponibles.

        Entrées:
            Aucune.

        Sortie:
            None: La valeur hypothécaire rejoint le cash du débiteur.
        """
        space = self._selected_mortgage()
        if space is None:
            return
        if self.game.rules.mortgage_property(self.player, space):
            self.game.record_financial_event(
                f"{self.player.name} hypothèque {space.name} "
                f"pour {space.mortgage_value} $ afin de régler sa dette."
            )
        self._refresh()

    def _transfer_selected_property(self) -> None:
        """Cède le bien choisi et crédite sa valeur intégrale sur la dette.

        Entrées:
            Aucune.

        Sortie:
            None: Le propriétaire change immédiatement et la dette restante diminue.
        """
        space = self._selected_transfer()
        if space is None or self.creditor is None:
            return

        value = self.game.rules.transfer_property_for_debt(
            self.player,
            self.creditor,
            space,
        )
        if value <= 0:
            self._refresh()
            return

        self.property_credit += value
        self._refresh()

    def _confirm_payment(self) -> None:
        """Valide la préparation lorsque le cash couvre le solde après cessions.

        Entrées:
            Aucune.

        Sortie:
            None: ``result`` décrit la valeur déjà payée en biens puis ferme le dialogue.
        """
        if self.player.cash < self.remaining_due:
            return
        self.result = DebtManagementResult(
            True,
            self.property_credit,
            False,
        )
        self.destroy()

    def _accept_bankruptcy(self) -> None:
        """Autorise la faillite immédiatement lorsque le remboursement maximal est insuffisant.

        Entrées:
            Aucune.

        Sortie:
            None: Le dialogue se ferme avec une demande explicite de faillite.
        """
        cash_ready = self.player.cash >= self.remaining_due
        no_actions = (
            not self._sellable_buildings()
            and not self._mortgageable_spaces()
            and not self._transferable_spaces()
        )
        if cash_ready:
            return
        if not self._is_definitely_insolvent() and not no_actions:
            return

        self.result = DebtManagementResult(
            False,
            self.property_credit,
            True,
        )
        self.destroy()

    def _attempt_close(self) -> None:
        """Empêche une fermeture qui contournerait une dette encore solvable.

        Entrées:
            Aucune.

        Sortie:
            None: La fermeture est convertie en paiement ou faillite uniquement si légale.
        """
        if self.player.cash >= self.remaining_due:
            self._confirm_payment()
            return

        no_actions = (
            not self._sellable_buildings()
            and not self._mortgageable_spaces()
            and not self._transferable_spaces()
        )
        if self._is_definitely_insolvent() or no_actions:
            self._accept_bankruptcy()
