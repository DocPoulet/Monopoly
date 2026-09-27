"""Fenêtre principale reliant l'interface Tkinter au moteur POO."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from monopoly import Game
from monopoly.auction import AuctionResult
from monopoly.building_auction import BuildingAuctionResult
from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property
from monopoly.trade import TradeResult

from .board_view import BoardView, PLAYER_COLORS
from .debt_dialog import DebtManagementDialog
from .mortgage_transfer_dialog import ReceivedMortgageDialog
from .widgets import DiceFace


class GameWindow(ttk.Frame):
    """Présente une partie jouable et traduit les interactions en appels du moteur.

    Entrées:
        master (tk.Misc): Conteneur parent.
        game (Game): Partie à afficher et contrôler.
        new_game_callback (callable): Fonction appelée pour revenir au menu d'accueil.
        save_game_callback (callable): Fonction appelée pour sauvegarder la partie.
        loaded (bool): Indique si la partie provient d'une sauvegarde.

    Sortie:
        GameWindow: Interface complète du plateau et du panneau de contrôle.
    """

    def __init__(
        self,
        master: tk.Misc,
        game: Game,
        new_game_callback: object,
        save_game_callback: object | None = None,
        loaded: bool = False,
    ) -> None:
        """Construit le plateau, les dés cliquables et les informations joueurs.

        Entrées:
            master (tk.Misc): Conteneur parent.
            game (Game): Moteur de la partie.
            new_game_callback (object): Callback ramenant au menu après confirmation.
            save_game_callback (object | None): Callback de sauvegarde JSON.
            loaded (bool): ``True`` pour une partie restaurée.

        Sortie:
            None: Tous les widgets sont créés et synchronisés.
        """
        super().__init__(master, padding=10)
        self.game = game
        self.new_game_callback = new_game_callback
        self.save_game_callback = save_game_callback
        self.loaded = loaded
        self.pending_purchase: tuple[Player, OwnableSpace] | None = None
        self.pending_landing_build: tuple[Player, Property] | None = None
        self.last_result_player: Player | None = None
        self.auction_in_progress = False
        self.auction_source: str | None = None
        self.building_auction_in_progress = False
        self.trade_in_progress = False
        self.property_management_in_progress = False
        self.history_in_progress = False
        self.rules_in_progress = False
        self.inspection_in_progress = False
        self.end_game_shown = False
        self.game.set_debt_manager(self._manage_debt)
        self.game.set_received_mortgage_selector(
            self._choose_received_mortgages_to_lift
        )

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        self.board_view = BoardView(
            self,
            game,
            on_space_clicked=self._inspect_space,
        )
        self.board_view.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.sidebar = ttk.Frame(self)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.columnconfigure(0, weight=1)
        self.sidebar.rowconfigure(4, weight=1)

        self._build_header()
        self._build_dice_panel()
        self._build_action_panel()
        self._build_players_panel()
        self._build_log_panel()
        if self.loaded:
            self._restore_log_from_history()
            self._log("Partie chargée.")
        else:
            self._log("Nouvelle partie créée.")
            self._log(f"C'est à {self.game.current_player.name} de jouer.")
        self.refresh()
        if self.game.is_over:
            self._check_game_over()

    def _build_header(self) -> None:
        """Crée le bandeau supérieur du joueur courant et le bouton Nouvelle partie.

        Entrées:
            Aucune.

        Sortie:
            None: Le bandeau est ajouté à la barre latérale.
        """
        frame = ttk.Frame(self.sidebar)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(0, weight=1)

        self.turn_label = ttk.Label(frame, text="", font=("Arial", 17, "bold"))
        self.turn_label.grid(row=0, column=0, sticky="w")
        self.save_button = ttk.Button(
            frame,
            text="Sauvegarder",
            command=self._save_game,
        )
        self.save_button.grid(row=0, column=1, sticky="e", padx=(0, 6))

        ttk.Button(
            frame,
            text="Nouvelle partie",
            command=self._request_new_game,
        ).grid(row=0, column=2, sticky="e")

        self.status_label = ttk.Label(frame, text="")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(3, 0))

    def _build_dice_panel(self) -> None:
        """Crée les dés cliquables et les actions de prison contextuelles.

        Entrées:
            Aucune.

        Sortie:
            None: Les dés deviennent le seul contrôle de lancer et la prison est intégrée dessous.
        """
        self.dice_frame = ttk.LabelFrame(
            self.sidebar,
            text="Dés — cliquez pour lancer",
            padding=10,
            style="Card.TLabelframe",
        )
        self.dice_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.dice_frame.columnconfigure(0, weight=1)
        self.dice_frame.columnconfigure(1, weight=1)
        self.dice_frame.columnconfigure(2, weight=2)

        self.die_one = DiceFace(self.dice_frame, size=82, command=self._roll_from_dice)
        self.die_one.grid(row=0, column=0, padx=(4, 6), pady=4)
        self.die_two = DiceFace(self.dice_frame, size=82, command=self._roll_from_dice)
        self.die_two.grid(row=0, column=1, padx=6, pady=4)

        info = ttk.Frame(self.dice_frame)
        info.grid(row=0, column=2, sticky="nsew", padx=(10, 4))
        self.dice_note = ttk.Label(
            info,
            text="Aucun lancer",
            style="DiceNote.TLabel",
            justify="center",
        )
        self.dice_note.pack(fill="x", expand=True)
        self.dice_hint = ttk.Label(
            info,
            text="Cliquez sur un dé pour lancer.",
            style="Muted.TLabel",
            justify="center",
        )
        self.dice_hint.pack(fill="x", pady=(4, 0))

        self.jail_controls = ttk.Frame(self.dice_frame)
        self.jail_controls.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.jail_controls.columnconfigure(0, weight=1)
        self.jail_controls.columnconfigure(1, weight=1)

        self.jail_label = ttk.Label(
            self.jail_controls,
            text="En prison : cliquez sur les dés pour tenter un double.",
            justify="center",
        )
        self.jail_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        self.jail_pay_button = ttk.Button(
            self.jail_controls,
            text="Payer 50 $",
            command=lambda: self._play_turn("pay"),
        )
        self.jail_pay_button.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.jail_card_button = ttk.Button(
            self.jail_controls,
            text="Utiliser carte sortie de prison",
            command=lambda: self._play_turn("card"),
        )
        self.jail_card_button.grid(row=1, column=1, sticky="ew", padx=(4, 0))
        self.jail_controls.grid_remove()

    def _build_action_panel(self) -> None:
        """Crée les actions générales de patrimoine et d'échange entre joueurs.

        Entrées:
            Aucune.

        Sortie:
            None: Les boutons de gestion et d'échange sont ajoutés à droite.
        """
        frame = ttk.LabelFrame(self.sidebar, text="Gestion", padding=8)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        self.manage_button = ttk.Button(
            frame,
            text="Gérer mes propriétés",
            command=self._manage_properties,
        )
        self.manage_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.trade_button = ttk.Button(
            frame,
            text="Échanger",
            command=self._start_trade,
        )
        self.trade_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.rent_claim_frame = ttk.LabelFrame(
            frame,
            text="Loyer manuel",
            padding=6,
        )
        self.rent_claim_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(7, 0),
        )
        self.rent_claim_frame.columnconfigure(0, weight=1)
        self.rent_claim_frame.columnconfigure(1, weight=1)
        self.rent_claim_label = ttk.Label(
            self.rent_claim_frame,
            text="",
            justify="center",
        )
        self.rent_claim_label.grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5)
        )
        self.rent_claim_button = ttk.Button(
            self.rent_claim_frame,
            text="Réclamer",
            command=self._claim_rent,
        )
        self.rent_claim_button.grid(row=1, column=0, sticky="ew", padx=(0, 3))
        self.rent_waive_button = ttk.Button(
            self.rent_claim_frame,
            text="Renoncer",
            command=self._waive_rent,
        )
        self.rent_waive_button.grid(row=1, column=1, sticky="ew", padx=(3, 0))
        self.rent_claim_frame.grid_remove()

        self.bank_stock_label = ttk.Label(
            frame,
            text="",
            style="Muted.TLabel",
            anchor="center",
        )
        self.history_button = ttk.Button(
            frame,
            text="Historique / Stats",
            command=self._show_history,
        )
        self.history_button.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(7, 0),
        )

        self.rules_button = ttk.Button(
            frame,
            text="Règles de la partie",
            command=self._show_rules,
        )
        self.rules_button.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(7, 0),
        )

        self.bank_stock_label.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(7, 0),
        )

    def _build_players_panel(self) -> None:
        """Crée le tableau récapitulatif de l'état de tous les joueurs.

        Entrées:
            Aucune.

        Sortie:
            None: Un tableau de joueurs est ajouté à la barre latérale.
        """
        frame = ttk.LabelFrame(self.sidebar, text="Joueurs", padding=6)
        frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        columns = ("cash", "position", "properties", "cards", "status")
        self.players_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="tree headings",
            height=min(6, len(self.game.players)),
        )
        self.players_tree.heading("#0", text="Joueur")
        self.players_tree.heading("cash", text="$")
        self.players_tree.heading("position", text="Case")
        self.players_tree.heading("properties", text="Biens")
        self.players_tree.heading("cards", text="Cartes")
        self.players_tree.heading("status", text="État")
        self.players_tree.column("#0", width=120)
        self.players_tree.column("cash", width=75, anchor="center")
        self.players_tree.column("position", width=55, anchor="center")
        self.players_tree.column("properties", width=55, anchor="center")
        self.players_tree.column("cards", width=55, anchor="center")
        self.players_tree.column("status", width=90, anchor="center")
        self.players_tree.pack(fill="x")
        self.players_tree.tag_configure("current", background="#E9F2FF")
        self.players_tree.tag_configure("bankrupt", foreground="#8A8A8A")

    def _build_log_panel(self) -> None:
        """Crée le journal textuel retraçant les événements de la partie.

        Entrées:
            Aucune.

        Sortie:
            None: Une zone de texte avec défilement est ajoutée.
        """
        frame = ttk.LabelFrame(self.sidebar, text="Journal", padding=6)
        frame.grid(row=4, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(
            frame,
            wrap="word",
            state="disabled",
            width=48,
            height=18,
            background="#F7F9FA",
            foreground="#27313A",
            relief="flat",
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _can_save_now(self) -> bool:
        """Indique si la partie se trouve dans un état stable pouvant être sauvegardé.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsqu'aucune décision intermédiaire n'est ouverte.
        """
        return not any(
            (
                self.pending_purchase is not None,
                self.pending_landing_build is not None,
                self.game.pending_rent_claim is not None,
                self.auction_in_progress,
                self.building_auction_in_progress,
                self.trade_in_progress,
                self.property_management_in_progress,
                self.history_in_progress,
                self.rules_in_progress,
                self.inspection_in_progress,
            )
        )

    def _save_game(self) -> None:
        """Demande au contrôleur d'écrire la partie dans un fichier JSON.

        Entrées:
            Aucune.

        Sortie:
            None: Le chemin final est journalisé en cas de succès.
        """
        if not self._can_save_now() or not callable(self.save_game_callback):
            return

        path = self.save_game_callback(self.game)
        if path:
            self._log(f"Partie sauvegardée : {path}")

    def _request_new_game(self) -> None:
        """Demande confirmation avant d'abandonner la partie en cours.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback ramène au menu d'accueil après confirmation.
        """
        confirmed = messagebox.askyesno(
            "Nouvelle partie",
            "Abandonner la partie actuelle et revenir au menu d’accueil ?",
            parent=self,
        )
        if confirmed and callable(self.new_game_callback):
            self.new_game_callback()

    def _roll_from_dice(self) -> None:
        """Lance le tour lorsque le joueur clique sur l'un des deux dés.

        Entrées:
            Aucune.

        Sortie:
            None: Un tour normal ou une tentative de double en prison est exécuté.
        """
        self._play_turn("roll")

    def _play_turn(self, jail_action: str) -> None:
        """Exécute un tour puis synchronise dés, cartes, achat et journal.

        Entrées:
            jail_action (str): Action de prison transmise à ``Game.take_turn``.

        Sortie:
            None: Le moteur et tous les éléments visuels sont actualisés.
        """
        if (
            self.pending_purchase is not None
            or self.pending_landing_build is not None
            or self.game.pending_rent_claim is not None
            or self.auction_in_progress
            or self.building_auction_in_progress
            or self.trade_in_progress
            or self.property_management_in_progress
            or self.history_in_progress
            or self.rules_in_progress
            or self.inspection_in_progress
        ):
            return

        try:
            result = self.game.take_turn(jail_action=jail_action)
        except ValueError as error:
            messagebox.showwarning("Action impossible", str(error), parent=self)
            self.refresh()
            return
        except RuntimeError as error:
            messagebox.showinfo("Partie terminée", str(error), parent=self)
            self.refresh()
            return

        self.last_result_player = result.player
        self.die_one.set_value(result.dice[0])
        self.die_two.set_value(result.dice[1])

        notes = []
        if result.rolled_double:
            notes.append("DOUBLE")
        if result.passed_go:
            notes.append(f"+{self.game.rules.go_salary} Départ")
        total = sum(result.dice)
        headline = f"Total : {total}" if total else "Pas de déplacement"
        self.dice_note.config(text="\n".join([headline, *notes]))

        self._log(
            f"Tour {result.turn_number} — {result.player.name} : "
            f"{result.dice[0]} + {result.dice[1]}."
        )
        if result.message:
            self._log(result.message)

        for financial_event in self.game.financial_events_this_turn:
            self._log(financial_event)

        if result.player.bankrupt:
            self._log(f"{result.player.name} est en faillite.")

        for event in self.game.drawn_cards_this_turn:
            self.board_view.display_drawn_card(event)

        space = self.game.board.get_player_space(result.player)
        if (
            not self.game.is_over
            and not result.player.bankrupt
            and isinstance(space, OwnableSpace)
            and space.owner is None
        ):
            self.pending_purchase = (result.player, space)
            if self.game.options.auctions_enabled:
                self._log(
                    f"Décision requise : acheter {space.name} pour {space.price} $ "
                    "ou lancer l'enchère."
                )
            else:
                self._log(
                    f"Décision requise : acheter {space.name} pour {space.price} $ "
                    "ou passer."
                )
        elif (
            not self.game.is_over
            and not result.player.bankrupt
            and isinstance(space, Property)
            and space.owner is result.player
        ):
            self._prepare_landing_build(result.player, space)

        self.refresh()

        if self._start_next_bankruptcy_auction():
            return

        self._show_purchase_card_if_needed()
        self._show_landing_build_if_needed()
        self._check_game_over()



    def _prepare_landing_build(
        self,
        player: Player,
        property_: Property,
    ) -> bool:
        """Prépare une unique décision de construction liée au dernier atterrissage.

        Entrées:
            player (Player): Joueur qui vient réellement d'atterrir.
            property_ (Property): Terrain atteint et possédé.

        Sortie:
            bool: ``True`` si au moins une construction peut être proposée.
        """
        if self.game.options.construction_anywhere or player.bankrupt:
            return False
        if property_.owner is not player:
            return False

        self.game.set_landing_build_context(player, property_)
        max_houses = self.game.rules.max_landing_house_purchase(player, property_)
        can_hotel = self.game.rules.can_build_hotel(player, property_)

        if max_houses <= 0 and not can_hotel:
            self.game.clear_landing_build_context()
            return False

        self.pending_landing_build = (player, property_)
        self._log(
            f"{player.name} peut construire sur {property_.name} après y être tombé."
        )
        return True

    def _show_landing_build_if_needed(self) -> None:
        """Affiche le menu de bâtiments lorsqu'un atterrissage attend une décision.

        Entrées:
            Aucune autre que ``pending_landing_build``.

        Sortie:
            None: La superposition apparaît avec quantité de maisons ou hôtel.
        """
        if self.pending_landing_build is None:
            return
        player, property_ = self.pending_landing_build
        self.board_view.show_landing_build(
            player,
            property_,
            on_buy_houses=self._buy_landing_houses,
            on_buy_hotel=self._buy_landing_hotel,
            on_pass=self._pass_landing_build,
        )

    def _finish_landing_build(self) -> None:
        """Clôt le droit temporaire de construire issu du dernier atterrissage.

        Entrées:
            Aucune.

        Sortie:
            None: Le contexte moteur et le menu graphique sont supprimés.
        """
        self.pending_landing_build = None
        self.game.clear_landing_build_context()
        self.board_view.hide_landing_build()
        self.refresh()

        if self._start_next_bankruptcy_auction():
            return
        self._check_game_over()

    def _buy_landing_houses(self, count: int) -> None:
        """Achète le nombre choisi de maisons pendant l'unique décision d'atterrissage.

        Entrées:
            count (int): Quantité de maisons demandée, au maximum quatre.

        Sortie:
            None: Toutes les maisons sont achetées ou la décision reste ouverte.
        """
        if self.pending_landing_build is None:
            return
        player, property_ = self.pending_landing_build

        if not self.game.rules.build_houses(player, property_, count):
            messagebox.showwarning(
                "Construction impossible",
                "Cette quantité n'est plus disponible ou n'est plus légalement constructible.",
                parent=self,
            )
            self.refresh()
            self._show_landing_build_if_needed()
            return

        label = "maison" if count == 1 else "maisons"
        self._log(
            f"{player.name} achète {count} {label} sur {property_.name}."
        )
        self._finish_landing_build()

    def _buy_landing_hotel(self) -> None:
        """Achète un unique hôtel pendant la décision d'atterrissage.

        Entrées:
            Aucune.

        Sortie:
            None: L'hôtel est construit si les quatre maisons préalables sont présentes.
        """
        if self.pending_landing_build is None:
            return
        player, property_ = self.pending_landing_build

        if not self.game.rules.build_hotel(player, property_):
            messagebox.showwarning(
                "Construction impossible",
                "L'hôtel n'est plus disponible ou le terrain n'est plus éligible.",
                parent=self,
            )
            self.refresh()
            self._show_landing_build_if_needed()
            return

        self._log(f"{player.name} achète un hôtel sur {property_.name}.")
        self._finish_landing_build()

    def _pass_landing_build(self) -> None:
        """Renonce à construire pendant cet atterrissage.

        Entrées:
            Aucune.

        Sortie:
            None: Le droit temporaire expire sans achat.
        """
        if self.pending_landing_build is not None:
            player, property_ = self.pending_landing_build
            self._log(
                f"{player.name} ne construit pas sur {property_.name} cette fois-ci."
            )
        self._finish_landing_build()

    def _claim_rent(self) -> None:
        """Fait réclamer le loyer manuel par le propriétaire concerné.

        Entrées:
            Aucune.

        Sortie:
            None: Le paiement est appliqué, journalisé puis les contrôles sont rafraîchis.
        """
        claim = self.game.pending_rent_claim
        if claim is None:
            return
        message = (
            f"{claim.recipient.name} réclame {claim.amount} $ de loyer à {claim.payer.name}."
        )
        if self.game.claim_pending_rent():
            self._log(message)
        self.refresh()
        if self._start_next_bankruptcy_auction():
            return
        self._check_game_over()

    def _waive_rent(self) -> None:
        """Permet au propriétaire de renoncer explicitement à un loyer manuel.

        Entrées:
            Aucune.

        Sortie:
            None: La demande est supprimée et le jeu peut reprendre.
        """
        claim = self.game.pending_rent_claim
        if claim is None:
            return
        message = (
            f"{claim.recipient.name} renonce au loyer de {claim.amount} $ dû par {claim.payer.name}."
        )
        if self.game.waive_pending_rent():
            self._log(message)
        self.refresh()

    def _show_purchase_card_if_needed(self) -> None:
        """Affiche la fiche d'achat intégrée lorsqu'un bien libre attend une décision.

        Entrées:
            Aucune autre que ``pending_purchase``.

        Sortie:
            None: La fiche apparaît au centre du plateau sans nouvelle fenêtre.
        """
        if self.pending_purchase is None or self.auction_in_progress:
            return
        player, space = self.pending_purchase
        self.board_view.show_purchase_card(
            player,
            space,
            on_buy=self._buy_pending_property,
            on_auction=self._auction_pending_property,
        )
        if not self.game.options.auctions_enabled:
            self.board_view.property_card.auction_button.configure(text="Passer")
        else:
            self.board_view.property_card.auction_button.configure(text="Enchères")

    def _buy_pending_property(self) -> None:
        """Achète le bien en attente puis retire sa fiche du plateau.

        Entrées:
            Aucune autre que ``pending_purchase``.

        Sortie:
            None: Le bien est acheté si possible et le tour peut reprendre.
        """
        if self.pending_purchase is None:
            return
        player, space = self.pending_purchase
        if not self.game.rules.buy_property(player, space):
            messagebox.showwarning(
                "Achat impossible",
                "Le joueur n'a pas assez d'argent ou le bien n'est plus disponible.",
                parent=self,
            )
            self.refresh()
            return
        self._log(f"{player.name} achète {space.name} pour {space.price} $.")
        self.pending_purchase = None
        self.board_view.hide_purchase_card()
        self.game.clear_landing_build_context()
        self.refresh()

    def _auction_pending_property(self) -> None:
        """Remplace la fiche d'achat par une enchère intégrée au plateau.

        Entrées:
            Aucune autre que ``pending_purchase``.

        Sortie:
            None: Le panneau d'enchère apparaît dans la même fenêtre de jeu.
        """
        if self.pending_purchase is None or self.auction_in_progress:
            return
        _player, space = self.pending_purchase

        if not self.game.options.auctions_enabled:
            self._log(f"{space.name} reste à la banque.")
            self.pending_purchase = None
            self.board_view.hide_purchase_card()
            self.refresh()
            self._check_game_over()
            return

        auction = self.game.start_auction(space)
        self.auction_in_progress = True
        self.auction_source = "purchase"
        self._log(f"Enchère ouverte pour {space.name}.")
        self.board_view.show_auction(auction, self._finish_auction)
        self.refresh()

    def _finish_auction(self, result: AuctionResult) -> None:
        """Finalise une enchère d'achat ou de faillite puis poursuit la file éventuelle.

        Entrées:
            result (AuctionResult): Résultat produit par le moteur d'enchères.

        Sortie:
            None: Le résultat est journalisé, le panneau disparaît et le jeu reprend
            ou passe au bien suivant d'une faillite envers la banque.
        """
        source = self.auction_source
        if result.sold and result.winner is not None:
            message = (
                f"{result.winner.name} remporte {result.space.name} "
                f"pour {result.amount} $."
            )
            self._log(message)
            self.game.record_event(
                "auction_win",
                message,
                result.winner,
                property_index=result.space.index,
                amount=result.amount,
                source=source,
            )
        else:
            self._log(f"{result.space.name} reste à la banque.")

        self.auction_in_progress = False
        self.auction_source = None
        self.board_view.hide_auction()
        self.board_view.hide_purchase_card()

        if source == "purchase":
            self.pending_purchase = None
            self.game.clear_landing_build_context()

        self.refresh()

        if source == "bankruptcy":
            if self._start_next_bankruptcy_auction():
                return

        self._check_game_over()

    def _start_next_bankruptcy_auction(self) -> bool:
        """Démarre la prochaine enchère obligatoire issue d'une faillite envers la banque.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` si une nouvelle enchère a été ouverte, sinon ``False``.
        """
        if (
            self.auction_in_progress
            or self.building_auction_in_progress
            or self.trade_in_progress
            or self.property_management_in_progress
            or self.pending_purchase is not None
            or self.pending_landing_build is not None
            or self.game.is_over
        ):
            return False

        space = self.game.pop_next_bank_auction()
        if space is None:
            return False

        auction = self.game.start_auction(space)
        self.auction_in_progress = True
        self.auction_source = "bankruptcy"
        self._log(
            f"La banque met {space.name} aux enchères après une faillite."
        )
        self.board_view.show_auction(auction, self._finish_auction)
        self.refresh()
        return True

    def _start_trade(self) -> None:
        """Ouvre le panneau d'échange intégré pour le joueur courant.

        Entrées:
            Aucune.

        Sortie:
            None: Les dés sont bloqués et le panneau central permet de composer l'offre.
        """
        if (
            self.pending_purchase is not None
            or self.pending_landing_build is not None
            or self.auction_in_progress
            or self.building_auction_in_progress
            or self.trade_in_progress
            or self.property_management_in_progress
            or self.game.pending_rent_claim is not None
            or self.history_in_progress
            or self.rules_in_progress
            or self.inspection_in_progress
            or self.game.is_over
        ):
            return

        if len(self.game.active_players) < 2:
            return

        self.trade_in_progress = True
        initiator = self.game.current_player
        self._log(f"{initiator.name} ouvre un échange.")
        self.board_view.show_trade(
            initiator,
            on_finished=self._finish_trade,
            on_cancel=self._cancel_trade,
        )
        self.refresh()

    def _finish_trade(self, result: TradeResult) -> None:
        """Journalise un échange réussi puis rend la main au joueur courant.

        Entrées:
            result (TradeResult): Résultat produit par l'objet métier ``TradeOffer``.

        Sortie:
            None: Le panneau est fermé et l'interface reflète les nouveaux patrimoines.
        """
        self.trade_in_progress = False
        self.board_view.hide_trade()
        self._log(result.message)
        self.refresh()

    def _cancel_trade(self) -> None:
        """Ferme le panneau d'échange sans modifier les patrimoines.

        Entrées:
            Aucune.

        Sortie:
            None: L'état d'échange est annulé et le tour peut reprendre.
        """
        self.trade_in_progress = False
        self.board_view.hide_trade()
        self._log("Échange annulé.")
        self.refresh()

    def _manage_debt(
        self,
        player: Player,
        target_cash: int,
        creditor: Player | None = None,
    ) -> DebtManagementResult:
        """Ouvre la gestion manuelle de dette avec cession de biens éventuelle.

        Entrées:
            player (Player): Joueur qui doit réunir des ressources.
            target_cash (int): Montant total de la dette.
            creditor (Player | None): Joueur créancier, ou ``None`` pour la banque.

        Sortie:
            DebtManagementResult: Cash préparé, valeur de biens cédés et faillite éventuelle.
        """
        dialog = DebtManagementDialog(
            self.winfo_toplevel(),
            self.game,
            player,
            target_cash,
            creditor=creditor,
        )
        self.wait_window(dialog)
        self.refresh()
        return dialog.result

    def _choose_received_mortgages_to_lift(
        self,
        player: Player,
        spaces: list[OwnableSpace],
    ) -> list[OwnableSpace]:
        """Demande quelles hypothèques reçues doivent être levées immédiatement.

        Entrées:
            player (Player): Nouveau propriétaire des biens.
            spaces (list[OwnableSpace]): Propriétés hypothéquées transférées.

        Sortie:
            list[OwnableSpace]: Biens choisis pour une déshypothèque immédiate.
        """
        dialog = ReceivedMortgageDialog(
            self.winfo_toplevel(),
            self.game,
            player,
            spaces,
        )
        self.wait_window(dialog)
        return list(dialog.result)

    def _inspect_space(self, space: OwnableSpace) -> None:
        """Affiche la fiche d'un bien après un clic direct sur sa case.

        Entrées:
            space (OwnableSpace): Bien cliqué sur le plateau.

        Sortie:
            None: Une fiche en lecture seule est affichée si aucune décision ne bloque.
        """
        if (
            self.game.is_over
            or self.pending_purchase is not None
            or self.pending_landing_build is not None
            or self.auction_in_progress
            or self.building_auction_in_progress
            or self.trade_in_progress
            or self.property_management_in_progress
            or self.game.pending_rent_claim is not None
            or self.history_in_progress
            or self.rules_in_progress
            or self.inspection_in_progress
        ):
            return

        self.inspection_in_progress = True
        self.board_view.show_space_info(
            space,
            on_close=self._finish_space_inspection,
        )
        self.refresh()

    def _finish_space_inspection(self) -> None:
        """Ferme la fiche de consultation et réactive les contrôles du tour.

        Entrées:
            Aucune.

        Sortie:
            None: Le mode consultation est désactivé.
        """
        self.inspection_in_progress = False
        self.board_view.hide_purchase_card()
        self.refresh()

    def _manage_properties(self) -> None:
        """Affiche la gestion du patrimoine directement au centre du plateau.

        Entrées:
            Aucune.

        Sortie:
            None: Les dés et autres actions sont bloqués jusqu'à fermeture du panneau.
        """
        if (
            self.property_management_in_progress
            or self.auction_in_progress
            or self.building_auction_in_progress
            or self.trade_in_progress
            or self.pending_purchase is not None
            or self.game.pending_rent_claim is not None
            or self.history_in_progress
            or self.rules_in_progress
            or self.inspection_in_progress
            or self.game.is_over
        ):
            return

        player = self.game.current_player
        if not player.properties:
            return

        self.property_management_in_progress = True
        self.board_view.show_property_manager(
            player,
            on_close=self._finish_property_management,
            on_changed=self._property_management_changed,
            on_building_auction=self._start_building_auction,
        )
        self.refresh()

    def _start_building_auction(
        self,
        building_type: str,
        requested_property: object,
    ) -> None:
        """Remplace temporairement le patrimoine par une enchère de bâtiment.

        Entrées:
            building_type (str): ``house`` ou ``hotel``.
            requested_property (object): Terrain ayant déclenché la demande, utilisé
                pour le journal et pour documenter l'intention initiale.

        Sortie:
            None: Le gestionnaire est masqué et l'enchère intégrée devient active.
        """
        if (
            self.building_auction_in_progress
            or self.auction_in_progress
            or self.trade_in_progress
            or self.game.is_over
        ):
            return

        try:
            auction = self.game.start_building_auction(building_type)
        except ValueError as error:
            self._log(str(error))
            self.refresh()
            return

        name = getattr(requested_property, "name", "un terrain")
        label = "maison" if building_type == "house" else "hôtel"

        self.property_management_in_progress = False
        self.building_auction_in_progress = True
        self.board_view.hide_property_manager()
        self._log(
            f"Pénurie : enchère d'un {label} déclenchée après la demande sur {name}."
        )
        self.board_view.show_building_auction(
            auction,
            on_finished=self._finish_building_auction,
        )
        self.refresh()

    def _finish_building_auction(self, result: BuildingAuctionResult) -> None:
        """Journalise une enchère de bâtiment puis rouvre le patrimoine du joueur courant.

        Entrées:
            result (BuildingAuctionResult): Résultat métier de l'enchère.

        Sortie:
            None: Le stock, le plateau et le panneau de propriétés sont actualisés.
        """
        self.building_auction_in_progress = False
        self.board_view.hide_building_auction()

        label = "maison" if result.building_type == "house" else "hôtel"
        if result.sold and result.winner is not None and result.property is not None:
            self._log(
                f"{result.winner.name} remporte un {label} pour {result.amount} $ "
                f"et le place sur {result.property.name}."
            )
        else:
            self._log(f"Aucun joueur n'achète le {label} mis aux enchères.")

        self.refresh()

        current = self.game.current_player
        if (
            not self.game.is_over
            and not current.bankrupt
            and current.properties
            and self.pending_purchase is None
            and self.pending_landing_build is None
            and not self.auction_in_progress
        ):
            self._manage_properties()

    def _property_management_changed(self) -> None:
        """Actualise l'interface pendant que le patrimoine reste ouvert.

        Entrées:
            Aucune.

        Sortie:
            None: Le plateau, le stock bancaire et les soldes sont redessinés.
        """
        self.refresh()

    def _finish_property_management(self, changed: bool) -> None:
        """Ferme la gestion intégrée et journalise les changements éventuels.

        Entrées:
            changed (bool): Indique si au moins une opération a été réalisée.

        Sortie:
            None: Le tour reprend et l'interface redevient interactive.
        """
        player = self.game.current_player
        self.property_management_in_progress = False
        self.board_view.hide_property_manager()

        if changed:
            self._log(f"{player.name} a modifié son patrimoine.")
            self._log(
                f"Solde de {player.name} : {player.cash} $ • "
                f"Banque : {self.game.bank.stock_text()}."
            )
        self.refresh()

    def _restore_log_from_history(self) -> None:
        """Reconstruit le journal visible à partir des événements structurés récents.

        Entrées:
            Aucune.

        Sortie:
            None: Les derniers messages de l'historique sont insérés dans le journal.
        """
        for event in self.game.history.recent(80):
            self._log(event.message)


    def _show_rules(self) -> None:
        """Ouvre le récapitulatif intégré des règles de la partie.

        Entrées:
            Aucune.

        Sortie:
            None: Les interactions de jeu sont bloquées jusqu'à fermeture du panneau.
        """
        if (
            self.rules_in_progress
            or self.pending_purchase is not None
            or self.pending_landing_build is not None
            or self.auction_in_progress
            or self.building_auction_in_progress
            or self.trade_in_progress
            or self.property_management_in_progress
            or self.game.pending_rent_claim is not None
            or self.history_in_progress
            or self.inspection_in_progress
        ):
            return

        self.rules_in_progress = True
        self.board_view.show_rules(self._finish_rules)
        self.refresh()

    def _finish_rules(self) -> None:
        """Ferme le récapitulatif des règles et réactive le jeu.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau est masqué et les contrôles sont rafraîchis.
        """
        self.rules_in_progress = False
        self.board_view.hide_rules()
        self.refresh()

    def _show_history(self) -> None:
        """Ouvre le panneau intégré d'historique et statistiques.

        Entrées:
            Aucune.

        Sortie:
            None: Les autres interactions sont bloquées jusqu'à fermeture.
        """
        if (
            self.history_in_progress
            or self.pending_purchase is not None
            or self.pending_landing_build is not None
            or self.auction_in_progress
            or self.building_auction_in_progress
            or self.trade_in_progress
            or self.property_management_in_progress
            or self.game.pending_rent_claim is not None
            or self.inspection_in_progress
            or self.rules_in_progress
        ):
            return

        self.history_in_progress = True
        self.board_view.show_history(self._finish_history)
        self.refresh()

    def _finish_history(self) -> None:
        """Ferme le panneau d'historique et réactive le tour.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau est masqué et les contrôles sont rafraîchis.
        """
        self.history_in_progress = False
        self.board_view.hide_history()
        self.refresh()

    def _show_end_history(self) -> None:
        """Ouvre l'historique depuis le bilan final.

        Entrées:
            Aucune.

        Sortie:
            None: Le bilan est masqué pendant la consultation.
        """
        self.board_view.hide_end_game()
        self.history_in_progress = True
        self.board_view.show_history(self._return_to_end_game)
        self.refresh()

    def _return_to_end_game(self) -> None:
        """Revient au bilan final après consultation de l'historique.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau de statistiques finales est restauré.
        """
        self.history_in_progress = False
        self.board_view.hide_history()
        self.board_view.show_end_game(
            self._show_end_history,
            self._return_home_after_game,
        )
        self.refresh()

    def _return_home_after_game(self) -> None:
        """Retourne directement au menu après la fin d'une partie.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback principal est exécuté sans confirmation d'abandon.
        """
        if callable(self.new_game_callback):
            self.new_game_callback()

    def _log(self, message: str) -> None:
        """Ajoute une ligne au journal et fait défiler vers le dernier événement.

        Entrées:
            message (str): Texte à ajouter.

        Sortie:
            None: Le journal graphique est mis à jour.
        """
        self.log_text.config(state="normal")
        self.log_text.insert("end", message.strip() + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _refresh_players(self) -> None:
        """Synchronise le tableau des joueurs avec l'état du moteur.

        Entrées:
            Aucune.

        Sortie:
            None: Les lignes du tableau sont reconstruites.
        """
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)

        for player in self.game.players:
            if player.bankrupt:
                status = "Faillite"
            elif player.in_jail:
                status = f"Prison {player.jail_turns}/{self.game.rules.max_jail_turns}"
            elif player is self.game.current_player:
                status = "À jouer"
            else:
                status = "Actif"
            tags: tuple[str, ...] = ()
            if player.bankrupt:
                tags = ("bankrupt",)
            elif player is self.game.current_player:
                tags = ("current",)
            self.players_tree.insert(
                "",
                "end",
                iid=str(player.player_id),
                text=f"● {player.name}",
                values=(
                    f"{player.cash} $",
                    player.position,
                    len(player.properties),
                    len(player.held_cards),
                    status,
                ),
                tags=tags,
            )

    def _set_button_state(self, button: ttk.Button, enabled: bool) -> None:
        """Active ou désactive un bouton ``ttk``.

        Entrées:
            button (ttk.Button): Bouton à modifier.
            enabled (bool): État souhaité.

        Sortie:
            None: L'état Tkinter du bouton est modifié.
        """
        button.state(["!disabled"] if enabled else ["disabled"])

    def refresh(self) -> None:
        """Actualise plateau, joueurs, dés et contrôles contextuels de prison.

        Entrées:
            Aucune autre que l'état courant du moteur.

        Sortie:
            None: Tous les widgets dynamiques sont synchronisés.
        """
        self.board_view.redraw()
        self._refresh_players()

        self.bank_stock_label.config(
            text=f"Banque : {self.game.bank.stock_text()}"
        )

        if self.game.is_over:
            winner = self.game.winner
            text = f"Partie terminée — {winner.name} gagne !" if winner else "Partie terminée"
            self.turn_label.config(text=text)
            self.status_label.config(text="")
            self.die_one.set_enabled(False)
            self.die_two.set_enabled(False)
            self.jail_controls.grid_remove()
            self._set_button_state(self.manage_button, False)
            self._set_button_state(self.trade_button, False)
            self._set_button_state(self.history_button, not self.history_in_progress)
            self._set_button_state(
                self.rules_button,
                not self.rules_in_progress and not self.history_in_progress,
            )
            self._set_button_state(self.save_button, self._can_save_now())
            return

        current = self.game.current_player
        color = PLAYER_COLORS[current.player_id % len(PLAYER_COLORS)]
        waiting = self.pending_purchase is not None
        building_waiting = self.pending_landing_build is not None
        rent_waiting = self.game.pending_rent_claim is not None
        auctioning = self.auction_in_progress
        building_auctioning = self.building_auction_in_progress
        trading = self.trade_in_progress
        managing = self.property_management_in_progress
        viewing_history = self.history_in_progress
        viewing_rules = self.rules_in_progress
        inspecting = self.inspection_in_progress
        in_jail = (
            current.in_jail
            and not waiting
            and not building_waiting
            and not rent_waiting
        )

        self.turn_label.config(
            text=f"Tour {self.game.upcoming_turn_number} — {current.name}"
        )
        self.status_label.config(
            text=(
                f"{current.cash} $ • case {current.position} • "
                f"{len(current.properties)} bien(s)"
                + (" • EN PRISON" if current.in_jail else "")
            ),
            foreground=color,
        )

        dice_enabled = (
            not waiting
            and not building_waiting
            and not rent_waiting
            and not auctioning
            and not building_auctioning
            and not trading
            and not managing
            and not viewing_history
            and not viewing_rules
            and not inspecting
        )
        self.die_one.set_enabled(dice_enabled)
        self.die_two.set_enabled(dice_enabled)

        self.bank_stock_label.config(
            text=f"Banque : {self.game.bank.stock_text()}"
        )

        if rent_waiting:
            claim = self.game.pending_rent_claim
            self.status_label.config(
                text=(
                    f"{claim.recipient.name} doit décider du loyer de "
                    f"{claim.amount} $ dû par {claim.payer.name}."
                )
            )
            self.dice_hint.config(text="Réclamez le loyer ou renoncez-y pour continuer.")
        elif viewing_rules:
            self.status_label.config(text="Consultation des règles de la partie.")
            self.dice_hint.config(text="Fermez le panneau pour reprendre la partie.")
        elif viewing_history:
            self.status_label.config(text="Consultation de l'historique et des statistiques.")
            self.dice_hint.config(text="Fermez le panneau pour reprendre la partie.")
        elif inspecting:
            self.status_label.config(text="Consultation d'une propriété du plateau.")
            self.dice_hint.config(text="Fermez la fiche pour reprendre le tour.")
        elif building_auctioning:
            self.status_label.config(text="Enchère de bâtiment en cours.")
            self.dice_hint.config(text="Terminez l'enchère de pénurie au centre du plateau.")
        elif managing:
            self.status_label.config(text=f"{current.name} gère son patrimoine.")
            self.dice_hint.config(text="Fermez la gestion des propriétés pour reprendre le tour.")
        elif trading:
            self.status_label.config(text=f"{current.name} prépare un échange.")
            self.dice_hint.config(text="Terminez ou annulez l'échange au centre du plateau.")
        elif auctioning and self.auction_source == "bankruptcy":
            self.status_label.config(text="Enchère obligatoire après faillite.")
            self.dice_hint.config(text="Terminez l'enchère au centre du plateau.")
        elif auctioning and self.pending_purchase is not None:
            _buyer, space = self.pending_purchase
            self.status_label.config(text=f"Enchère en cours pour {space.name}.")
            self.dice_hint.config(text="Terminez l'enchère au centre du plateau.")
        elif waiting:
            buyer, space = self.pending_purchase
            self.status_label.config(
                text=f"{buyer.name} doit décider pour {space.name} ({space.price} $)."
            )
            self.dice_hint.config(text="Décision d'achat en attente sur le plateau.")
        elif building_waiting:
            builder, property_ = self.pending_landing_build
            self.status_label.config(
                text=f"{builder.name} peut construire sur {property_.name}."
            )
            self.dice_hint.config(
                text="Choisissez les bâtiments ou passez avant de continuer."
            )
        elif in_jail:
            self.dice_hint.config(text="Cliquez sur un dé pour tenter un double.")
        else:
            self.dice_hint.config(text="Cliquez sur un dé pour lancer.")

        if rent_waiting:
            claim = self.game.pending_rent_claim
            self.rent_claim_frame.grid()
            self.rent_claim_label.configure(
                text=(
                    f"{claim.recipient.name} : {claim.amount} $ sur "
                    f"{self.game.board[claim.property_index].name}"
                )
            )
            self.rent_claim_button.configure(text=f"Réclamer {claim.amount} $")
        else:
            self.rent_claim_frame.grid_remove()

        if in_jail:
            self.jail_controls.grid()
            self.jail_pay_button.configure(
                text=f"Payer {self.game.rules.jail_fine} $"
            )
            self._set_button_state(
                self.jail_pay_button,
                not current.bankrupt,
            )
            self._set_button_state(self.jail_card_button, bool(current.held_cards))
        else:
            self.jail_controls.grid_remove()

        if waiting:
            property_player = self.pending_purchase[0]
        elif building_waiting:
            property_player = self.pending_landing_build[0]
        else:
            property_player = current
        self._set_button_state(
            self.manage_button,
            (
                bool(property_player.properties)
                and not waiting
                and not building_waiting
                and not rent_waiting
                and not auctioning
                and not building_auctioning
                and not trading
                and not managing
                and not viewing_history
                and not viewing_rules
                and not inspecting
            ),
        )
        self._set_button_state(
            self.trade_button,
            (
                len(self.game.active_players) >= 2
                and not waiting
                and not building_waiting
                and not rent_waiting
                and not auctioning
                and not building_auctioning
                and not trading
                and not managing
                and not viewing_history
                and not viewing_rules
                and not inspecting
            ),
        )
        self._set_button_state(
            self.history_button,
            (
                not waiting
                and not rent_waiting
                and not auctioning
                and not building_auctioning
                and not trading
                and not managing
                and not viewing_history
                and not viewing_rules
                and not inspecting
            ),
        )
        self._set_button_state(
            self.rules_button,
            (
                not waiting
                and not rent_waiting
                and not auctioning
                and not building_auctioning
                and not trading
                and not managing
                and not viewing_history
                and not viewing_rules
                and not inspecting
            ),
        )
        self._set_button_state(
            self.save_button,
            self._can_save_now(),
        )

    def _check_game_over(self) -> None:
        """Affiche une seule fois le bilan final intégré lorsqu'un vainqueur est déterminé.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau final remplace les anciennes boîtes d'information.
        """
        if not self.game.is_over or self.end_game_shown:
            return

        winner = self.game.winner
        if winner is not None:
            self._log(f"Victoire de {winner.name} !")
            self.game.record_event(
                "game_over",
                f"{winner.name} remporte la partie.",
                winner,
                reason=(
                    "turn_limit"
                    if self.game.reached_turn_limit
                    else "last_player"
                ),
                net_worth=self.game.player_net_worth(winner),
            )

        self.end_game_shown = True
        self.board_view.show_end_game(
            self._show_end_history,
            self._return_home_after_game,
        )
        self.refresh()
