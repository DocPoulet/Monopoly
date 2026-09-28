"""Couche audio optionnelle V22, fonctionnelle sans aucun fichier sonore livré."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tkinter as tk


SOUND_FILES: dict[str, str] = {
    "dice_roll": "dice_roll.wav",
    "pawn_move": "pawn_move.wav",
    "cash_gain": "cash_gain.wav",
    "cash_loss": "cash_loss.wav",
    "property_buy": "property_buy.wav",
    "house_build": "house_build.wav",
    "hotel_build": "hotel_build.wav",
    "jail": "jail.wav",
    "card_draw": "card_draw.wav",
    "auction": "auction.wav",
    "victory": "victory.wav",
}


class AudioManager:
    """Joue des effets sonores utilisateur sans rendre les fichiers obligatoires.

    Entrées:
        root (tk.Misc): Racine utilisée comme secours silencieux.
        sound_directory (str | Path): Dossier contenant les fichiers attendus.
        enabled (bool): Active ou désactive globalement la lecture.

    Sortie:
        AudioManager: Gestionnaire tolérant les fichiers absents.
    """

    def __init__(self, root: tk.Misc, sound_directory: str | Path, enabled: bool = True) -> None:
        """Détecte un lecteur disponible sans lancer de son.

        Entrées:
            root (tk.Misc): Widget racine.
            sound_directory (str | Path): Dossier des fichiers WAV.
            enabled (bool): État initial de la couche audio.

        Sortie:
            None: Le gestionnaire est prêt, même sur une machine sans lecteur audio.
        """
        self.root = root
        self.sound_directory = Path(sound_directory)
        self.enabled = enabled
        self._player_command = self._discover_player_command()

    @staticmethod
    def _discover_player_command() -> list[str] | None:
        """Détecte une commande audio non bloquante disponible sur le système.

        Entrées:
            Aucune.

        Sortie:
            list[str] | None: Préfixe de commande ou ``None`` sur Windows/secours.
        """
        if sys.platform.startswith("win"):
            return None
        for command, arguments in (
            ("paplay", []),
            ("aplay", ["-q"]),
            ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
        ):
            path = shutil.which(command)
            if path:
                return [path, *arguments]
        return None

    def set_enabled(self, enabled: bool) -> None:
        """Active ou coupe la lecture sans modifier les fichiers du dossier.

        Entrées:
            enabled (bool): Nouvel état global.

        Sortie:
            None: Les futurs appels ``play`` respectent cet état.
        """
        self.enabled = bool(enabled)

    def path_for(self, event_name: str) -> Path | None:
        """Retourne le fichier attendu pour un événement sonore.

        Entrées:
            event_name (str): Clé comme ``dice_roll`` ou ``victory``.

        Sortie:
            Path | None: Chemin attendu, ou ``None`` pour une clé inconnue.
        """
        filename = SOUND_FILES.get(event_name)
        if filename is None:
            return None
        return self.sound_directory / filename

    def play(self, event_name: str) -> bool:
        """Tente de jouer un effet et échoue silencieusement si le fichier manque.

        Entrées:
            event_name (str): Nom logique de l'effet sonore.

        Sortie:
            bool: ``True`` lorsqu'une lecture a pu être déclenchée.
        """
        if not self.enabled:
            return False
        path = self.path_for(event_name)
        if path is None or not path.is_file():
            return False
        try:
            if sys.platform.startswith("win"):
                import winsound

                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
            if self._player_command:
                subprocess.Popen(
                    [*self._player_command, str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env={**os.environ},
                )
                return True
        except (OSError, RuntimeError):
            return False
        return False
