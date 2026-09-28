"""Widgets graphiques réutilisables pour l'interface Monopoly."""

from __future__ import annotations

import random
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

    def animate_roll(
        self,
        final_value: int,
        speed: str = "normal",
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        """Anime rapidement plusieurs faces puis s'arrête sur la valeur réelle.

        Entrées:
            final_value (int): Résultat moteur final compris entre 1 et 6.
            speed (str): ``normal``, ``fast`` ou ``off``.
            on_complete (Callable[[], None] | None): Callback appelé après la dernière face.

        Sortie:
            None: Le dé change visuellement puis signale la fin de l'animation.
        """
        if final_value not in self.PIP_LAYOUTS:
            raise ValueError("La valeur finale du dé doit être comprise entre 1 et 6.")
        if speed == "off":
            self.set_value(final_value)
            if on_complete is not None:
                self.after_idle(on_complete)
            return
        frames = 7 if speed == "normal" else 4
        delay = 48 if speed == "normal" else 26
        system_random = random.SystemRandom()

        def step(index: int) -> None:
            """Affiche une frame aléatoire puis planifie la suivante.

            Entrées:
                index (int): Numéro de frame déjà jouée.

            Sortie:
                None: La séquence se termine sur ``final_value``.
            """
            if not self.winfo_exists():
                return
            if index >= frames:
                self.set_value(final_value)
                if on_complete is not None:
                    self.after_idle(on_complete)
                return
            self.set_value(system_random.randint(1, 6))
            self.after(delay, lambda: step(index + 1))

        step(0)


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

class TreeviewMultiSorter:
    """Ajoute un tri multi-colonnes cyclique à un ``ttk.Treeview``.

    Entrées:
        tree (ttk.Treeview): Tableau dont les en-têtes deviennent cliquables.
        labels (dict[str, str]): Libellés de base des colonnes, ``#0`` compris si présent.

    Sortie:
        TreeviewMultiSorter: Contrôleur conservant l'ordre de clic et l'état des tris.
    """

    _RANK_SYMBOLS = ("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨")

    def __init__(self, tree: ttk.Treeview, labels: dict[str, str]) -> None:
        """Mémorise le tableau et installe les commandes de tri sur ses titres.

        Entrées:
            tree (ttk.Treeview): Tableau à rendre triable.
            labels (dict[str, str]): Texte original de chaque en-tête.

        Sortie:
            None: Les colonnes sont prêtes pour le cycle croissant/décroissant/aucun.
        """
        self.tree = tree
        self.labels = dict(labels)
        self.criteria: list[tuple[str, int]] = []
        self.base_order: list[str] = list(tree.get_children(""))
        self._install_headings()

    def _install_headings(self) -> None:
        """Associe chaque en-tête connu au gestionnaire de clic.

        Entrées:
            Aucune.

        Sortie:
            None: Chaque titre appelle ``cycle`` avec sa colonne.
        """
        for column, label in self.labels.items():
            self.tree.heading(
                column,
                text=label,
                command=lambda current=column: self.cycle(current),
            )

    def refresh_base_order(self, reset_sort: bool = False) -> None:
        """Actualise l'ordre naturel après remplissage du tableau puis réapplique le tri.

        Entrées:
            reset_sort (bool): Efface les critères actifs lorsque vrai.

        Sortie:
            None: L'ordre de référence correspond aux lignes actuellement présentes.
        """
        self.base_order = list(self.tree.get_children(""))
        if reset_sort:
            self.criteria.clear()
        self.apply()

    def cycle(self, column: str) -> None:
        """Fait évoluer une colonne entre croissant, décroissant puis aucun tri.

        Entrées:
            column (str): Identifiant Treeview de la colonne cliquée.

        Sortie:
            None: Les critères sont mis à jour en conservant l'ordre des autres clics.
        """
        position = next(
            (index for index, (name, _) in enumerate(self.criteria) if name == column),
            None,
        )
        if position is None:
            self.criteria.append((column, 1))
        else:
            direction = self.criteria[position][1]
            if direction == 1:
                self.criteria[position] = (column, -1)
            else:
                self.criteria.pop(position)
        self.apply()

    def apply(self) -> None:
        """Réordonne les lignes selon tous les critères actifs dans l'ordre des clics.

        Entrées:
            Aucune.

        Sortie:
            None: Les lignes et les indicateurs d'en-tête sont actualisés.
        """
        children = list(self.tree.get_children(""))
        if not self.criteria:
            ordered = [item for item in self.base_order if item in children]
            ordered.extend(item for item in children if item not in ordered)
        else:
            ordered = sorted(children, key=self._comparison_key)
        for index, item in enumerate(ordered):
            self.tree.move(item, "", index)
        self._refresh_headings()

    def _comparison_key(self, item: str):
        """Construit une clé composite respectant priorité et direction de chaque critère.

        Entrées:
            item (str): Identifiant d'une ligne du Treeview.

        Sortie:
            tuple: Clé comparable utilisée par ``sorted``.
        """
        result = []
        for column, direction in self.criteria:
            raw = self.tree.item(item, "text") if column == "#0" else self.tree.set(item, column)
            missing, value = self._normalize_value(raw)
            if isinstance(value, (int, float)):
                comparable = value if direction == 1 else -value
                result.append((missing, 0, comparable))
            else:
                result.append((missing, 1, _DescendingText(value) if direction == -1 else value))
        return tuple(result)

    def _normalize_value(self, value: object) -> tuple[int, float | str]:
        """Convertit une cellule affichée en nombre lorsque c'est possible.

        Entrées:
            value (object): Valeur issue du Treeview, potentiellement formatée avec ``$`` ou ``%``.

        Sortie:
            tuple[int, float | str]: Indicateur de valeur absente puis valeur comparable.
        """
        text = str(value).strip()
        if text in {"", "—", "-", "N/A", "n/a"}:
            return (1, "")
        cleaned = (
            text.replace("$", "")
            .replace("%", "")
            .replace(" ", "")
            .replace(" ", "")
            .replace(",", ".")
        )
        try:
            return (0, float(cleaned))
        except ValueError:
            return (0, text.casefold())

    def _refresh_headings(self) -> None:
        """Affiche priorité et sens de tri directement dans les titres des colonnes.

        Entrées:
            Aucune.

        Sortie:
            None: Les libellés deviennent par exemple ``Loyers ①↓``.
        """
        active = {column: (index, direction) for index, (column, direction) in enumerate(self.criteria)}
        for column, label in self.labels.items():
            suffix = ""
            if column in active:
                index, direction = active[column]
                rank = self._RANK_SYMBOLS[index] if index < len(self._RANK_SYMBOLS) else f"[{index + 1}]"
                suffix = f" {rank}{'↑' if direction == 1 else '↓'}"
            self.tree.heading(
                column,
                text=label + suffix,
                command=lambda current=column: self.cycle(current),
            )


class _DescendingText:
    """Inverse uniquement la comparaison lexicographique d'une valeur texte.

    Entrées:
        value (str): Texte normalisé à comparer en ordre décroissant.

    Sortie:
        _DescendingText: Petit adaptateur comparable utilisable dans une clé ``sorted``.
    """

    def __init__(self, value: str) -> None:
        """Conserve le texte normalisé.

        Entrées:
            value (str): Chaîne déjà préparée pour le tri.

        Sortie:
            None: La valeur est mémorisée.
        """
        self.value = value

    def __lt__(self, other: object) -> bool:
        """Inverse l'opérateur inférieur afin d'obtenir un ordre alphabétique décroissant.

        Entrées:
            other (object): Autre adaptateur texte à comparer.

        Sortie:
            bool: ``True`` lorsque le texte courant doit venir avant en ordre décroissant.
        """
        if not isinstance(other, _DescendingText):
            return NotImplemented
        return self.value > other.value

    def __eq__(self, other: object) -> bool:
        """Teste l'égalité des textes normalisés.

        Entrées:
            other (object): Autre adaptateur texte.

        Sortie:
            bool: ``True`` lorsque les deux valeurs sont identiques.
        """
        return isinstance(other, _DescendingText) and self.value == other.value
