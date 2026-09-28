"""Définit les cartes et les paquets Chance / Caisse de communauté."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from .properties import Property, Railroad, Utility

if TYPE_CHECKING:
    from .game import Game
    from .player import Player


@dataclass
class DrawnCardEvent:
    """Décrit une carte effectivement tirée pendant un tour.

    Entrées:
        deck_name (str): Nom interne du paquet, ``chance`` ou ``community_chest``.
        card (Card): Objet carte qui a été tiré.
        message (str): Résultat textuel produit après application de la carte.

    Sortie:
        DrawnCardEvent: Événement exploitable par l'interface, les replays ou les stats.
    """

    deck_name: str
    card: "Card"
    message: str = ""


class Card(ABC):
    """Interface abstraite commune à toutes les cartes du jeu.

    Entrées:
        Aucune au niveau de la classe abstraite. Les sous-classes définissent
        les données nécessaires à leur effet.

    Sortie:
        Card: Une base polymorphe dont chaque sous-classe sait appliquer son effet.
    """

    keep_when_drawn = False

    @abstractmethod
    def apply(self, game: Game, player: Player) -> str:
        """Applique l'effet de la carte à un joueur.

        Entrées:
            game (Game): Partie courante que la carte peut modifier.
            player (Player): Joueur ciblé par la carte.

        Sortie:
            str: Message décrivant l'effet appliqué.
        """
        raise NotImplementedError


@dataclass
class MoneyCard(Card):
    """Carte qui crédite ou débite une somme fixe au joueur.

    Entrées:
        text (str): Description de l'événement.
        amount (int): Somme à ajouter si positive ou à payer si négative.

    Sortie:
        MoneyCard: Une carte financière directement applicable à un joueur.
    """

    text: str
    amount: int

    def apply(self, game: Game, player: Player) -> str:
        """Applique le gain ou la dépense définie par la carte.

        Entrées:
            game (Game): Partie courante utilisée pour les paiements à la banque.
            player (Player): Joueur qui reçoit ou paie la somme.

        Sortie:
            str: Description de la carte suivie du montant signé appliqué.
        """
        if self.amount >= 0:
            player.receive(self.amount)
        else:
            game.rules.pay_bank(player, -self.amount)

        return f"{self.text} ({self.amount:+d})"


@dataclass
class MoveToCard(Card):
    """Carte qui déplace le joueur vers une case précise puis résout cette case.

    Entrées:
        text (str): Description affichée de la carte.
        destination (int): Index de la case de destination.
        collect_go (bool): Indique si le passage par Départ verse 200.

    Sortie:
        MoveToCard: Carte de déplacement absolu.
    """

    text: str
    destination: int
    collect_go: bool = True

    def apply(self, game: Game, player: Player) -> str:
        """Déplace le joueur vers la destination et applique l'effet de la case.

        Entrées:
            game (Game): Partie contenant le plateau et les règles de déplacement.
            player (Player): Joueur déplacé par la carte.

        Sortie:
            str: Texte de la carte complété par l'effet de la case d'arrivée.
        """
        effect = game.move_to_and_resolve(
            player,
            self.destination,
            collect_go=self.collect_go,
            dice_total=0,
        )
        return game.combine_messages(self.text, effect)


@dataclass
class MoveBackCard(Card):
    """Carte qui fait reculer un joueur puis résout la nouvelle case.

    Entrées:
        text (str): Description affichée de la carte.
        steps (int): Nombre positif de cases à reculer.

    Sortie:
        MoveBackCard: Carte de déplacement relatif vers l'arrière.
    """

    text: str
    steps: int

    def apply(self, game: Game, player: Player) -> str:
        """Recule le joueur sans salaire de Départ puis résout sa case finale.

        Entrées:
            game (Game): Partie contenant les règles de déplacement.
            player (Player): Joueur à faire reculer.

        Sortie:
            str: Texte de la carte suivi de l'effet éventuel de la case finale.
        """
        effect = game.move_backward_and_resolve(player, self.steps)
        return game.combine_messages(self.text, effect)


@dataclass
class GoToJailCard(Card):
    """Carte qui envoie immédiatement un joueur en prison sans passer par Départ.

    Entrées:
        text (str): Description affichée de la carte.

    Sortie:
        GoToJailCard: Carte d'incarcération immédiate.
    """

    text: str

    def apply(self, game: Game, player: Player) -> str:
        """Envoie le joueur sur la case Prison et active son état de prison.

        Entrées:
            game (Game): Partie dont les règles savent envoyer en prison.
            player (Player): Joueur ciblé.

        Sortie:
            str: Texte descriptif de la carte.
        """
        game.rules.send_to_jail(player)
        return self.text


@dataclass
class GetOutOfJailCard(Card):
    """Carte conservée par le joueur jusqu'à son utilisation pour sortir de prison.

    Entrées:
        text (str): Description affichée lors de la pioche.
        deck_name (str): Identifiant du paquet auquel rendre la carte après usage.

    Sortie:
        GetOutOfJailCard: Carte conservable qui n'est pas replacée après la pioche.
    """

    text: str
    deck_name: str
    keep_when_drawn = True

    def apply(self, game: Game, player: Player) -> str:
        """Ajoute la carte à la main du joueur sans la consommer immédiatement.

        Entrées:
            game (Game): Partie courante, utilisée lors du retour futur au paquet.
            player (Player): Joueur qui conserve la carte.

        Sortie:
            str: Texte indiquant que la carte peut être conservée.
        """
        player.add_held_card(self)
        return self.text


@dataclass
class NearestRailroadCard(Card):
    """Carte qui avance jusqu'à la prochaine gare et double un éventuel loyer.

    Entrées:
        text (str): Description affichée de la carte.

    Sortie:
        NearestRailroadCard: Carte spécialisée pour les gares.
    """

    text: str

    def apply(self, game: Game, player: Player) -> str:
        """Déplace le joueur à la prochaine gare et résout la case avec loyer x2.

        Entrées:
            game (Game): Partie utilisée pour rechercher la prochaine gare.
            player (Player): Joueur déplacé.

        Sortie:
            str: Texte de la carte suivi de l'effet de la gare d'arrivée.
        """
        destination = game.board.find_next_space_of_type(player.position, Railroad)
        effect = game.move_to_and_resolve(
            player,
            destination,
            collect_go=True,
            dice_total=0,
            rent_multiplier=2,
        )
        return game.combine_messages(self.text, effect)


@dataclass
class NearestUtilityCard(Card):
    """Carte qui avance jusqu'à la prochaine compagnie avec un loyer spécial.

    Entrées:
        text (str): Description affichée de la carte.

    Sortie:
        NearestUtilityCard: Carte spécialisée pour les compagnies.
    """

    text: str

    def apply(self, game: Game, player: Player) -> str:
        """Va à la prochaine compagnie et ne relance les dés que si un loyer spécial est dû.

        Entrées:
            game (Game): Partie utilisée pour chercher la compagnie et relancer les dés.
            player (Player): Joueur déplacé.

        Sortie:
            str: Texte de la carte, lancer spécial éventuel et effet de la case.

        Notes:
            Si la compagnie est libre, appartient déjà au joueur ou est hypothéquée,
            aucun lancer supplémentaire n'est consommé.
        """
        destination = game.board.find_next_space_of_type(player.position, Utility)
        utility = game.board[destination]

        if (
            isinstance(utility, Utility)
            and utility.owner is not None
            and utility.owner is not player
            and not utility.mortgaged
        ):
            dice = game.roll_dice()
            dice_total = sum(dice)
            effect = game.move_to_and_resolve(
                player,
                destination,
                collect_go=True,
                dice_total=dice_total,
                utility_multiplier=10,
            )
            detail = f"Nouveau lancer pour la compagnie : {dice[0]} + {dice[1]}."
            return game.combine_messages(self.text, detail, effect)

        effect = game.move_to_and_resolve(
            player,
            destination,
            collect_go=True,
            dice_total=0,
        )
        return game.combine_messages(self.text, effect)


@dataclass
class RepairsCard(Card):
    """Carte qui facture un montant par maison et par hôtel possédés.

    Entrées:
        text (str): Description affichée de la carte.
        house_cost (int): Montant dû pour chaque maison.
        hotel_cost (int): Montant dû pour chaque hôtel.

    Sortie:
        RepairsCard: Carte calculant automatiquement les réparations du patrimoine.
    """

    text: str
    house_cost: int
    hotel_cost: int

    def apply(self, game: Game, player: Player) -> str:
        """Compte les bâtiments du joueur puis fait payer le total à la banque.

        Entrées:
            game (Game): Partie utilisée pour effectuer le paiement.
            player (Player): Propriétaire dont les bâtiments sont comptés.

        Sortie:
            str: Texte détaillant le nombre de bâtiments et le montant total payé.
        """
        houses = sum(
            space.houses
            for space in player.properties
            if isinstance(space, Property)
        )
        hotels = sum(
            1
            for space in player.properties
            if isinstance(space, Property) and space.hotel
        )
        total = houses * self.house_cost + hotels * self.hotel_cost
        game.rules.pay_bank(player, total)
        return f"{self.text} {houses} maison(s), {hotels} hôtel(s) : -{total}."


@dataclass
class PerPlayerCard(Card):
    """Carte qui transfère une somme fixe entre le joueur et tous ses adversaires.

    Entrées:
        text (str): Description affichée de la carte.
        amount (int): Montant par adversaire. Positif = le joueur encaisse,
            négatif = le joueur paie chaque adversaire.

    Sortie:
        PerPlayerCard: Carte de transfert collectif entre joueurs.
    """

    text: str
    amount: int

    def apply(self, game: Game, player: Player) -> str:
        """Effectue les transferts un par un entre le joueur et ses adversaires actifs.

        Entrées:
            game (Game): Partie contenant les joueurs actifs et les règles de paiement.
            player (Player): Joueur concerné par les transferts.

        Sortie:
            str: Message indiquant le montant appliqué par adversaire.
        """
        others = [p for p in list(game.active_players) if p is not player]

        if self.amount >= 0:
            for other in others:
                if not other.bankrupt:
                    game.rules.transfer_money(other, player, self.amount)
        else:
            for other in others:
                if player.bankrupt:
                    break
                game.rules.transfer_money(player, other, -self.amount)

        sign = "+" if self.amount >= 0 else "-"
        return f"{self.text} ({sign}{abs(self.amount)} par autre joueur)"


class CardDeck:
    """Gère un paquet cyclique de cartes, avec possibilité de cartes conservées.

    Entrées:
        name (str): Identifiant stable du paquet.
        cards (list[Card]): Cartes placées dans le paquet.
        rng (Random | None): Générateur utilisé pour mélanger le paquet.
        shuffle (bool): Active ou non le mélange initial.

    Sortie:
        CardDeck: Un paquet prêt à être pioché et à récupérer ses cartes conservées.
    """

    def __init__(
        self,
        name: str,
        cards: list[Card],
        rng: Random | None = None,
        shuffle: bool = True,
    ) -> None:
        """Initialise le paquet, avec mélange optionnel reproductible.

        Entrées:
            name (str): Nom interne du paquet.
            cards (list[Card]): Cartes à charger.
            rng (Random | None): Générateur aléatoire de la partie ou ``None``.
            shuffle (bool): ``True`` pour mélanger avant la première pioche.

        Sortie:
            None: Les cartes sont stockées dans une ``deque`` interne.
        """
        ordered_cards = list(cards)
        if shuffle:
            (rng or Random()).shuffle(ordered_cards)
        self.name = name
        self.cards = deque(ordered_cards)

    def draw(self, game: Game, player: Player) -> str:
        """Pioche et applique la première carte du paquet.

        Entrées:
            game (Game): Partie courante transmise à la carte.
            player (Player): Joueur auquel la carte s'applique.

        Sortie:
            str: Message produit par l'effet de la carte. Une carte conservable
            reste hors du paquet jusqu'à son utilisation.
        """
        if not self.cards:
            raise RuntimeError(f"Le paquet {self.name} ne contient plus de cartes.")

        card = self.cards.popleft()
        event = DrawnCardEvent(self.name, card)
        game.drawn_cards_this_turn.append(event)

        cash_before = {item.player_id: item.cash for item in game.players}
        position_before = player.position
        jail_before = player.in_jail
        held_before = len(player.held_cards)
        pot_before = game.free_parking_pot

        game.begin_card_resolution()
        try:
            message = card.apply(game, player)
        finally:
            game.end_card_resolution()
        event.message = message

        cash_after = {item.player_id: item.cash for item in game.players}
        drawer_cash_delta = cash_after[player.player_id] - cash_before[player.player_id]
        other_players_cash_delta = sum(
            cash_after[item.player_id] - cash_before[item.player_id]
            for item in game.players
            if item.player_id != player.player_id
        )
        total_player_cash_delta = sum(
            cash_after[item.player_id] - cash_before[item.player_id]
            for item in game.players
        )

        game.record_event(
            "card_draw",
            f"{player.name} pioche : {getattr(card, 'text', type(card).__name__)}",
            player,
            deck=self.name,
            card_type=type(card).__name__,
            card_text=getattr(card, "text", ""),
            drawer_cash_delta=drawer_cash_delta,
            other_players_cash_delta=other_players_cash_delta,
            total_player_cash_delta=total_player_cash_delta,
            free_parking_pot_delta=game.free_parking_pot - pot_before,
            position_before=position_before,
            position_after=player.position,
            moved=player.position != position_before,
            sent_to_jail=(not jail_before and player.in_jail),
            get_out_card_received=len(player.held_cards) > held_before,
        )

        if not card.keep_when_drawn:
            self.cards.append(card)

        return message

    def return_card(self, card: Card) -> None:
        """Replace en fin de paquet une carte précédemment conservée par un joueur.

        Entrées:
            card (Card): Carte à remettre dans le paquet.

        Sortie:
            None: La carte est ajoutée en fin de file si elle n'y est pas déjà.
        """
        if card not in self.cards:
            self.cards.append(card)

    def __len__(self) -> int:
        """Retourne le nombre de cartes actuellement présentes dans le paquet.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            int: Taille courante du paquet, hors cartes détenues par les joueurs.
        """
        return len(self.cards)


def create_chance_deck(rng: Random | None = None, shuffle: bool = True) -> CardDeck:
    """Crée un paquet Chance classique de seize cartes adaptées au plateau générique.

    Entrées:
        rng (Random | None): Générateur de la partie utilisé pour le mélange.
        shuffle (bool): ``True`` pour mélanger le paquet à sa création.

    Sortie:
        CardDeck: Paquet Chance complet prêt à être utilisé.
    """
    return CardDeck(
        "chance",
        [
            MoveToCard("Avancez jusqu'au terrain le plus cher.", 39),
            MoveToCard("Avancez jusqu'à Départ.", 0),
            MoveToCard("Avancez jusqu'au terrain rouge n°2.", 24),
            MoveToCard("Avancez jusqu'au premier terrain rose.", 11),
            NearestRailroadCard("Avancez jusqu'à la prochaine gare. Loyer doublé si elle est possédée."),
            NearestRailroadCard("Avancez jusqu'à la prochaine gare. Loyer doublé si elle est possédée."),
            NearestUtilityCard("Avancez jusqu'à la prochaine compagnie."),
            MoneyCard("La banque vous verse un dividende", 50),
            GetOutOfJailCard("Conservez cette carte : sortie de prison gratuite.", "chance"),
            MoveBackCard("Reculez de trois cases.", 3),
            GoToJailCard("Allez directement en prison, sans passer par Départ."),
            RepairsCard("Réparations générales.", 25, 100),
            MoneyCard("Amende", -15),
            MoveToCard("Avancez jusqu'à la première gare.", 5),
            PerPlayerCard("Vous êtes nommé président : payez chaque joueur.", -50),
            MoneyCard("Votre prêt immobilier arrive à échéance", 150),
        ],
        rng=rng,
        shuffle=shuffle,
    )


def create_community_chest_deck(
    rng: Random | None = None,
    shuffle: bool = True,
) -> CardDeck:
    """Crée un paquet Caisse de communauté classique de seize cartes.

    Entrées:
        rng (Random | None): Générateur de la partie utilisé pour le mélange.
        shuffle (bool): ``True`` pour mélanger le paquet à sa création.

    Sortie:
        CardDeck: Paquet Caisse de communauté complet prêt à être utilisé.
    """
    return CardDeck(
        "community_chest",
        [
            MoveToCard("Avancez jusqu'à Départ.", 0),
            MoneyCard("Erreur de la banque en votre faveur", 200),
            MoneyCard("Frais médicaux", -50),
            MoneyCard("Vente de placements", 50),
            GetOutOfJailCard("Conservez cette carte : sortie de prison gratuite.", "community_chest"),
            GoToJailCard("Allez directement en prison, sans passer par Départ."),
            MoneyCard("Votre fonds de vacances arrive à échéance", 100),
            MoneyCard("Remboursement d'impôt", 20),
            PerPlayerCard("C'est votre anniversaire : recevez de chaque joueur.", 10),
            MoneyCard("Assurance-vie", 100),
            MoneyCard("Frais d'hôpital", -100),
            MoneyCard("Frais de scolarité", -50),
            MoneyCard("Honoraires de consultation", 25),
            RepairsCard("Réparations de voirie.", 40, 115),
            MoneyCard("Prix de beauté", 10),
            MoneyCard("Héritage", 100),
        ],
        rng=rng,
        shuffle=shuffle,
    )
