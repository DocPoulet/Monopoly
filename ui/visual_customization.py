"""Écran V22 de choix du style, du thème, des animations et des pions."""

from __future__ import annotations

from dataclasses import replace
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .board_view import PLAYER_COLORS
from .pawns import PAWNS, PawnPreview
from .theme import VISUAL_STYLES, VisualPreferences


class VisualStylePreview(tk.Canvas):
    """Dessine une miniature 2.5D d'un style V22.

    Entrées:
        master (tk.Misc): Parent Tkinter.
        style_key (str): Identifiant du style à représenter.
        selected (bool): Met en évidence la miniature sélectionnée.

    Sortie:
        VisualStylePreview: Canvas compact utilisable comme bouton visuel.
    """

    def __init__(
        self,
        master: tk.Misc,
        style_key: str,
        selected: bool = False,
        command: Callable[[], None] | None = None,
    ) -> None:
        """Initialise la miniature et ses événements de clic.

        Entrées:
            master (tk.Misc): Parent Tkinter.
            style_key (str): Style connu.
            selected (bool): État de sélection initial.
            command (Callable[[], None] | None): Callback de clic.

        Sortie:
            None: La miniature est immédiatement dessinée.
        """
        super().__init__(master, width=190, height=125, highlightthickness=0, cursor="hand2")
        self.style_key = style_key
        self.selected = selected
        self.command = command
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", self._on_resize)
        self.redraw()

    def _on_click(self, event: tk.Event) -> None:
        """Déclenche la sélection associée à la miniature.

        Entrées:
            event (tk.Event): Clic souris.

        Sortie:
            None: Le callback est exécuté lorsqu'il existe.
        """
        if self.command is not None:
            self.command()

    def _on_resize(self, event: tk.Event) -> None:
        """Redessine la miniature après redimensionnement.

        Entrées:
            event (tk.Event): Événement Tkinter.

        Sortie:
            None: La perspective reste centrée.
        """
        self.redraw()

    def set_selected(self, selected: bool) -> None:
        """Change la mise en évidence de sélection.

        Entrées:
            selected (bool): Nouvel état.

        Sortie:
            None: Le contour est redessiné.
        """
        self.selected = bool(selected)
        self.redraw()

    def redraw(self) -> None:
        """Dessine un mini plateau isométrique flottant et ses bandes de couleurs.

        Entrées:
            Aucune.

        Sortie:
            None: Le Canvas reflète le style tel qu'il apparaîtra dans V22.2.
        """
        spec = VISUAL_STYLES[self.style_key]
        self.delete("all")
        width = max(190, self.winfo_width())
        height = max(125, self.winfo_height())
        self.configure(background=spec.preview_background)
        outline = spec.accent if self.selected else spec.board_edge
        border_width = 4 if self.selected else 2
        cx = width / 2
        top_y = height * 0.10
        half_w = width * 0.42
        half_h = height * 0.34
        outer = (
            cx, top_y,
            cx + half_w, top_y + half_h,
            cx, top_y + half_h * 2,
            cx - half_w, top_y + half_h,
        )
        thickness = height * 0.035
        self.create_polygon(
            cx + half_w, top_y + half_h,
            cx, top_y + half_h * 2,
            cx, top_y + half_h * 2 + thickness,
            cx + half_w, top_y + half_h + thickness,
            fill=spec.board_edge, outline="",
        )
        self.create_polygon(
            cx, top_y + half_h * 2,
            cx - half_w, top_y + half_h,
            cx - half_w, top_y + half_h + thickness,
            cx, top_y + half_h * 2 + thickness,
            fill=spec.accent_secondary, outline="",
        )
        self.create_polygon(*outer, fill=spec.board_surface, outline=outline, width=border_width)
        inset = 0.23
        inner = (
            cx, top_y + half_h * inset * 2,
            cx + half_w * (1 - inset), top_y + half_h,
            cx, top_y + half_h * (2 - inset * 2),
            cx - half_w * (1 - inset), top_y + half_h,
        )
        self.create_polygon(*inner, fill=spec.board_center, outline=spec.board_edge, width=1)
        colors = ("#8B5A2B", "#79CFE8", "#D95FA6", "#F39C12", "#E74C3C", "#F4D03F", "#27AE60", "#3156A6")
        for index, color in enumerate(colors):
            ratio = 0.10 + index * 0.11
            x = cx - half_w + half_w * ratio
            y = top_y + half_h + half_h * ratio
            self.create_polygon(
                x, y,
                x + width * 0.055, y + height * 0.020,
                x + width * 0.042, y + height * 0.055,
                x - width * 0.013, y + height * 0.035,
                fill=color, outline="",
            )
        self.create_text(cx, top_y + half_h * 0.92, text="MONOPOLY", font=("Arial", 12, "bold"), fill=spec.board_edge)
        self.create_text(cx, top_y + half_h * 1.18, text=spec.name, font=("Arial", 8, "bold"), fill=spec.accent)


class VisualCustomizationView(ttk.Frame):
    """Permet de choisir les préférences graphiques et les vingt pions V22.

    Entrées:
        master (tk.Misc): Fenêtre parent.
        player_names (list[str]): Joueurs actuellement saisis.
        preferences (VisualPreferences): Profil à éditer.
        save_callback (Callable): Reçoit le profil validé.
        cancel_callback (Callable): Retour sans changement.

    Sortie:
        VisualCustomizationView: Écran de configuration purement graphique.
    """

    def __init__(
        self,
        master: tk.Misc,
        player_names: list[str],
        preferences: VisualPreferences,
        save_callback: Callable[[VisualPreferences], None],
        cancel_callback: Callable[[], None],
        show_style_options: bool = True,
        show_pawn_options: bool = True,
        title: str = "Apparence de la partie",
    ) -> None:
        """Construit les previews de style, options et sélecteurs de pions.

        Entrées:
            master (tk.Misc): Parent Tkinter.
            player_names (list[str]): Joueurs actifs pour l'attribution des pions.
            preferences (VisualPreferences): Configuration initiale.
            save_callback (Callable): Callback de validation.
            cancel_callback (Callable): Callback d'annulation.
            show_style_options (bool): Affiche l'onglet des préférences globales.
            show_pawn_options (bool): Affiche l'onglet des pions liés aux joueurs.
            title (str): Titre principal de l'écran.

        Sortie:
            None: L'écran est prêt à être utilisé.
        """
        super().__init__(master, padding=18)
        self.player_names = list(player_names) or ["Alice", "Bob"]
        self.preferences = preferences
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback
        self.show_style_options = show_style_options
        self.show_pawn_options = show_pawn_options
        self.title_text = title
        self.style_var = tk.StringVar(value=preferences.style_key)
        self.theme_var = tk.StringVar(value=preferences.theme)
        self.animation_var = tk.StringVar(value=preferences.animation_speed)
        self.net_worth_var = tk.BooleanVar(value=preferences.show_net_worth)
        self.sound_var = tk.BooleanVar(value=preferences.sound_enabled)
        self.case_numbers_var = tk.BooleanVar(value=preferences.show_case_numbers)
        self.style_previews: dict[str, VisualStylePreview] = {}
        self.pawn_vars: list[tk.StringVar] = []
        self.pawn_previews: list[PawnPreview] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text=self.title_text, style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text="Ces préférences ne changent aucune règle de jeu.",
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="e")

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(12, 12))

        if self.show_style_options:
            style_tab = ttk.Frame(notebook, padding=14)
            notebook.add(style_tab, text="Affichage")
            self._build_style_tab(style_tab)
        if self.show_pawn_options:
            pawn_tab = ttk.Frame(notebook, padding=14)
            notebook.add(pawn_tab, text="Pions")
            self._build_pawn_tab(pawn_tab)

        buttons = ttk.Frame(self)
        buttons.grid(row=2, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=2)
        ttk.Button(buttons, text="Annuler", command=self.cancel_callback).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(buttons, text="Appliquer l'apparence", style="Primary.TButton", command=self._save).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_style_tab(self, parent: ttk.Frame) -> None:
        """Construit les cinq miniatures de style et les options globales.

        Entrées:
            parent (ttk.Frame): Onglet de destination.

        Sortie:
            None: Les styles et options sont interactifs.
        """
        for column in range(3):
            parent.columnconfigure(column, weight=1)
        for index, (key, spec) in enumerate(VISUAL_STYLES.items()):
            row, col = divmod(index, 3)
            card = ttk.Frame(parent, style="V22Card.TFrame", padding=8)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            preview = VisualStylePreview(
                card,
                key,
                selected=(key == self.style_var.get()),
                command=lambda current=key: self._select_style(current),
            )
            preview.pack(fill="x")
            self.style_previews[key] = preview
            ttk.Label(card, text=spec.name, style="V22Card.TLabel", font=("Arial", 10, "bold")).pack(anchor="w", pady=(6, 1))
            ttk.Label(card, text=spec.description, style="V22MutedCard.TLabel", wraplength=210).pack(anchor="w")

        options = ttk.LabelFrame(parent, text="Préférences", padding=12)
        options.grid(row=2, column=0, columnspan=3, sticky="ew", padx=6, pady=(14, 6))
        ttk.Label(options, text="Thème menus/background :").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(options, text="Clair", variable=self.theme_var, value="light").grid(row=0, column=1, padx=6)
        ttk.Radiobutton(options, text="Sombre", variable=self.theme_var, value="dark").grid(row=0, column=2, padx=6)
        ttk.Label(options, text="Animations :").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(options, textvariable=self.animation_var, values=("normal", "fast", "off"), state="readonly", width=14).grid(row=1, column=1, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(options, text="Afficher le patrimoine dans les cartes joueur", variable=self.net_worth_var).grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Checkbutton(options, text="Activer les sons lorsqu'un fichier correspondant existe", variable=self.sound_var).grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Checkbutton(
            options,
            text="Afficher les numéros 0–39 autour du plateau (debug)",
            variable=self.case_numbers_var,
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def _build_pawn_tab(self, parent: ttk.Frame) -> None:
        """Construit une ligne de choix avec preview pour chaque joueur actif.

        Entrées:
            parent (ttk.Frame): Onglet de destination.

        Sortie:
            None: Chaque joueur peut sélectionner l'un des vingt pions.
        """
        parent.columnconfigure(1, weight=1)
        names = [item.name for item in PAWNS]
        defaults = list(self.preferences.pawn_ids)
        while len(defaults) < len(self.player_names):
            defaults.append(PAWNS[len(defaults) % len(PAWNS)].key)
        for index, player_name in enumerate(self.player_names):
            color = PLAYER_COLORS[index % len(PLAYER_COLORS)]
            preview = PawnPreview(parent, defaults[index], color=color, size=58)
            preview.grid(row=index, column=0, padx=(0, 10), pady=6)
            self.pawn_previews.append(preview)
            block = ttk.Frame(parent, style="V22Card.TFrame", padding=8)
            block.grid(row=index, column=1, sticky="ew", pady=6)
            block.columnconfigure(1, weight=1)
            ttk.Label(block, text=player_name, style="V22Card.TLabel", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 12))
            current_name = next((item.name for item in PAWNS if item.key == defaults[index]), PAWNS[0].name)
            variable = tk.StringVar(value=current_name)
            self.pawn_vars.append(variable)
            combo = ttk.Combobox(block, textvariable=variable, values=names, state="readonly")
            combo.grid(row=0, column=1, sticky="ew")
            combo.bind("<<ComboboxSelected>>", lambda event, row=index: self._pawn_changed(row))
        ttk.Label(
            parent,
            text="20 pions vectoriels sont fournis. Aucun asset externe n'est nécessaire.",
            style="Muted.TLabel",
        ).grid(row=len(self.player_names), column=0, columnspan=2, sticky="w", pady=(12, 0))

    def _select_style(self, style_key: str) -> None:
        """Sélectionne un style et actualise les contours de toutes les miniatures.

        Entrées:
            style_key (str): Style choisi.

        Sortie:
            None: Une seule miniature reste mise en évidence.
        """
        self.style_var.set(style_key)
        for key, preview in self.style_previews.items():
            preview.set_selected(key == style_key)

    def _pawn_changed(self, row: int) -> None:
        """Actualise la preview du pion d'un joueur après changement de liste.

        Entrées:
            row (int): Index du joueur dans l'écran.

        Sortie:
            None: Le pion sélectionné est redessiné.
        """
        name = self.pawn_vars[row].get()
        pawn = next((item for item in PAWNS if item.name == name), PAWNS[0])
        self.pawn_previews[row].set_pawn(pawn.key)

    def _save(self) -> None:
        """Valide l'unicité des pions actifs puis renvoie le profil V22.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit un ``VisualPreferences`` validé.
        """
        selected: list[str] = []
        for variable in self.pawn_vars:
            pawn = next((item for item in PAWNS if item.name == variable.get()), PAWNS[0])
            selected.append(pawn.key)
        if selected and len(set(selected)) != len(selected):
            messagebox.showwarning(
                "Pions en double",
                "Choisissez un pion différent pour chaque joueur actif.",
                parent=self,
            )
            return
        preferences = replace(
            self.preferences,
            style_key=self.style_var.get(),
            theme=self.theme_var.get(),
            animation_speed=self.animation_var.get(),
            show_net_worth=self.net_worth_var.get(),
            pawn_ids=tuple(selected) if selected else self.preferences.pawn_ids,
            sound_enabled=self.sound_var.get(),
            show_case_numbers=self.case_numbers_var.get(),
        )
        self.save_callback(preferences)
