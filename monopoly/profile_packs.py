"""Import et export d'un pack complet combinant règles et plateau."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .board_config import BoardConfig
from .options import GameOptions

PROFILE_PACK_FORMAT = "monopoly-profile-pack"
PROFILE_PACK_VERSION = 1


class ProfilePackError(ValueError):
    """Signale un pack complet absent, corrompu ou incompatible.

    Entrées:
        message (str): Description de l'erreur.

    Sortie:
        ProfilePackError: Exception dédiée aux packs règles + plateau.
    """


@dataclass(frozen=True)
class ProfilePack:
    """Regroupe un profil de règles et un plateau personnalisable.

    Entrées:
        name (str): Nom lisible du pack.
        options (GameOptions): Règles du pack.
        board_config (BoardConfig): Plateau et cartes du pack.
        saved_at (str): Date ISO d'export.
        path (Path | None): Fichier source éventuel.

    Sortie:
        ProfilePack: Variante complète portable.
    """

    name: str
    options: GameOptions
    board_config: BoardConfig
    saved_at: str
    path: Path | None = None

    def summary(self) -> str:
        """Construit un résumé compact des deux parties du pack.

        Entrées:
            Aucune.

        Sortie:
            str: Nom, résumé des règles et résumé du plateau.
        """
        return f"{self.name} • {self.options.summary()} • {self.board_config.summary()}"


def profile_pack_to_dict(
    name: str,
    options: GameOptions,
    board_config: BoardConfig,
) -> dict[str, Any]:
    """Construit la structure JSON versionnée d'un pack complet.

    Entrées:
        name (str): Nom lisible du pack.
        options (GameOptions): Règles à embarquer.
        board_config (BoardConfig): Plateau et cartes à embarquer.

    Sortie:
        dict[str, Any]: Structure prête à être sérialisée.
    """
    options.validate()
    board_config.validate()
    return {
        "format": PROFILE_PACK_FORMAT,
        "version": PROFILE_PACK_VERSION,
        "name": name.strip() or "Pack Monopoly",
        "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "options": options.to_dict(),
        "board": board_config.to_dict(),
    }


def save_profile_pack(
    path: str | Path,
    name: str,
    options: GameOptions,
    board_config: BoardConfig,
) -> Path:
    """Écrit un pack complet règles + plateau dans un fichier JSON.

    Entrées:
        path (str | Path): Destination du fichier.
        name (str): Nom du pack.
        options (GameOptions): Profil de règles.
        board_config (BoardConfig): Plateau et cartes.

    Sortie:
        Path: Chemin effectivement écrit.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            profile_pack_to_dict(name, options, board_config),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return destination


def load_profile_pack(path: str | Path) -> ProfilePack:
    """Charge et valide un pack complet depuis un fichier JSON.

    Entrées:
        path (str | Path): Fichier à lire.

    Sortie:
        ProfilePack: Pack validé et prêt à être appliqué.

    Lève:
        ProfilePackError: Si le fichier, le format, les règles ou le plateau sont invalides.
    """
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProfilePackError("Impossible de lire ce pack complet.") from error

    if not isinstance(data, dict) or data.get("format") != PROFILE_PACK_FORMAT:
        raise ProfilePackError("Ce fichier n'est pas un pack complet Monopoly POO.")
    if int(data.get("version", -1)) != PROFILE_PACK_VERSION:
        raise ProfilePackError("Version de pack complet incompatible.")

    try:
        options = GameOptions.from_dict(dict(data.get("options", {})))
        board_config = BoardConfig.from_dict(dict(data.get("board", {})))
    except (TypeError, ValueError, KeyError) as error:
        raise ProfilePackError("Le contenu du pack complet est invalide.") from error

    return ProfilePack(
        name=str(data.get("name", source.stem)),
        options=options,
        board_config=board_config,
        saved_at=str(data.get("saved_at", "")),
        path=source,
    )
