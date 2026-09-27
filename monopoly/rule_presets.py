"""Sauvegarde, import et export de presets de règles Monopoly."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from .options import GameOptions

PRESET_FORMAT = "monopoly-rule-preset"
PRESET_VERSION = 1


class RulePresetError(ValueError):
    """Signale un preset absent, corrompu ou incompatible.

    Entrées:
        message (str): Explication de l'erreur.

    Sortie:
        RulePresetError: Exception spécialisée de gestion des presets.
    """


@dataclass(frozen=True)
class RulePreset:
    """Représente un preset de règles chargé depuis un fichier.

    Entrées:
        name (str): Nom lisible du preset.
        options (GameOptions): Profil de règles associé.
        saved_at (str): Date ISO de sauvegarde.
        path (Path | None): Fichier source lorsque connu.

    Sortie:
        RulePreset: Profil nommé réutilisable dans l'éditeur.
    """

    name: str
    options: GameOptions
    saved_at: str
    path: Path | None = None


def safe_preset_filename(name: str) -> str:
    """Transforme un nom libre en nom de fichier JSON stable.

    Entrées:
        name (str): Nom saisi par l'utilisateur.

    Sortie:
        str: Nom de fichier sans caractères spéciaux, terminé par ``.json``.
    """
    cleaned = re.sub(r"[^A-Za-z0-9À-ÿ_-]+", "_", name.strip())
    cleaned = cleaned.strip("_-") or "preset"
    return f"{cleaned}.json"


def preset_to_dict(name: str, options: GameOptions) -> dict[str, Any]:
    """Construit la structure JSON versionnée d'un preset.

    Entrées:
        name (str): Nom lisible du preset.
        options (GameOptions): Règles à enregistrer.

    Sortie:
        dict[str, Any]: Structure complète prête à être encodée en JSON.
    """
    options.validate()
    return {
        "format": PRESET_FORMAT,
        "version": PRESET_VERSION,
        "name": name.strip() or "Preset",
        "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "options": options.to_dict(),
    }


def save_rule_preset(
    options: GameOptions,
    path: str | Path,
    name: str,
) -> Path:
    """Écrit un preset de règles dans un fichier JSON.

    Entrées:
        options (GameOptions): Règles à sauvegarder.
        path (str | Path): Fichier de destination.
        name (str): Nom lisible enregistré dans le JSON.

    Sortie:
        Path: Chemin effectivement écrit.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            preset_to_dict(name, options),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return destination


def save_named_rule_preset(
    options: GameOptions,
    directory: str | Path,
    name: str,
) -> Path:
    """Sauvegarde un preset dans le dossier local à partir de son nom.

    Entrées:
        options (GameOptions): Profil à enregistrer.
        directory (str | Path): Dossier local des presets.
        name (str): Nom choisi par l'utilisateur.

    Sortie:
        Path: Fichier local du preset.
    """
    folder = Path(directory)
    return save_rule_preset(
        options,
        folder / safe_preset_filename(name),
        name,
    )


def load_rule_preset(path: str | Path) -> RulePreset:
    """Charge et valide un preset de règles JSON.

    Entrées:
        path (str | Path): Fichier à lire.

    Sortie:
        RulePreset: Preset validé avec ses options.

    Lève:
        RulePresetError: Si le fichier est illisible, invalide ou incompatible.
    """
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RulePresetError("Impossible de lire ce preset de règles.") from error

    if not isinstance(data, dict) or data.get("format") != PRESET_FORMAT:
        raise RulePresetError("Ce fichier n'est pas un preset Monopoly POO.")
    if int(data.get("version", -1)) != PRESET_VERSION:
        raise RulePresetError("Version de preset incompatible.")

    try:
        options = GameOptions.from_dict(dict(data.get("options", {})))
    except (TypeError, ValueError) as error:
        raise RulePresetError("Les règles du preset sont invalides.") from error

    return RulePreset(
        name=str(data.get("name", source.stem)),
        options=options,
        saved_at=str(data.get("saved_at", "")),
        path=source,
    )


def list_rule_presets(directory: str | Path) -> list[RulePreset]:
    """Liste tous les presets valides d'un dossier local.

    Entrées:
        directory (str | Path): Dossier à parcourir.

    Sortie:
        list[RulePreset]: Presets valides triés par nom ; les fichiers invalides sont ignorés.
    """
    folder = Path(directory)
    if not folder.exists():
        return []

    presets: list[RulePreset] = []
    for path in folder.glob("*.json"):
        try:
            presets.append(load_rule_preset(path))
        except RulePresetError:
            continue
    return sorted(presets, key=lambda preset: preset.name.casefold())


def import_rule_preset(
    source: str | Path,
    directory: str | Path,
) -> RulePreset:
    """Importe un preset externe dans le dossier local sans écraser un fichier existant.

    Entrées:
        source (str | Path): Preset externe à importer.
        directory (str | Path): Dossier local de destination.

    Sortie:
        RulePreset: Copie locale importée et immédiatement utilisable.
    """
    preset = load_rule_preset(source)
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)

    stem = Path(safe_preset_filename(preset.name)).stem
    destination = folder / f"{stem}.json"
    suffix = 2
    while destination.exists():
        destination = folder / f"{stem}_{suffix}.json"
        suffix += 1

    save_rule_preset(preset.options, destination, preset.name)
    return load_rule_preset(destination)
