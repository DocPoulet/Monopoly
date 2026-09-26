"""Panneau d'enchère intégré directement au plateau graphique."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from monopoly.auction import Auction, AuctionResult
from monopoly.player import Player

from .property_card import PropertyCardOverlay


class AuctionOverlay(tk.Frame):
    """Gère une enchère dans le plateau sans ouvrir de fenêtre secondaire.

    Entrées:
        master (tk.Misc): Conteneur parent, généralement ``BoardView``.

    Sortie:
        AuctionOverlay: Panneau superposé réutilisable pour toutes les enchères.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit la carte d'enchère et ses contrôles interactifs.

        Entrées:
            master (tk.Misc): Conteneur graphique qui recevra le panneau.

        Sortie:
            None: Le panneau est créé mais reste caché jusqu'à ``show``.
        """
        super().__init__(
            master,
            background="#DCE3E7",
            highlightbackground="#8E9AA3",
            highlightthickness=1,
            padx=8,
            pady=8,
        )
        self.auction: Auction | None = None
        self.bidder_index = 0
        self.on_finished: Callable[[AuctionResult], None] | None = None

        self.card = tk.Frame(
            self,
            background="#FFFFFF",
            highlightbackground="#29323A",
            highlightthickness=2,
        )
        self.card.pack(fill="both", expand=True)

        self.header = tk.Frame(self.card, background="#34495E", height=72)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.header_title_label = tk.Label(
            self.header,
            text="ENCHÈRE",
            background="#34495E",
            foreground="#F7FAFC",
            font=("Arial", 9, "bold"),
        )
        self.header_title_label.pack(pady=(8, 0))
        self.name_label = tk.Label(
            self.header,
            text="",
            background="#34495E",
            foreground="#FFFFFF",
            font=("Arial", 16, "bold"),
        )
        self.name_label.pack(pady=(1, 7))

        body = tk.Frame(self.card, background="#FFFFFF", padx=18, pady=12)
        body.pack(fill="both", expand=True)

        self.price_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#66727B",
            font=("Arial", 9),
        )
        self.price_label.pack()

        self.highest_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#1F2933",
            font=("Arial", 11, "bold"),
        )
        self.highest_label.pack(pady=(6, 8))

        self.bidder_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#2E5F87",
            font=("Arial", 11, "bold"),
        )
        self.bidder_label.pack(pady=(2, 8))

        amount_row = tk.Frame(body, background="#FFFFFF")
        amount_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            amount_row,
            text="Votre offre :",
            background="#FFFFFF",
            foreground="#46515C",
            font=("Arial", 9, "bold"),
        ).pack(side="left")
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(
            amount_row,
            textvariable=self.amount_var,
            justify="center",
            width=12,
        )
        self.amount_entry.pack(side="right")
        self.amount_entry.bind("<Return>", self._on_enter_key)

        button_row = ttk.Frame(body)
        button_row.pack(fill="x", pady=(2, 8))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)

        self.bid_button = ttk.Button(
            button_row,
            text="Enchérir",
            style="Primary.TButton",
            command=self._place_bid,
        )
        self.bid_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.withdraw_button = ttk.Button(
            button_row,
            text="Abandonner",
            command=self._withdraw,
        )
        self.withdraw_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.error_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#B13B3B",
            wraplength=365,
            justify="center",
            font=("Arial", 8, "bold"),
        )
        self.error_label.pack(fill="x", pady=(0, 6))

        tk.Frame(body, height=1, background="#DDE3E7").pack(fill="x", pady=(0, 8))
        self.players_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#4F5B64",
            justify="left",
            anchor="w",
            font=("Arial", 8),
        )
        self.players_label.pack(fill="x")

    def show(
        self,
        auction: Auction,
        on_finished: Callable[[AuctionResult], None],
    ) -> None:
        """Charge une enchère et affiche le panneau au centre du plateau.

        Entrées:
            auction (Auction): Enchère métier déjà créée par ``Game``.
            on_finished (Callable[[AuctionResult], None]): Callback recevant le résultat final.

        Sortie:
            None: Le panneau devient visible et le premier joueur est invité à agir.
        """
        self.auction = auction
        self.bidder_index = 0
        self.on_finished = on_finished
        self.error_label.configure(text="")
        header_color = PropertyCardOverlay._header_color(auction.space)
        self.header.configure(background=header_color)
        self.header_title_label.configure(background=header_color)
        self.name_label.configure(
            text=auction.space.name.upper(),
            background=header_color,
        )
        self.price_label.configure(text=f"Prix affiché : {auction.space.price} $")
        self.place(relx=0.70, rely=0.50, anchor="center", width=350)
        self.lift()
        self._refresh()

    def hide(self) -> None:
        """Masque le panneau et réinitialise les références de l'enchère précédente.

        Entrées:
            Aucune.

        Sortie:
            None: Le panneau disparaît et libère son état temporaire.
        """
        self.place_forget()
        self.auction = None
        self.bidder_index = 0
        self.on_finished = None
        self.amount_var.set("")
        self.error_label.configure(text="")

    def _on_enter_key(self, event: tk.Event) -> None:
        """Valide l'offre quand le joueur appuie sur Entrée dans le champ de montant.

        Entrées:
            event (tk.Event): Événement clavier Tkinter.

        Sortie:
            None: La même action que le bouton Enchérir est exécutée.
        """
        self._place_bid()

    def _current_bidder(self) -> Player | None:
        """Retourne le participant qui doit actuellement prendre une décision.

        Entrées:
            Aucune autre que l'état interne de l'enchère.

        Sortie:
            Player | None: Participant actif courant, ou ``None`` si l'enchère peut finir.
        """
        if self.auction is None:
            return None
        if self.auction.can_finish or not self.auction.active_bidders:
            return None

        attempts = 0
        while attempts < len(self.auction.active_bidders):
            self.bidder_index %= len(self.auction.active_bidders)
            bidder = self.auction.active_bidders[self.bidder_index]
            if bidder is not self.auction.highest_bidder:
                return bidder
            self.bidder_index = (self.bidder_index + 1) % len(self.auction.active_bidders)
            attempts += 1
        return None

    def _advance_bidder(self) -> None:
        """Passe au participant actif suivant dans l'ordre de l'enchère.

        Entrées:
            Aucune.

        Sortie:
            None: L'index circulaire du participant est avancé.
        """
        if self.auction is not None and self.auction.active_bidders:
            self.bidder_index = (self.bidder_index + 1) % len(
                self.auction.active_bidders
            )

    def _place_bid(self) -> None:
        """Tente d'enregistrer l'offre saisie pour le participant courant.

        Entrées:
            Aucune autre que le champ de saisie et l'état de l'enchère.

        Sortie:
            None: L'offre est appliquée ou une erreur est affichée dans le panneau.
        """
        if self.auction is None:
            return
        bidder = self._current_bidder()
        if bidder is None:
            self._finish_if_possible()
            return

        try:
            amount = int(self.amount_var.get())
        except ValueError:
            self.error_label.configure(text="Saisissez un montant entier.")
            return

        if not self.auction.place_bid(bidder, amount):
            self.error_label.configure(
                text=(
                    f"L'offre doit dépasser {self.auction.highest_bid} $ et rester "
                    f"dans le budget de {bidder.name} ({bidder.cash} $)."
                )
            )
            return

        self.error_label.configure(text="")
        self._advance_bidder()
        self._refresh()

    def _withdraw(self) -> None:
        """Retire définitivement le participant courant de l'enchère.

        Entrées:
            Aucune autre que l'état du panneau.

        Sortie:
            None: Le joueur abandonne puis le panneau passe au participant suivant.
        """
        if self.auction is None:
            return
        bidder = self._current_bidder()
        if bidder is None:
            self._finish_if_possible()
            return

        if not self.auction.withdraw(bidder):
            self.error_label.configure(
                text="Le meilleur enchérisseur ne peut pas abandonner tant qu'il reste d'autres joueurs."
            )
            return

        self.error_label.configure(text="")
        if self.bidder_index >= len(self.auction.active_bidders):
            self.bidder_index = 0
        self._refresh()

    def _refresh(self) -> None:
        """Actualise le meilleur prix, le joueur courant et les participants actifs.

        Entrées:
            Aucune autre que l'enchère chargée.

        Sortie:
            None: Tous les textes et états de boutons sont synchronisés.
        """
        if self.auction is None:
            return
        if self._finish_if_possible():
            return

        highest_name = (
            self.auction.highest_bidder.name
            if self.auction.highest_bidder is not None
            else "personne"
        )
        self.highest_label.configure(
            text=f"Meilleure offre : {self.auction.highest_bid} $ — {highest_name}"
        )

        bidder = self._current_bidder()
        if bidder is not None:
            self.bidder_label.configure(
                text=f"À {bidder.name} de jouer • {bidder.cash} $ disponibles"
            )
            next_bid = self.auction.highest_bid + 1
            self.amount_var.set(str(next_bid))
            can_outbid = bidder.cash >= next_bid
            self.bid_button.state(["!disabled"] if can_outbid else ["disabled"])
            self.withdraw_button.state(["!disabled"])
            self.amount_entry.state(["!disabled"] if can_outbid else ["disabled"])
            if can_outbid:
                self.amount_entry.focus_set()
        else:
            self.bid_button.state(["disabled"])
            self.withdraw_button.state(["disabled"])
            self.amount_entry.state(["disabled"])

        lines: list[str] = []
        for player in self.auction.active_bidders:
            marker = "  ← meilleure offre" if player is self.auction.highest_bidder else ""
            lines.append(f"• {player.name} — {player.cash} ${marker}")
        self.players_label.configure(
            text="Joueurs encore en lice :\n" + ("\n".join(lines) or "Aucun")
        )

    def _finish_if_possible(self) -> bool:
        """Clôture l'enchère si le moteur indique qu'elle est terminée.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` si le résultat final a été produit et transmis au parent.
        """
        if self.auction is None or not self.auction.can_finish:
            return False

        result = self.auction.finish()
        callback = self.on_finished
        self.hide()
        if callback is not None:
            callback(result)
        return True
