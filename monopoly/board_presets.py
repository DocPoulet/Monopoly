"""Sauvegarde, import et export de presets de plateau Monopoly."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from .board_config import BoardConfig

BOARD_PRESET_FORMAT = "monopoly-board-preset"
BOARD_PRESET_VERSION = 1


class BoardPresetError(ValueError):
    """Signale un preset de plateau absent, corrompu ou incompatible.

    Entrées:
        message (str): Explication de l'erreur.

    Sortie:
        BoardPresetError: Exception spécialisée de gestion des presets de plateau.
    """


@dataclass(frozen=True)
class BoardPreset:
    """Représente un preset de plateau chargé depuis un fichier.

    Entrées:
        name (str): Nom lisible du preset.
        board_config (BoardConfig): Définition du plateau et des cartes.
        saved_at (str): Date ISO de sauvegarde.
        path (Path | None): Fichier source lorsque connu.

    Sortie:
        BoardPreset: Plateau nommé réutilisable dans l'éditeur.
    """

    name: str
    board_config: BoardConfig
    saved_at: str
    path: Path | None = None


def safe_board_preset_filename(name: str) -> str:
    """Transforme un nom libre en nom de fichier JSON stable.

    Entrées:
        name (str): Nom saisi par l'utilisateur.

    Sortie:
        str: Nom de fichier terminé par ``.json``.
    """
    cleaned = re.sub(r"[^A-Za-z0-9À-ÿ_-]+", "_", name.strip())
    cleaned = cleaned.strip("_-") or "plateau"
    return f"{cleaned}.json"


def board_preset_to_dict(name: str, board_config: BoardConfig) -> dict[str, Any]:
    """Construit la structure JSON versionnée d'un preset de plateau.

    Entrées:
        name (str): Nom lisible du preset.
        board_config (BoardConfig): Plateau à enregistrer.

    Sortie:
        dict[str, Any]: Structure prête à être encodée en JSON.
    """
    board_config.validate()
    return {
        "format": BOARD_PRESET_FORMAT,
        "version": BOARD_PRESET_VERSION,
        "name": name.strip() or board_config.name or "Plateau",
        "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "board": board_config.to_dict(),
    }


def save_board_preset(
    board_config: BoardConfig,
    path: str | Path,
    name: str,
) -> Path:
    """Écrit un preset de plateau dans un fichier JSON.

    Entrées:
        board_config (BoardConfig): Définition à sauvegarder.
        path (str | Path): Fichier de destination.
        name (str): Nom lisible enregistré dans le preset.

    Sortie:
        Path: Chemin effectivement écrit.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = board_preset_to_dict(name, board_config)
    data["board"]["name"] = name.strip() or board_config.name
    destination.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def save_named_board_preset(
    board_config: BoardConfig,
    directory: str | Path,
    name: str,
) -> Path:
    """Sauvegarde un preset dans la bibliothèque locale.

    Entrées:
        board_config (BoardConfig): Plateau à enregistrer.
        directory (str | Path): Dossier local des presets.
        name (str): Nom choisi.

    Sortie:
        Path: Fichier local créé ou remplacé.
    """
    folder = Path(directory)
    return save_board_preset(
        board_config,
        folder / safe_board_preset_filename(name),
        name,
    )


def load_board_preset(path: str | Path) -> BoardPreset:
    """Charge et valide un preset de plateau JSON.

    Entrées:
        path (str | Path): Fichier à lire.

    Sortie:
        BoardPreset: Preset validé.

    Lève:
        BoardPresetError: Si le format ou le plateau est invalide.
    """
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BoardPresetError("Impossible de lire ce preset de plateau.") from error
    if not isinstance(data, dict) or data.get("format") != BOARD_PRESET_FORMAT:
        raise BoardPresetError("Ce fichier n'est pas un preset de plateau Monopoly POO.")
    if int(data.get("version", -1)) != BOARD_PRESET_VERSION:
        raise BoardPresetError("Version de preset de plateau incompatible.")
    try:
        board_config = BoardConfig.from_dict(dict(data.get("board", {})))
    except (TypeError, ValueError, KeyError) as error:
        raise BoardPresetError("Le contenu du plateau est invalide.") from error
    return BoardPreset(
        name=str(data.get("name", source.stem)),
        board_config=board_config,
        saved_at=str(data.get("saved_at", "")),
        path=source,
    )


def list_board_presets(directory: str | Path) -> list[BoardPreset]:
    """Liste les presets de plateau valides d'un dossier.

    Entrées:
        directory (str | Path): Dossier à parcourir.

    Sortie:
        list[BoardPreset]: Presets triés par nom.
    """
    folder = Path(directory)
    if not folder.exists():
        return []
    presets: list[BoardPreset] = []
    for path in folder.glob("*.json"):
        try:
            presets.append(load_board_preset(path))
        except BoardPresetError:
            continue
    return sorted(presets, key=lambda preset: preset.name.casefold())


def import_board_preset(
    source: str | Path,
    directory: str | Path,
) -> BoardPreset:
    """Importe un preset externe dans la bibliothèque locale sans écrasement.

    Entrées:
        source (str | Path): Fichier externe.
        directory (str | Path): Dossier local de destination.

    Sortie:
        BoardPreset: Copie locale importée.
    """
    preset = load_board_preset(source)
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    stem = Path(safe_board_preset_filename(preset.name)).stem
    destination = folder / f"{stem}.json"
    suffix = 2
    while destination.exists():
        destination = folder / f"{stem}_{suffix}.json"
        suffix += 1
    save_board_preset(preset.board_config, destination, preset.name)
    return load_board_preset(destination)


def rename_board_preset(preset: BoardPreset, new_name: str) -> BoardPreset:
    """Renomme un preset local, son contenu et son fichier.

    Entrées:
        preset (BoardPreset): Preset local à renommer.
        new_name (str): Nouveau nom lisible.

    Sortie:
        BoardPreset: Preset rechargé depuis son nouveau fichier.

    Lève:
        ValueError: Si le preset n'a pas de fichier local ou si le nom est vide.
    """
    if preset.path is None:
        raise ValueError("Ce preset n'est pas associé à un fichier local.")
    cleaned = new_name.strip()
    if not cleaned:
        raise ValueError("Le nouveau nom du preset ne peut pas être vide.")
    destination = preset.path.parent / safe_board_preset_filename(cleaned)
    if destination.exists() and destination.resolve() != preset.path.resolve():
        raise ValueError("Un preset de plateau porte déjà ce nom.")
    board = preset.board_config.clone()
    board.name = cleaned
    save_board_preset(board, destination, cleaned)
    if destination.resolve() != preset.path.resolve() and preset.path.exists():
        preset.path.unlink()
    return load_board_preset(destination)


def delete_board_preset(preset: BoardPreset) -> None:
    """Supprime le fichier local d'un preset de plateau.

    Entrées:
        preset (BoardPreset): Preset à supprimer.

    Sortie:
        None: Le fichier local est supprimé s'il existe.
    """
    if preset.path is None:
        raise ValueError("Ce preset n'est pas associé à un fichier local.")
    if preset.path.exists():
        preset.path.unlink()
