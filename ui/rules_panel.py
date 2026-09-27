"""Panneau intégré présentant les règles actives et le résultat de l'audit."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from monopoly.rules_audit import AUDITED_RULES, audited_rule_count, simplified_rule_count

if TYPE_CHECKING:
    from monopoly.game import Game


class RulesSummaryOverlay(tk.Frame):
    """Affiche les paramètres de la partie et les mécaniques auditées.

    Entrées:
        master (tk.Misc): Conteneur parent, généralement ``BoardView``.

    Sortie:
        RulesSummaryOverlay: Panneau en lecture seule réutilisable.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit le résumé des paramètres et la liste des règles auditées.

        Entrées:
            master (tk.Misc): Conteneur graphique parent.

        Sortie:
            None: Le panneau est construit puis masqué.
        """
        super().__init__(
            master,
            background="#E9EEF1",
            highlightbackground="#788790",
            highlightthickness=2,
            padx=12,
            pady=12,
        )
        self.game: Game | None = None
        self.on_close: Callable[[], None] | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.title_label = ttk.Label(
            self,
            text="Règles de la partie",
            font=("Arial", 18, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.profile_label = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            wraplength=760,
        )
        self.profile_label.grid(row=1, column=0, sticky="ew", pady=(3, 9))

        parameters = ttk.LabelFrame(self, text="Paramètres actifs", padding=8)
        parameters.grid(row=2, column=0, sticky="ew", pady=(0, 9))
        parameters.columnconfigure(0, weight=1)
        parameters.columnconfigure(1, weight=1)

        self.left_parameters = ttk.Label(
            parameters,
            text="",
            justify="left",
        )
        self.left_parameters.grid(row=0, column=0, sticky="nw", padx=(0, 12))

        self.right_parameters = ttk.Label(
            parameters,
            text="",
            justify="left",
        )
        self.right_parameters.grid(row=0, column=1, sticky="nw")

        audit_frame = ttk.LabelFrame(
            self,
            text="Audit des règles",
            padding=7,
        )
        audit_frame.grid(row=3, column=0, sticky="nsew")
        audit_frame.columnconfigure(0, weight=1)
        audit_frame.rowconfigure(0, weight=1)

        columns = ("status", "detail")
        self.tree = ttk.Treeview(
            audit_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Règle")
        self.tree.heading("status", text="État")
        self.tree.heading("detail", text="Comportement")
        self.tree.column("#0", width=175)
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("detail", width=500)

        scrollbar = ttk.Scrollbar(
            audit_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.note_label = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            wraplength=760,
            justify="left",
        )
        self.note_label.grid(row=4, column=0, sticky="ew", pady=(8, 0))

        ttk.Button(
            self,
            text="Fermer",
            command=self._close,
        ).grid(row=5, column=0, sticky="e", pady=(9, 0))

        self.place_forget()

    def show(self, game: "Game", on_close: Callable[[], None]) -> None:
        """Affiche le profil courant et la synthèse de l'audit.

        Entrées:
            game (Game): Partie dont les règles doivent être présentées.
            on_close (Callable[[], None]): Callback exécuté à la fermeture.

        Sortie:
            None: Le panneau apparaît au centre du plateau.
        """
        self.game = game
        self.on_close = on_close
        options = game.options

        self.profile_label.configure(text=options.summary())

        auctions = "activées" if options.auctions_enabled else "désactivées"
        self.left_parameters.configure(
            text=(
                f"Argent de départ : {options.starting_cash} $\n"
                f"Passage par Départ : {options.go_salary} $\n"
                f"Prix propriétés : {options.property_price_percent} %\n"
                f"Loyers : {options.rent_percent} %\n"
                f"Amende de prison : {options.jail_fine} $\n"
                f"Tentatives max en prison : {options.max_jail_turns}\n"
                f"Revente bâtiments : {options.building_resale_percent} %\n"
                f"Paiement dette en biens : {'oui' if options.property_debt_payment else 'non'}\n"
                f"Taxe déshypothèque : {options.unmortgage_tax_percent} %"
            )
        )
        self.right_parameters.configure(
            text=(
                f"Doubles avant prison : {options.doubles_to_jail}\n"
                f"Enchères immobilières : {auctions}\n"
                f"Monopole pour construire : {'oui' if options.monopoly_required_for_building else 'non'}\n"
                f"Stock maisons : {options.house_stock or 'illimité'}\n"
                f"Stock hôtels : {options.hotel_stock or 'illimité'}\n"
                f"Hypothèques : {'oui' if options.mortgages_enabled else 'non'}\n"
                f"Hypothèques transférées : {'oui' if options.transferred_mortgages else 'non'}\n"
                f"Loyer automatique : {'oui' if options.automatic_rent else 'non'}\n"
                f"Construction partout : {'oui' if options.construction_anywhere else 'uniquement à l’atterrissage'}\n"
                f"Max constructions à la fois : {options.max_buildings_per_action}\n"
                f"Cagnotte cartes Parc Gratuit : {'oui' if options.free_parking_card_pot else 'non'}\n"
                f"Bonus fixe Parc Gratuit : {options.free_parking_bonus} $\n"
                f"Cagnotte actuelle : {game.free_parking_pot} $\n"
                f"Limite de tours : {options.turn_limit or 'aucune'}"
            )
        )

        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, audit in enumerate(AUDITED_RULES):
            tag = "ok" if audit.status == "ok" else "simplified"
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                text=audit.title,
                values=(audit.status_label, audit.detail),
                tags=(tag,),
            )

        self.tree.tag_configure("ok")
        self.tree.tag_configure("simplified")

        self.note_label.configure(
            text=(
                f"{audited_rule_count()} mécaniques vérifiées • "
                f"{simplified_rule_count()} adaptations logicielles documentées. "
                "Les variantes choisies avant la partie restent distinctes des règles classiques."
            )
        )

        self.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.92,
            relheight=0.86,
        )
        self.lift()

    def hide(self) -> None:
        """Masque le panneau et libère ses références temporaires.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît.
        """
        self.place_forget()
        self.game = None
        self.on_close = None

    def _close(self) -> None:
        """Ferme le panneau puis rend la main à la fenêtre de jeu.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback est exécuté après masquage.
        """
        callback = self.on_close
        self.hide()
        if callback is not None:
            callback()
