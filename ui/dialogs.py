"""Fenêtres modales utilisées par l'interface graphique Monopoly."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property


if TYPE_CHECKING:
    from monopoly.game import Game


class NewGameDialog(tk.Toplevel):
    """Demande les noms de deux à six joueurs avant de créer une partie.

    Entrées:
        master (tk.Misc): Fenêtre parente.

    Sortie:
        NewGameDialog: Dialogue modal dont ``result`` contient les noms validés.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit le formulaire de création d'une nouvelle partie.

        Entrées:
            master (tk.Misc): Fenêtre parente à bloquer pendant le dialogue.

        Sortie:
            None: Les contrôles sont créés et le dialogue devient modal.
        """
        super().__init__(master)
        self.title("Nouvelle partie")
        self.resizable(False, False)
        self.result: list[str] | None = None
        self.entries: list[ttk.Entry] = []

        container = ttk.Frame(self, padding=18)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Nouvelle partie",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        ttk.Label(
            container,
            text="Entre 2 et 6 joueurs. Les champs vides sont ignorés.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        defaults = ["Alice", "Bob", "", "", "", ""]
        for index in range(6):
            ttk.Label(container, text=f"Joueur {index + 1}").grid(
                row=index + 2,
                column=0,
                sticky="e",
                padx=(0, 8),
                pady=3,
            )
            entry = ttk.Entry(container, width=28)
            entry.insert(0, defaults[index])
            entry.grid(row=index + 2, column=1, sticky="ew", pady=3)
            self.entries.append(entry)

        button_row = ttk.Frame(container)
        button_row.grid(row=8, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(button_row, text="Annuler", command=self._cancel).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(button_row, text="Commencer", command=self._confirm).pack(
            side="left"
        )

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.entries[0].focus_set()

    def _confirm(self) -> None:
        """Valide les noms saisis et ferme le dialogue si leur nombre est correct.

        Entrées:
            Aucune autre que les champs présents dans la fenêtre.

        Sortie:
            None: ``result`` est rempli puis la fenêtre est détruite si la saisie est valide.
        """
        names = [entry.get().strip() for entry in self.entries]
        names = [name for name in names if name]

        if len(names) < 2:
            messagebox.showwarning(
                "Joueurs insuffisants",
                "Il faut au moins deux joueurs.",
                parent=self,
            )
            return

        if len(set(names)) != len(names):
            messagebox.showwarning(
                "Noms identiques",
                "Chaque joueur doit avoir un nom différent.",
                parent=self,
            )
            return

        self.result = names
        self.destroy()

    def _cancel(self) -> None:
        """Annule la création de partie et ferme le dialogue.

        Entrées:
            Aucune.

        Sortie:
            None: ``result`` reste à ``None`` et la fenêtre est détruite.
        """
        self.result = None
        self.destroy()



class PropertyManagerDialog(tk.Toplevel):
    """Permet à un joueur de construire, vendre et gérer ses hypothèques.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        game (Game): Partie contenant les règles immobilières.
        player (Player): Joueur dont les biens doivent être gérés.

    Sortie:
        PropertyManagerDialog: Fenêtre modale de gestion des propriétés.
    """

    def __init__(self, master: tk.Misc, game: Game, player: Player) -> None:
        """Construit la liste de biens et les boutons d'actions immobilières.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            game (Game): Partie à modifier.
            player (Player): Propriétaire dont les biens sont affichés.

        Sortie:
            None: La fenêtre est initialisée et son contenu est affiché.
        """
        super().__init__(master)
        self.title(f"Propriétés — {player.name}")
        self.geometry("720x430")
        self.minsize(650, 380)
        self.game = game
        self.player = player
        self.changed = False

        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text=f"Gestion des propriétés de {player.name}",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w")

        self.cash_label = ttk.Label(container, text="")
        self.cash_label.pack(anchor="w", pady=(2, 10))

        columns = ("name", "type", "state", "value")
        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=11,
        )
        self.tree.heading("name", text="Bien")
        self.tree.heading("type", text="Type")
        self.tree.heading("state", text="État")
        self.tree.heading("value", text="Hypothèque")
        self.tree.column("name", width=220)
        self.tree.column("type", width=110, anchor="center")
        self.tree.column("state", width=170, anchor="center")
        self.tree.column("value", width=110, anchor="center")
        self.tree.pack(fill="both", expand=True)

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(buttons, text="Construire", command=self._build).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(buttons, text="Vendre bâtiment", command=self._sell).pack(
            side="left", padx=5
        )
        ttk.Button(buttons, text="Hypothéquer", command=self._mortgage).pack(
            side="left", padx=5
        )
        ttk.Button(buttons, text="Déshypothéquer", command=self._unmortgage).pack(
            side="left", padx=5
        )
        ttk.Button(buttons, text="Fermer", command=self.destroy).pack(side="right")

        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)
        self.transient(master)
        self.grab_set()
        self._refresh()

    def _selected_space(self) -> OwnableSpace | None:
        """Retourne le bien actuellement sélectionné dans le tableau.

        Entrées:
            Aucune autre que la sélection du ``Treeview``.

        Sortie:
            OwnableSpace | None: Bien choisi, ou ``None`` sans sélection valide.
        """
        selection = self.tree.selection()
        if not selection:
            return None

        try:
            index = int(selection[0])
        except ValueError:
            return None

        for space in self.player.properties:
            if space.index == index:
                return space

        return None

    def _selection_changed(self, event: tk.Event) -> None:
        """Réagit à une nouvelle sélection sans modifier directement le moteur.

        Entrées:
            event (tk.Event): Événement de sélection du tableau.

        Sortie:
            None: La méthode existe comme point d'extension pour l'interface.
        """
        return None

    def _build(self) -> None:
        """Construit une maison ou un hôtel sur le terrain sélectionné.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: Le moteur est modifié si la construction est autorisée.
        """
        space = self._selected_space()
        if not isinstance(space, Property):
            messagebox.showinfo(
                "Construction",
                "Sélectionnez un terrain de couleur.",
                parent=self,
            )
            return

        success = False
        if space.houses < 4 and not space.hotel:
            success = self.game.rules.build_house(self.player, space)
        elif space.houses == 4 and not space.hotel:
            success = self.game.rules.build_hotel(self.player, space)

        if not success:
            messagebox.showwarning(
                "Construction impossible",
                (
                    "Vérifiez le monopole, l'équilibre des constructions, "
                    "les hypothèques et votre argent."
                ),
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _sell(self) -> None:
        """Vend un niveau de développement du terrain sélectionné à la banque.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: Le bâtiment est vendu si les règles l'autorisent.
        """
        space = self._selected_space()
        if not isinstance(space, Property) or not self.game.rules.sell_building(
            self.player, space
        ):
            messagebox.showwarning(
                "Vente impossible",
                "Aucun bâtiment vendable ici ou développement non équilibré.",
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _mortgage(self) -> None:
        """Hypothèque le bien sélectionné si les règles l'autorisent.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: Le bien devient hypothéqué et le joueur reçoit sa valeur.
        """
        space = self._selected_space()
        if space is None or not self.game.rules.mortgage_property(self.player, space):
            messagebox.showwarning(
                "Hypothèque impossible",
                "Ce bien ne peut pas être hypothéqué dans son état actuel.",
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _unmortgage(self) -> None:
        """Lève l'hypothèque du bien sélectionné en payant le coût correspondant.

        Entrées:
            Aucune autre que la sélection courante.

        Sortie:
            None: L'hypothèque est levée si le joueur possède assez d'argent.
        """
        space = self._selected_space()
        if space is None or not self.game.rules.unmortgage_property(self.player, space):
            messagebox.showwarning(
                "Déshypothèque impossible",
                "Le bien n'est pas hypothéqué ou votre argent est insuffisant.",
                parent=self,
            )
            return

        self.changed = True
        self._refresh(select_index=space.index)

    def _refresh(self, select_index: int | None = None) -> None:
        """Reconstruit le tableau des biens après une modification.

        Entrées:
            select_index (int | None): Index de case à sélectionner après rafraîchissement.

        Sortie:
            None: Le tableau et le solde affiché sont synchronisés avec le moteur.
        """
        self.cash_label.config(text=f"Argent disponible : {self.player.cash} $")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for space in sorted(self.player.properties, key=lambda item: item.index):
            if isinstance(space, Property):
                type_name = "Terrain"
                if space.hotel:
                    state = "Hôtel"
                elif space.houses:
                    state = f"{space.houses} maison(s)"
                else:
                    state = "Nu"
            else:
                type_name = type(space).__name__
                state = "Actif"

            if space.mortgaged:
                state = "Hypothéqué"

            self.tree.insert(
                "",
                "end",
                iid=str(space.index),
                values=(
                    space.name,
                    type_name,
                    state,
                    f"{space.mortgage_value} $",
                ),
            )

        if select_index is not None and self.tree.exists(str(select_index)):
            self.tree.selection_set(str(select_index))
            self.tree.focus(str(select_index))
