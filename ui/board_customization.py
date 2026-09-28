"""Éditeur intégré du plateau, de ses cartes et de ses presets."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable

from monopoly.board_config import BoardConfig, CardConfig, CARD_TYPES, SpaceConfig
from monopoly.board_presets import (
    BoardPreset,
    BoardPresetError,
    import_board_preset,
    list_board_presets,
    load_board_preset,
    save_board_preset,
    save_named_board_preset,
)
from .board_creation_wizard import BoardCreationWizard
from .preset_library import BoardPresetLibraryDialog


SPACE_LABELS = {
    "go": "Départ",
    "property": "Terrain",
    "community_chest": "Communauté",
    "tax": "Taxe",
    "railroad": "Gare",
    "chance": "Chance",
    "jail": "Prison",
    "utility": "Compagnie",
    "free_parking": "Parc Gratuit",
    "go_to_jail": "Allez en prison",
}

CARD_LABELS = {
    "MoneyCard": "Argent banque",
    "MoveToCard": "Déplacement vers case",
    "MoveBackCard": "Recul",
    "GoToJailCard": "Allez en prison",
    "GetOutOfJailCard": "Sortie de prison",
    "NearestRailroadCard": "Prochaine gare",
    "NearestUtilityCard": "Prochaine compagnie",
    "RepairsCard": "Réparations",
    "PerPlayerCard": "Paiement par joueur",
}


class BoardCustomizationView(ttk.Frame):
    """Permet de modifier les 40 cases et les deux paquets de cartes.

    Entrées:
        master (tk.Misc): Conteneur parent.
        board_config (BoardConfig): Définition initiale à éditer.
        save_callback (Callable[[BoardConfig], None]): Applique le plateau à la préparation.
        cancel_callback (Callable[[], None]): Retourne sans appliquer les modifications.
        preset_directory (str | Path | None): Bibliothèque locale des presets de plateau.

    Sortie:
        BoardCustomizationView: Éditeur intégré avec import/export et presets locaux.
    """

    def __init__(
        self,
        master: tk.Misc,
        board_config: BoardConfig,
        save_callback: Callable[[BoardConfig], None],
        cancel_callback: Callable[[], None],
        preset_directory: str | Path | None = None,
    ) -> None:
        """Construit l'éditeur, les onglets et la barre de presets.

        Entrées:
            master (tk.Misc): Conteneur parent.
            board_config (BoardConfig): Plateau actuel copié avant édition.
            save_callback (Callable[[BoardConfig], None]): Callback de validation finale.
            cancel_callback (Callable[[], None]): Callback d'annulation.
            preset_directory (str | Path | None): Dossier des presets locaux.

        Sortie:
            None: L'éditeur est prêt à être affiché.
        """
        super().__init__(master, style="Home.TFrame")
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback
        self.preset_directory = Path(preset_directory or Path.cwd() / "board_presets")
        self.preset_directory.mkdir(parents=True, exist_ok=True)
        self.board_config = board_config.clone()
        self.board_name_var = tk.StringVar(value=self.board_config.name)
        self.local_presets: dict[str, BoardPreset] = {}
        self.selected_space_index = 0
        self.selected_card_index: dict[str, int] = {"chance": 0, "community_chest": 0}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        shell = ttk.Frame(self, padding=16)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(4, weight=1)

        ttk.Label(
            shell,
            text="Éditeur de plateau",
            font=("Arial", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            shell,
            text=(
                "Les 40 positions restent structurellement compatibles avec le moteur, "
                "mais les noms, valeurs économiques et deux paquets de cartes sont éditables."
            ),
            style="Muted.TLabel",
            wraplength=980,
        ).grid(row=1, column=0, sticky="ew", pady=(3, 9))

        self._build_preset_bar(shell)
        self._build_validation_panel(shell)

        self.notebook = ttk.Notebook(shell)
        self.notebook.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        self._build_spaces_tab()
        self._build_cards_tab("chance", "Chance")
        self._build_cards_tab("community_chest", "Communauté")

        footer = ttk.Frame(shell)
        footer.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=1)
        footer.columnconfigure(2, weight=2)

        ttk.Button(
            footer,
            text="Plateau standard",
            command=self._reset_standard,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(
            footer,
            text="Annuler",
            command=self.cancel_callback,
        ).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(
            footer,
            text="Appliquer ce plateau",
            style="HomePrimary.TButton",
            command=self._save_board,
        ).grid(row=0, column=2, sticky="ew", padx=(5, 0))

        self._refresh_preset_list()
        self._refresh_space_tree()
        self._load_space_editor(0)
        self._refresh_card_tree("chance")
        self._refresh_card_tree("community_chest")
        self._load_card_editor("chance", 0)
        self._load_card_editor("community_chest", 0)
        self._refresh_validation_report(commit=False)

    def _build_preset_bar(self, parent: ttk.Frame) -> None:
        """Construit le nom du plateau et les commandes de presets.

        Entrées:
            parent (ttk.Frame): Conteneur principal.

        Sortie:
            None: Nom, bibliothèque, import et export sont placés en haut.
        """
        frame = ttk.LabelFrame(parent, text="Plateau et presets", padding=8)
        frame.grid(row=2, column=0, sticky="ew")
        frame.columnconfigure(1, weight=2)
        for column in range(2, 8):
            frame.columnconfigure(column, weight=1)

        ttk.Label(frame, text="Nom du plateau").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(frame, textvariable=self.board_name_var).grid(
            row=0, column=1, sticky="ew", padx=(0, 10)
        )

        self.preset_var = tk.StringVar(value="")
        self.preset_combo = ttk.Combobox(
            frame,
            textvariable=self.preset_var,
            state="readonly",
        )
        self.preset_combo.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 5), pady=(7, 0))
        ttk.Button(frame, text="Charger", command=self._load_selected_preset).grid(
            row=1, column=2, sticky="ew", padx=3, pady=(7, 0)
        )
        ttk.Button(frame, text="Bibliothèque…", command=self._open_preset_library).grid(
            row=1, column=3, sticky="ew", padx=3, pady=(7, 0)
        )
        ttk.Button(frame, text="Sauvegarder", command=self._save_local_preset).grid(
            row=1, column=4, sticky="ew", padx=3, pady=(7, 0)
        )
        ttk.Button(frame, text="Importer JSON", command=self._import_preset).grid(
            row=1, column=5, sticky="ew", padx=3, pady=(7, 0)
        )
        ttk.Button(frame, text="Exporter", command=self._export_current_preset).grid(
            row=1, column=6, sticky="ew", padx=3, pady=(7, 0)
        )
        ttk.Button(frame, text="Nouveau…", command=self._new_board_wizard).grid(
            row=1, column=7, sticky="ew", padx=(3, 0), pady=(7, 0)
        )

    def _build_validation_panel(self, parent: ttk.Frame) -> None:
        """Construit le rapport visuel des erreurs et avertissements du plateau.

        Entrées:
            parent (ttk.Frame): Conteneur principal de l'éditeur.

        Sortie:
            None: Un tableau compact de validation est placé sous les presets.
        """
        frame = ttk.LabelFrame(parent, text="Validation du plateau", padding=7)
        frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        frame.columnconfigure(0, weight=1)

        self.validation_summary_label = ttk.Label(frame, text="", style="Muted.TLabel")
        self.validation_summary_label.grid(row=0, column=0, sticky="w")
        ttk.Button(
            frame,
            text="Valider maintenant",
            command=self._refresh_validation_report,
        ).grid(row=0, column=1, sticky="e", padx=(8, 0))
        ttk.Button(
            frame,
            text="Aller au problème",
            command=self._focus_validation_issue,
        ).grid(row=0, column=2, sticky="e", padx=(6, 0))

        self.validation_tree = ttk.Treeview(
            frame,
            columns=("location", "message"),
            show="tree headings",
            height=4,
            selectmode="browse",
        )
        self.validation_tree.heading("#0", text="État")
        self.validation_tree.heading("location", text="Emplacement")
        self.validation_tree.heading("message", text="Message")
        self.validation_tree.column("#0", width=100, anchor="center")
        self.validation_tree.column("location", width=130)
        self.validation_tree.column("message", width=650)
        self.validation_tree.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.validation_tree.bind("<Double-1>", self._validation_double_clicked)
        self.validation_tree.tag_configure("error", background="#FDE5E5")
        self.validation_tree.tag_configure("warning", background="#FFF3D6")
        self.validation_issues = []

    def _refresh_validation_report(self, commit: bool = True) -> bool:
        """Actualise le rapport structuré et indique si des erreurs bloquantes subsistent.

        Entrées:
            commit (bool): Tente d'enregistrer les formulaires visibles avant analyse.

        Sortie:
            bool: ``True`` lorsqu'aucune erreur bloquante n'est présente.
        """
        if commit:
            if not self._apply_space_editor():
                return False
            for deck_name in ("chance", "community_chest"):
                if not self._apply_card_editor(deck_name):
                    return False
            self.board_config.name = self.board_name_var.get().strip() or "Plateau personnalisé"

        self.validation_issues = self.board_config.validation_issues()
        for item in self.validation_tree.get_children():
            self.validation_tree.delete(item)

        errors = sum(issue.severity == "error" for issue in self.validation_issues)
        warnings = sum(issue.severity == "warning" for issue in self.validation_issues)
        self.validation_summary_label.configure(
            text=f"{errors} erreur(s) bloquante(s) • {warnings} avertissement(s)"
        )
        for index, issue in enumerate(self.validation_issues):
            if issue.location_type == "space":
                location = f"Case {issue.index}"
            elif issue.location_type == "chance":
                location = f"Chance #{(issue.index or 0) + 1}"
            elif issue.location_type == "community_chest":
                location = f"Communauté #{(issue.index or 0) + 1}"
            else:
                location = "Plateau"
            self.validation_tree.insert(
                "",
                "end",
                iid=str(index),
                text=issue.label,
                values=(location, issue.message),
                tags=(issue.severity,),
            )
        if not self.validation_issues:
            self.validation_tree.insert(
                "",
                "end",
                iid="ok",
                text="OK",
                values=("Plateau", "Aucune anomalie détectée."),
            )
        return errors == 0

    def _validation_double_clicked(self, event: tk.Event) -> None:
        """Ouvre directement l'élément correspondant à une anomalie double-cliquée.

        Entrées:
            event (tk.Event): Événement souris du tableau de validation.

        Sortie:
            None: L'onglet et l'élément concernés deviennent actifs.
        """
        self._focus_validation_issue()

    def _focus_validation_issue(self) -> None:
        """Navigue vers la case ou la carte associée au problème sélectionné.

        Entrées:
            Aucune.

        Sortie:
            None: La sélection de l'éditeur correspond à l'anomalie choisie.
        """
        selection = self.validation_tree.selection()
        if not selection or selection[0] == "ok":
            return
        issue = self.validation_issues[int(selection[0])]
        if issue.location_type == "space" and issue.index is not None:
            self.notebook.select(0)
            self.selected_space_index = issue.index
            self._refresh_space_tree()
            self._load_space_editor(issue.index)
        elif issue.location_type in {"chance", "community_chest"} and issue.index is not None:
            deck = issue.location_type
            self.notebook.select(1 if deck == "chance" else 2)
            cards = self._deck_cards(deck)
            if cards:
                index = min(issue.index, len(cards) - 1)
                self.selected_card_index[deck] = index
                self._refresh_card_tree(deck)
                self._load_card_editor(deck, index)

    def _build_spaces_tab(self) -> None:
        """Construit l'onglet d'édition des quarante cases.

        Entrées:
            Aucune.

        Sortie:
            None: Un tableau des cases et un formulaire dynamique sont ajoutés.
        """
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="40 cases")
        tab.columnconfigure(0, weight=2)
        tab.columnconfigure(1, weight=3)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.space_tree = ttk.Treeview(
            left,
            columns=("type", "name"),
            show="tree headings",
            selectmode="browse",
        )
        self.space_tree.heading("#0", text="#")
        self.space_tree.heading("type", text="Type")
        self.space_tree.heading("name", text="Nom")
        self.space_tree.column("#0", width=42, anchor="center")
        self.space_tree.column("type", width=110)
        self.space_tree.column("name", width=210)
        self.space_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.space_tree.yview)
        self.space_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        self.space_tree.bind("<<TreeviewSelect>>", self._space_selected)

        right = ttk.LabelFrame(tab, text="Case sélectionnée", padding=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        right.columnconfigure(1, weight=1)

        ttk.Label(right, text="Type de case", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8)
        )
        self.space_type_var = tk.StringVar()
        self.space_type_combo = ttk.Combobox(
            right,
            textvariable=self.space_type_var,
            state="readonly",
        )
        self.space_type_combo.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        self.space_type_combo.bind("<<ComboboxSelected>>", self._space_type_changed)

        self.space_name_var = tk.StringVar()
        self.space_price_var = tk.StringVar()
        self.space_group_var = tk.StringVar()
        self.space_base_rent_var = tk.StringVar()
        self.space_house_cost_var = tk.StringVar()
        self.space_house_rent_vars = [tk.StringVar() for _ in range(4)]
        self.space_hotel_rent_var = tk.StringVar()
        self.space_tax_var = tk.StringVar()
        self.space_railroad_rent_vars = [tk.StringVar() for _ in range(4)]
        self.space_utility_multiplier_vars = [tk.StringVar() for _ in range(2)]

        self._form_row(right, 1, "Nom", self.space_name_var)
        self.space_price_row = self._form_row(right, 2, "Prix d'achat", self.space_price_var)
        self.space_group_row = self._form_row(right, 3, "Groupe couleur", self.space_group_var)
        self.space_base_row = self._form_row(right, 4, "Loyer sans maison", self.space_base_rent_var)
        self.space_house_cost_row = self._form_row(right, 5, "Prix maison / hôtel", self.space_house_cost_var)
        self.space_house_rows = []
        for offset, variable in enumerate(self.space_house_rent_vars, start=1):
            self.space_house_rows.append(
                self._form_row(right, 5 + offset, f"Loyer {offset} maison(s)", variable)
            )
        self.space_hotel_row = self._form_row(right, 10, "Loyer hôtel", self.space_hotel_rent_var)
        self.space_tax_row = self._form_row(right, 11, "Montant taxe", self.space_tax_var)
        self.space_railroad_rows = []
        for offset, variable in enumerate(self.space_railroad_rent_vars, start=1):
            self.space_railroad_rows.append(
                self._form_row(right, 11 + offset, f"Loyer avec {offset} gare(s)", variable)
            )
        self.space_utility_rows = [
            self._form_row(right, 16, "Multiplicateur avec 1 compagnie", self.space_utility_multiplier_vars[0]),
            self._form_row(right, 17, "Multiplicateur avec 2+ compagnies", self.space_utility_multiplier_vars[1]),
        ]

        case_buttons = ttk.Frame(right)
        case_buttons.grid(row=18, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        case_buttons.columnconfigure(0, weight=2)
        case_buttons.columnconfigure(1, weight=1)
        ttk.Button(
            case_buttons,
            text="Enregistrer cette case",
            style="Primary.TButton",
            command=self._apply_space_editor,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(
            case_buttons,
            text="Dupliquer vers…",
            command=self._duplicate_space,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _form_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> tuple[ttk.Label, ttk.Entry]:
        """Ajoute une ligne libellé + champ dans un formulaire.

        Entrées:
            parent (ttk.Frame): Conteneur du formulaire.
            row (int): Ligne de grille.
            label (str): Intitulé visible.
            variable (tk.StringVar): Valeur du champ.

        Sortie:
            tuple[ttk.Label, ttk.Entry]: Widgets créés pour pouvoir les masquer.
        """
        label_widget = ttk.Label(parent, text=label)
        label_widget.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=3)
        return label_widget, entry

    def _build_cards_tab(self, deck_name: str, title: str) -> None:
        """Construit un onglet d'édition de paquet de cartes.

        Entrées:
            deck_name (str): ``chance`` ou ``community_chest``.
            title (str): Titre visible de l'onglet.

        Sortie:
            None: Liste, éditeur et boutons ajouter/supprimer sont créés.
        """
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text=title)
        tab.columnconfigure(0, weight=2)
        tab.columnconfigure(1, weight=3)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        tree = ttk.Treeview(left, columns=("type", "text"), show="tree headings", selectmode="browse")
        tree.heading("#0", text="#")
        tree.heading("type", text="Type")
        tree.heading("text", text="Texte")
        tree.column("#0", width=38, anchor="center")
        tree.column("type", width=125)
        tree.column("text", width=235)
        tree.grid(row=0, column=0, columnspan=3, sticky="nsew")
        tree.bind("<<TreeviewSelect>>", lambda event, deck=deck_name: self._card_selected(deck, event))
        ttk.Button(left, text="Ajouter", command=lambda deck=deck_name: self._add_card(deck)).grid(
            row=1, column=0, sticky="ew", padx=(0, 3), pady=(7, 0)
        )
        ttk.Button(left, text="Dupliquer", command=lambda deck=deck_name: self._duplicate_card(deck)).grid(
            row=1, column=1, sticky="ew", padx=3, pady=(7, 0)
        )
        ttk.Button(left, text="Supprimer", command=lambda deck=deck_name: self._remove_card(deck)).grid(
            row=1, column=2, sticky="ew", padx=(3, 0), pady=(7, 0)
        )

        right = ttk.LabelFrame(tab, text="Carte sélectionnée", padding=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        right.columnconfigure(1, weight=1)

        type_var = tk.StringVar()
        text_var = tk.StringVar()
        param1_var = tk.StringVar()
        param2_var = tk.StringVar()
        collect_var = tk.BooleanVar(value=True)

        ttk.Label(right, text="Type").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        combo = ttk.Combobox(
            right,
            textvariable=type_var,
            values=list(CARD_TYPES),
            state="readonly",
        )
        combo.grid(row=0, column=1, sticky="ew", pady=3)
        combo.bind("<<ComboboxSelected>>", lambda event, deck=deck_name: self._refresh_card_params(deck))
        ttk.Label(right, text="Texte").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(right, textvariable=text_var).grid(row=1, column=1, sticky="ew", pady=3)

        param1_label = ttk.Label(right, text="Paramètre 1")
        param1_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
        param1_entry = ttk.Entry(right, textvariable=param1_var)
        param1_entry.grid(row=2, column=1, sticky="ew", pady=3)
        param2_label = ttk.Label(right, text="Paramètre 2")
        param2_label.grid(row=3, column=0, sticky="w", padx=(0, 8), pady=3)
        param2_entry = ttk.Entry(right, textvariable=param2_var)
        param2_entry.grid(row=3, column=1, sticky="ew", pady=3)
        collect_check = ttk.Checkbutton(right, text="Percevoir Départ si franchi", variable=collect_var)
        collect_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 0))
        hint = ttk.Label(right, text="", style="Muted.TLabel", wraplength=430)
        hint.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(
            right,
            text="Enregistrer cette carte",
            style="Primary.TButton",
            command=lambda deck=deck_name: self._apply_card_editor(deck),
        ).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        setattr(self, f"{deck_name}_tree", tree)
        setattr(self, f"{deck_name}_type_var", type_var)
        setattr(self, f"{deck_name}_text_var", text_var)
        setattr(self, f"{deck_name}_param1_var", param1_var)
        setattr(self, f"{deck_name}_param2_var", param2_var)
        setattr(self, f"{deck_name}_collect_var", collect_var)
        setattr(self, f"{deck_name}_param1_label", param1_label)
        setattr(self, f"{deck_name}_param1_entry", param1_entry)
        setattr(self, f"{deck_name}_param2_label", param2_label)
        setattr(self, f"{deck_name}_param2_entry", param2_entry)
        setattr(self, f"{deck_name}_collect_check", collect_check)
        setattr(self, f"{deck_name}_hint", hint)

    def _deck_cards(self, deck_name: str) -> list[CardConfig]:
        """Retourne la liste de cartes correspondant à un nom de paquet.

        Entrées:
            deck_name (str): ``chance`` ou ``community_chest``.

        Sortie:
            list[CardConfig]: Liste éditable du paquet demandé.
        """
        if deck_name == "chance":
            return self.board_config.chance_cards
        return self.board_config.community_chest_cards

    def _refresh_space_tree(self) -> None:
        """Reconstruit le tableau des quarante cases depuis le brouillon.

        Entrées:
            Aucune.

        Sortie:
            None: Noms et types visibles reflètent ``board_config``.
        """
        for item in self.space_tree.get_children():
            self.space_tree.delete(item)
        for space in self.board_config.spaces:
            self.space_tree.insert(
                "",
                "end",
                iid=str(space.index),
                text=str(space.index),
                values=(SPACE_LABELS.get(space.space_type, space.space_type), space.name),
            )
        iid = str(min(self.selected_space_index, 39))
        self.space_tree.selection_set(iid)
        self.space_tree.focus(iid)
        self.space_tree.see(iid)

    def _space_selected(self, event: tk.Event | None) -> None:
        """Charge la case sélectionnée dans le formulaire.

        Entrées:
            event (tk.Event | None): Événement Treeview, facultatif en test.

        Sortie:
            None: Les champs correspondent à la nouvelle sélection.
        """
        selection = self.space_tree.selection()
        if not selection:
            return
        self.selected_space_index = int(selection[0])
        self._load_space_editor(self.selected_space_index)

    def _load_space_editor(self, index: int) -> None:
        """Copie une configuration de case dans les champs visibles.

        Entrées:
            index (int): Index de case à éditer.

        Sortie:
            None: Valeurs et visibilité des champs sont actualisées.
        """
        space = self.board_config.spaces[index]
        if index in {0, 10, 20, 30}:
            self.space_type_combo.configure(values=[space.space_type], state="disabled")
        else:
            self.space_type_combo.configure(
                values=["property", "railroad", "utility", "tax", "chance", "community_chest"],
                state="readonly",
            )
        self.space_type_var.set(space.space_type)
        self.space_name_var.set(space.name)
        self.space_price_var.set(str(space.price))
        self.space_group_var.set(space.color_group)
        self.space_base_rent_var.set(str(space.base_rent))
        self.space_house_cost_var.set(str(space.house_cost))
        for variable, value in zip(self.space_house_rent_vars, space.house_rents):
            variable.set(str(value))
        self.space_hotel_rent_var.set(str(space.hotel_rent))
        self.space_tax_var.set(str(space.tax_amount))
        for variable, value in zip(self.space_railroad_rent_vars, space.railroad_rents):
            variable.set(str(value))
        for variable, value in zip(self.space_utility_multiplier_vars, space.utility_multipliers):
            variable.set(str(value))

        self._refresh_space_field_visibility()

    def _space_type_changed(self, event: tk.Event | None) -> None:
        """Actualise les champs économiques après changement du type d'une case.

        Entrées:
            event (tk.Event | None): Événement de combobox, facultatif en test.

        Sortie:
            None: Seuls les paramètres utiles au nouveau type restent visibles.
        """
        self._refresh_space_field_visibility()

    def _refresh_space_field_visibility(self) -> None:
        """Affiche les champs économiques correspondant au type actuellement choisi.

        Entrées:
            Aucune.

        Sortie:
            None: Prix, loyers, taxe ou multiplicateurs sont masqués/affichés.
        """
        space_type = self.space_type_var.get()
        property_rows = [
            self.space_group_row,
            self.space_base_row,
            self.space_house_cost_row,
            *self.space_house_rows,
            self.space_hotel_row,
        ]
        all_rows = [
            self.space_price_row,
            self.space_tax_row,
            *property_rows,
            *self.space_railroad_rows,
            *self.space_utility_rows,
        ]
        for row in all_rows:
            for widget in row:
                widget.grid_remove()
        if space_type in {"property", "railroad", "utility"}:
            for widget in self.space_price_row:
                widget.grid()
        if space_type == "property":
            for row in property_rows:
                for widget in row:
                    widget.grid()
        elif space_type == "tax":
            for widget in self.space_tax_row:
                widget.grid()
        elif space_type == "railroad":
            for row in self.space_railroad_rows:
                for widget in row:
                    widget.grid()
        elif space_type == "utility":
            for row in self.space_utility_rows:
                for widget in row:
                    widget.grid()

    def _apply_space_editor(self) -> bool:
        """Valide et enregistre les champs de la case actuellement sélectionnée.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` si la case a été validée et enregistrée.
        """
        current = self.board_config.spaces[self.selected_space_index]
        try:
            rents = tuple(int(variable.get()) for variable in self.space_house_rent_vars)
            railroad_rents = tuple(
                int(variable.get() or 0) for variable in self.space_railroad_rent_vars
            )
            utility_multipliers = tuple(
                int(variable.get() or 0) for variable in self.space_utility_multiplier_vars
            )
            updated = SpaceConfig(
                index=current.index,
                space_type=self.space_type_var.get(),
                name=self.space_name_var.get().strip(),
                price=int(self.space_price_var.get() or 0),
                color_group=self.space_group_var.get().strip(),
                base_rent=int(self.space_base_rent_var.get() or 0),
                house_rents=rents,  # type: ignore[arg-type]
                hotel_rent=int(self.space_hotel_rent_var.get() or 0),
                house_cost=int(self.space_house_cost_var.get() or 0),
                tax_amount=int(self.space_tax_var.get() or 0),
                railroad_rents=railroad_rents,  # type: ignore[arg-type]
                utility_multipliers=utility_multipliers,  # type: ignore[arg-type]
            )
            updated.validate()
        except ValueError as error:
            messagebox.showwarning("Case invalide", str(error), parent=self)
            return False
        self.board_config.spaces[self.selected_space_index] = updated
        self._refresh_space_tree()
        if hasattr(self, "validation_tree"):
            self._refresh_validation_report(commit=False)
        return True

    def _duplicate_space(self) -> None:
        """Copie la case sélectionnée vers une position choisie par l'utilisateur.

        Entrées:
            Aucune.

        Sortie:
            None: La case cible reçoit une copie modifiable du contenu source.
        """
        if not self._apply_space_editor():
            return
        target = simpledialog.askinteger(
            "Dupliquer une case",
            "Position cible (0 à 39, hors 0/10/20/30) :",
            minvalue=0,
            maxvalue=39,
            parent=self,
        )
        if target is None:
            return
        try:
            self.board_config.duplicate_space(self.selected_space_index, target)
        except ValueError as error:
            messagebox.showwarning("Duplication impossible", str(error), parent=self)
            return
        self.selected_space_index = target
        self._refresh_space_tree()
        self._load_space_editor(target)
        self._refresh_validation_report(commit=False)

    def _duplicate_card(self, deck_name: str) -> None:
        """Duplique la carte sélectionnée à la fin du même paquet.

        Entrées:
            deck_name (str): Paquet Chance ou Communauté.

        Sortie:
            None: Une nouvelle carte indépendante est ajoutée puis sélectionnée.
        """
        if not self._apply_card_editor(deck_name):
            return
        try:
            index = self.board_config.duplicate_card(
                deck_name,
                self.selected_card_index[deck_name],
            )
        except ValueError as error:
            messagebox.showwarning("Duplication impossible", str(error), parent=self)
            return
        self.selected_card_index[deck_name] = index
        self._refresh_card_tree(deck_name)
        self._load_card_editor(deck_name, index)
        self._refresh_validation_report(commit=False)

    def _refresh_card_tree(self, deck_name: str) -> None:
        """Reconstruit la liste visible d'un paquet de cartes.

        Entrées:
            deck_name (str): Nom du paquet à actualiser.

        Sortie:
            None: Les cartes du brouillon sont affichées dans l'ordre.
        """
        tree: ttk.Treeview = getattr(self, f"{deck_name}_tree")
        for item in tree.get_children():
            tree.delete(item)
        cards = self._deck_cards(deck_name)
        for index, card in enumerate(cards):
            tree.insert(
                "",
                "end",
                iid=str(index),
                text=str(index + 1),
                values=(CARD_LABELS.get(card.card_type, card.card_type), card.text),
            )
        if cards:
            index = min(self.selected_card_index[deck_name], len(cards) - 1)
            self.selected_card_index[deck_name] = index
            tree.selection_set(str(index))
            tree.focus(str(index))
            tree.see(str(index))

    def _card_selected(self, deck_name: str, event: tk.Event | None) -> None:
        """Charge la carte sélectionnée dans son formulaire.

        Entrées:
            deck_name (str): Paquet concerné.
            event (tk.Event | None): Événement Treeview, facultatif en test.

        Sortie:
            None: Les variables du formulaire sont actualisées.
        """
        tree: ttk.Treeview = getattr(self, f"{deck_name}_tree")
        selection = tree.selection()
        if not selection:
            return
        index = int(selection[0])
        self.selected_card_index[deck_name] = index
        self._load_card_editor(deck_name, index)

    def _load_card_editor(self, deck_name: str, index: int) -> None:
        """Copie une carte dans les variables d'édition du paquet.

        Entrées:
            deck_name (str): Paquet concerné.
            index (int): Position de la carte.

        Sortie:
            None: Le type, texte et paramètres sont chargés.
        """
        cards = self._deck_cards(deck_name)
        if not cards:
            return
        card = cards[index]
        getattr(self, f"{deck_name}_type_var").set(card.card_type)
        getattr(self, f"{deck_name}_text_var").set(card.text)
        param1, param2 = self._card_param_values(card)
        getattr(self, f"{deck_name}_param1_var").set(str(param1))
        getattr(self, f"{deck_name}_param2_var").set(str(param2))
        getattr(self, f"{deck_name}_collect_var").set(card.collect_go)
        self._refresh_card_params(deck_name)

    def _card_param_values(self, card: CardConfig) -> tuple[int, int]:
        """Retourne les deux valeurs numériques pertinentes pour un type de carte.

        Entrées:
            card (CardConfig): Carte à résumer.

        Sortie:
            tuple[int, int]: Paramètres principaux dans l'ordre de l'éditeur.
        """
        if card.card_type in {"MoneyCard", "PerPlayerCard"}:
            return card.amount, 0
        if card.card_type == "MoveToCard":
            return card.destination, 0
        if card.card_type == "MoveBackCard":
            return card.steps, 0
        if card.card_type == "RepairsCard":
            return card.house_cost, card.hotel_cost
        return 0, 0

    def _refresh_card_params(self, deck_name: str) -> None:
        """Adapte les libellés et la visibilité des paramètres au type de carte.

        Entrées:
            deck_name (str): Paquet dont le formulaire doit être adapté.

        Sortie:
            None: Paramètres inutiles sont masqués et une aide contextuelle est affichée.
        """
        card_type = getattr(self, f"{deck_name}_type_var").get()
        label1: ttk.Label = getattr(self, f"{deck_name}_param1_label")
        entry1: ttk.Entry = getattr(self, f"{deck_name}_param1_entry")
        label2: ttk.Label = getattr(self, f"{deck_name}_param2_label")
        entry2: ttk.Entry = getattr(self, f"{deck_name}_param2_entry")
        check: ttk.Checkbutton = getattr(self, f"{deck_name}_collect_check")
        hint: ttk.Label = getattr(self, f"{deck_name}_hint")

        for widget in (label1, entry1, label2, entry2, check):
            widget.grid_remove()
        text = "Cette carte ne nécessite qu'un texte."
        if card_type in {"MoneyCard", "PerPlayerCard"}:
            label1.configure(text="Montant (+ gain / - paiement)")
            label1.grid(); entry1.grid()
            text = "PerPlayerCard applique ce montant pour chaque adversaire."
        elif card_type == "MoveToCard":
            label1.configure(text="Index destination (0 à 39)")
            label1.grid(); entry1.grid(); check.grid()
            text = "La case de destination est ensuite résolue normalement."
        elif card_type == "MoveBackCard":
            label1.configure(text="Nombre de cases à reculer")
            label1.grid(); entry1.grid()
            text = "Le recul ne déclenche pas de salaire Départ."
        elif card_type == "RepairsCard":
            label1.configure(text="Coût par maison")
            label2.configure(text="Coût par hôtel")
            label1.grid(); entry1.grid(); label2.grid(); entry2.grid()
            text = "Le total dépend des bâtiments possédés au moment de la pioche."
        hint.configure(text=text)

    def _apply_card_editor(self, deck_name: str) -> bool:
        """Valide et enregistre la carte actuellement éditée.

        Entrées:
            deck_name (str): Paquet concerné.

        Sortie:
            bool: ``True`` si la carte a été validée et enregistrée.
        """
        cards = self._deck_cards(deck_name)
        if not cards:
            return False
        try:
            card_type = getattr(self, f"{deck_name}_type_var").get()
            text = getattr(self, f"{deck_name}_text_var").get().strip()
            param1 = int(getattr(self, f"{deck_name}_param1_var").get() or 0)
            param2 = int(getattr(self, f"{deck_name}_param2_var").get() or 0)
            card = CardConfig(card_type=card_type, text=text)
            if card_type in {"MoneyCard", "PerPlayerCard"}:
                card.amount = param1
            elif card_type == "MoveToCard":
                card.destination = param1
                card.collect_go = bool(getattr(self, f"{deck_name}_collect_var").get())
            elif card_type == "MoveBackCard":
                card.steps = param1
            elif card_type == "RepairsCard":
                card.house_cost = param1
                card.hotel_cost = param2
            card.validate()
        except ValueError as error:
            messagebox.showwarning("Carte invalide", str(error), parent=self)
            return False
        cards[self.selected_card_index[deck_name]] = card
        self._refresh_card_tree(deck_name)
        return True

    def _add_card(self, deck_name: str) -> None:
        """Ajoute une nouvelle carte financière neutre au paquet.

        Entrées:
            deck_name (str): Paquet à agrandir.

        Sortie:
            None: La nouvelle carte devient la sélection courante.
        """
        cards = self._deck_cards(deck_name)
        cards.append(CardConfig("MoneyCard", "Nouvelle carte", amount=0))
        self.selected_card_index[deck_name] = len(cards) - 1
        self._refresh_card_tree(deck_name)
        self._load_card_editor(deck_name, len(cards) - 1)

    def _remove_card(self, deck_name: str) -> None:
        """Supprime la carte sélectionnée sans permettre un paquet vide.

        Entrées:
            deck_name (str): Paquet concerné.

        Sortie:
            None: La carte est retirée lorsque le paquet en contient plusieurs.
        """
        cards = self._deck_cards(deck_name)
        if len(cards) <= 1:
            messagebox.showwarning("Paquet", "Un paquet doit garder au moins une carte.", parent=self)
            return
        index = self.selected_card_index[deck_name]
        del cards[index]
        self.selected_card_index[deck_name] = max(0, min(index, len(cards) - 1))
        self._refresh_card_tree(deck_name)
        self._load_card_editor(deck_name, self.selected_card_index[deck_name])
        self._refresh_validation_report(commit=False)

    def _commit_current_editors(self) -> bool:
        """Enregistre les trois formulaires courants avant une opération globale.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` si la case, les cartes et le plateau complet sont valides.
        """
        if not self._apply_space_editor():
            return False
        for deck_name in ("chance", "community_chest"):
            if not self._apply_card_editor(deck_name):
                return False
        self.board_config.name = self.board_name_var.get().strip() or "Plateau personnalisé"
        valid = self._refresh_validation_report(commit=False)
        if not valid:
            messagebox.showwarning(
                "Plateau invalide",
                "Corrigez les erreurs bloquantes indiquées dans le panneau de validation.",
                parent=self,
            )
            return False
        return True

    def _refresh_preset_list(self) -> None:
        """Recharge les presets locaux de plateau.

        Entrées:
            Aucune.

        Sortie:
            None: La combobox reflète la bibliothèque locale.
        """
        presets = list_board_presets(self.preset_directory)
        self.local_presets = {preset.name: preset for preset in presets}
        names = list(self.local_presets)
        self.preset_combo.configure(values=names)
        if self.preset_var.get() not in self.local_presets:
            self.preset_var.set(names[0] if names else "")

    def _apply_board_config(self, board_config: BoardConfig) -> None:
        """Remplace le brouillon complet et recharge les trois onglets.

        Entrées:
            board_config (BoardConfig): Nouveau plateau à éditer.

        Sortie:
            None: Cases, cartes et sélections sont réinitialisées.
        """
        self.board_config = board_config.clone()
        self.board_name_var.set(self.board_config.name)
        self.selected_space_index = 0
        self.selected_card_index = {"chance": 0, "community_chest": 0}
        self._refresh_space_tree()
        self._load_space_editor(0)
        for deck_name in ("chance", "community_chest"):
            self._refresh_card_tree(deck_name)
            self._load_card_editor(deck_name, 0)
        self._refresh_validation_report(commit=False)

    def _open_preset_library(self) -> None:
        """Ouvre la bibliothèque avancée avec aperçu, renommage et suppression.

        Entrées:
            Aucune.

        Sortie:
            None: Le preset chargé depuis le dialogue devient le brouillon courant.
        """
        dialog = BoardPresetLibraryDialog(self, self.preset_directory)
        self.wait_window(dialog)
        self._refresh_preset_list()
        if dialog.selected is not None:
            self.preset_var.set(dialog.selected.name)
            self._apply_board_config(dialog.selected.board_config)

    def _new_board_wizard(self) -> None:
        """Lance l'assistant de création d'un plateau standard ou vierge.

        Entrées:
            Aucune.

        Sortie:
            None: Le plateau créé remplace le brouillon actuel après confirmation implicite.
        """
        dialog = BoardCreationWizard(self)
        self.wait_window(dialog)
        if dialog.result is not None:
            self._apply_board_config(dialog.result)

    def _load_selected_preset(self) -> None:
        """Charge le preset local sélectionné dans l'éditeur.

        Entrées:
            Aucune.

        Sortie:
            None: Le plateau du preset remplace le brouillon.
        """
        preset = self.local_presets.get(self.preset_var.get())
        if preset is None:
            messagebox.showwarning("Preset", "Sélectionnez un preset de plateau.", parent=self)
            return
        self._apply_board_config(preset.board_config)

    def _save_local_preset(self) -> None:
        """Sauvegarde le brouillon courant dans la bibliothèque locale.

        Entrées:
            Aucune.

        Sortie:
            None: Un preset JSON local est créé puis sélectionné.
        """
        if not self._commit_current_editors():
            return
        name = simpledialog.askstring("Preset de plateau", "Nom du preset :", parent=self)
        if not name or not name.strip():
            return
        self.board_config.name = name.strip()
        self.board_name_var.set(name.strip())
        save_named_board_preset(self.board_config, self.preset_directory, name.strip())
        self._refresh_preset_list()
        self.preset_var.set(name.strip())

    def _import_preset(self) -> None:
        """Importe un preset externe dans la bibliothèque locale et le charge.

        Entrées:
            Aucune.

        Sortie:
            None: Le preset importé devient le brouillon courant.
        """
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer un preset de plateau",
            filetypes=[("Preset de plateau", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        try:
            preset = import_board_preset(path, self.preset_directory)
        except BoardPresetError as error:
            messagebox.showerror("Import impossible", str(error), parent=self)
            return
        self._refresh_preset_list()
        self.preset_var.set(preset.name)
        self._apply_board_config(preset.board_config)

    def _export_current_preset(self) -> None:
        """Exporte le brouillon actuel vers un fichier JSON externe.

        Entrées:
            Aucune.

        Sortie:
            None: Un fichier portable est écrit à l'emplacement choisi.
        """
        if not self._commit_current_editors():
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le plateau",
            defaultextension=".json",
            filetypes=[("Preset de plateau", "*.json"), ("Tous les fichiers", "*.*")],
            initialfile="plateau_personnalise.json",
        )
        if not path:
            return
        name = self.board_config.name or Path(path).stem
        save_board_preset(self.board_config, path, name)

    def _reset_standard(self) -> None:
        """Restaure le plateau et les cartes standards dans l'éditeur.

        Entrées:
            Aucune.

        Sortie:
            None: Le brouillon redevient la configuration standard.
        """
        self._apply_board_config(BoardConfig.standard())

    def _save_board(self) -> None:
        """Valide le brouillon et le transmet à l'écran de préparation.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit une copie indépendante du plateau.
        """
        if not self._commit_current_editors():
            return
        self.save_callback(self.board_config.clone())
