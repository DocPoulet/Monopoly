"""Cartes joueur compactes et actives de la nouvelle interface V22."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from monopoly.game import Game
from monopoly.player import Player

from .pawns import PawnPreview


class PlayerStatusCard(ttk.Frame):
    """Présente les informations d'un joueur autour du plateau.

    Entrées:
        master (tk.Misc): Rail de joueurs parent.
        game (Game): Partie courante pour calculer le patrimoine.
        player (Player): Joueur représenté.
        pawn_id (str): Pion graphique attribué.
        color (str): Couleur du joueur.
        show_net_worth (bool): Affiche ou masque le patrimoine.

    Sortie:
        PlayerStatusCard: Carte actualisable et agrandissable pour le joueur actif.
    """

    def __init__(
        self,
        master: tk.Misc,
        game: Game,
        player: Player,
        pawn_id: str,
        color: str,
        show_net_worth: bool = True,
    ) -> None:
        """Construit la carte joueur avec ses libellés fixes.

        Entrées:
            master (tk.Misc): Parent Tkinter.
            game (Game): Partie source.
            player (Player): Joueur source.
            pawn_id (str): Identifiant visuel du pion.
            color (str): Couleur associée.
            show_net_worth (bool): Affichage initial du patrimoine.

        Sortie:
            None: La carte est créée puis remplie.
        """
        super().__init__(master, style="V22Card.TFrame", padding=9)
        self.game = game
        self.player = player
        self.pawn_id = pawn_id
        self.color = color
        self.show_net_worth = show_net_worth
        self.columnconfigure(1, weight=1)
        self.accent_bar = tk.Frame(self, background=color, height=4, borderwidth=0)
        self.accent_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.accent_bar.grid_propagate(False)
        self.preview = PawnPreview(self, pawn_id, color=color, size=40)
        self.preview.grid(row=1, column=0, rowspan=3, padx=(0, 8), sticky="n")
        self.name_label = ttk.Label(self, text="", style="V22Card.TLabel", font=("Arial", 10, "bold"))
        self.name_label.grid(row=1, column=1, sticky="w")
        self.cash_label = ttk.Label(self, text="", style="V22Card.TLabel")
        self.cash_label.grid(row=2, column=1, sticky="w")
        self.detail_label = ttk.Label(self, text="", style="V22MutedCard.TLabel", wraplength=185)
        self.detail_label.grid(row=3, column=1, sticky="w")
        self.refresh(active=False)

    def refresh(self, active: bool) -> None:
        """Actualise cash, patrimoine, biens et état de prison/faillite.

        Entrées:
            active (bool): Indique si ce joueur joue actuellement.

        Sortie:
            None: Les textes et dimensions reflètent l'état courant.
        """
        player = self.player
        prefix = "▶ " if active else ""
        self.name_label.configure(text=f"{prefix}{player.name}", foreground=self.color)
        self.cash_label.configure(text=f"Cash : {player.cash} $")
        status = "Faillite" if player.bankrupt else (f"Prison {player.jail_turns}" if player.in_jail else f"Case {player.position}")
        first_line = f"{len(player.properties)} biens • {len(player.held_cards)} cartes"
        second_line = status
        if self.show_net_worth:
            second_line = f"P {self.game.player_net_worth(player)} $ • {status}"
        self.detail_label.configure(text=f"{first_line}\n{second_line}")
        self.configure(padding=11 if active else 7)
        self.accent_bar.configure(height=7 if active else 4)
        self.preview.configure(width=48 if active else 36, height=48 if active else 36)
