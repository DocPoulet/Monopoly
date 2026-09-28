"""Affichage graphique interactif du plateau de Monopoly."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

from monopoly.auction import Auction, AuctionResult
from monopoly.building_auction import BuildingAuction, BuildingAuctionResult
from monopoly.cards import DrawnCardEvent
from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property, Railroad, Utility
from monopoly.spaces import (
    ChanceSpace,
    CommunityChestSpace,
    FreeParkingSpace,
    GoSpace,
    GoToJailSpace,
    JailSpace,
    TaxSpace,
)
from .auction_panel import AuctionOverlay
from .building_auction_panel import BuildingAuctionOverlay
from .property_card import PropertyCardOverlay
from .property_manager import PropertyManagerOverlay
from .history_panel import HistoryOverlay
from .landing_build_panel import LandingBuildOverlay
from .end_game_panel import EndGameOverlay
from .rules_panel import RulesSummaryOverlay
from .trade_panel import TradeOverlay
from .card_reveal import CardRevealOverlay
from .pawns import draw_pawn
from .theme import VisualPreferences, theme_palette

if TYPE_CHECKING:
    from monopoly.game import Game


COLOR_GROUPS = {
    "brown": "#8B5A2B",
    "light_blue": "#79CFE8",
    "pink": "#D95FA6",
    "orange": "#F39C12",
    "red": "#E74C3C",
    "yellow": "#F4D03F",
    "green": "#27AE60",
    "dark_blue": "#3156A6",
}

BOARD_ROTATION_DEGREES = 26.0
ISOMETRIC_HEIGHT_RATIO = 0.50
BOARD_THICKNESS = 14.0


PLAYER_COLORS = [
    "#D94343",
    "#3478D4",
    "#2D9B64",
    "#E0912E",
    "#8E5AC7",
    "#188E9E",
]


def board_grid_position(index: int) -> tuple[int, int]:
    """Convertit un index de case Monopoly en coordonnées de grille 11 × 11.

    Entrées:
        index (int): Index de la case compris entre 0 et 39.

    Sortie:
        tuple[int, int]: Couple ``(ligne, colonne)`` correspondant au bord du plateau.

    Lève:
        ValueError: Si l'index ne correspond pas à une case du plateau.
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


def center_deck_rectangles(
    x1: float,
    x2: float,
    center_y: float,
    cell: float,
) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
    """Calcule deux rectangles de cartes entièrement contenus dans le centre du plateau.

    Entrées:
        x1 (float): Bord gauche de la zone centrale.
        x2 (float): Bord droit de la zone centrale.
        center_y (float): Coordonnée verticale du centre du plateau.
        cell (float): Taille d'une case du plateau.

    Sortie:
        tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
            Rectangles ``(x, y, largeur, hauteur)`` pour Caisse puis Chance.
    """
    margin = cell * 0.55
    gap = cell * 0.55
    usable_width = max(cell * 2.0, (x2 - x1) - 2 * margin - gap)
    deck_width = usable_width / 2
    deck_height = cell * 2.15
    deck_y = center_y + cell * 0.12
    left_x = x1 + margin
    right_x = left_x + deck_width + gap
    return (
        (left_x, deck_y, deck_width, deck_height),
        (right_x, deck_y, deck_width, deck_height),
    )



def free_parking_pot_stack_level(amount: int) -> int:
    """Convertit le montant de cagnotte en hauteur visuelle de pile de billets.

    Entrées:
        amount (int): Montant actuel de la cagnotte, en dollars.

    Sortie:
        int: Niveau graphique compris entre zéro et six.
    """
    if amount <= 0:
        return 0
    if amount < 100:
        return 1
    if amount < 250:
        return 2
    if amount < 500:
        return 3
    if amount < 1000:
        return 4
    if amount < 2000:
        return 5
    return 6


class BoardView(ttk.Frame):
    """Affiche le plateau, ses cartes centrales et la fiche d'achat intégrée.

    Entrées:
        master (tk.Misc): Widget parent Tkinter.
        game (Game): Partie dont l'état doit être représenté.

    Sortie:
        BoardView: Vue graphique actualisable du plateau.
    """

    def __init__(
        self,
        master: tk.Misc,
        game: Game,
        on_space_clicked: Callable[[OwnableSpace], None] | None = None,
        visual_preferences: VisualPreferences | None = None,
    ) -> None:
        """Construit le Canvas, le cache de cartes et la fiche de propriété superposée.

        Entrées:
            master (tk.Misc): Conteneur parent.
            game (Game): Partie à dessiner.
            on_space_clicked (Callable | None): Callback de consultation d'un bien.
            visual_preferences (VisualPreferences | None): Style, pions et animations V22.

        Sortie:
            None: Le plateau est prêt à être affiché et redimensionné.
        """
        super().__init__(master, style="Board.TFrame")
        self.game = game
        self.on_space_clicked = on_space_clicked
        self.visual_preferences = visual_preferences or VisualPreferences.default()
        self._board_geometry: tuple[float, float, float] | None = None
        self._perspective_geometry: tuple[float, float, float, float] | None = None
        self._space_polygons: dict[int, tuple[float, ...]] = {}
        self._animated_player_positions: dict[int, tuple[float, float]] = {}
        self._visual_position_overrides: dict[int, int] = {}
        self._pulse_player_id: int | None = None
        self._pulse_factor = 1.0
        self._notice_after_id: str | None = None
        self.last_drawn_cards: dict[str, DrawnCardEvent | None] = {
            "chance": None,
            "community_chest": None,
        }
        self.canvas = tk.Canvas(
            self,
            background=theme_palette(self.visual_preferences)["background"],
            highlightthickness=0,
            width=650,
            height=520,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.notice_label = tk.Label(
            self,
            text="",
            background="#263238",
            foreground="#FFFFFF",
            font=("Arial", 11, "bold"),
            padx=14,
            pady=8,
            relief="raised",
            borderwidth=1,
        )
        self.property_card = PropertyCardOverlay(self)
        self.landing_build_panel = LandingBuildOverlay(self)
        self.auction_panel = AuctionOverlay(self)
        self.building_auction_panel = BuildingAuctionOverlay(self)
        self.trade_panel = TradeOverlay(self)
        self.property_manager = PropertyManagerOverlay(self)
        self.history_panel = HistoryOverlay(self)
        self.end_game_panel = EndGameOverlay(self)
        self.rules_panel = RulesSummaryOverlay(self)
        self.card_reveal = CardRevealOverlay(self)

    def show_notice(self, message: str, duration_ms: int = 1500) -> None:
        """Affiche brièvement un message animé au-dessus du plateau.

        Entrées:
            message (str): Texte compact, généralement une variation de cash.
            duration_ms (int): Durée d'affichage avant disparition automatique.

        Sortie:
            None: Une notification non bloquante apparaît en haut du plateau.
        """
        if not message.strip():
            return
        if self._notice_after_id is not None:
            try:
                self.after_cancel(self._notice_after_id)
            except tk.TclError:
                pass
        self.notice_label.configure(text=message)
        self.notice_label.place(relx=0.5, rely=0.035, anchor="n")
        self.notice_label.lift()
        self._notice_after_id = self.after(duration_ms, self.hide_notice)

    def hide_notice(self) -> None:
        """Masque immédiatement la notification temporaire.

        Entrées:
            Aucune.

        Sortie:
            None: Le bandeau disparaît.
        """
        self.notice_label.place_forget()
        self._notice_after_id = None

    def lock_player_visual_position(self, player_id: int, position: int) -> None:
        """Fige temporairement un pion sur une case pendant une séquence visuelle.

        Entrées:
            player_id (int): Identifiant du joueur concerné.
            position (int): Case logique à conserver à l'écran.

        Sortie:
            None: Les redessins utilisent cette position sans modifier le moteur.
        """
        self._visual_position_overrides[player_id] = position % 40

    def release_player_visual_position(self, player_id: int) -> None:
        """Libère une position visuelle temporaire d'un pion.

        Entrées:
            player_id (int): Identifiant du joueur concerné.

        Sortie:
            None: Le pion reprend la position réelle stockée dans le moteur.
        """
        self._visual_position_overrides.pop(player_id, None)

    def animate_player_arrival(self, player_id: int) -> None:
        """Fait pulser légèrement le pion qui vient de terminer son déplacement.

        Entrées:
            player_id (int): Identifiant du joueur à mettre en évidence.

        Sortie:
            None: Quelques redessins non bloquants accentuent l'arrivée du pion.
        """
        self._pulse_player_id = player_id
        factors = (1.0, 1.45, 1.1, 1.32, 1.0)

        def step(index: int) -> None:
            """Applique une étape de l'animation de pulsation.

            Entrées:
                index (int): Position dans la séquence de facteurs.

            Sortie:
                None: Le plateau est redessiné puis l'étape suivante est planifiée.
            """
            if not self.winfo_exists():
                return
            if index >= len(factors):
                self._pulse_player_id = None
                self._pulse_factor = 1.0
                self.redraw()
                return
            self._pulse_factor = factors[index]
            self.redraw()
            self.after(70, lambda: step(index + 1))

        step(0)

    def set_game(self, game: Game) -> None:
        """Remplace la partie et réinitialise les éléments temporaires de l'affichage.

        Entrées:
            game (Game): Nouvelle partie à représenter.

        Sortie:
            None: Le plateau est réinitialisé puis redessiné.
        """
        self.game = game
        self._pulse_player_id = None
        self._pulse_factor = 1.0
        self._visual_position_overrides.clear()
        self._animated_player_positions.clear()
        self.hide_notice()
        self.last_drawn_cards = {"chance": None, "community_chest": None}
        self.property_card.hide()
        self.landing_build_panel.hide()
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.history_panel.hide()
        self.end_game_panel.hide()
        self.rules_panel.hide()
        self.card_reveal.hide()
        self.redraw()

    def display_drawn_card(self, event: DrawnCardEvent) -> None:
        """Affiche une carte tirée directement dans la zone centrale de son paquet.

        Entrées:
            event (DrawnCardEvent): Carte réellement tirée et appliquée par le moteur.

        Sortie:
            None: Le dernier tirage du paquet est mémorisé et le plateau redessiné.
        """
        if event.deck_name in self.last_drawn_cards:
            self.last_drawn_cards[event.deck_name] = event
            self.redraw()

    def show_card_reveal(
        self,
        event: DrawnCardEvent,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        """Affiche en grand la carte tirée avant de reprendre les décisions du tour.

        Entrées:
            event (DrawnCardEvent): Carte résolue par le moteur.
            on_close (Callable[[], None] | None): Callback après validation visuelle.

        Sortie:
            None: La carte V22 recouvre le plateau sans ouvrir de fenêtre externe.
        """
        self.display_drawn_card(event)
        self.card_reveal.show(event, on_close=on_close)

    def show_purchase_card(
        self,
        player: Player,
        space: OwnableSpace,
        on_buy: Callable[[], None],
        on_auction: Callable[[], None],
    ) -> None:
        """Affiche la fiche d'un bien libre au centre du plateau.

        Entrées:
            player (Player): Joueur qui doit choisir.
            space (OwnableSpace): Bien proposé.
            on_buy (Callable[[], None]): Callback d'achat.
            on_auction (Callable[[], None]): Callback de mise aux enchères.

        Sortie:
            None: La fiche superposée devient visible.
        """
        self.auction_panel.hide()
        self.landing_build_panel.hide()
        self.property_card.show(player, space, on_buy, on_auction)

    def hide_purchase_card(self) -> None:
        """Masque la fiche de propriété intégrée au plateau.

        Entrées:
            Aucune.

        Sortie:
            None: La fiche superposée disparaît.
        """
        self.property_card.hide()


    def show_landing_build(
        self,
        player: Player,
        property_: Property,
        on_buy_houses: Callable[[int], None],
        on_buy_hotel: Callable[[], None],
        on_pass: Callable[[], None],
    ) -> None:
        """Affiche le menu de construction lié au dernier atterrissage.

        Entrées:
            player (Player): Joueur ayant atterri sur son terrain.
            property_ (Property): Terrain concerné.
            on_buy_houses (Callable[[int], None]): Achat groupé de maisons.
            on_buy_hotel (Callable[[], None]): Achat d'un hôtel.
            on_pass (Callable[[], None]): Renoncement à construire.

        Sortie:
            None: Le menu apparaît au centre du plateau.
        """
        self.property_card.hide()
        self.landing_build_panel.hide()
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.history_panel.hide()
        self.rules_panel.hide()
        self.end_game_panel.hide()
        self.landing_build_panel.show(
            self.game,
            player,
            property_,
            on_buy_houses,
            on_buy_hotel,
            on_pass,
        )

    def hide_landing_build(self) -> None:
        """Masque le menu de construction après atterrissage.

        Entrées:
            Aucune.

        Sortie:
            None: La superposition disparaît.
        """
        self.landing_build_panel.hide()

    def show_auction(
        self,
        auction: Auction,
        on_finished: Callable[[AuctionResult], None],
    ) -> None:
        """Affiche l'enchère au centre du plateau à la place de la fiche d'achat.

        Entrées:
            auction (Auction): Enchère métier à piloter.
            on_finished (Callable[[AuctionResult], None]): Callback appelé à la clôture.

        Sortie:
            None: La fiche du bien reste visible à gauche et l'enchère apparaît à droite.
        """
        self.property_card.show_for_auction(auction.space, relx=0.30, width=300)
        self.auction_panel.show(auction, on_finished)
        self.property_card.lift()
        self.auction_panel.lift()

    def hide_auction(self) -> None:
        """Masque le panneau d'enchère intégré.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau d'enchère disparaît du plateau.
        """
        self.auction_panel.hide()
        if self.property_card.player is None:
            self.property_card.hide()

    def show_trade(
        self,
        initiator: Player,
        on_finished: Callable[[object], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Affiche le panneau d'échange intégré au centre du plateau.

        Entrées:
            initiator (Player): Joueur qui ouvre l'échange.
            on_finished (Callable[[object], None]): Callback recevant le résultat réussi.
            on_cancel (Callable[[], None]): Callback déclenché si l'échange est annulé.

        Sortie:
            None: Les autres superpositions sont masquées et l'échange apparaît.
        """
        self.property_card.hide()
        self.auction_panel.hide()
        self.trade_panel.show(
            self.game,
            initiator,
            on_finished=on_finished,
            on_cancel=on_cancel,
        )

    def hide_trade(self) -> None:
        """Masque le panneau d'échange intégré.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît et oublie son état temporaire.
        """
        self.trade_panel.hide()

    def show_property_manager(
        self,
        player: Player,
        on_close: Callable[[bool], None],
        on_changed: Callable[[], None],
        on_building_auction: Callable[[str, Property], None],
    ) -> None:
        """Affiche la gestion des propriétés directement au centre du plateau.

        Entrées:
            player (Player): Joueur dont le patrimoine doit être géré.
            on_close (Callable[[bool], None]): Callback appelé à la fermeture.
            on_changed (Callable[[], None]): Callback après une modification réussie.
            on_building_auction (Callable[[str, Property], None]): Callback de pénurie.

        Sortie:
            None: Les autres superpositions sont masquées et le gestionnaire apparaît.
        """
        self.property_card.hide()
        self.landing_build_panel.hide()
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.show(
            self.game,
            player,
            on_close=on_close,
            on_changed=on_changed,
            on_building_auction=on_building_auction,
        )

    def hide_property_manager(self) -> None:
        """Masque le panneau intégré de gestion des propriétés.

        Entrées:
            Aucune.

        Sortie:
            None: Le gestionnaire disparaît du plateau.
        """
        self.property_manager.hide()

    def show_building_auction(
        self,
        auction: BuildingAuction,
        on_finished: Callable[[BuildingAuctionResult], None],
    ) -> None:
        """Affiche une enchère de maison ou d'hôtel au centre du plateau.

        Entrées:
            auction (BuildingAuction): Enchère métier à piloter.
            on_finished (Callable[[BuildingAuctionResult], None]): Callback final.

        Sortie:
            None: Les autres superpositions disparaissent pendant l'enchère.
        """
        self.property_card.hide()
        self.landing_build_panel.hide()
        self.auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.building_auction_panel.show(auction, on_finished)

    def hide_building_auction(self) -> None:
        """Masque le panneau d'enchère de bâtiment.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît et oublie son état temporaire.
        """
        self.building_auction_panel.hide()

    def show_history(
        self,
        on_close: Callable[[], None],
    ) -> None:
        """Affiche historique et statistiques au centre du plateau.

        Entrées:
            on_close (Callable[[], None]): Callback exécuté à la fermeture.

        Sortie:
            None: Les autres superpositions sont masquées et le panneau apparaît.
        """
        self.property_card.hide()
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.history_panel.show(self.game, on_close)

    def hide_history(self) -> None:
        """Masque le panneau d'historique et statistiques.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît du plateau.
        """
        self.history_panel.hide()

    def show_space_info(
        self,
        space: OwnableSpace,
        on_close: Callable[[], None],
    ) -> None:
        """Affiche la fiche de consultation d'un bien cliqué.

        Entrées:
            space (OwnableSpace): Bien à consulter.
            on_close (Callable[[], None]): Callback de fermeture.

        Sortie:
            None: La fiche apparaît en lecture seule au centre du plateau.
        """
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.history_panel.hide()
        self.end_game_panel.hide()
        self.property_card.show_info(space, on_close)

    def show_end_game(
        self,
        on_history: Callable[[], None],
        on_new_game: Callable[[], None],
        abandoned: bool = False,
    ) -> None:
        """Affiche le bilan final intégré de la partie.

        Entrées:
            on_history (Callable[[], None]): Callback ouvrant l'historique.
            on_new_game (Callable[[], None]): Callback retournant au menu.
            abandoned (bool): Affiche un bilan d'abandon plutôt qu'une victoire.

        Sortie:
            None: Le panneau final masque les autres superpositions.
        """
        self.property_card.hide()
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.history_panel.hide()
        self.end_game_panel.show(
            self.game,
            on_history,
            on_new_game,
            abandoned=abandoned,
        )

    def hide_end_game(self) -> None:
        """Masque le panneau final.

        Entrées:
            Aucune.

        Sortie:
            None: Le bilan final disparaît.
        """
        self.end_game_panel.hide()

    def space_at_canvas_point(
        self,
        x: float,
        y: float,
    ) -> OwnableSpace | None:
        """Identifie le bien achetable situé sous une coordonnée du Canvas.

        Entrées:
            x (float): Coordonnée horizontale du clic.
            y (float): Coordonnée verticale du clic.

        Sortie:
            OwnableSpace | None: Bien correspondant à la case, sinon ``None``.
        """
        polygons = getattr(self, "_space_polygons", {})
        if polygons:
            for index, polygon in polygons.items():
                if self._point_in_polygon(x, y, polygon):
                    space = self.game.board[index]
                    return space if isinstance(space, OwnableSpace) else None
            return None

        # Compatibilité avec les anciens tests et vues rectangulaires.
        if self._board_geometry is None:
            return None
        offset_x, offset_y, cell = self._board_geometry
        col = int((x - offset_x) // cell)
        row = int((y - offset_y) // cell)
        if not 0 <= row <= 10 or not 0 <= col <= 10:
            return None
        if 1 <= row <= 9 and 1 <= col <= 9:
            return None
        for index, space in enumerate(self.game.board.spaces):
            grid_row, grid_col = board_grid_position(index)
            if grid_row == row and grid_col == col and isinstance(space, OwnableSpace):
                return space
        return None

    @staticmethod
    def _point_in_polygon(x: float, y: float, polygon: tuple[float, ...]) -> bool:
        """Teste l'appartenance d'un point à un quadrilatère/polygone Canvas.

        Entrées:
            x (float): Coordonnée horizontale.
            y (float): Coordonnée verticale.
            polygon (tuple[float, ...]): Suite ``x1, y1, x2, y2, ...``.

        Sortie:
            bool: ``True`` lorsque le point est à l'intérieur.
        """
        points = list(zip(polygon[0::2], polygon[1::2]))
        inside = False
        j = len(points) - 1
        for i, (xi, yi) in enumerate(points):
            xj, yj = points[j]
            intersects = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
            )
            if intersects:
                inside = not inside
            j = i
        return inside

    def _on_canvas_click(self, event: tk.Event) -> None:
        """Transmet au contrôleur un clic effectué sur une case achetable.

        Entrées:
            event (tk.Event): Événement souris contenant les coordonnées du Canvas.

        Sortie:
            None: Le callback reçoit le bien cliqué lorsqu'il existe.
        """
        if self.on_space_clicked is None:
            return
        space = self.space_at_canvas_point(event.x, event.y)
        if space is not None:
            self.on_space_clicked(space)


    def show_rules(
        self,
        on_close: Callable[[], None],
    ) -> None:
        """Affiche les règles actives et l'audit au centre du plateau.

        Entrées:
            on_close (Callable[[], None]): Callback exécuté à la fermeture.

        Sortie:
            None: Les autres superpositions sont masquées et le panneau apparaît.
        """
        self.property_card.hide()
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.history_panel.hide()
        self.end_game_panel.hide()
        self.rules_panel.show(self.game, on_close)

    def hide_rules(self) -> None:
        """Masque le panneau de règles.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît du plateau.
        """
        self.rules_panel.hide()

    def _on_resize(self, event: tk.Event) -> None:
        """Redessine le plateau lorsque la taille du Canvas change.

        Entrées:
            event (tk.Event): Événement Tkinter de redimensionnement.

        Sortie:
            None: Le dessin est recalculé à la nouvelle échelle.
        """
        self.redraw()

    def redraw(self) -> None:
        """Redessine le plateau V22.2 comme un diorama isométrique flottant.

        Entrées:
            Aucune autre que l'état courant de la vue et de la partie.

        Sortie:
            None: Le Canvas est entièrement recalculé à la taille disponible.
        """
        self.canvas.delete("all")
        self._space_polygons.clear()
        width = max(self.canvas.winfo_width(), 260)
        height = max(self.canvas.winfo_height(), 220)

        # La scène garde volontairement de grands bords libres : les cartes joueur
        # flottantes occupent ces zones, comme dans un jeu de plateau numérique.
        board_width = min(width * 0.72, height * 1.56)
        board_height = board_width * ISOMETRIC_HEIGHT_RATIO
        center_x = width / 2
        top = (height - board_height) / 2 - min(14.0, height * 0.02)
        cell = board_width / 11
        self._board_geometry = (center_x - board_width / 2, top, cell)
        self._perspective_geometry = (center_x, top, board_width, board_height)
        self.canvas.configure(background=theme_palette(self.visual_preferences)["background"])

        outer = self._grid_polygon(0, 0, 11, 11)
        pts = list(zip(outer[0::2], outer[1::2]))
        top_pt, right_pt, bottom_pt, left_pt = pts
        thickness = max(7.0, min(BOARD_THICKNESS, cell * 0.24))

        shadow = tuple(
            value + (10 if index % 2 == 0 else thickness + 12)
            for index, value in enumerate(outer)
        )
        self.canvas.create_polygon(*shadow, fill="#707979", outline="")

        # Deux chants visibles donnent au plateau une vraie épaisseur de diorama.
        lower_right = (right_pt[0], right_pt[1] + thickness)
        lower_bottom = (bottom_pt[0], bottom_pt[1] + thickness)
        lower_left = (left_pt[0], left_pt[1] + thickness)
        self.canvas.create_polygon(
            right_pt[0], right_pt[1],
            bottom_pt[0], bottom_pt[1],
            lower_bottom[0], lower_bottom[1],
            lower_right[0], lower_right[1],
            fill=self._shade_color(self.visual_preferences.style.board_edge, 0.82),
            outline=self._shade_color(self.visual_preferences.style.board_edge, 0.70),
            width=1,
        )
        self.canvas.create_polygon(
            bottom_pt[0], bottom_pt[1],
            left_pt[0], left_pt[1],
            lower_left[0], lower_left[1],
            lower_bottom[0], lower_bottom[1],
            fill=self._shade_color(self.visual_preferences.style.board_edge, 0.68),
            outline=self._shade_color(self.visual_preferences.style.board_edge, 0.58),
            width=1,
        )
        self.canvas.create_polygon(
            *outer,
            fill=self.visual_preferences.style.board_surface,
            outline=self.visual_preferences.style.board_edge,
            width=3,
        )
        self._draw_center(center_x - board_width / 2, top, cell)

        for index, space in enumerate(self.game.board.spaces):
            row, col = board_grid_position(index)
            self._draw_space(space, row, col, center_x - board_width / 2, top, cell)

        for player in self.game.players:
            if not player.bankrupt:
                self._draw_player(player, center_x - board_width / 2, top, cell)

    @staticmethod
    def _shade_color(color: str, factor: float) -> str:
        """Assombrit ou éclaircit une couleur hexadécimale pour créer un relief.

        Entrées:
            color (str): Couleur ``#RRGGBB`` de référence.
            factor (float): Multiplicateur appliqué aux composantes RVB.

        Sortie:
            str: Couleur hexadécimale transformée, avec repli neutre si nécessaire.
        """
        try:
            raw = color.lstrip("#")
            red = min(255, max(0, round(int(raw[0:2], 16) * factor)))
            green = min(255, max(0, round(int(raw[2:4], 16) * factor)))
            blue = min(255, max(0, round(int(raw[4:6], 16) * factor)))
            return f"#{red:02x}{green:02x}{blue:02x}"
        except (ValueError, IndexError):
            return "#555555"

    def _project_grid_point(self, gx: float, gy: float) -> tuple[float, float]:
        """Projette un point de grille dans le losange isométrique V22.2.

        Entrées:
            gx (float): Abscisse logique de 0 à 11.
            gy (float): Ordonnée logique de 0 à 11.

        Sortie:
            tuple[float, float]: Coordonnées Canvas dans la scène isométrique.
        """
        if self._perspective_geometry is None:
            if self._board_geometry is None:
                return gx, gy
            left, top, cell = self._board_geometry
            return left + gx * cell, top + gy * cell
        center_x, top, board_width, board_height = self._perspective_geometry
        horizontal_unit = board_width / 22.0
        vertical_unit = board_height / 22.0
        x = center_x + (gx - gy) * horizontal_unit
        y = top + (gx + gy) * vertical_unit
        return x, y

    def _space_text_angle(self, row: int, col: int) -> float:
        """Retourne l'angle de base lisible du texte d'une case isométrique.

        Entrées:
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            float: Angle Canvas en degrés, aligné sur le côté principal de la case.
        """
        if self._perspective_geometry is None:
            return 0.0
        _center_x, _top, board_width, board_height = self._perspective_geometry
        angle = math.degrees(math.atan2(board_height, board_width))
        return angle if row in {0, 10} else -angle

    def _space_name_angle(self, index: int, row: int, col: int) -> float:
        """Retourne l'orientation du nom parallèle au bord coloré de la case.

        Entrées:
            index (int): Index Monopoly de la case.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            float: Angle du nom. Les coins restent à 0° et les autres noms
            suivent exactement l'axe visuel du bord de leur tuile isométrique.
        """
        if index in {0, 10, 20, 30}:
            return 0.0
        return -self._space_text_angle(row, col)

    def _space_content_angle(self, index: int, row: int, col: int) -> float:
        """Retourne l'angle général du contenu visuel d'une case.

        Entrées:
            index (int): Index Monopoly de la case.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            float: Zéro degré pour les quatre coins, sinon l'angle isométrique du côté.
        """
        if index in {0, 10, 20, 30}:
            return 0.0
        return self._space_text_angle(row, col)

    def _space_icon_angle(
        self,
        space: object,
        index: int,
        row: int,
        col: int,
    ) -> float:
        """Retourne l'orientation du pictogramme principal d'une case.

        Entrées:
            space (object): Case dont le pictogramme va être affiché.
            index (int): Index Monopoly de la case.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            float: GO et les autres coins restent à 0° écran.
        """
        if isinstance(space, GoSpace) and index == 0:
            return 0.0
        return self._space_content_angle(index, row, col)

    @staticmethod
    def _space_display_name(space: object) -> str:
        """Retourne le nom réellement affiché dans la tuile.

        Entrées:
            space (object): Case dont le nom doit être dessiné.

        Sortie:
            str: Chaîne vide pour Départ, sinon le nom configuré de la case.
        """
        if isinstance(space, GoSpace):
            return ""
        return str(getattr(space, "name", ""))

    def _space_price_angle(self, index: int, row: int, col: int) -> float:
        """Retourne la rotation des prix décalée d'un côté du plateau.

        Entrées:
            index (int): Index Monopoly du bien.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            float: Angle appliqué au prix. Il reprend le sens du côté précédent
            selon le cycle 1–9 → 11–19 → 21–29 → 31–39 → 1–9.
        """
        if index in {0, 10, 20, 30}:
            return 0.0
        return -self._space_text_angle(row, col)

    def _grid_polygon(self, col: float, row: float, width: float = 1.0, height: float = 1.0) -> tuple[float, ...]:
        """Construit le quadrilatère projeté d'une zone logique du plateau.

        Entrées:
            col (float): Colonne logique de départ.
            row (float): Ligne logique de départ.
            width (float): Largeur logique en cellules.
            height (float): Hauteur logique en cellules.

        Sortie:
            tuple[float, ...]: Huit coordonnées compatibles ``create_polygon``.
        """
        points = (
            self._project_grid_point(col, row),
            self._project_grid_point(col + width, row),
            self._project_grid_point(col + width, row + height),
            self._project_grid_point(col, row + height),
        )
        return tuple(value for point in points for value in point)

    @staticmethod
    def _polygon_center(polygon: tuple[float, ...]) -> tuple[float, float]:
        """Calcule le centre moyen d'un quadrilatère projeté.

        Entrées:
            polygon (tuple[float, ...]): Coordonnées du polygone.

        Sortie:
            tuple[float, float]: Centre horizontal et vertical.
        """
        xs = polygon[0::2]
        ys = polygon[1::2]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def animate_player_move(
        self,
        player_id: int,
        from_position: int,
        to_position: int,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        """Anime un déplacement logique case par case sans modifier le moteur.

        Entrées:
            player_id (int): Joueur à animer.
            from_position (int): Case visuelle de départ.
            to_position (int): Case déjà atteinte dans le moteur.
            on_complete (Callable[[], None] | None): Callback déclenché après l'arrivée.

        Sortie:
            None: Le pion interpole plusieurs cases puis déclenche la suite visuelle.
        """
        speed = self.visual_preferences.animation_speed
        if speed == "off" or from_position == to_position:
            self.release_player_visual_position(player_id)
            self.redraw()
            self.animate_player_arrival(player_id)
            if on_complete is not None:
                self.after_idle(on_complete)
            return
        forward = (to_position - from_position) % 40
        backward = (from_position - to_position) % 40
        if backward <= 3:
            direction, steps = -1, backward
        elif forward <= 12:
            direction, steps = 1, forward
        else:
            self.release_player_visual_position(player_id)
            self.redraw()
            self.animate_player_arrival(player_id)
            if on_complete is not None:
                self.after_idle(on_complete)
            return
        path = [(from_position + direction * step) % 40 for step in range(steps + 1)]
        frames_per_segment = 4 if speed == "normal" else 2
        delay = 28 if speed == "normal" else 16
        self._animate_path_frame(
            player_id,
            path,
            0,
            0,
            frames_per_segment,
            delay,
            on_complete,
        )

    def _animate_path_frame(
        self,
        player_id: int,
        path: list[int],
        segment: int,
        frame: int,
        frames_per_segment: int,
        delay: int,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        """Dessine une frame interpolée d'un déplacement de pion.

        Entrées:
            player_id (int): Joueur animé.
            path (list[int]): Suite de cases à parcourir.
            segment (int): Segment courant dans ``path``.
            frame (int): Frame d'interpolation du segment.
            frames_per_segment (int): Nombre de frames par case.
            delay (int): Délai en millisecondes entre deux frames.
            on_complete (Callable[[], None] | None): Callback appelé après la dernière frame.

        Sortie:
            None: La prochaine frame est planifiée jusqu'à l'arrivée.
        """
        if segment >= len(path) - 1 or not self.winfo_exists():
            self._animated_player_positions.pop(player_id, None)
            self.release_player_visual_position(player_id)
            self.redraw()
            self.animate_player_arrival(player_id)
            if on_complete is not None and self.winfo_exists():
                self.after_idle(on_complete)
            return
        start_row, start_col = board_grid_position(path[segment])
        end_row, end_col = board_grid_position(path[segment + 1])
        sx, sy = self._project_grid_point(start_col + 0.5, start_row + 0.5)
        ex, ey = self._project_grid_point(end_col + 0.5, end_row + 0.5)
        ratio = (frame + 1) / frames_per_segment
        self._animated_player_positions[player_id] = (sx + (ex - sx) * ratio, sy + (ey - sy) * ratio)
        self.redraw()
        next_frame = frame + 1
        next_segment = segment
        if next_frame >= frames_per_segment:
            next_frame = 0
            next_segment += 1
        self.after(
            delay,
            lambda: self._animate_path_frame(
                player_id,
                path,
                next_segment,
                next_frame,
                frames_per_segment,
                delay,
                on_complete,
            ),
        )

    def _draw_center(self, offset_x: float, offset_y: float, cell: float) -> None:
        """Dessine un centre volontairement épuré dans le diorama isométrique.

        Entrées:
            offset_x (float): Conservé pour compatibilité de signature.
            offset_y (float): Conservé pour compatibilité de signature.
            cell (float): Taille logique de référence avant projection.

        Sortie:
            None: Centre, terrain décoratif, titre et informations discrètes sont dessinés.
        """
        polygon = self._grid_polygon(1, 1, 9, 9)
        self.canvas.create_polygon(
            *polygon,
            fill=self.visual_preferences.style.board_center,
            outline=self._shade_color(self.visual_preferences.style.board_edge, 1.12),
            width=2,
        )

        # Deux lignes discrètes donnent un effet de terrain/diorama sans charger le centre.
        for offset in (3.7, 7.3):
            p1 = self._project_grid_point(1.7, offset)
            p2 = self._project_grid_point(9.3, offset)
            self.canvas.create_line(
                p1[0], p1[1], p2[0], p2[1],
                fill=self._shade_color(self.visual_preferences.style.board_center, 0.93),
                width=1,
            )
        for offset in (3.7, 7.3):
            p1 = self._project_grid_point(offset, 1.7)
            p2 = self._project_grid_point(offset, 9.3)
            self.canvas.create_line(
                p1[0], p1[1], p2[0], p2[1],
                fill=self._shade_color(self.visual_preferences.style.board_center, 0.93),
                width=1,
            )

        center_x, center_y = self._project_grid_point(5.5, 5.5)
        board_name = getattr(
            getattr(self.game, "board_config", None),
            "name",
            "Plateau classique",
        )
        self.canvas.create_text(
            center_x,
            center_y - cell * 0.18,
            text=str(board_name).upper(),
            font=("Arial", max(9, int(cell * 0.13)), "bold"),
            fill=self._shade_color(self.visual_preferences.style.board_edge, 0.95),
        )
        self.canvas.create_text(
            center_x,
            center_y + cell * 0.08,
            text=f"TOUR {self.game.turn_number}",
            font=("Arial", max(8, int(cell * 0.10)), "bold"),
            fill=self.visual_preferences.style.accent,
        )

        if self.game.options.free_parking_card_pot:
            self._draw_free_parking_pot(center_x, center_y + cell * 0.46, cell * 0.78)

        # Les paquets restent matérialisés mais beaucoup plus discrets que dans V22.1.
        self._draw_iso_deck(2.2, 4.6, 1.25, 2.0, "COMMUNAUTÉ", "#4F95C8", "▤", self.last_drawn_cards["community_chest"])
        self._draw_iso_deck(7.55, 4.6, 1.25, 2.0, "CHANCE", "#E59B31", "?", self.last_drawn_cards["chance"])

    def _draw_iso_deck(
        self,
        col: float,
        row: float,
        width: float,
        height: float,
        title: str,
        color: str,
        icon: str,
        event: DrawnCardEvent | None = None,
    ) -> None:
        """Dessine un petit paquet projeté directement sur le centre du plateau.

        Entrées:
            col (float): Colonne logique du paquet.
            row (float): Ligne logique du paquet.
            width (float): Largeur logique en cellules.
            height (float): Hauteur logique en cellules.
            title (str): Nom court du paquet.
            color (str): Couleur d'identité.
            icon (str): Symbole central lorsqu'aucune carte n'a encore été tirée.
            event (DrawnCardEvent | None): Dernier tirage du paquet, s'il existe.

        Sortie:
            None: Un paquet minimaliste suit la perspective du plateau.
        """
        shadow = self._grid_polygon(col + 0.10, row + 0.10, width, height)
        card = self._grid_polygon(col, row, width, height)
        self.canvas.create_polygon(*shadow, fill="#7B8581", outline="")
        self.canvas.create_polygon(*card, fill="#FFFDF8", outline=color, width=2)
        center_x, center_y = self._polygon_center(card)
        display_icon = "✓" if event is not None else icon
        self.canvas.create_text(
            center_x,
            center_y - 4,
            text=display_icon,
            font=("Arial", 12, "bold"),
            fill=color,
        )
        self.canvas.create_text(
            center_x,
            center_y + 10,
            text="DERNIÈRE" if event is not None else title,
            font=("Arial", 5, "bold"),
            fill=color,
        )

    def _draw_free_parking_pot(
        self,
        center_x: float,
        center_y: float,
        cell: float,
    ) -> None:
        """Dessine une pile de billets dont la hauteur dépend de la cagnotte.

        Entrées:
            center_x (float): Centre horizontal de la zone intérieure.
            center_y (float): Centre vertical de la zone intérieure.
            cell (float): Taille d'une case utilisée comme unité graphique.

        Sortie:
            None: Une pile graduée et son montant apparaissent au milieu du plateau.
        """
        amount = max(0, int(self.game.free_parking_pot))
        level = free_parking_pot_stack_level(amount)

        base_y = center_y - cell * 0.16
        bill_w = cell * 0.86
        bill_h = cell * 0.23
        step = cell * 0.075

        self.canvas.create_text(
            center_x,
            center_y - cell * 0.72,
            text="CAGNOTTE PARC GRATUIT",
            font=("Arial", max(7, int(cell * 0.12)), "bold"),
            fill="#2E5D3B",
        )

        if level == 0:
            self.canvas.create_rectangle(
                center_x - bill_w / 2,
                base_y - bill_h / 2,
                center_x + bill_w / 2,
                base_y + bill_h / 2,
                fill="#E5EFE7",
                outline="#7EA287",
                width=2,
            )
            self.canvas.create_text(
                center_x,
                base_y,
                text="$",
                font=("Arial", max(10, int(cell * 0.18)), "bold"),
                fill="#88A990",
            )
        else:
            for index in range(level):
                y = base_y - index * step
                x_shift = (index % 2) * cell * 0.045
                self.canvas.create_rectangle(
                    center_x - bill_w / 2 + x_shift,
                    y - bill_h / 2,
                    center_x + bill_w / 2 + x_shift,
                    y + bill_h / 2,
                    fill="#CFE8D2",
                    outline="#3D7A4A",
                    width=2,
                )
                self.canvas.create_text(
                    center_x + x_shift,
                    y,
                    text="$",
                    font=("Arial", max(9, int(cell * 0.15)), "bold"),
                    fill="#2E6D3C",
                )

        self.canvas.create_text(
            center_x,
            center_y + cell * 0.02,
            text=f"{amount} $",
            font=("Arial", max(10, int(cell * 0.18)), "bold"),
            fill="#263238",
        )

    def _draw_deck(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str,
        color: str,
        icon: str,
        event: DrawnCardEvent | None,
    ) -> None:
        """Dessine un paquet ou la dernière carte tirée dans son emplacement central.

        Entrées:
            x (float): Coordonnée gauche.
            y (float): Coordonnée haute.
            width (float): Largeur de la zone.
            height (float): Hauteur de la zone.
            title (str): Nom du paquet.
            color (str): Couleur d'identité du paquet.
            icon (str): Icône lorsque rien n'a encore été tiré.
            event (DrawnCardEvent | None): Dernier tirage à afficher, s'il existe.

        Sortie:
            None: Une carte stylisée est ajoutée au Canvas.
        """
        self.canvas.create_rectangle(
            x + 5, y + 6, x + width + 5, y + height + 6,
            fill="#AEB9B6", outline="",
        )
        self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill="#FFFDF8", outline=color, width=3,
        )
        band_h = height * 0.23
        self.canvas.create_rectangle(
            x, y, x + width, y + band_h,
            fill=color, outline="",
        )
        self.canvas.create_text(
            x + width / 2,
            y + band_h / 2,
            text=title,
            fill="#FFFFFF",
            font=("Arial", max(7, int(height * 0.075)), "bold"),
        )

        if event is None:
            self.canvas.create_text(
                x + width / 2,
                y + height * 0.62,
                text=icon,
                fill=color,
                font=("Arial", max(24, int(height * 0.30)), "bold"),
            )
            self.canvas.create_text(
                x + width / 2,
                y + height * 0.88,
                text="Dernière carte tirée",
                fill="#8A949B",
                font=("Arial", max(6, int(height * 0.05))),
            )
            return

        text = getattr(event.card, "text", event.message)
        self.canvas.create_text(
            x + width / 2,
            y + band_h + (height - band_h) * 0.47,
            text=text,
            width=width * 0.82,
            justify="center",
            fill="#263238",
            font=("Arial", max(7, int(height * 0.065)), "bold"),
        )
        self.canvas.create_text(
            x + width / 2,
            y + height * 0.91,
            text="Dernier tirage",
            fill=color,
            font=("Arial", max(6, int(height * 0.045)), "bold"),
        )

    def _space_fill(self, space: object) -> str:
        """Choisit une couleur de fond légère selon le type d'une case.

        Entrées:
            space (object): Case du plateau.

        Sortie:
            str: Couleur hexadécimale utilisée comme fond de la case.
        """
        if isinstance(space, OwnableSpace) and space.owner is not None:
            owner_color = PLAYER_COLORS[
                space.owner.player_id % len(PLAYER_COLORS)
            ]
            return (
                self._shade_color(owner_color, 0.58)
                if space.mortgaged
                else owner_color
            )
        if isinstance(space, ChanceSpace):
            return "#FFF0D7"
        if isinstance(space, CommunityChestSpace):
            return "#E2F0FB"
        if isinstance(space, GoToJailSpace):
            return "#F8DFDF"
        if isinstance(space, JailSpace):
            return "#ECE6DF"
        if isinstance(space, FreeParkingSpace):
            return "#FFF4D6"
        if isinstance(space, TaxSpace):
            return "#F6E6E6"
        if isinstance(space, GoSpace):
            return "#E3F4E8"
        return "#FCFCF7"

    def _draw_space(
        self,
        space: object,
        row: int,
        col: int,
        offset_x: float,
        offset_y: float,
        cell: float,
    ) -> None:
        """Dessine une case projetée avec icône, bande de couleur et état financier.

        Entrées:
            space (object): Case du plateau à afficher.
            row (int): Ligne logique.
            col (int): Colonne logique.
            offset_x (float): Compatibilité de signature.
            offset_y (float): Compatibilité de signature.
            cell (float): Taille logique de référence.

        Sortie:
            None: La case V22 est dessinée et mémorisée pour le hit-test.
        """
        polygon = self._grid_polygon(col, row)
        index = int(getattr(space, "index", len(self._space_polygons)))
        self._space_polygons[index] = polygon
        self.canvas.create_polygon(
            *polygon,
            fill=self._space_fill(space),
            outline=self.visual_preferences.style.board_edge,
            width=1,
        )
        self._draw_color_band_polygon(space, polygon, row, col)
        xs = polygon[0::2]
        ys = polygon[1::2]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        center_x, center_y = self._polygon_center(polygon)
        angle = self._space_content_angle(index, row, col)
        icon_angle = self._space_icon_angle(space, index, row, col)
        name_angle = (
            self._space_name_angle(index, row, col)
            if isinstance(space, Property)
            else angle
        )
        if isinstance(space, (Railroad, Utility)):
            self._draw_case_landmark(space, row, col, cell)
        label_x, label_y = self._space_label_position(index, row, col)
        icon_x, icon_y = self._space_icon_position(index, row, col)
        foreground = self._space_foreground(space)
        icon = "" if isinstance(space, (Railroad, Utility)) else self._space_icon(space)
        if icon:
            self.canvas.create_text(
                icon_x,
                icon_y,
                text=icon,
                font=("Arial", max(7, int(cell * 0.105)), "bold"),
                fill=foreground,
                angle=icon_angle,
            )
        raw_name = self._space_display_name(space)
        name = self._short_name(raw_name) if raw_name else ""
        if name:
            self.canvas.create_text(
                label_x,
                label_y,
                text=name,
                justify="center",
                font=("Arial", max(5, int(cell * 0.054)), "bold"),
                fill=foreground,
                angle=name_angle,
            )
        if self.visual_preferences.show_case_numbers:
            number_x, number_y = self._space_number_position(polygon, cell)
            self.canvas.create_text(
                number_x,
                number_y,
                text=str(getattr(space, "index", "")),
                anchor="center",
                font=("Arial", max(6, int(cell * 0.064)), "bold"),
                fill=self._shade_color(self.visual_preferences.style.board_edge, 0.82),
                tags=("case_number",),
            )
        if isinstance(space, OwnableSpace):
            self._draw_property_state(space, polygon, row, col, cell)

    def _space_label_position(
        self,
        index: int,
        row: int,
        col: int,
    ) -> tuple[float, float]:
        """Place le nom près de la bande de groupe selon l'orientation de la case.

        Entrées:
            index (int): Index Monopoly de la case.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            tuple[float, float]: Coordonnées Canvas du libellé principal.
        """
        reversed_side = 11 <= index <= 29
        if row == 10:
            return self._project_grid_point(col + 0.50, row + 0.33)
        if row == 0:
            y = row + (0.29 if reversed_side else 0.67)
            return self._project_grid_point(col + 0.50, y)
        if col == 0:
            x = col + (0.29 if reversed_side else 0.67)
            return self._project_grid_point(x, row + 0.50)
        return self._project_grid_point(col + 0.33, row + 0.50)

    def _space_icon_position(
        self,
        index: int,
        row: int,
        col: int,
    ) -> tuple[float, float]:
        """Place l'icône à l'opposé du nom pour équilibrer la tuile.

        Entrées:
            index (int): Index Monopoly de la case.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            tuple[float, float]: Coordonnées Canvas de l'icône.
        """
        reversed_side = 11 <= index <= 29
        if row == 10:
            return self._project_grid_point(col + 0.50, row + 0.66)
        if row == 0:
            y = row + (0.68 if reversed_side else 0.32)
            return self._project_grid_point(col + 0.50, y)
        if col == 0:
            x = col + (0.68 if reversed_side else 0.32)
            return self._project_grid_point(x, row + 0.50)
        return self._project_grid_point(col + 0.66, row + 0.50)

    def _space_number_position(
        self,
        polygon: tuple[float, ...],
        cell: float,
    ) -> tuple[float, float]:
        """Place le numéro au-delà du bord extérieur réel de la tuile.

        Entrées:
            polygon (tuple[float, ...]): Polygone projeté de la case.
            cell (float): Taille logique servant à doser l'écart extérieur.

        Sortie:
            tuple[float, float]: Position Canvas extérieure formant une couronne autour du plateau.
        """
        points = list(zip(polygon[0::2], polygon[1::2]))
        board_x, board_y = self._project_grid_point(5.5, 5.5)
        edges = [
            (points[index], points[(index + 1) % len(points)])
            for index in range(len(points))
        ]
        midpoint = max(
            (
                ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                for a, b in edges
            ),
            key=lambda point: math.hypot(point[0] - board_x, point[1] - board_y),
        )
        dx = midpoint[0] - board_x
        dy = midpoint[1] - board_y
        distance = math.hypot(dx, dy) or 1.0
        gap = max(20.0, cell * 0.24)
        return (
            midpoint[0] + dx / distance * gap,
            midpoint[1] + dy / distance * gap,
        )

    def _space_foreground(self, space: object) -> str:
        """Choisit une couleur de texte lisible sur le fond courant de la case.

        Entrées:
            space (object): Case dont le fond a déjà été déterminé.

        Sortie:
            str: Blanc sur une propriété possédée, sombre dans les autres cas.
        """
        if isinstance(space, OwnableSpace) and space.owner is not None:
            return "#FFFFFF"
        return "#20252A"

    def _draw_color_band_polygon(
        self,
        space: object,
        polygon: tuple[float, ...],
        row: int,
        col: int,
    ) -> None:
        """Dessine la bande de groupe le long du bord intérieur d'une case projetée.

        Entrées:
            space (object): Case potentiellement de type terrain.
            polygon (tuple[float, ...]): Quadrilatère projeté TL/TR/BR/BL.
            row (int): Ligne logique.
            col (int): Colonne logique.

        Sortie:
            None: Une bande colorée en perspective est ajoutée pour un terrain.
        """
        if not isinstance(space, Property):
            return
        color = COLOR_GROUPS.get(space.color_group, "#CCCCCC")
        pts = list(zip(polygon[0::2], polygon[1::2]))
        tl, tr, br, bl = pts
        t = 0.18
        def lerp(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
            """Interpole deux points pour construire l'épaisseur de la bande.

            Entrées:
                a (tuple[float, float]): Premier point.
                b (tuple[float, float]): Second point.

            Sortie:
                tuple[float, float]: Point situé à la fraction ``t``.
            """
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        if row == 10:
            strip = (tl, tr, lerp(tr, br), lerp(tl, bl))
        elif col == 0:
            strip = (tl, lerp(tl, tr), lerp(bl, br), bl)
        elif row == 0:
            strip = (tl, tr, lerp(tr, br), lerp(tl, bl))
        else:
            strip = (tl, lerp(tl, tr), lerp(bl, br), bl)
        coords = tuple(value for point in strip for value in point)
        self.canvas.create_polygon(*coords, fill=color, outline="")

    def _draw_case_landmark(
        self,
        space: object,
        row: int,
        col: int,
        cell: float,
    ) -> None:
        """Ajoute une petite miniature de décor aux gares et compagnies.

        Entrées:
            space (object): Gare ou compagnie à représenter.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.
            cell (float): Taille logique de référence.

        Sortie:
            None: Un petit volume renforce l'effet de diorama sans changer le jeu.
        """
        if row == 10:
            gx, gy = col + 0.50, row + 0.28
        elif row == 0:
            gx, gy = col + 0.50, row + 0.72
        elif col == 0:
            gx, gy = col + 0.72, row + 0.50
        else:
            gx, gy = col + 0.28, row + 0.50
        x, y = self._project_grid_point(gx, gy)
        if isinstance(space, Railroad):
            color = "#666D72"
            size = max(3.8, cell * 0.048)
        else:
            color = "#4F95C8"
            size = max(3.5, cell * 0.044)
        self._draw_mini_building(x, y, size, color)

    @staticmethod
    def _space_icon(space: object) -> str:
        """Retourne un pictogramme compact selon le type de case.

        Entrées:
            space (object): Case à identifier.

        Sortie:
            str: Symbole sûr pour Canvas, ou chaîne vide pour un terrain standard.
        """
        if isinstance(space, Railroad):
            return "▣"
        if isinstance(space, Utility):
            return "⚡"
        if isinstance(space, ChanceSpace):
            return "?"
        if isinstance(space, CommunityChestSpace):
            return "▤"
        if isinstance(space, JailSpace):
            return "▦"
        if isinstance(space, GoToJailSpace):
            return "→"
        if isinstance(space, FreeParkingSpace):
            return "P"
        if isinstance(space, TaxSpace):
            return "$"
        if isinstance(space, GoSpace):
            return "GO"
        return ""

    def _current_rent_label(self, space: OwnableSpace) -> str:
        """Construit le loyer actuellement applicable pour un bien possédé.

        Entrées:
            space (OwnableSpace): Terrain, gare ou compagnie dont le loyer doit être affiché.

        Sortie:
            str: Montant actuel en dollars, multiplicateur de dés pour une compagnie,
            ou chaîne vide lorsque le bien n'a pas de propriétaire ou est hypothéqué.
        """
        if space.owner is None or space.mortgaged:
            return ""

        if isinstance(space, Utility):
            owned_count = sum(
                1
                for property_ in space.owner.properties
                if isinstance(property_, Utility)
            )
            multiplier = space.multipliers[1] if owned_count >= 2 else space.multipliers[0]
            suffix = (
                ""
                if self.game.options.rent_percent == 100
                else f" × {self.game.options.rent_percent} %"
            )
            return f"{multiplier}× dés{suffix}"

        if isinstance(space, Railroad):
            rent = self.game.rules.calculate_rent(space, 0)
            return f"{rent} $"

        if isinstance(space, Property):
            rent = self.game.rules.calculate_rent(space, 0)
            return f"{rent} $"

        return ""

    def _space_price_position(self, row: int, col: int) -> tuple[float, float]:
        """Place le prix sur le bord opposé au nom de la case.

        Entrées:
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.

        Sortie:
            tuple[float, float]: Prix dehors pour 31–09 et dedans pour 11–29.
        """
        if row == 10:
            return self._project_grid_point(col + 0.50, row + 0.80)
        if row == 0:
            return self._project_grid_point(col + 0.50, row + 0.78)
        if col == 0:
            return self._project_grid_point(col + 0.78, row + 0.50)
        return self._project_grid_point(col + 0.80, row + 0.50)

    def _draw_property_state(
        self,
        space: OwnableSpace,
        polygon: tuple[float, ...],
        row: int,
        col: int,
        cell: float,
    ) -> None:
        """Affiche le prix et le développement sans répéter le nom du propriétaire.

        Entrées:
            space (OwnableSpace): Bien à représenter.
            polygon (tuple[float, ...]): Quadrilatère projeté de la case.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.
            cell (float): Taille logique de référence.

        Sortie:
            None: Le prix occupe le bord opposé au nom et les bâtiments restent visibles.
        """
        index = int(getattr(space, "index", -1))
        angle = self._space_price_angle(index, row, col)
        footer = f"{space.price} $"
        foreground = self._space_foreground(space)

        pos = self._space_price_position(row, col)
        self.canvas.create_text(
            pos[0],
            pos[1],
            text=footer,
            font=("Arial", max(5, int(cell * 0.058)), "bold"),
            fill=foreground,
            angle=angle,
        )

        if isinstance(space, Property) and space.development_level > 0:
            self._draw_buildings(space, row, col, cell)

    def _draw_buildings(
        self,
        space: Property,
        row: int,
        col: int,
        cell: float,
    ) -> None:
        """Dessine maisons et hôtel comme de petites miniatures de diorama.

        Entrées:
            space (Property): Terrain développé à représenter.
            row (int): Ligne logique de la case.
            col (int): Colonne logique de la case.
            cell (float): Taille logique de référence.

        Sortie:
            None: Les constructions suivent la bande de groupe, y compris sur les côtés retournés.
        """
        count = 1 if space.hotel else max(0, min(4, space.houses))
        if count == 0:
            return
        for index in range(count):
            spread = (index - (count - 1) / 2) * 0.14
            if row == 10:
                gx, gy = col + 0.50 + spread, row + 0.16
            elif row == 0:
                gx, gy = col + 0.50 + spread, row + 0.16
            elif col == 0:
                gx, gy = col + 0.16, row + 0.50 + spread
            else:
                gx, gy = col + 0.16, row + 0.50 + spread
            x, y = self._project_grid_point(gx, gy)
            self._draw_mini_building(
                x,
                y,
                max(4.0, cell * (0.085 if space.hotel else 0.055)),
                "#B43A35" if space.hotel else "#3A8D4E",
            )

    def _draw_mini_building(
        self,
        x: float,
        y: float,
        size: float,
        color: str,
    ) -> None:
        """Dessine un petit volume pseudo-3D utilisé pour maisons et hôtels.

        Entrées:
            x (float): Centre horizontal de la miniature.
            y (float): Base verticale de la miniature.
            size (float): Taille générale du volume.
            color (str): Couleur principale du bâtiment.

        Sortie:
            None: Un toit et deux façades donnent un relief lisible à petite taille.
        """
        dark = self._shade_color(color, 0.68)
        light = self._shade_color(color, 1.18)
        h = size * 1.35
        self.canvas.create_polygon(
            x - size, y,
            x, y - size * 0.52,
            x + size, y,
            x, y + size * 0.52,
            fill=light,
            outline=dark,
            width=1,
        )
        self.canvas.create_polygon(
            x - size, y,
            x, y + size * 0.52,
            x, y + h,
            x - size, y + h - size * 0.52,
            fill=dark,
            outline=dark,
        )
        self.canvas.create_polygon(
            x + size, y,
            x, y + size * 0.52,
            x, y + h,
            x + size, y + h - size * 0.52,
            fill=color,
            outline=dark,
        )

    def _draw_player(
        self,
        player: object,
        offset_x: float,
        offset_y: float,
        cell: float,
    ) -> None:
        """Dessine le pion vectoriel V22 d'un joueur sur sa case projetée.

        Entrées:
            player (object): Joueur possédant ``position`` et ``player_id``.
            offset_x (float): Compatibilité de signature.
            offset_y (float): Compatibilité de signature.
            cell (float): Taille logique de référence.

        Sortie:
            None: Le pion sélectionné est dessiné avec couleur et léger relief.
        """
        if player.player_id in self._animated_player_positions:
            center_x, center_y = self._animated_player_positions[player.player_id]
        else:
            visual_position = self._visual_position_overrides.get(
                player.player_id,
                player.position,
            )
            row, col = board_grid_position(visual_position)
            slot = player.player_id % 6
            slot_col = slot % 3
            slot_row = slot // 3
            center_x, center_y = self._project_grid_point(
                col + 0.28 + slot_col * 0.22,
                row + 0.30 + slot_row * 0.22,
            )
        pulse = self._pulse_factor if player.player_id == self._pulse_player_id else 1.0
        color = PLAYER_COLORS[player.player_id % len(PLAYER_COLORS)]
        pawns = self.visual_preferences.pawn_ids
        pawn_id = pawns[player.player_id % len(pawns)] if pawns else "car"
        draw_pawn(
            self.canvas,
            pawn_id,
            center_x,
            center_y,
            max(16, cell * 0.26) * pulse,
            color,
        )

    @staticmethod
    def _short_name(name: str) -> str:
        """Produit un nom de case complet et limité à deux lignes équilibrées.

        Entrées:
            name (str): Nom complet de la case.

        Sortie:
            str: Libellé complet sans troncature ni empilement automatique supplémentaire.
        """
        replacements = {
            "Caisse de communauté": "Caisse de\ncommunauté",
            "Prison / Simple visite": "Prison /\nSimple visite",
            "Impôt sur le revenu": "Impôt sur\nle revenu",
            "Allez en prison": "Allez en\nprison",
            "Taxe de luxe": "Taxe de luxe",
            "Parc Gratuit": "Parc Gratuit",
        }
        if name in replacements:
            return replacements[name]
        words = name.split()
        if len(name) <= 14 or len(words) <= 1:
            return name
        best_index = 1
        best_delta = len(name)
        for index in range(1, len(words)):
            left = " ".join(words[:index])
            right = " ".join(words[index:])
            delta = abs(len(left) - len(right))
            if delta < best_delta:
                best_delta = delta
                best_index = index
        return f"{' '.join(words[:best_index])}\n{' '.join(words[best_index:])}"
