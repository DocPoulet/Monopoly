"""Panneau d'enchère intégré pour les maisons et hôtels en pénurie."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from monopoly.building_auction import BuildingAuction, BuildingAuctionResult
from monopoly.player import Player
from monopoly.properties import Property

from .property_card import PropertyCardOverlay


class BuildingAuctionOverlay(tk.Frame):
    """Pilote une enchère de bâtiment directement dans le plateau.

    Entrées:
        master (tk.Misc): Conteneur parent, généralement ``BoardView``.

    Sortie:
        BuildingAuctionOverlay: Panneau réutilisable masqué hors enchère.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit l'en-tête, la cible de construction et les contrôles d'offre.

        Entrées:
            master (tk.Misc): Conteneur graphique parent.

        Sortie:
            None: Le panneau est créé puis masqué.
        """
        super().__init__(
            master,
            background="#DCE3E7",
            highlightbackground="#8E9AA3",
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        self.auction: BuildingAuction | None = None
        self.bidder_index = 0
        self.on_finished: Callable[[BuildingAuctionResult], None] | None = None
        self.target_map: dict[str, Property] = {}

        card = tk.Frame(
            self,
            background="#FFFFFF",
            highlightbackground="#29323A",
            highlightthickness=2,
        )
        card.pack(fill="both", expand=True)

        self.header = tk.Frame(card, background="#2F6B45", height=76)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.header_type = tk.Label(
            self.header,
            text="PÉNURIE DE BÂTIMENTS",
            background="#2F6B45",
            foreground="#E9F5ED",
            font=("Arial", 9, "bold"),
        )
        self.header_type.pack(pady=(10, 0))

        self.header_name = tk.Label(
            self.header,
            text="ENCHÈRE MAISON",
            background="#2F6B45",
            foreground="#FFFFFF",
            font=("Arial", 18, "bold"),
        )
        self.header_name.pack(pady=(2, 8))

        body = tk.Frame(card, background="#FFFFFF", padx=20, pady=14)
        body.pack(fill="both", expand=True)

        self.stock_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#64717A",
            font=("Arial", 9),
        )
        self.stock_label.pack()

        self.highest_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#1F2933",
            font=("Arial", 12, "bold"),
        )
        self.highest_label.pack(pady=(8, 6))

        self.bidder_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#2E5F87",
            font=("Arial", 11, "bold"),
        )
        self.bidder_label.pack(pady=(2, 8))

        target_row = tk.Frame(body, background="#FFFFFF")
        target_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            target_row,
            text="Terrain cible :",
            background="#FFFFFF",
            foreground="#46515C",
            font=("Arial", 9, "bold"),
        ).pack(side="left")
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(
            target_row,
            textvariable=self.target_var,
            state="readonly",
            width=25,
        )
        self.target_combo.pack(side="right")

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

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(2, 8))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        ttk.Button(
            buttons,
            text="Enchérir",
            style="Primary.TButton",
            command=self._place_bid,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(
            buttons,
            text="Je n'en veux pas",
            command=self._withdraw,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.error_label = tk.Label(
            body,
            text="",
            background="#FFFFFF",
            foreground="#B13B3B",
            wraplength=430,
            justify="center",
            font=("Arial", 8, "bold"),
        )
        self.error_label.pack(fill="x", pady=(0, 7))

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

        self.place_forget()

    def show(
        self,
        auction: BuildingAuction,
        on_finished: Callable[[BuildingAuctionResult], None],
    ) -> None:
        """Affiche une enchère de bâtiment au centre du plateau.

        Entrées:
            auction (BuildingAuction): Enchère métier à piloter.
            on_finished (Callable[[BuildingAuctionResult], None]): Callback final.

        Sortie:
            None: Le panneau devient visible et invite le premier participant.
        """
        self.auction = auction
        self.bidder_index = 0
        self.on_finished = on_finished
        self.error_label.configure(text="")
        self.header_name.configure(
            text=f"ENCHÈRE {auction.display_name.upper()}"
        )
        self.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.56,
            relheight=0.64,
        )
        self.lift()
        self._refresh()

    def hide(self) -> None:
        """Masque le panneau et réinitialise son état temporaire.

        Entrées:
            Aucune.

        Sortie:
            None: Les références d'enchère et les champs sont vidés.
        """
        self.place_forget()
        self.auction = None
        self.bidder_index = 0
        self.on_finished = None
        self.target_map = {}
        self.target_var.set("")
        self.amount_var.set("")
        self.error_label.configure(text="")

    def _on_enter_key(self, event: tk.Event) -> None:
        """Valide l'offre lorsqu'Entrée est pressée.

        Entrées:
            event (tk.Event): Événement clavier Tkinter.

        Sortie:
            None: L'action d'enchère courante est déclenchée.
        """
        self._place_bid()

    def _current_bidder(self) -> Player | None:
        """Retourne le joueur devant actuellement agir.

        Entrées:
            Aucune.

        Sortie:
            Player | None: Participant courant ou ``None`` si l'enchère peut finir.
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
            self.bidder_index = (self.bidder_index + 1) % len(
                self.auction.active_bidders
            )
            attempts += 1
        return None

    def _advance_bidder(self) -> None:
        """Passe au participant actif suivant.

        Entrées:
            Aucune.

        Sortie:
            None: L'index circulaire du joueur est avancé.
        """
        if self.auction is not None and self.auction.active_bidders:
            self.bidder_index = (self.bidder_index + 1) % len(
                self.auction.active_bidders
            )

    def _refresh_targets(self, bidder: Player) -> None:
        """Actualise la liste des terrains où le participant peut construire.

        Entrées:
            bidder (Player): Joueur qui doit choisir une cible.

        Sortie:
            None: Le ``Combobox`` contient uniquement les terrains légaux.
        """
        if self.auction is None:
            return

        targets = self.auction.eligible_targets(bidder)
        self.target_map = {
            f"{target.name} — niveau {target.development_level}": target
            for target in targets
        }
        values = list(self.target_map)
        self.target_combo["values"] = values

        if values:
            self.target_var.set(values[0])
        else:
            self.target_var.set("")

    def _selected_target(self) -> Property | None:
        """Retourne le terrain actuellement choisi dans la liste.

        Entrées:
            Aucune.

        Sortie:
            Property | None: Terrain associé au libellé sélectionné.
        """
        return self.target_map.get(self.target_var.get())

    def _place_bid(self) -> None:
        """Tente d'enregistrer l'offre et la cible du participant courant.

        Entrées:
            Aucune autre que les champs visibles.

        Sortie:
            None: L'offre devient la meilleure ou une erreur locale est affichée.
        """
        if self.auction is None:
            return

        bidder = self._current_bidder()
        if bidder is None:
            self._finish_if_possible()
            return

        target = self._selected_target()
        if target is None:
            self.error_label.configure(text="Choisissez un terrain cible.")
            return

        try:
            amount = int(self.amount_var.get())
        except ValueError:
            self.error_label.configure(text="Saisissez un montant entier.")
            return

        if not self.auction.place_bid(bidder, amount, target):
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
        """Retire le joueur courant de l'enchère de bâtiment.

        Entrées:
            Aucune.

        Sortie:
            None: Le participant abandonne et le suivant prend la main.
        """
        if self.auction is None:
            return

        bidder = self._current_bidder()
        if bidder is None:
            self._finish_if_possible()
            return

        if not self.auction.withdraw(bidder):
            self.error_label.configure(
                text="Le meilleur enchérisseur ne peut pas abandonner maintenant."
            )
            return

        self.error_label.configure(text="")
        if self.bidder_index >= len(self.auction.active_bidders):
            self.bidder_index = 0
        self._refresh()

    def _refresh(self) -> None:
        """Synchronise stock, meilleure offre, participant et cibles.

        Entrées:
            Aucune.

        Sortie:
            None: Tous les libellés et champs reflètent l'état métier.
        """
        if self.auction is None:
            return

        if self._finish_if_possible():
            return

        winner = (
            self.auction.highest_bidder.name
            if self.auction.highest_bidder is not None
            else "personne"
        )
        self.stock_label.configure(
            text=(
                f"Stock actuel : {self.auction.stock_available} "
                f"{self.auction.display_name}(s)"
            )
        )
        self.highest_label.configure(
            text=f"Meilleure offre : {self.auction.highest_bid} $ — {winner}"
        )

        bidder = self._current_bidder()
        if bidder is not None:
            self.bidder_label.configure(
                text=f"À {bidder.name} de jouer — {bidder.cash} $ disponibles"
            )
            self._refresh_targets(bidder)
            self.amount_var.set(str(self.auction.highest_bid + 1))
            self.amount_entry.focus_set()

        lines = []
        for player in self.auction.active_bidders:
            marker = " ← meilleure offre" if player is self.auction.highest_bidder else ""
            targets = len(self.auction.eligible_targets(player))
            lines.append(
                f"• {player.name} — {player.cash} $ — {targets} cible(s){marker}"
            )
        self.players_label.configure(text="\n".join(lines))

    def _finish_if_possible(self) -> bool:
        """Clôture l'enchère lorsque le moteur l'autorise.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` si le panneau a été clôturé.
        """
        if self.auction is None or not self.auction.can_finish:
            return False

        result = self.auction.finish()
        callback = self.on_finished
        self.hide()

        if callback is not None:
            callback(result)
        return True
