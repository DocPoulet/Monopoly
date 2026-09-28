"""Assistant modal pour créer rapidement un nouveau plateau éditable."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from monopoly.board_config import BoardConfig


class BoardCreationWizard(tk.Toplevel):
    """Crée un plateau standard copié ou une structure économique vierge.

    Entrées:
        master (tk.Misc): Fenêtre parente.

    Sortie:
        BoardCreationWizard: Dialogue modal dont ``result`` contient le plateau créé.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Construit le choix de nom et de modèle de départ.

        Entrées:
            master (tk.Misc): Fenêtre parente.

        Sortie:
            None: L'assistant est affiché et prêt à valider.
        """
        super().__init__(master)
        self.title("Assistant nouveau plateau")
        self.geometry("560x360")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result: BoardConfig | None = None

        shell = ttk.Frame(self, padding=18)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)

        ttk.Label(
            shell,
            text="Créer un nouveau plateau",
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            shell,
            text=(
                "Les quatre positions structurelles restent fixes. Le modèle vierge "
                "conserve une structure jouable mais remplace les noms, valeurs et cartes "
                "par une base neutre à personnaliser."
            ),
            style="Muted.TLabel",
            wraplength=500,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(shell, text="Nom du plateau").grid(row=2, column=0, sticky="w")
        self.name_var = tk.StringVar(value="Mon nouveau plateau")
        ttk.Entry(shell, textvariable=self.name_var).grid(
            row=3, column=0, sticky="ew", pady=(3, 12)
        )

        self.template_var = tk.StringVar(value="blank")
        templates = ttk.LabelFrame(shell, text="Point de départ", padding=10)
        templates.grid(row=4, column=0, sticky="ew")
        ttk.Radiobutton(
            templates,
            text="Structure Monopoly vierge",
            variable=self.template_var,
            value="blank",
        ).pack(anchor="w")
        ttk.Label(
            templates,
            text="Noms génériques, économie neutre, une carte simple par paquet.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=(24, 0), pady=(0, 8))
        ttk.Radiobutton(
            templates,
            text="Copie du plateau standard",
            variable=self.template_var,
            value="standard",
        ).pack(anchor="w")
        ttk.Label(
            templates,
            text="Toutes les valeurs classiques sont copiées puis restent modifiables.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=(24, 0))

        buttons = ttk.Frame(shell)
        buttons.grid(row=5, column=0, sticky="ew", pady=(18, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=2)
        ttk.Button(buttons, text="Annuler", command=self.destroy).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(
            buttons,
            text="Créer et ouvrir",
            style="Primary.TButton",
            command=self._create,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _create(self) -> None:
        """Construit le plateau choisi et ferme l'assistant.

        Entrées:
            Aucune.

        Sortie:
            None: ``result`` reçoit une définition valide avant fermeture.
        """
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(
                "Nom requis",
                "Donnez un nom au nouveau plateau.",
                parent=self,
            )
            return
        if self.template_var.get() == "standard":
            board = BoardConfig.standard()
            board.name = name
        else:
            board = BoardConfig.blank_template(name)
        self.result = board
        self.destroy()
