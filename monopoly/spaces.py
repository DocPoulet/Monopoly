"""Définit les cases non achetables du plateau et leur comportement à l'arrivée."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .player import Player


@dataclass
class Space(ABC):
    """Classe abstraite commune aux cases non achetables du plateau.

    Entrées:
        index (int): Position de la case sur le plateau.
        name (str): Nom affiché de la case.

    Sortie:
        Space: Base polymorphe pour toutes les cases spéciales du plateau.
    """

    index: int
    name: str

    @abstractmethod
    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Applique l'effet de la case lorsqu'un joueur s'y arrête.

        Entrées:
            game (Game): Partie courante dans laquelle l'effet doit être appliqué.
            player (Player): Joueur qui vient d'arriver sur la case.
            dice_total (int): Somme des dés du déplacement courant.

        Sortie:
            str: Message décrivant l'effet appliqué au joueur.
        """
        raise NotImplementedError


@dataclass
class GoSpace(Space):
    """Représente la case Départ.

    Entrées:
        index (int): Position de la case.
        name (str): Nom affiché.

    Sortie:
        GoSpace: Case spéciale sans effet supplémentaire à l'arrêt.
    """

    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Traite l'arrivée exacte d'un joueur sur la case Départ.

        Entrées:
            game (Game): Partie courante, non modifiée par cette méthode.
            player (Player): Joueur arrivant sur Départ.
            dice_total (int): Somme des dés, non utilisée ici.

        Sortie:
            str: Message indiquant que le joueur se trouve sur Départ.
        """
        return f"{player.name} est sur la case Départ."


@dataclass
class TaxSpace(Space):
    """Représente une case de taxe versée à la banque.

    Entrées:
        index (int): Position de la case.
        name (str): Nom de la taxe.
        amount (int): Montant à payer lorsque le joueur s'arrête sur la case.

    Sortie:
        TaxSpace: Une case capable de prélever la taxe définie.
    """

    amount: int = 0

    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Prélève la taxe au joueur qui arrive sur la case.

        Entrées:
            game (Game): Partie courante donnant accès aux règles de paiement.
            player (Player): Joueur qui doit payer la taxe.
            dice_total (int): Somme des dés, non utilisée pour une taxe.

        Sortie:
            str: Message indiquant le montant payé à la banque.
        """
        game.rules.pay_bank(player, self.amount)
        return f"{player.name} paie {self.amount} à la banque."


@dataclass
class JailSpace(Space):
    """Représente la case Prison lorsqu'un joueur y est en simple visite.

    Entrées:
        index (int): Position de la prison sur le plateau.
        name (str): Nom affiché de la case.

    Sortie:
        JailSpace: Une case sans effet pour un joueur qui y arrive normalement.
    """

    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Traite une arrivée normale sur la case Prison.

        Entrées:
            game (Game): Partie courante, non modifiée ici.
            player (Player): Joueur en simple visite.
            dice_total (int): Somme des dés, non utilisée ici.

        Sortie:
            str: Message indiquant que le joueur est en simple visite.
        """
        return f"{player.name} est en simple visite."


@dataclass
class FreeParkingSpace(Space):
    """Représente la case Parc Gratuit sans cagnotte maison.

    Entrées:
        index (int): Position de la case.
        name (str): Nom affiché de la case.

    Sortie:
        FreeParkingSpace: Une case neutre sans effet financier.
    """

    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Traite l'arrivée sur le Parc Gratuit sans modifier la partie.

        Entrées:
            game (Game): Partie courante, non modifiée ici.
            player (Player): Joueur arrivant sur la case.
            dice_total (int): Somme des dés, non utilisée ici.

        Sortie:
            str: Message signalant le passage sur le Parc Gratuit.
        """
        return f"{player.name} se repose au Parc Gratuit."


@dataclass
class GoToJailSpace(Space):
    """Représente la case qui envoie immédiatement le joueur en prison.

    Entrées:
        index (int): Position de la case.
        name (str): Nom affiché de la case.

    Sortie:
        GoToJailSpace: Une case qui délègue l'incarcération aux règles du jeu.
    """

    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Envoie le joueur sur la case Prison et active son état de prisonnier.

        Entrées:
            game (Game): Partie courante donnant accès aux règles de prison.
            player (Player): Joueur à envoyer en prison.
            dice_total (int): Somme des dés, non utilisée ici.

        Sortie:
            str: Message confirmant l'envoi en prison.
        """
        game.rules.send_to_jail(player)
        return f"{player.name} va directement en prison."


@dataclass
class ChanceSpace(Space):
    """Représente une case Chance qui fait piocher dans le paquet Chance.

    Entrées:
        index (int): Position de la case.
        name (str): Nom affiché de la case.

    Sortie:
        ChanceSpace: Une case qui déclenche la prochaine carte Chance.
    """

    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Pioche et applique la prochaine carte Chance.

        Entrées:
            game (Game): Partie contenant le paquet Chance.
            player (Player): Joueur auquel la carte s'applique.
            dice_total (int): Somme des dés, non utilisée directement ici.

        Sortie:
            str: Message renvoyé par la carte Chance appliquée.
        """
        return game.chance_deck.draw(game, player)


@dataclass
class CommunityChestSpace(Space):
    """Représente une case Caisse de communauté.

    Entrées:
        index (int): Position de la case.
        name (str): Nom affiché de la case.

    Sortie:
        CommunityChestSpace: Une case qui déclenche la prochaine carte du paquet.
    """

    def land(self, game: Game, player: Player, dice_total: int) -> str:
        """Pioche et applique la prochaine carte Caisse de communauté.

        Entrées:
            game (Game): Partie contenant le paquet Caisse de communauté.
            player (Player): Joueur auquel la carte s'applique.
            dice_total (int): Somme des dés, non utilisée directement ici.

        Sortie:
            str: Message renvoyé par la carte appliquée.
        """
        return game.community_chest_deck.draw(game, player)
