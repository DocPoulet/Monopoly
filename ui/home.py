"""Écrans d'accueil, de préparation et de chargement intégrés à la fenêtre principale."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from monopoly.options import GameOptions
from monopoly.board_config import BoardConfig
from .theme import VisualPreferences, theme_palette


class HomeView(ttk.Frame):
    """Affiche le menu d'accueil principal du jeu.

    Entrées:
        master (tk.Misc): Conteneur parent.
        new_game_callback (callable): Fonction appelée après un clic sur Nouvelle partie.
        load_game_callback (callable): Fonction appelée après un clic sur Charger une partie.
        simulation_callback (callable): Fonction ouvrant le laboratoire de simulations.
        options_callback (callable): Fonction ouvrant les options globales d'affichage.
        quit_callback (callable): Fonction appelée après un clic sur Quitter.

    Sortie:
        HomeView: Écran d'accueil intégré à la fenêtre principale.
    """

    def __init__(
        self,
        master: tk.Misc,
        new_game_callback: object,
        load_game_callback: object,
        simulation_callback: object,
        options_callback: object,
        quit_callback: object,
        visual_preferences: VisualPreferences | None = None,
    ) -> None:
        """Construit l'accueil V22.2 avec preview isométrique et cartes d'action.

        Entrées:
            master (tk.Misc): Conteneur parent.
            new_game_callback (object): Callback du bouton Nouvelle partie.
            load_game_callback (object): Callback du bouton Charger une partie.
            simulation_callback (object): Callback du laboratoire de simulations.
            options_callback (object): Callback du menu d'options d'affichage.
            quit_callback (object): Callback du bouton Quitter.
            visual_preferences (VisualPreferences | None): Style courant à refléter dans la preview.

        Sortie:
            None: L'écran d'accueil responsive est prêt à être affiché.
        """
        super().__init__(master, style="Home.TFrame")
        self.new_game_callback = new_game_callback
        self.load_game_callback = load_game_callback
        self.simulation_callback = simulation_callback
        self.options_callback = options_callback
        self.quit_callback = quit_callback
        self.visual_preferences = visual_preferences or VisualPreferences.default()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        shell = ttk.Frame(self, style="Home.TFrame", padding=28)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=5)
        shell.columnconfigure(1, weight=4)
        shell.rowconfigure(0, weight=1)

        hero = ttk.Frame(shell, style="V22Card.TFrame", padding=22)
        hero.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        hero.columnconfigure(0, weight=1)
        hero.rowconfigure(3, weight=1)
        ttk.Label(hero, text="MONOPOLY POO", style="V22Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            hero,
            text="V22.2.2 • diorama isométrique",
            style="V22MutedCard.TLabel",
            font=("Arial", 11, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 12))
        ttk.Label(
            hero,
            text=(
                "Plateau isométrique flottant, pions animés, HUD périphérique et panneaux "
                "intégrés — toujours sur le même moteur POO indépendant."
            ),
            style="V22Card.TLabel",
            wraplength=620,
            justify="left",
        ).grid(row=2, column=0, sticky="w")
        self.home_preview = tk.Canvas(hero, height=430, highlightthickness=0, background="#DCE8E1")
        self.home_preview.grid(row=3, column=0, sticky="nsew", pady=(16, 0))
        self.home_preview.bind("<Configure>", self._draw_home_preview)

        menu = ttk.Frame(shell, style="V22Card.TFrame", padding=24)
        menu.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        menu.columnconfigure(0, weight=1)
        ttk.Label(menu, text="Que voulez-vous faire ?", style="V22Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(
            menu,
            text="Le style du plateau et des menus se règle dans Options. Les pions se choisissent à la création de partie.",
            style="V22MutedCard.TLabel",
            wraplength=430,
        ).grid(row=1, column=0, sticky="w", pady=(0, 22))

        actions = (
            ("Nouvelle partie", "Créer joueurs, règles, plateau et choisir les pions", self._start_new_game, True),
            ("Charger une partie", "Reprendre une sauvegarde avec son profil visuel", self._load_game, False),
            ("Laboratoire", "Simulations, heatmaps, statistiques et rapports", self._open_simulation_lab, False),
            ("Options", "Style du plateau, thème des menus et préférences visuelles", self._open_options, False),
            ("Quitter", "Fermer l'application", self._quit, False),
        )
        for row, (title, subtitle, command, primary) in enumerate(actions, start=2):
            card = ttk.Frame(menu, style="V22SurfaceAlt.TFrame", padding=12)
            card.grid(row=row, column=0, sticky="ew", pady=5)
            card.columnconfigure(0, weight=1)
            ttk.Label(card, text=title, font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
            ttk.Label(card, text=subtitle, style="Muted.TLabel", wraplength=330).grid(row=1, column=0, sticky="w")
            ttk.Button(
                card,
                text="Ouvrir",
                style="Primary.TButton" if primary else "TButton",
                command=command,
            ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        ttk.Label(
            menu,
            text="V23 introduira l'architecture multi-modes : Classic, Empire, Builder, Gamer, Deal…",
            style="V22MutedCard.TLabel",
            wraplength=430,
        ).grid(row=8, column=0, sticky="sw", pady=(22, 0))

    def _draw_home_preview(self, event: tk.Event | None = None) -> None:
        """Dessine le diorama isométrique V22.2 sur l'écran d'accueil.

        Entrées:
            event (tk.Event | None): Redimensionnement éventuel du Canvas.

        Sortie:
            None: La miniature isométrique s'adapte à la zone disponible.
        """
        canvas = self.home_preview
        canvas.delete("all")
        width = max(canvas.winfo_width(), 420)
        height = max(canvas.winfo_height(), 300)
        palette = theme_palette(self.visual_preferences)
        style = self.visual_preferences.style
        canvas.configure(background=palette["background"])
        cx = width * 0.50
        top_y = height * 0.15
        half_w = width * 0.39
        half_h = height * 0.31
        outer = (
            cx, top_y,
            cx + half_w, top_y + half_h,
            cx, top_y + half_h * 2,
            cx - half_w, top_y + half_h,
        )
        thickness = height * 0.035
        canvas.create_polygon(
            cx + half_w, top_y + half_h,
            cx, top_y + half_h * 2,
            cx, top_y + half_h * 2 + thickness,
            cx + half_w, top_y + half_h + thickness,
            fill=style.board_edge, outline="",
        )
        canvas.create_polygon(
            cx, top_y + half_h * 2,
            cx - half_w, top_y + half_h,
            cx - half_w, top_y + half_h + thickness,
            cx, top_y + half_h * 2 + thickness,
            fill=style.board_edge, outline="",
        )
        canvas.create_polygon(*outer, fill=style.board_surface, outline=style.board_edge, width=4)
        inset = 0.23
        inner = (
            cx, top_y + half_h * inset * 2,
            cx + half_w * (1 - inset), top_y + half_h,
            cx, top_y + half_h * (2 - inset * 2),
            cx - half_w * (1 - inset), top_y + half_h,
        )
        canvas.create_polygon(*inner, fill=style.board_center, outline=style.board_edge, width=2)
        colors = ("#8B5A2B", "#79CFE8", "#D95FA6", "#F39C12", "#E74C3C", "#F4D03F", "#27AE60", "#3156A6")
        for index, color in enumerate(colors):
            ratio = 0.12 + index * 0.105
            x = cx - half_w + half_w * ratio
            y = top_y + half_h + half_h * ratio
            canvas.create_polygon(
                x, y,
                x + width * 0.045, y + height * 0.017,
                x + width * 0.032, y + height * 0.045,
                x - width * 0.013, y + height * 0.028,
                fill=color, outline="",
            )
        canvas.create_text(cx, top_y + half_h * 0.95, text="MONOPOLY", font=("Arial", max(22, int(width * 0.04)), "bold"), fill=style.board_edge)
        canvas.create_text(cx, top_y + half_h * 1.18, text=f"POO • {style.name.upper()}", font=("Arial", max(9, int(width * 0.014)), "bold"), fill=style.accent)
        canvas.create_text(cx - half_w * 0.88, top_y + half_h * 1.08, text="●", font=("Arial", 20, "bold"), fill="#D94343")
        canvas.create_text(cx + half_w * 0.86, top_y + half_h * 0.92, text="◆", font=("Arial", 20, "bold"), fill="#3478D4")

    def _start_new_game(self) -> None:
        """Transmet au contrôleur la demande d'ouvrir l'écran des joueurs.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback est exécuté s'il est appelable.
        """
        if callable(self.new_game_callback):
            self.new_game_callback()

    def _load_game(self) -> None:
        """Transmet au contrôleur la demande d'ouvrir le navigateur de sauvegardes.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback de chargement est exécuté s'il est appelable.
        """
        if callable(self.load_game_callback):
            self.load_game_callback()

    def _open_simulation_lab(self) -> None:
        """Transmet la demande d'ouvrir le laboratoire de simulation V21.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback est exécuté s'il est disponible.
        """
        if callable(self.simulation_callback):
            self.simulation_callback()

    def _open_options(self) -> None:
        """Ouvre les préférences globales de style et d'affichage.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback d'options est déclenché s'il est disponible.
        """
        if callable(self.options_callback):
            self.options_callback()

    def _quit(self) -> None:
        """Transmet au contrôleur la demande de fermer l'application.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback est exécuté s'il est disponible.
        """
        if callable(self.quit_callback):
            self.quit_callback()



class PlayerSetupView(ttk.Frame):
    """Demande les joueurs puis permet d'ouvrir l'éditeur de règles.

    Entrées:
        master (tk.Misc): Conteneur parent.
        start_callback (callable): Fonction recevant noms et règles validés.
        back_callback (callable): Fonction permettant de revenir à l'accueil.
        rules_callback (callable): Fonction ouvrant l'éditeur de règles.
        board_callback (callable): Fonction ouvrant l'éditeur de plateau.
        pack_import_callback (callable): Importe un pack complet règles + plateau.
        pack_export_callback (callable): Exporte le profil courant en pack complet.
        visual_callback (callable): Ouvre le sélecteur de pions V22.
        player_names (list[str] | None): Noms déjà saisis à restaurer.
        options (GameOptions | None): Profil de règles déjà configuré.
        board_config (BoardConfig | None): Plateau déjà sélectionné.
        visual_preferences (VisualPreferences | None): Apparence V22 déjà choisie.

    Sortie:
        PlayerSetupView: Formulaire intégré de création de partie.
    """

    MAX_PLAYERS = 4

    def __init__(
        self,
        master: tk.Misc,
        start_callback: object,
        back_callback: object,
        rules_callback: object | None = None,
        board_callback: object | None = None,
        pack_import_callback: object | None = None,
        pack_export_callback: object | None = None,
        visual_callback: object | None = None,
        player_names: list[str] | None = None,
        options: GameOptions | None = None,
        board_config: BoardConfig | None = None,
        visual_preferences: VisualPreferences | None = None,
    ) -> None:
        """Construit les champs joueurs, le résumé des règles et les boutons.

        Entrées:
            master (tk.Misc): Conteneur parent.
            start_callback (object): Callback appelé avec joueurs et règles.
            back_callback (object): Callback du bouton Retour.
            rules_callback (object | None): Callback ouvrant la personnalisation des règles.
            board_callback (object | None): Callback ouvrant la personnalisation du plateau.
            pack_import_callback (object | None): Callback important un pack complet.
            pack_export_callback (object | None): Callback exportant règles et plateau.
            visual_callback (object | None): Callback ouvrant le sélecteur de pions V22.
            player_names (list[str] | None): Noms à restaurer.
            options (GameOptions | None): Profil de règles courant.
            board_config (BoardConfig | None): Plateau courant.
            visual_preferences (VisualPreferences | None): Apparence graphique courante.

        Sortie:
            None: Le formulaire est prêt à être utilisé.
        """
        super().__init__(master, style="Home.TFrame")
        self.start_callback = start_callback
        self.back_callback = back_callback
        self.rules_callback = rules_callback
        self.board_callback = board_callback
        self.pack_import_callback = pack_import_callback
        self.pack_export_callback = pack_export_callback
        self.visual_callback = visual_callback
        self.options = options or GameOptions.classic()
        self.board_config = (board_config or BoardConfig.standard()).clone()
        self.visual_preferences = visual_preferences or VisualPreferences.default()
        self.entries: list[ttk.Entry] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        card = ttk.Frame(self, style="SetupCard.TFrame", padding=26)
        card.grid(row=0, column=0)
        card.columnconfigure(1, weight=1)

        ttk.Label(
            card,
            text="Nouvelle partie",
            style="SetupTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(
            card,
            text="Choisissez entre 2 et 4 joueurs, puis ajustez les règles si nécessaire.",
            style="SetupSubtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 16))

        defaults = list(player_names or ["Alice", "Bob"])
        defaults.extend([""] * max(0, self.MAX_PLAYERS - len(defaults)))

        for index in range(self.MAX_PLAYERS):
            ttk.Label(
                card,
                text=f"Joueur {index + 1}",
                style="SetupLabel.TLabel",
            ).grid(
                row=index + 2,
                column=0,
                sticky="e",
                padx=(0, 12),
                pady=3,
            )
            entry = ttk.Entry(card, width=30, font=("Arial", 10))
            entry.insert(0, defaults[index])
            entry.grid(row=index + 2, column=1, sticky="ew", pady=3)
            entry.bind("<Return>", self._on_enter)
            self.entries.append(entry)

        rules_frame = ttk.LabelFrame(
            card,
            text="Règles de la partie",
            padding=10,
        )
        rules_frame.grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 0),
        )
        rules_frame.columnconfigure(0, weight=1)

        self.rules_summary_label = ttk.Label(
            rules_frame,
            text=self.options.summary(),
            style="Muted.TLabel",
            wraplength=560,
        )
        self.rules_summary_label.grid(row=0, column=0, sticky="w", padx=(0, 12))

        ttk.Button(
            rules_frame,
            text="Personnaliser les règles",
            command=self._customize_rules,
        ).grid(row=0, column=1, sticky="e")

        board_frame = ttk.LabelFrame(
            card,
            text="Plateau et cartes",
            padding=10,
        )
        board_frame.grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0),
        )
        board_frame.columnconfigure(0, weight=1)
        self.board_summary_label = ttk.Label(
            board_frame,
            text=self.board_config.summary(),
            style="Muted.TLabel",
            wraplength=560,
        )
        self.board_summary_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Button(
            board_frame,
            text="Personnaliser le plateau",
            command=self._customize_board,
        ).grid(row=0, column=1, sticky="e")

        pack_frame = ttk.LabelFrame(
            card,
            text="Pack complet",
            padding=10,
        )
        pack_frame.grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0),
        )
        pack_frame.columnconfigure(0, weight=1)
        pack_frame.columnconfigure(1, weight=1)
        ttk.Button(
            pack_frame,
            text="Importer règles + plateau",
            command=self._import_pack,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(
            pack_frame,
            text="Exporter règles + plateau",
            command=self._export_pack,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        visual_frame = ttk.LabelFrame(
            card,
            text="Pions",
            padding=10,
        )
        visual_frame.grid(
            row=9,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0),
        )
        visual_frame.columnconfigure(0, weight=1)
        self.visual_summary_label = ttk.Label(
            visual_frame,
            text="Choisissez un pion différent pour chaque joueur. Le style et le thème se règlent depuis Options.",
            style="Muted.TLabel",
            wraplength=560,
        )
        self.visual_summary_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Button(
            visual_frame,
            text="Choisir les pions",
            command=self._customize_visual,
        ).grid(row=0, column=1, sticky="e")

        buttons = ttk.Frame(card, style="SetupCard.TFrame")
        buttons.grid(
            row=10,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(18, 0),
        )
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=2)

        ttk.Button(
            buttons,
            text="Retour",
            style="HomeSecondary.TButton",
            command=self._back,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ttk.Button(
            buttons,
            text="Commencer la partie",
            style="HomePrimary.TButton",
            command=self._confirm,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.entries[0].focus_set()

    def get_player_names(self) -> list[str]:
        """Retourne uniquement les noms non vides actuellement saisis.

        Entrées:
            Aucune autre que les champs du formulaire.

        Sortie:
            list[str]: Noms nettoyés dans l'ordre des champs.
        """
        names = [entry.get().strip() for entry in self.entries]
        return [name for name in names if name]

    @classmethod
    def validate_player_names(cls, names: list[str]) -> tuple[bool, str]:
        """Vérifie le nombre et l'unicité des noms de joueurs.

        Entrées:
            names (list[str]): Noms nettoyés à valider.

        Sortie:
            tuple[bool, str]: Validité et message d'erreur éventuel.
        """
        if len(names) < 2:
            return False, "Il faut au moins deux joueurs."
        if len(names) > cls.MAX_PLAYERS:
            return False, f"Le nombre maximum de joueurs est {cls.MAX_PLAYERS}."
        if len(set(names)) != len(names):
            return False, "Chaque joueur doit avoir un nom différent."
        return True, ""

    @staticmethod
    def validate_options(
        starting_cash_text: str,
        free_parking_text: str,
        turn_limit_text: str,
        auctions_enabled: bool,
    ) -> tuple[GameOptions | None, str]:
        """Conserve l'ancienne validation compacte pour compatibilité et tests.

        Entrées:
            starting_cash_text (str): Argent initial saisi.
            free_parking_text (str): Bonus du Parc Gratuit.
            turn_limit_text (str): Limite de tours.
            auctions_enabled (bool): État de l'option d'enchères.

        Sortie:
            tuple[GameOptions | None, str]: Profil classique modifié ou message d'erreur.
        """
        try:
            options = GameOptions(
                starting_cash=int(starting_cash_text),
                auctions_enabled=bool(auctions_enabled),
                free_parking_bonus=int(free_parking_text),
                turn_limit=int(turn_limit_text),
            )
            options.validate()
        except ValueError:
            return None, "Les options doivent contenir des nombres entiers valides."
        return options, ""

    def _customize_rules(self) -> None:
        """Ouvre l'éditeur de règles sans perdre les noms déjà saisis.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit les noms courants et le profil actif.
        """
        if callable(self.rules_callback):
            self.rules_callback(self.get_player_names(), self.options)

    def _customize_board(self) -> None:
        """Ouvre l'éditeur de plateau sans perdre joueurs ni règles.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit les noms, règles et plateau courants.
        """
        if callable(self.board_callback):
            self.board_callback(
                self.get_player_names(),
                self.options,
                self.board_config,
            )

    def _customize_visual(self) -> None:
        """Ouvre le sélecteur de pions sans perdre noms, règles ni plateau.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit toutes les informations nécessaires au retour.
        """
        if callable(self.visual_callback):
            self.visual_callback(
                self.get_player_names(),
                self.options,
                self.board_config,
                self.visual_preferences,
            )

    def _import_pack(self) -> None:
        """Demande l'import d'un pack complet sans perdre les noms des joueurs.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit les noms actuellement saisis.
        """
        if callable(self.pack_import_callback):
            self.pack_import_callback(self.get_player_names())

    def _export_pack(self) -> None:
        """Demande l'export du couple règles + plateau actuellement préparé.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit les deux configurations actives.
        """
        if callable(self.pack_export_callback):
            self.pack_export_callback(self.options, self.board_config)

    def _on_enter(self, event: tk.Event) -> None:
        """Tente de lancer la partie lorsque l'utilisateur appuie sur Entrée.

        Entrées:
            event (tk.Event): Événement clavier Tkinter.

        Sortie:
            None: La validation du formulaire est déclenchée.
        """
        self._confirm()

    def _confirm(self) -> None:
        """Valide les joueurs puis démarre la partie avec les règles choisies.

        Entrées:
            Aucune.

        Sortie:
            None: La partie est demandée ou une erreur de joueurs est affichée.
        """
        names = self.get_player_names()
        valid, error = self.validate_player_names(names)
        if not valid:
            messagebox.showwarning("Joueurs invalides", error, parent=self)
            return

        if callable(self.start_callback):
            import inspect

            parameters = inspect.signature(self.start_callback).parameters
            if len(parameters) >= 4:
                self.start_callback(
                    names,
                    self.options,
                    self.board_config,
                    self.visual_preferences,
                )
            elif len(parameters) >= 3:
                self.start_callback(names, self.options, self.board_config)
            else:
                self.start_callback(names, self.options)

    def _back(self) -> None:
        """Retourne au menu d'accueil sans créer de partie.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback Retour est appelé s'il est disponible.
        """
        if callable(self.back_callback):
            self.back_callback()


class SaveBrowserView(ttk.Frame):
    """Affiche les sauvegardes connues avec un aperçu avant chargement.

    Entrées:
        master (tk.Misc): Conteneur parent.
        saves (list[dict]): Métadonnées des sauvegardes disponibles.
        load_callback (Callable[[str], None]): Charge le chemin sélectionné.
        browse_callback (Callable[[], None]): Ouvre un fichier situé ailleurs.
        back_callback (Callable[[], None]): Revient à l'accueil.

    Sortie:
        SaveBrowserView: Écran intégré de sélection de sauvegarde.
    """

    def __init__(
        self,
        master: tk.Misc,
        saves: list[dict],
        load_callback: Callable[[str], None],
        browse_callback: Callable[[], None],
        back_callback: Callable[[], None],
    ) -> None:
        """Construit la liste des sauvegardes et le panneau de métadonnées.

        Entrées:
            master (tk.Misc): Conteneur parent.
            saves (list[dict]): Métadonnées fournies par la persistance.
            load_callback (Callable[[str], None]): Callback de chargement.
            browse_callback (Callable[[], None]): Callback de sélection externe.
            back_callback (Callable[[], None]): Callback Retour.

        Sortie:
            None: L'écran est prêt à prévisualiser les sauvegardes.
        """
        super().__init__(master, style="Home.TFrame")
        self.saves = list(saves)
        self.load_callback = load_callback
        self.browse_callback = browse_callback
        self.back_callback = back_callback

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        card = ttk.Frame(self, style="SetupCard.TFrame", padding=28)
        card.grid(row=0, column=0, sticky="")
        card.columnconfigure(0, weight=2)
        card.columnconfigure(1, weight=3)
        card.rowconfigure(2, weight=1)

        ttk.Label(
            card,
            text="Charger une partie",
            style="SetupTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(
            card,
            text="Sélectionnez une sauvegarde pour voir son aperçu.",
            style="SetupSubtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 16))

        left = ttk.LabelFrame(card, text="Sauvegardes", padding=8)
        left.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            left,
            columns=("turn", "date"),
            show="tree headings",
            height=11,
            selectmode="browse",
        )
        self.tree.heading("#0", text="Fichier")
        self.tree.heading("turn", text="Tour")
        self.tree.heading("date", text="Date")
        self.tree.column("#0", width=190)
        self.tree.column("turn", width=55, anchor="center")
        self.tree.column("date", width=145)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        right = ttk.LabelFrame(card, text="Aperçu", padding=14)
        right.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)

        self.preview_title = ttk.Label(
            right,
            text="Aucune sauvegarde sélectionnée",
            font=("Arial", 14, "bold"),
        )
        self.preview_title.grid(row=0, column=0, sticky="w")

        self.preview_text = ttk.Label(
            right,
            text="",
            style="Muted.TLabel",
            justify="left",
            wraplength=390,
        )
        self.preview_text.grid(row=1, column=0, sticky="nw", pady=(8, 0))

        buttons = ttk.Frame(card, style="SetupCard.TFrame")
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        for column in range(3):
            buttons.columnconfigure(column, weight=1)

        ttk.Button(
            buttons,
            text="Retour",
            command=self.back_callback,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ttk.Button(
            buttons,
            text="Parcourir un fichier…",
            command=self.browse_callback,
        ).grid(row=0, column=1, sticky="ew", padx=4)

        self.load_button = ttk.Button(
            buttons,
            text="Charger",
            style="Primary.TButton",
            command=self._load_selected,
        )
        self.load_button.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        self.load_button.state(["disabled"])

        for index, metadata in enumerate(self.saves):
            saved_at = str(metadata.get("saved_at", "")).replace("T", " ")
            if "+" in saved_at:
                saved_at = saved_at.split("+", 1)[0]
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                text=str(metadata.get("filename", "Sauvegarde")),
                values=(metadata.get("turn_number", 0), saved_at),
            )

        if self.saves:
            self.tree.selection_set("0")
            self.tree.focus("0")
            self._selection_changed(None)
        else:
            self.preview_text.configure(
                text=(
                    "Aucune sauvegarde dans le dossier local.\n\n"
                    "Utilisez « Parcourir un fichier… » pour charger un JSON situé ailleurs."
                )
            )

    def _selected_metadata(self) -> dict | None:
        """Retourne les métadonnées de la sauvegarde sélectionnée.

        Entrées:
            Aucune.

        Sortie:
            dict | None: Métadonnées ou ``None`` sans sélection valide.
        """
        selection = self.tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        if not 0 <= index < len(self.saves):
            return None
        return self.saves[index]

    def _selection_changed(self, event: tk.Event | None) -> None:
        """Actualise l'aperçu après un changement de ligne.

        Entrées:
            event (tk.Event | None): Événement de sélection, éventuellement absent en test.

        Sortie:
            None: Les joueurs, le tour et la date sont affichés.
        """
        metadata = self._selected_metadata()
        if metadata is None:
            self.load_button.state(["disabled"])
            return

        players = ", ".join(metadata.get("players", [])) or "Inconnus"
        winner = metadata.get("winner")
        state = f"Vainqueur : {winner}" if winner else (
            f"Joueurs encore actifs : {metadata.get('active_players', '?')}"
        )
        self.preview_title.configure(text=str(metadata.get("filename", "Sauvegarde")))
        self.preview_text.configure(
            text=(
                f"Joueurs : {players}\n"
                f"Tour : {metadata.get('turn_number', 0)}\n"
                f"Plateau : {metadata.get('board_name', 'Plateau standard')}\n"
                f"{state}\n"
                f"Sauvegardée : {str(metadata.get('saved_at', '')).replace('T', ' ')}"
            )
        )
        self.load_button.state(["!disabled"])

    def _load_selected(self) -> None:
        """Charge la sauvegarde actuellement sélectionnée.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit le chemin du fichier choisi.
        """
        metadata = self._selected_metadata()
        if metadata is not None:
            self.load_callback(str(metadata["path"]))
