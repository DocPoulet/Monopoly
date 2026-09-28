"""Interface V21.8 du laboratoire statistique neutre, analyses et rapports."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from monopoly.profile_packs import ProfilePackError, load_profile_pack
from monopoly.simulation_reports import (
    SimulationReportError,
    export_html_report,
    load_simulation_report,
)
from monopoly.simulation import (
    PlayerSimulationSummary,
    SimulationCampaignResult,
    SimulationComparisonResult,
    SimulationConfig,
    SimulationRunner,
    SimulationScenario,
    resolve_base_seed,
)
from ui.widgets import TreeviewMultiSorter


CASE_PROPERTY_COLORS = {
    "brown": "#8B5A2B",
    "light_blue": "#79CFE8",
    "pink": "#D95FA6",
    "orange": "#F39C12",
    "red": "#E74C3C",
    "yellow": "#F4D03F",
    "green": "#27AE60",
    "dark_blue": "#3156A6",
}

CASE_TYPE_COLORS = {
    "go": "#8BCB98",
    "property": "#B8B8B8",
    "community_chest": "#7FB9E1",
    "tax": "#E5A2A2",
    "railroad": "#70767B",
    "chance": "#F0B05B",
    "jail": "#B7A18E",
    "utility": "#9FD5E6",
    "free_parking": "#E8D06C",
    "go_to_jail": "#DD8D8D",
}

CARD_DECK_COLORS = {
    "chance": "#F0B05B",
    "community_chest": "#7FB9E1",
}

CARD_DECK_LABELS = {
    "Tous": "",
    "Chance": "chance",
    "Communauté": "community_chest",
}

SPACE_TYPE_LABELS = {
    "go": "DÉPART",
    "property": "TERRAIN",
    "community_chest": "CAISSE DE COMMUNAUTÉ",
    "tax": "TAXE",
    "railroad": "GARE",
    "chance": "CHANCE",
    "jail": "PRISON / VISITE",
    "utility": "COMPAGNIE",
    "free_parking": "PARC GRATUIT",
    "go_to_jail": "ALLEZ EN PRISON",
}


class BoardBarHoverCard:
    """Affiche une fiche de case lors du survol d'une barre analytique.

    Entrées:
        master (tk.Misc): Fenêtre ou vue propriétaire de la fiche flottante.

    Sortie:
        BoardBarHoverCard: Info-bulle riche capable de reproduire une carte de propriété.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit une fenêtre flottante non activante et initialement cachée.

        Entrées:
            master (tk.Misc): Widget parent utilisé pour créer le ``Toplevel``.

        Sortie:
            None: La fiche existe mais reste invisible jusqu'au premier survol.
        """
        self.window = tk.Toplevel(master)
        self.window.withdraw()
        self.window.overrideredirect(True)
        try:
            self.window.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.frame = tk.Frame(
            self.window,
            background="#FFFFFF",
            highlightbackground="#263238",
            highlightthickness=2,
        )
        self.frame.pack(fill="both", expand=True)
        self.header = tk.Frame(self.frame, background="#70767B", padx=10, pady=7)
        self.header.pack(fill="x")
        self.type_label = tk.Label(
            self.header,
            text="",
            background="#70767B",
            foreground="#FFFFFF",
            font=("Arial", 8, "bold"),
        )
        self.type_label.pack(anchor="center")
        self.name_label = tk.Label(
            self.header,
            text="",
            background="#70767B",
            foreground="#FFFFFF",
            font=("Arial", 12, "bold"),
            wraplength=300,
            justify="center",
        )
        self.name_label.pack(anchor="center", pady=(2, 0))
        self.metric_label = tk.Label(
            self.frame,
            text="",
            background="#EEF3F0",
            foreground="#23402F",
            font=("Arial", 9, "bold"),
            padx=9,
            pady=5,
        )
        self.metric_label.pack(fill="x")
        self.details = tk.Frame(self.frame, background="#FFFFFF", padx=10, pady=8)
        self.details.pack(fill="both", expand=True)

    def show(
        self,
        scenario: SimulationScenario,
        space_index: int,
        metric_label: str,
        metric_value: str,
        x_root: int,
        y_root: int,
    ) -> None:
        """Remplit la fiche avec la case survolée et la place près du pointeur.

        Entrées:
            scenario (SimulationScenario): Profil dont provient le plateau affiché.
            space_index (int): Index de la case survolée.
            metric_label (str): Nom de la statistique représentée par la barre.
            metric_value (str): Valeur formatée de cette statistique.
            x_root (int): Coordonnée écran horizontale du pointeur.
            y_root (int): Coordonnée écran verticale du pointeur.

        Sortie:
            None: La fiche détaillée devient visible.
        """
        if not 0 <= space_index < len(scenario.board_config.spaces):
            self.hide()
            return
        space = scenario.board_config.spaces[space_index]
        color = CASE_TYPE_COLORS.get(space.space_type, "#70767B")
        if space.space_type == "property":
            color = CASE_PROPERTY_COLORS.get(
                space.color_group.strip().casefold(),
                CASE_TYPE_COLORS["property"],
            )
        self.header.configure(background=color)
        self.type_label.configure(
            text=f"CASE {space.index:02d} • {SPACE_TYPE_LABELS.get(space.space_type, space.space_type.upper())}",
            background=color,
        )
        self.name_label.configure(text=space.name.upper(), background=color)
        self.metric_label.configure(text=f"{metric_label} : {metric_value}")
        for child in self.details.winfo_children():
            child.destroy()
        for label, value, bold in self._detail_rows(scenario, space_index):
            row = tk.Frame(self.details, background="#FFFFFF")
            row.pack(fill="x", pady=1)
            font = ("Arial", 8, "bold" if bold else "normal")
            tk.Label(
                row,
                text=label,
                background="#FFFFFF",
                foreground="#46515C",
                font=font,
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                background="#FFFFFF",
                foreground="#1F2933",
                font=font,
            ).pack(side="right")
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = min(x_root + 16, max(0, screen_w - width - 8))
        y = min(y_root + 16, max(0, screen_h - height - 8))
        self.window.geometry(f"+{x}+{y}")
        self.window.deiconify()
        self.window.lift()

    def move(self, x_root: int, y_root: int) -> None:
        """Déplace une fiche déjà visible pour suivre légèrement le pointeur.

        Entrées:
            x_root (int): Nouvelle coordonnée écran horizontale.
            y_root (int): Nouvelle coordonnée écran verticale.

        Sortie:
            None: La fenêtre conserve un décalage confortable autour de la souris.
        """
        if self.window.state() == "withdrawn":
            return
        width = max(1, self.window.winfo_width())
        height = max(1, self.window.winfo_height())
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = min(x_root + 16, max(0, screen_w - width - 8))
        y = min(y_root + 16, max(0, screen_h - height - 8))
        self.window.geometry(f"+{x}+{y}")

    def hide(self) -> None:
        """Masque immédiatement la fiche flottante.

        Entrées:
            Aucune.

        Sortie:
            None: Aucun détail de case ne reste affiché.
        """
        self.window.withdraw()

    def _detail_rows(
        self,
        scenario: SimulationScenario,
        space_index: int,
    ) -> list[tuple[str, str, bool]]:
        """Construit les lignes financières adaptées au type de case survolé.

        Entrées:
            scenario (SimulationScenario): Règles et plateau de la campagne.
            space_index (int): Position de la case à décrire.

        Sortie:
            list[tuple[str, str, bool]]: Libellé, valeur et indicateur de graisse.
        """
        space = scenario.board_config.spaces[space_index]
        options = scenario.options
        rows: list[tuple[str, str, bool]] = []
        if space.space_type in {"property", "railroad", "utility"}:
            effective_price = max(
                1,
                round(space.price * options.property_price_percent / 100),
            )
            rows.append(("Prix simulation", f"{effective_price} $", True))
            rows.append(("Hypothèque", f"{effective_price // 2} $", False))
        if space.space_type == "property":
            scale = options.rent_percent / 100
            rows.append(("Groupe", space.color_group, False))
            rows.append(("Loyer nu", f"{round(space.base_rent * scale)} $", True))
            for count, rent in enumerate(space.house_rents, start=1):
                rows.append((f"{count} maison{'s' if count > 1 else ''}", f"{round(rent * scale)} $", False))
            rows.append(("Hôtel", f"{round(space.hotel_rent * scale)} $", True))
            rows.append(("Construction", f"{space.house_cost} $", False))
        elif space.space_type == "railroad":
            scale = options.rent_percent / 100
            for count, rent in enumerate(space.railroad_rents, start=1):
                rows.append((f"{count} gare{'s' if count > 1 else ''}", f"{round(rent * scale)} $", count == 4))
        elif space.space_type == "utility":
            multipliers = " / ".join(f"×{value}" for value in space.utility_multipliers)
            rows.append(("Multiplicateurs", multipliers, True))
            if options.rent_percent != 100:
                rows.append(("Modif. loyers", f"{options.rent_percent} %", False))
        elif space.space_type == "tax":
            rows.append(("Taxe", f"{space.tax_amount} $", True))
        else:
            rows.append(("Type", SPACE_TYPE_LABELS.get(space.space_type, space.space_type), True))
        return rows


class SimulationLabView(ttk.Frame):
    """Configure, lance, compare et analyse des campagnes sans stratégie.

    Entrées:
        master (tk.Misc): Conteneur parent.
        back_callback (Callable[[], None]): Retour vers le menu principal.

    Sortie:
        SimulationLabView: Laboratoire complet de stress-test statistique.
    """

    PLAYER_METRICS = (
        "1re place (%)",
        "Victoire finie (%)",
        "Faillite (%)",
        "Patrimoine final",
        "Cash final",
        "Biens finaux",
        "Loyers reçus",
        "Loyers payés",
        "Prison",
    )

    def __init__(
        self,
        master: tk.Misc,
        back_callback: Callable[[], None],
    ) -> None:
        """Construit paramètres, scénarios, tableaux et graphiques du laboratoire.

        Entrées:
            master (tk.Misc): Conteneur parent.
            back_callback (Callable[[], None]): Callback du bouton Retour.

        Sortie:
            None: L'écran est prêt avec un scénario classique initial.
        """
        super().__init__(master, padding=12)
        self.back_callback = back_callback
        self.scenarios: list[SimulationScenario] = [SimulationScenario.standard()]
        self.result: SimulationComparisonResult | None = None
        self.running = False
        self.selected_campaign_index = 0
        self.last_used_seed: int | None = None
        self.table_sorters: dict[ttk.Treeview, TreeviewMultiSorter] = {}
        self.bar_hover_card = BoardBarHoverCard(self)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._build_header()
        self._build_controls()
        self._build_scenarios()
        self._build_results()
        self._refresh_scenarios()

    def _build_header(self) -> None:
        """Construit le titre, la méthode neutre et le bouton de retour.

        Entrées:
            Aucune.

        Sortie:
            None: L'en-tête est affiché.
        """
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 9))
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text="Laboratoire de simulation — analyse avancée",
            font=("Arial", 21, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame,
            text=(
                "Aucune stratégie : décisions neutres/aléatoires fixes. Le laboratoire mesure "
                "le moteur, les règles et les plateaux sans chercher à gagner."
            ),
            style="Muted.TLabel",
            wraplength=1000,
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(
            frame,
            text="Retour",
            command=self._back,
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

    def _build_controls(self) -> None:
        """Construit volume, joueurs, limite, seed et parallélisme de campagne.

        Entrées:
            Aucune.

        Sortie:
            None: Les contrôles de campagne sont affichés.
        """
        frame = ttk.LabelFrame(self, text="Campagne", padding=9)
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 9))
        frame.columnconfigure(13, weight=1)

        self.games_var = tk.StringVar(value="100")
        self.players_var = tk.StringVar(value="4")
        self.max_rounds_var = tk.StringVar(value="250")
        self.seed_var = tk.StringVar(value="")
        self.workers_var = tk.StringVar(value="Auto")
        self._last_progress_refresh = 0.0

        ttk.Label(frame, text="Parties / scénario").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.games_var, width=8).grid(
            row=0, column=1, sticky="w", padx=(5, 14)
        )
        ttk.Label(frame, text="Joueurs").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.players_var,
            values=("2", "3", "4"),
            state="readonly",
            width=5,
        ).grid(row=0, column=3, sticky="w", padx=(5, 14))
        ttk.Label(frame, text="Tours max (0/vide = ∞)").grid(row=0, column=4, sticky="w")
        ttk.Entry(frame, textvariable=self.max_rounds_var, width=8).grid(
            row=0, column=5, sticky="w", padx=(5, 14)
        )
        ttk.Label(frame, text="Seed").grid(row=0, column=6, sticky="w")
        ttk.Entry(frame, textvariable=self.seed_var, width=12).grid(
            row=0, column=7, sticky="w", padx=(5, 5)
        )
        ttk.Label(
            frame,
            text="vide = aléatoire",
            style="Muted.TLabel",
        ).grid(row=0, column=8, sticky="w", padx=(0, 14))
        ttk.Label(frame, text="Processus").grid(row=0, column=9, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.workers_var,
            values=("Auto", "1", "2", "4", "8"),
            state="readonly",
            width=6,
        ).grid(row=0, column=10, sticky="w", padx=(5, 14))

        self.run_button = ttk.Button(
            frame,
            text="Lancer les simulations",
            style="Primary.TButton",
            command=self._run,
        )
        self.run_button.grid(row=0, column=11, sticky="e")

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(
            frame,
            variable=self.progress_var,
            maximum=100.0,
        )
        self.progress.grid(row=1, column=0, columnspan=14, sticky="ew", pady=(8, 0))
        self.progress_label = ttk.Label(
            frame,
            text="Prêt. Seed vide : une seed aléatoire sera générée au lancement.",
            style="Muted.TLabel",
        )
        self.progress_label.grid(row=2, column=0, columnspan=14, sticky="w", pady=(3, 0))

    def _build_scenarios(self) -> None:
        """Construit la liste des scénarios et les actions d'import de packs.

        Entrées:
            Aucune.

        Sortie:
            None: La zone de comparaison est affichée.
        """
        frame = ttk.LabelFrame(self, text="Scénarios comparés", padding=8)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 9))
        frame.columnconfigure(0, weight=1)

        self.scenario_tree = ttk.Treeview(
            frame,
            columns=("rules", "board"),
            show="tree headings",
            height=3,
            selectmode="browse",
        )
        self.scenario_tree.heading("#0", text="Scénario")
        self.scenario_tree.heading("rules", text="Règles")
        self.scenario_tree.heading("board", text="Plateau")
        self.scenario_tree.column("#0", width=170)
        self.scenario_tree.column("rules", width=560)
        self.scenario_tree.column("board", width=250)
        self.scenario_tree.grid(row=0, column=0, sticky="ew")

        buttons = ttk.Frame(frame)
        buttons.grid(row=1, column=0, sticky="ew", pady=(7, 0))
        ttk.Button(buttons, text="Ajouter classique", command=self._add_standard).pack(
            side="left"
        )
        ttk.Button(
            buttons,
            text="Importer un pack règles + plateau",
            command=self._import_pack,
        ).pack(side="left", padx=(6, 0))
        ttk.Button(
            buttons,
            text="Charger rapport JSON",
            command=self._load_report,
        ).pack(side="left", padx=(6, 0))
        ttk.Button(buttons, text="Retirer", command=self._remove_selected).pack(
            side="left", padx=(6, 0)
        )
        ttk.Label(
            buttons,
            text=(
                "Tous les scénarios utilisent la même série de seeds : comparaison plus propre, "
                "toujours sans stratégie."
            ),
            style="Muted.TLabel",
        ).pack(side="left", padx=(14, 0))

    def _build_results(self) -> None:
        """Construit les onglets de comparaison, détails, parties et méthode.

        Entrées:
            Aucune.

        Sortie:
            None: La zone d'analyse enrichie occupe l'espace inférieur.
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=3, column=0, sticky="nsew")

        self.comparison_tab = ttk.Frame(self.notebook, padding=7)
        self.details_tab = ttk.Frame(self.notebook, padding=7)
        self.board_stats_tab = ttk.Frame(self.notebook, padding=7)
        self.cards_tab = ttk.Frame(self.notebook, padding=7)
        self.cross_tab = ttk.Frame(self.notebook, padding=7)
        self.games_tab = ttk.Frame(self.notebook, padding=7)
        self.method_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.comparison_tab, text="Comparaison")
        self.notebook.add(self.details_tab, text="Détail scénario")
        self.notebook.add(self.board_stats_tab, text="Cases & rendement")
        self.notebook.add(self.cards_tab, text="Cartes")
        self.notebook.add(self.cross_tab, text="Analyse croisée")
        self.notebook.add(self.games_tab, text="Parties")
        self.notebook.add(self.method_tab, text="Méthode")

        self._build_comparison_tab()
        self._build_details_tab()
        self._build_board_stats_tab()
        self._build_cards_tab()
        self._build_cross_analysis_tab()
        self._build_games_tab()
        self._build_method_tab()

    def _build_comparison_tab(self) -> None:
        """Construit le tableau synthétique et quatre graphiques comparatifs.

        Entrées:
            Aucune.

        Sortie:
            None: L'onglet Comparaison est prêt.
        """
        tab = self.comparison_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)

        columns = (
            "games",
            "finish",
            "rounds",
            "median",
            "p90",
            "std",
            "actions",
            "rent",
            "maxrent",
            "bankruptcies",
        )
        self.result_tree = ttk.Treeview(
            top,
            columns=columns,
            show="tree headings",
            height=6,
            selectmode="browse",
        )
        labels = {
            "#0": "Scénario",
            "games": "Parties",
            "finish": "Fin %",
            "rounds": "Tours moy.",
            "median": "Médiane",
            "p90": "P90",
            "std": "Écart-type",
            "actions": "Actions moy.",
            "rent": "Loyers moy.",
            "maxrent": "Loyer max",
            "bankruptcies": "Faillites moy.",
        }
        for key, label in labels.items():
            self.result_tree.heading(key, text=label)
        self.result_tree.column("#0", width=160)
        for column in columns:
            self.result_tree.column(column, width=88, anchor="center")
        self.result_tree.grid(row=0, column=0, sticky="ew")
        self.result_tree.bind("<<TreeviewSelect>>", self._result_selected)
        self._register_sortable_tree(self.result_tree, labels)

        export = ttk.Frame(top)
        export.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.export_json_button = ttk.Button(
            export,
            text="Exporter JSON complet",
            command=self._export_json,
        )
        self.export_json_button.pack(side="left")
        self.export_csv_button = ttk.Button(
            export,
            text="Exporter parties CSV",
            command=self._export_csv,
        )
        self.export_csv_button.pack(side="left", padx=(6, 0))
        self.export_summary_button = ttk.Button(
            export,
            text="Exporter résumé CSV",
            command=self._export_summary_csv,
        )
        self.export_summary_button.pack(side="left", padx=(6, 0))
        self.export_board_button = ttk.Button(
            export,
            text="Exporter cases / ROI CSV",
            command=self._export_board_csv,
        )
        self.export_board_button.pack(side="left", padx=(6, 0))
        self.export_development_button = ttk.Button(
            export,
            text="Exporter constructions CSV",
            command=self._export_development_csv,
        )
        self.export_development_button.pack(side="left", padx=(6, 0))
        self.export_cards_button = ttk.Button(
            export,
            text="Exporter cartes CSV",
            command=self._export_cards_csv,
        )
        self.export_cards_button.pack(side="left", padx=(6, 0))
        self.export_html_button = ttk.Button(
            export,
            text="Rapport HTML",
            command=self._export_html,
        )
        self.export_html_button.pack(side="left", padx=(6, 0))
        for button in (
            self.export_json_button,
            self.export_csv_button,
            self.export_summary_button,
            self.export_board_button,
            self.export_development_button,
            self.export_cards_button,
            self.export_html_button,
        ):
            button.state(["disabled"])

        charts = ttk.Frame(tab)
        charts.grid(row=1, column=0, sticky="nsew", pady=(7, 0))
        charts.columnconfigure(0, weight=1)
        charts.columnconfigure(1, weight=1)
        charts.rowconfigure(0, weight=1)
        charts.rowconfigure(1, weight=1)

        self.duration_chart = self._make_chart_box(
            charts, "Durée : moyenne et P90", 0, 0
        )
        self.finish_chart = self._make_chart_box(
            charts, "Parties terminées (%)", 0, 1
        )
        self.rent_chart = self._make_chart_box(
            charts, "Loyers : moyenne et maximum", 1, 0
        )
        self.activity_chart = self._make_chart_box(
            charts, "Activité moyenne par partie", 1, 1
        )

    def _make_chart_box(
        self,
        parent: ttk.Frame,
        title: str,
        row: int,
        column: int,
    ) -> tk.Canvas:
        """Crée un cadre graphique redimensionnable et retourne son canvas.

        Entrées:
            parent (ttk.Frame): Conteneur de graphiques.
            title (str): Titre du graphique.
            row (int): Ligne de la grille.
            column (int): Colonne de la grille.

        Sortie:
            tk.Canvas: Canvas prêt pour les histogrammes du laboratoire.
        """
        frame = ttk.LabelFrame(parent, text=title, padding=5)
        frame.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=(0, 4) if column == 0 else (4, 0),
            pady=(0, 4) if row == 0 else (4, 0),
        )
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        canvas = tk.Canvas(
            frame,
            background="#FFFFFF",
            highlightthickness=0,
            height=175,
        )
        canvas.grid(row=0, column=0, sticky="nsew")
        canvas.bind("<Configure>", self._redraw_all_charts_event)
        return canvas

    def _register_sortable_tree(
        self,
        tree: ttk.Treeview,
        labels: dict[str, str],
    ) -> None:
        """Active le tri multi-colonnes cyclique sur un tableau statistique.

        Entrées:
            tree (ttk.Treeview): Tableau dont les en-têtes deviennent cliquables.
            labels (dict[str, str]): Libellés de base à conserver sous les indicateurs de tri.

        Sortie:
            None: Le contrôleur de tri est conservé par la vue.
        """
        self.table_sorters[tree] = TreeviewMultiSorter(tree, labels)

    def _refresh_tree_sorter(self, tree: ttk.Treeview) -> None:
        """Actualise l'ordre naturel d'un tableau après son remplissage.

        Entrées:
            tree (ttk.Treeview): Tableau venant d'être repeuplé.

        Sortie:
            None: Le tri actif est réappliqué aux nouvelles lignes.
        """
        sorter = self.table_sorters.get(tree)
        if sorter is not None:
            sorter.refresh_base_order()

    def _build_details_tab(self) -> None:
        """Construit les statistiques de propriétés, sièges et distributions.

        Entrées:
            Aucune.

        Sortie:
            None: L'onglet détaillé est prêt.
        """
        tab = self.details_tab
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=2)
        tab.rowconfigure(2, weight=2)

        header = ttk.Frame(tab)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        header.columnconfigure(0, weight=1)
        self.detail_title = ttk.Label(
            header,
            text="Aucune campagne sélectionnée",
            font=("Arial", 13, "bold"),
        )
        self.detail_title.grid(row=0, column=0, sticky="w")
        self.detail_kpi = ttk.Label(header, text="", style="Muted.TLabel")
        self.detail_kpi.grid(row=1, column=0, sticky="w", pady=(2, 0))

        properties = ttk.LabelFrame(tab, text="Rentabilité des propriétés", padding=6)
        properties.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        properties.columnconfigure(0, weight=1)
        properties.rowconfigure(0, weight=1)
        self.property_tree = ttk.Treeview(
            properties,
            columns=("average", "eventavg", "total", "events", "games", "biggest"),
            show="tree headings",
            selectmode="browse",
        )
        for key, text in {
            "#0": "Bien",
            "average": "$/partie",
            "eventavg": "$/loyer",
            "total": "Total",
            "events": "Loyers",
            "games": "Parties +",
            "biggest": "Max",
        }.items():
            self.property_tree.heading(key, text=text)
        self.property_tree.column("#0", width=180)
        for key in ("average", "eventavg", "total", "events", "games", "biggest"):
            self.property_tree.column(key, width=72, anchor="center")
        self.property_tree.grid(row=0, column=0, sticky="nsew")
        self._register_sortable_tree(
            self.property_tree,
            {
                "#0": "Bien",
                "average": "$/partie",
                "eventavg": "$/loyer",
                "total": "Total",
                "events": "Loyers",
                "games": "Parties +",
                "biggest": "Max",
            },
        )

        players = ttk.LabelFrame(tab, text="Profil par siège neutre", padding=6)
        players.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
        players.columnconfigure(0, weight=1)
        players.rowconfigure(0, weight=1)
        self.player_tree = ttk.Treeview(
            players,
            columns=("wins", "natural", "cutoff", "bankrupt", "worth", "cash", "props", "rentplus", "rentminus", "jail"),
            show="tree headings",
            selectmode="browse",
        )
        player_labels = {
            "#0": "Siège",
            "wins": "1re place %",
            "natural": "Victoire finie %",
            "cutoff": "Leads cutoff",
            "bankrupt": "Faillite %",
            "worth": "Patrimoine",
            "cash": "Cash",
            "props": "Biens",
            "rentplus": "Loyers +",
            "rentminus": "Loyers -",
            "jail": "Prison",
        }
        for key, text in player_labels.items():
            self.player_tree.heading(key, text=text)
        self.player_tree.column("#0", width=100)
        for key in player_labels:
            if key != "#0":
                self.player_tree.column(key, width=78, anchor="center")
        self.player_tree.grid(row=0, column=0, sticky="nsew")
        self._register_sortable_tree(self.player_tree, player_labels)

        duration_frame = ttk.LabelFrame(tab, text="Distribution des durées", padding=6)
        duration_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 4), pady=(7, 0))
        duration_frame.columnconfigure(0, weight=1)
        duration_frame.rowconfigure(0, weight=1)
        self.histogram_chart = tk.Canvas(
            duration_frame,
            background="#FFFFFF",
            highlightthickness=0,
            height=190,
        )
        self.histogram_chart.grid(row=0, column=0, sticky="nsew")
        self.histogram_chart.bind("<Configure>", self._redraw_detail_charts_event)

        seat_frame = ttk.LabelFrame(tab, text="Comparaison des sièges", padding=6)
        seat_frame.grid(row=2, column=1, sticky="nsew", padx=(4, 0), pady=(7, 0))
        seat_frame.columnconfigure(0, weight=1)
        seat_frame.rowconfigure(1, weight=1)
        controls = ttk.Frame(seat_frame)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(controls, text="Mesure :").pack(side="left")
        self.player_metric_var = tk.StringVar(value=self.PLAYER_METRICS[0])
        player_combo = ttk.Combobox(
            controls,
            textvariable=self.player_metric_var,
            values=self.PLAYER_METRICS,
            state="readonly",
            width=23,
        )
        player_combo.pack(side="left", padx=(5, 0))
        player_combo.bind("<<ComboboxSelected>>", self._player_metric_changed)
        self.player_chart = tk.Canvas(
            seat_frame,
            background="#FFFFFF",
            highlightthickness=0,
            height=165,
        )
        self.player_chart.grid(row=1, column=0, sticky="nsew")
        self.player_chart.bind("<Configure>", self._redraw_detail_charts_event)

    def _build_board_stats_tab(self) -> None:
        """Construit fréquentation, ROI par case et rendement par construction.

        Entrées:
            Aucune.

        Sortie:
            None: Un nouvel onglet analytique est prêt.
        """
        tab = self.board_stats_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=2)
        tab.rowconfigure(2, weight=1)

        header = ttk.Frame(tab)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(0, weight=1)
        self.board_stats_title = ttk.Label(
            header,
            text="Cases & rendement — aucun scénario sélectionné",
            font=("Arial", 13, "bold"),
        )
        self.board_stats_title.grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=(
                "ROI brut = loyers encaissés / argent réellement investi en achats, "
                "enchères et constructions. Les hypothèques/reventes ne sont pas déduites."
            ),
            style="Muted.TLabel",
            wraplength=1050,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.board_stats_kpi = ttk.Label(
            header,
            text="",
            style="Muted.TLabel",
            wraplength=1050,
        )
        self.board_stats_kpi.grid(row=2, column=0, sticky="w", pady=(2, 0))

        charts = ttk.Frame(tab)
        charts.grid(row=1, column=0, sticky="nsew")
        charts.columnconfigure(0, weight=1)
        charts.columnconfigure(1, weight=1)
        charts.rowconfigure(0, weight=1)
        charts.rowconfigure(1, weight=1)

        self.landings_chart = self._make_chart_box(
            charts, "Arrêts moyens par case / partie", 0, 0
        )
        self.roi_chart = self._make_chart_box(
            charts, "Rendement brut loyers / investissement", 0, 1
        )
        self.rent_per_stop_chart = self._make_chart_box(
            charts, "Loyer généré par arrêt sur la case", 1, 0
        )
        for canvas in (self.landings_chart, self.roi_chart, self.rent_per_stop_chart):
            canvas.bind("<Configure>", self._redraw_board_charts_event)
            canvas.bind("<Leave>", self._hide_bar_hover)

        development_frame = ttk.LabelFrame(
            charts, text="Rendement par nombre de constructions", padding=5
        )
        development_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0), pady=(4, 0))
        development_frame.columnconfigure(0, weight=1)
        development_frame.rowconfigure(1, weight=1)
        control = ttk.Frame(development_frame)
        control.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(control, text="Terrain :").pack(side="left")
        self.development_property_var = tk.StringVar(value="")
        self.development_property_combo = ttk.Combobox(
            control,
            textvariable=self.development_property_var,
            state="readonly",
            width=36,
        )
        self.development_property_combo.pack(side="left", padx=(5, 0))
        self.development_property_combo.bind(
            "<<ComboboxSelected>>",
            self._development_property_changed,
        )
        self.development_chart = tk.Canvas(
            development_frame,
            background="#FFFFFF",
            highlightthickness=0,
            height=175,
        )
        self.development_chart.grid(row=1, column=0, sticky="nsew")
        self.development_chart.bind("<Configure>", self._redraw_board_charts_event)
        self.development_chart.bind("<Leave>", self._hide_bar_hover)

        table = ttk.LabelFrame(tab, text="Données exactes par case", padding=5)
        table.grid(row=2, column=0, sticky="nsew", pady=(7, 0))
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        columns = ("stops", "share", "invest", "rent", "roi", "net", "rentstop")
        self.case_tree = ttk.Treeview(
            table,
            columns=columns,
            show="tree headings",
            height=7,
        )
        labels = {
            "#0": "Case",
            "stops": "Arrêts/partie",
            "share": "Part arrêts %",
            "invest": "Investi",
            "rent": "Loyers",
            "roi": "ROI %",
            "net": "Loyers-invest.",
            "rentstop": "$/arrêt",
        }
        for key, label in labels.items():
            self.case_tree.heading(key, text=label)
        self.case_tree.column("#0", width=230)
        for key in columns:
            self.case_tree.column(key, width=100, anchor="center")
        self.case_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.case_tree.yview)
        self.case_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        self._register_sortable_tree(self.case_tree, labels)


    def _build_cards_tab(self) -> None:
        """Construit les statistiques détaillées Chance et Communauté.

        Entrées:
            Aucune.

        Sortie:
            None: Un tableau et quatre graphiques dédiés aux cartes sont disponibles.
        """
        tab = self.cards_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=2)
        tab.rowconfigure(2, weight=1)

        header = ttk.Frame(tab)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(0, weight=1)
        self.cards_title = ttk.Label(
            header,
            text="Cartes — aucun scénario sélectionné",
            font=("Arial", 13, "bold"),
        )
        self.cards_title.grid(row=0, column=0, sticky="w")
        self.cards_kpi = ttk.Label(
            header,
            text="",
            style="Muted.TLabel",
            wraplength=1000,
        )
        self.cards_kpi.grid(row=1, column=0, sticky="w", pady=(2, 0))

        filter_frame = ttk.Frame(header)
        filter_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))
        ttk.Label(filter_frame, text="Paquet :").pack(side="left")
        self.card_deck_var = tk.StringVar(value="Chance")
        combo = ttk.Combobox(
            filter_frame,
            textvariable=self.card_deck_var,
            values=tuple(CARD_DECK_LABELS),
            state="readonly",
            width=14,
        )
        combo.pack(side="left", padx=(5, 0))
        combo.bind("<<ComboboxSelected>>", self._card_deck_changed)

        charts = ttk.Frame(tab)
        charts.grid(row=1, column=0, sticky="nsew")
        charts.columnconfigure(0, weight=1)
        charts.columnconfigure(1, weight=1)
        charts.rowconfigure(0, weight=1)
        charts.rowconfigure(1, weight=1)

        self.card_frequency_chart = self._make_chart_box(
            charts, "Fréquence de tirage par carte", 0, 0
        )
        self.card_cash_chart = self._make_chart_box(
            charts, "Impact cash moyen sur le joueur", 0, 1
        )
        self.card_pot_chart = self._make_chart_box(
            charts, "Contribution cumulée à la cagnotte", 1, 0
        )
        self.card_effect_chart = self._make_chart_box(
            charts, "Effets observés (%)", 1, 1
        )
        for canvas in (
            self.card_frequency_chart,
            self.card_cash_chart,
            self.card_pot_chart,
            self.card_effect_chart,
        ):
            canvas.bind("<Configure>", self._redraw_card_charts_event)

        table = ttk.LabelFrame(tab, text="Données exactes par carte", padding=5)
        table.grid(row=2, column=0, sticky="nsew", pady=(7, 0))
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        columns = (
            "deck", "type", "draws", "avg", "share", "cashavg", "cashtotal",
            "others", "pot", "move", "jail", "getout", "gain", "loss",
        )
        self.card_tree = ttk.Treeview(
            table,
            columns=columns,
            show="tree headings",
            height=8,
        )
        labels = {
            "#0": "Carte",
            "deck": "Paquet",
            "type": "Type",
            "draws": "Tirages",
            "avg": "/partie",
            "share": "Part paquet %",
            "cashavg": "Cash/tirage",
            "cashtotal": "Cash total",
            "others": "Autres joueurs",
            "pot": "Cagnotte",
            "move": "Déplacement %",
            "jail": "Prison %",
            "getout": "Sortie prison %",
            "gain": "Gain max",
            "loss": "Perte max",
        }
        for key, label in labels.items():
            self.card_tree.heading(key, text=label)
        self.card_tree.column("#0", width=330)
        self.card_tree.column("deck", width=90, anchor="center")
        self.card_tree.column("type", width=125, anchor="center")
        for key in columns:
            if key not in ("deck", "type"):
                self.card_tree.column(key, width=92, anchor="center")
        self.card_tree.grid(row=0, column=0, sticky="nsew")
        vscroll = ttk.Scrollbar(table, orient="vertical", command=self.card_tree.yview)
        hscroll = ttk.Scrollbar(table, orient="horizontal", command=self.card_tree.xview)
        self.card_tree.configure(
            yscrollcommand=vscroll.set,
            xscrollcommand=hscroll.set,
        )
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        self._register_sortable_tree(self.card_tree, labels)

    def _build_cross_analysis_tab(self) -> None:
        """Construit les comparaisons transversales entre plusieurs scénarios.

        Entrées:
            Aucune.

        Sortie:
            None: Courbe des 40 cases, heatmap et comparaison des paquets sont prêts.
        """
        tab = self.cross_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        tab.rowconfigure(2, weight=1)

        header = ttk.Frame(tab)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(2, weight=1)
        ttk.Label(
            header,
            text="Analyse croisée des scénarios",
            font=("Arial", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Métrique cases :").grid(
            row=0, column=1, sticky="e", padx=(14, 4)
        )
        self.cross_metric_var = tk.StringVar(value="Arrêts / partie")
        combo = ttk.Combobox(
            header,
            textvariable=self.cross_metric_var,
            values=("Arrêts / partie", "ROI brut (%)", "$/arrêt"),
            state="readonly",
            width=18,
        )
        combo.grid(row=0, column=2, sticky="w")
        combo.bind("<<ComboboxSelected>>", self._cross_metric_changed)
        self.cross_kpi = ttk.Label(
            header,
            text="Lancez ou rechargez au moins une campagne.",
            style="Muted.TLabel",
        )
        self.cross_kpi.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))

        top = ttk.Frame(tab)
        top.grid(row=1, column=0, sticky="nsew")
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)
        top.rowconfigure(0, weight=1)
        self.cross_case_chart = self._make_chart_box(
            top, "40 cases — comparaison multi-scénarios", 0, 0
        )
        self.cross_heatmap = self._make_chart_box(
            top, "Heatmap des arrêts — scénario × case", 0, 1
        )
        self.cross_case_chart.bind("<Configure>", self._redraw_cross_charts_event)
        self.cross_heatmap.bind("<Configure>", self._redraw_cross_charts_event)

        bottom = ttk.Frame(tab)
        bottom.grid(row=2, column=0, sticky="nsew", pady=(7, 0))
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(0, weight=1)

        card_charts = ttk.Frame(bottom)
        card_charts.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        card_charts.columnconfigure(0, weight=1)
        card_charts.rowconfigure(0, weight=1)
        card_charts.rowconfigure(1, weight=1)
        self.cross_card_frequency_chart = self._make_chart_box(
            card_charts, "Chance / Communauté — tirages par partie", 0, 0
        )
        self.cross_card_cash_chart = self._make_chart_box(
            card_charts, "Chance / Communauté — impact cash par tirage", 1, 0
        )
        self.cross_card_frequency_chart.bind(
            "<Configure>", self._redraw_cross_charts_event
        )
        self.cross_card_cash_chart.bind(
            "<Configure>", self._redraw_cross_charts_event
        )

        table_frame = ttk.LabelFrame(
            bottom,
            text="Comparaison des paquets",
            padding=5,
        )
        table_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        columns = (
            "chance_draws", "chance_cash", "community_draws", "community_cash",
            "pot", "cards",
        )
        self.cross_card_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="tree headings",
            height=8,
        )
        labels = {
            "#0": "Scénario",
            "chance_draws": "Chance / partie",
            "chance_cash": "Chance $/tirage",
            "community_draws": "Communauté / partie",
            "community_cash": "Communauté $/tirage",
            "pot": "Cagnotte cartes",
            "cards": "Cartes / partie",
        }
        for key, label in labels.items():
            self.cross_card_tree.heading(key, text=label)
        self.cross_card_tree.column("#0", width=150)
        for column in columns:
            self.cross_card_tree.column(column, width=115, anchor="center")
        self.cross_card_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.cross_card_tree.yview,
        )
        self.cross_card_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        self._register_sortable_tree(self.cross_card_tree, labels)

    def _cross_metric_changed(self, event: tk.Event) -> None:
        """Redessine la comparaison des 40 cases après changement de métrique.

        Entrées:
            event (tk.Event): Événement de sélection du combobox.

        Sortie:
            None: Le graphique principal est recalculé depuis les mêmes résultats.
        """
        self._draw_cross_case_chart()

    def _redraw_cross_charts_event(self, event: tk.Event) -> None:
        """Redessine les graphiques croisés après redimensionnement d'un canvas.

        Entrées:
            event (tk.Event): Événement ``Configure`` Tkinter.

        Sortie:
            None: Les quatre graphiques croisés suivent la taille disponible.
        """
        self._refresh_cross_analysis()

    def _cross_case_values(
        self,
        campaign: SimulationCampaignResult,
        metric: str,
    ) -> list[float]:
        """Retourne quarante valeurs alignées par index de case pour une métrique.

        Entrées:
            campaign (SimulationCampaignResult): Campagne à convertir.
            metric (str): Mesure sélectionnée par l'utilisateur.

        Sortie:
            list[float]: Une valeur pour chaque index 0 à 39.
        """
        values = [0.0] * 40
        if metric == "Arrêts / partie":
            for item in campaign.space_summary:
                if 0 <= item.index < 40:
                    values[item.index] = item.average_landings_per_game
            return values
        investments = {
            item.index: item for item in campaign.property_investment_summary
        }
        for index in range(40):
            item = investments.get(index)
            if item is None:
                continue
            if metric == "ROI brut (%)":
                values[index] = item.roi_percent
            else:
                values[index] = item.rent_per_landing
        return values

    def _refresh_cross_analysis(self) -> None:
        """Actualise l'ensemble de l'onglet d'analyse multi-scénarios.

        Entrées:
            Aucune.

        Sortie:
            None: KPI, tableau, courbe, heatmap et comparaison cartes sont synchronisés.
        """
        for item in self.cross_card_tree.get_children():
            self.cross_card_tree.delete(item)
        if self.result is None or not self.result.campaigns:
            self.cross_kpi.configure(text="Lancez ou rechargez au moins une campagne.")
            for canvas in (
                self.cross_case_chart,
                self.cross_heatmap,
                self.cross_card_frequency_chart,
                self.cross_card_cash_chart,
            ):
                self._draw_empty_chart(canvas, "Aucun rapport chargé.")
            return

        total_games = sum(len(campaign.games) for campaign in self.result.campaigns)
        self.cross_kpi.configure(
            text=(
                f"{len(self.result.campaigns)} scénario(s) • {total_games} parties analysées • "
                f"mêmes seeds de base : {self.result.config.base_seed}."
            )
        )
        for index, campaign in enumerate(self.result.campaigns):
            chance = [item for item in campaign.card_summary if item.deck == "chance"]
            community = [
                item for item in campaign.card_summary
                if item.deck == "community_chest"
            ]
            chance_draws = sum(item.draws for item in chance)
            community_draws = sum(item.draws for item in community)
            chance_delta = sum(item.drawer_cash_delta for item in chance)
            community_delta = sum(item.drawer_cash_delta for item in community)
            games = max(1, len(campaign.games))
            chance_cash = chance_delta / chance_draws if chance_draws else 0.0
            community_cash = (
                community_delta / community_draws if community_draws else 0.0
            )
            self.cross_card_tree.insert(
                "",
                "end",
                iid=str(index),
                text=campaign.scenario_name,
                values=(
                    f"{chance_draws / games:.2f}",
                    f"{chance_cash:+.1f} $",
                    f"{community_draws / games:.2f}",
                    f"{community_cash:+.1f} $",
                    f"{campaign.total_card_pot_contribution:+d} $",
                    f"{campaign.average_cards_drawn:.2f}",
                ),
            )
        self._refresh_tree_sorter(self.cross_card_tree)
        self._draw_cross_case_chart()
        self._draw_landing_heatmap()
        self._draw_cross_card_charts()

    def _draw_cross_case_chart(self) -> None:
        """Dessine une courbe par scénario sur les indexes de case 0 à 39.

        Entrées:
            Aucune.

        Sortie:
            None: La métrique choisie devient comparable sur tout le plateau.
        """
        canvas = self.cross_case_chart
        if self.result is None or not self.result.campaigns:
            self._draw_empty_chart(canvas, "Aucune donnée multi-scénarios.")
            return
        metric = self.cross_metric_var.get()
        series = [
            (
                campaign.scenario_name,
                self._cross_case_values(campaign, metric),
            )
            for campaign in self.result.campaigns
        ]
        suffix = ""
        if metric == "ROI brut (%)":
            suffix = " %"
        elif metric == "$/arrêt":
            suffix = " $"
        self._draw_multi_line_chart(canvas, series, suffix=suffix)

    def _draw_multi_line_chart(
        self,
        canvas: tk.Canvas,
        series: list[tuple[str, list[float]]],
        suffix: str = "",
    ) -> None:
        """Dessine plusieurs séries continues alignées sur les 40 cases.

        Entrées:
            canvas (tk.Canvas): Surface graphique cible.
            series (list[tuple[str, list[float]]]): Nom et valeurs par scénario.
            suffix (str): Unité affichée dans la légende maximale.

        Sortie:
            None: Courbes, axes et légende sont dessinés sans dépendance externe.
        """
        canvas.delete("all")
        if not series:
            self._draw_empty_chart(canvas, "Aucune série.")
            return
        width = max(360, canvas.winfo_width())
        height = max(180, canvas.winfo_height())
        left, right, top, bottom = 42, 16, 25, 34
        usable_w = max(1, width - left - right)
        usable_h = max(1, height - top - bottom)
        maximum = max(
            1.0,
            max((max(values, default=0.0) for _, values in series), default=1.0),
        )
        canvas.create_line(left, height - bottom, width - right, height - bottom, fill="#7A8880")
        canvas.create_line(left, top, left, height - bottom, fill="#7A8880")
        palette = (
            "#2E7D57", "#3156A6", "#D17C2F", "#9B4D96",
            "#B23A48", "#3B8F9B", "#6A7D2E", "#8064A2",
        )
        for index in range(0, 40, 5):
            x = left + usable_w * index / 39
            canvas.create_text(x, height - bottom + 13, text=str(index), font=("Arial", 7), fill="#53615A")
        canvas.create_text(left - 5, top + 4, text=f"{maximum:.1f}{suffix}", anchor="e", font=("Arial", 7), fill="#53615A")
        for series_index, (name, values) in enumerate(series):
            color = palette[series_index % len(palette)]
            points: list[float] = []
            for index in range(40):
                value = values[index] if index < len(values) else 0.0
                x = left + usable_w * index / 39
                y = height - bottom - usable_h * max(0.0, value) / maximum
                points.extend((x, y))
            if len(points) >= 4:
                canvas.create_line(*points, fill=color, width=2, smooth=False)
            for index in range(0, 40, 5):
                value = values[index] if index < len(values) else 0.0
                x = left + usable_w * index / 39
                y = height - bottom - usable_h * max(0.0, value) / maximum
                canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=color, outline=color)
            legend_x = left + 8 + (series_index % 4) * max(110, usable_w / 4)
            legend_y = 10 + (series_index // 4) * 12
            canvas.create_line(legend_x, legend_y, legend_x + 16, legend_y, fill=color, width=3)
            canvas.create_text(legend_x + 20, legend_y, text=name[:18], anchor="w", font=("Arial", 7), fill="#344139")

    def _temperature_heat_color(self, ratio: float) -> str:
        """Convertit une intensité normalisée en couleur de heatmap type capteur.

        Entrées:
            ratio (float): Intensité comprise idéalement entre 0.0 et 1.0.

        Sortie:
            str: Couleur hexadécimale allant du bleu foncé au rouge foncé.
        """
        value = min(1.0, max(0.0, ratio))
        stops = [
            (0.00, (8, 48, 107)),
            (0.25, (33, 113, 181)),
            (0.50, (107, 174, 214)),
            (0.68, (255, 237, 160)),
            (0.84, (253, 141, 60)),
            (1.00, (103, 0, 13)),
        ]
        for (left_pos, left_rgb), (right_pos, right_rgb) in zip(stops, stops[1:]):
            if value <= right_pos:
                span = max(1e-9, right_pos - left_pos)
                local = (value - left_pos) / span
                red = round(left_rgb[0] + (right_rgb[0] - left_rgb[0]) * local)
                green = round(left_rgb[1] + (right_rgb[1] - left_rgb[1]) * local)
                blue = round(left_rgb[2] + (right_rgb[2] - left_rgb[2]) * local)
                return f"#{red:02x}{green:02x}{blue:02x}"
        return "#67000d"

    def _draw_landing_heatmap(self) -> None:
        """Dessine une heatmap des arrêts moyens pour chaque scénario et case.

        Entrées:
            Aucune.

        Sortie:
            None: Chaque ligne représente un scénario et chaque colonne une case.
        """
        canvas = self.cross_heatmap
        canvas.delete("all")
        if self.result is None or not self.result.campaigns:
            self._draw_empty_chart(canvas, "Aucune donnée de fréquentation.")
            return
        width = max(360, canvas.winfo_width())
        height = max(180, canvas.winfo_height())
        campaigns = self.result.campaigns
        left, right, top, bottom = 105, 10, 28, 18
        usable_w = max(1, width - left - right)
        usable_h = max(1, height - top - bottom)
        cell_w = usable_w / 40
        cell_h = usable_h / max(1, len(campaigns))
        all_values = [
            item.average_landings_per_game
            for campaign in campaigns
            for item in campaign.space_summary
        ]
        maximum = max(all_values, default=1.0) or 1.0
        for case in range(0, 40, 5):
            x = left + (case + 0.5) * cell_w
            canvas.create_text(x, 12, text=str(case), font=("Arial", 7), fill="#53615A")
        for row, campaign in enumerate(campaigns):
            y0 = top + row * cell_h
            y1 = top + (row + 1) * cell_h - 1
            canvas.create_text(left - 6, (y0 + y1) / 2, text=campaign.scenario_name[:14], anchor="e", font=("Arial", 7, "bold"), fill="#344139")
            by_index = {item.index: item.average_landings_per_game for item in campaign.space_summary}
            for case in range(40):
                value = by_index.get(case, 0.0)
                ratio = min(1.0, max(0.0, value / maximum))
                color = self._temperature_heat_color(ratio)
                x0 = left + case * cell_w
                x1 = left + (case + 1) * cell_w - 1
                rect = canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="#FFFFFF")
                canvas.tag_bind(
                    rect,
                    "<Enter>",
                    lambda event, text=f"{campaign.scenario_name} • case {case} • {value:.2f} arrêts/partie": self._show_simple_canvas_tip(event, text),
                )
                canvas.tag_bind(rect, "<Leave>", self._hide_simple_canvas_tip)

    def _show_simple_canvas_tip(self, event: tk.Event, text: str) -> None:
        """Affiche un petit texte contextuel pour une cellule de heatmap.

        Entrées:
            event (tk.Event): Position du pointeur.
            text (str): Valeur complète de la cellule survolée.

        Sortie:
            None: Une info-bulle native temporaire est affichée près du pointeur.
        """
        self._hide_simple_canvas_tip(None)
        self.cross_tip = tk.Toplevel(self)
        self.cross_tip.overrideredirect(True)
        label = ttk.Label(self.cross_tip, text=text, padding=5, relief="solid")
        label.pack()
        self.cross_tip.geometry(f"+{event.x_root + 12}+{event.y_root + 12}")

    def _hide_simple_canvas_tip(self, event: tk.Event | None) -> None:
        """Ferme l'info-bulle légère de la heatmap si elle existe.

        Entrées:
            event (tk.Event | None): Événement de sortie facultatif.

        Sortie:
            None: Aucune info-bulle de heatmap ne reste ouverte.
        """
        tip = getattr(self, "cross_tip", None)
        if tip is not None:
            try:
                tip.destroy()
            except tk.TclError:
                pass
            self.cross_tip = None

    def _draw_cross_card_charts(self) -> None:
        """Compare Chance et Communauté entre scénarios sur deux métriques simples.

        Entrées:
            Aucune.

        Sortie:
            None: Tirages/partie et impact cash/tirage sont redessinés.
        """
        if self.result is None or not self.result.campaigns:
            self._draw_empty_chart(self.cross_card_frequency_chart, "Aucune carte analysée.")
            self._draw_empty_chart(self.cross_card_cash_chart, "Aucune carte analysée.")
            return
        labels = [campaign.scenario_name for campaign in self.result.campaigns]
        chance_freq: list[float] = []
        community_freq: list[float] = []
        chance_cash: list[float] = []
        community_cash: list[float] = []
        for campaign in self.result.campaigns:
            games = max(1, len(campaign.games))
            chance = [item for item in campaign.card_summary if item.deck == "chance"]
            community = [item for item in campaign.card_summary if item.deck == "community_chest"]
            chance_draws = sum(item.draws for item in chance)
            community_draws = sum(item.draws for item in community)
            chance_freq.append(chance_draws / games)
            community_freq.append(community_draws / games)
            chance_cash.append(
                sum(item.drawer_cash_delta for item in chance) / chance_draws
                if chance_draws else 0.0
            )
            community_cash.append(
                sum(item.drawer_cash_delta for item in community) / community_draws
                if community_draws else 0.0
            )
        self._draw_grouped_bar_chart(
            self.cross_card_frequency_chart,
            labels,
            (("Chance", chance_freq), ("Communauté", community_freq)),
        )
        self._draw_cross_signed_grouped_chart(
            self.cross_card_cash_chart,
            labels,
            (("Chance", chance_cash), ("Communauté", community_cash)),
            suffix=" $",
        )

    def _draw_cross_signed_grouped_chart(
        self,
        canvas: tk.Canvas,
        categories: list[str],
        series: tuple[tuple[str, list[float]], ...],
        suffix: str = "",
    ) -> None:
        """Dessine plusieurs séries signées côte à côte autour d'une ligne zéro.

        Entrées:
            canvas (tk.Canvas): Surface graphique cible.
            categories (list[str]): Scénarios comparés.
            series (tuple[tuple[str, list[float]], ...]): Séries Chance/Communauté.
            suffix (str): Unité ajoutée aux valeurs affichées.

        Sortie:
            None: Les gains et pertes restent visibles avec une légende par série.
        """
        canvas.delete("all")
        if not categories or not series:
            self._draw_empty_chart(canvas, "Pas de données.")
            return
        width = max(320, canvas.winfo_width())
        height = max(160, canvas.winfo_height())
        left, right, top, bottom = 38, 12, 24, 38
        usable_w = max(1.0, width - left - right)
        usable_h = max(1.0, height - top - bottom)
        values_all = [value for _, values in series for value in values]
        maximum = max(1.0, max(values_all, default=0.0))
        minimum = min(-1.0, min(values_all, default=0.0))
        span = maximum - minimum
        zero_y = top + usable_h * maximum / span
        canvas.create_line(left, zero_y, width - right, zero_y, fill="#78867D", width=2)
        slot = usable_w / max(1, len(categories))
        group_w = slot * 0.74
        bar_w = group_w / max(1, len(series))
        colors = (CARD_DECK_COLORS["chance"], CARD_DECK_COLORS["community_chest"])
        for cat_index, category in enumerate(categories):
            start = left + cat_index * slot + (slot - group_w) / 2
            for series_index, (_, values) in enumerate(series):
                value = values[cat_index] if cat_index < len(values) else 0.0
                x0 = start + series_index * bar_w + 1
                x1 = start + (series_index + 1) * bar_w - 1
                value_y = zero_y - usable_h * value / span
                canvas.create_rectangle(
                    x0,
                    min(zero_y, value_y),
                    x1,
                    max(zero_y, value_y),
                    fill=colors[series_index % len(colors)],
                    outline="#526159",
                )
            canvas.create_text(
                left + cat_index * slot + slot / 2,
                height - bottom + 13,
                text=category[:14],
                font=("Arial", 7),
                fill="#4D5A52",
            )
        for series_index, (name, _) in enumerate(series):
            x = left + 8 + series_index * 120
            canvas.create_rectangle(
                x,
                7,
                x + 10,
                15,
                fill=colors[series_index % len(colors)],
                outline="",
            )
            canvas.create_text(x + 14, 11, text=name, anchor="w", font=("Arial", 7), fill="#344139")
        canvas.create_text(left - 4, top + 5, text=f"{maximum:+.1f}{suffix}", anchor="e", font=("Arial", 7), fill="#53615A")
        canvas.create_text(left - 4, height - bottom - 2, text=f"{minimum:+.1f}{suffix}", anchor="e", font=("Arial", 7), fill="#53615A")

    def _build_games_tab(self) -> None:
        """Construit la table d'une ligne par partie simulée.

        Entrées:
            Aucune.

        Sortie:
            None: L'onglet permet d'inspecter les seeds et cas extrêmes.
        """
        tab = self.games_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        header = ttk.Frame(tab)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(0, weight=1)
        self.games_title = ttk.Label(
            header,
            text="Parties du scénario sélectionné",
            font=("Arial", 12, "bold"),
        )
        self.games_title.grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Trie visuellement les cas extrêmes via tours, loyer max, faillites ou seed.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w")

        columns = (
            "seed", "rounds", "actions", "winner", "status", "rent", "maxrent",
            "bankruptcies", "buildings", "jail", "cards", "purchases", "auctions",
            "mortgages", "potpeak", "potcollected",
        )
        self.games_tree = ttk.Treeview(
            tab,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        labels = {
            "seed": "Seed",
            "rounds": "Tours",
            "actions": "Actions",
            "winner": "1er / leader",
            "status": "État",
            "rent": "Loyers",
            "maxrent": "Loyer max",
            "bankruptcies": "Faillites",
            "buildings": "Bâtiments",
            "jail": "Prison",
            "cards": "Cartes",
            "purchases": "Achats",
            "auctions": "Enchères",
            "mortgages": "Hypothèques",
            "potpeak": "Pic cagnotte",
            "potcollected": "Cagnotte prise",
        }
        for key in columns:
            self.games_tree.heading(key, text=labels[key])
            self.games_tree.column(key, width=84, anchor="center")
        self.games_tree.column("seed", width=100)
        self.games_tree.column("winner", width=95)
        self.games_tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tab, orient="horizontal", command=self.games_tree.xview)
        self.games_tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=0, sticky="ew")
        self._register_sortable_tree(self.games_tree, labels)

    def _build_method_tab(self) -> None:
        """Construit l'explication transparente du protocole neutre.

        Entrées:
            Aucune.

        Sortie:
            None: La méthodologie sans stratégie est explicitée dans l'interface.
        """
        text = (
            "PROTOCOLE DU LABORATOIRE\n\n"
            "• Aucune stratégie et aucune IA.\n"
            "• Achat direct : tirage fixe à 50 % lorsque le bien est payable.\n"
            "• Enchères : budgets aléatoires reproductibles.\n"
            "• Loyer manuel : réclamer / renoncer à probabilité égale.\n"
            "• Construction : tirage aléatoire uniquement parmi les constructions légales.\n"
            "• Pas d'échanges spontanés entre joueurs.\n"
            "• Même série de seeds entre scénarios d'une comparaison.\n"
            "• Seed vide au lancement : génération aléatoire, puis affichage de la seed utilisée.\n"
            "• Tours max vide ou égal à 0 : pas de limite de tours ; seul un watchdog technique "
            "de 20 000 actions protège la machine en dernier recours.\n"
            "• Performance V21.7 : cache des groupes de couleur, contrôles de construction ciblés "
            "sur les biens possédés et exécution multi-processus. Le mode Auto choisit jusqu'à "
            "8 processus selon les CPU disponibles et le volume de la campagne.\n"
            "• Analyse V21.8 : comparaison croisée des 40 cases, heatmap multi-scénarios bleu foncé → rouge foncé, "
            "comparaison Chance/Communauté, rapports JSON rechargeables et HTML autonome.\n"
            "• Partie coupée par un garde-fou : une 1re place est attribuée au leader patrimoine/cash, "
            "mais la partie reste marquée comme tronquée.\n"
            "• P90 : 90 % des parties ont une durée inférieure ou égale à cette valeur.\n\n"
            "Les statistiques servent à mesurer les règles et le plateau, pas à évaluer une "
            "façon optimale de jouer. Les écarts entre sièges doivent notamment être interprétés "
            "comme du bruit ou un possible biais structurel à investiguer, jamais comme une stratégie."
        )
        label = ttk.Label(
            self.method_tab,
            text=text,
            justify="left",
            wraplength=950,
        )
        label.pack(anchor="nw")

    def _read_config(self) -> SimulationConfig:
        """Transforme les champs en configuration et résout une éventuelle seed vide.

        Entrées:
            Aucune.

        Sortie:
            SimulationConfig: Configuration prête à lancer avec seed effective.

        Lève:
            ValueError: Si un champ numérique obligatoire est invalide.
        """
        try:
            games = int(self.games_var.get())
            players = int(self.players_var.get())
            rounds_text = self.max_rounds_var.get().strip()
            rounds = 0 if rounds_text == "" else int(rounds_text)
        except ValueError as error:
            raise ValueError(
                "Parties, joueurs et tours max doivent être des nombres entiers ; "
                "laisse Tours max vide ou mets 0 pour le mode illimité."
            ) from error

        seed = resolve_base_seed(self.seed_var.get())
        workers_text = self.workers_var.get().strip()
        workers = 0 if workers_text.casefold() == "auto" else int(workers_text)
        config = SimulationConfig(
            games_per_scenario=games,
            player_count=players,
            max_rounds=rounds,
            base_seed=seed,
            parallel_workers=workers,
        )
        config.validate()
        self.last_used_seed = seed
        self.seed_var.set(str(seed))
        return config

    def _refresh_scenarios(self) -> None:
        """Recharge le tableau des scénarios depuis la liste interne.

        Entrées:
            Aucune.

        Sortie:
            None: Une ligne est affichée par scénario.
        """
        for item in self.scenario_tree.get_children():
            self.scenario_tree.delete(item)
        for index, scenario in enumerate(self.scenarios):
            self.scenario_tree.insert(
                "",
                "end",
                iid=str(index),
                text=scenario.name,
                values=(scenario.options.summary(), scenario.board_config.summary()),
            )

    def _unique_name(self, base: str) -> str:
        """Produit un nom de scénario non utilisé dans la liste courante.

        Entrées:
            base (str): Nom souhaité.

        Sortie:
            str: Nom original ou suffixé par un numéro.
        """
        existing = {scenario.name for scenario in self.scenarios}
        if base not in existing:
            return base
        suffix = 2
        while f"{base} {suffix}" in existing:
            suffix += 1
        return f"{base} {suffix}"

    def _add_standard(self) -> None:
        """Ajoute une nouvelle copie du scénario classique.

        Entrées:
            Aucune.

        Sortie:
            None: La liste des scénarios est actualisée.
        """
        scenario = SimulationScenario.standard()
        scenario.name = self._unique_name(scenario.name)
        self.scenarios.append(scenario)
        self._refresh_scenarios()

    def _import_pack(self) -> None:
        """Importe un pack complet comme scénario de comparaison.

        Entrées:
            Aucune.

        Sortie:
            None: Le pack valide est ajouté à la liste.
        """
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer un pack complet",
            filetypes=(("Pack JSON", "*.json"), ("Tous les fichiers", "*.*")),
        )
        if not path:
            return
        try:
            pack = load_profile_pack(path)
        except ProfilePackError as error:
            messagebox.showerror("Pack invalide", str(error), parent=self)
            return
        scenario = SimulationScenario.from_profile_pack(pack)
        scenario.name = self._unique_name(scenario.name)
        self.scenarios.append(scenario)
        self._refresh_scenarios()

    def _remove_selected(self) -> None:
        """Retire le scénario sélectionné de la comparaison.

        Entrées:
            Aucune.

        Sortie:
            None: La liste est raccourcie d'un scénario au maximum.
        """
        selection = self.scenario_tree.selection()
        if not selection:
            return
        index = int(selection[0])
        if 0 <= index < len(self.scenarios):
            self.scenarios.pop(index)
            self._refresh_scenarios()

    def _run(self) -> None:
        """Lance toutes les campagnes et remplit les analyses enrichies.

        Entrées:
            Aucune.

        Sortie:
            None: Le rapport courant est remplacé par le résultat du runner.
        """
        if self.running:
            return
        try:
            config = self._read_config()
            if not self.scenarios:
                raise ValueError("Ajoutez au moins un scénario.")
        except ValueError as error:
            messagebox.showwarning("Simulation invalide", str(error), parent=self)
            return

        self.running = True
        self.run_button.state(["disabled"])
        self.progress_var.set(0.0)
        total = len(self.scenarios) * config.games_per_scenario

        started_at = time.perf_counter()
        effective_workers = 1
        try:
            runner = SimulationRunner(progress_callback=self._progress)
            self.result = runner.run(
                [scenario.clone() for scenario in self.scenarios],
                config,
            )
            effective_workers = runner.last_worker_count
        except Exception as error:
            messagebox.showerror(
                "Erreur de simulation",
                f"La campagne a été interrompue : {error}",
                parent=self,
            )
            self.result = None
        finally:
            self.running = False
            self.run_button.state(["!disabled"])

        if self.result is None:
            self.progress_label.configure(text="Simulation interrompue.")
            return

        elapsed = time.perf_counter() - started_at
        self.progress_var.set(100.0)
        self.progress_label.configure(
            text=(
                f"Terminé : {total} parties en {elapsed:.2f} s • "
                f"{effective_workers} processus • seed : {config.base_seed}."
            )
        )
        self._refresh_results()
        for button in (
            self.export_json_button,
            self.export_csv_button,
            self.export_summary_button,
            self.export_board_button,
            self.export_development_button,
            self.export_cards_button,
            self.export_html_button,
        ):
            button.state(["!disabled"])

    def _progress(self, completed: int, total: int, scenario_name: str) -> None:
        """Met à jour la barre de progression pendant le calcul synchrone.

        Entrées:
            completed (int): Nombre de parties terminées.
            total (int): Nombre total prévu.
            scenario_name (str): Scénario actuellement simulé.

        Sortie:
            None: La progression visuelle est actualisée.
        """
        percent = 100.0 * completed / max(1, total)
        self.progress_var.set(percent)
        self.progress_label.configure(
            text=f"{scenario_name} — {completed}/{total} parties"
        )
        now = time.monotonic()
        if completed == total or now - self._last_progress_refresh >= 0.10:
            self._last_progress_refresh = now
            self.update()

    def _refresh_results(self) -> None:
        """Recharge synthèse, détails, parties et graphiques du dernier rapport.

        Entrées:
            Aucune.

        Sortie:
            None: Toutes les vues sont synchronisées sur le rapport courant.
        """
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        if self.result is None:
            self._clear_detail_tables()
            self._draw_all_charts()
            return

        for index, campaign in enumerate(self.result.campaigns):
            self.result_tree.insert(
                "",
                "end",
                iid=str(index),
                text=campaign.scenario_name,
                values=(
                    len(campaign.games),
                    f"{campaign.finish_rate:.1f}",
                    f"{campaign.average_rounds:.1f}",
                    f"{campaign.median_rounds:.1f}",
                    f"{campaign.round_percentile(90):.1f}",
                    f"{campaign.round_stddev:.1f}",
                    f"{campaign.average_actions:.1f}",
                    f"{campaign.average_rent:.0f} $",
                    f"{campaign.maximum_single_rent} $",
                    f"{campaign.average_bankruptcies:.2f}",
                ),
            )

        self._refresh_tree_sorter(self.result_tree)

        if self.result.campaigns:
            self.selected_campaign_index = 0
            self.result_tree.selection_set("0")
            self.result_tree.focus("0")
            self._show_campaign_details(0)
        self._draw_all_charts()
        self._refresh_cross_analysis()

    def _result_selected(self, event: tk.Event) -> None:
        """Synchronise tous les onglets avec le scénario sélectionné.

        Entrées:
            event (tk.Event): Événement Treeview.

        Sortie:
            None: Les détails et graphiques du scénario sont rafraîchis.
        """
        selection = self.result_tree.selection()
        if not selection:
            return
        self._show_campaign_details(int(selection[0]))

    def _clear_detail_tables(self) -> None:
        """Vide les tableaux dépendant d'une campagne sélectionnée.

        Entrées:
            Aucune.

        Sortie:
            None: Propriétés, sièges et parties deviennent vides.
        """
        for tree in (
            self.property_tree,
            self.player_tree,
            self.games_tree,
            self.case_tree,
            self.card_tree,
        ):
            for item in tree.get_children():
                tree.delete(item)

    def _show_campaign_details(self, index: int) -> None:
        """Affiche toutes les statistiques du scénario demandé.

        Entrées:
            index (int): Index de campagne dans le rapport.

        Sortie:
            None: Tableaux, KPIs, histogramme et parties sont réécrits.
        """
        self._clear_detail_tables()
        if self.result is None or not 0 <= index < len(self.result.campaigns):
            return

        self.selected_campaign_index = index
        campaign = self.result.campaigns[index]
        self.detail_title.configure(text=campaign.scenario_name)
        self.detail_kpi.configure(
            text=(
                f"Tours : moyenne {campaign.average_rounds:.1f}, médiane {campaign.median_rounds:.1f}, "
                f"P10 {campaign.round_percentile(10):.1f}, P90 {campaign.round_percentile(90):.1f} (90 % ≤), "
                f"σ {campaign.round_stddev:.1f} • fin {campaign.finish_rate:.1f} % • "
                f"cutoffs tours {campaign.round_limit_games}, watchdog {campaign.action_watchdog_games} • "
                f"cartes {campaign.average_cards_drawn:.1f}/partie • achats {campaign.average_purchases:.1f} • "
                f"enchères {campaign.average_auctions_won:.1f} • hypothèques {campaign.average_mortgages:.1f}"
            )
        )
        self.games_title.configure(
            text=f"Parties — {campaign.scenario_name} ({len(campaign.games)} seeds)"
        )

        for row, item in enumerate(campaign.property_summary):
            self.property_tree.insert(
                "",
                "end",
                iid=str(row),
                text=item.name,
                values=(
                    f"{item.average_rent_per_game:.1f}",
                    f"{item.average_rent_per_event:.1f}",
                    item.total_rent,
                    item.total_rent_events,
                    item.games_with_rent,
                    item.biggest_rent,
                ),
            )

        for row, item in enumerate(campaign.player_summary):
            self.player_tree.insert(
                "",
                "end",
                iid=str(row),
                text=item.name,
                values=(
                    f"{item.win_rate:.1f}",
                    f"{item.finished_win_rate:.1f}",
                    item.cutoff_leads,
                    f"{item.bankruptcy_rate:.1f}",
                    f"{item.average_final_net_worth:.0f}",
                    f"{item.average_final_cash:.0f}",
                    f"{item.average_final_properties:.1f}",
                    f"{item.average_rent_received:.0f}",
                    f"{item.average_rent_paid:.0f}",
                    f"{item.average_jail_visits:.1f}",
                ),
            )

        sorted_games = sorted(
            campaign.games,
            key=lambda item: (item.rounds, item.actions, item.seed),
            reverse=True,
        )
        for row, game in enumerate(sorted_games):
            if not game.truncated:
                status = "finie"
            else:
                status = {
                    "round_limit": "limite tours",
                    "action_watchdog": "watchdog actions",
                }.get(game.stop_reason, "cutoff")
                status += " (leader)"
            self.games_tree.insert(
                "",
                "end",
                iid=str(row),
                values=(
                    game.seed,
                    game.rounds,
                    game.actions,
                    game.winner_name or "—",
                    status,
                    game.rent_transferred,
                    game.biggest_rent,
                    game.bankruptcies,
                    game.buildings_built,
                    game.jail_visits,
                    game.cards_drawn,
                    game.purchases,
                    game.auctions_won,
                    game.mortgages,
                    game.free_parking_peak,
                    game.free_parking_collected,
                ),
            )

        self._refresh_tree_sorter(self.property_tree)
        self._refresh_tree_sorter(self.player_tree)
        self._refresh_tree_sorter(self.games_tree)
        self._refresh_board_stats(campaign)
        self._refresh_card_stats(campaign)
        self._draw_detail_charts()

    def _redraw_all_charts_event(self, event: tk.Event) -> None:
        """Redessine les graphiques comparatifs après redimensionnement.

        Entrées:
            event (tk.Event): Événement Configure Tkinter.

        Sortie:
            None: Les quatre graphiques sont recalculés.
        """
        self._draw_all_charts()

    def _redraw_detail_charts_event(self, event: tk.Event) -> None:
        """Redessine les graphiques détaillés après redimensionnement.

        Entrées:
            event (tk.Event): Événement Configure Tkinter.

        Sortie:
            None: Histogramme et graphique par siège sont recalculés.
        """
        self._draw_detail_charts()

    def _player_metric_changed(self, event: tk.Event) -> None:
        """Redessine le graphique de sièges après changement de métrique.

        Entrées:
            event (tk.Event): Événement de sélection de la combobox.

        Sortie:
            None: Le canvas des sièges adopte la nouvelle mesure.
        """
        self._draw_player_chart()

    def _development_property_changed(self, event: tk.Event) -> None:
        """Redessine le rendement par niveau après choix d'un terrain.

        Entrées:
            event (tk.Event): Événement de combobox.

        Sortie:
            None: Le graphique de développement est actualisé.
        """
        self._draw_development_chart()

    def _redraw_board_charts_event(self, event: tk.Event) -> None:
        """Redessine les graphiques de cases après redimensionnement.

        Entrées:
            event (tk.Event): Événement Configure Tkinter.

        Sortie:
            None: Les graphiques de l'onglet Cases sont recalculés.
        """
        self._draw_board_charts()

    def _refresh_board_stats(self, campaign: SimulationCampaignResult) -> None:
        """Remplit tableau et sélecteur de développement pour une campagne.

        Entrées:
            campaign (SimulationCampaignResult): Scénario sélectionné.

        Sortie:
            None: Les données exactes et les choix de terrains sont synchronisés.
        """
        self.board_stats_title.configure(text=f"Cases & rendement — {campaign.scenario_name}")
        self.board_stats_kpi.configure(
            text=(
                f"Arrêts enregistrés : {campaign.average_recorded_landings:.1f}/partie • "
                f"case la plus fréquentée : {campaign.most_landed_space} • "
                f"ROI global des biens : {campaign.global_property_roi_percent:.1f} % • "
                f"meilleur ROI : {campaign.best_roi_property}"
            )
        )
        investment_by_index = {item.index: item for item in campaign.property_investment_summary}
        for item in self.case_tree.get_children():
            self.case_tree.delete(item)
        for space in campaign.space_summary:
            inv = investment_by_index.get(space.index)
            self.case_tree.insert(
                "",
                "end",
                iid=str(space.index),
                text=f"{space.index:02d} — {space.name}",
                values=(
                    f"{space.average_landings_per_game:.2f}",
                    f"{space.landing_share_percent:.2f}",
                    "—" if inv is None else f"{inv.total_investment} $",
                    "—" if inv is None else f"{inv.total_rent} $",
                    "—" if inv is None else f"{inv.roi_percent:.1f}",
                    "—" if inv is None else f"{inv.net_return} $",
                    "—" if inv is None else f"{inv.rent_per_landing:.1f} $",
                ),
            )

        self._refresh_tree_sorter(self.case_tree)

        property_choices = []
        seen: set[int] = set()
        for item in campaign.property_development_summary:
            if item.property_index not in seen:
                seen.add(item.property_index)
                property_choices.append(
                    f"{item.property_index:02d} — {item.property_name}"
                )
        self.development_property_combo.configure(values=property_choices)
        if property_choices:
            current = self.development_property_var.get()
            if current not in property_choices:
                self.development_property_var.set(property_choices[0])
        else:
            self.development_property_var.set("")
        self._draw_board_charts()


    def _card_deck_changed(self, event: tk.Event) -> None:
        """Actualise les cartes après changement de filtre de paquet.

        Entrées:
            event (tk.Event): Événement de sélection de la combobox.

        Sortie:
            None: Tableau et graphiques utilisent le nouveau paquet.
        """
        if self.result is None:
            return
        if not 0 <= self.selected_campaign_index < len(self.result.campaigns):
            return
        self._refresh_card_stats(self.result.campaigns[self.selected_campaign_index])


    def _redraw_card_charts_event(self, event: tk.Event) -> None:
        """Redessine les graphiques de cartes après redimensionnement.

        Entrées:
            event (tk.Event): Événement Configure Tkinter.

        Sortie:
            None: Les quatre graphiques sont recalculés.
        """
        self._draw_card_charts()


    def _filtered_card_items(self, campaign: SimulationCampaignResult):
        """Retourne les cartes correspondant au filtre actuellement choisi.

        Entrées:
            campaign (SimulationCampaignResult): Campagne sélectionnée.

        Sortie:
            list: Cartes triées par fréquence décroissante.
        """
        deck = CARD_DECK_LABELS.get(self.card_deck_var.get(), "")
        items = campaign.card_summary
        if deck:
            items = [item for item in items if item.deck == deck]
        return sorted(items, key=lambda item: (item.draws, item.card_text), reverse=True)


    def _card_label(self, text: str, fallback: str) -> str:
        """Produit un libellé court pour l'axe horizontal des cartes.

        Entrées:
            text (str): Texte complet de la carte.
            fallback (str): Type de carte utilisé si le texte est vide.

        Sortie:
            str: Libellé compact de douze caractères environ.
        """
        cleaned = " ".join(text.split()) or fallback
        return cleaned if len(cleaned) <= 14 else cleaned[:12] + "…"


    def _refresh_card_stats(self, campaign: SimulationCampaignResult) -> None:
        """Remplit l'onglet cartes pour le scénario sélectionné.

        Entrées:
            campaign (SimulationCampaignResult): Campagne dont les cartes sont analysées.

        Sortie:
            None: KPIs, tableau et graphiques sont synchronisés.
        """
        self.cards_title.configure(text=f"Cartes — {campaign.scenario_name}")
        total_draws = campaign.chance_draws + campaign.community_draws
        games = max(1, len(campaign.games))
        most_drawn = max(campaign.card_summary, key=lambda item: item.draws, default=None)
        most_positive = max(
            campaign.card_summary,
            key=lambda item: item.average_drawer_cash_delta,
            default=None,
        )
        most_negative = min(
            campaign.card_summary,
            key=lambda item: item.average_drawer_cash_delta,
            default=None,
        )
        positive_text = (
            "—" if most_positive is None
            else f"{self._card_label(most_positive.card_text, most_positive.card_type)} "
            f"({most_positive.average_drawer_cash_delta:+.1f} $/tirage)"
        )
        negative_text = (
            "—" if most_negative is None
            else f"{self._card_label(most_negative.card_text, most_negative.card_type)} "
            f"({most_negative.average_drawer_cash_delta:+.1f} $/tirage)"
        )
        most_text = (
            "—" if most_drawn is None
            else f"{self._card_label(most_drawn.card_text, most_drawn.card_type)} "
            f"({most_drawn.draws} tirages)"
        )
        self.cards_kpi.configure(
            text=(
                f"Chance : {campaign.chance_draws / games:.2f}/partie • "
                f"Communauté : {campaign.community_draws / games:.2f}/partie • "
                f"total : {total_draws / games:.2f}/partie • "
                f"impact cash moyen : {campaign.average_card_cash_impact:+.1f} $/tirage • "
                f"cagnotte cartes : {campaign.total_card_pot_contribution:+d} $ • "
                f"plus tirée : {most_text} • meilleure : {positive_text} • pire : {negative_text}"
            )
        )

        for item in self.card_tree.get_children():
            self.card_tree.delete(item)
        for row, item in enumerate(self._filtered_card_items(campaign)):
            deck_label = "Chance" if item.deck == "chance" else "Communauté"
            self.card_tree.insert(
                "",
                "end",
                iid=str(row),
                text=item.card_text or item.card_type,
                values=(
                    deck_label,
                    item.card_type,
                    item.draws,
                    f"{item.average_draws_per_game:.2f}",
                    f"{item.deck_share_percent:.1f}",
                    f"{item.average_drawer_cash_delta:+.1f} $",
                    f"{item.drawer_cash_delta:+d} $",
                    f"{item.other_players_cash_delta:+d} $",
                    f"{item.free_parking_pot_delta:+d} $",
                    f"{item.movement_rate:.1f}",
                    f"{item.jail_rate:.1f}",
                    f"{item.get_out_rate:.1f}",
                    f"+{item.biggest_gain} $",
                    f"-{item.biggest_loss} $",
                ),
            )
        self._refresh_tree_sorter(self.card_tree)
        self._draw_card_charts()


    def _draw_card_charts(self) -> None:
        """Dessine fréquence, impact financier, cagnotte et effets des cartes.

        Entrées:
            Aucune.

        Sortie:
            None: Les quatre canvas du nouvel onglet sont actualisés.
        """
        if self.result is None or not 0 <= self.selected_campaign_index < len(self.result.campaigns):
            for canvas in (
                self.card_frequency_chart,
                self.card_cash_chart,
                self.card_pot_chart,
                self.card_effect_chart,
            ):
                self._draw_empty_chart(canvas, "Lancez une campagne pour analyser les cartes.")
            return

        campaign = self.result.campaigns[self.selected_campaign_index]
        items = self._filtered_card_items(campaign)
        if not items:
            for canvas in (
                self.card_frequency_chart,
                self.card_cash_chart,
                self.card_pot_chart,
                self.card_effect_chart,
            ):
                self._draw_empty_chart(canvas, "Aucun tirage pour ce paquet.")
            return

        labels = [self._card_label(item.card_text, item.card_type) for item in items]
        colors = [CARD_DECK_COLORS.get(item.deck, "#AEB7B1") for item in items]
        self._draw_grouped_bar_chart(
            self.card_frequency_chart,
            labels,
            (("Tirages", [item.average_draws_per_game for item in items]),),
            category_colors=colors,
        )
        self._draw_signed_bar_chart(
            self.card_cash_chart,
            labels,
            [item.average_drawer_cash_delta for item in items],
            colors,
            suffix=" $",
        )
        self._draw_signed_bar_chart(
            self.card_pot_chart,
            labels,
            [float(item.free_parking_pot_delta) for item in items],
            colors,
            suffix=" $",
        )
        self._draw_grouped_bar_chart(
            self.card_effect_chart,
            labels,
            (
                ("Déplacement", [item.movement_rate for item in items]),
                ("Prison", [item.jail_rate for item in items]),
                ("Sortie prison", [item.get_out_rate for item in items]),
            ),
            suffix=" %",
            fixed_max=100.0,
        )

    def _selected_scenario(self):
        """Retourne le scénario correspondant à la campagne actuellement affichée.

        Entrées:
            Aucune.

        Sortie:
            SimulationScenario | None: Scénario sélectionné, sinon ``None``.
        """
        if not 0 <= self.selected_campaign_index < len(self.scenarios):
            return None
        return self.scenarios[self.selected_campaign_index]

    def _space_chart_color(self, index: int) -> str:
        """Retourne la couleur visuelle de la case utilisée dans les graphiques.

        Entrées:
            index (int): Position de la case sur le plateau du scénario courant.

        Sortie:
            str: Couleur hexadécimale cohérente avec le plateau.
        """
        scenario = self._selected_scenario()
        if scenario is None or not 0 <= index < len(scenario.board_config.spaces):
            return "#AEB7B1"
        space = scenario.board_config.spaces[index]
        if space.space_type == "property":
            return CASE_PROPERTY_COLORS.get(
                space.color_group.strip().casefold(),
                CASE_TYPE_COLORS["property"],
            )
        return CASE_TYPE_COLORS.get(space.space_type, "#AEB7B1")

    def _space_chart_colors(self, indexes: list[int]) -> list[str]:
        """Construit la palette des cases dans le même ordre que les catégories.

        Entrées:
            indexes (list[int]): Positions des cases représentées par les barres.

        Sortie:
            list[str]: Une couleur de plateau par index.
        """
        return [self._space_chart_color(index) for index in indexes]

    def _show_bar_hover(
        self,
        event: tk.Event,
        payload: tuple[int, str, str],
    ) -> None:
        """Affiche la fiche de case correspondant à une barre survolée.

        Entrées:
            event (tk.Event): Événement Canvas contenant les coordonnées écran.
            payload (tuple[int, str, str]): Index de case, libellé de métrique et valeur.

        Sortie:
            None: La fiche flottante apparaît près du pointeur.
        """
        scenario = self._selected_scenario()
        if scenario is None:
            return
        index, metric_label, metric_value = payload
        self.bar_hover_card.show(
            scenario,
            index,
            metric_label,
            metric_value,
            int(event.x_root),
            int(event.y_root),
        )

    def _move_bar_hover(self, event: tk.Event) -> None:
        """Déplace la fiche de case pendant le déplacement sur une même barre.

        Entrées:
            event (tk.Event): Mouvement Canvas courant.

        Sortie:
            None: La fiche suit le pointeur sans le recouvrir.
        """
        self.bar_hover_card.move(int(event.x_root), int(event.y_root))

    def _hide_bar_hover(self, event: tk.Event | None = None) -> None:
        """Masque la fiche de case à la sortie d'une barre ou lors d'un redessin.

        Entrées:
            event (tk.Event | None): Événement de sortie facultatif.

        Sortie:
            None: La fiche flottante disparaît.
        """
        self.bar_hover_card.hide()

    def _bind_bar_hover(
        self,
        canvas: tk.Canvas,
        item_id: int,
        payload: tuple[int, str, str],
    ) -> None:
        """Associe entrée, mouvement et sortie d'une barre à sa fiche détaillée.

        Entrées:
            canvas (tk.Canvas): Graphique propriétaire de la barre.
            item_id (int): Identifiant Canvas du rectangle interactif.
            payload (tuple[int, str, str]): Données de case affichées au survol.

        Sortie:
            None: La barre devient interactive sans modifier le calcul statistique.
        """
        canvas.tag_bind(
            item_id,
            "<Enter>",
            lambda event, data=payload: self._show_bar_hover(event, data),
        )
        canvas.tag_bind(item_id, "<Motion>", self._move_bar_hover)
        canvas.tag_bind(item_id, "<Leave>", self._hide_bar_hover)

    def _draw_board_charts(self) -> None:
        """Dessine fréquentation, ROI, rendement par arrêt et développement.

        Entrées:
            Aucune.

        Sortie:
            None: Les quatre graphiques de cases sont actualisés.
        """
        self.bar_hover_card.hide()
        if self.result is None or not 0 <= self.selected_campaign_index < len(self.result.campaigns):
            for canvas in (self.landings_chart, self.roi_chart, self.rent_per_stop_chart, self.development_chart):
                self._draw_empty_chart(canvas, "Aucun scénario sélectionné.")
            return
        campaign = self.result.campaigns[self.selected_campaign_index]
        space_indexes = [item.index for item in campaign.space_summary]
        landing_values = [item.average_landings_per_game for item in campaign.space_summary]
        self._draw_grouped_bar_chart(
            self.landings_chart,
            [str(index) for index in space_indexes],
            (("Arrêts/partie", landing_values),),
            category_colors=self._space_chart_colors(space_indexes),
            hover_payloads=[
                (index, "Arrêts moyens / partie", f"{value:.2f}")
                for index, value in zip(space_indexes, landing_values)
            ],
        )
        investments = sorted(campaign.property_investment_summary, key=lambda item: item.index)
        investment_indexes = [item.index for item in investments]
        investment_colors = self._space_chart_colors(investment_indexes)
        roi_values = [item.roi_percent for item in investments]
        rent_stop_values = [item.rent_per_landing for item in investments]
        self._draw_grouped_bar_chart(
            self.roi_chart,
            [str(index) for index in investment_indexes],
            (("ROI", roi_values),),
            suffix=" %",
            category_colors=investment_colors,
            hover_payloads=[
                (index, "ROI brut", f"{value:.1f} %")
                for index, value in zip(investment_indexes, roi_values)
            ],
        )
        self._draw_grouped_bar_chart(
            self.rent_per_stop_chart,
            [str(index) for index in investment_indexes],
            (("$/arrêt", rent_stop_values),),
            suffix=" $",
            category_colors=investment_colors,
            hover_payloads=[
                (index, "Loyer généré / arrêt", f"{value:.1f} $")
                for index, value in zip(investment_indexes, rent_stop_values)
            ],
        )
        self._draw_development_chart()

    def _draw_development_chart(self) -> None:
        """Dessine le ROI d'un terrain selon son nombre de maisons ou hôtel.

        Entrées:
            Aucune.

        Sortie:
            None: Le canvas de développement affiche jusqu'à six niveaux.
        """
        if self.result is None or not 0 <= self.selected_campaign_index < len(self.result.campaigns):
            self._draw_empty_chart(self.development_chart, "Aucun scénario sélectionné.")
            return
        text = self.development_property_var.get().strip()
        if not text:
            self._draw_empty_chart(self.development_chart, "Aucun terrain construit dans cette campagne.")
            return
        try:
            index = int(text.split("—", 1)[0].strip())
        except ValueError:
            self._draw_empty_chart(self.development_chart, "Terrain invalide.")
            return
        campaign = self.result.campaigns[self.selected_campaign_index]
        items = [
            item for item in campaign.property_development_summary
            if item.property_index == index
        ]
        items.sort(key=lambda item: item.level)
        if not items:
            self._draw_empty_chart(self.development_chart, "Aucune donnée de construction.")
            return
        property_color = self._space_chart_color(index)
        development_values = [item.roi_percent for item in items]
        self._draw_grouped_bar_chart(
            self.development_chart,
            [item.level_label for item in items],
            (("ROI", development_values),),
            suffix=" %",
            category_colors=[property_color] * len(items),
            hover_payloads=[
                (index, f"ROI • {item.level_label}", f"{item.roi_percent:.1f} %")
                for item in items
            ],
        )

    def _draw_all_charts(self) -> None:
        """Dessine les quatre comparaisons principales entre scénarios.

        Entrées:
            Aucune.

        Sortie:
            None: Tous les canvas comparatifs sont actualisés.
        """
        if self.result is None or not self.result.campaigns:
            for canvas in (
                self.duration_chart,
                self.finish_chart,
                self.rent_chart,
                self.activity_chart,
            ):
                self._draw_empty_chart(canvas, "Lancez une campagne pour afficher ce graphique.")
            return

        campaigns = self.result.campaigns
        labels = [campaign.scenario_name for campaign in campaigns]
        self._draw_grouped_bar_chart(
            self.duration_chart,
            labels,
            (
                ("Moyenne", [campaign.average_rounds for campaign in campaigns]),
                ("P90", [campaign.round_percentile(90) for campaign in campaigns]),
            ),
            suffix=" tours",
        )
        self._draw_grouped_bar_chart(
            self.finish_chart,
            labels,
            (("Fin", [campaign.finish_rate for campaign in campaigns]),),
            suffix=" %",
            fixed_max=100.0,
        )
        self._draw_grouped_bar_chart(
            self.rent_chart,
            labels,
            (
                ("Moyenne", [campaign.average_rent for campaign in campaigns]),
                ("Maximum", [campaign.maximum_single_rent for campaign in campaigns]),
            ),
            suffix=" $",
        )
        self._draw_grouped_bar_chart(
            self.activity_chart,
            labels,
            (
                ("Bâtiments", [campaign.average_buildings for campaign in campaigns]),
                ("Prison", [campaign.average_jail_visits for campaign in campaigns]),
                ("Cartes", [campaign.average_cards_drawn for campaign in campaigns]),
                ("Hypothèques", [campaign.average_mortgages for campaign in campaigns]),
            ),
        )

    def _draw_detail_charts(self) -> None:
        """Dessine histogramme de durée et profil statistique des sièges.

        Entrées:
            Aucune.

        Sortie:
            None: Les deux graphiques du scénario sélectionné sont actualisés.
        """
        if self.result is None or not 0 <= self.selected_campaign_index < len(self.result.campaigns):
            self._draw_empty_chart(self.histogram_chart, "Aucun scénario sélectionné.")
            self._draw_empty_chart(self.player_chart, "Aucun scénario sélectionné.")
            return
        campaign = self.result.campaigns[self.selected_campaign_index]
        histogram = campaign.duration_histogram()
        self._draw_grouped_bar_chart(
            self.histogram_chart,
            [label for label, _ in histogram],
            (("Parties", [count for _, count in histogram]),),
            suffix="",
        )
        self._draw_player_chart()
        self._draw_board_charts()

    def _draw_player_chart(self) -> None:
        """Dessine la métrique choisie pour chaque siège neutre.

        Entrées:
            Aucune.

        Sortie:
            None: Un histogramme par siège est affiché.
        """
        if self.result is None or not 0 <= self.selected_campaign_index < len(self.result.campaigns):
            self._draw_empty_chart(self.player_chart, "Aucun scénario sélectionné.")
            return
        campaign = self.result.campaigns[self.selected_campaign_index]
        metric = self.player_metric_var.get()
        accessors: dict[str, tuple[Callable[[PlayerSimulationSummary], float], str, float | None]] = {
            "1re place (%)": (lambda item: item.win_rate, " %", 100.0),
            "Victoire finie (%)": (lambda item: item.finished_win_rate, " %", 100.0),
            "Faillite (%)": (lambda item: item.bankruptcy_rate, " %", 100.0),
            "Patrimoine final": (lambda item: item.average_final_net_worth, " $", None),
            "Cash final": (lambda item: item.average_final_cash, " $", None),
            "Biens finaux": (lambda item: item.average_final_properties, "", None),
            "Loyers reçus": (lambda item: item.average_rent_received, " $", None),
            "Loyers payés": (lambda item: item.average_rent_paid, " $", None),
            "Prison": (lambda item: item.average_jail_visits, "", None),
        }
        accessor, suffix, fixed_max = accessors.get(metric, accessors["1re place (%)"])
        self._draw_grouped_bar_chart(
            self.player_chart,
            [item.name for item in campaign.player_summary],
            ((metric, [accessor(item) for item in campaign.player_summary]),),
            suffix=suffix,
            fixed_max=fixed_max,
        )

    def _draw_empty_chart(self, canvas: tk.Canvas, message: str) -> None:
        """Affiche un message centré lorsqu'un graphique n'a pas encore de données.

        Entrées:
            canvas (tk.Canvas): Zone à vider.
            message (str): Texte explicatif.

        Sortie:
            None: Le canvas contient uniquement le message.
        """
        canvas.delete("all")
        width = max(260, canvas.winfo_width())
        height = max(130, canvas.winfo_height())
        canvas.create_text(
            width / 2,
            height / 2,
            text=message,
            fill="#6E7A83",
            font=("Arial", 9),
            width=width - 30,
        )


    def _draw_signed_bar_chart(
        self,
        canvas: tk.Canvas,
        categories: list[str],
        values: list[float],
        colors: list[str],
        suffix: str = "",
    ) -> None:
        """Dessine un histogramme acceptant des valeurs positives et négatives.

        Entrées:
            canvas (tk.Canvas): Zone graphique cible.
            categories (list[str]): Libellés des cartes.
            values (list[float]): Valeurs signées à représenter.
            colors (list[str]): Couleur de paquet de chaque barre.
            suffix (str): Unité affichée dans les valeurs.

        Sortie:
            None: Une ligne zéro sépare gains et pertes.
        """
        canvas.delete("all")
        width = max(280, canvas.winfo_width())
        height = max(150, canvas.winfo_height())
        if not categories or not values:
            self._draw_empty_chart(canvas, "Pas de données.")
            return

        margin_left = 34
        margin_right = 12
        margin_top = 18
        margin_bottom = 35
        usable_w = max(1.0, width - margin_left - margin_right)
        usable_h = max(1.0, height - margin_top - margin_bottom)
        maximum = max(1.0, max(values, default=0.0))
        minimum = min(-1.0, min(values, default=0.0))
        span = maximum - minimum
        zero_y = margin_top + usable_h * maximum / span
        slot = usable_w / max(1, len(categories))
        bar_width = slot * 0.62

        canvas.create_line(
            margin_left,
            zero_y,
            width - margin_right,
            zero_y,
            fill="#78867D",
            width=2,
        )

        for index, category in enumerate(categories):
            value = values[index] if index < len(values) else 0.0
            center = margin_left + slot * index + slot / 2
            x0 = center - bar_width / 2
            x1 = center + bar_width / 2
            value_y = zero_y - usable_h * value / span
            y0 = min(zero_y, value_y)
            y1 = max(zero_y, value_y)
            canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=colors[index] if index < len(colors) else "#AEB7B1",
                outline="#526159",
            )
            if len(categories) <= 8:
                canvas.create_text(
                    center,
                    y0 - 7 if value >= 0 else y1 + 7,
                    text=f"{value:+.1f}{suffix}",
                    font=("Arial", 7, "bold"),
                    fill="#2F3B34",
                )
            label = category if len(category) <= 14 else category[:12] + "…"
            canvas.create_text(
                center,
                height - margin_bottom + 12,
                text=label,
                font=("Arial", 7),
                fill="#4D5A52",
            )

    def _draw_grouped_bar_chart(
        self,
        canvas: tk.Canvas,
        categories: list[str],
        series: tuple[tuple[str, list[float]], ...],
        suffix: str = "",
        fixed_max: float | None = None,
        category_colors: list[str] | None = None,
        hover_payloads: list[tuple[int, str, str]] | None = None,
    ) -> None:
        """Dessine un histogramme groupé générique pour les métriques du laboratoire.

        Entrées:
            canvas (tk.Canvas): Zone graphique cible.
            categories (list[str]): Scénarios, plages ou sièges sur l'axe horizontal.
            series (tuple): Couples libellé / valeurs de chaque série.
            suffix (str): Unité ajoutée aux valeurs affichées.
            fixed_max (float | None): Maximum d'axe imposé, par exemple 100 pour un taux.
            category_colors (list[str] | None): Couleur optionnelle de chaque catégorie.
                Quand elle est fournie sur une série unique, chaque barre reprend la
                couleur de sa case de plateau.
            hover_payloads (list[tuple[int, str, str]] | None): Fiches de case optionnelles
                alignées sur les catégories pour rendre les barres survolables.

        Sortie:
            None: Le canvas est entièrement redessiné.
        """
        canvas.delete("all")
        width = max(280, canvas.winfo_width())
        height = max(150, canvas.winfo_height())
        if not categories or not series:
            self._draw_empty_chart(canvas, "Pas de données.")
            return

        all_values = [value for _, values in series for value in values]
        maximum = fixed_max if fixed_max is not None else max(1.0, max(all_values, default=1.0))
        margin_left = 34
        margin_right = 12
        margin_top = 18
        margin_bottom = 35
        usable_w = max(1.0, width - margin_left - margin_right)
        usable_h = max(1.0, height - margin_top - margin_bottom)
        slot = usable_w / max(1, len(categories))
        group_width = slot * 0.72
        bar_width = group_width / max(1, len(series))
        colors = ("#80B68C", "#6F95C8", "#D6A45F", "#B07DB8")

        canvas.create_line(
            margin_left,
            height - margin_bottom,
            width - margin_right,
            height - margin_bottom,
            fill="#78867D",
        )

        for category_index, category in enumerate(categories):
            center = margin_left + slot * category_index + slot / 2
            group_start = center - group_width / 2
            for series_index, (_, values) in enumerate(series):
                value = values[category_index] if category_index < len(values) else 0.0
                bar_height = usable_h * max(0.0, value) / max(1e-9, maximum)
                x0 = group_start + series_index * bar_width + 1
                x1 = group_start + (series_index + 1) * bar_width - 1
                y0 = height - margin_bottom - bar_height
                bar_color = colors[series_index % len(colors)]
                if (
                    category_colors is not None
                    and len(series) == 1
                    and category_index < len(category_colors)
                ):
                    bar_color = category_colors[category_index]
                bar_id = canvas.create_rectangle(
                    x0,
                    y0,
                    x1,
                    height - margin_bottom,
                    fill=bar_color,
                    outline="#526159",
                )
                if (
                    hover_payloads is not None
                    and len(series) == 1
                    and category_index < len(hover_payloads)
                ):
                    self._bind_bar_hover(
                        canvas,
                        bar_id,
                        hover_payloads[category_index],
                    )
                if len(categories) <= 6 and height >= 160:
                    value_text = f"{value:.1f}" if abs(value - round(value)) > 0.04 else f"{value:.0f}"
                    canvas.create_text(
                        (x0 + x1) / 2,
                        max(margin_top + 3, y0 - 7),
                        text=f"{value_text}{suffix}",
                        font=("Arial", 7, "bold"),
                        fill="#2F3B34",
                    )

            label = category if len(category) <= 14 else category[:12] + "…"
            canvas.create_text(
                center,
                height - margin_bottom + 12,
                text=label,
                font=("Arial", 7),
                fill="#4D5A52",
            )

        if len(series) > 1:
            legend_x = margin_left
            for series_index, (label, _) in enumerate(series):
                canvas.create_rectangle(
                    legend_x,
                    4,
                    legend_x + 9,
                    13,
                    fill=colors[series_index % len(colors)],
                    outline="",
                )
                canvas.create_text(
                    legend_x + 13,
                    8,
                    text=label,
                    anchor="w",
                    font=("Arial", 7),
                    fill="#4D5A52",
                )
                legend_x += 16 + max(52, len(label) * 5)

    def _load_report(self) -> None:
        """Recharge un rapport JSON existant sans relancer les simulations.

        Entrées:
            Aucune.

        Sortie:
            None: Résultats, scénarios et contrôles sont restaurés depuis le fichier choisi.
        """
        if self.running:
            return
        path = filedialog.askopenfilename(
            parent=self,
            title="Charger un rapport de simulation",
            filetypes=(("Rapport JSON", "*.json"), ("Tous les fichiers", "*.*")),
        )
        if not path:
            return
        try:
            result = load_simulation_report(path)
        except SimulationReportError as error:
            messagebox.showerror("Rapport invalide", str(error), parent=self)
            return
        self.result = result
        self.scenarios = [scenario.clone() for scenario in result.scenarios]
        self.games_var.set(str(result.config.games_per_scenario))
        self.players_var.set(str(result.config.player_count))
        self.max_rounds_var.set("0" if result.config.max_rounds == 0 else str(result.config.max_rounds))
        self.seed_var.set(str(result.config.base_seed))
        workers = result.config.parallel_workers
        self.workers_var.set("Auto" if workers == 0 else str(workers))
        self.last_used_seed = result.config.base_seed
        self.progress_var.set(100.0)
        self.progress_label.configure(
            text=(
                f"Rapport chargé : {sum(len(item.games) for item in result.campaigns)} parties • "
                f"{len(result.campaigns)} scénario(s) • aucune resimulation."
            )
        )
        self._refresh_scenarios()
        self._refresh_results()
        for button in (
            self.export_json_button,
            self.export_csv_button,
            self.export_summary_button,
            self.export_board_button,
            self.export_development_button,
            self.export_cards_button,
            self.export_html_button,
        ):
            button.state(["!disabled"])

    def _export_html(self) -> None:
        """Exporte un rapport HTML autonome consultable sans l'application.

        Entrées:
            Aucune.

        Sortie:
            None: Un fichier HTML avec tableaux et SVG est créé si choisi.
        """
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le rapport HTML autonome",
            defaultextension=".html",
            filetypes=(("HTML", "*.html"),),
            initialfile="simulation_monopoly_rapport.html",
        )
        if path:
            export_html_report(self.result, path)

    def _export_json(self) -> None:
        """Exporte le rapport complet enrichi au format JSON.

        Entrées:
            Aucune.

        Sortie:
            None: Un fichier est écrit si une destination est choisie.
        """
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le rapport JSON",
            defaultextension=".json",
            filetypes=(("JSON", "*.json"),),
            initialfile="simulation_monopoly_complete.json",
        )
        if path:
            self.result.export_json(path)

    def _export_csv(self) -> None:
        """Exporte une ligne CSV enrichie par partie simulée.

        Entrées:
            Aucune.

        Sortie:
            None: Le fichier est écrit si une destination est choisie.
        """
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter les parties CSV",
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"),),
            initialfile="simulation_monopoly_parties.csv",
        )
        if path:
            self.result.export_csv(path)

    def _export_summary_csv(self) -> None:
        """Exporte une ligne synthétique par scénario au format CSV.

        Entrées:
            Aucune.

        Sortie:
            None: Le résumé comparatif est écrit si une destination est choisie.
        """
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le résumé CSV",
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"),),
            initialfile="simulation_monopoly_resume.csv",
        )
        if path:
            self.result.export_summary_csv(path)

    def _export_board_csv(self) -> None:
        """Exporte fréquentation et rendement de chaque case en CSV.

        Entrées:
            Aucune.

        Sortie:
            None: Un fichier est créé si l'utilisateur choisit une destination.
        """
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter les cases et ROI",
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"),),
            initialfile="simulation_monopoly_cases_roi.csv",
        )
        if path:
            self.result.export_board_csv(path)

    def _export_development_csv(self) -> None:
        """Exporte les rendements par terrain et niveau de construction.

        Entrées:
            Aucune.

        Sortie:
            None: Un CSV détaillé est écrit si une destination est choisie.
        """
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le rendement par construction",
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"),),
            initialfile="simulation_monopoly_constructions_roi.csv",
        )
        if path:
            self.result.export_development_csv(path)


    def _export_cards_csv(self) -> None:
        """Exporte les statistiques détaillées des cartes en CSV.

        Entrées:
            Aucune.

        Sortie:
            None: Un fichier est écrit si une destination est choisie.
        """
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter les statistiques des cartes",
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"),),
            initialfile="simulation_monopoly_cartes.csv",
        )
        if path:
            self.result.export_cards_csv(path)

    def _back(self) -> None:
        """Retourne au menu principal si aucune campagne n'est en cours.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback de retour est exécuté si possible.
        """
        if not self.running:
            self.back_callback()
