"""Définit le plateau, ses 40 cases et les opérations liées aux groupes de couleur."""

from __future__ import annotations

from .player import Player
from .properties import OwnableSpace, Property, Railroad, Utility
from .spaces import (
    ChanceSpace,
    CommunityChestSpace,
    FreeParkingSpace,
    GoSpace,
    GoToJailSpace,
    JailSpace,
    Space,
    TaxSpace,
)


class Board:
    """Contient l'ensemble des cases du plateau et les recherches associées.

    Entrées:
        spaces (list[Space | OwnableSpace]): Liste ordonnée des 40 cases du plateau.

    Sortie:
        Board: Un plateau indexable capable de retrouver les cases et les groupes.
    """

    SIZE = 40

    def __init__(self, spaces: list[Space | OwnableSpace]) -> None:
        """Initialise un plateau et vérifie qu'il possède exactement 40 cases.

        Entrées:
            spaces (list[Space | OwnableSpace]): Cases du plateau dans l'ordre de jeu.

        Sortie:
            None: Le constructeur stocke les cases dans l'instance.

        Lève:
            ValueError: Si le nombre de cases est différent de ``Board.SIZE``.
        """
        if len(spaces) != self.SIZE:
            raise ValueError(f"Le plateau doit contenir {self.SIZE} cases.")
        self.spaces = spaces

    def __len__(self) -> int:
        """Retourne le nombre de cases présentes sur le plateau.

        Entrées:
            Aucune autre que l'instance courante.

        Sortie:
            int: Nombre total de cases du plateau.
        """
        return len(self.spaces)

    def __getitem__(self, index: int) -> Space | OwnableSpace:
        """Permet d'accéder à une case avec la syntaxe ``board[index]``.

        Entrées:
            index (int): Index de la case recherchée.

        Sortie:
            Space | OwnableSpace: Case située à l'index demandé.
        """
        return self.spaces[index]

    def get_space(self, index: int) -> Space | OwnableSpace:
        """Retourne explicitement une case du plateau par son index.

        Entrées:
            index (int): Position de la case recherchée.

        Sortie:
            Space | OwnableSpace: Case correspondant à l'index.
        """
        return self.spaces[index]

    def get_player_space(self, player: Player) -> Space | OwnableSpace:
        """Retourne la case actuellement occupée par un joueur.

        Entrées:
            player (Player): Joueur dont on veut connaître la case.

        Sortie:
            Space | OwnableSpace: Case située à ``player.position``.
        """
        return self.spaces[player.position]

    def spaces_in_group(self, color_group: str) -> list[Property]:
        """Liste tous les terrains appartenant à un groupe de couleur.

        Entrées:
            color_group (str): Identifiant interne du groupe de couleur.

        Sortie:
            list[Property]: Terrains du groupe demandé, dans l'ordre du plateau.
        """
        return [
            space
            for space in self.spaces
            if isinstance(space, Property) and space.color_group == color_group
        ]

    def player_owns_group(self, player: Player, color_group: str) -> bool:
        """Vérifie si un joueur possède tous les terrains d'un groupe de couleur.

        Entrées:
            player (Player): Joueur dont les possessions sont contrôlées.
            color_group (str): Groupe de couleur à vérifier.

        Sortie:
            bool: ``True`` si le groupe existe et que tous ses terrains appartiennent
            au joueur, sinon ``False``.
        """
        group = self.spaces_in_group(color_group)
        return bool(group) and all(space.owner is player for space in group)

    def find_next_space_of_type(self, start_index: int, space_type: type) -> int:
        """Recherche la prochaine case correspondant à un type donné en bouclant le plateau.

        Entrées:
            start_index (int): Position à partir de laquelle commencer la recherche.
            space_type (type): Classe de case recherchée, par exemple ``Railroad``.

        Sortie:
            int: Index de la première case du type demandé rencontrée après le départ.

        Lève:
            LookupError: Si aucune case du type demandé n'existe sur le plateau.
        """
        for offset in range(1, len(self.spaces) + 1):
            index = (start_index + offset) % len(self.spaces)
            if isinstance(self.spaces[index], space_type):
                return index
        raise LookupError(f"Aucune case du type {space_type!r} sur le plateau.")

    @classmethod
    def standard(cls) -> "Board":
        """Construit le plateau standard utilisé par cette version du moteur.

        Entrées:
            Aucune. La méthode utilise les données de plateau définies dans son corps.

        Sortie:
            Board: Nouveau plateau de 40 cases avec propriétés, gares, compagnies
            et cases spéciales préconfigurées.
        """
        def prop(
            index: int,
            name: str,
            price: int,
            rent: int,
            group: str,
            house_cost: int,
            house_rents: tuple[int, int, int, int],
            hotel_rent: int,
        ) -> Property:
            """Crée un terrain standardisé pour alléger la définition du plateau.

            Entrées:
                index (int): Position du terrain sur le plateau.
                name (str): Nom affiché du terrain.
                price (int): Prix d'achat.
                rent (int): Loyer de base.
                group (str): Groupe de couleur.
                house_cost (int): Prix d'une maison.
                house_rents (tuple[int, int, int, int]): Loyers pour 1 à 4 maisons.
                hotel_rent (int): Loyer avec hôtel.

            Sortie:
                Property: Terrain configuré avec les valeurs fournies.
            """
            return Property(
                index=index,
                name=name,
                price=price,
                color_group=group,
                base_rent=rent,
                house_cost=house_cost,
                house_rents=house_rents,
                hotel_rent=hotel_rent,
            )

        spaces: list[Space | OwnableSpace] = [
            GoSpace(0, "Départ"),
            prop(1, "Marron 1", 60, 2, "brown", 50, (10, 30, 90, 160), 250),
            CommunityChestSpace(2, "Caisse de communauté"),
            prop(3, "Marron 2", 60, 4, "brown", 50, (20, 60, 180, 320), 450),
            TaxSpace(4, "Impôt sur le revenu", 200),
            Railroad(5, "Gare 1", 200),
            prop(6, "Bleu clair 1", 100, 6, "light_blue", 50, (30, 90, 270, 400), 550),
            ChanceSpace(7, "Chance"),
            prop(8, "Bleu clair 2", 100, 6, "light_blue", 50, (30, 90, 270, 400), 550),
            prop(9, "Bleu clair 3", 120, 8, "light_blue", 50, (40, 100, 300, 450), 600),
            JailSpace(10, "Prison / Simple visite"),
            prop(11, "Rose 1", 140, 10, "pink", 100, (50, 150, 450, 625), 750),
            Utility(12, "Compagnie 1", 150),
            prop(13, "Rose 2", 140, 10, "pink", 100, (50, 150, 450, 625), 750),
            prop(14, "Rose 3", 160, 12, "pink", 100, (60, 180, 500, 700), 900),
            Railroad(15, "Gare 2", 200),
            prop(16, "Orange 1", 180, 14, "orange", 100, (70, 200, 550, 750), 950),
            CommunityChestSpace(17, "Caisse de communauté"),
            prop(18, "Orange 2", 180, 14, "orange", 100, (70, 200, 550, 750), 950),
            prop(19, "Orange 3", 200, 16, "orange", 100, (80, 220, 600, 800), 1000),
            FreeParkingSpace(20, "Parc Gratuit"),
            prop(21, "Rouge 1", 220, 18, "red", 150, (90, 250, 700, 875), 1050),
            ChanceSpace(22, "Chance"),
            prop(23, "Rouge 2", 220, 18, "red", 150, (90, 250, 700, 875), 1050),
            prop(24, "Rouge 3", 240, 20, "red", 150, (100, 300, 750, 925), 1100),
            Railroad(25, "Gare 3", 200),
            prop(26, "Jaune 1", 260, 22, "yellow", 150, (110, 330, 800, 975), 1150),
            prop(27, "Jaune 2", 260, 22, "yellow", 150, (110, 330, 800, 975), 1150),
            Utility(28, "Compagnie 2", 150),
            prop(29, "Jaune 3", 280, 24, "yellow", 150, (120, 360, 850, 1025), 1200),
            GoToJailSpace(30, "Allez en prison"),
            prop(31, "Vert 1", 300, 26, "green", 200, (130, 390, 900, 1100), 1275),
            prop(32, "Vert 2", 300, 26, "green", 200, (130, 390, 900, 1100), 1275),
            CommunityChestSpace(33, "Caisse de communauté"),
            prop(34, "Vert 3", 320, 28, "green", 200, (150, 450, 1000, 1200), 1400),
            Railroad(35, "Gare 4", 200),
            ChanceSpace(36, "Chance"),
            prop(37, "Bleu foncé 1", 350, 35, "dark_blue", 200, (175, 500, 1100, 1300), 1500),
            TaxSpace(38, "Taxe de luxe", 100),
            prop(39, "Bleu foncé 2", 400, 50, "dark_blue", 200, (200, 600, 1400, 1700), 2000),
        ]
        return cls(spaces)
