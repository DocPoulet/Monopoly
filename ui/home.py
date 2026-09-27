"""Écrans d'accueil, de préparation et de chargement intégrés à la fenêtre principale."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from monopoly.options import GameOptions


class HomeView(ttk.Frame):
    """Affiche le menu d'accueil principal du jeu.

    Entrées:
        master (tk.Misc): Conteneur parent.
        new_game_callback (callable): Fonction appelée après un clic sur Nouvelle partie.
        load_game_callback (callable): Fonction appelée après un clic sur Charger une partie.
        quit_callback (callable): Fonction appelée après un clic sur Quitter.

    Sortie:
        HomeView: Écran d'accueil intégré à la fenêtre principale.
    """

    def __init__(
        self,
        master: tk.Misc,
        new_game_callback: object,
        load_game_callback: object,
        quit_callback: object,
    ) -> None:
        """Construit le titre, les éléments décoratifs et les boutons du menu.

        Entrées:
            master (tk.Misc): Conteneur parent.
            new_game_callback (object): Callback du bouton Nouvelle partie.
            load_game_callback (object): Callback du bouton Charger une partie.
            quit_callback (object): Callback du bouton Quitter.

        Sortie:
            None: L'écran d'accueil est prêt à être affiché.
        """
        super().__init__(master, style="Home.TFrame")
        self.new_game_callback = new_game_callback
        self.load_game_callback = load_game_callback
        self.quit_callback = quit_callback

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        shell = ttk.Frame(self, style="Home.TFrame", padding=30)
        shell.grid(row=0, column=0)

        logo = tk.Frame(
            shell,
            background="#C62828",
            padx=34,
            pady=15,
            highlightbackground="#922020",
            highlightthickness=2,
        )
        logo.pack(pady=(0, 18))

        tk.Label(
            logo,
            text="MONOPOLY",
            background="#C62828",
            foreground="#FFFFFF",
            font=("Arial", 34, "bold"),
        ).pack()

        ttk.Label(
            shell,
            text="Moteur POO",
            style="HomeSubtitle.TLabel",
        ).pack()

        ttk.Label(
            shell,
            text=(
                "Une version pensée pour jouer et tester les règles,\n"
                "avec sauvegardes, historique et options de partie."
            ),
            justify="center",
            style="HomeText.TLabel",
        ).pack(pady=(8, 28))

        menu = ttk.Frame(shell, style="Home.TFrame")
        menu.pack(fill="x")

        ttk.Button(
            menu,
            text="Nouvelle partie",
            style="HomePrimary.TButton",
            command=self._start_new_game,
        ).pack(fill="x", ipady=7, pady=(0, 10))

        ttk.Button(
            menu,
            text="Charger une partie",
            style="HomeSecondary.TButton",
            command=self._load_game,
        ).pack(fill="x", ipady=4, pady=(0, 10))

        ttk.Button(
            menu,
            text="Quitter",
            style="HomeSecondary.TButton",
            command=self._quit,
        ).pack(fill="x", ipady=4)

        ttk.Label(
            shell,
            text="Les règles classiques restent les réglages par défaut.",
            style="HomeHint.TLabel",
        ).pack(pady=(24, 0))

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
        player_names (list[str] | None): Noms déjà saisis à restaurer.
        options (GameOptions | None): Profil de règles déjà configuré.

    Sortie:
        PlayerSetupView: Formulaire intégré de création de partie.
    """

    MAX_PLAYERS = 6

    def __init__(
        self,
        master: tk.Misc,
        start_callback: object,
        back_callback: object,
        rules_callback: object | None = None,
        player_names: list[str] | None = None,
        options: GameOptions | None = None,
    ) -> None:
        """Construit les champs joueurs, le résumé des règles et les boutons.

        Entrées:
            master (tk.Misc): Conteneur parent.
            start_callback (object): Callback appelé avec joueurs et règles.
            back_callback (object): Callback du bouton Retour.
            rules_callback (object | None): Callback ouvrant la personnalisation.
            player_names (list[str] | None): Noms à restaurer.
            options (GameOptions | None): Profil de règles courant.

        Sortie:
            None: Le formulaire est prêt à être utilisé.
        """
        super().__init__(master, style="Home.TFrame")
        self.start_callback = start_callback
        self.back_callback = back_callback
        self.rules_callback = rules_callback
        self.options = options or GameOptions.classic()
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
            text="Choisissez entre 2 et 6 joueurs, puis ajustez les règles si nécessaire.",
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
            row=8,
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

        buttons = ttk.Frame(card, style="SetupCard.TFrame")
        buttons.grid(
            row=9,
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
