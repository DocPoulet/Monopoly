"""Panneau intégré d'historique filtrable et de statistiques de partie."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from monopoly.history import GameEvent
from monopoly.statistics import GameStatistics

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
    "trade": "Échanges",
    "bankruptcy": "Faillites",
    "financial": "Financier",
    "free_parking_bonus": "Parc Gratuit",
}


class HistoryOverlay(tk.Frame):
    """Affiche statistiques et journal filtrable sans ouvrir de nouvelle fenêtre.

    Entrées:
        master (tk.Misc): Conteneur parent, généralement ``BoardView``.

    Sortie:
        HistoryOverlay: Panneau masqué hors consultation.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit les compteurs, filtres, navigation et liste d'événements.

        Entrées:
            master (tk.Misc): Conteneur graphique parent.

        Sortie:
            None: Le panneau est créé et masqué.
        """
        super().__init__(
            master,
            background="#E8EEF1",
            highlightbackground="#7E8C95",
            highlightthickness=2,
            padx=12,
            pady=12,
        )
        self.game: Game | None = None
        self.on_close: Callable[[], None] | None = None
        self.filtered_events: list[GameEvent] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        ttk.Label(
            self,
            text="Historique & statistiques",
            font=("Arial", 17, "bold"),
        ).grid(row=0, column=0, sticky="w")

        self.summary_label = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            wraplength=760,
        )
        self.summary_label.grid(row=1, column=0, sticky="ew", pady=(3, 8))

        player_frame = ttk.LabelFrame(self, text="Joueurs", padding=6)
        player_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        columns = (
            "turns",
            "cards",
            "bought",
            "rent_paid",
            "rent_received",
            "buildings",
        )
        self.player_tree = ttk.Treeview(
            player_frame,
            columns=columns,
            show="tree headings",
            height=4,
        )
        self.player_tree.heading("#0", text="Joueur")
        self.player_tree.heading("turns", text="Tours")
        self.player_tree.heading("cards", text="Cartes")
        self.player_tree.heading("bought", text="Achats")
        self.player_tree.heading("rent_paid", text="Loyers payés")
        self.player_tree.heading("rent_received", text="Loyers reçus")
        self.player_tree.heading("buildings", text="Bâtiments")
        self.player_tree.column("#0", width=120)
        for column in columns:
            self.player_tree.column(column, width=90, anchor="center")
        self.player_tree.pack(fill="x")

        controls = ttk.Frame(self)
        controls.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Filtre :").grid(row=0, column=0, sticky="w")
        self.filter_var = tk.StringVar(value="Tous")
        self.filter_combo = ttk.Combobox(
            controls,
            textvariable=self.filter_var,
            state="readonly",
            values=list(EVENT_LABELS.values()),
            width=22,
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

        event_frame = ttk.LabelFrame(self, text="Journal détaillé", padding=6)
        event_frame.grid(row=4, column=0, sticky="nsew")
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
        self.event_tree.column("type", width=130, anchor="center")
        self.event_tree.column("message", width=520)

        scrollbar = ttk.Scrollbar(
            event_frame,
            orient="vertical",
            command=self.event_tree.yview,
        )
        self.event_tree.configure(yscrollcommand=scrollbar.set)
        self.event_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.event_tree.bind("<<TreeviewSelect>>", self._event_selected)

        self.detail_label = ttk.Label(
            self,
            text="",
            style="Muted.TLabel",
            wraplength=760,
            justify="left",
        )
        self.detail_label.grid(row=5, column=0, sticky="ew", pady=(8, 0))

        footer = ttk.Frame(self)
        footer.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(
            footer,
            text="Fermer",
            command=self._close,
        ).pack(side="right")

        self.place_forget()

    def show(self, game: "Game", on_close: Callable[[], None]) -> None:
        """Affiche l'historique courant et recalcule toutes les statistiques.

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
            relwidth=0.92,
            relheight=0.86,
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
        """Reconstruit statistiques, joueurs et événements selon le filtre.

        Entrées:
            Aucune autre que la partie courante.

        Sortie:
            None: Les tableaux affichent les données les plus récentes.
        """
        if self.game is None:
            return

        stats = GameStatistics.from_game(self.game)
        self.summary_label.configure(text=" • ".join(stats.summary_lines()))

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
                ),
            )

        key = self._selected_filter_key()
        events = self.game.history.recent(500)
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
            event (tk.Event | None): Événement de combobox, facultatif en test.

        Sortie:
            None: La liste est reconstruite.
        """
        self.refresh_data()

    def _selected_event_index(self) -> int | None:
        """Retourne l'index de l'événement sélectionné.

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
            None: Tour, catégorie, joueur et données sont résumés sous la liste.
        """
        index = self._selected_event_index()
        if index is None or not 0 <= index < len(self.filtered_events):
            return

        item = self.filtered_events[index]
        data_text = ", ".join(
            f"{key}={value}"
            for key, value in item.data.items()
        )
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
        """Déplace la sélection d'un événement vers l'avant ou l'arrière.

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
        """Sélectionne l'événement précédent.

        Entrées:
            Aucune.

        Sortie:
            None: La navigation recule d'une ligne si possible.
        """
        self._move_selection(-1)

    def _next_event(self) -> None:
        """Sélectionne l'événement suivant.

        Entrées:
            Aucune.

        Sortie:
            None: La navigation avance d'une ligne si possible.
        """
        self._move_selection(1)

    def _refresh_navigation(self) -> None:
        """Active les boutons précédent/suivant selon la position courante.

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
