"""Application Tkinter principale et navigation entre les écrans du jeu."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from monopoly import Game, GameOptions
from monopoly.persistence import (
    SaveGameError,
    list_save_metadata,
    load_game,
    save_game,
)

from .game_window import GameWindow
from .home import HomeView, PlayerSetupView, SaveBrowserView
from .rule_customization import RuleCustomizationView


class MonopolyApp:
    """Contrôle la fenêtre principale et les différents écrans de l'application.

    Entrées:
        root (tk.Tk | None): Racine Tkinter existante ou ``None`` pour en créer une.

    Sortie:
        MonopolyApp: Application capable d'afficher accueil, préparation et plateau.
    """

    def __init__(self, root: tk.Tk | None = None) -> None:
        """Configure la fenêtre, le style et l'état de navigation initial.

        Entrées:
            root (tk.Tk | None): Fenêtre racine optionnelle.

        Sortie:
            None: L'application est initialisée sur aucun écran actif.
        """
        self.root = root or tk.Tk()
        self.root.title("Monopoly POO")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)

        self._configure_style()
        self.current_view: ttk.Frame | None = None
        self.game_window: GameWindow | None = None
        self.save_directory = Path.cwd() / "saves"
        self.save_directory.mkdir(parents=True, exist_ok=True)
        self.rule_preset_directory = Path.cwd() / "rule_presets"
        self.rule_preset_directory.mkdir(parents=True, exist_ok=True)
        self.pending_player_names: list[str] = ["Alice", "Bob"]
        self.pending_game_options = GameOptions.classic()

    def _configure_style(self) -> None:
        """Configure les styles communs au jeu et aux nouveaux écrans d'accueil.

        Entrées:
            Aucune.

        Sortie:
            None: Les styles ``ttk`` et la couleur de fond racine sont appliqués.
        """
        style = ttk.Style(self.root)
        available = style.theme_names()

        if "clam" in available:
            style.theme_use("clam")

        background = "#EEF2F5"
        home_background = "#E6ECE9"
        card_background = "#FFFFFF"

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
        style.configure("Card.TLabelframe", padding=6, background=background)
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
        style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

        style.configure("Home.TFrame", background=home_background)
        style.configure(
            "HomeSubtitle.TLabel",
            background=home_background,
            foreground="#263238",
            font=("Arial", 17, "bold"),
        )
        style.configure(
            "HomeText.TLabel",
            background=home_background,
            foreground="#5B686F",
            font=("Arial", 11),
        )
        style.configure(
            "HomeHint.TLabel",
            background=home_background,
            foreground="#7B858A",
            font=("Arial", 9),
        )
        style.configure(
            "HomePrimary.TButton",
            padding=(20, 12),
            font=("Arial", 12, "bold"),
        )
        style.configure(
            "HomeSecondary.TButton",
            padding=(20, 10),
            font=("Arial", 11),
        )
        style.configure("SetupCard.TFrame", background=card_background)
        style.configure(
            "SetupTitle.TLabel",
            background=card_background,
            foreground="#263238",
            font=("Arial", 24, "bold"),
        )
        style.configure(
            "SetupSubtitle.TLabel",
            background=card_background,
            foreground="#69767D",
            font=("Arial", 11),
        )
        style.configure(
            "SetupLabel.TLabel",
            background=card_background,
            foreground="#364149",
            font=("Arial", 10, "bold"),
        )

    def _replace_view(self, view: ttk.Frame) -> None:
        """Détruit l'écran courant puis affiche le nouveau sur toute la fenêtre.

        Entrées:
            view (ttk.Frame): Nouvel écran déjà construit.

        Sortie:
            None: ``current_view`` référence désormais l'écran affiché.
        """
        if self.current_view is not None:
            self.current_view.destroy()

        self.current_view = view
        self.current_view.pack(fill="both", expand=True)

    def show_home(self) -> None:
        """Affiche le menu d'accueil principal.

        Entrées:
            Aucune.

        Sortie:
            None: Toute partie ou formulaire visible est remplacé par l'accueil.
        """
        self.game_window = None
        view = HomeView(
            self.root,
            new_game_callback=self.start_new_game_setup,
            load_game_callback=self.show_save_browser,
            quit_callback=self.root.destroy,
        )
        self._replace_view(view)


    def start_new_game_setup(self) -> None:
        """Réinitialise le brouillon puis ouvre une nouvelle préparation de partie.

        Entrées:
            Aucune.

        Sortie:
            None: Les noms par défaut et règles classiques deviennent actifs.
        """
        self.pending_player_names = ["Alice", "Bob"]
        self.pending_game_options = GameOptions.classic()
        self.show_player_setup()

    def show_player_setup(self) -> None:
        """Affiche les joueurs avec le profil de règles actuellement mémorisé.

        Entrées:
            Aucune.

        Sortie:
            None: Le formulaire restaure noms et règles après chaque aller-retour.
        """
        view = PlayerSetupView(
            self.root,
            start_callback=self.start_game,
            back_callback=self.show_home,
            rules_callback=self.show_rule_customization,
            player_names=self.pending_player_names,
            options=self.pending_game_options,
        )
        self._replace_view(view)

    def show_rule_customization(
        self,
        player_names: list[str],
        options: GameOptions,
    ) -> None:
        """Ouvre l'éditeur en mémorisant les noms déjà saisis.

        Entrées:
            player_names (list[str]): Noms courants du formulaire.
            options (GameOptions): Profil actif avant modification.

        Sortie:
            None: L'éditeur de règles remplace temporairement l'écran des joueurs.
        """
        self.pending_player_names = list(player_names)
        self.pending_game_options = options
        view = RuleCustomizationView(
            self.root,
            options=options,
            save_callback=self.apply_custom_rules,
            cancel_callback=self.show_player_setup,
            preset_directory=self.rule_preset_directory,
        )
        self._replace_view(view)

    def apply_custom_rules(self, options: GameOptions) -> None:
        """Mémorise le profil personnalisé puis revient à l'écran des joueurs.

        Entrées:
            options (GameOptions): Profil validé dans l'éditeur.

        Sortie:
            None: Le résumé affiché dans la préparation est mis à jour.
        """
        self.pending_game_options = options
        self.show_player_setup()

    def start_game(
        self,
        player_names: list[str],
        options: GameOptions | None = None,
    ) -> None:
        """Crée une partie avec joueurs et options validés puis affiche le plateau.

        Entrées:
            player_names (list[str]): Noms des joueurs dans leur ordre de création.
            options (GameOptions | None): Réglages de partie ; classiques si absents.

        Sortie:
            None: Une nouvelle instance ``Game`` et sa vue deviennent actives.
        """
        selected_options = options or GameOptions.classic()
        self.pending_player_names = list(player_names)
        self.pending_game_options = selected_options
        self.show_game(
            Game(player_names, options=selected_options),
            loaded=False,
        )

    def show_game(self, game: Game, loaded: bool = False) -> None:
        """Affiche une instance de partie neuve ou chargée.

        Entrées:
            game (Game): Partie à connecter à l'interface.
            loaded (bool): Indique si la partie provient d'une sauvegarde.

        Sortie:
            None: Un ``GameWindow`` devient la vue principale.
        """
        window = GameWindow(
            self.root,
            game,
            new_game_callback=self.show_home,
            save_game_callback=self.save_game_to_file,
            loaded=loaded,
        )
        self.game_window = window
        self._replace_view(window)

    def save_game_to_file(self, game: Game) -> str | None:
        """Demande un fichier puis sauvegarde la partie courante en JSON.

        Entrées:
            game (Game): Partie à écrire.

        Sortie:
            str | None: Chemin sauvegardé, ou ``None`` si l'utilisateur annule.
        """
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Sauvegarder la partie",
            initialdir=self.save_directory,
            defaultextension=".json",
            filetypes=[
                ("Sauvegarde Monopoly", "*.json"),
                ("Tous les fichiers", "*.*"),
            ],
            initialfile=(
                f"partie_{game.players[0].name.lower().replace(' ', '_')}_"
                f"tour_{game.upcoming_turn_number}.json"
            ),
        )
        if not path:
            return None

        try:
            saved = save_game(game, path)
        except (OSError, SaveGameError) as error:
            messagebox.showerror(
                "Sauvegarde impossible",
                str(error),
                parent=self.root,
            )
            return None
        return str(saved)

    def show_save_browser(self) -> None:
        """Affiche les sauvegardes locales et leurs métadonnées avant chargement.

        Entrées:
            Aucune.

        Sortie:
            None: L'accueil est remplacé par le navigateur de sauvegardes.
        """
        view = SaveBrowserView(
            self.root,
            saves=list_save_metadata(self.save_directory),
            load_callback=self.load_game_path,
            browse_callback=self.browse_load_game,
            back_callback=self.show_home,
        )
        self._replace_view(view)

    def load_game_path(self, path: str) -> None:
        """Charge une sauvegarde connue à partir de son chemin.

        Entrées:
            path (str): Fichier JSON à restaurer.

        Sortie:
            None: La partie chargée remplace le navigateur si elle est valide.
        """
        try:
            game = load_game(path)
        except (OSError, SaveGameError) as error:
            messagebox.showerror(
                "Chargement impossible",
                str(error),
                parent=self.root,
            )
            return
        self.show_game(game, loaded=True)

    def browse_load_game(self) -> None:
        """Permet de sélectionner une sauvegarde située hors du dossier local.

        Entrées:
            Aucune.

        Sortie:
            None: Le fichier choisi est chargé s'il est valide.
        """
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Charger une partie",
            initialdir=self.save_directory,
            filetypes=[
                ("Sauvegarde Monopoly", "*.json"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if path:
            self.load_game_path(path)

    def run(self) -> None:
        """Affiche l'accueil puis démarre la boucle événementielle Tkinter.

        Entrées:
            Aucune.

        Sortie:
            None: La méthode reste dans ``mainloop`` jusqu'à fermeture.
        """
        self.show_home()
        self.root.mainloop()
