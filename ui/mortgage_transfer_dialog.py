"""Choix du traitement des propriétés hypothéquées reçues lors d'un transfert."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from monopoly.player import Player
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from monopoly.game import Game
from monopoly.properties import OwnableSpace


class ReceivedMortgageDialog(tk.Toplevel):
    """Permet de choisir quelles hypothèques reçues seront levées immédiatement.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        player (Player): Nouveau propriétaire.
        spaces (list[OwnableSpace]): Biens hypothéqués reçus.

    Sortie:
        ReceivedMortgageDialog: Dialogue modal dont ``result`` contient les biens à libérer.
    """

    def __init__(
        self,
        master: tk.Misc,
        game: "Game",
        player: Player,
        spaces: list[OwnableSpace],
    ) -> None:
        """Construit une ligne par hypothèque avec son coût immédiat.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            game (Game): Partie fournissant la taxe d'hypothèque configurée.
            player (Player): Joueur concerné.
            spaces (list[OwnableSpace]): Biens hypothéqués reçus.

        Sortie:
            None: Les choix sont initialisés sur ``Conserver hypothéqué``.
        """
        super().__init__(master)
        self.title("Biens hypothéqués reçus")
        self.geometry("760x500")
        self.minsize(690, 430)
        self.game = game
        self.player = player
        self.spaces = list(spaces)
        self.result: list[OwnableSpace] = []
        self.variables: dict[int, tk.BooleanVar] = {}

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._confirm)

        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        ttk.Label(
            root,
            text=f"{player.name} reçoit des biens hypothéqués",
            font=("Arial", 17, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            root,
            text=(
                f"Pour chaque bien, {game.options.unmortgage_tax_percent} % d'intérêts "
                "sont dus immédiatement. Vous pouvez aussi lever l'hypothèque "
                "tout de suite en payant le principal + cet intérêt."
            ),
            style="Muted.TLabel",
            wraplength=710,
        ).pack(anchor="w", pady=(4, 12))

        table = ttk.Frame(root)
        table.pack(fill="both", expand=True)

        for space in self.spaces:
            row = ttk.LabelFrame(table, text=space.name, padding=8)
            row.pack(fill="x", pady=4)
            row.columnconfigure(0, weight=1)

            interest = self.game.rules.mortgage_interest(space)
            total_now = space.mortgage_value + interest
            ttk.Label(
                row,
                text=(
                    f"Hypothèque : {space.mortgage_value} $ • "
                    f"intérêt obligatoire : {interest} $"
                ),
            ).grid(row=0, column=0, sticky="w")

            variable = tk.BooleanVar(value=False)
            self.variables[space.index] = variable
            ttk.Checkbutton(
                row,
                text=f"Lever immédiatement — coût total maintenant : {total_now} $",
                variable=variable,
                command=self._refresh_total,
            ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.total_label = ttk.Label(
            root,
            text="",
            font=("Arial", 10, "bold"),
        )
        self.total_label.pack(fill="x", pady=(10, 6))

        ttk.Button(
            root,
            text="Valider ces choix",
            style="Primary.TButton",
            command=self._confirm,
        ).pack(fill="x")

        self._refresh_total()

    def _refresh_total(self) -> None:
        """Calcule le paiement bancaire correspondant aux choix courants.

        Entrées:
            Aucune.

        Sortie:
            None: Le coût total immédiat est affiché.
        """
        total = 0
        for space in self.spaces:
            interest = self.game.rules.mortgage_interest(space)
            if self.variables[space.index].get():
                total += space.mortgage_value + interest
            else:
                total += interest

        self.total_label.configure(
            text=(
                f"Paiement bancaire immédiat prévu : {total} $ • "
                f"argent actuel : {self.player.cash} $"
            )
        )

    def _confirm(self) -> None:
        """Conserve la liste des biens à déshypothéquer et ferme le dialogue.

        Entrées:
            Aucune.

        Sortie:
            None: ``result`` contient les biens cochés.
        """
        self.result = [
            space
            for space in self.spaces
            if self.variables[space.index].get()
        ]
        self.destroy()
