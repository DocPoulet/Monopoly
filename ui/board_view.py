"""Affichage graphique interactif du plateau de Monopoly."""

from __future__ import annotations

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
    ) -> None:
        """Construit le Canvas, le cache de cartes et la fiche de propriété superposée.

        Entrées:
            master (tk.Misc): Conteneur parent.
            game (Game): Partie à dessiner.
            on_space_clicked (Callable | None): Callback de consultation d'un bien.

        Sortie:
            None: Le plateau est prêt à être affiché et redimensionné.
        """
        super().__init__(master, style="Board.TFrame")
        self.game = game
        self.on_space_clicked = on_space_clicked
        self._board_geometry: tuple[float, float, float] | None = None
        self.last_drawn_cards: dict[str, DrawnCardEvent | None] = {
            "chance": None,
            "community_chest": None,
        }
        self.canvas = tk.Canvas(
            self,
            background="#D9E2DF",
            highlightthickness=0,
            width=820,
            height=820,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.property_card = PropertyCardOverlay(self)
        self.landing_build_panel = LandingBuildOverlay(self)
        self.auction_panel = AuctionOverlay(self)
        self.building_auction_panel = BuildingAuctionOverlay(self)
        self.trade_panel = TradeOverlay(self)
        self.property_manager = PropertyManagerOverlay(self)
        self.history_panel = HistoryOverlay(self)
        self.end_game_panel = EndGameOverlay(self)
        self.rules_panel = RulesSummaryOverlay(self)

    def set_game(self, game: Game) -> None:
        """Remplace la partie et réinitialise les éléments temporaires de l'affichage.

        Entrées:
            game (Game): Nouvelle partie à représenter.

        Sortie:
            None: Le plateau est réinitialisé puis redessiné.
        """
        self.game = game
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
    ) -> None:
        """Affiche le bilan final intégré de la partie.

        Entrées:
            on_history (Callable[[], None]): Callback ouvrant l'historique.
            on_new_game (Callable[[], None]): Callback retournant au menu.

        Sortie:
            None: Le panneau final masque les autres superpositions.
        """
        self.property_card.hide()
        self.auction_panel.hide()
        self.building_auction_panel.hide()
        self.trade_panel.hide()
        self.property_manager.hide()
        self.history_panel.hide()
        self.end_game_panel.show(self.game, on_history, on_new_game)

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
        """Redessine toutes les cases, zones centrales et pions.

        Entrées:
            Aucune autre que l'état courant de la vue et de la partie.

        Sortie:
            None: Le contenu du Canvas est remplacé.
        """
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        size = min(width, height) * 0.97
        offset_x = (width - size) / 2
        offset_y = (height - size) / 2
        cell = size / 11
        self._board_geometry = (offset_x, offset_y, cell)

        self.canvas.create_rectangle(
            offset_x + 7,
            offset_y + 9,
            offset_x + size + 7,
            offset_y + size + 9,
            fill="#AEB9B6",
            outline="",
        )
        self._draw_center(offset_x, offset_y, cell)

        for index, space in enumerate(self.game.board.spaces):
            row, col = board_grid_position(index)
            self._draw_space(space, row, col, offset_x, offset_y, cell)

        for player in self.game.players:
            if not player.bankrupt:
                self._draw_player(player, offset_x, offset_y, cell)

    def _draw_center(self, offset_x: float, offset_y: float, cell: float) -> None:
        """Dessine le titre et les zones permanentes Chance / Caisse de communauté.

        Entrées:
            offset_x (float): Décalage horizontal du plateau.
            offset_y (float): Décalage vertical du plateau.
            cell (float): Taille d'une case.

        Sortie:
            None: La zone centrale complète est dessinée.
        """
        x1 = offset_x + cell
        y1 = offset_y + cell
        x2 = offset_x + 10 * cell
        y2 = offset_y + 10 * cell
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#E8F3EA",
            outline="#9CAB9F",
            width=2,
        )

        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        self.canvas.create_text(
            center_x,
            center_y - cell * 1.55,
            text="MONOPOLY",
            font=("Arial", max(22, int(cell * 0.58)), "bold"),
            fill="#263238",
        )
        self.canvas.create_text(
            center_x,
            center_y - cell * 1.02,
            text="POO • moteur indépendant • interface Tkinter",
            font=("Arial", max(9, int(cell * 0.16))),
            fill="#61706B",
        )

        if self.game.options.free_parking_card_pot:
            self._draw_free_parking_pot(center_x, center_y, cell)

        community_rect, chance_rect = center_deck_rectangles(
            x1, x2, center_y, cell
        )
        self._draw_deck(
            *community_rect,
            "CAISSE DE COMMUNAUTÉ",
            "#4F95C8",
            "☰",
            self.last_drawn_cards["community_chest"],
        )
        self._draw_deck(
            *chance_rect,
            "CHANCE",
            "#E59B31",
            "?",
            self.last_drawn_cards["chance"],
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
        if isinstance(space, OwnableSpace) and space.mortgaged:
            return "#D8D8D8"
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
        """Dessine une case et les informations pertinentes liées à son état.

        Entrées:
            space (object): Case du plateau à afficher.
            row (int): Ligne de grille de la case.
            col (int): Colonne de grille de la case.
            offset_x (float): Décalage horizontal du plateau.
            offset_y (float): Décalage vertical du plateau.
            cell (float): Taille de la cellule.

        Sortie:
            None: La case est ajoutée au Canvas.
        """
        x1 = offset_x + col * cell
        y1 = offset_y + row * cell
        x2 = x1 + cell
        y2 = y1 + cell
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self._space_fill(space),
            outline="#343A40",
            width=1,
        )
        self._draw_color_band(space, x1, y1, x2, y2, row, col, cell)
        name = self._short_name(getattr(space, "name", ""))
        self.canvas.create_text(
            (x1 + x2) / 2,
            y1 + cell * 0.45,
            text=name,
            width=max(30, cell * 0.84),
            justify="center",
            font=("Arial", max(6, int(cell * 0.11)), "bold"),
            fill="#20252A",
        )
        self.canvas.create_text(
            x1 + 4,
            y1 + 4,
            text=str(getattr(space, "index", "")),
            anchor="nw",
            font=("Arial", max(6, int(cell * 0.085))),
            fill="#7A858D",
        )
        if isinstance(space, OwnableSpace):
            self._draw_property_state(space, x1, y1, x2, y2, cell)

    def _draw_color_band(
        self,
        space: object,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        row: int,
        col: int,
        cell: float,
    ) -> None:
        """Dessine la bande colorée d'un terrain selon le côté du plateau.

        Entrées:
            space (object): Case potentiellement colorée.
            x1, y1, x2, y2 (float): Limites graphiques de la case.
            row (int): Ligne de grille.
            col (int): Colonne de grille.
            cell (float): Taille d'une cellule.

        Sortie:
            None: Une bande est ajoutée uniquement pour les terrains de couleur.
        """
        if not isinstance(space, Property):
            return
        color = COLOR_GROUPS.get(space.color_group, "#CCCCCC")
        thickness = cell * 0.16
        if row == 10:
            coords = (x1, y1, x2, y1 + thickness)
        elif col == 0:
            coords = (x2 - thickness, y1, x2, y2)
        elif row == 0:
            coords = (x1, y2 - thickness, x2, y2)
        else:
            coords = (x1, y1, x1 + thickness, y2)
        self.canvas.create_rectangle(*coords, fill=color, outline="")

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
            multiplier = 10 if owned_count >= 2 else 4
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

    def _draw_property_state(
        self,
        space: OwnableSpace,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        cell: float,
    ) -> None:
        """Affiche propriétaire, loyer actuel, hypothèque et développement d'un bien.

        Entrées:
            space (OwnableSpace): Bien à représenter.
            x1, y1, x2, y2 (float): Limites graphiques de la case.
            cell (float): Taille d'une cellule pour adapter les textes.

        Sortie:
            None: Les informations courantes sont ajoutées à la case.
        """
        if space.owner is None:
            footer = f"{space.price} $"
        else:
            footer = space.owner.name
            if space.mortgaged:
                footer += " • HYP."

            owner_color = PLAYER_COLORS[
                space.owner.player_id % len(PLAYER_COLORS)
            ]
            radius = max(3, cell * 0.045)
            self.canvas.create_oval(
                x2 - radius * 3,
                y2 - radius * 3,
                x2 - radius,
                y2 - radius,
                fill=owner_color,
                outline="#FFFFFF",
                width=1,
            )

        self.canvas.create_text(
            (x1 + x2) / 2,
            y2 - cell * 0.075,
            text=footer,
            width=max(30, cell * 0.84),
            font=("Arial", max(6, int(cell * 0.08))),
            fill="#4A5056",
        )

        if space.owner is not None and not space.mortgaged:
            rent_label = self._current_rent_label(space)
            if rent_label:
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    y1 + cell * 0.77,
                    text=f"Loyer {rent_label}",
                    width=max(30, cell * 0.86),
                    font=("Arial", max(6, int(cell * 0.075)), "bold"),
                    fill="#2D3A42",
                )

        if isinstance(space, Property) and space.development_level > 0:
            buildings = "HÔTEL" if space.hotel else "⌂" * space.houses
            self.canvas.create_text(
                (x1 + x2) / 2,
                y1 + cell * 0.63,
                text=buildings,
                font=("Arial", max(7, int(cell * 0.11)), "bold"),
                fill="#1B5E20",
            )

        if isinstance(space, Railroad):
            icon = "GARE"
        elif isinstance(space, Utility):
            icon = "CIE"
        else:
            icon = ""

        if icon:
            self.canvas.create_text(
                (x1 + x2) / 2,
                y1 + cell * 0.61,
                text=icon,
                font=("Arial", max(6, int(cell * 0.085)), "bold"),
                fill="#59636E",
            )

    def _draw_player(
        self,
        player: object,
        offset_x: float,
        offset_y: float,
        cell: float,
    ) -> None:
        """Dessine le pion circulaire d'un joueur sur sa case actuelle.

        Entrées:
            player (object): Joueur possédant ``position`` et ``player_id``.
            offset_x (float): Décalage horizontal du plateau.
            offset_y (float): Décalage vertical du plateau.
            cell (float): Taille d'une cellule.

        Sortie:
            None: Un pion coloré et son numéro sont ajoutés au Canvas.
        """
        row, col = board_grid_position(player.position)
        x1 = offset_x + col * cell
        y1 = offset_y + row * cell
        slot = player.player_id % 6
        slot_col = slot % 3
        slot_row = slot // 3
        radius = max(5, cell * 0.085)
        center_x = x1 + cell * (0.25 + slot_col * 0.25)
        center_y = y1 + cell * (0.25 + slot_row * 0.22)
        color = PLAYER_COLORS[player.player_id % len(PLAYER_COLORS)]
        self.canvas.create_oval(
            center_x - radius - 2,
            center_y - radius + 2,
            center_x + radius - 2,
            center_y + radius + 2,
            fill="#8D9995",
            outline="",
        )
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=color,
            outline="#FFFFFF",
            width=2,
        )
        self.canvas.create_text(
            center_x,
            center_y,
            text=str(player.player_id + 1),
            font=("Arial", max(6, int(radius * 0.9)), "bold"),
            fill="#FFFFFF",
        )

    @staticmethod
    def _short_name(name: str) -> str:
        """Raccourcit certains intitulés afin qu'ils restent lisibles dans une case.

        Entrées:
            name (str): Nom complet de la case.

        Sortie:
            str: Nom abrégé, éventuellement réparti sur plusieurs lignes.
        """
        replacements = {
            "Caisse de communauté": "Caisse\ncommunauté",
            "Prison / Simple visite": "Prison /\nVisite",
            "Impôt sur le revenu": "Impôt",
            "Allez en prison": "Allez en\nprison",
            "Taxe de luxe": "Taxe luxe",
            "Parc Gratuit": "Parc\nGratuit",
        }
        return replacements.get(name, name.replace(" ", "\n", 1))
