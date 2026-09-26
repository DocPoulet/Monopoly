"""Centralise les règles transversales qui font interagir joueurs, argent et plateau."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .properties import OwnableSpace, Property

if TYPE_CHECKING:
    from .game import Game
    from .player import Player


class Rules:
    """Applique les règles générales d'une partie de Monopoly.

    Entrées:
        game (Game): Partie à laquelle ces règles sont rattachées.

    Sortie:
        Rules: Service central pour les déplacements, paiements, achats et bâtiments.
    """

    GO_SALARY = 200
    JAIL_POSITION = 10
    MAX_JAIL_TURNS = 3
    JAIL_FINE = 50

    def __init__(self, game: Game) -> None:
        """Associe l'ensemble de règles à une partie précise.

        Entrées:
            game (Game): Partie dont l'état sera modifié par les règles.

        Sortie:
            None: Le constructeur conserve une référence vers la partie.
        """
        self.game = game

    def move_player(self, player: Player, steps: int) -> bool:
        """Avance un joueur et verse le salaire s'il passe par Départ.

        Entrées:
            player (Player): Joueur à déplacer.
            steps (int): Nombre de cases à avancer.

        Sortie:
            bool: ``True`` si le déplacement franchit Départ, sinon ``False``.
        """
        raw_position = player.position + steps
        passed_go = raw_position >= len(self.game.board)
        if passed_go:
            player.receive(self.GO_SALARY)
        player.move_to(raw_position % len(self.game.board))
        return passed_go

    def move_player_to(self, player: Player, destination: int, collect_go: bool = True) -> bool:
        """Déplace un joueur vers une case absolue avec salaire éventuel au passage par Départ.

        Entrées:
            player (Player): Joueur à déplacer.
            destination (int): Index exact de la case d'arrivée.
            collect_go (bool): Autorise le versement de 200 si le déplacement boucle le plateau.

        Sortie:
            bool: ``True`` si le joueur a franchi Départ et a pu recevoir le salaire.
        """
        if not 0 <= destination < len(self.game.board):
            raise ValueError("La destination doit correspondre à une case du plateau.")
        passed_go = collect_go and destination < player.position
        if passed_go:
            player.receive(self.GO_SALARY)
        player.move_to(destination)
        return passed_go

    def move_player_backward(self, player: Player, steps: int) -> None:
        """Fait reculer un joueur sans jamais verser le salaire de Départ.

        Entrées:
            player (Player): Joueur à déplacer vers l'arrière.
            steps (int): Nombre positif de cases à reculer.

        Sortie:
            None: La position du joueur est mise à jour modulo la taille du plateau.
        """
        if steps < 0:
            raise ValueError("Le nombre de cases à reculer doit être positif.")
        player.move_to((player.position - steps) % len(self.game.board))

    def send_to_jail(self, player: Player) -> None:
        """Envoie un joueur en prison et réinitialise son compteur de prison.

        Entrées:
            player (Player): Joueur à incarcérer.

        Sortie:
            None: La position et l'état de prison du joueur sont modifiés.
        """
        player.move_to(self.JAIL_POSITION)
        player.in_jail = True
        player.jail_turns = 0

    def release_from_jail(self, player: Player) -> None:
        """Libère un joueur de prison et remet son compteur de tentatives à zéro.

        Entrées:
            player (Player): Joueur actuellement emprisonné.

        Sortie:
            None: ``in_jail`` devient faux et ``jail_turns`` revient à zéro.
        """
        player.in_jail = False
        player.jail_turns = 0

    def pay_jail_fine(self, player: Player) -> bool:
        """Tente de faire payer volontairement l'amende permettant de sortir de prison.

        Entrées:
            player (Player): Joueur qui souhaite payer 50 avant de lancer les dés.

        Sortie:
            bool: ``True`` si le joueur avait assez d'argent et a été libéré,
            sinon ``False`` sans provoquer automatiquement sa faillite.
        """
        if not player.in_jail or not player.can_afford(self.JAIL_FINE):
            return False
        player.pay(self.JAIL_FINE)
        self.release_from_jail(player)
        return True

    def pay_bank(self, player: Player, amount: int) -> None:
        """Fait payer une somme à la banque et gère une éventuelle faillite.

        Entrées:
            player (Player): Joueur qui doit payer.
            amount (int): Somme due à la banque.

        Sortie:
            None: Le solde est réduit et une faillite peut être déclenchée.
        """
        paid = player.pay(amount)
        if paid < amount:
            self.bankrupt_player(player)

    def transfer_money(self, payer: Player, recipient: Player, amount: int) -> None:
        """Transfère de l'argent entre deux joueurs et gère l'insolvabilité.

        Entrées:
            payer (Player): Joueur qui doit verser la somme.
            recipient (Player): Joueur qui reçoit le paiement effectif.
            amount (int): Montant total réclamé.

        Sortie:
            None: Les soldes sont modifiés et le payeur peut faire faillite.
        """
        paid = payer.pay(amount)
        recipient.receive(paid)
        if paid < amount:
            self.bankrupt_player(payer, creditor=recipient)

    def bankrupt_player(self, player: Player, creditor: Player | None = None) -> None:
        """Déclare un joueur en faillite et redistribue ses biens et cartes conservées.

        Entrées:
            player (Player): Joueur insolvable.
            creditor (Player | None): Joueur recevant les biens, ou ``None`` pour la banque.

        Sortie:
            None: Biens et cartes sont transférés/réinitialisés puis le joueur est marqué failli.
        """
        if player.bankrupt:
            return

        if creditor is not None:
            for property_ in list(player.properties):
                property_.assign_to(creditor)
        else:
            for property_ in list(player.properties):
                property_.reset_ownership()

        for card in list(player.held_cards):
            player.remove_held_card(card)
            if creditor is not None:
                creditor.add_held_card(card)
            else:
                self.game.return_card_to_deck(card)

        player.declare_bankruptcy()

    def buy_property(self, player: Player, space: OwnableSpace) -> bool:
        """Tente d'acheter une case achetable pour le compte d'un joueur.

        Entrées:
            player (Player): Acheteur potentiel.
            space (OwnableSpace): Bien que le joueur souhaite acheter.

        Sortie:
            bool: ``True`` si l'achat est réalisé, sinon ``False``.
        """
        if player.bankrupt:
            return False
        return space.buy(player)

    def calculate_rent(self, space: OwnableSpace, dice_total: int) -> int:
        """Délègue le calcul du loyer au type concret de bien.

        Entrées:
            space (OwnableSpace): Bien dont il faut déterminer le loyer.
            dice_total (int): Somme des dés, utile notamment pour les compagnies.

        Sortie:
            int: Montant du loyer calculé par le bien.
        """
        return space.calculate_rent(self.game, dice_total)

    def _group_properties(self, property_: Property) -> list[Property]:
        """Retourne les terrains appartenant au même groupe de couleur.

        Entrées:
            property_ (Property): Terrain de référence.

        Sortie:
            list[Property]: Tous les terrains du groupe, dans l'ordre du plateau.
        """
        return self.game.board.spaces_in_group(property_.color_group)

    def _group_is_buildable(self, player: Player, property_: Property) -> bool:
        """Vérifie les prérequis communs à toute construction sur un groupe.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si le groupe entier appartient au joueur et n'est pas hypothéqué.
        """
        group = self._group_properties(property_)
        return bool(group) and all(space.owner is player for space in group) and all(
            not space.mortgaged for space in group
        )

    def can_build_house(self, player: Player, property_: Property) -> bool:
        """Vérifie la règle de construction uniforme avant d'ajouter une maison.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si le terrain est parmi les moins développés du groupe,
            possède moins de quatre maisons et si le joueur peut payer.
        """
        if not self._group_is_buildable(player, property_):
            return False
        if property_.hotel or property_.houses >= 4 or not player.can_afford(property_.house_cost):
            return False
        group = self._group_properties(property_)
        minimum_level = min(space.development_level for space in group)
        return property_.development_level == minimum_level

    def build_house(self, player: Player, property_: Property) -> bool:
        """Construit une maison en respectant le développement uniforme du groupe.

        Entrées:
            player (Player): Joueur qui finance la construction.
            property_ (Property): Terrain sur lequel construire.

        Sortie:
            bool: ``True`` si une maison est construite, sinon ``False``.
        """
        if not self.can_build_house(player, property_):
            return False
        player.pay(property_.house_cost)
        property_.houses += 1
        return True

    def can_build_hotel(self, player: Player, property_: Property) -> bool:
        """Vérifie si quatre maisons peuvent être remplacées par un hôtel.

        Entrées:
            player (Player): Joueur souhaitant construire l'hôtel.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si tout le groupe est développé au niveau quatre ou plus
            et si le joueur peut payer le coût de construction.
        """
        if not self._group_is_buildable(player, property_):
            return False
        if property_.hotel or property_.houses != 4 or not player.can_afford(property_.house_cost):
            return False
        group = self._group_properties(property_)
        return min(space.development_level for space in group) >= 4

    def build_hotel(self, player: Player, property_: Property) -> bool:
        """Remplace quatre maisons par un hôtel lorsque la règle l'autorise.

        Entrées:
            player (Player): Joueur qui finance l'hôtel.
            property_ (Property): Terrain à améliorer.

        Sortie:
            bool: ``True`` si l'hôtel est construit, sinon ``False``.
        """
        if not self.can_build_hotel(player, property_):
            return False
        player.pay(property_.house_cost)
        property_.houses = 0
        property_.hotel = True
        return True

    def can_sell_building(self, player: Player, property_: Property) -> bool:
        """Vérifie si un bâtiment peut être vendu en respectant l'équilibre inverse.

        Entrées:
            player (Player): Propriétaire souhaitant vendre un bâtiment.
            property_ (Property): Terrain sur lequel retirer un bâtiment.

        Sortie:
            bool: ``True`` si le terrain est l'un des plus développés du groupe.
        """
        if property_.owner is not player or property_.development_level == 0:
            return False
        group = self._group_properties(property_)
        if not group or any(space.owner is not player for space in group):
            return False
        maximum_level = max(space.development_level for space in group)
        return property_.development_level == maximum_level

    def sell_building(self, player: Player, property_: Property) -> bool:
        """Vend une maison ou un hôtel à la banque pour la moitié de son coût.

        Entrées:
            player (Player): Propriétaire recevant le remboursement.
            property_ (Property): Terrain dont on retire un niveau de développement.

        Sortie:
            bool: ``True`` si un bâtiment est vendu, sinon ``False``.
        """
        if not self.can_sell_building(player, property_):
            return False
        if property_.hotel:
            property_.hotel = False
            property_.houses = 4
        else:
            property_.houses -= 1
        player.receive(property_.house_cost // 2)
        return True

    def can_mortgage(self, player: Player, space: OwnableSpace) -> bool:
        """Vérifie si un bien peut être hypothéqué.

        Entrées:
            player (Player): Propriétaire demandant l'hypothèque.
            space (OwnableSpace): Bien ciblé.

        Sortie:
            bool: ``True`` si le bien appartient au joueur, n'est pas déjà hypothéqué
            et, pour un terrain, si aucun bâtiment n'existe dans son groupe de couleur.
        """
        if space.owner is not player or space.mortgaged:
            return False
        if isinstance(space, Property):
            group = self._group_properties(space)
            if any(property_.development_level > 0 for property_ in group):
                return False
        return True

    def mortgage_property(self, player: Player, space: OwnableSpace) -> bool:
        """Hypothèque un bien et verse sa valeur hypothécaire au propriétaire.

        Entrées:
            player (Player): Propriétaire du bien.
            space (OwnableSpace): Bien à hypothéquer.

        Sortie:
            bool: ``True`` si l'hypothèque est appliquée, sinon ``False``.
        """
        if not self.can_mortgage(player, space):
            return False
        space.mortgaged = True
        player.receive(space.mortgage_value)
        return True

    def can_unmortgage(self, player: Player, space: OwnableSpace) -> bool:
        """Vérifie si un joueur peut lever l'hypothèque d'un de ses biens.

        Entrées:
            player (Player): Propriétaire souhaitant déshypothéquer.
            space (OwnableSpace): Bien ciblé.

        Sortie:
            bool: ``True`` si le bien est hypothéqué et si le joueur peut payer le coût.
        """
        return space.owner is player and space.mortgaged and player.can_afford(space.unmortgage_cost)

    def unmortgage_property(self, player: Player, space: OwnableSpace) -> bool:
        """Lève l'hypothèque d'un bien après paiement du principal et des intérêts.

        Entrées:
            player (Player): Propriétaire qui paie la levée d'hypothèque.
            space (OwnableSpace): Bien à déshypothéquer.

        Sortie:
            bool: ``True`` si l'opération est effectuée, sinon ``False``.
        """
        if not self.can_unmortgage(player, space):
            return False
        player.pay(space.unmortgage_cost)
        space.mortgaged = False
        return True
