"""Panneau intégré de fin de partie avec statistiques détaillées."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from monopoly.statistics import GameStatistics

if TYPE_CHECKING:
    from monopoly.game import Game


class EndGameOverlay(tk.Frame):
    """Présente le vainqueur et les statistiques finales sans boîte de dialogue.

    Entrées:
        master (tk.Misc): Conteneur parent, généralement ``BoardView``.

    Sortie:
        EndGameOverlay: Panneau réutilisable de fin de partie.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit les zones de résumé, classement et actions finales.

        Entrées:
            master (tk.Misc): Conteneur graphique parent.

        Sortie:
            None: Le panneau est créé puis masqué.
        """
        super().__init__(
            master,
            background="#E7ECEF",
            highlightbackground="#6E7D86",
            highlightthickness=2,
            padx=12,
            pady=12,
        )
        self.game: Game | None = None
        self.on_history: Callable[[], None] | None = None
        self.on_new_game: Callable[[], None] | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self.title_label = ttk.Label(
            self,
            text="Partie terminée",
            font=("Arial", 22, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="ew")

        self.reason_label = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            justify="center",
        )
        self.reason_label.grid(row=1, column=0, sticky="ew", pady=(3, 10))

        self.summary_label = ttk.Label(
            self,
            text="",
            justify="center",
            font=("Arial", 10, "bold"),
            wraplength=680,
        )
        self.summary_label.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        table_frame = ttk.LabelFrame(self, text="Bilan des joueurs", padding=7)
        table_frame.grid(row=3, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = (
            "cash",
            "worth",
            "properties",
            "rent_paid",
            "rent_received",
            "buildings",
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="tree headings",
            height=8,
        )
        self.tree.heading("#0", text="Joueur")
        self.tree.heading("cash", text="Argent")
        self.tree.heading("worth", text="Valeur")
        self.tree.heading("properties", text="Biens")
        self.tree.heading("rent_paid", text="Loyers payés")
        self.tree.heading("rent_received", text="Loyers reçus")
        self.tree.heading("buildings", text="Bâtiments")
        self.tree.column("#0", width=120)
        for column in columns:
            self.tree.column(column, width=90, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        ttk.Button(
            buttons,
            text="Voir replay & statistiques",
            command=self._history,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ttk.Button(
            buttons,
            text="Retour au menu",
            style="Primary.TButton",
            command=self._new_game,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.place_forget()

    def show(
        self,
        game: "Game",
        on_history: Callable[[], None],
        on_new_game: Callable[[], None],
        abandoned: bool = False,
    ) -> None:
        """Affiche le bilan final calculé depuis le moteur et l'historique.

        Entrées:
            game (Game): Partie terminée.
            on_history (Callable[[], None]): Ouvre l'historique complet.
            on_new_game (Callable[[], None]): Revient au menu principal.
            abandoned (bool): Indique un retour volontaire au menu avant la fin naturelle.

        Sortie:
            None: Le panneau devient visible au centre du plateau.
        """
        self.game = game
        self.on_history = on_history
        self.on_new_game = on_new_game

        winner = game.winner
        if abandoned:
            self.title_label.configure(text="Bilan de la partie")
            self.reason_label.configure(
                text="Partie interrompue volontairement avant son terme."
            )
        elif winner is not None:
            self.title_label.configure(text=f"Victoire de {winner.name}")
            if game.reached_turn_limit:
                self.reason_label.configure(
                    text=(
                        f"Limite de {game.options.turn_limit} tours atteinte — "
                        "classement selon la valeur nette."
                    )
                )
            else:
                self.reason_label.configure(text="Dernier joueur encore solvable.")
        else:
            self.title_label.configure(text="Partie terminée")
            self.reason_label.configure(text="Bilan final de la partie.")

        stats = GameStatistics.from_game(game)
        largest_rent = max(
            (
                int(event.data.get("amount", 0))
                for event in game.history.events
                if event.event_type == "rent"
            ),
            default=0,
        )
        self.summary_label.configure(
            text=(
                f"{stats.turns} tours • {stats.cards_drawn} cartes • "
                f"{stats.purchases} achats • {stats.buildings_built} constructions • "
                f"{stats.trades} échanges • plus gros loyer : {largest_rent} $"
            )
        )

        for item in self.tree.get_children():
            self.tree.delete(item)

        by_id = {player.player_id: player for player in stats.players}
        ordered = sorted(
            game.players,
            key=lambda player: (
                game.player_net_worth(player),
                player.cash,
            ),
            reverse=True,
        )
        for player in ordered:
            pstats = by_id[player.player_id]
            self.tree.insert(
                "",
                "end",
                text=player.name + (" 🏆" if player is winner and not abandoned else ""),
                values=(
                    f"{player.cash} $",
                    f"{game.player_net_worth(player)} $",
                    len(player.properties),
                    f"{pstats.rent_paid} $",
                    f"{pstats.rent_received} $",
                    pstats.buildings_built,
                ),
            )

        self.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.84,
            relheight=0.74,
        )
        self.lift()

    def hide(self) -> None:
        """Masque le bilan final.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît.
        """
        self.place_forget()

    def _history(self) -> None:
        """Demande l'ouverture de l'historique complet.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback associé est exécuté.
        """
        if self.on_history is not None:
            self.on_history()

    def _new_game(self) -> None:
        """Demande le retour au menu principal.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback associé est exécuté.
        """
        if self.on_new_game is not None:
            self.on_new_game()
