"""Orchestre une partie complète : joueurs, tours, dés, cartes et résolution des cases."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .auction import Auction
from .board import Board
from .cards import Card, DrawnCardEvent, GetOutOfJailCard, create_chance_deck, create_community_chest_deck
from .player import Player
from .properties import OwnableSpace, Utility
from .rules import Rules
from .spaces import Space


@dataclass
class TurnResult:
    """Regroupe toutes les informations produites par l'exécution d'un tour.

    Entrées:
        turn_number (int): Numéro global du tour exécuté.
        player (Player): Joueur qui vient de jouer.
        dice (tuple[int, int]): Valeurs obtenues sur les deux dés.
        passed_go (bool): Indique si Départ a été franchi pendant le tour,
            y compris à cause d'une carte.
        landed_space_name (str): Nom de la case finale réelle du joueur.
        message (str): Description textuelle de l'effet du tour.
        rolled_double (bool): Indique si les deux dés avaient la même valeur.

    Sortie:
        TurnResult: Objet exploitable par une interface, une simulation ou des statistiques.
    """

    turn_number: int
    player: Player
    dice: tuple[int, int]
    passed_go: bool
    landed_space_name: str
    message: str
    rolled_double: bool


class Game:
    """Orchestre l'état global et le déroulement d'une partie de Monopoly.

    Entrées:
        player_names (list[str]): Noms des joueurs à créer. Deux joueurs minimum.
        seed (int | None): Graine optionnelle pour rendre les lancers reproductibles.
        board (Board | None): Plateau personnalisé ou ``None`` pour le plateau standard.

    Sortie:
        Game: Partie initialisée avec joueurs, règles, plateau et paquets mélangés.
    """

    def __init__(
        self,
        player_names: list[str],
        seed: int | None = None,
        board: Board | None = None,
    ) -> None:
        """Initialise une nouvelle partie et ses composants principaux.

        Entrées:
            player_names (list[str]): Noms des joueurs dans l'ordre de jeu initial.
            seed (int | None): Graine du générateur aléatoire, utile pour les tests.
            board (Board | None): Plateau à utiliser ou ``None`` pour le standard.

        Sortie:
            None: Le constructeur prépare tous les composants de la partie.

        Lève:
            ValueError: Si moins de deux noms de joueurs sont fournis.
        """
        if len(player_names) < 2:
            raise ValueError("Il faut au moins 2 joueurs.")

        self.random = random.Random(seed)
        self.board = board or Board.standard()
        self.players = [Player(player_id=i, name=name) for i, name in enumerate(player_names)]
        self.rules = Rules(self)
        self.chance_deck = create_chance_deck(self.random)
        self.community_chest_deck = create_community_chest_deck(self.random)
        self.current_player_index = 0
        self.turn_number = 0
        self.consecutive_doubles = 0
        self._turn_passed_go = False
        self.drawn_cards_this_turn: list[DrawnCardEvent] = []

    @property
    def current_player(self) -> Player:
        """Retourne le joueur dont c'est actuellement le tour.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            Player: Joueur pointé par ``current_player_index``.
        """
        return self.players[self.current_player_index]

    @property
    def active_players(self) -> list[Player]:
        """Liste les joueurs qui ne sont pas encore en faillite.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            list[Player]: Joueurs encore actifs dans la partie.
        """
        return [player for player in self.players if not player.bankrupt]

    @property
    def is_over(self) -> bool:
        """Indique si la partie est terminée faute d'au moins deux joueurs actifs.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            bool: ``True`` lorsqu'il reste au maximum un joueur non failli.
        """
        return len(self.active_players) <= 1

    @property
    def winner(self) -> Player | None:
        """Retourne le vainqueur lorsque la partie est terminée.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            Player | None: Dernier joueur actif si la partie est finie, sinon ``None``.
        """
        active = self.active_players
        return active[0] if self.is_over and active else None

    def roll_dice(self) -> tuple[int, int]:
        """Lance les deux dés avec le générateur aléatoire interne.

        Entrées:
            Aucune.

        Sortie:
            tuple[int, int]: Deux entiers compris entre 1 et 6 inclus.
        """
        return self.random.randint(1, 6), self.random.randint(1, 6)

    def get_current_space(self, player: Player | None = None) -> Space | OwnableSpace:
        """Retourne la case occupée par un joueur ou par le joueur courant.

        Entrées:
            player (Player | None): Joueur à consulter. ``None`` utilise le joueur courant.

        Sortie:
            Space | OwnableSpace: Case actuellement occupée par le joueur choisi.
        """
        player = player or self.current_player
        return self.board.get_player_space(player)

    def buy_current_property(self, player: Player) -> bool:
        """Tente d'acheter la case sur laquelle se trouve un joueur.

        Entrées:
            player (Player): Joueur qui souhaite acheter sa case actuelle.

        Sortie:
            bool: ``True`` si la case est achetable et que l'achat réussit.
        """
        space = self.board.get_player_space(player)
        if not isinstance(space, OwnableSpace):
            return False
        return self.rules.buy_property(player, space)

    def start_auction(self, space: OwnableSpace) -> Auction:
        """Crée une enchère pour un bien encore libre.

        Entrées:
            space (OwnableSpace): Bien refusé à l'achat direct et mis aux enchères.

        Sortie:
            Auction: Enchère contenant tous les joueurs actifs comme participants.
        """
        return Auction(space, self.active_players)

    @staticmethod
    def combine_messages(*parts: str) -> str:
        """Assemble plusieurs morceaux de message en ignorant les chaînes vides.

        Entrées:
            *parts (str): Fragments textuels à concaténer dans l'ordre.

        Sortie:
            str: Fragments non vides séparés par un espace.
        """
        return " ".join(part.strip() for part in parts if part and part.strip())

    def return_card_to_deck(self, card: Card) -> None:
        """Replace une carte conservée dans son paquet d'origine.

        Entrées:
            card (Card): Carte à rendre. Elle doit exposer un ``deck_name`` connu.

        Sortie:
            None: La carte est replacée en fin du paquet correspondant.

        Lève:
            ValueError: Si le paquet d'origine de la carte est inconnu.
        """
        deck_name = getattr(card, "deck_name", None)
        if deck_name == "chance":
            self.chance_deck.return_card(card)
        elif deck_name == "community_chest":
            self.community_chest_deck.return_card(card)
        else:
            raise ValueError("Impossible de déterminer le paquet d'origine de cette carte.")

    def use_get_out_of_jail_card(self, player: Player) -> bool:
        """Utilise la première carte de sortie de prison détenue par un joueur.

        Entrées:
            player (Player): Joueur emprisonné souhaitant utiliser une carte.

        Sortie:
            bool: ``True`` si une carte a été trouvée, rendue au paquet et utilisée.
        """
        if not player.in_jail:
            return False

        for card in list(player.held_cards):
            if isinstance(card, GetOutOfJailCard):
                player.remove_held_card(card)
                self.return_card_to_deck(card)
                self.rules.release_from_jail(player)
                return True
        return False

    def move_to_and_resolve(
        self,
        player: Player,
        destination: int,
        collect_go: bool = True,
        dice_total: int = 0,
        rent_multiplier: int = 1,
        utility_multiplier: int | None = None,
    ) -> str:
        """Déplace un joueur vers une case absolue puis applique l'effet de cette case.

        Entrées:
            player (Player): Joueur à déplacer.
            destination (int): Index exact de la case d'arrivée.
            collect_go (bool): Autorise le salaire au passage par Départ.
            dice_total (int): Valeur de dés utilisée pour un loyer de compagnie.
            rent_multiplier (int): Multiplicateur supplémentaire de loyer.
            utility_multiplier (int | None): Multiplicateur forcé pour une compagnie.

        Sortie:
            str: Message généré par la case d'arrivée.
        """
        passed_go = self.rules.move_player_to(player, destination, collect_go)
        self._turn_passed_go = self._turn_passed_go or passed_go
        return self.resolve_current_space(
            player,
            dice_total=dice_total,
            rent_multiplier=rent_multiplier,
            utility_multiplier=utility_multiplier,
        )

    def move_backward_and_resolve(self, player: Player, steps: int) -> str:
        """Fait reculer un joueur puis applique l'effet de sa nouvelle case.

        Entrées:
            player (Player): Joueur à faire reculer.
            steps (int): Nombre positif de cases à reculer.

        Sortie:
            str: Message généré par la case d'arrivée.
        """
        self.rules.move_player_backward(player, steps)
        return self.resolve_current_space(player, dice_total=0)

    def resolve_current_space(
        self,
        player: Player,
        dice_total: int,
        rent_multiplier: int = 1,
        utility_multiplier: int | None = None,
    ) -> str:
        """Résout la case actuellement occupée par un joueur.

        Entrées:
            player (Player): Joueur dont la case doit être résolue.
            dice_total (int): Somme des dés utile pour les compagnies.
            rent_multiplier (int): Multiplicateur exceptionnel du loyer calculé.
            utility_multiplier (int | None): Multiplicateur forcé pour une compagnie.

        Sortie:
            str: Description de l'effet appliqué au joueur.
        """
        space = self.board.get_player_space(player)
        return self._resolve_space(
            player,
            space,
            dice_total,
            rent_multiplier=rent_multiplier,
            utility_multiplier=utility_multiplier,
        )

    def take_turn(self, jail_action: str = "roll") -> TurnResult:
        """Exécute un tour complet du joueur courant.

        Entrées:
            jail_action (str): Si le joueur commence en prison : ``"roll"`` pour
                tenter un double, ``"pay"`` pour payer 50 avant le lancer, ou
                ``"card"`` pour utiliser une carte de sortie de prison.

        Sortie:
            TurnResult: Résumé structuré du lancer, des déplacements et des effets.

        Lève:
            RuntimeError: Si la partie est déjà terminée.
            ValueError: Si l'action de prison est inconnue ou impossible.
        """
        if self.is_over:
            raise RuntimeError("La partie est terminée.")

        self.turn_number += 1
        self._turn_passed_go = False
        self.drawn_cards_this_turn = []
        player = self.current_player

        if player.in_jail:
            return self._take_jail_turn(player, jail_action)
        return self._take_free_turn(player)

    def _take_free_turn(self, player: Player) -> TurnResult:
        """Exécute un lancer normal pour un joueur qui n'est pas emprisonné.

        Entrées:
            player (Player): Joueur libre qui doit lancer les dés et avancer.

        Sortie:
            TurnResult: Résultat complet du lancer normal.
        """
        d1, d2 = self.roll_dice()
        dice_total = d1 + d2
        rolled_double = d1 == d2

        if rolled_double:
            self.consecutive_doubles += 1
        else:
            self.consecutive_doubles = 0

        if self.consecutive_doubles >= 3:
            self.rules.send_to_jail(player)
            self.consecutive_doubles = 0
            result = self._make_turn_result(
                player,
                (d1, d2),
                rolled_double=True,
                message=f"{player.name} a fait trois doubles et va en prison.",
            )
            self._advance_turn()
            return result

        passed_go = self.rules.move_player(player, dice_total)
        self._turn_passed_go = self._turn_passed_go or passed_go
        message = self.resolve_current_space(player, dice_total)
        result = self._make_turn_result(player, (d1, d2), rolled_double, message)

        if player.in_jail or player.bankrupt or not rolled_double:
            self.consecutive_doubles = 0
            self._advance_turn()

        return result

    def _take_jail_turn(self, player: Player, jail_action: str) -> TurnResult:
        """Exécute la logique particulière d'un tour commencé en prison.

        Entrées:
            player (Player): Joueur actuellement emprisonné.
            jail_action (str): ``"roll"``, ``"pay"`` ou ``"card"``.

        Sortie:
            TurnResult: Résultat de la tentative de sortie et du déplacement éventuel.

        Lève:
            ValueError: Si l'action demandée est inconnue ou impossible.
        """
        if jail_action not in {"roll", "pay", "card"}:
            raise ValueError("jail_action doit valoir 'roll', 'pay' ou 'card'.")

        if jail_action == "pay":
            if not self.rules.pay_jail_fine(player):
                raise ValueError("Le joueur ne peut pas payer l'amende de prison.")
            return self._take_free_turn(player)

        if jail_action == "card":
            if not self.use_get_out_of_jail_card(player):
                raise ValueError("Le joueur ne possède pas de carte de sortie de prison.")
            return self._take_free_turn(player)

        d1, d2 = self.roll_dice()
        dice_total = d1 + d2
        rolled_double = d1 == d2

        if rolled_double:
            self.rules.release_from_jail(player)
            passed_go = self.rules.move_player(player, dice_total)
            self._turn_passed_go = self._turn_passed_go or passed_go
            effect = self.resolve_current_space(player, dice_total)
            message = self.combine_messages(
                f"{player.name} fait un double et sort de prison.",
                effect,
            )
            result = self._make_turn_result(player, (d1, d2), True, message)
            self.consecutive_doubles = 0
            self._advance_turn()
            return result

        player.jail_turns += 1
        if player.jail_turns < self.rules.MAX_JAIL_TURNS:
            result = self._make_turn_result(
                player,
                (d1, d2),
                False,
                f"{player.name} reste en prison ({player.jail_turns}/{self.rules.MAX_JAIL_TURNS}).",
            )
            self._advance_turn()
            return result

        self.rules.pay_bank(player, self.rules.JAIL_FINE)
        if player.bankrupt:
            result = self._make_turn_result(
                player,
                (d1, d2),
                False,
                f"{player.name} ne peut pas payer l'amende obligatoire et fait faillite.",
            )
            self._advance_turn()
            return result

        self.rules.release_from_jail(player)
        passed_go = self.rules.move_player(player, dice_total)
        self._turn_passed_go = self._turn_passed_go or passed_go
        effect = self.resolve_current_space(player, dice_total)
        message = self.combine_messages(
            f"{player.name} paie {self.rules.JAIL_FINE} après sa troisième tentative et sort de prison.",
            effect,
        )
        result = self._make_turn_result(player, (d1, d2), False, message)
        self._advance_turn()
        return result

    def _make_turn_result(
        self,
        player: Player,
        dice: tuple[int, int],
        rolled_double: bool,
        message: str,
    ) -> TurnResult:
        """Construit un résultat de tour à partir de l'état final réel du joueur.

        Entrées:
            player (Player): Joueur venant de terminer son action.
            dice (tuple[int, int]): Dés utilisés pour le tour.
            rolled_double (bool): Indique si le lancer principal était un double.
            message (str): Description cumulée des effets du tour.

        Sortie:
            TurnResult: Résultat dont la case correspond à la position finale du joueur.
        """
        final_space = self.board.get_player_space(player)
        return TurnResult(
            turn_number=self.turn_number,
            player=player,
            dice=dice,
            passed_go=self._turn_passed_go,
            landed_space_name=final_space.name,
            message=message,
            rolled_double=rolled_double,
        )

    def _resolve_space(
        self,
        player: Player,
        space: Space | OwnableSpace,
        dice_total: int,
        rent_multiplier: int = 1,
        utility_multiplier: int | None = None,
    ) -> str:
        """Applique le comportement concret d'une case au joueur qui vient d'y arriver.

        Entrées:
            player (Player): Joueur arrivé sur la case.
            space (Space | OwnableSpace): Case à résoudre.
            dice_total (int): Somme des dés du déplacement pertinent.
            rent_multiplier (int): Multiplicateur exceptionnel du loyer normal.
            utility_multiplier (int | None): Multiplicateur forcé pour une compagnie.

        Sortie:
            str: Message décrivant l'achat possible, le loyer ou l'effet spécial.
        """
        if isinstance(space, OwnableSpace):
            if space.owner is None:
                return f"{space.name} est disponible à l'achat pour {space.price}."
            if space.owner is player:
                return f"{space.name} appartient déjà à {player.name}."
            if space.mortgaged:
                return f"{space.name} est hypothéquée : aucun loyer."

            if isinstance(space, Utility) and utility_multiplier is not None:
                rent = dice_total * utility_multiplier
            else:
                rent = self.rules.calculate_rent(space, dice_total) * rent_multiplier

            owner = space.owner
            self.rules.transfer_money(player, owner, rent)
            return f"{player.name} paie {rent} de loyer à {owner.name}."

        return space.land(self, player, dice_total)

    def _advance_turn(self) -> None:
        """Passe au prochain joueur actif dans l'ordre de la table.

        Entrées:
            Aucune autre que l'état courant de la partie.

        Sortie:
            None: ``current_player_index`` est déplacé vers le prochain joueur non failli.
        """
        if self.is_over:
            return
        for _ in range(len(self.players)):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if not self.current_player.bankrupt:
                return
