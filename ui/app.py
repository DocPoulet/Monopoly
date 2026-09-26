"""Application Tkinter principale et gestion du cycle de vie des parties."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from monopoly import Game

from .dialogs import NewGameDialog
from .game_window import GameWindow


class MonopolyApp:
    """Crée la fenêtre principale et remplace l'interface lors d'une nouvelle partie.

    Entrées:
        root (tk.Tk | None): Racine Tkinter existante ou ``None`` pour en créer une.

    Sortie:
        MonopolyApp: Application prête à ouvrir une partie et lancer sa boucle graphique.
    """

    def __init__(self, root: tk.Tk | None = None) -> None:
        """Configure la fenêtre, le style et l'état initial de l'application.

        Entrées:
            root (tk.Tk | None): Fenêtre racine optionnelle.

        Sortie:
            None: L'application est initialisée sans encore démarrer ``mainloop``.
        """
        self.root = root or tk.Tk()
        self.root.title("Monopoly POO — Interface graphique")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)

        self._configure_style()
        self.game_window: GameWindow | None = None

    def _configure_style(self) -> None:
        """Applique quelques réglages ``ttk`` pour une interface plus lisible.

        Entrées:
            Aucune.

        Sortie:
            None: Le thème disponible et les espacements de boutons sont configurés.
        """
        style = ttk.Style(self.root)
        available = style.theme_names()

        if "clam" in available:
            style.theme_use("clam")

        background = "#EEF2F5"
        self.root.configure(background=background)

        style.configure("TFrame", background=background)
        style.configure("Board.TFrame", background="#D9E2DF")
        style.configure("TLabel", background=background, foreground="#263238")
        style.configure(
            "TButton",
            padding=(10, 7),
            font=("Arial", 10),
        )
        style.configure(
            "Primary.TButton",
            padding=(11, 8),
            font=("Arial", 10, "bold"),
        )
        style.configure(
            "TLabelframe",
            padding=5,
            background=background,
        )
        style.configure(
            "TLabelframe.Label",
            background=background,
            foreground="#34434D",
            font=("Arial", 10, "bold"),
        )
        style.configure(
            "Card.TLabelframe",
            padding=6,
            background=background,
        )
        style.configure(
            "DiceNote.TLabel",
            background=background,
            foreground="#36434D",
            font=("Arial", 11, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=background,
            foreground="#6E7A83",
        )
        style.configure(
            "SectionTitle.TLabel",
            background=background,
            foreground="#263238",
            font=("Arial", 15, "bold"),
        )
        style.configure(
            "Treeview",
            rowheight=25,
            font=("Arial", 9),
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 9, "bold"),
        )

    def new_game(self) -> bool:
        """Ouvre le dialogue de création puis installe une nouvelle partie.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` si une partie a été créée, ``False`` si le dialogue est annulé.
        """
        dialog = NewGameDialog(self.root)
        self.root.wait_window(dialog)

        if dialog.result is None:
            return False

        game = Game(dialog.result)
        self._show_game(game)
        return True

    def _show_game(self, game: Game) -> None:
        """Remplace l'ancienne vue de jeu par une vue reliée à la nouvelle partie.

        Entrées:
            game (Game): Partie qui doit devenir active.

        Sortie:
            None: L'ancienne vue est détruite et la nouvelle remplit la fenêtre.
        """
        if self.game_window is not None:
            self.game_window.destroy()

        self.game_window = GameWindow(
            self.root,
            game,
            new_game_callback=self.new_game,
        )
        self.game_window.pack(fill="both", expand=True)

    def run(self) -> None:
        """Crée une partie initiale puis démarre la boucle événementielle Tkinter.

        Entrées:
            Aucune.

        Sortie:
            None: La méthode reste dans ``mainloop`` jusqu'à fermeture de la fenêtre.
        """
        created = self.new_game()
        if not created:
            self.root.destroy()
            return

        self.root.mainloop()
