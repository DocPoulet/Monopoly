"""Thèmes et styles visuels de la refonte graphique V22."""

from __future__ import annotations

from dataclasses import dataclass, replace
import tkinter as tk
from tkinter import ttk


@dataclass(frozen=True)
class VisualStyleSpec:
    """Décrit une identité visuelle indépendante des règles du jeu.

    Entrées:
        key (str): Identifiant stable du style.
        name (str): Nom affiché à l'utilisateur.
        description (str): Résumé visuel compact.
        accent (str): Couleur d'accent principale.
        accent_secondary (str): Accent secondaire.
        board_surface (str): Couleur dominante du plateau.
        board_center (str): Couleur de la zone centrale.
        board_edge (str): Couleur de bordure du plateau.
        preview_background (str): Fond de la miniature de sélection.

    Sortie:
        VisualStyleSpec: Style exploitable par les vues Tkinter.
    """

    key: str
    name: str
    description: str
    accent: str
    accent_secondary: str
    board_surface: str
    board_center: str
    board_edge: str
    preview_background: str


VISUAL_STYLES: dict[str, VisualStyleSpec] = {
    "classic": VisualStyleSpec(
        "classic",
        "Classique modernisé",
        "Crème, vert et codes du plateau physique.",
        "#2E7D4D",
        "#B23A48",
        "#F4EEDC",
        "#E8F1DF",
        "#37594B",
        "#DCE7D4",
    ),
    "premium": VisualStyleSpec(
        "premium",
        "Premium",
        "Bois sombre, doré et panneaux élégants.",
        "#B9934F",
        "#6F5530",
        "#CBB990",
        "#E9DFC8",
        "#4E3E2B",
        "#28241E",
    ),
    "arcade": VisualStyleSpec(
        "arcade",
        "Arcade / jeu vidéo",
        "Contrastes francs et accents électriques.",
        "#00A7E1",
        "#FF4D6D",
        "#DCEBFF",
        "#EAF7FF",
        "#1A3A5A",
        "#13283F",
    ),
    "cartoon": VisualStyleSpec(
        "cartoon",
        "Familial / cartoon",
        "Couleurs douces, contours ronds et ambiance ludique.",
        "#F28C45",
        "#5E9ED6",
        "#FFF0C9",
        "#FFF7E5",
        "#7C5B43",
        "#F5D79C",
    ),
    "hybrid": VisualStyleSpec(
        "hybrid",
        "Hybride",
        "Plateau traditionnel avec interface numérique moderne.",
        "#3A8D63",
        "#3F6FA9",
        "#E5EFE7",
        "#EEF5EF",
        "#4C6258",
        "#DCE8E1",
    ),
}


@dataclass(frozen=True)
class VisualPreferences:
    """Conserve les préférences d'affichage d'une partie.

    Entrées:
        style_key (str): Style V22 sélectionné.
        theme (str): ``light`` ou ``dark`` pour menus et arrière-plan.
        animation_speed (str): ``normal``, ``fast`` ou ``off``.
        show_net_worth (bool): Affiche ou masque le patrimoine estimé.
        pawn_ids (tuple[str, ...]): Pions attribués par ordre de joueur.
        sound_enabled (bool): Autorise la couche audio si des fichiers existent.
        show_case_numbers (bool): Affiche les index 0–39 autour du plateau à des fins de debug.

    Sortie:
        VisualPreferences: Configuration purement graphique sérialisable.
    """

    style_key: str = "hybrid"
    theme: str = "light"
    animation_speed: str = "normal"
    show_net_worth: bool = True
    pawn_ids: tuple[str, ...] = (
        "car",
        "boat",
        "hat",
        "cat",
        "rocket",
        "diamond",
    )
    sound_enabled: bool = True
    show_case_numbers: bool = False

    @classmethod
    def default(cls) -> "VisualPreferences":
        """Construit le profil V22 utilisé lorsqu'aucun choix n'a encore été fait.

        Entrées:
            Aucune.

        Sortie:
            VisualPreferences: Profil hybride clair avec animations normales.
        """
        return cls()

    @property
    def style(self) -> VisualStyleSpec:
        """Retourne la fiche de style correspondant à ``style_key``.

        Entrées:
            Aucune.

        Sortie:
            VisualStyleSpec: Style connu, ou hybride en secours.
        """
        return VISUAL_STYLES.get(self.style_key, VISUAL_STYLES["hybrid"])

    def with_pawns(self, pawn_ids: list[str] | tuple[str, ...]) -> "VisualPreferences":
        """Crée une copie avec une nouvelle attribution de pions.

        Entrées:
            pawn_ids (list[str] | tuple[str, ...]): Identifiants dans l'ordre des joueurs.

        Sortie:
            VisualPreferences: Nouvelle configuration immuable.
        """
        return replace(self, pawn_ids=tuple(pawn_ids))

    def to_dict(self) -> dict[str, object]:
        """Sérialise les préférences afin de les joindre à une sauvegarde UI.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Données JSON simples et rétrocompatibles.
        """
        return {
            "style_key": self.style_key,
            "theme": self.theme,
            "animation_speed": self.animation_speed,
            "show_net_worth": self.show_net_worth,
            "pawn_ids": list(self.pawn_ids),
            "sound_enabled": self.sound_enabled,
            "show_case_numbers": self.show_case_numbers,
        }

    @classmethod
    def from_dict(cls, data: object) -> "VisualPreferences":
        """Reconstruit des préférences depuis un objet JSON éventuellement incomplet.

        Entrées:
            data (object): Dictionnaire issu d'une sauvegarde ou autre valeur.

        Sortie:
            VisualPreferences: Profil validé avec valeurs par défaut en secours.
        """
        if not isinstance(data, dict):
            return cls.default()
        style_key = str(data.get("style_key", "hybrid"))
        if style_key not in VISUAL_STYLES:
            style_key = "hybrid"
        theme = str(data.get("theme", "light"))
        if theme not in {"light", "dark"}:
            theme = "light"
        animation_speed = str(data.get("animation_speed", "normal"))
        if animation_speed not in {"normal", "fast", "off"}:
            animation_speed = "normal"
        raw_pawns = data.get("pawn_ids", cls.default().pawn_ids)
        if isinstance(raw_pawns, (list, tuple)):
            pawns = tuple(str(item) for item in raw_pawns)
        else:
            pawns = cls.default().pawn_ids
        return cls(
            style_key=style_key,
            theme=theme,
            animation_speed=animation_speed,
            show_net_worth=bool(data.get("show_net_worth", True)),
            pawn_ids=pawns or cls.default().pawn_ids,
            sound_enabled=bool(data.get("sound_enabled", True)),
            show_case_numbers=bool(data.get("show_case_numbers", False)),
        )

    def summary(self) -> str:
        """Produit un résumé compact pour l'écran de préparation.

        Entrées:
            Aucune.

        Sortie:
            str: Style, thème, animation et visibilité du patrimoine.
        """
        theme_label = "sombre" if self.theme == "dark" else "clair"
        animation_labels = {"normal": "normales", "fast": "rapides", "off": "désactivées"}
        worth = "patrimoine visible" if self.show_net_worth else "patrimoine masqué"
        numbers = "numéros visibles" if self.show_case_numbers else "numéros masqués"
        return (
            f"{self.style.name} • thème {theme_label} • animations "
            f"{animation_labels[self.animation_speed]} • {worth} • {numbers}"
        )


def theme_palette(preferences: VisualPreferences) -> dict[str, str]:
    """Construit la palette des menus à partir du style et du thème clair/sombre.

    Entrées:
        preferences (VisualPreferences): Préférences graphiques actives.

    Sortie:
        dict[str, str]: Couleurs nommées utilisées par les widgets V22.
    """
    style = preferences.style
    if preferences.theme == "dark":
        return {
            "background": "#151A1D",
            "surface": "#20272B",
            "surface_alt": "#293237",
            "text": "#F3F6F7",
            "muted": "#AAB5BA",
            "border": "#3C474D",
            "accent": style.accent,
            "accent_secondary": style.accent_secondary,
            "danger": "#C95A5A",
        }
    return {
        "background": "#E9EFEC",
        "surface": "#FFFFFF",
        "surface_alt": "#F4F7F5",
        "text": "#23302A",
        "muted": "#67766E",
        "border": "#C5D0CA",
        "accent": style.accent,
        "accent_secondary": style.accent_secondary,
        "danger": "#B54A4A",
    }


def apply_ttk_theme(root: tk.Misc, preferences: VisualPreferences) -> dict[str, str]:
    """Applique la palette V22 aux styles ttk globaux de l'application.

    Entrées:
        root (tk.Misc): Racine Tkinter possédant le moteur ``ttk.Style``.
        preferences (VisualPreferences): Style et thème à appliquer.

    Sortie:
        dict[str, str]: Palette finale, réutilisable par les Canvas et widgets ``tk``.
    """
    palette = theme_palette(preferences)
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    try:
        root.configure(background=palette["background"])
    except tk.TclError:
        pass

    style.configure("TFrame", background=palette["background"])
    style.configure("Board.TFrame", background=palette["background"])
    style.configure("TLabel", background=palette["background"], foreground=palette["text"])
    style.configure("Muted.TLabel", background=palette["background"], foreground=palette["muted"])
    style.configure("SectionTitle.TLabel", background=palette["background"], foreground=palette["text"], font=("Arial", 15, "bold"))
    style.configure("TButton", padding=(10, 7), font=("Arial", 10))
    style.configure("Primary.TButton", padding=(12, 9), font=("Arial", 10, "bold"), background=palette["accent"], foreground="#FFFFFF")
    style.map("Primary.TButton", background=[("active", palette["accent_secondary"]), ("disabled", palette["border"])])
    style.configure("Action.TButton", padding=(11, 8), font=("Arial", 10, "bold"), background=palette["surface_alt"], foreground=palette["text"])
    style.configure("ActionHint.TLabel", background=palette["background"], foreground=palette["accent"], font=("Arial", 10, "bold"))
    style.configure("DiceNote.TLabel", background=palette["background"], foreground=palette["text"], font=("Arial", 11, "bold"))
    style.configure("TLabelframe", padding=6, background=palette["background"])
    style.configure("TLabelframe.Label", background=palette["background"], foreground=palette["text"], font=("Arial", 10, "bold"))
    style.configure("Card.TLabelframe", padding=7, background=palette["background"])
    style.configure("V22Surface.TFrame", background=palette["surface"])
    style.configure("V22SurfaceAlt.TFrame", background=palette["surface_alt"])
    style.configure("V22Card.TFrame", background=palette["surface"])
    style.configure("V22Card.TLabel", background=palette["surface"], foreground=palette["text"])
    style.configure("V22MutedCard.TLabel", background=palette["surface"], foreground=palette["muted"])
    style.configure("V22Title.TLabel", background=palette["surface"], foreground=palette["text"], font=("Arial", 24, "bold"))
    style.configure("V22PlayerActive.TFrame", background=palette["surface"])
    style.configure("Treeview", rowheight=26, font=("Arial", 9), background=palette["surface"], fieldbackground=palette["surface"], foreground=palette["text"])
    style.configure("Treeview.Heading", font=("Arial", 9, "bold"), background=palette["surface_alt"], foreground=palette["text"])

    # Compatibilité avec les anciens écrans, désormais recolorés par le thème.
    style.configure("Home.TFrame", background=palette["background"])
    style.configure("HomeSubtitle.TLabel", background=palette["background"], foreground=palette["text"], font=("Arial", 17, "bold"))
    style.configure("HomeText.TLabel", background=palette["background"], foreground=palette["muted"], font=("Arial", 11))
    style.configure("HomeHint.TLabel", background=palette["background"], foreground=palette["muted"], font=("Arial", 9))
    style.configure("HomePrimary.TButton", padding=(20, 12), font=("Arial", 12, "bold"), background=palette["accent"], foreground="#FFFFFF")
    style.configure("HomeSecondary.TButton", padding=(20, 10), font=("Arial", 11))
    style.configure("SetupCard.TFrame", background=palette["surface"])
    style.configure("SetupTitle.TLabel", background=palette["surface"], foreground=palette["text"], font=("Arial", 24, "bold"))
    style.configure("SetupSubtitle.TLabel", background=palette["surface"], foreground=palette["muted"], font=("Arial", 11))
    style.configure("SetupLabel.TLabel", background=palette["surface"], foreground=palette["text"], font=("Arial", 10, "bold"))
    return palette
