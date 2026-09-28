"""Bibliothèques visuelles de presets de règles et de plateaux."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Generic, TypeVar

from monopoly.board_presets import (
    BoardPreset,
    delete_board_preset,
    list_board_presets,
    rename_board_preset,
)
from monopoly.rule_presets import (
    RulePreset,
    delete_rule_preset,
    list_rule_presets,
    rename_rule_preset,
)

PresetT = TypeVar("PresetT", RulePreset, BoardPreset)


class _PresetLibraryDialog(tk.Toplevel, Generic[PresetT]):
    """Base interne d'une bibliothèque avec aperçu, chargement, renommage et suppression.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        title (str): Titre du dialogue.
        directory (Path): Dossier local de presets.
        loader (Callable[[], list[PresetT]]): Fonction de rafraîchissement.
        previewer (Callable[[PresetT], str]): Génère le texte d'aperçu.
        rename_callback (Callable[[PresetT, str], PresetT]): Renomme le preset sélectionné.
        delete_callback (Callable[[PresetT], None]): Supprime le preset sélectionné.

    Sortie:
        _PresetLibraryDialog: Dialogue modal avec ``selected`` après chargement.
    """

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        directory: Path,
        loader: Callable[[], list[PresetT]],
        previewer: Callable[[PresetT], str],
        rename_callback: Callable[[PresetT, str], PresetT],
        delete_callback: Callable[[PresetT], None],
    ) -> None:
        """Construit la liste, l'aperçu et les actions de gestion.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            title (str): Titre visible.
            directory (Path): Dossier géré.
            loader (Callable): Recharge les presets locaux.
            previewer (Callable): Construit l'aperçu sélectionné.
            rename_callback (Callable): Applique un renommage.
            delete_callback (Callable): Applique une suppression.

        Sortie:
            None: Le dialogue est prêt à être utilisé.
        """
        super().__init__(master)
        self.title(title)
        self.geometry("850x520")
        self.minsize(760, 460)
        self.transient(master)
        self.grab_set()
        self.directory = directory
        self.loader = loader
        self.previewer = previewer
        self.rename_callback = rename_callback
        self.delete_callback = delete_callback
        self.presets: list[PresetT] = []
        self.selected: PresetT | None = None

        shell = ttk.Frame(self, padding=14)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=2)
        shell.columnconfigure(1, weight=3)
        shell.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(shell, text="Presets locaux", padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            left,
            columns=("date",),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Nom")
        self.tree.heading("date", text="Sauvegardé")
        self.tree.column("#0", width=190)
        self.tree.column("date", width=145)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

        right = ttk.LabelFrame(shell, text="Aperçu", padding=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        self.preview = tk.Text(
            right,
            wrap="word",
            state="disabled",
            relief="flat",
            background="#FFFFFF",
            padx=8,
            pady=8,
        )
        self.preview.grid(row=0, column=0, sticky="nsew")

        buttons = ttk.Frame(shell)
        buttons.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        for column in range(4):
            buttons.columnconfigure(column, weight=1)
        ttk.Button(buttons, text="Charger", command=self._load_selected).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(buttons, text="Renommer", command=self._rename_selected).grid(
            row=0, column=1, sticky="ew", padx=4
        )
        ttk.Button(buttons, text="Supprimer", command=self._delete_selected).grid(
            row=0, column=2, sticky="ew", padx=4
        )
        ttk.Button(buttons, text="Fermer", command=self.destroy).grid(
            row=0, column=3, sticky="ew", padx=(4, 0)
        )
        self._refresh()

    def _refresh(self, select_name: str | None = None) -> None:
        """Recharge la bibliothèque locale et restaure si possible une sélection.

        Entrées:
            select_name (str | None): Nom à sélectionner après rafraîchissement.

        Sortie:
            None: La liste et l'aperçu sont actualisés.
        """
        self.presets = self.loader()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, preset in enumerate(self.presets):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                text=preset.name,
                values=(preset.saved_at.replace("T", " ")[:16],),
            )
        if not self.presets:
            self._set_preview("Aucun preset local.")
            return
        target = 0
        if select_name:
            for index, preset in enumerate(self.presets):
                if preset.name == select_name:
                    target = index
                    break
        self.tree.selection_set(str(target))
        self.tree.focus(str(target))
        self._selection_changed(None)

    def _current(self) -> PresetT | None:
        """Retourne le preset correspondant à la sélection actuelle.

        Entrées:
            Aucune.

        Sortie:
            PresetT | None: Preset sélectionné ou ``None``.
        """
        selection = self.tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        if 0 <= index < len(self.presets):
            return self.presets[index]
        return None

    def _selection_changed(self, event: tk.Event | None) -> None:
        """Actualise l'aperçu lorsque la sélection change.

        Entrées:
            event (tk.Event | None): Événement Treeview facultatif.

        Sortie:
            None: Le texte d'aperçu décrit le preset courant.
        """
        preset = self._current()
        self._set_preview(self.previewer(preset) if preset is not None else "")

    def _set_preview(self, text: str) -> None:
        """Remplace le texte de l'aperçu en conservant le widget en lecture seule.

        Entrées:
            text (str): Contenu à afficher.

        Sortie:
            None: Le widget contient le nouveau texte.
        """
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _load_selected(self) -> None:
        """Valide le preset courant comme résultat du dialogue.

        Entrées:
            Aucune.

        Sortie:
            None: ``selected`` est renseigné puis le dialogue se ferme.
        """
        preset = self._current()
        if preset is None:
            return
        self.selected = preset
        self.destroy()

    def _rename_selected(self) -> None:
        """Demande un nouveau nom puis renomme le fichier et son contenu.

        Entrées:
            Aucune.

        Sortie:
            None: La bibliothèque est rechargée avec le nouveau nom.
        """
        preset = self._current()
        if preset is None:
            return
        name = simpledialog.askstring(
            "Renommer le preset",
            "Nouveau nom :",
            initialvalue=preset.name,
            parent=self,
        )
        if not name or not name.strip() or name.strip() == preset.name:
            return
        try:
            renamed = self.rename_callback(preset, name.strip())
        except (OSError, ValueError) as error:
            messagebox.showerror("Renommage impossible", str(error), parent=self)
            return
        self._refresh(renamed.name)

    def _delete_selected(self) -> None:
        """Supprime le preset sélectionné après confirmation.

        Entrées:
            Aucune.

        Sortie:
            None: Le fichier disparaît puis la bibliothèque est rechargée.
        """
        preset = self._current()
        if preset is None:
            return
        if not messagebox.askyesno(
            "Supprimer le preset",
            f"Supprimer définitivement « {preset.name} » ?",
            parent=self,
        ):
            return
        try:
            self.delete_callback(preset)
        except OSError as error:
            messagebox.showerror("Suppression impossible", str(error), parent=self)
            return
        self._refresh()


class RulePresetLibraryDialog(_PresetLibraryDialog[RulePreset]):
    """Bibliothèque de presets de règles avec aperçu détaillé.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        directory (str | Path): Dossier local des presets de règles.

    Sortie:
        RulePresetLibraryDialog: Dialogue dont ``selected`` contient le profil choisi.
    """

    def __init__(self, master: tk.Misc, directory: str | Path) -> None:
        """Configure la bibliothèque pour les objets ``RulePreset``.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            directory (str | Path): Dossier des presets.

        Sortie:
            None: Le dialogue spécialisé est construit.
        """
        folder = Path(directory)
        super().__init__(
            master,
            "Bibliothèque de presets de règles",
            folder,
            loader=lambda: list_rule_presets(folder),
            previewer=self._preview_rule,
            rename_callback=lambda preset, name: rename_rule_preset(preset, name),
            delete_callback=delete_rule_preset,
        )

    @staticmethod
    def _preview_rule(preset: RulePreset) -> str:
        """Construit l'aperçu lisible d'un preset de règles.

        Entrées:
            preset (RulePreset): Profil à décrire.

        Sortie:
            str: Résumé et principales valeurs configurées.
        """
        options = preset.options
        return (
            f"{preset.name}\n\n{options.summary()}\n\n"
            f"Argent de départ : {options.starting_cash} $\n"
            f"Départ : {options.go_salary} $\n"
            f"Prix propriétés : {options.property_price_percent} %\n"
            f"Loyers : {options.rent_percent} %\n"
            f"Revente bâtiments : {options.building_resale_percent} %\n"
            f"Stock maisons / hôtels : {options.house_stock} / {options.hotel_stock}\n"
            f"Loyer automatique : {'oui' if options.automatic_rent else 'non'}\n"
            f"Construction partout : {'oui' if options.construction_anywhere else 'non'}\n"
            f"Limite de tours : {options.turn_limit or 'aucune'}"
        )


class BoardPresetLibraryDialog(_PresetLibraryDialog[BoardPreset]):
    """Bibliothèque de presets de plateau avec aperçu structurel.

    Entrées:
        master (tk.Misc): Fenêtre parente.
        directory (str | Path): Dossier local des presets de plateau.

    Sortie:
        BoardPresetLibraryDialog: Dialogue dont ``selected`` contient le plateau choisi.
    """

    def __init__(self, master: tk.Misc, directory: str | Path) -> None:
        """Configure la bibliothèque pour les objets ``BoardPreset``.

        Entrées:
            master (tk.Misc): Fenêtre parente.
            directory (str | Path): Dossier des presets.

        Sortie:
            None: Le dialogue spécialisé est construit.
        """
        folder = Path(directory)
        super().__init__(
            master,
            "Bibliothèque de presets de plateau",
            folder,
            loader=lambda: list_board_presets(folder),
            previewer=self._preview_board,
            rename_callback=lambda preset, name: rename_board_preset(preset, name),
            delete_callback=delete_board_preset,
        )

    @staticmethod
    def _preview_board(preset: BoardPreset) -> str:
        """Construit l'aperçu lisible d'un preset de plateau.

        Entrées:
            preset (BoardPreset): Plateau à décrire.

        Sortie:
            str: Résumé, comptage de types et état de validation.
        """
        board = preset.board_config
        counts: dict[str, int] = {}
        for space in board.spaces:
            counts[space.space_type] = counts.get(space.space_type, 0) + 1
        issues = board.validation_issues()
        errors = sum(issue.severity == "error" for issue in issues)
        warnings = sum(issue.severity == "warning" for issue in issues)
        structure = "\n".join(
            f"- {kind}: {count}" for kind, count in sorted(counts.items())
        )
        return (
            f"{preset.name}\n\n{board.summary()}\n\n"
            f"Chance : {len(board.chance_cards)} carte(s)\n"
            f"Communauté : {len(board.community_chest_cards)} carte(s)\n\n"
            f"Structure :\n{structure}\n\n"
            f"Validation : {errors} erreur(s), {warnings} avertissement(s)"
        )
