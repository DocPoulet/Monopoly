"""Centralise les règles transversales qui font interagir joueurs, argent et plateau."""

from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

from .properties import OwnableSpace, Property
from .debt import DebtManagementResult

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


    @property
    def go_salary(self) -> int:
        """Retourne le salaire de Départ configuré pour la partie.

        Entrées:
            Aucune.

        Sortie:
            int: Somme versée lors d'un passage par Départ.
        """
        return self.game.options.go_salary

    @property
    def jail_fine(self) -> int:
        """Retourne l'amende de prison configurée pour la partie.

        Entrées:
            Aucune.

        Sortie:
            int: Montant du paiement de sortie de prison.
        """
        return self.game.options.jail_fine

    @property
    def max_jail_turns(self) -> int:
        """Retourne le nombre maximal de tentatives de dés en prison.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de tentatives autorisées avant paiement obligatoire.
        """
        return self.game.options.max_jail_turns

    @property
    def doubles_to_jail(self) -> int:
        """Retourne le seuil de doubles consécutifs envoyant en prison.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de doubles consécutifs configuré.
        """
        return self.game.options.doubles_to_jail


    def scale_rent(self, amount: int) -> int:
        """Applique le pourcentage de loyer configuré à un montant brut.

        Entrées:
            amount (int): Loyer calculé selon le titre de propriété.

        Sortie:
            int: Loyer ajusté et arrondi à l'entier le plus proche.
        """
        return max(0, round(amount * self.game.options.rent_percent / 100))

    def mortgage_interest(self, space: OwnableSpace) -> int:
        """Calcule l'intérêt configuré sur une hypothèque.

        Entrées:
            space (OwnableSpace): Bien hypothéqué concerné.

        Sortie:
            int: Intérêt arrondi au supérieur selon ``unmortgage_tax_percent``.
        """
        return ceil(
            space.mortgage_value
            * self.game.options.unmortgage_tax_percent
            / 100
        )

    def unmortgage_cost(self, space: OwnableSpace) -> int:
        """Calcule le coût total configuré pour lever une hypothèque.

        Entrées:
            space (OwnableSpace): Bien à déshypothéquer.

        Sortie:
            int: Principal hypothécaire plus intérêt configuré.
        """
        return space.mortgage_value + self.mortgage_interest(space)

    def building_resale_value(self, property_: Property, levels: int = 1) -> int:
        """Calcule le remboursement configuré lors d'une revente de bâtiments.

        Entrées:
            property_ (Property): Terrain donnant le coût de construction d'un niveau.
            levels (int): Nombre de niveaux revendus simultanément.

        Sortie:
            int: Remboursement selon ``building_resale_percent``.
        """
        if levels <= 0:
            return 0
        return round(
            property_.house_cost
            * levels
            * self.game.options.building_resale_percent
            / 100
        )

    def _owned_build_group(self, player: Player, property_: Property) -> list[Property]:
        """Retourne le groupe pertinent pour l'équilibrage des constructions.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain de référence.

        Sortie:
            list[Property]: Groupe complet si le monopole est requis, sinon terrains du
            même groupe appartenant effectivement au joueur.
        """
        group = self._group_properties(property_)
        if self.game.options.monopoly_required_for_building:
            return group
        return [space for space in group if space.owner is player]

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
            player.receive(self.go_salary)
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
            player.receive(self.go_salary)
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
        """Tente de payer volontairement l'amende permettant de sortir de prison.

        Entrées:
            player (Player): Joueur emprisonné souhaitant payer avant son lancer.

        Sortie:
            bool: ``True`` si l'amende a pu être réunie et payée, sinon ``False``.

        Notes:
            Le joueur peut légalement vendre des bâtiments ou hypothéquer des biens
            pour réunir l'amende. Un échec volontaire ne déclenche pas à lui seul
            une faillite : le joueur peut encore tenter les dés si les règles le permettent.
        """
        if not player.in_jail or player.bankrupt:
            return False

        if player.cash < self.jail_fine:
            self.raise_cash_for_debt(player, self.jail_fine)

        if player.bankrupt or not player.can_afford(self.jail_fine):
            return False

        player.pay(self.jail_fine)
        self.release_from_jail(player)
        return True


    def debt_transfer_value(self, space: OwnableSpace) -> int:
        """Calcule la valeur à 100 % d'un bien cédé directement à un créancier.

        Entrées:
            space (OwnableSpace): Terrain, gare ou compagnie destiné au créancier.

        Sortie:
            int: Prix actuel du bien plus 100 % du coût des bâtiments encore présents.
        """
        value = space.price
        if isinstance(space, Property):
            value += space.development_level * space.house_cost
        return value

    def can_transfer_property_for_debt(
        self,
        player: Player,
        creditor: Player | None,
        space: OwnableSpace,
    ) -> bool:
        """Vérifie si un bien peut servir directement au paiement d'une dette joueur.

        Entrées:
            player (Player): Débiteur propriétaire du bien.
            creditor (Player | None): Joueur devant recevoir le bien.
            space (OwnableSpace): Bien envisagé.

        Sortie:
            bool: ``True`` lorsque la variante est active et que le bien n'a pas déjà
            été monétisé par une hypothèque.
        """
        return (
            self.game.options.property_debt_payment
            and creditor is not None
            and creditor is not player
            and not creditor.bankrupt
            and not player.bankrupt
            and space.owner is player
            and not space.mortgaged
        )

    def transfer_property_for_debt(
        self,
        player: Player,
        creditor: Player,
        space: OwnableSpace,
    ) -> int:
        """Cède un bien au créancier et retourne la valeur imputée sur la dette.

        Entrées:
            player (Player): Débiteur actuel.
            creditor (Player): Joueur créancier.
            space (OwnableSpace): Bien non hypothéqué à transférer.

        Sortie:
            int: Valeur intégrale du bien et des bâtiments restants, ou zéro si refusé.
        """
        if not self.can_transfer_property_for_debt(player, creditor, space):
            return 0

        value = self.debt_transfer_value(space)
        space.assign_to(creditor)
        self.game.record_event(
            "debt_property_transfer",
            (
                f"{player.name} cède {space.name} à {creditor.name} "
                f"pour réduire sa dette de {value} $."
            ),
            player,
            creditor_id=creditor.player_id,
            property_index=space.index,
            debt_value=value,
            development_level=(
                space.development_level if isinstance(space, Property) else 0
            ),
        )
        return value

    def maximum_debt_capacity(
        self,
        player: Player,
        creditor: Player | None = None,
    ) -> int:
        """Estime le remboursement maximal encore accessible sans modifier la partie.

        Entrées:
            player (Player): Débiteur à analyser.
            creditor (Player | None): Joueur créancier permettant éventuellement
                la cession directe de biens.

        Sortie:
            int: Somme maximale théorique composée du cash actuel et de la meilleure
            valorisation de chaque actif restant.

        Notes:
            Cette borne choisit, bien par bien, la meilleure voie entre revente des
            bâtiments + hypothèque et cession au créancier. Elle sert à détecter
            immédiatement les dettes définitivement impossibles à rembourser.
        """
        if player.bankrupt:
            return 0

        capacity = player.cash
        for space in player.properties:
            if space.mortgaged:
                continue

            building_levels = (
                space.development_level if isinstance(space, Property) else 0
            )
            resale_value = (
                self.building_resale_value(space, building_levels)
                if isinstance(space, Property)
                else 0
            )

            liquidation_value = resale_value
            if self.game.options.mortgages_enabled:
                liquidation_value += space.mortgage_value

            transfer_value = 0
            if self.can_transfer_property_for_debt(player, creditor, space):
                intact_transfer = self.debt_transfer_value(space)
                stripped_transfer = resale_value + space.price
                transfer_value = max(intact_transfer, stripped_transfer)

            capacity += max(liquidation_value, transfer_value)

        return capacity



    def raise_cash_for_debt(
        self,
        player: Player,
        target_cash: int,
        creditor: Player | None = None,
    ) -> DebtManagementResult:
        """Réunit des ressources avant paiement, avec cession de biens optionnelle.

        Entrées:
            player (Player): Joueur devant trouver des ressources.
            target_cash (int): Montant total de la dette à couvrir.
            creditor (Player | None): Joueur créancier ; ``None`` signifie la banque.

        Sortie:
            DebtManagementResult: Liquidités disponibles, valeur de biens déjà cédés
            et éventuelle demande explicite de faillite.

        Notes:
            En interface graphique, le joueur décide lui-même des ventes, hypothèques
            et cessions. Sans interface, la variante de cession est privilégiée avant
            l'hypothèque afin qu'un bien puisse réellement compter à 100 % de sa valeur.
        """
        if player.bankrupt:
            return DebtManagementResult(False, 0, True)

        managed = self.game.manage_debt(player, target_cash, creditor)
        if managed is not None:
            return managed

        property_credit = 0

        while player.cash < max(0, target_cash - property_credit):
            remaining = max(0, target_cash - property_credit)

            transferable = []
            if creditor is not None:
                transferable = [
                    space
                    for space in list(player.properties)
                    if self.can_transfer_property_for_debt(player, creditor, space)
                ]

            if transferable:
                shortfall = max(0, remaining - player.cash)
                transferable.sort(
                    key=lambda space: (
                        self.debt_transfer_value(space) < shortfall,
                        abs(self.debt_transfer_value(space) - shortfall),
                        self.debt_transfer_value(space),
                        space.index,
                    )
                )
                chosen = transferable[0]
                property_credit += self.transfer_property_for_debt(
                    player,
                    creditor,
                    chosen,
                )
                continue

            sellable = [
                space
                for space in player.properties
                if isinstance(space, Property)
                and self.can_sell_building(player, space)
            ]
            if sellable:
                property_ = max(
                    sellable,
                    key=lambda item: (
                        item.development_level,
                        item.house_cost,
                        -item.index,
                    ),
                )
                previous_level = property_.development_level
                if self.sell_building(player, property_):
                    label = "hôtel" if previous_level == 5 else "maison"
                    self.game.record_financial_event(
                        f"{player.name} vend un {label} sur {property_.name} "
                        f"pour {self.building_resale_value(property_)} $ afin de régler sa dette."
                    )
                    continue

            mortgageable = [
                space
                for space in player.properties
                if self.can_mortgage(player, space)
            ]
            if mortgageable:
                selected = self.game.choose_mortgages_for_debt(
                    player,
                    mortgageable,
                    remaining,
                )

                if selected:
                    mortgaged_any = False
                    for space in selected:
                        if player.cash >= remaining:
                            break
                        if self.can_mortgage(player, space) and self.mortgage_property(player, space):
                            mortgaged_any = True
                            self.game.record_financial_event(
                                f"{player.name} hypothèque {space.name} "
                                f"pour {space.mortgage_value} $ afin de régler sa dette."
                            )
                    if mortgaged_any:
                        continue

            break

        remaining_cash = max(0, target_cash - property_credit)
        return DebtManagementResult(
            player.cash >= remaining_cash,
            property_credit,
            False,
        )

    def pay_bank(self, player: Player, amount: int) -> None:
        """Fait payer la banque après avoir tenté de liquider légalement des actifs.

        Entrées:
            player (Player): Joueur qui doit payer.
            amount (int): Somme due à la banque.

        Sortie:
            None: La dette est payée si possible ; sinon les liquidités restantes
            sont versées avant la faillite du joueur.
        """
        if amount <= 0 or player.bankrupt:
            return

        if player.cash < amount:
            self.raise_cash_for_debt(player, amount, creditor=None)

        paid = player.pay(amount)
        if self.game.card_resolution_active and paid > 0:
            self.game.add_to_free_parking_pot(paid, player)
        if paid < amount:
            self.bankrupt_player(player)


    def transfer_money(self, payer: Player, recipient: Player, amount: int) -> None:
        """Règle une dette joueur par cash et, si activé, par cession directe de biens.

        Entrées:
            payer (Player): Joueur qui doit verser la somme.
            recipient (Player): Joueur créancier.
            amount (int): Montant total réclamé.

        Sortie:
            None: Les biens cédés réduisent d'abord la dette à leur valeur configurée,
            puis les liquidités règlent le solde ; l'insolvabilité restante entraîne
            la faillite envers le créancier.
        """
        if amount <= 0 or payer.bankrupt:
            return

        resolution = DebtManagementResult(payer.cash >= amount, 0, False)
        if payer.cash < amount:
            resolution = self.raise_cash_for_debt(
                payer,
                amount,
                creditor=recipient,
            )

        remaining = max(0, amount - resolution.property_credit)
        paid = payer.pay(remaining)
        recipient.receive(paid)

        if resolution.property_credit:
            self.game.record_financial_event(
                f"{resolution.property_credit} $ de la dette de {payer.name} envers "
                f"{recipient.name} ont été réglés par cession de biens."
            )

        if paid < remaining:
            self.bankrupt_player(payer, creditor=recipient)

    def _liquidate_all_buildings_for_bankruptcy(self, player: Player) -> int:
        """Retire tous les bâtiments restants et verse leur valeur de revente.

        Entrées:
            player (Player): Joueur dont les améliorations doivent être liquidées.

        Sortie:
            int: Somme totale versée au joueur avant la redistribution de ses biens.

        Notes:
            Cette liquidation complète est utilisée uniquement lors d'une faillite.
            Elle remet directement les bâtiments dans le stock de la banque sans
            nécessiter les quatre maisons intermédiaires d'une vente normale d'hôtel.
        """
        total = 0

        for space in list(player.properties):
            if not isinstance(space, Property):
                continue

            if space.hotel:
                refund = self.building_resale_value(space, 5)
                self.game.bank.return_hotels(1)
                space.hotel = False
                space.houses = 0
                player.receive(refund)
                total += refund
                self.game.record_financial_event(
                    f"La banque reprend l'hôtel de {space.name} pour {refund} $ "
                    f"lors de la faillite de {player.name}."
                )
                continue

            if space.houses > 0:
                count = space.houses
                refund = self.building_resale_value(space, count)
                self.game.bank.return_houses(count)
                space.houses = 0
                player.receive(refund)
                total += refund
                self.game.record_financial_event(
                    f"La banque reprend {count} maison(s) sur {space.name} "
                    f"pour {refund} $ lors de la faillite de {player.name}."
                )

        return total

    def bankrupt_player(self, player: Player, creditor: Player | None = None) -> None:
        """Déclare un joueur en faillite et applique la redistribution correspondante.

        Entrées:
            player (Player): Joueur insolvable.
            creditor (Player | None): Joueur créancier, ou ``None`` si la dette est envers la banque.

        Sortie:
            None: Bâtiments, argent restant, biens et cartes sont redistribués,
            puis le joueur est marqué en faillite.

        Notes:
            - envers un joueur : les biens et cartes lui sont transférés et les
              hypothèques reçues déclenchent immédiatement 10 % d'intérêts ;
            - envers la banque : les biens sont libérés et placés dans une file
              d'enchères obligatoires pour les joueurs encore actifs.
        """
        if player.bankrupt:
            return

        self._liquidate_all_buildings_for_bankruptcy(player)

        if creditor is not None and player.cash > 0:
            creditor.receive(player.pay(player.cash))

        transferred_mortgaged: list[OwnableSpace] = []

        if creditor is not None:
            for property_ in list(player.properties):
                if property_.mortgaged:
                    transferred_mortgaged.append(property_)
                property_.assign_to(creditor)
        else:
            for property_ in list(player.properties):
                property_.reset_ownership()
                if self.game.options.auctions_enabled:
                    self.game.queue_bank_auction(property_)

        for card in list(player.held_cards):
            player.remove_held_card(card)
            if creditor is not None:
                creditor.add_held_card(card)
            else:
                self.game.return_card_to_deck(card)

        player.declare_bankruptcy()
        self.game.record_event(
            "bankruptcy",
            f"{player.name} est déclaré en faillite.",
            player,
            creditor_id=None if creditor is None else creditor.player_id,
        )

        if creditor is not None and transferred_mortgaged and not creditor.bankrupt:
            self.game.settle_received_mortgages(
                creditor,
                transferred_mortgaged,
            )

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
        purchased = space.buy(player)
        if purchased:
            self.game.record_event(
                "purchase",
                f"{player.name} achète {space.name} pour {space.price} $.",
                player,
                property_index=space.index,
                price=space.price,
            )
        return purchased

    def calculate_rent(self, space: OwnableSpace, dice_total: int) -> int:
        """Délègue le calcul du loyer au type concret de bien.

        Entrées:
            space (OwnableSpace): Bien dont il faut déterminer le loyer.
            dice_total (int): Somme des dés, utile notamment pour les compagnies.

        Sortie:
            int: Montant du loyer calculé par le bien.
        """
        return self.scale_rent(space.calculate_rent(self.game, dice_total))

    def _group_properties(self, property_: Property) -> list[Property]:
        """Retourne les terrains appartenant au même groupe de couleur.

        Entrées:
            property_ (Property): Terrain de référence.

        Sortie:
            list[Property]: Tous les terrains du groupe, dans l'ordre du plateau.
        """
        return self.game.board.spaces_in_group(property_.color_group)


    def _group_is_buildable(self, player: Player, property_: Property) -> bool:
        """Vérifie les prérequis communs à toute construction selon les variantes.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si possession, hypothèques, monopole éventuel et position
            autorisent la construction.
        """
        if property_.owner is not player:
            return False
        if (
            not self.game.options.construction_anywhere
            and not self.game.can_build_from_landing(player, property_)
        ):
            return False

        group = self._owned_build_group(player, property_)
        if not group:
            return False
        if self.game.options.monopoly_required_for_building:
            full_group = self._group_properties(property_)
            if not full_group or any(space.owner is not player for space in full_group):
                return False
        return all(not space.mortgaged for space in group)

    def can_request_house(self, player: Player, property_: Property) -> bool:
        """Vérifie si une maison peut légalement être placée sans regarder prix ni stock.

        Entrées:
            player (Player): Joueur souhaitant développer son groupe.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si propriété, monopole, hypothèques et équilibre autorisent
            l'ajout d'une maison.
        """
        if not self._group_is_buildable(player, property_):
            return False
        if property_.hotel or property_.houses >= 4:
            return False
        group = self._owned_build_group(player, property_)
        minimum_level = min(space.development_level for space in group)
        return property_.development_level == minimum_level

    def eligible_house_targets(self, player: Player) -> list[Property]:
        """Retourne tous les terrains où le joueur peut légalement ajouter une maison.

        Entrées:
            player (Player): Joueur dont les groupes sont inspectés.

        Sortie:
            list[Property]: Terrains éligibles, indépendamment du stock et du prix.
        """
        return [
            space
            for space in self.game.board.spaces
            if isinstance(space, Property)
            and self.can_request_house(player, space)
        ]

    def can_build_house(self, player: Player, property_: Property) -> bool:
        """Vérifie si une maison peut être achetée directement à son prix normal.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si la construction est légale, payable et disponible en banque.
        """
        return (
            self.can_request_house(player, property_)
            and player.can_afford(property_.house_cost)
            and self.game.bank.can_supply_houses(1)
        )

    def build_house_at_price(
        self,
        player: Player,
        property_: Property,
        price: int,
    ) -> bool:
        """Construit une maison pour un prix donné, notamment après une enchère.

        Entrées:
            player (Player): Joueur recevant la maison.
            property_ (Property): Terrain où la placer.
            price (int): Prix effectivement payé à la banque.

        Sortie:
            bool: ``True`` si la maison est placée et payée.
        """
        if (
            price < 0
            or not self.can_request_house(player, property_)
            or not player.can_afford(price)
            or not self.game.bank.take_houses(1)
        ):
            return False

        player.pay(price)
        property_.houses += 1
        self.game.record_event(
            "building",
            f"{player.name} construit une maison sur {property_.name} pour {price} $.",
            player,
            building_type="house",
            property_index=property_.index,
            price=price,
        )
        return True


    def max_landing_house_purchase(
        self,
        player: Player,
        property_: Property,
        limit: int = 4,
    ) -> int:
        """Calcule combien de maisons peuvent être achetées lors de cet atterrissage.

        Entrées:
            player (Player): Joueur possédant le terrain fraîchement atteint.
            property_ (Property): Terrain concerné.
            limit (int): Maximum technique demandé avant application du réglage de partie.

        Sortie:
            int: Nombre maximal de maisons achetables immédiatement, borné par le réglage de partie.

        Notes:
            Le calcul respecte l'équilibre des constructions, l'argent disponible et le
            stock bancaire. Il ne permet jamais d'acheter un hôtel dans la même opération.
        """
        if limit <= 0 or not self.can_request_house(player, property_):
            return 0

        limit = min(
            4,
            self.game.options.max_buildings_per_action,
            limit,
            4 - property_.houses,
        )
        if limit <= 0:
            return 0

        original_houses = property_.houses
        count = 0
        try:
            while count < limit:
                if not self.can_request_house(player, property_):
                    break
                next_count = count + 1
                if not player.can_afford(next_count * property_.house_cost):
                    break
                if not self.game.bank.can_supply_houses(next_count):
                    break
                property_.houses += 1
                count += 1
        finally:
            property_.houses = original_houses

        return count

    def build_houses(
        self,
        player: Player,
        property_: Property,
        count: int,
    ) -> bool:
        """Achète plusieurs maisons d'un seul choix sans pouvoir inclure un hôtel.

        Entrées:
            player (Player): Joueur qui finance les maisons.
            property_ (Property): Terrain fraîchement atteint.
            count (int): Nombre de maisons demandé, limité par ``max_buildings_per_action``.

        Sortie:
            bool: ``True`` si toutes les maisons demandées ont été achetées.

        Notes:
            La quantité est validée avant toute modification afin d'éviter un achat partiel.
        """
        if count < 1 or count > self.game.options.max_buildings_per_action:
            return False
        if count > self.max_landing_house_purchase(
            player,
            property_,
            limit=self.game.options.max_buildings_per_action,
        ):
            return False

        for _ in range(count):
            if not self.build_house(player, property_):
                return False
        return True

    def build_house(self, player: Player, property_: Property) -> bool:
        """Construit une maison au prix imprimé sur le titre de propriété.

        Entrées:
            player (Player): Joueur qui finance la construction.
            property_ (Property): Terrain sur lequel construire.

        Sortie:
            bool: ``True`` si une maison est construite.
        """
        if not self.can_build_house(player, property_):
            return False
        return self.build_house_at_price(player, property_, property_.house_cost)

    def can_request_hotel(self, player: Player, property_: Property) -> bool:
        """Vérifie si un hôtel peut légalement remplacer les quatre maisons d'un terrain.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si l'équilibre du groupe autorise la conversion en hôtel,
            indépendamment du prix et du stock d'hôtels.
        """
        if not self._group_is_buildable(player, property_):
            return False
        if property_.hotel or property_.houses != 4:
            return False
        group = self._owned_build_group(player, property_)
        return min(space.development_level for space in group) >= 4

    def eligible_hotel_targets(self, player: Player) -> list[Property]:
        """Retourne tous les terrains où le joueur peut légalement placer un hôtel.

        Entrées:
            player (Player): Joueur dont les groupes sont inspectés.

        Sortie:
            list[Property]: Terrains éligibles, sans tenir compte du prix ou du stock.
        """
        return [
            space
            for space in self.game.board.spaces
            if isinstance(space, Property)
            and self.can_request_hotel(player, space)
        ]

    def can_build_hotel(self, player: Player, property_: Property) -> bool:
        """Vérifie si un hôtel peut être acheté directement à son prix normal.

        Entrées:
            player (Player): Joueur souhaitant construire.
            property_ (Property): Terrain ciblé.

        Sortie:
            bool: ``True`` si conversion, paiement et stock bancaire sont possibles.
        """
        return (
            self.can_request_hotel(player, property_)
            and player.can_afford(property_.house_cost)
            and self.game.bank.can_supply_hotels(1)
        )

    def build_hotel_at_price(
        self,
        player: Player,
        property_: Property,
        price: int,
    ) -> bool:
        """Construit un hôtel pour un prix donné et rend quatre maisons à la banque.

        Entrées:
            player (Player): Joueur recevant l'hôtel.
            property_ (Property): Terrain à convertir.
            price (int): Prix réellement payé, éventuellement issu d'une enchère.

        Sortie:
            bool: ``True`` si l'hôtel est placé et le stock correctement échangé.
        """
        if (
            price < 0
            or not self.can_request_hotel(player, property_)
            or not player.can_afford(price)
            or not self.game.bank.take_hotels(1)
        ):
            return False

        self.game.bank.return_houses(4)
        player.pay(price)
        property_.houses = 0
        property_.hotel = True
        self.game.record_event(
            "building",
            f"{player.name} construit un hôtel sur {property_.name} pour {price} $.",
            player,
            building_type="hotel",
            property_index=property_.index,
            price=price,
        )
        return True

    def build_hotel(self, player: Player, property_: Property) -> bool:
        """Construit un hôtel au prix imprimé sur le titre de propriété.

        Entrées:
            player (Player): Joueur qui finance l'hôtel.
            property_ (Property): Terrain à améliorer.

        Sortie:
            bool: ``True`` si l'hôtel est construit.
        """
        if not self.can_build_hotel(player, property_):
            return False
        return self.build_hotel_at_price(player, property_, property_.house_cost)

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
        group = self._owned_build_group(player, property_)
        if not group:
            return False
        maximum_level = max(space.development_level for space in group)
        if property_.development_level != maximum_level:
            return False

        if property_.hotel and not self.game.bank.can_supply_houses(4):
            return False

        return True

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
            if not self.game.bank.take_houses(4):
                return False
            self.game.bank.return_hotels(1)
            property_.hotel = False
            property_.houses = 4
        else:
            property_.houses -= 1
            self.game.bank.return_houses(1)

        refund = self.building_resale_value(property_)
        player.receive(refund)
        self.game.record_event(
            "building_sale",
            f"{player.name} vend un niveau de bâtiment sur {property_.name} pour {refund} $.",
            player,
            property_index=property_.index,
            refund=refund,
        )
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
        if not self.game.options.mortgages_enabled:
            return False
        if space.owner is not player or space.mortgaged:
            return False
        if isinstance(space, Property):
            group = self._owned_build_group(player, space)
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
        self.game.record_event(
            "mortgage",
            f"{player.name} hypothèque {space.name} pour {space.mortgage_value} $.",
            player,
            property_index=space.index,
            amount=space.mortgage_value,
        )
        return True

    def can_unmortgage(self, player: Player, space: OwnableSpace) -> bool:
        """Vérifie si un joueur peut lever l'hypothèque d'un de ses biens.

        Entrées:
            player (Player): Propriétaire souhaitant déshypothéquer.
            space (OwnableSpace): Bien ciblé.

        Sortie:
            bool: ``True`` si le bien est hypothéqué et si le joueur peut payer le coût.
        """
        cost = self.unmortgage_cost(space)
        return space.owner is player and space.mortgaged and player.can_afford(cost)

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
        cost = self.unmortgage_cost(space)
        player.pay(cost)
        space.mortgaged = False
        self.game.record_event(
            "unmortgage",
            f"{player.name} lève l'hypothèque de {space.name} pour {cost} $.",
            player,
            property_index=space.index,
            amount=cost,
        )
        return True
