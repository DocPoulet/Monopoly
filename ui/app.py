"""Application Tkinter principale et navigation entre les écrans du jeu."""

from __future__ import annotations

from pathlib import Path
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from monopoly import BoardConfig, Game, GameOptions
from monopoly.persistence import (
    SaveGameError,
    list_save_metadata,
    load_game,
    save_game,
)
from monopoly.profile_packs import ProfilePackError, load_profile_pack, save_profile_pack

from .game_window import GameWindow
from .home import HomeView, PlayerSetupView, SaveBrowserView
from .rule_customization import RuleCustomizationView
from .simulation_lab import SimulationLabView
from .board_customization import BoardCustomizationView
from .theme import VisualPreferences, apply_ttk_theme
from .pawns import normalize_pawn_ids
from .visual_customization import VisualCustomizationView


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
        self.root.title("Monopoly POO — V22.2.2")
        self.root.geometry("1500x900")
        self.root.minsize(1050, 700)
        self._maximize_windowed()

        self.pending_visual_preferences = VisualPreferences.default()
        self._configure_style()
        self.current_view: ttk.Frame | None = None
        self.game_window: GameWindow | None = None
        self.save_directory = Path.cwd() / "saves"
        self.save_directory.mkdir(parents=True, exist_ok=True)
        self.rule_preset_directory = Path.cwd() / "rule_presets"
        self.rule_preset_directory.mkdir(parents=True, exist_ok=True)
        self.board_preset_directory = Path.cwd() / "board_presets"
        self.board_preset_directory.mkdir(parents=True, exist_ok=True)
        self.pending_player_names: list[str] = ["Alice", "Bob"]
        self.pending_game_options = GameOptions.classic()
        self.pending_board_config = BoardConfig.standard()

    def _maximize_windowed(self) -> None:
        """Ouvre l'application sur toute la zone disponible sans plein écran exclusif.

        Entrées:
            Aucune.

        Sortie:
            None: La fenêtre est maximisée lorsque le gestionnaire le permet.
        """
        try:
            self.root.state("zoomed")
            return
        except tk.TclError:
            pass
        try:
            self.root.attributes("-zoomed", True)
        except tk.TclError:
            return

    def _configure_style(self) -> None:
        """Applique le style V22 actif à tous les écrans Tkinter.

        Entrées:
            Aucune.

        Sortie:
            None: La palette dépend du style et du thème actuellement préparés.
        """
        self.palette = apply_ttk_theme(self.root, self.pending_visual_preferences)

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
            simulation_callback=self.show_simulation_lab,
            options_callback=self.show_display_options,
            quit_callback=self.root.destroy,
            visual_preferences=self.pending_visual_preferences,
        )
        self._replace_view(view)


    def show_simulation_lab(self) -> None:
        """Affiche le laboratoire V21 depuis le menu principal.

        Entrées:
            Aucune.

        Sortie:
            None: L'écran courant est remplacé par ``SimulationLabView``.
        """
        self.game_window = None
        view = SimulationLabView(
            self.root,
            back_callback=self.show_home,
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
        self.pending_board_config = BoardConfig.standard()
        self._configure_style()
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
            board_callback=self.show_board_customization,
            pack_import_callback=self.import_profile_pack,
            pack_export_callback=self.export_profile_pack,
            visual_callback=self.show_pawn_customization,
            player_names=self.pending_player_names,
            options=self.pending_game_options,
            board_config=self.pending_board_config,
            visual_preferences=self.pending_visual_preferences,
        )
        self._replace_view(view)

    def show_pawn_customization(
        self,
        player_names: list[str],
        options: GameOptions,
        board_config: BoardConfig,
        visual_preferences: VisualPreferences,
    ) -> None:
        """Ouvre le sélecteur de pions en conservant joueurs, règles et plateau.

        Entrées:
            player_names (list[str]): Noms actuellement saisis.
            options (GameOptions): Règles courantes.
            board_config (BoardConfig): Plateau courant.
            visual_preferences (VisualPreferences): Apparence courante.

        Sortie:
            None: L'écran des pions remplace temporairement la préparation.
        """
        self.pending_player_names = list(player_names)
        self.pending_game_options = options
        self.pending_board_config = board_config.clone()
        self.pending_visual_preferences = visual_preferences
        view = VisualCustomizationView(
            self.root,
            player_names=self.pending_player_names,
            preferences=self.pending_visual_preferences,
            save_callback=self.apply_pawn_preferences,
            cancel_callback=self.show_player_setup,
            show_style_options=False,
            show_pawn_options=True,
            title="Choix des pions",
        )
        self._replace_view(view)

    def apply_pawn_preferences(self, preferences: VisualPreferences) -> None:
        """Mémorise les pions choisis puis revient à la préparation.

        Entrées:
            preferences (VisualPreferences): Profil contenant les pions validés.

        Sortie:
            None: Le choix des pions est conservé dans le brouillon courant.
        """
        self.pending_visual_preferences = preferences
        self.show_player_setup()

    def show_display_options(self) -> None:
        """Ouvre les options globales de style, thème et affichage.

        Entrées:
            Aucune.

        Sortie:
            None: Les préférences visuelles sont éditées hors de la création de partie.
        """
        view = VisualCustomizationView(
            self.root,
            player_names=self.pending_player_names,
            preferences=self.pending_visual_preferences,
            save_callback=self.apply_display_options,
            cancel_callback=self.show_home,
            show_style_options=True,
            show_pawn_options=False,
            title="Options d'affichage",
        )
        self._replace_view(view)

    def apply_display_options(self, preferences: VisualPreferences) -> None:
        """Applique les options visuelles globales puis revient à l'accueil.

        Entrées:
            preferences (VisualPreferences): Nouveau style, thème et préférences d'affichage.

        Sortie:
            None: Le thème global est appliqué immédiatement puis l'accueil est restauré.
        """
        self.pending_visual_preferences = preferences
        self._configure_style()
        self.show_home()

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

    def show_board_customization(
        self,
        player_names: list[str],
        options: GameOptions,
        board_config: BoardConfig,
    ) -> None:
        """Ouvre l'éditeur de plateau en conservant joueurs et règles.

        Entrées:
            player_names (list[str]): Noms actuellement saisis.
            options (GameOptions): Profil de règles courant.
            board_config (BoardConfig): Plateau courant à éditer.

        Sortie:
            None: L'éditeur de plateau remplace temporairement la préparation.
        """
        self.pending_player_names = list(player_names)
        self.pending_game_options = options
        self.pending_board_config = board_config.clone()
        view = BoardCustomizationView(
            self.root,
            board_config=self.pending_board_config,
            save_callback=self.apply_custom_board,
            cancel_callback=self.show_player_setup,
            preset_directory=self.board_preset_directory,
        )
        self._replace_view(view)

    def apply_custom_board(self, board_config: BoardConfig) -> None:
        """Mémorise un plateau personnalisé puis revient à la préparation.

        Entrées:
            board_config (BoardConfig): Plateau validé par l'éditeur.

        Sortie:
            None: Le résumé du plateau est actualisé sur l'écran des joueurs.
        """
        self.pending_board_config = board_config.clone()
        self.show_player_setup()

    def apply_custom_rules(self, options: GameOptions) -> None:
        """Mémorise le profil personnalisé puis revient à l'écran des joueurs.

        Entrées:
            options (GameOptions): Profil validé dans l'éditeur.

        Sortie:
            None: Le résumé affiché dans la préparation est mis à jour.
        """
        self.pending_game_options = options
        self.show_player_setup()

    def import_profile_pack(self, player_names: list[str]) -> None:
        """Importe un fichier combinant règles et plateau dans la préparation courante.

        Entrées:
            player_names (list[str]): Noms déjà saisis à conserver.

        Sortie:
            None: Les deux configurations du pack remplacent le brouillon courant.
        """
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Importer un pack complet",
            filetypes=[("Pack Monopoly", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        try:
            pack = load_profile_pack(path)
        except ProfilePackError as error:
            messagebox.showerror("Import impossible", str(error), parent=self.root)
            return
        self.pending_player_names = list(player_names)
        self.pending_game_options = pack.options
        self.pending_board_config = pack.board_config.clone()
        self.show_player_setup()
        messagebox.showinfo(
            "Pack importé",
            f"Le pack « {pack.name} » a été appliqué aux règles et au plateau.",
            parent=self.root,
        )

    def export_profile_pack(
        self,
        options: GameOptions,
        board_config: BoardConfig,
    ) -> None:
        """Exporte les règles et le plateau courants dans un seul fichier portable.

        Entrées:
            options (GameOptions): Profil de règles actuellement préparé.
            board_config (BoardConfig): Plateau et cartes actuellement préparés.

        Sortie:
            None: Un fichier JSON est écrit après choix de destination.
        """
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Exporter un pack complet",
            defaultextension=".json",
            initialfile="pack_monopoly.json",
            filetypes=[("Pack Monopoly", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        try:
            save_profile_pack(
                path,
                Path(path).stem,
                options,
                board_config,
            )
        except (OSError, ValueError) as error:
            messagebox.showerror("Export impossible", str(error), parent=self.root)
            return
        messagebox.showinfo(
            "Pack exporté",
            "Les règles et le plateau ont été exportés ensemble.",
            parent=self.root,
        )

    def start_game(
        self,
        player_names: list[str],
        options: GameOptions | None = None,
        board_config: BoardConfig | None = None,
        visual_preferences: VisualPreferences | None = None,
    ) -> None:
        """Crée une partie avec joueurs et options validés puis affiche le plateau.

        Entrées:
            player_names (list[str]): Noms des joueurs dans leur ordre de création.
            options (GameOptions | None): Réglages de partie ; classiques si absents.
            board_config (BoardConfig | None): Plateau et cartes ; standards si absents.
            visual_preferences (VisualPreferences | None): Apparence V22 sélectionnée.

        Sortie:
            None: Une nouvelle instance ``Game`` et sa vue deviennent actives.
        """
        if not 2 <= len(player_names) <= 4:
            raise ValueError("Une nouvelle partie doit contenir entre 2 et 4 joueurs.")
        selected_options = options or GameOptions.classic()
        selected_board = (board_config or BoardConfig.standard()).clone()
        selected_visual = visual_preferences or self.pending_visual_preferences
        selected_visual = selected_visual.with_pawns(
            normalize_pawn_ids(selected_visual.pawn_ids, len(player_names))
        )
        self.pending_player_names = list(player_names)
        self.pending_game_options = selected_options
        self.pending_board_config = selected_board
        self.pending_visual_preferences = selected_visual
        self._configure_style()
        self.show_game(
            Game(
                player_names,
                options=selected_options,
                board_config=selected_board,
            ),
            loaded=False,
            visual_preferences=selected_visual,
        )

    def show_game(
        self,
        game: Game,
        loaded: bool = False,
        visual_preferences: VisualPreferences | None = None,
    ) -> None:
        """Affiche une instance de partie neuve ou chargée.

        Entrées:
            game (Game): Partie à connecter à l'interface.
            loaded (bool): Indique si la partie provient d'une sauvegarde.
            visual_preferences (VisualPreferences | None): Apparence à utiliser.

        Sortie:
            None: Un ``GameWindow`` devient la vue principale.
        """
        selected_visual = visual_preferences or self.pending_visual_preferences
        self.pending_visual_preferences = selected_visual
        self._configure_style()
        window = GameWindow(
            self.root,
            game,
            new_game_callback=self.show_home,
            save_game_callback=self.save_game_to_file,
            loaded=loaded,
            visual_preferences=selected_visual,
        )
        self.game_window = window
        self._replace_view(window)

    def save_game_to_file(
        self,
        game: Game,
        visual_preferences: VisualPreferences | None = None,
    ) -> str | None:
        """Demande un fichier puis sauvegarde la partie courante en JSON.

        Entrées:
            game (Game): Partie à écrire.
            visual_preferences (VisualPreferences | None): Apparence à joindre à la sauvegarde.

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
            selected_visual = visual_preferences or self.pending_visual_preferences
            self.pending_visual_preferences = selected_visual
            self._embed_visual_preferences(saved, selected_visual)
        except (OSError, SaveGameError) as error:
            messagebox.showerror(
                "Sauvegarde impossible",
                str(error),
                parent=self.root,
            )
            return None
        return str(saved)

    @staticmethod
    def _embed_visual_preferences(path: str | Path, preferences: VisualPreferences) -> None:
        """Ajoute des métadonnées UI optionnelles au JSON sans modifier le moteur.

        Entrées:
            path (str | Path): Sauvegarde moteur déjà écrite.
            preferences (VisualPreferences): Apparence de la partie.

        Sortie:
            None: La clé top-level ``ui_v22`` est ajoutée au fichier.
        """
        destination = Path(path)
        data = json.loads(destination.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data["ui_v22"] = preferences.to_dict()
            destination.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    @staticmethod
    def _read_visual_preferences(path: str | Path) -> VisualPreferences:
        """Lit l'apparence V22 d'une sauvegarde ou retourne le profil par défaut.

        Entrées:
            path (str | Path): Fichier JSON de sauvegarde.

        Sortie:
            VisualPreferences: Apparence enregistrée ou profil hybride de secours.
        """
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return VisualPreferences.default()
        if not isinstance(data, dict):
            return VisualPreferences.default()
        return VisualPreferences.from_dict(data.get("ui_v22"))

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
            visual = self._read_visual_preferences(path)
        except (OSError, SaveGameError) as error:
            messagebox.showerror(
                "Chargement impossible",
                str(error),
                parent=self.root,
            )
            return
        self.pending_visual_preferences = visual
        self.show_game(game, loaded=True, visual_preferences=visual)

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
