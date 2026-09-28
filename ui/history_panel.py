"""Panneau intégré combinant replay, statistiques avancées et journal filtrable."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from monopoly.history import GameEvent
from monopoly.statistics import GameStatistics
from .replay_panel import AdvancedStatisticsTab, ReplayTab

if TYPE_CHECKING:
    from monopoly.game import Game


EVENT_LABELS = {
    "all": "Tous",
    "turn": "Tours",
    "card_draw": "Cartes",
    "purchase": "Achats",
    "auction_win": "Enchères",
    "building": "Constructions",
    "building_sale": "Ventes bâtiments",
    "building_auction_win": "Enchères bâtiments",
    "mortgage": "Hypothèques",
    "unmortgage": "Déshypothèques",
    "rent": "Loyers",
    "rent_pending": "Loyers à réclamer",
    "rent_waived": "Loyers abandonnés",
    "trade": "Échanges",
    "debt_property_transfer": "Biens cédés pour dette",
    "bankruptcy": "Faillites",
    "jail_enter": "Prison",
    "financial": "Financier",
    "free_parking_bonus": "Bonus Parc Gratuit",
    "free_parking_pot_add": "Cagnotte +",
    "free_parking_pot_collect": "Cagnotte gagnée",
    "game_over": "Fin de partie",
}


class HistoryOverlay(tk.Frame):
    """Affiche replay, statistiques et journal sans modifier la partie courante.

    Entrées:
        master (tk.Misc): Conteneur parent, généralement ``BoardView``.

    Sortie:
        HistoryOverlay: Panneau masqué hors consultation.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit les trois onglets et la navigation du journal détaillé.

        Entrées:
            master (tk.Misc): Conteneur graphique parent.

        Sortie:
            None: Le panneau est créé puis masqué.
        """
        super().__init__(
            master,
            background="#E8EEF1",
            highlightbackground="#7E8C95",
            highlightthickness=2,
            padx=10,
            pady=10,
        )
        self.game: Game | None = None
        self.on_close: Callable[[], None] | None = None
        self.filtered_events: list[GameEvent] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        ttk.Label(
            self,
            text="Replay & analyse de partie",
            font=("Arial", 17, "bold"),
        ).grid(row=0, column=0, sticky="w")

        self.summary_label = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            wraplength=880,
        )
        self.summary_label.grid(row=1, column=0, sticky="ew", pady=(3, 7))

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, sticky="nsew")

        self.replay_tab = ReplayTab(self.notebook)
        self.statistics_tab = AdvancedStatisticsTab(self.notebook)
        self.journal_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.replay_tab, text="Replay")
        self.notebook.add(self.statistics_tab, text="Statistiques avancées")
        self.notebook.add(self.journal_tab, text="Journal")

        self._build_journal_tab()

        footer = ttk.Frame(self)
        footer.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(
            footer,
            text=(
                "Le replay utilise des snapshots en lecture seule : consulter un ancien tour "
                "ne modifie jamais la partie réelle."
            ),
            style="Muted.TLabel",
        ).pack(side="left")
        ttk.Button(
            footer,
            text="Fermer",
            command=self._close,
        ).pack(side="right")

        self.place_forget()

    def _build_journal_tab(self) -> None:
        """Construit le journal filtrable compatible avec les versions précédentes.

        Entrées:
            Aucune.

        Sortie:
            None: Filtres, tableau, détail et navigation sont ajoutés à l'onglet.
        """
        self.journal_tab.columnconfigure(0, weight=1)
        self.journal_tab.rowconfigure(2, weight=1)

        controls = ttk.Frame(self.journal_tab)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Filtre :").grid(row=0, column=0, sticky="w")
        self.filter_var = tk.StringVar(value="Tous")
        self.filter_combo = ttk.Combobox(
            controls,
            textvariable=self.filter_var,
            state="readonly",
            values=list(EVENT_LABELS.values()),
            width=24,
        )
        self.filter_combo.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.filter_combo.bind("<<ComboboxSelected>>", self._filter_changed)

        self.previous_button = ttk.Button(
            controls,
            text="← Précédent",
            command=self._previous_event,
        )
        self.previous_button.grid(row=0, column=2, padx=3)

        self.next_button = ttk.Button(
            controls,
            text="Suivant →",
            command=self._next_event,
        )
        self.next_button.grid(row=0, column=3, padx=3)

        stats = ttk.LabelFrame(self.journal_tab, text="Résumé joueurs", padding=5)
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 7))
        columns = (
            "turns",
            "cards",
            "bought",
            "rent_paid",
            "rent_received",
            "buildings",
            "jail",
        )
        self.player_tree = ttk.Treeview(
            stats,
            columns=columns,
            show="tree headings",
            height=4,
        )
        headings = {
            "turns": "Tours",
            "cards": "Cartes",
            "bought": "Achats",
            "rent_paid": "Loyers payés",
            "rent_received": "Loyers reçus",
            "buildings": "Bâtiments",
            "jail": "Prison",
        }
        self.player_tree.heading("#0", text="Joueur")
        self.player_tree.column("#0", width=110)
        for column in columns:
            self.player_tree.heading(column, text=headings[column])
            self.player_tree.column(column, width=88, anchor="center")
        self.player_tree.pack(fill="x")

        event_frame = ttk.LabelFrame(self.journal_tab, text="Journal détaillé", padding=5)
        event_frame.grid(row=2, column=0, sticky="nsew")
        event_frame.columnconfigure(0, weight=1)
        event_frame.rowconfigure(0, weight=1)
        event_columns = ("turn", "type", "message")
        self.event_tree = ttk.Treeview(
            event_frame,
            columns=event_columns,
            show="headings",
            selectmode="browse",
        )
        self.event_tree.heading("turn", text="Tour")
        self.event_tree.heading("type", text="Type")
        self.event_tree.heading("message", text="Événement")
        self.event_tree.column("turn", width=55, anchor="center")
        self.event_tree.column("type", width=145, anchor="center")
        self.event_tree.column("message", width=590)
        scroll = ttk.Scrollbar(event_frame, orient="vertical", command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=scroll.set)
        self.event_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.event_tree.bind("<<TreeviewSelect>>", self._event_selected)

        self.detail_label = ttk.Label(
            self.journal_tab,
            text="",
            style="Muted.TLabel",
            wraplength=850,
            justify="left",
        )
        self.detail_label.grid(row=3, column=0, sticky="ew", pady=(7, 0))

    def show(self, game: "Game", on_close: Callable[[], None]) -> None:
        """Affiche la timeline courante et recalcule toutes les analyses.

        Entrées:
            game (Game): Partie à analyser.
            on_close (Callable[[], None]): Callback de fermeture.

        Sortie:
            None: Le panneau apparaît au centre du plateau.
        """
        self.game = game
        self.on_close = on_close
        self.filter_var.set("Tous")
        self.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.96,
            relheight=0.92,
        )
        self.lift()
        self.refresh_data()

    def hide(self) -> None:
        """Masque le panneau et oublie ses références temporaires.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît du plateau.
        """
        self.place_forget()
        self.game = None
        self.on_close = None
        self.filtered_events = []

    def _selected_filter_key(self) -> str:
        """Convertit le libellé visible du filtre en type d'événement.

        Entrées:
            Aucune.

        Sortie:
            str: Clé d'événement ou ``all``.
        """
        label = self.filter_var.get()
        for key, value in EVENT_LABELS.items():
            if value == label:
                return key
        return "all"

    def refresh_data(self) -> None:
        """Reconstruit replay, statistiques et journal à partir de la partie courante.

        Entrées:
            Aucune autre que la partie courante.

        Sortie:
            None: Les trois onglets affichent les données les plus récentes.
        """
        if self.game is None:
            return

        stats = GameStatistics.from_game(self.game)
        self.summary_label.configure(
            text=(
                " • ".join(stats.summary_lines())
                + f" • snapshots : {len(self.game.replay.display_snapshots(self.game))}"
            )
        )
        self.replay_tab.set_game(self.game)
        self.statistics_tab.set_game(self.game)

        for item in self.player_tree.get_children():
            self.player_tree.delete(item)
        for player in stats.players:
            self.player_tree.insert(
                "",
                "end",
                text=player.name,
                values=(
                    player.turns,
                    player.cards_drawn,
                    player.properties_bought,
                    f"{player.rent_paid} $",
                    f"{player.rent_received} $",
                    player.buildings_built,
                    player.jail_visits,
                ),
            )

        key = self._selected_filter_key()
        events = self.game.history.recent(1000)
        if key != "all":
            events = [event for event in events if event.event_type == key]
        self.filtered_events = events

        for item in self.event_tree.get_children():
            self.event_tree.delete(item)
        for index, event in enumerate(events):
            self.event_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    event.turn_number,
                    EVENT_LABELS.get(event.event_type, event.event_type),
                    event.message,
                ),
            )

        items = self.event_tree.get_children()
        if items:
            last = items[-1]
            self.event_tree.selection_set(last)
            self.event_tree.focus(last)
            self.event_tree.see(last)
            self._event_selected(None)
        else:
            self.detail_label.configure(text="Aucun événement pour ce filtre.")
        self._refresh_navigation()

    def _filter_changed(self, event: tk.Event | None) -> None:
        """Réapplique le filtre après sélection d'une catégorie.

        Entrées:
            event (tk.Event | None): Événement de combobox facultatif.

        Sortie:
            None: La liste du journal est reconstruite.
        """
        self.refresh_data()

    def _selected_event_index(self) -> int | None:
        """Retourne l'index de l'événement sélectionné dans le journal global.

        Entrées:
            Aucune.

        Sortie:
            int | None: Index dans ``filtered_events`` ou ``None``.
        """
        selection = self.event_tree.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except ValueError:
            return None

    def _event_selected(self, event: tk.Event | None) -> None:
        """Affiche les détails structurés de l'événement choisi.

        Entrées:
            event (tk.Event | None): Événement de sélection.

        Sortie:
            None: Tour, catégorie et données sont résumés sous la liste.
        """
        index = self._selected_event_index()
        if index is None or not 0 <= index < len(self.filtered_events):
            return
        item = self.filtered_events[index]
        data_text = ", ".join(f"{key}={value}" for key, value in item.data.items())
        suffix = f" • {data_text}" if data_text else ""
        self.detail_label.configure(
            text=(
                f"Événement #{item.sequence} • tour {item.turn_number} • "
                f"{EVENT_LABELS.get(item.event_type, item.event_type)} : "
                f"{item.message}{suffix}"
            )
        )
        self._refresh_navigation()

    def _move_selection(self, delta: int) -> None:
        """Déplace la sélection du journal vers l'avant ou l'arrière.

        Entrées:
            delta (int): Décalage, généralement -1 ou +1.

        Sortie:
            None: La ligne voisine est sélectionnée lorsqu'elle existe.
        """
        index = self._selected_event_index()
        if index is None:
            return
        target = index + delta
        if not 0 <= target < len(self.filtered_events):
            return
        iid = str(target)
        self.event_tree.selection_set(iid)
        self.event_tree.focus(iid)
        self.event_tree.see(iid)
        self._event_selected(None)

    def _previous_event(self) -> None:
        """Sélectionne l'événement précédent du journal global.

        Entrées:
            Aucune.

        Sortie:
            None: La navigation recule d'une ligne si possible.
        """
        self._move_selection(-1)

    def _next_event(self) -> None:
        """Sélectionne l'événement suivant du journal global.

        Entrées:
            Aucune.

        Sortie:
            None: La navigation avance d'une ligne si possible.
        """
        self._move_selection(1)

    def _refresh_navigation(self) -> None:
        """Active les boutons précédent/suivant selon la sélection du journal.

        Entrées:
            Aucune.

        Sortie:
            None: Les états des boutons sont synchronisés.
        """
        index = self._selected_event_index()
        previous = index is not None and index > 0
        next_ = index is not None and index < len(self.filtered_events) - 1
        self.previous_button.state(["!disabled"] if previous else ["disabled"])
        self.next_button.state(["!disabled"] if next_ else ["disabled"])

    def _close(self) -> None:
        """Ferme le panneau et rend la main à la fenêtre de jeu.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback est exécuté après masquage.
        """
        callback = self.on_close
        self.hide()
        if callback is not None:
            callback()
