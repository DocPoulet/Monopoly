"""Widgets graphiques réutilisables pour l'interface Monopoly."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class DiceFace(tk.Canvas):
    """Dessine un dé cliquable à six faces avec des points.

    Entrées:
        master (tk.Misc): Widget parent.
        size (int): Largeur et hauteur souhaitées en pixels.
        command (Callable[[], None] | None): Action exécutée lors d'un clic activé.

    Sortie:
        DiceFace: Canvas capable d'afficher et de lancer visuellement un dé.
    """

    PIP_LAYOUTS = {
        1: ((0.50, 0.50),),
        2: ((0.28, 0.28), (0.72, 0.72)),
        3: ((0.28, 0.28), (0.50, 0.50), (0.72, 0.72)),
        4: ((0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)),
        5: ((0.28, 0.28), (0.72, 0.28), (0.50, 0.50), (0.28, 0.72), (0.72, 0.72)),
        6: (
            (0.28, 0.25), (0.72, 0.25),
            (0.28, 0.50), (0.72, 0.50),
            (0.28, 0.75), (0.72, 0.75),
        ),
    }

    def __init__(
        self,
        master: tk.Misc,
        size: int = 72,
        command: Callable[[], None] | None = None,
    ) -> None:
        """Initialise le Canvas, son callback et ses événements de souris.

        Entrées:
            master (tk.Misc): Conteneur parent.
            size (int): Taille carrée nominale du dé.
            command (Callable[[], None] | None): Callback exécuté au clic.

        Sortie:
            None: Le dé est créé dans son état vide et activé.
        """
        super().__init__(
            master,
            width=size,
            height=size,
            background="#EEF2F5",
            highlightthickness=0,
            cursor="hand2",
        )
        self.size = size
        self.value: int | None = None
        self.command = command
        self.enabled = True
        self.hovered = False
        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.set_value(None)

    def _on_resize(self, event: tk.Event) -> None:
        """Redessine la face lorsque le Canvas change de taille.

        Entrées:
            event (tk.Event): Événement de redimensionnement Tkinter.

        Sortie:
            None: La face actuelle est recalculée à la nouvelle taille.
        """
        self.set_value(self.value)

    def _on_click(self, event: tk.Event) -> None:
        """Exécute le callback de lancer lorsque le dé est cliquable.

        Entrées:
            event (tk.Event): Événement de clic souris.

        Sortie:
            None: Le callback est exécuté uniquement si le dé est activé.
        """
        if self.enabled and self.command is not None:
            self.command()

    def _on_enter(self, event: tk.Event) -> None:
        """Active l'effet de survol visuel du dé.

        Entrées:
            event (tk.Event): Événement d'entrée du pointeur.

        Sortie:
            None: Le dé est redessiné avec son contour de survol.
        """
        self.hovered = True
        self.set_value(self.value)

    def _on_leave(self, event: tk.Event) -> None:
        """Supprime l'effet de survol lorsque le pointeur quitte le dé.

        Entrées:
            event (tk.Event): Événement de sortie du pointeur.

        Sortie:
            None: Le dé revient à son apparence normale.
        """
        self.hovered = False
        self.set_value(self.value)

    def set_enabled(self, enabled: bool) -> None:
        """Active ou désactive le clic sur le dé et adapte son curseur.

        Entrées:
            enabled (bool): ``True`` pour autoriser le lancer au clic.

        Sortie:
            None: L'état interactif et l'apparence du dé sont actualisés.
        """
        self.enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self.set_value(self.value)

    def set_value(self, value: int | None) -> None:
        """Affiche une valeur de dé ou une face vide avant le premier lancer.

        Entrées:
            value (int | None): Valeur de 1 à 6, ou ``None`` pour une face vide.

        Sortie:
            None: Le Canvas est entièrement redessiné.

        Lève:
            ValueError: Si une valeur différente de 1 à 6 ou ``None`` est fournie.
        """
        if value is not None and value not in self.PIP_LAYOUTS:
            raise ValueError("Un dé doit afficher une valeur comprise entre 1 et 6.")

        self.value = value
        self.delete("all")

        width = max(self.winfo_width(), self.size)
        height = max(self.winfo_height(), self.size)
        side = min(width, height) - 8
        x1 = (width - side) / 2
        y1 = (height - side) / 2
        x2 = x1 + side
        y2 = y1 + side

        shadow = "#C7CED4" if self.enabled else "#D7DADD"
        face = "#FFFFFF" if self.enabled else "#ECEFF1"
        outline = "#4479B8" if self.enabled and self.hovered else "#A8B1B9"
        width_outline = 3 if self.enabled and self.hovered else 2
        pip = "#20262C" if self.enabled else "#9AA2A8"

        self.create_rectangle(
            x1 + 3, y1 + 5, x2 + 3, y2 + 5,
            fill=shadow, outline="",
        )
        self.create_rectangle(
            x1, y1, x2, y2,
            fill=face, outline=outline, width=width_outline,
        )

        if value is None:
            self.create_text(
                width / 2, height / 2,
                text="?",
                font=("Arial", int(side * 0.42), "bold"),
                fill="#9EA8AF" if self.enabled else "#B7BEC3",
            )
            return

        radius = max(4, side * 0.075)
        for rel_x, rel_y in self.PIP_LAYOUTS[value]:
            cx = x1 + side * rel_x
            cy = y1 + side * rel_y
            self.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill=pip, outline="",
            )


class SectionTitle(ttk.Frame):
    """Affiche un petit titre de section avec un sous-titre facultatif.

    Entrées:
        master (tk.Misc): Widget parent.
        title (str): Titre principal.
        subtitle (str): Texte secondaire facultatif.

    Sortie:
        SectionTitle: En-tête compact réutilisable dans les panneaux latéraux.
    """

    def __init__(self, master: tk.Misc, title: str, subtitle: str = "") -> None:
        """Construit les deux libellés de l'en-tête.

        Entrées:
            master (tk.Misc): Conteneur parent.
            title (str): Titre principal.
            subtitle (str): Sous-titre optionnel.

        Sortie:
            None: Les libellés sont créés et placés.
        """
        super().__init__(master)
        ttk.Label(self, text=title, style="SectionTitle.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(self, text=subtitle, style="Muted.TLabel").pack(anchor="w")
