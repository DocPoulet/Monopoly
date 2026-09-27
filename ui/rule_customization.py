"""Écran intégré de personnalisation avancée des règles avant une partie."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable

from monopoly.options import GameOptions
from monopoly.rule_presets import (
    RulePreset,
    RulePresetError,
    import_rule_preset,
    list_rule_presets,
    load_rule_preset,
    save_named_rule_preset,
    save_rule_preset,
    safe_preset_filename,
)


class RuleCustomizationView(ttk.Frame):
    """Permet de modifier les règles classiques et les variantes avancées.

    Entrées:
        master (tk.Misc): Conteneur parent.
        options (GameOptions): Profil actuellement sélectionné.
        save_callback (Callable[[GameOptions], None]): Enregistre les règles.
        cancel_callback (Callable[[], None]): Retourne sans appliquer les changements.
        preset_directory (str | Path | None): Dossier local où conserver les presets.

    Sortie:
        RuleCustomizationView: Éditeur de règles défilable intégré à la fenêtre principale.
    """

    def __init__(
        self,
        master: tk.Misc,
        options: GameOptions,
        save_callback: Callable[[GameOptions], None],
        cancel_callback: Callable[[], None],
        preset_directory: str | Path | None = None,
    ) -> None:
        """Construit les sections générales, économie, bâtiments et variantes.

        Entrées:
            master (tk.Misc): Conteneur parent.
            options (GameOptions): Valeurs initiales.
            save_callback (Callable[[GameOptions], None]): Callback de validation.
            cancel_callback (Callable[[], None]): Callback d'annulation.
            preset_directory (str | Path | None): Dossier local des presets.

        Sortie:
            None: L'éditeur est prêt à être affiché.
        """
        super().__init__(master, style="Home.TFrame")
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback
        self.preset_directory = Path(preset_directory or Path.cwd() / "rule_presets")
        self.preset_directory.mkdir(parents=True, exist_ok=True)
        self.local_presets: dict[str, RulePreset] = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        canvas = tk.Canvas(self, highlightthickness=0, background="#F3F6F8")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        card = ttk.Frame(canvas, style="SetupCard.TFrame", padding=24)
        window_id = canvas.create_window((0, 0), window=card, anchor="nw")
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        def resize_scroll(event: tk.Event) -> None:
            """Synchronise largeur et zone de défilement avec le contenu.

            Entrées:
                event (tk.Event): Événement de redimensionnement Tkinter.

            Sortie:
                None: Le Canvas adopte la largeur disponible et recalcule le scroll.
            """
            canvas.itemconfigure(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize_scroll)
        card.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        ttk.Label(card, text="Personnaliser les règles", style="SetupTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            card,
            text=(
                "Tous les pourcentages utilisent 100 % comme valeur classique. "
                "Pour les stocks de bâtiments, 0 signifie illimité."
            ),
            style="SetupSubtitle.TLabel",
            wraplength=850,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 14))

        self.starting_cash_var = tk.StringVar(value=str(options.starting_cash))
        self.go_salary_var = tk.StringVar(value=str(options.go_salary))
        self.jail_fine_var = tk.StringVar(value=str(options.jail_fine))
        self.max_jail_turns_var = tk.StringVar(value=str(options.max_jail_turns))
        self.doubles_to_jail_var = tk.StringVar(value=str(options.doubles_to_jail))
        self.auctions_var = tk.BooleanVar(value=options.auctions_enabled)
        self.free_parking_var = tk.StringVar(value=str(options.free_parking_bonus))
        self.free_parking_pot_var = tk.BooleanVar(value=options.free_parking_card_pot)
        self.turn_limit_var = tk.StringVar(value=str(options.turn_limit))
        self.property_price_percent_var = tk.StringVar(value=str(options.property_price_percent))
        self.rent_percent_var = tk.StringVar(value=str(options.rent_percent))
        self.monopoly_required_var = tk.BooleanVar(value=options.monopoly_required_for_building)
        self.house_stock_var = tk.StringVar(value=str(options.house_stock))
        self.hotel_stock_var = tk.StringVar(value=str(options.hotel_stock))
        self.mortgages_var = tk.BooleanVar(value=options.mortgages_enabled)
        self.unmortgage_tax_var = tk.StringVar(value=str(options.unmortgage_tax_percent))
        self.transferred_mortgages_var = tk.BooleanVar(value=options.transferred_mortgages)
        self.resale_percent_var = tk.StringVar(value=str(options.building_resale_percent))
        self.automatic_rent_var = tk.BooleanVar(value=options.automatic_rent)
        self.construction_anywhere_var = tk.BooleanVar(value=options.construction_anywhere)
        self.property_debt_payment_var = tk.BooleanVar(value=options.property_debt_payment)
        self.max_buildings_per_action_var = tk.StringVar(
            value=str(options.max_buildings_per_action)
        )

        presets = self._section(card, 2, "Presets de règles")
        presets.columnconfigure(0, weight=2)
        presets.columnconfigure(1, weight=1)
        presets.columnconfigure(2, weight=1)
        presets.columnconfigure(3, weight=1)

        self.preset_var = tk.StringVar(value="")
        self.preset_combo = ttk.Combobox(
            presets,
            textvariable=self.preset_var,
            state="readonly",
        )
        self.preset_combo.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            presets,
            text="Charger",
            command=self._load_selected_preset,
        ).grid(row=0, column=1, sticky="ew", padx=3)
        ttk.Button(
            presets,
            text="Sauvegarder preset",
            command=self._save_local_preset,
        ).grid(row=0, column=2, sticky="ew", padx=3)
        ttk.Button(
            presets,
            text="Importer JSON",
            command=self._import_preset,
        ).grid(row=0, column=3, sticky="ew", padx=(3, 0))
        ttk.Button(
            presets,
            text="Exporter le profil courant",
            command=self._export_current_preset,
        ).grid(row=1, column=2, columnspan=2, sticky="ew", padx=(3, 0), pady=(6, 0))
        ttk.Label(
            presets,
            text=(
                "Les presets locaux restent disponibles entre les parties. "
                "Importer ajoute un preset externe à la bibliothèque locale."
            ),
            style="Muted.TLabel",
            wraplength=620,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        general = self._section(card, 3, "Règles générales")
        self._numeric(general, 0, 0, "Argent de départ", self.starting_cash_var, "1500 $")
        self._numeric(general, 0, 1, "Salaire Départ", self.go_salary_var, "200 $")
        self._numeric(general, 1, 0, "Amende de prison", self.jail_fine_var, "50 $")
        self._numeric(general, 1, 1, "Tentatives max en prison", self.max_jail_turns_var, "3")
        self._numeric(general, 2, 0, "Doubles → prison", self.doubles_to_jail_var, "3")
        self._numeric(general, 2, 1, "Limite de tours", self.turn_limit_var, "0 = aucune")

        economy = self._section(card, 4, "Économie et loyers")
        self._numeric(economy, 0, 0, "Prix des propriétés (%)", self.property_price_percent_var, "100 %")
        self._numeric(economy, 0, 1, "Prix des loyers (%)", self.rent_percent_var, "100 %")
        self._numeric(economy, 1, 0, "Prix revente bâtiments (%)", self.resale_percent_var, "50 %")
        self._numeric(economy, 1, 1, "Taxe déshypothèque (%)", self.unmortgage_tax_var, "10 %")
        self._check(economy, 2, 0, "Loyer automatique", self.automatic_rent_var, "Sinon le propriétaire doit le réclamer.")
        self._check(economy, 2, 1, "Hypothèques autorisées", self.mortgages_var, "Désactivé : aucune nouvelle hypothèque.")
        self._check(economy, 3, 0, "Hypothèques transférées", self.transferred_mortgages_var, "Désactivé : transfert = hypothèque annulée, sans frais.")
        self._check(economy, 3, 1, "Enchères immobilières", self.auctions_var, "Bien refusé mis aux enchères.")
        self._check(
            economy,
            4,
            0,
            "Paiement de dette en propriétés",
            self.property_debt_payment_var,
            "Dette envers un joueur : céder un bien non hypothéqué à 100 % de sa valeur + bâtiments restants.",
        )

        buildings = self._section(card, 5, "Construction et stock")
        self._check(buildings, 0, 0, "Monopole nécessaire pour construire", self.monopoly_required_var, "Désactivé : équilibre seulement entre vos terrains du groupe.")
        self._check(buildings, 0, 1, "Construction partout", self.construction_anywhere_var, "Désactivé : construire uniquement juste après être tombé sur la propriété.")
        self._numeric(buildings, 1, 0, "Stock maisons", self.house_stock_var, "32 classique • 0 = illimité")
        self._numeric(buildings, 1, 1, "Stock hôtels", self.hotel_stock_var, "12 classique • 0 = illimité")
        self._numeric(
            buildings,
            2,
            0,
            "Max constructions à la fois",
            self.max_buildings_per_action_var,
            "1 à 4 maisons par décision • un hôtel reste toujours une seule construction",
        )

        parking = self._section(card, 6, "Parc Gratuit")
        self._numeric(parking, 0, 0, "Bonus fixe Parc Gratuit", self.free_parking_var, "0 $ classique")
        self._check(
            parking,
            0,
            1,
            "Cagnotte Chance / Communauté",
            self.free_parking_pot_var,
            "Tous les paiements à la banque causés par une carte alimentent la cagnotte ; jamais les paiements à un autre joueur.",
        )

        self.preview_label = ttk.Label(card, text="", style="Muted.TLabel", wraplength=850)
        self.preview_label.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        buttons = ttk.Frame(card, style="SetupCard.TFrame")
        buttons.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        for column in range(3):
            buttons.columnconfigure(column, weight=1)
        ttk.Button(buttons, text="Règles classiques", command=self._reset_classic).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(buttons, text="Annuler", command=self.cancel_callback).grid(
            row=0, column=1, sticky="ew", padx=5
        )
        ttk.Button(
            buttons,
            text="Enregistrer les règles",
            style="HomePrimary.TButton",
            command=self._save,
        ).grid(row=0, column=2, sticky="ew", padx=(5, 0))

        variables = (
            self.starting_cash_var,
            self.go_salary_var,
            self.jail_fine_var,
            self.max_jail_turns_var,
            self.doubles_to_jail_var,
            self.free_parking_var,
            self.turn_limit_var,
            self.property_price_percent_var,
            self.rent_percent_var,
            self.house_stock_var,
            self.hotel_stock_var,
            self.unmortgage_tax_var,
            self.resale_percent_var,
            self.auctions_var,
            self.free_parking_pot_var,
            self.monopoly_required_var,
            self.mortgages_var,
            self.transferred_mortgages_var,
            self.automatic_rent_var,
            self.construction_anywhere_var,
            self.property_debt_payment_var,
            self.max_buildings_per_action_var,
        )
        for variable in variables:
            variable.trace_add("write", self._refresh_preview)
        self._refresh_preset_list()
        self._refresh_preview()

    def _section(self, parent: ttk.Frame, row: int, title: str) -> ttk.LabelFrame:
        """Crée une section pleine largeur à deux colonnes.

        Entrées:
            parent (ttk.Frame): Conteneur principal.
            row (int): Ligne de la section.
            title (str): Titre visible.

        Sortie:
            ttk.LabelFrame: Section configurée pour recevoir des contrôles.
        """
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        return frame

    def _numeric(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label: str,
        variable: tk.StringVar,
        hint: str,
    ) -> None:
        """Ajoute un champ numérique avec son aide.

        Entrées:
            parent (ttk.Frame): Section parente.
            row (int): Ligne.
            column (int): Colonne.
            label (str): Intitulé.
            variable (tk.StringVar): Valeur liée.
            hint (str): Aide courte.

        Sortie:
            None: Les widgets sont placés dans la section.
        """
        cell = ttk.Frame(parent)
        cell.grid(row=row, column=column, sticky="ew", padx=6, pady=4)
        ttk.Label(cell, text=label, font=("Arial", 9, "bold")).pack(anchor="w")
        ttk.Entry(cell, textvariable=variable, width=16).pack(anchor="w", pady=(2, 0))
        ttk.Label(cell, text=hint, style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

    def _check(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label: str,
        variable: tk.BooleanVar,
        hint: str,
    ) -> None:
        """Ajoute une variante booléenne et son explication.

        Entrées:
            parent (ttk.Frame): Section parente.
            row (int): Ligne.
            column (int): Colonne.
            label (str): Intitulé de la case.
            variable (tk.BooleanVar): Valeur liée.
            hint (str): Explication courte.

        Sortie:
            None: Le contrôle est placé dans la section.
        """
        cell = ttk.Frame(parent)
        cell.grid(row=row, column=column, sticky="nsew", padx=6, pady=4)
        ttk.Checkbutton(cell, text=label, variable=variable).pack(anchor="w")
        ttk.Label(cell, text=hint, style="Muted.TLabel", wraplength=380).pack(anchor="w", pady=(2, 0))


    def _refresh_preset_list(self) -> None:
        """Recharge la bibliothèque locale et actualise la combobox des presets.

        Entrées:
            Aucune.

        Sortie:
            None: Les presets valides du dossier local deviennent sélectionnables.
        """
        presets = list_rule_presets(self.preset_directory)
        self.local_presets = {preset.name: preset for preset in presets}
        names = list(self.local_presets)
        self.preset_combo.configure(values=names)
        if self.preset_var.get() not in self.local_presets:
            self.preset_var.set(names[0] if names else "")


    def _apply_options_to_fields(self, options: GameOptions) -> None:
        """Copie un profil ``GameOptions`` dans tous les champs de l'éditeur.

        Entrées:
            options (GameOptions): Profil à afficher et éventuellement modifier.

        Sortie:
            None: Chaque variable Tkinter reflète les valeurs du profil.
        """
        self.starting_cash_var.set(str(options.starting_cash))
        self.go_salary_var.set(str(options.go_salary))
        self.jail_fine_var.set(str(options.jail_fine))
        self.max_jail_turns_var.set(str(options.max_jail_turns))
        self.doubles_to_jail_var.set(str(options.doubles_to_jail))
        self.auctions_var.set(options.auctions_enabled)
        self.free_parking_var.set(str(options.free_parking_bonus))
        self.free_parking_pot_var.set(options.free_parking_card_pot)
        self.turn_limit_var.set(str(options.turn_limit))
        self.property_price_percent_var.set(str(options.property_price_percent))
        self.rent_percent_var.set(str(options.rent_percent))
        self.monopoly_required_var.set(options.monopoly_required_for_building)
        self.house_stock_var.set(str(options.house_stock))
        self.hotel_stock_var.set(str(options.hotel_stock))
        self.mortgages_var.set(options.mortgages_enabled)
        self.unmortgage_tax_var.set(str(options.unmortgage_tax_percent))
        self.transferred_mortgages_var.set(options.transferred_mortgages)
        self.resale_percent_var.set(str(options.building_resale_percent))
        self.automatic_rent_var.set(options.automatic_rent)
        self.construction_anywhere_var.set(options.construction_anywhere)
        self.property_debt_payment_var.set(options.property_debt_payment)
        self.max_buildings_per_action_var.set(str(options.max_buildings_per_action))


    def _load_selected_preset(self) -> None:
        """Charge le preset local sélectionné dans les champs sans lancer la partie.

        Entrées:
            Aucune.

        Sortie:
            None: Les valeurs du preset deviennent le profil actuellement édité.
        """
        preset = self.local_presets.get(self.preset_var.get())
        if preset is None:
            messagebox.showwarning("Preset", "Sélectionnez d'abord un preset local.", parent=self)
            return
        self._apply_options_to_fields(preset.options)


    def _save_local_preset(self) -> None:
        """Sauvegarde le profil courant dans la bibliothèque locale de presets.

        Entrées:
            Aucune.

        Sortie:
            None: Un fichier JSON nommé est créé ou remplacé après confirmation.
        """
        options, error = self._build_options()
        if options is None:
            messagebox.showwarning("Preset impossible", error, parent=self)
            return

        name = simpledialog.askstring(
            "Sauvegarder un preset",
            "Nom du preset :",
            parent=self,
        )
        if not name or not name.strip():
            return

        destination = self.preset_directory / (
            __import__("monopoly.rule_presets", fromlist=["safe_preset_filename"])
            .safe_preset_filename(name)
        )
        if destination.exists() and not messagebox.askyesno(
            "Remplacer le preset",
            f"Le preset « {name.strip()} » existe déjà. Le remplacer ?",
            parent=self,
        ):
            return

        save_named_rule_preset(options, self.preset_directory, name.strip())
        self._refresh_preset_list()
        self.preset_var.set(name.strip())


    def _import_preset(self) -> None:
        """Importe un preset JSON externe puis l'applique immédiatement.

        Entrées:
            Aucune.

        Sortie:
            None: Le preset externe est copié dans la bibliothèque locale et chargé.
        """
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer un preset de règles",
            filetypes=[("Preset Monopoly", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        try:
            preset = import_rule_preset(path, self.preset_directory)
        except RulePresetError as error:
            messagebox.showerror("Import impossible", str(error), parent=self)
            return

        self._refresh_preset_list()
        self.preset_var.set(preset.name)
        self._apply_options_to_fields(preset.options)


    def _export_current_preset(self) -> None:
        """Exporte le profil courant vers un fichier JSON portable.

        Entrées:
            Aucune.

        Sortie:
            None: Un fichier choisi par l'utilisateur reçoit le preset courant.
        """
        options, error = self._build_options()
        if options is None:
            messagebox.showwarning("Export impossible", error, parent=self)
            return

        name = simpledialog.askstring(
            "Exporter le preset",
            "Nom du preset exporté :",
            initialvalue="Mon preset",
            parent=self,
        )
        if not name or not name.strip():
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter un preset de règles",
            defaultextension=".json",
            initialfile=f"{name.strip()}.json",
            filetypes=[("Preset Monopoly", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        save_rule_preset(options, path, name.strip())

    def _build_options(self) -> tuple[GameOptions | None, str]:
        """Transforme les champs visibles en profil validé.

        Entrées:
            Aucune.

        Sortie:
            tuple[GameOptions | None, str]: Profil valide ou message d'erreur.
        """
        try:
            options = GameOptions(
                starting_cash=int(self.starting_cash_var.get()),
                go_salary=int(self.go_salary_var.get()),
                jail_fine=int(self.jail_fine_var.get()),
                max_jail_turns=int(self.max_jail_turns_var.get()),
                doubles_to_jail=int(self.doubles_to_jail_var.get()),
                auctions_enabled=self.auctions_var.get(),
                free_parking_bonus=int(self.free_parking_var.get()),
                free_parking_card_pot=self.free_parking_pot_var.get(),
                turn_limit=int(self.turn_limit_var.get()),
                property_price_percent=int(self.property_price_percent_var.get()),
                rent_percent=int(self.rent_percent_var.get()),
                monopoly_required_for_building=self.monopoly_required_var.get(),
                house_stock=int(self.house_stock_var.get()),
                hotel_stock=int(self.hotel_stock_var.get()),
                mortgages_enabled=self.mortgages_var.get(),
                unmortgage_tax_percent=int(self.unmortgage_tax_var.get()),
                transferred_mortgages=self.transferred_mortgages_var.get(),
                building_resale_percent=int(self.resale_percent_var.get()),
                automatic_rent=self.automatic_rent_var.get(),
                construction_anywhere=self.construction_anywhere_var.get(),
                property_debt_payment=self.property_debt_payment_var.get(),
                max_buildings_per_action=int(self.max_buildings_per_action_var.get()),
            )
            options.validate()
        except ValueError as error:
            return None, str(error)
        return options, ""

    def _refresh_preview(self, *args: object) -> None:
        """Actualise le résumé du profil pendant la saisie.

        Entrées:
            *args (object): Arguments envoyés automatiquement par Tkinter.

        Sortie:
            None: Le résumé ou l'erreur est affiché.
        """
        options, error = self._build_options()
        self.preview_label.configure(
            text=f"Réglage incomplet : {error}" if options is None else options.summary()
        )


    def _reset_classic(self) -> None:
        """Replace toutes les règles sur le profil classique.

        Entrées:
            Aucune.

        Sortie:
            None: Tous les champs retrouvent leurs valeurs standard.
        """
        self._apply_options_to_fields(GameOptions.classic())

    def _save(self) -> None:
        """Valide le profil et retourne à l'écran des joueurs.

        Entrées:
            Aucune.

        Sortie:
            None: Le callback reçoit le profil si tous les champs sont valides.
        """
        options, error = self._build_options()
        if options is None:
            messagebox.showwarning("Règles invalides", error, parent=self)
            return
        self.save_callback(options)
