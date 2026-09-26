"""Fenêtre principale reliant l'interface Tkinter au moteur POO."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from monopoly import Game
from monopoly.auction import AuctionResult
from monopoly.player import Player
from monopoly.properties import OwnableSpace

from .board_view import BoardView, PLAYER_COLORS
from .dialogs import PropertyManagerDialog
from .widgets import DiceFace


class GameWindow(ttk.Frame):
    """Présente une partie jouable et traduit les interactions en appels du moteur.

    Entrées:
        master (tk.Misc): Conteneur parent.
        game (Game): Partie à afficher et contrôler.
        new_game_callback (callable): Fonction appelée pour créer une nouvelle partie.

    Sortie:
        GameWindow: Interface complète du plateau et du panneau de contrôle.
    """

    def __init__(self, master: tk.Misc, game: Game, new_game_callback: object) -> None:
        """Construit le plateau, les dés cliquables et les informations joueurs.

        Entrées:
            master (tk.Misc): Conteneur parent.
            game (Game): Moteur de la partie.
            new_game_callback (object): Callback du bouton Nouvelle partie.

        Sortie:
            None: Tous les widgets sont créés et synchronisés.
        """
        super().__init__(master, padding=10)
        self.game = game
        self.new_game_callback = new_game_callback
        self.pending_purchase: tuple[Player, OwnableSpace] | None = None
        self.last_result_player: Player | None = None
        self.auction_in_progress = False

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        self.board_view = BoardView(self, game)
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
        self._log("Nouvelle partie créée.")
        self._log(f"C'est à {self.game.current_player.name} de jouer.")
        self.refresh()

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
        ttk.Button(
            frame,
            text="Nouvelle partie",
            command=self._request_new_game,
        ).grid(row=0, column=1, sticky="e")
        self.status_label = ttk.Label(frame, text="")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 0))

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
        """Crée uniquement l'action générale de gestion des propriétés.

        Entrées:
            Aucune.

        Sortie:
            None: Aucun bouton Achat, Enchères ou Lancer n'est ajouté à droite.
        """
        frame = ttk.LabelFrame(self.sidebar, text="Gestion", padding=8)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(0, weight=1)
        self.manage_button = ttk.Button(
            frame,
            text="Gérer mes propriétés",
            command=self._manage_properties,
        )
        self.manage_button.grid(row=0, column=0, sticky="ew")

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

    def _request_new_game(self) -> None:
        """Demande confirmation avant d'abandonner la partie en cours.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback de nouvelle partie est appelé après confirmation.
        """
        confirmed = messagebox.askyesno(
            "Nouvelle partie",
            "Abandonner la partie actuelle et en commencer une nouvelle ?",
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
        if self.pending_purchase is not None:
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
            notes.append("+200 Départ")
        total = sum(result.dice)
        headline = f"Total : {total}" if total else "Pas de déplacement"
        self.dice_note.config(text="\n".join([headline, *notes]))

        self._log(
            f"Tour {result.turn_number} — {result.player.name} : "
            f"{result.dice[0]} + {result.dice[1]}."
        )
        if result.message:
            self._log(result.message)
        if result.player.bankrupt:
            self._log(f"{result.player.name} est en faillite.")

        for event in self.game.drawn_cards_this_turn:
            self.board_view.display_drawn_card(event)

        space = self.game.board.get_player_space(result.player)
        if (
            not result.player.bankrupt
            and isinstance(space, OwnableSpace)
            and space.owner is None
        ):
            self.pending_purchase = (result.player, space)
            self._log(
                f"Décision requise : acheter {space.name} pour {space.price} $ "
                "ou lancer l'enchère."
            )

        self.refresh()
        self._show_purchase_card_if_needed()
        self._check_game_over()

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
        auction = self.game.start_auction(space)
        self.auction_in_progress = True
        self._log(f"Enchère ouverte pour {space.name}.")
        self.board_view.show_auction(auction, self._finish_auction)
        self.refresh()

    def _finish_auction(self, result: AuctionResult) -> None:
        """Finalise visuellement l'enchère intégrée et libère le tour.

        Entrées:
            result (AuctionResult): Résultat produit par le moteur d'enchères.

        Sortie:
            None: Le résultat est journalisé, le panneau disparaît et le jeu reprend.
        """
        if result.sold and result.winner is not None:
            self._log(
                f"{result.winner.name} remporte {result.space.name} "
                f"pour {result.amount} $."
            )
        else:
            self._log(f"{result.space.name} reste à la banque.")
        self.auction_in_progress = False
        self.pending_purchase = None
        self.board_view.hide_auction()
        self.board_view.hide_purchase_card()
        self.refresh()

    def _manage_properties(self) -> None:
        """Ouvre la fenêtre de gestion des biens du joueur qui doit agir.

        Entrées:
            Aucune.

        Sortie:
            None: Les modifications immobilières sont appliquées au moteur puis affichées.
        """
        player = self.pending_purchase[0] if self.pending_purchase else self.game.current_player
        if not player.properties:
            messagebox.showinfo(
                "Propriétés",
                f"{player.name} ne possède encore aucun bien.",
                parent=self,
            )
            return
        dialog = PropertyManagerDialog(self, self.game, player)
        self.wait_window(dialog)
        if dialog.changed:
            self._log(f"{player.name} a modifié son patrimoine.")
        self.refresh()

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
                status = f"Prison {player.jail_turns}/3"
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

        if self.game.is_over:
            winner = self.game.winner
            text = f"Partie terminée — {winner.name} gagne !" if winner else "Partie terminée"
            self.turn_label.config(text=text)
            self.status_label.config(text="")
            self.die_one.set_enabled(False)
            self.die_two.set_enabled(False)
            self.jail_controls.grid_remove()
            self._set_button_state(self.manage_button, False)
            return

        current = self.game.current_player
        color = PLAYER_COLORS[current.player_id % len(PLAYER_COLORS)]
        waiting = self.pending_purchase is not None
        auctioning = self.auction_in_progress
        in_jail = current.in_jail and not waiting

        self.turn_label.config(text=f"Tour de {current.name}")
        self.status_label.config(
            text=(
                f"{current.cash} $ • case {current.position} • "
                f"{len(current.properties)} bien(s)"
                + (" • EN PRISON" if current.in_jail else "")
            ),
            foreground=color,
        )

        dice_enabled = not waiting and not auctioning
        self.die_one.set_enabled(dice_enabled)
        self.die_two.set_enabled(dice_enabled)

        if auctioning and self.pending_purchase is not None:
            _buyer, space = self.pending_purchase
            self.status_label.config(text=f"Enchère en cours pour {space.name}.")
            self.dice_hint.config(text="Terminez l'enchère au centre du plateau.")
        elif waiting:
            buyer, space = self.pending_purchase
            self.status_label.config(
                text=f"{buyer.name} doit décider pour {space.name} ({space.price} $)."
            )
            self.dice_hint.config(text="Décision d'achat en attente sur le plateau.")
        elif in_jail:
            self.dice_hint.config(text="Cliquez sur un dé pour tenter un double.")
        else:
            self.dice_hint.config(text="Cliquez sur un dé pour lancer.")

        if in_jail:
            self.jail_controls.grid()
            self._set_button_state(
                self.jail_pay_button,
                current.can_afford(self.game.rules.JAIL_FINE),
            )
            self._set_button_state(self.jail_card_button, bool(current.held_cards))
        else:
            self.jail_controls.grid_remove()

        property_player = self.pending_purchase[0] if waiting else current
        self._set_button_state(
            self.manage_button,
            bool(property_player.properties) and not auctioning,
        )

    def _check_game_over(self) -> None:
        """Affiche une notification lorsqu'un vainqueur est déterminé.

        Entrées:
            Aucune.

        Sortie:
            None: Une boîte d'information annonce le vainqueur à la fin de la partie.
        """
        if not self.game.is_over:
            return
        winner = self.game.winner
        if winner is not None:
            self._log(f"Victoire de {winner.name} !")
            messagebox.showinfo(
                "Fin de partie",
                f"{winner.name} remporte la partie !",
                parent=self,
            )
