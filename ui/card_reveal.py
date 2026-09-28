"""Grande carte animée intégrée au plateau pour Chance et Communauté."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from monopoly.cards import DrawnCardEvent


class CardRevealOverlay(tk.Frame):
    """Affiche une carte tirée au centre du plateau jusqu'à validation.

    Entrées:
        master (tk.Misc): Plateau parent.

    Sortie:
        CardRevealOverlay: Overlay intégré avec animation d'entrée/sortie.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit la carte et son bouton Continuer sans l'afficher.

        Entrées:
            master (tk.Misc): Parent graphique.

        Sortie:
            None: L'overlay est prêt à recevoir un événement de carte.
        """
        super().__init__(master, background="#172026", highlightthickness=0)
        self._on_close: Callable[[], None] | None = None
        self.card = tk.Frame(self, background="#FFFDF8", highlightbackground="#263238", highlightthickness=3, padx=0, pady=0)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.48, relheight=0.62)
        self.header = tk.Frame(self.card, background="#E59B31", height=82)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.deck_label = tk.Label(self.header, text="CHANCE", background="#E59B31", foreground="#FFFFFF", font=("Arial", 18, "bold"))
        self.deck_label.pack(expand=True)
        self.body = tk.Frame(self.card, background="#FFFDF8", padx=26, pady=22)
        self.body.pack(fill="both", expand=True)
        self.icon_label = tk.Label(self.body, text="?", background="#FFFDF8", foreground="#E59B31", font=("Arial", 46, "bold"))
        self.icon_label.pack()
        self.text_label = tk.Label(self.body, text="", background="#FFFDF8", foreground="#263238", font=("Arial", 14, "bold"), wraplength=440, justify="center")
        self.text_label.pack(expand=True, fill="both", pady=(8, 12))
        self.message_label = tk.Label(self.body, text="", background="#FFFDF8", foreground="#65717A", font=("Arial", 9), wraplength=440, justify="center")
        self.message_label.pack(fill="x", pady=(0, 12))
        ttk.Button(self.body, text="Continuer", style="Primary.TButton", command=self.hide).pack(fill="x")

    def show(self, event: DrawnCardEvent, on_close: Callable[[], None] | None = None) -> None:
        """Charge une carte puis anime son arrivée depuis le haut du plateau.

        Entrées:
            event (DrawnCardEvent): Carte réellement tirée.
            on_close (Callable[[], None] | None): Callback après validation.

        Sortie:
            None: L'overlay couvre le plateau jusqu'au clic Continuer.
        """
        self._on_close = on_close
        community = event.deck_name == "community_chest"
        color = "#4F95C8" if community else "#E59B31"
        title = "CAISSE DE COMMUNAUTÉ" if community else "CHANCE"
        icon = "▤" if community else "?"
        self.header.configure(background=color)
        self.deck_label.configure(text=title, background=color)
        self.icon_label.configure(text=icon, foreground=color)
        self.text_label.configure(text=getattr(event.card, "text", event.message))
        self.message_label.configure(text=event.message or "Effet appliqué.")
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.card.place_configure(rely=0.34)
        self._animate_to(0.50, 0)

    def _animate_to(self, target: float, step: int) -> None:
        """Interpôle verticalement la carte vers sa position centrale.

        Entrées:
            target (float): Position ``rely`` finale.
            step (int): Index d'animation courant.

        Sortie:
            None: La prochaine frame est planifiée jusqu'à stabilisation.
        """
        if not self.winfo_ismapped():
            return
        steps = 7
        if step >= steps:
            self.card.place_configure(rely=target)
            return
        start = 0.34
        value = start + (target - start) * ((step + 1) / steps)
        self.card.place_configure(rely=value)
        self.after(24, lambda: self._animate_to(target, step + 1))

    def hide(self) -> None:
        """Ferme la carte puis déclenche le callback de reprise du tour.

        Entrées:
            Aucune.

        Sortie:
            None: L'overlay disparaît et le contrôleur peut continuer.
        """
        self.place_forget()
        callback = self._on_close
        self._on_close = None
        if callback is not None:
            callback()
