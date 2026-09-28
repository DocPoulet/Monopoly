"""Écran privé de passage de main entre joueurs d'une partie locale."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class TurnTransitionOverlay(tk.Frame):
    """Masque la partie pendant que l'écran change de joueur.

    Entrées:
        master (tk.Misc): Conteneur couvrant toute la fenêtre de jeu.
        on_continue (Callable[[], None]): Callback appelé lorsque le nouveau joueur
            confirme qu'il a pris l'écran.

    Sortie:
        TurnTransitionOverlay: Rideau opaque réutilisable entre deux joueurs.
    """

    def __init__(
        self,
        master: tk.Misc,
        on_continue: Callable[[], None],
    ) -> None:
        """Construit le rideau de confidentialité et son bouton principal.

        Entrées:
            master (tk.Misc): Conteneur parent.
            on_continue (Callable[[], None]): Action de révélation de la partie.

        Sortie:
            None: Le rideau est créé puis masqué.
        """
        super().__init__(master, background="#24313A")
        self.on_continue = on_continue

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        card = tk.Frame(
            self,
            background="#F7FAFB",
            padx=42,
            pady=36,
            highlightbackground="#A8B3BA",
            highlightthickness=2,
        )
        card.grid(row=0, column=0)

        self.color_bar = tk.Frame(card, background="#4479B8", height=8)
        self.color_bar.pack(fill="x", pady=(0, 24))

        tk.Label(
            card,
            text="CHANGEMENT DE JOUEUR",
            background="#F7FAFB",
            foreground="#68767F",
            font=("Arial", 11, "bold"),
        ).pack()

        self.player_label = tk.Label(
            card,
            text="",
            background="#F7FAFB",
            foreground="#263238",
            font=("Arial", 30, "bold"),
        )
        self.player_label.pack(pady=(8, 4))

        self.turn_label = tk.Label(
            card,
            text="",
            background="#F7FAFB",
            foreground="#52616A",
            font=("Arial", 13),
        )
        self.turn_label.pack()

        tk.Label(
            card,
            text=(
                "Passez l'écran au joueur indiqué.\n"
                "Le plateau, les soldes et les propriétés restent masqués jusqu'à confirmation."
            ),
            background="#F7FAFB",
            foreground="#69767D",
            justify="center",
            font=("Arial", 10),
        ).pack(pady=(22, 20))

        self.continue_button = ttk.Button(
            card,
            text="Continuer",
            style="HomePrimary.TButton",
            command=self._continue,
        )
        self.continue_button.pack(fill="x")

        tk.Label(
            card,
            text="Entrée ou Espace pour continuer",
            background="#F7FAFB",
            foreground="#8A959B",
            font=("Arial", 9),
        ).pack(pady=(10, 0))

        self.place_forget()

    def show(
        self,
        player_name: str,
        turn_number: int,
        color: str,
    ) -> None:
        """Affiche le rideau pour le joueur qui va prendre la main.

        Entrées:
            player_name (str): Nom du nouveau joueur courant.
            turn_number (int): Numéro du tour de table affiché.
            color (str): Couleur d'identité du joueur.

        Sortie:
            None: Le rideau couvre toute la fenêtre de jeu.
        """
        self.player_label.configure(text=player_name)
        self.turn_label.configure(text=f"Tour {turn_number}")
        self.color_bar.configure(background=color)
        self.continue_button.configure(text=f"Je suis {player_name} — continuer")
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.continue_button.focus_set()

    def hide(self) -> None:
        """Masque le rideau de confidentialité.

        Entrées:
            Aucune.

        Sortie:
            None: La partie redevient visible.
        """
        self.place_forget()

    def _continue(self) -> None:
        """Transmet la confirmation de prise en main au contrôleur.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback est exécuté.
        """
        self.on_continue()
