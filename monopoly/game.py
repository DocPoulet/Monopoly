"""Orchestre une partie complète : joueurs, tours, dés, cartes et résolution des cases."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from .auction import Auction
from .bank import Bank
from .building_auction import BuildingAuction, BuildingType
from .board import Board
from .cards import Card, DrawnCardEvent, GetOutOfJailCard, create_chance_deck, create_community_chest_deck
from .player import Player
from .properties import OwnableSpace, Property, Utility
from .rules import Rules
from .history import GameHistory
from .options import GameOptions
from .debt import DebtManagementResult
from .trade import TradeOffer
from .spaces import Space


@dataclass
class TurnResult:
    """Regroupe toutes les informations produites par l'exécution d'un tour.

    Entrées:
        turn_number (int): Numéro du tour de table auquel appartient cette action.
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


@dataclass
class PendingRentClaim:
    """Décrit un loyer calculé mais non encore réclamé en mode manuel.

    Entrées:
        payer (Player): Joueur ayant atterri sur le bien.
        recipient (Player): Propriétaire pouvant réclamer le loyer.
        amount (int): Montant du loyer calculé.
        property_index (int): Index du bien concerné.

    Sortie:
        PendingRentClaim: Décision de loyer différée jusqu'à l'action du propriétaire.
    """

    payer: Player
    recipient: Player
    amount: int
    property_index: int


class Game:
    """Orchestre l'état global et le déroulement d'une partie de Monopoly.

    Entrées:
        player_names (list[str]): Noms des joueurs à créer. Deux joueurs minimum.
        seed (int | None): Graine optionnelle pour rendre les lancers reproductibles.
        board (Board | None): Plateau personnalisé ou ``None`` pour le plateau standard.
        options (GameOptions | None): Variantes de partie ; ``None`` utilise les règles classiques.

    Sortie:
        Game: Partie initialisée avec joueurs, règles, plateau et paquets mélangés.
    """

    def __init__(
        self,
        player_names: list[str],
        seed: int | None = None,
        board: Board | None = None,
        options: GameOptions | None = None,
    ) -> None:
        """Initialise une nouvelle partie et ses composants principaux.

        Entrées:
            player_names (list[str]): Noms des joueurs dans l'ordre de jeu initial.
            seed (int | None): Graine du générateur aléatoire, utile pour les tests.
            board (Board | None): Plateau à utiliser ou ``None`` pour le standard.
            options (GameOptions | None): Options configurables de la partie.

        Sortie:
            None: Le constructeur prépare tous les composants de la partie.

        Lève:
            ValueError: Si moins de deux noms de joueurs sont fournis.
        """
        if len(player_names) < 2:
            raise ValueError("Il faut au moins 2 joueurs.")

        self.random = random.Random(seed)
        self.board = board or Board.standard()
        self.options = options or GameOptions()
        self.options.validate()
        self._apply_property_price_percent()
        self.players = [
            Player(
                player_id=i,
                name=name,
                cash=self.options.starting_cash,
            )
            for i, name in enumerate(player_names)
        ]
        self.bank = Bank(
            house_limit=self.options.house_stock,
            hotel_limit=self.options.hotel_stock,
        )
        self.free_parking_pot = 0
        self._card_resolution_depth = 0
        self.pending_rent_claim: PendingRentClaim | None = None
        self._landing_build_context: tuple[int, int] | None = None
        self.rules = Rules(self)
        self.chance_deck = create_chance_deck(self.random)
        self.community_chest_deck = create_community_chest_deck(self.random)
        self.current_player_index = 0
        self.turn_number = 1
        self.completed_rounds = 0
        self._new_round_pending = False
        self.consecutive_doubles = 0
        self._turn_passed_go = False
        self.drawn_cards_this_turn: list[DrawnCardEvent] = []
        self.financial_events_this_turn: list[str] = []
        self.pending_bank_auctions: list[OwnableSpace] = []
        self.history = GameHistory()
        self.mortgage_selector: Callable[
            [Player, list[OwnableSpace], int], list[OwnableSpace]
        ] | None = None
        self.debt_manager: Callable[
            [Player, int, Player | None], DebtManagementResult | bool
        ] | None = None
        self.received_mortgage_selector: Callable[
            [Player, list[OwnableSpace]], list[OwnableSpace]
        ] | None = None


    def _apply_property_price_percent(self) -> None:
        """Applique le pourcentage de prix configuré aux biens achetables du plateau.

        Entrées:
            Aucune.

        Sortie:
            None: Les prix affichés, d'achat et hypothécaires utilisent la valeur ajustée.
        """
        for space in self.board.spaces:
            if not isinstance(space, OwnableSpace):
                continue
            if not hasattr(space, "_base_price"):
                setattr(space, "_base_price", space.price)
            base_price = int(getattr(space, "_base_price"))
            space.price = max(1, round(base_price * self.options.property_price_percent / 100))

    def begin_card_resolution(self) -> None:
        """Marque le début de l'application d'une carte Chance ou Caisse de communauté.

        Entrées:
            Aucune.

        Sortie:
            None: Les paiements bancaires imbriqués peuvent alimenter la cagnotte.
        """
        self._card_resolution_depth += 1

    def end_card_resolution(self) -> None:
        """Marque la fin de l'application d'une carte.

        Entrées:
            Aucune.

        Sortie:
            None: Le contexte de paiement de carte est décrémenté sans devenir négatif.
        """
        self._card_resolution_depth = max(0, self._card_resolution_depth - 1)

    @property
    def card_resolution_active(self) -> bool:
        """Indique si un effet de carte est actuellement en cours de résolution.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` pendant l'application directe ou indirecte d'une carte.
        """
        return self._card_resolution_depth > 0

    def add_to_free_parking_pot(self, amount: int, payer: Player | None = None) -> None:
        """Ajoute un paiement bancaire de carte à la cagnotte du Parc Gratuit.

        Entrées:
            amount (int): Montant effectivement payé à la banque.
            payer (Player | None): Joueur ayant alimenté la cagnotte.

        Sortie:
            None: La cagnotte est augmentée uniquement si la variante est active.
        """
        if amount <= 0 or not self.options.free_parking_card_pot:
            return
        self.free_parking_pot += amount
        self.record_event(
            "free_parking_pot_add",
            f"La cagnotte du Parc Gratuit reçoit {amount} $.",
            payer,
            amount=amount,
            pot=self.free_parking_pot,
        )

    def collect_free_parking_pot(self, player: Player) -> int:
        """Verse et réinitialise la cagnotte du Parc Gratuit.

        Entrées:
            player (Player): Joueur arrivé sur Parc Gratuit.

        Sortie:
            int: Montant récupéré, éventuellement nul.
        """
        if not self.options.free_parking_card_pot or self.free_parking_pot <= 0:
            return 0
        amount = self.free_parking_pot
        self.free_parking_pot = 0
        player.receive(amount)
        self.record_event(
            "free_parking_pot_collect",
            f"{player.name} récupère {amount} $ de cagnotte au Parc Gratuit.",
            player,
            amount=amount,
        )
        return amount

    def claim_pending_rent(self) -> bool:
        """Réclame le loyer manuel actuellement en attente.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsqu'un loyer en attente a été traité.
        """
        claim = self.pending_rent_claim
        if claim is None:
            return False
        self.pending_rent_claim = None
        self.rules.transfer_money(claim.payer, claim.recipient, claim.amount)
        self.record_event(
            "rent",
            f"{claim.payer.name} paie {claim.amount} $ de loyer à {claim.recipient.name}.",
            claim.payer,
            amount=claim.amount,
            recipient_id=claim.recipient.player_id,
            property_index=claim.property_index,
            manual=True,
        )
        return True

    def waive_pending_rent(self) -> bool:
        """Renonce au loyer manuel actuellement en attente.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsqu'une demande de loyer a été abandonnée.
        """
        claim = self.pending_rent_claim
        if claim is None:
            return False
        self.pending_rent_claim = None
        self.record_event(
            "rent_waived",
            f"{claim.recipient.name} renonce au loyer de {claim.amount} $ dû par {claim.payer.name}.",
            claim.recipient,
            amount=claim.amount,
            payer_id=claim.payer.player_id,
            property_index=claim.property_index,
        )
        return True

    def record_event(
        self,
        event_type: str,
        message: str,
        player: Player | None = None,
        **data: object,
    ) -> None:
        """Enregistre un événement structuré dans l'historique de la partie.

        Entrées:
            event_type (str): Catégorie stable de l'événement.
            message (str): Description lisible.
            player (Player | None): Joueur principal concerné.
            **data (object): Données complémentaires destinées aux statistiques.

        Sortie:
            None: Un nouvel événement est ajouté à ``history``.
        """
        self.history.add(
            self.turn_number,
            event_type,
            message,
            player,
            **data,
        )

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
    def upcoming_turn_number(self) -> int:
        """Retourne le numéro qui sera affiché pour le prochain joueur à agir.

        Entrées:
            Aucune.

        Sortie:
            int: Tour courant, ou tour suivant lorsqu'un tour de table vient de se terminer.
        """
        if self._new_round_pending and not self.reached_turn_limit:
            return self.turn_number + 1
        return self.turn_number

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
    def reached_turn_limit(self) -> bool:
        """Indique si la limite optionnelle de tours a été atteinte.

        Entrées:
            Aucune.

        Sortie:
            bool: ``True`` lorsque la partie possède une limite positive déjà atteinte.
        """
        return (
            self.options.turn_limit > 0
            and self.completed_rounds >= self.options.turn_limit
        )

    @property
    def is_over(self) -> bool:
        """Indique si la partie est terminée par faillites ou limite de tours.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            bool: ``True`` lorsqu'il reste au maximum un joueur actif ou que la
            limite de tours configurée est atteinte.
        """
        return len(self.active_players) <= 1 or self.reached_turn_limit

    def player_net_worth(self, player: Player) -> int:
        """Estime la valeur totale d'un joueur pour une fin à durée limitée.

        Entrées:
            player (Player): Joueur à valoriser.

        Sortie:
            int: Argent liquide, valeur des biens et coût payé des bâtiments.
        """
        if player.bankrupt:
            return 0

        total = player.cash
        for space in player.properties:
            total += space.mortgage_value if space.mortgaged else space.price
            if hasattr(space, "houses") and hasattr(space, "house_cost"):
                total += int(getattr(space, "houses", 0)) * int(space.house_cost)
                if bool(getattr(space, "hotel", False)):
                    total += 5 * int(space.house_cost)
        return total

    @property
    def winner(self) -> Player | None:
        """Retourne le vainqueur selon faillite classique ou valeur à la limite de tours.

        Entrées:
            Aucune autre que l'état courant.

        Sortie:
            Player | None: Dernier joueur actif ou joueur actif ayant la plus grande valeur.
        """
        active = self.active_players
        if not self.is_over or not active:
            return None
        if len(active) == 1:
            return active[0]
        if self.reached_turn_limit:
            return max(
                active,
                key=lambda player: (
                    self.player_net_worth(player),
                    player.cash,
                    -player.player_id,
                ),
            )
        return None

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

    def eligible_building_bidders(self, building_type: BuildingType) -> list[Player]:
        """Retourne les joueurs actifs ayant au moins un terrain éligible au bâtiment.

        Entrées:
            building_type (BuildingType): ``house`` ou ``hotel``.

        Sortie:
            list[Player]: Joueurs pouvant légalement placer ce type de bâtiment.
        """
        if building_type == "house":
            target_getter = self.rules.eligible_house_targets
        elif building_type == "hotel":
            target_getter = self.rules.eligible_hotel_targets
        else:
            raise ValueError("Le type de bâtiment doit être 'house' ou 'hotel'.")

        return [
            player
            for player in self.active_players
            if player.cash > 0 and bool(target_getter(player))
        ]

    def building_stock(self, building_type: BuildingType) -> int:
        """Retourne le stock bancaire du type de bâtiment demandé.

        Entrées:
            building_type (BuildingType): ``house`` ou ``hotel``.

        Sortie:
            int: Nombre d'unités encore disponibles.

        Lève:
            ValueError: Si le type de bâtiment est inconnu.
        """
        if building_type == "house":
            return self.bank.houses_available
        if building_type == "hotel":
            return self.bank.hotels_available
        raise ValueError("Le type de bâtiment doit être 'house' ou 'hotel'.")

    def building_shortage_requires_auction(self, building_type: BuildingType) -> bool:
        """Détecte une pénurie où le stock est inférieur au nombre de joueurs éligibles.

        Entrées:
            building_type (BuildingType): Type de bâtiment demandé.

        Sortie:
            bool: ``True`` lorsqu'au moins deux joueurs peuvent construire et que
            le stock positif est insuffisant pour leur fournir une unité chacun.

        Notes:
            L'interface utilise cette situation pour demander réellement aux joueurs
            s'ils souhaitent participer. Ceux qui ne veulent pas acheter peuvent abandonner.
        """
        if building_type == "house" and self.bank.houses_unlimited:
            return False
        if building_type == "hotel" and self.bank.hotels_unlimited:
            return False
        stock = self.building_stock(building_type)
        eligible = self.eligible_building_bidders(building_type)
        return stock > 0 and len(eligible) >= 2 and stock < len(eligible)

    def start_building_auction(self, building_type: BuildingType) -> BuildingAuction:
        """Crée une enchère pour une maison ou un hôtel en stock limité.

        Entrées:
            building_type (BuildingType): Type mis aux enchères.

        Sortie:
            BuildingAuction: Enchère contenant tous les joueurs actifs éligibles.

        Lève:
            ValueError: Si le stock est nul ou si moins de deux joueurs sont éligibles.
        """
        bidders = self.eligible_building_bidders(building_type)
        if self.building_stock(building_type) <= 0:
            raise ValueError("La banque ne possède plus ce type de bâtiment.")
        if len(bidders) < 2:
            raise ValueError("Il faut au moins deux joueurs éligibles pour cette enchère.")
        return BuildingAuction(self, building_type, bidders)

    def queue_bank_auction(self, space: OwnableSpace) -> None:
        """Ajoute un bien rendu à la banque à la file d'enchères obligatoires.

        Entrées:
            space (OwnableSpace): Bien libre devant être revendu aux joueurs actifs.

        Sortie:
            None: Le bien est ajouté une seule fois à la file d'attente.
        """
        if space.owner is not None:
            raise ValueError("Un bien possédé ne peut pas être mis dans la file de la banque.")
        if space not in self.pending_bank_auctions:
            self.pending_bank_auctions.append(space)

    def pop_next_bank_auction(self) -> OwnableSpace | None:
        """Retire et retourne le prochain bien devant être mis aux enchères.

        Entrées:
            Aucune.

        Sortie:
            OwnableSpace | None: Premier bien en attente, ou ``None`` si la file est vide.
        """
        if not self.pending_bank_auctions:
            return None
        return self.pending_bank_auctions.pop(0)


    def set_landing_build_context(
        self,
        player: Player,
        property_: Property,
    ) -> None:
        """Autorise temporairement la construction liée à un atterrissage précis.

        Entrées:
            player (Player): Joueur qui vient réellement d'atterrir sur le terrain.
            property_ (Property): Terrain correspondant à la case d'arrivée.

        Sortie:
            None: Le couple joueur/terrain devient l'unique contexte de construction
            lorsque la variante ``construction_anywhere`` est désactivée.
        """
        self._landing_build_context = (player.player_id, property_.index)

    def clear_landing_build_context(self) -> None:
        """Supprime le droit temporaire de construire issu d'un atterrissage.

        Entrées:
            Aucune.

        Sortie:
            None: Aucun terrain n'est considéré comme fraîchement atteint.
        """
        self._landing_build_context = None

    def can_build_from_landing(
        self,
        player: Player,
        property_: Property,
    ) -> bool:
        """Vérifie qu'un joueur vient effectivement d'atterrir sur le terrain.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` uniquement pour le contexte d'atterrissage encore actif.
        """
        return self._landing_build_context == (player.player_id, property_.index)

    def set_debt_manager(
        self,
        manager: Callable[..., DebtManagementResult | bool] | None,
    ) -> None:
        """Configure le gestionnaire humain utilisé pour résoudre une dette.

        Entrées:
            manager (Callable | None): Fonction recevant au minimum le joueur et le
                montant dû. Les gestionnaires V16.2 peuvent aussi recevoir le créancier.

        Sortie:
            None: Le callback est mémorisé ; ``None`` restaure l'automatisation.
        """
        self.debt_manager = manager

    def manage_debt(
        self,
        player: Player,
        amount_due: int,
        creditor: Player | None = None,
    ) -> DebtManagementResult | None:
        """Appelle le gestionnaire de dette tout en restant compatible avec l'ancienne API.

        Entrées:
            player (Player): Joueur devant payer.
            amount_due (int): Montant total de la dette.
            creditor (Player | None): Joueur créancier, ou ``None`` pour la banque.

        Sortie:
            DebtManagementResult | None: Résultat structuré, ou ``None`` sans gestionnaire.
        """
        if self.debt_manager is None:
            return None

        import inspect

        parameters = inspect.signature(self.debt_manager).parameters
        if len(parameters) >= 3:
            raw_result = self.debt_manager(player, amount_due, creditor)
        else:
            raw_result = self.debt_manager(player, amount_due)

        if isinstance(raw_result, DebtManagementResult):
            return raw_result
        return DebtManagementResult(bool(raw_result), 0, False)

    def set_received_mortgage_selector(
        self,
        selector: Callable[[Player, list[OwnableSpace]], list[OwnableSpace]] | None,
    ) -> None:
        """Configure le choix de déshypothèque immédiate après réception d'un bien.

        Entrées:
            selector (Callable | None): Fonction retournant les biens que le nouveau
                propriétaire souhaite déshypothéquer immédiatement.

        Sortie:
            None: Le sélecteur est enregistré pour échanges et faillites.
        """
        self.received_mortgage_selector = selector

    def choose_received_mortgages_to_lift(
        self,
        player: Player,
        spaces: list[OwnableSpace],
    ) -> list[OwnableSpace]:
        """Choisit les hypothèques reçues qui seront levées immédiatement.

        Entrées:
            player (Player): Nouveau propriétaire.
            spaces (list[OwnableSpace]): Biens hypothéqués tout juste reçus.

        Sortie:
            list[OwnableSpace]: Sous-ensemble choisi ; vide sans interface.
        """
        if not spaces or self.received_mortgage_selector is None:
            return []

        chosen = self.received_mortgage_selector(player, list(spaces))
        allowed = {id(space): space for space in spaces}
        unique: list[OwnableSpace] = []
        seen: set[int] = set()
        for space in chosen:
            key = id(space)
            if key in allowed and key not in seen:
                unique.append(allowed[key])
                seen.add(key)
        return unique


    def settle_received_mortgages(
        self,
        player: Player,
        spaces: list[OwnableSpace],
    ) -> None:
        """Applique la règle choisie aux hypothèques reçues lors d'un transfert.

        Entrées:
            player (Player): Nouveau propriétaire.
            spaces (list[OwnableSpace]): Biens hypothéqués tout juste reçus.

        Sortie:
            None: Les hypothèques suivent le bien avec frais, ou sont annulées gratuitement
            lorsque la règle ``transferred_mortgages`` est désactivée.
        """
        mortgaged = [space for space in spaces if space.mortgaged]
        if not mortgaged or player.bankrupt:
            return

        if not self.options.transferred_mortgages:
            for space in mortgaged:
                space.mortgaged = False
                self.record_event(
                    "mortgage_transfer_cleared",
                    f"L'hypothèque de {space.name} est annulée lors du transfert.",
                    player,
                    property_index=space.index,
                )
            return

        chosen = {
            id(space)
            for space in self.choose_received_mortgages_to_lift(player, mortgaged)
        }

        for space in mortgaged:
            interest = self.rules.mortgage_interest(space)
            if id(space) in chosen:
                total = space.mortgage_value + interest
                self.record_financial_event(
                    f"{player.name} choisit de lever immédiatement l'hypothèque de "
                    f"{space.name} pour {total} $."
                )
                self.rules.pay_bank(player, total)
                if not player.bankrupt:
                    space.mortgaged = False
                    self.record_event(
                        "unmortgage",
                        f"{player.name} lève immédiatement l'hypothèque de {space.name}.",
                        player,
                        property_index=space.index,
                        amount=total,
                        received_transfer=True,
                    )
            else:
                self.record_financial_event(
                    f"{player.name} paie {interest} $ d'intérêts pour conserver "
                    f"{space.name} hypothéquée."
                )
                self.rules.pay_bank(player, interest)

            if player.bankrupt:
                break

    def set_mortgage_selector(
        self,
        selector: Callable[[Player, list[OwnableSpace], int], list[OwnableSpace]] | None,
    ) -> None:
        """Configure le mécanisme utilisé pour choisir des hypothèques en cas de dette.

        Entrées:
            selector (Callable | None): Fonction recevant le joueur, les biens
                hypothécables et le montant de liquidités à atteindre. ``None`` restaure
                le comportement automatique prévu pour les simulations.

        Sortie:
            None: Le sélecteur est conservé par la partie.
        """
        self.mortgage_selector = selector

    def choose_mortgages_for_debt(
        self,
        player: Player,
        mortgageable: list[OwnableSpace],
        target_cash: int,
    ) -> list[OwnableSpace]:
        """Choisit les biens à hypothéquer pour atteindre un montant de liquidités.

        Entrées:
            player (Player): Joueur devant réunir de l'argent.
            mortgageable (list[OwnableSpace]): Biens actuellement autorisés à l'hypothèque.
            target_cash (int): Solde liquide minimum à atteindre pour régler la dette.

        Sortie:
            list[OwnableSpace]: Biens choisis par l'interface ou, sans interface,
            sélection automatique privilégiant les valeurs hypothécaires les plus élevées.
        """
        if self.mortgage_selector is not None:
            selected = self.mortgage_selector(
                player,
                list(mortgageable),
                target_cash,
            )
            allowed_ids = {id(space) for space in mortgageable}
            unique: list[OwnableSpace] = []
            seen: set[int] = set()

            for space in selected:
                space_id = id(space)
                if space_id in allowed_ids and space_id not in seen:
                    unique.append(space)
                    seen.add(space_id)

            return unique

        needed = max(0, target_cash - player.cash)
        selected: list[OwnableSpace] = []
        total = 0

        for space in sorted(
            mortgageable,
            key=lambda item: (item.mortgage_value, -item.index),
            reverse=True,
        ):
            selected.append(space)
            total += space.mortgage_value
            if total >= needed:
                break

        return selected

    def create_trade(self, initiator: Player, recipient: Player) -> TradeOffer:
        """Crée une proposition d'échange vide entre deux joueurs actifs.

        Entrées:
            initiator (Player): Joueur qui ouvre l'échange.
            recipient (Player): Joueur sélectionné comme partenaire.

        Sortie:
            TradeOffer: Offre vide à compléter puis valider/exécuter.

        Lève:
            ValueError: Si les joueurs sont identiques, en faillite ou hors de la partie.
        """
        if initiator is recipient:
            raise ValueError("Un joueur ne peut pas échanger avec lui-même.")
        if initiator not in self.players or recipient not in self.players:
            raise ValueError("Les deux joueurs doivent appartenir à la partie.")
        if initiator.bankrupt or recipient.bankrupt:
            raise ValueError("Un joueur en faillite ne peut pas échanger.")
        return TradeOffer(self, initiator, recipient)

    def record_financial_event(self, message: str) -> None:
        """Ajoute un événement financier au tour courant et à l'historique.

        Entrées:
            message (str): Description d'une vente, hypothèque ou autre opération.

        Sortie:
            None: Le message est ajouté aux événements financiers et au journal structuré.
        """
        if message.strip():
            cleaned = message.strip()
            self.financial_events_this_turn.append(cleaned)
            self.record_event("financial", cleaned)

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

        self.clear_landing_build_context()

        if self._new_round_pending:
            self.turn_number += 1
            self._new_round_pending = False

        self._turn_passed_go = False
        self.drawn_cards_this_turn = []
        self.financial_events_this_turn = []
        player = self.current_player

        if player.in_jail:
            result = self._take_jail_turn(player, jail_action)
        else:
            result = self._take_free_turn(player)

        self.record_event(
            "turn",
            (
                f"Tour {result.turn_number} — {result.player.name} : "
                f"{result.dice[0]} + {result.dice[1]} → {result.landed_space_name}."
            ),
            result.player,
            dice=list(result.dice),
            rolled_double=result.rolled_double,
            passed_go=result.passed_go,
            landed_space=result.landed_space_name,
        )
        return result

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

        if self.consecutive_doubles >= self.rules.doubles_to_jail:
            self.rules.send_to_jail(player)
            self.consecutive_doubles = 0
            result = self._make_turn_result(
                player,
                (d1, d2),
                rolled_double=True,
                message=(
                    f"{player.name} a fait {self.rules.doubles_to_jail} doubles "
                    "consécutifs et va en prison."
                ),
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
        if player.jail_turns < self.rules.max_jail_turns:
            result = self._make_turn_result(
                player,
                (d1, d2),
                False,
                f"{player.name} reste en prison ({player.jail_turns}/{self.rules.max_jail_turns}).",
            )
            self._advance_turn()
            return result

        self.rules.pay_bank(player, self.rules.jail_fine)
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
            f"{player.name} paie {self.rules.jail_fine} après sa dernière tentative et sort de prison.",
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
                rent = self.rules.scale_rent(dice_total * utility_multiplier)
            else:
                base_rent = space.calculate_rent(self, dice_total) * rent_multiplier
                rent = self.rules.scale_rent(base_rent)

            owner = space.owner
            if rent <= 0:
                return f"{space.name} applique un loyer de 0 $."
            if not self.options.automatic_rent:
                self.pending_rent_claim = PendingRentClaim(
                    payer=player,
                    recipient=owner,
                    amount=rent,
                    property_index=space.index,
                )
                self.record_event(
                    "rent_pending",
                    f"{owner.name} peut réclamer {rent} $ de loyer à {player.name}.",
                    owner,
                    amount=rent,
                    payer_id=player.player_id,
                    property_index=space.index,
                )
                return f"Loyer manuel : {owner.name} peut réclamer {rent} $ à {player.name}."

            self.rules.transfer_money(player, owner, rent)
            self.record_event(
                "rent",
                f"{player.name} paie {rent} $ de loyer à {owner.name}.",
                player,
                amount=rent,
                recipient_id=owner.player_id,
                property_index=space.index,
            )
            return f"{player.name} paie {rent} de loyer à {owner.name}."

        return space.land(self, player, dice_total)

    def _advance_turn(self) -> None:
        """Passe au prochain joueur actif et détecte la fin d'un tour de table.

        Entrées:
            Aucune autre que l'état courant de la partie.

        Sortie:
            None: Le joueur courant avance ; un passage de la fin vers le début
            de l'ordre de table marque un tour complet et prépare le numéro suivant.
        """
        if len(self.active_players) <= 1:
            return

        previous_index = self.current_player_index
        for _ in range(len(self.players)):
            candidate = (self.current_player_index + 1) % len(self.players)
            self.current_player_index = candidate
            if self.current_player.bankrupt:
                continue

            if candidate < previous_index:
                self.completed_rounds += 1
                self._new_round_pending = True
            return
