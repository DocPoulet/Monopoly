"""Composants graphiques du replay et des statistiques avancées."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from monopoly.history import GameEvent
from monopoly.replay import ReplaySnapshot
from monopoly.statistics import GameStatistics

if TYPE_CHECKING:
    from monopoly.game import Game


PLAYER_COLORS = [
    "#D94343",
    "#3478D4",
    "#2D9B64",
    "#E0912E",
    "#8E5AC7",
    "#188E9E",
]


def replay_grid_position(index: int) -> tuple[int, int]:
    """Convertit une case du plateau en coordonnées de grille pour le mini replay.

    Entrées:
        index (int): Index de case compris entre zéro et trente-neuf.

    Sortie:
        tuple[int, int]: Ligne et colonne sur la grille 11 × 11.

    Lève:
        ValueError: Si l'index n'appartient pas au plateau.
    """
    if not 0 <= index <= 39:
        raise ValueError("L'index d'une case doit être compris entre 0 et 39.")
    if index == 0:
        return 10, 10
    if 1 <= index <= 9:
        return 10, 10 - index
    if index == 10:
        return 10, 0
    if 11 <= index <= 19:
        return 20 - index, 0
    if index == 20:
        return 0, 0
    if 21 <= index <= 29:
        return 0, index - 20
    if index == 30:
        return 0, 10
    return index - 30, 10


class ReplayBoardCanvas(tk.Canvas):
    """Dessine un mini-plateau statique à partir d'un snapshot de replay.

    Entrées:
        master (tk.Misc): Conteneur Tkinter.

    Sortie:
        ReplayBoardCanvas: Canvas réutilisable sans référence mutable au moteur.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise le canvas du mini-plateau.

        Entrées:
            master (tk.Misc): Conteneur parent.

        Sortie:
            None: Le canvas est prêt à recevoir un snapshot.
        """
        super().__init__(
            master,
            background="#DCE6E2",
            highlightbackground="#7F8C8D",
            highlightthickness=1,
            width=410,
            height=410,
        )
        self.game: Game | None = None
        self.snapshot: ReplaySnapshot | None = None
        self.bind("<Configure>", self._redraw_event)

    def show_snapshot(self, game: "Game", snapshot: ReplaySnapshot) -> None:
        """Mémorise puis dessine un état historique.

        Entrées:
            game (Game): Partie fournissant noms et types de cases.
            snapshot (ReplaySnapshot): État immuable à afficher.

        Sortie:
            None: Le mini-plateau est redessiné.
        """
        self.game = game
        self.snapshot = snapshot
        self.redraw()

    def _redraw_event(self, event: tk.Event) -> None:
        """Redessine après redimensionnement du canvas.

        Entrées:
            event (tk.Event): Événement Configure de Tkinter.

        Sortie:
            None: Le contenu suit la nouvelle taille.
        """
        self.redraw()

    def redraw(self) -> None:
        """Dessine cases, propriétaires, bâtiments et pions du snapshot.

        Entrées:
            Aucune autre que le snapshot mémorisé.

        Sortie:
            None: Tous les objets graphiques précédents sont remplacés.
        """
        self.delete("all")
        if self.game is None or self.snapshot is None:
            return

        width = max(220, self.winfo_width())
        height = max(220, self.winfo_height())
        size = min(width, height) - 12
        cell = size / 11
        ox = (width - size) / 2
        oy = (height - size) / 2

        property_by_index = {
            item.index: item
            for item in self.snapshot.properties
        }

        for index in range(40):
            row, column = replay_grid_position(index)
            x1 = ox + column * cell
            y1 = oy + row * cell
            x2 = x1 + cell
            y2 = y1 + cell
            self.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#F7F3E8",
                outline="#77827D",
                width=1,
            )
            self.create_text(
                (x1 + x2) / 2,
                y1 + cell * 0.16,
                text=str(index),
                font=("Arial", max(6, int(cell * 0.13)), "bold"),
                fill="#68736E",
            )

            state = property_by_index.get(index)
            if state is not None and state.owner_id is not None:
                color = PLAYER_COLORS[state.owner_id % len(PLAYER_COLORS)]
                self.create_rectangle(
                    x1 + 2,
                    y2 - cell * 0.17,
                    x2 - 2,
                    y2 - 2,
                    fill=color,
                    outline=color,
                )
                if state.mortgaged:
                    self.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text="HYP",
                        font=("Arial", max(5, int(cell * 0.11)), "bold"),
                        fill="#A22B2B",
                    )
                elif state.hotel:
                    self.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text="H",
                        font=("Arial", max(7, int(cell * 0.17)), "bold"),
                        fill="#922B21",
                    )
                elif state.houses:
                    self.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=f"M{state.houses}",
                        font=("Arial", max(6, int(cell * 0.13)), "bold"),
                        fill="#267A43",
                    )

        token_offsets = [
            (-0.19, -0.18),
            (0.19, -0.18),
            (-0.19, 0.18),
            (0.19, 0.18),
            (0.0, -0.02),
            (0.0, 0.24),
        ]
        for player in self.snapshot.players:
            if player.bankrupt:
                continue
            row, column = replay_grid_position(player.position)
            cx = ox + (column + 0.5) * cell
            cy = oy + (row + 0.5) * cell
            dx, dy = token_offsets[player.player_id % len(token_offsets)]
            radius = max(4, cell * 0.105)
            color = PLAYER_COLORS[player.player_id % len(PLAYER_COLORS)]
            self.create_oval(
                cx + dx * cell - radius,
                cy + dy * cell - radius,
                cx + dx * cell + radius,
                cy + dy * cell + radius,
                fill=color,
                outline="#FFFFFF",
                width=1,
            )

        self.create_text(
            width / 2,
            height / 2 - 22,
            text=self.snapshot.label,
            font=("Arial", 13, "bold"),
            fill="#263238",
        )
        self.create_text(
            width / 2,
            height / 2 + 2,
            text=f"Cagnotte : {self.snapshot.free_parking_pot} $",
            font=("Arial", 10, "bold"),
            fill="#356B42",
        )
        self.create_text(
            width / 2,
            height / 2 + 24,
            text="Snapshot en lecture seule",
            font=("Arial", 8),
            fill="#65726C",
        )


class ReplayTab(ttk.Frame):
    """Permet de parcourir les snapshots et événements d'un tour de table.

    Entrées:
        master (tk.Misc): Onglet parent.

    Sortie:
        ReplayTab: Interface de replay indépendante de la partie réelle.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit navigation, mini-plateau, joueurs et journal du tour.

        Entrées:
            master (tk.Misc): Conteneur parent.

        Sortie:
            None: L'onglet est prêt à recevoir une partie.
        """
        super().__init__(master, padding=8)
        self.game: Game | None = None
        self.snapshots: list[ReplaySnapshot] = []
        self.round_events: list[GameEvent] = []
        self.snapshot_index = 0

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(3, weight=2)

        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 7))
        controls.columnconfigure(1, weight=1)

        self.previous_snapshot_button = ttk.Button(
            controls,
            text="← Tour précédent",
            command=self._previous_snapshot,
        )
        self.previous_snapshot_button.grid(row=0, column=0, padx=(0, 5))

        self.snapshot_var = tk.StringVar(value="")
        self.snapshot_combo = ttk.Combobox(
            controls,
            textvariable=self.snapshot_var,
            state="readonly",
        )
        self.snapshot_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.snapshot_combo.bind("<<ComboboxSelected>>", self._snapshot_changed)

        self.next_snapshot_button = ttk.Button(
            controls,
            text="Tour suivant →",
            command=self._next_snapshot,
        )
        self.next_snapshot_button.grid(row=0, column=2, padx=(5, 0))

        board_frame = ttk.LabelFrame(self, text="Plateau au snapshot", padding=5)
        board_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        board_frame.columnconfigure(0, weight=1)
        board_frame.rowconfigure(0, weight=1)
        self.board_canvas = ReplayBoardCanvas(board_frame)
        self.board_canvas.grid(row=0, column=0, sticky="nsew")

        player_frame = ttk.LabelFrame(self, text="État des joueurs", padding=5)
        player_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        player_frame.columnconfigure(0, weight=1)
        player_frame.rowconfigure(0, weight=1)
        columns = ("cash", "worth", "position", "properties", "state")
        self.player_tree = ttk.Treeview(
            player_frame,
            columns=columns,
            show="tree headings",
            height=7,
        )
        self.player_tree.heading("#0", text="Joueur")
        self.player_tree.heading("cash", text="Cash")
        self.player_tree.heading("worth", text="Patrimoine")
        self.player_tree.heading("position", text="Case")
        self.player_tree.heading("properties", text="Biens")
        self.player_tree.heading("state", text="État")
        self.player_tree.column("#0", width=95)
        for column in columns:
            self.player_tree.column(column, width=72, anchor="center")
        self.player_tree.grid(row=0, column=0, sticky="nsew")

        self.snapshot_summary = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            wraplength=820,
        )
        self.snapshot_summary.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(7, 5),
        )

        events_frame = ttk.LabelFrame(self, text="Événements de ce tour", padding=5)
        events_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        events_frame.columnconfigure(0, weight=1)
        events_frame.rowconfigure(0, weight=1)
        event_columns = ("seq", "player", "type", "message")
        self.event_tree = ttk.Treeview(
            events_frame,
            columns=event_columns,
            show="headings",
            selectmode="browse",
        )
        self.event_tree.heading("seq", text="#")
        self.event_tree.heading("player", text="Joueur")
        self.event_tree.heading("type", text="Type")
        self.event_tree.heading("message", text="Événement")
        self.event_tree.column("seq", width=45, anchor="center")
        self.event_tree.column("player", width=90, anchor="center")
        self.event_tree.column("type", width=110, anchor="center")
        self.event_tree.column("message", width=510)
        self.event_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(events_frame, orient="vertical", command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        self.event_tree.bind("<<TreeviewSelect>>", self._event_selected)

        navigation = ttk.Frame(self)
        navigation.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        navigation.columnconfigure(1, weight=1)
        self.previous_event_button = ttk.Button(
            navigation,
            text="← Événement",
            command=lambda: self._move_event(-1),
        )
        self.previous_event_button.grid(row=0, column=0)
        self.event_detail = ttk.Label(
            navigation,
            text="",
            style="Muted.TLabel",
            wraplength=650,
            justify="center",
        )
        self.event_detail.grid(row=0, column=1, sticky="ew", padx=8)
        self.next_event_button = ttk.Button(
            navigation,
            text="Événement →",
            command=lambda: self._move_event(1),
        )
        self.next_event_button.grid(row=0, column=2)

    def set_game(self, game: "Game") -> None:
        """Charge les snapshots de la partie et sélectionne l'état courant.

        Entrées:
            game (Game): Partie à parcourir en lecture seule.

        Sortie:
            None: Les listes et le mini-plateau sont synchronisés.
        """
        self.game = game
        self.snapshots = game.replay.display_snapshots(game)
        labels = [snapshot.label for snapshot in self.snapshots]
        self.snapshot_combo.configure(values=labels)
        if self.snapshots:
            self.snapshot_index = len(self.snapshots) - 1
            self.snapshot_var.set(labels[self.snapshot_index])
            self._render_snapshot()
        else:
            self.snapshot_var.set("")

    def _snapshot_changed(self, event: tk.Event | None) -> None:
        """Affiche le snapshot choisi dans la liste déroulante.

        Entrées:
            event (tk.Event | None): Événement de sélection facultatif.

        Sortie:
            None: Le snapshot et son journal deviennent actifs.
        """
        value = self.snapshot_var.get()
        for index, snapshot in enumerate(self.snapshots):
            if snapshot.label == value:
                self.snapshot_index = index
                self._render_snapshot()
                return

    def _move_snapshot(self, delta: int) -> None:
        """Déplace la sélection dans la timeline.

        Entrées:
            delta (int): Décalage négatif ou positif.

        Sortie:
            None: La timeline change de snapshot si possible.
        """
        target = self.snapshot_index + delta
        if not 0 <= target < len(self.snapshots):
            return
        self.snapshot_index = target
        self.snapshot_var.set(self.snapshots[target].label)
        self._render_snapshot()

    def _previous_snapshot(self) -> None:
        """Recule d'un snapshot dans le replay.

        Entrées:
            Aucune.

        Sortie:
            None: La sélection recule si possible.
        """
        self._move_snapshot(-1)

    def _next_snapshot(self) -> None:
        """Avance d'un snapshot dans le replay.

        Entrées:
            Aucune.

        Sortie:
            None: La sélection avance si possible.
        """
        self._move_snapshot(1)

    def _render_snapshot(self) -> None:
        """Rafraîchit mini-plateau, joueurs et événements du snapshot sélectionné.

        Entrées:
            Aucune.

        Sortie:
            None: Tous les widgets du replay sont mis à jour.
        """
        if self.game is None or not self.snapshots:
            return
        snapshot = self.snapshots[self.snapshot_index]
        self.board_canvas.show_snapshot(self.game, snapshot)

        for item in self.player_tree.get_children():
            self.player_tree.delete(item)
        for player in snapshot.players:
            state = "Faillite" if player.bankrupt else ("Prison" if player.in_jail else "Actif")
            self.player_tree.insert(
                "",
                "end",
                text=player.name,
                values=(
                    f"{player.cash} $",
                    f"{player.net_worth} $",
                    player.position,
                    player.properties_count,
                    state,
                ),
            )

        houses = "∞" if self.game.bank.house_limit == 0 else str(snapshot.houses_available)
        hotels = "∞" if self.game.bank.hotel_limit == 0 else str(snapshot.hotels_available)
        self.snapshot_summary.configure(
            text=(
                f"{snapshot.label} • cagnotte {snapshot.free_parking_pot} $ • "
                f"banque : {houses} maisons / {hotels} hôtels • "
                f"événements inclus jusqu'au #{snapshot.event_sequence}"
            )
        )

        if snapshot.round_number <= 0:
            self.round_events = []
        else:
            self.round_events = [
                event
                for event in self.game.history.events
                if event.turn_number == snapshot.round_number
                and event.sequence <= snapshot.event_sequence
            ]
        self._render_round_events()
        self._refresh_snapshot_buttons()

    def _render_round_events(self) -> None:
        """Remplit le journal du tour de table sélectionné.

        Entrées:
            Aucune.

        Sortie:
            None: Le tableau est reconstruit dans l'ordre des événements.
        """
        for item in self.event_tree.get_children():
            self.event_tree.delete(item)
        if self.game is None:
            return
        names = {player.player_id: player.name for player in self.game.players}
        for index, event in enumerate(self.round_events):
            self.event_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    event.sequence,
                    names.get(event.player_id, "—"),
                    event.event_type,
                    event.message,
                ),
            )
        if self.round_events:
            last = str(len(self.round_events) - 1)
            self.event_tree.selection_set(last)
            self.event_tree.focus(last)
            self.event_tree.see(last)
            self._event_selected(None)
        else:
            self.event_detail.configure(text="Aucun événement dans ce snapshot.")
            self._refresh_event_buttons()

    def _selected_event_index(self) -> int | None:
        """Retourne l'index du journal actuellement sélectionné.

        Entrées:
            Aucune.

        Sortie:
            int | None: Index valide ou ``None``.
        """
        selection = self.event_tree.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except ValueError:
            return None

    def _event_selected(self, event: tk.Event | None) -> None:
        """Affiche le détail de l'événement de replay choisi.

        Entrées:
            event (tk.Event | None): Événement Tkinter facultatif.

        Sortie:
            None: Le détail structuré est affiché sous le journal.
        """
        index = self._selected_event_index()
        if index is None or not 0 <= index < len(self.round_events):
            return
        item = self.round_events[index]
        data_text = ", ".join(f"{key}={value}" for key, value in item.data.items())
        suffix = f" • {data_text}" if data_text else ""
        self.event_detail.configure(text=f"#{item.sequence} — {item.message}{suffix}")
        self._refresh_event_buttons()

    def _move_event(self, delta: int) -> None:
        """Déplace la sélection dans le journal du tour.

        Entrées:
            delta (int): Décalage, généralement -1 ou +1.

        Sortie:
            None: L'événement voisin est sélectionné s'il existe.
        """
        index = self._selected_event_index()
        if index is None:
            return
        target = index + delta
        if not 0 <= target < len(self.round_events):
            return
        iid = str(target)
        self.event_tree.selection_set(iid)
        self.event_tree.focus(iid)
        self.event_tree.see(iid)
        self._event_selected(None)

    def _refresh_event_buttons(self) -> None:
        """Active la navigation événement selon la sélection courante.

        Entrées:
            Aucune.

        Sortie:
            None: Les deux boutons reflètent les bornes du journal.
        """
        index = self._selected_event_index()
        previous = index is not None and index > 0
        next_ = index is not None and index < len(self.round_events) - 1
        self.previous_event_button.state(["!disabled"] if previous else ["disabled"])
        self.next_event_button.state(["!disabled"] if next_ else ["disabled"])

    def _refresh_snapshot_buttons(self) -> None:
        """Active la navigation de tours selon la position dans la timeline.

        Entrées:
            Aucune.

        Sortie:
            None: Les boutons précédent/suivant sont synchronisés.
        """
        previous = self.snapshot_index > 0
        next_ = self.snapshot_index < len(self.snapshots) - 1
        self.previous_snapshot_button.state(["!disabled"] if previous else ["disabled"])
        self.next_snapshot_button.state(["!disabled"] if next_ else ["disabled"])


class StatisticsChart(tk.Canvas):
    """Trace une série temporelle légère directement avec Tkinter.

    Entrées:
        master (tk.Misc): Conteneur parent.

    Sortie:
        StatisticsChart: Canvas capable d'afficher les métriques du replay.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit le canvas du graphique.

        Entrées:
            master (tk.Misc): Conteneur parent.

        Sortie:
            None: Le graphique est initialisé.
        """
        super().__init__(
            master,
            background="#FFFFFF",
            highlightbackground="#A7B0B5",
            highlightthickness=1,
            height=250,
        )
        self.stats: GameStatistics | None = None
        self.metric = "Cash"
        self.bind("<Configure>", self._redraw_event)

    def show_statistics(self, stats: GameStatistics, metric: str) -> None:
        """Charge une statistique et une métrique à tracer.

        Entrées:
            stats (GameStatistics): Données calculées.
            metric (str): ``Cash``, ``Patrimoine``, ``Biens`` ou ``Cagnotte``.

        Sortie:
            None: Le graphique est redessiné.
        """
        self.stats = stats
        self.metric = metric
        self.redraw()

    def _redraw_event(self, event: tk.Event) -> None:
        """Redessine le graphique après redimensionnement.

        Entrées:
            event (tk.Event): Événement Configure.

        Sortie:
            None: La géométrie est recalculée.
        """
        self.redraw()

    def redraw(self) -> None:
        """Trace axes, échelle, lignes joueurs ou cagnotte.

        Entrées:
            Aucune autre que les statistiques mémorisées.

        Sortie:
            None: Le canvas contient le nouveau graphique.
        """
        self.delete("all")
        if self.stats is None or not self.stats.round_series:
            self.create_text(
                max(1, self.winfo_width()) / 2,
                max(1, self.winfo_height()) / 2,
                text="Pas encore assez de snapshots pour tracer l'évolution.",
                fill="#687076",
            )
            return

        width = max(360, self.winfo_width())
        height = max(190, self.winfo_height())
        left, right, top, bottom = 52, width - 18, 20, height - 36
        points = self.stats.round_series

        if self.metric == "Cagnotte":
            series = {None: [point.free_parking_pot for point in points]}
        elif self.metric == "Patrimoine":
            series = {
                player.player_id: [
                    point.worth_by_player.get(player.player_id, 0)
                    for point in points
                ]
                for player in self.stats.players
            }
        elif self.metric == "Biens":
            series = {
                player.player_id: [
                    point.properties_by_player.get(player.player_id, 0)
                    for point in points
                ]
                for player in self.stats.players
            }
        else:
            series = {
                player.player_id: [
                    point.cash_by_player.get(player.player_id, 0)
                    for point in points
                ]
                for player in self.stats.players
            }

        all_values = [value for values in series.values() for value in values]
        maximum = max(all_values, default=1)
        minimum = min(all_values, default=0)
        if maximum == minimum:
            maximum += 1
        padding = max(1, (maximum - minimum) * 0.08)
        low = min(0, minimum - padding)
        high = maximum + padding

        self.create_line(left, top, left, bottom, fill="#6F7B80", width=1)
        self.create_line(left, bottom, right, bottom, fill="#6F7B80", width=1)

        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - (bottom - top) * fraction
            value = low + (high - low) * fraction
            self.create_line(left, y, right, y, fill="#EEF1F2")
            self.create_text(
                left - 6,
                y,
                text=f"{int(value)}",
                anchor="e",
                font=("Arial", 7),
                fill="#69747A",
            )

        count = len(points)
        def x_at(index: int) -> float:
            """Calcule l'abscisse d'un point de série.

            Entrées:
                index (int): Position dans la série.

            Sortie:
                float: Coordonnée X dans la zone de tracé.
            """
            if count <= 1:
                return (left + right) / 2
            return left + (right - left) * index / (count - 1)

        def y_at(value: int) -> float:
            """Calcule l'ordonnée d'une valeur suivant l'échelle courante.

            Entrées:
                value (int): Valeur financière ou nombre de biens.

            Sortie:
                float: Coordonnée Y dans la zone de tracé.
            """
            ratio = (value - low) / (high - low)
            return bottom - ratio * (bottom - top)

        for series_id, values in series.items():
            if series_id is None:
                color = "#3E7C4B"
                label = "Cagnotte"
            else:
                color = PLAYER_COLORS[int(series_id) % len(PLAYER_COLORS)]
                player = next(
                    item for item in self.stats.players
                    if item.player_id == series_id
                )
                label = player.name
            coords: list[float] = []
            for index, value in enumerate(values):
                coords.extend([x_at(index), y_at(value)])
            if len(coords) >= 4:
                self.create_line(*coords, fill=color, width=2)
            elif coords:
                self.create_oval(
                    coords[0] - 2,
                    coords[1] - 2,
                    coords[0] + 2,
                    coords[1] + 2,
                    fill=color,
                    outline=color,
                )
            legend_x = left + 8 + list(series.keys()).index(series_id) * 120
            self.create_line(legend_x, 10, legend_x + 18, 10, fill=color, width=3)
            self.create_text(
                legend_x + 23,
                10,
                text=label,
                anchor="w",
                font=("Arial", 8),
                fill="#3F484C",
            )

        if points:
            self.create_text(
                left,
                bottom + 15,
                text=points[0].label,
                anchor="w",
                font=("Arial", 7),
                fill="#69747A",
            )
            self.create_text(
                right,
                bottom + 15,
                text=points[-1].label,
                anchor="e",
                font=("Arial", 7),
                fill="#69747A",
            )


class AdvancedStatisticsTab(ttk.Frame):
    """Affiche indicateurs, graphique temporel et rentabilité des propriétés.

    Entrées:
        master (tk.Misc): Onglet parent.

    Sortie:
        AdvancedStatisticsTab: Vue statistique recalculable à partir d'une partie.
    """

    METRICS = ("Cash", "Patrimoine", "Biens", "Cagnotte")

    def __init__(self, master: tk.Misc) -> None:
        """Construit les indicateurs globaux, joueurs, graphique et propriétés.

        Entrées:
            master (tk.Misc): Conteneur parent.

        Sortie:
            None: L'onglet statistique est prêt.
        """
        super().__init__(master, padding=8)
        self.stats: GameStatistics | None = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=2)
        self.rowconfigure(5, weight=1)

        self.summary_label = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            wraplength=900,
        )
        self.summary_label.grid(row=0, column=0, sticky="ew", pady=(0, 7))

        self.highlights_label = ttk.Label(
            self,
            text="",
            justify="center",
            font=("Arial", 9, "bold"),
            wraplength=900,
        )
        self.highlights_label.grid(row=1, column=0, sticky="ew", pady=(0, 7))

        player_frame = ttk.LabelFrame(self, text="Joueurs", padding=5)
        player_frame.grid(row=2, column=0, sticky="ew", pady=(0, 7))
        columns = (
            "cash",
            "worth",
            "properties",
            "rent_paid",
            "rent_received",
            "jail",
            "trades",
        )
        self.player_tree = ttk.Treeview(
            player_frame,
            columns=columns,
            show="tree headings",
            height=4,
        )
        headings = {
            "cash": "Cash",
            "worth": "Patrimoine",
            "properties": "Biens",
            "rent_paid": "Loyers payés",
            "rent_received": "Loyers reçus",
            "jail": "Prison",
            "trades": "Échanges",
        }
        self.player_tree.heading("#0", text="Joueur")
        self.player_tree.column("#0", width=110)
        for column in columns:
            self.player_tree.heading(column, text=headings[column])
            self.player_tree.column(column, width=90, anchor="center")
        self.player_tree.pack(fill="x")

        chart_frame = ttk.LabelFrame(self, text="Évolution par tour", padding=5)
        chart_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 7))
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(1, weight=1)
        controls = ttk.Frame(chart_frame)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(controls, text="Métrique :").pack(side="left")
        self.metric_var = tk.StringVar(value="Cash")
        self.metric_combo = ttk.Combobox(
            controls,
            textvariable=self.metric_var,
            state="readonly",
            values=self.METRICS,
            width=16,
        )
        self.metric_combo.pack(side="left", padx=(6, 0))
        self.metric_combo.bind("<<ComboboxSelected>>", self._metric_changed)
        self.chart = StatisticsChart(chart_frame)
        self.chart.grid(row=1, column=0, sticky="nsew")

        property_frame = ttk.LabelFrame(self, text="Rentabilité des propriétés", padding=5)
        property_frame.grid(row=5, column=0, sticky="nsew")
        property_frame.columnconfigure(0, weight=1)
        property_frame.rowconfigure(0, weight=1)
        columns = ("total", "events", "biggest")
        self.property_tree = ttk.Treeview(
            property_frame,
            columns=columns,
            show="tree headings",
            height=5,
        )
        self.property_tree.heading("#0", text="Propriété")
        self.property_tree.heading("total", text="Loyers cumulés")
        self.property_tree.heading("events", text="Loyers payés")
        self.property_tree.heading("biggest", text="Plus gros")
        self.property_tree.column("#0", width=210)
        for column in columns:
            self.property_tree.column(column, width=110, anchor="center")
        self.property_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(property_frame, orient="vertical", command=self.property_tree.yview)
        self.property_tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

    def set_game(self, game: "Game") -> None:
        """Recalcule et affiche toutes les statistiques de la partie.

        Entrées:
            game (Game): Partie source.

        Sortie:
            None: Tableaux, indicateurs et graphique sont rafraîchis.
        """
        self.stats = GameStatistics.from_game(game)
        stats = self.stats
        self.summary_label.configure(text=" • ".join(stats.summary_lines()))

        profitable = stats.most_profitable_property
        property_text = (
            f"propriété la plus rentable : {profitable.name} ({profitable.rent_received} $)"
            if profitable is not None
            else "aucun loyer encaissé pour l'instant"
        )
        self.highlights_label.configure(
            text=(
                f"Plus gros loyer : {stats.biggest_rent} $ sur {stats.biggest_rent_property} • "
                f"{property_text} • pic cagnotte : {stats.free_parking_peak} $ • "
                f"plus gros échange cash : {stats.largest_trade_cash} $"
            )
        )

        for item in self.player_tree.get_children():
            self.player_tree.delete(item)
        for player in stats.players:
            self.player_tree.insert(
                "",
                "end",
                text=player.name + (" (faillite)" if player.bankrupt else ""),
                values=(
                    f"{player.cash} $",
                    f"{player.net_worth} $",
                    player.properties_owned,
                    f"{player.rent_paid} $",
                    f"{player.rent_received} $",
                    player.jail_visits,
                    player.trades,
                ),
            )

        for item in self.property_tree.get_children():
            self.property_tree.delete(item)
        for property_ in stats.properties:
            if property_.rent_received <= 0 and property_.rent_events <= 0:
                continue
            self.property_tree.insert(
                "",
                "end",
                text=property_.name,
                values=(
                    f"{property_.rent_received} $",
                    property_.rent_events,
                    f"{property_.biggest_rent} $",
                ),
            )

        self.chart.show_statistics(stats, self.metric_var.get())

    def _metric_changed(self, event: tk.Event | None) -> None:
        """Redessine le graphique après changement de métrique.

        Entrées:
            event (tk.Event | None): Événement de combobox facultatif.

        Sortie:
            None: Le graphique utilise la nouvelle série.
        """
        if self.stats is not None:
            self.chart.show_statistics(self.stats, self.metric_var.get())
