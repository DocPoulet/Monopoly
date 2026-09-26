"""Définit une enchère indépendante de l'interface utilisateur."""

from __future__ import annotations

from dataclasses import dataclass

from .player import Player
from .properties import OwnableSpace


@dataclass
class AuctionResult:
    """Représente le résultat final d'une enchère.

    Entrées:
        space (OwnableSpace): Bien mis aux enchères.
        winner (Player | None): Gagnant, ou ``None`` si personne n'a enchéri.
        amount (int): Montant de l'enchère gagnante, ou zéro sans vente.

    Sortie:
        AuctionResult: Résultat immuable exploitable par une interface ou des tests.
    """

    space: OwnableSpace
    winner: Player | None
    amount: int

    @property
    def sold(self) -> bool:
        """Indique si l'enchère s'est conclue par une vente.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            bool: ``True`` lorsqu'un gagnant existe, sinon ``False``.
        """
        return self.winner is not None


class Auction:
    """Gère les offres faites pour un bien libre sans dépendre du terminal.

    Entrées:
        space (OwnableSpace): Bien libre mis aux enchères.
        bidders (list[Player]): Joueurs autorisés à participer à l'enchère.

    Sortie:
        Auction: Objet conservant les participants actifs et la meilleure offre.
    """

    def __init__(self, space: OwnableSpace, bidders: list[Player]) -> None:
        """Initialise une enchère pour un bien encore détenu par la banque.

        Entrées:
            space (OwnableSpace): Bien à vendre aux enchères.
            bidders (list[Player]): Joueurs pouvant enchérir.

        Sortie:
            None: L'enchère démarre à zéro sans meilleur enchérisseur.

        Lève:
            ValueError: Si le bien possède déjà un propriétaire.
        """
        if space.owner is not None:
            raise ValueError("Impossible d'enchérir sur un bien déjà possédé.")

        self.space = space
        self.active_bidders = [player for player in bidders if not player.bankrupt]
        self.highest_bid = 0
        self.highest_bidder: Player | None = None
        self.finished = False

    def can_bid(self, player: Player, amount: int) -> bool:
        """Vérifie si une offre peut être acceptée dans l'état actuel de l'enchère.

        Entrées:
            player (Player): Joueur souhaitant faire une offre.
            amount (int): Montant proposé.

        Sortie:
            bool: ``True`` si le joueur participe, peut payer et dépasse l'offre actuelle.
        """
        return (
            not self.finished
            and player in self.active_bidders
            and amount > self.highest_bid
            and player.can_afford(amount)
        )

    def place_bid(self, player: Player, amount: int) -> bool:
        """Enregistre une nouvelle meilleure offre lorsqu'elle est valide.

        Entrées:
            player (Player): Joueur qui enchérit.
            amount (int): Nouvelle offre proposée.

        Sortie:
            bool: ``True`` si l'offre devient la meilleure, sinon ``False``.
        """
        if not self.can_bid(player, amount):
            return False

        self.highest_bid = amount
        self.highest_bidder = player
        return True

    def withdraw(self, player: Player) -> bool:
        """Retire définitivement un joueur de l'enchère en cours.

        Entrées:
            player (Player): Participant souhaitant abandonner.

        Sortie:
            bool: ``True`` si le joueur a été retiré, sinon ``False``.
        """
        if self.finished or player not in self.active_bidders:
            return False

        if player is self.highest_bidder:
            return False

        self.active_bidders.remove(player)
        return True

    @property
    def can_finish(self) -> bool:
        """Indique si l'enchère possède assez d'informations pour être clôturée.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            bool: ``True`` si personne ne reste, ou si le meilleur enchérisseur
            est le seul participant encore actif.
        """
        if not self.active_bidders:
            return True

        return (
            self.highest_bidder is not None
            and len(self.active_bidders) == 1
            and self.active_bidders[0] is self.highest_bidder
        )

    def finish(self) -> AuctionResult:
        """Clôture l'enchère et transfère le bien au meilleur enchérisseur.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            AuctionResult: Gagnant et prix final, ou résultat sans vente.

        Lève:
            RuntimeError: Si plusieurs participants actifs empêchent encore la clôture.
        """
        if self.finished:
            return AuctionResult(self.space, self.highest_bidder, self.highest_bid)

        if not self.can_finish:
            raise RuntimeError("L'enchère ne peut pas encore être clôturée.")

        if self.highest_bidder is None:
            self.finished = True
            return AuctionResult(self.space, None, 0)

        self.highest_bidder.pay(self.highest_bid)
        self.space.assign_to(self.highest_bidder)
        self.finished = True
        return AuctionResult(self.space, self.highest_bidder, self.highest_bid)
