"""Interface console minimale permettant de jouer avec le moteur Monopoly."""

from monopoly import Auction, Game
from monopoly.player import Player
from monopoly.properties import OwnableSpace, Property


def print_player_state(player: Player) -> None:
    """Affiche dans le terminal l'état principal d'un joueur.

    Entrées:
        player (Player): Joueur dont les informations doivent être affichées.

    Sortie:
        None: Les informations sont écrites directement dans le terminal.
    """
    properties = ", ".join(
        f"{p.name}{' [H]' if p.mortgaged else ''}"
        for p in player.properties
    ) or "aucune"
    print(
        f"{player.name} | argent={player.cash} | "
        f"position={player.position} | propriétés={properties} | "
        f"cartes conservées={len(player.held_cards)}"
    )


def choose_jail_action(game: Game, player: Player) -> str:
    """Demande au joueur comment il souhaite tenter de sortir de prison.

    Entrées:
        game (Game): Partie fournissant le montant de l'amende.
        player (Player): Joueur actuellement emprisonné.

    Sortie:
        str: ``"roll"``, ``"pay"`` ou ``"card"`` selon le choix valide obtenu.
    """
    options = ["r = tenter un double"]
    if player.can_afford(game.rules.JAIL_FINE):
        options.append(f"p = payer {game.rules.JAIL_FINE}")
    if player.held_cards:
        options.append("c = utiliser une carte sortie de prison")

    print("Prison : " + " | ".join(options))
    choice = input("Choix [r] : ").strip().lower() or "r"

    if choice == "p" and player.can_afford(game.rules.JAIL_FINE):
        return "pay"
    if choice == "c" and player.held_cards:
        return "card"
    return "roll"


def run_console_auction(auction: Auction) -> None:
    """Pilote une enchère avec des saisies terminal jusqu'à sa clôture.

    Entrées:
        auction (Auction): Enchère déjà initialisée par la partie.

    Sortie:
        None: Les offres sont lues avec ``input`` puis le résultat est affiché.
    """
    print(f"Enchère pour {auction.space.name}.")

    while not auction.can_finish:
        progress = False
        for bidder in list(auction.active_bidders):
            if bidder is auction.highest_bidder:
                continue

            minimum = auction.highest_bid + 1
            answer = input(
                f"{bidder.name} (cash {bidder.cash}) : "
                f"offre >= {minimum}, ou 0 pour abandonner : "
            ).strip()

            try:
                amount = int(answer)
            except ValueError:
                print("Saisie invalide.")
                continue

            if amount == 0:
                if auction.withdraw(bidder):
                    progress = True
                continue

            if auction.place_bid(bidder, amount):
                print(f"Meilleure offre : {amount} par {bidder.name}.")
                progress = True
            else:
                print("Offre invalide ou supérieure à votre argent disponible.")

            if auction.can_finish:
                break

        if not progress and not auction.can_finish:
            print("Aucune progression : recommencez avec une offre valide ou abandonnez.")

    result = auction.finish()
    if result.sold:
        print(f"{result.winner.name} remporte {result.space.name} pour {result.amount}.")
    else:
        print(f"{result.space.name} reste à la banque.")


def offer_property_purchase(game: Game, player: Player, space: OwnableSpace) -> None:
    """Propose l'achat direct d'un bien puis lance une enchère en cas de refus.

    Entrées:
        game (Game): Partie contenant les règles et les joueurs actifs.
        player (Player): Joueur ayant atterri sur le bien libre.
        space (OwnableSpace): Bien disponible à l'achat.

    Sortie:
        None: Le bien peut être acheté directement ou attribué après enchère.
    """
    bought = False
    if player.can_afford(space.price):
        answer = input(f"Acheter {space.name} pour {space.price} ? [o/N] ").strip().lower()
        if answer == "o":
            bought = game.rules.buy_property(player, space)
            if bought:
                print("Achat effectué.")

    if not bought and space.owner is None:
        run_console_auction(game.start_auction(space))


def offer_property_management(game: Game, player: Player) -> None:
    """Permet au joueur de gérer bâtiments et hypothèques après son déplacement.

    Entrées:
        game (Game): Partie contenant les règles de gestion immobilière.
        player (Player): Joueur dont les biens peuvent être modifiés.

    Sortie:
        None: Les actions choisies sont directement appliquées au moteur.
    """
    if not player.properties:
        return

    answer = input("Gérer vos propriétés maintenant ? [o/N] ").strip().lower()
    if answer != "o":
        return

    for number, space in enumerate(player.properties, start=1):
        if isinstance(space, Property):
            development = "hôtel" if space.hotel else f"{space.houses} maison(s)"
        else:
            development = "-"
        mortgage = "hypothéqué" if space.mortgaged else "actif"
        print(f"{number}. {space.name} | {development} | {mortgage}")

    try:
        choice = int(input("Numéro du bien (0 pour quitter) : ").strip())
    except ValueError:
        return

    if choice <= 0 or choice > len(player.properties):
        return

    space = player.properties[choice - 1]
    if space.mortgaged:
        if game.rules.unmortgage_property(player, space):
            print(f"{space.name} est déshypothéqué.")
        else:
            print("Déshypothèque impossible.")
        return

    if isinstance(space, Property):
        print("1 = construire, 2 = vendre un bâtiment, 3 = hypothéquer")
        action = input("Action : ").strip()
        if action == "1":
            if game.rules.build_house(player, space):
                print("Maison construite.")
            elif game.rules.build_hotel(player, space):
                print("Hôtel construit.")
            else:
                print("Construction impossible actuellement.")
        elif action == "2":
            print("Bâtiment vendu." if game.rules.sell_building(player, space) else "Vente impossible.")
        elif action == "3":
            print("Bien hypothéqué." if game.rules.mortgage_property(player, space) else "Hypothèque impossible.")
    else:
        print("Bien hypothéqué." if game.rules.mortgage_property(player, space) else "Hypothèque impossible.")


def main() -> None:
    """Lance une partie interactive de démonstration dans le terminal.

    Entrées:
        Aucune. Deux joueurs de démonstration sont créés directement.

    Sortie:
        None: La boucle se poursuit jusqu'à ce qu'un seul joueur reste actif.
    """
    game = Game(["Alice", "Bob"])
    print("=== Monopoly POO V3 — mode console ===")

    while not game.is_over:
        player = game.current_player
        print(f"\n--- Tour de {player.name} ---")

        jail_action = choose_jail_action(game, player) if player.in_jail else "roll"
        result = game.take_turn(jail_action=jail_action)

        print(f"Dés : {result.dice[0]} + {result.dice[1]}")
        if result.rolled_double:
            print("Double !")
        if result.passed_go:
            print("+200 pour passage par Départ.")

        print(f"Case finale : {result.landed_space_name}")
        print(result.message)
        print_player_state(result.player)

        if result.player.bankrupt:
            print(f"{result.player.name} est en faillite.")
            continue

        space = game.board.get_player_space(result.player)
        if isinstance(space, OwnableSpace) and space.owner is None:
            offer_property_purchase(game, result.player, space)

        offer_property_management(game, result.player)

    winner = game.winner
    if winner:
        print(f"\nVictoire de {winner.name} !")


if __name__ == "__main__":
    main()
