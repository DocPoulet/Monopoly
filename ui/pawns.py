"""Catalogue de vingt pions vectoriels pour l'interface V22."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk


@dataclass(frozen=True)
class PawnSpec:
    """Décrit un pion sélectionnable sans asset externe.

    Entrées:
        key (str): Identifiant stable enregistré dans les préférences.
        name (str): Nom lisible du pion.
        glyph (str): Symbole vectoriel/texte dessiné dans le médaillon.
        silhouette (str): Forme de fond utilisée pour différencier le pion.

    Sortie:
        PawnSpec: Définition exploitable sur plateau et preview.
    """

    key: str
    name: str
    glyph: str
    silhouette: str


PAWNS: tuple[PawnSpec, ...] = (
    PawnSpec("car", "Voiture", "▰", "round"),
    PawnSpec("boat", "Bateau", "▲", "boat"),
    PawnSpec("hat", "Chapeau", "⌒", "wide"),
    PawnSpec("cat", "Chat", "⌃", "round"),
    PawnSpec("dog", "Chien", "●", "round"),
    PawnSpec("rocket", "Fusée", "↑", "tall"),
    PawnSpec("plane", "Avion", "✈", "wide"),
    PawnSpec("train", "Train", "▣", "wide"),
    PawnSpec("duck", "Canard", "◒", "round"),
    PawnSpec("crown", "Couronne", "♛", "wide"),
    PawnSpec("die", "Dé", "⚄", "square"),
    PawnSpec("robot", "Robot", "▤", "square"),
    PawnSpec("dragon", "Dragon", "ϟ", "tall"),
    PawnSpec("star", "Étoile", "★", "round"),
    PawnSpec("diamond", "Diamant", "◆", "diamond"),
    PawnSpec("guitar", "Guitare", "♪", "tall"),
    PawnSpec("cup", "Tasse", "∪", "round"),
    PawnSpec("key", "Clé", "⚿", "wide"),
    PawnSpec("moon", "Lune", "☾", "round"),
    PawnSpec("ghost", "Fantôme", "∩", "round"),
)
PAWN_BY_KEY = {item.key: item for item in PAWNS}


def normalize_pawn_ids(pawn_ids: tuple[str, ...] | list[str], player_count: int) -> tuple[str, ...]:
    """Complète une attribution de pions avec des choix valides et uniques.

    Entrées:
        pawn_ids (tuple[str, ...] | list[str]): Sélection éventuellement incomplète.
        player_count (int): Nombre de joueurs à équiper.

    Sortie:
        tuple[str, ...]: Exactement ``player_count`` identifiants uniques lorsque possible.
    """
    available = [item.key for item in PAWNS]
    selected: list[str] = []
    for key in pawn_ids:
        if key in PAWN_BY_KEY and key not in selected:
            selected.append(key)
        if len(selected) >= player_count:
            return tuple(selected[:player_count])
    for key in available:
        if key not in selected:
            selected.append(key)
        if len(selected) >= player_count:
            break
    return tuple(selected[:player_count])


def pawn_spec(key: str) -> PawnSpec:
    """Retourne une définition de pion connue avec secours sur la voiture.

    Entrées:
        key (str): Identifiant recherché.

    Sortie:
        PawnSpec: Définition correspondante ou pion voiture.
    """
    return PAWN_BY_KEY.get(key, PAWNS[0])


def draw_pawn(
    canvas: tk.Canvas,
    pawn_id: str,
    x: float,
    y: float,
    size: float,
    color: str,
    outline: str = "#FFFFFF",
    tag: str | None = None,
) -> list[int]:
    """Dessine un pion vectoriel compact sur un Canvas Tkinter.

    Entrées:
        canvas (tk.Canvas): Surface cible.
        pawn_id (str): Identifiant du pion.
        x (float): Centre horizontal.
        y (float): Centre vertical.
        size (float): Diamètre/hauteur nominale.
        color (str): Couleur attribuée au joueur.
        outline (str): Couleur du contour contrasté.
        tag (str | None): Tag Canvas optionnel commun aux éléments.

    Sortie:
        list[int]: Identifiants Canvas créés pour le pion.
    """
    spec = pawn_spec(pawn_id)
    r = max(4.0, size / 2)
    ids: list[int] = []
    tags = (tag,) if tag else ()
    ids.append(canvas.create_oval(x - r * 0.72, y + r * 0.36, x + r * 0.72, y + r * 0.62, fill="#00000033" if False else "#7B8581", outline="", tags=tags))
    if spec.silhouette == "square":
        ids.append(canvas.create_rectangle(x-r*.62, y-r*.68, x+r*.62, y+r*.50, fill=color, outline=outline, width=2, tags=tags))
    elif spec.silhouette == "diamond":
        ids.append(canvas.create_polygon(x, y-r*.80, x+r*.66, y-r*.10, x, y+r*.58, x-r*.66, y-r*.10, fill=color, outline=outline, width=2, tags=tags))
    elif spec.silhouette == "wide":
        ids.append(canvas.create_oval(x-r*.82, y-r*.48, x+r*.82, y+r*.45, fill=color, outline=outline, width=2, tags=tags))
    elif spec.silhouette == "tall":
        ids.append(canvas.create_oval(x-r*.50, y-r*.78, x+r*.50, y+r*.50, fill=color, outline=outline, width=2, tags=tags))
    elif spec.silhouette == "boat":
        ids.append(canvas.create_polygon(x-r*.78, y+r*.28, x+r*.78, y+r*.28, x+r*.48, y+r*.55, x-r*.48, y+r*.55, fill=color, outline=outline, width=2, tags=tags))
        ids.append(canvas.create_polygon(x, y-r*.72, x, y+r*.20, x+r*.56, y+r*.10, fill=color, outline=outline, width=2, tags=tags))
    else:
        ids.append(canvas.create_oval(x-r*.64, y-r*.66, x+r*.64, y+r*.50, fill=color, outline=outline, width=2, tags=tags))
    ids.append(canvas.create_text(x, y-r*.05, text=spec.glyph, fill="#FFFFFF", font=("Arial", max(7, int(r*.92)), "bold"), tags=tags))
    return ids


class PawnPreview(tk.Canvas):
    """Affiche un pion dans les écrans de sélection V22.

    Entrées:
        master (tk.Misc): Conteneur parent.
        pawn_id (str): Pion à afficher.
        color (str): Couleur de joueur utilisée pour l'aperçu.
        size (int): Taille carrée nominale.

    Sortie:
        PawnPreview: Petit Canvas actualisable.
    """

    def __init__(self, master: tk.Misc, pawn_id: str = "car", color: str = "#3A7BD5", size: int = 54) -> None:
        """Initialise l'aperçu avec fond transparent simulé.

        Entrées:
            master (tk.Misc): Parent Tkinter.
            pawn_id (str): Identifiant initial.
            color (str): Couleur initiale.
            size (int): Dimension du Canvas.

        Sortie:
            None: Le pion initial est dessiné.
        """
        super().__init__(master, width=size, height=size, highlightthickness=0, background="#F5F7F6")
        self.nominal_size = size
        self.pawn_id = pawn_id
        self.color = color
        self.bind("<Configure>", self._on_resize)
        self.redraw()

    def _on_resize(self, event: tk.Event) -> None:
        """Redessine le pion lorsque l'aperçu change de taille.

        Entrées:
            event (tk.Event): Événement Tkinter de redimensionnement.

        Sortie:
            None: Le dessin reste centré.
        """
        self.redraw()

    def set_pawn(self, pawn_id: str, color: str | None = None) -> None:
        """Change le pion et éventuellement sa couleur.

        Entrées:
            pawn_id (str): Nouvel identifiant de pion.
            color (str | None): Nouvelle couleur, si fournie.

        Sortie:
            None: L'aperçu est immédiatement actualisé.
        """
        self.pawn_id = pawn_id
        if color is not None:
            self.color = color
        self.redraw()

    def redraw(self) -> None:
        """Redessine l'aperçu complet.

        Entrées:
            Aucune.

        Sortie:
            None: Le Canvas ne contient que le pion courant.
        """
        self.delete("all")
        width = max(self.winfo_width(), self.nominal_size)
        height = max(self.winfo_height(), self.nominal_size)
        draw_pawn(self, self.pawn_id, width / 2, height / 2, min(width, height) * 0.72, self.color)
