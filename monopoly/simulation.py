"""Lance et analyse des campagnes de parties neutres sans stratégie."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
import csv
import json
import multiprocessing
import os
from pathlib import Path
import random
from statistics import mean, median, pstdev
from typing import Callable

from .board_config import BoardConfig
from .game import Game
from .options import GameOptions
from .profile_packs import ProfilePack
from .properties import OwnableSpace, Property
from .statistics import GameStatistics


UNLIMITED_ACTION_WATCHDOG = 20_000


@dataclass
class SimulationScenario:
    """Associe un profil de règles et un plateau pour une campagne de simulation.

    Entrées:
        name (str): Nom lisible du scénario comparé.
        options (GameOptions): Règles utilisées pour chaque partie.
        board_config (BoardConfig): Plateau et cartes utilisés.

    Sortie:
        SimulationScenario: Configuration indépendante et clonable.
    """

    name: str
    options: GameOptions = field(default_factory=GameOptions.classic)
    board_config: BoardConfig = field(default_factory=BoardConfig.standard)

    def clone(self) -> "SimulationScenario":
        """Crée une copie profonde du scénario.

        Entrées:
            Aucune.

        Sortie:
            SimulationScenario: Copie indépendante des règles et du plateau.
        """
        return SimulationScenario(
            self.name,
            GameOptions.from_dict(self.options.to_dict()),
            self.board_config.clone(),
        )

    @classmethod
    def standard(cls) -> "SimulationScenario":
        """Construit le scénario Monopoly classique par défaut.

        Entrées:
            Aucune.

        Sortie:
            SimulationScenario: Règles classiques et plateau standard.
        """
        return cls("Classique", GameOptions.classic(), BoardConfig.standard())

    @classmethod
    def from_profile_pack(cls, pack: ProfilePack) -> "SimulationScenario":
        """Construit un scénario à partir d'un pack complet V20.

        Entrées:
            pack (ProfilePack): Pack règles + plateau déjà validé.

        Sortie:
            SimulationScenario: Copie indépendante du pack.
        """
        return cls(
            pack.name,
            GameOptions.from_dict(pack.options.to_dict()),
            pack.board_config.clone(),
        )

    def summary(self) -> str:
        """Produit un résumé compact du scénario.

        Entrées:
            Aucune.

        Sortie:
            str: Nom, règles et plateau.
        """
        return f"{self.name} • {self.options.summary()} • {self.board_config.summary()}"

    def to_dict(self) -> dict[str, object]:
        """Sérialise le scénario pour rendre un rapport rechargeable.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Nom, règles et plateau complet.
        """
        return {
            "name": self.name,
            "options": self.options.to_dict(),
            "board_config": self.board_config.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SimulationScenario":
        """Reconstruit un scénario sérialisé dans un rapport de laboratoire.

        Entrées:
            data (dict[str, object]): Dictionnaire contenant nom, règles et plateau.

        Sortie:
            SimulationScenario: Scénario indépendant prêt pour affichage ou relance.
        """
        return cls(
            str(data.get("name", "Scénario")),
            GameOptions.from_dict(data.get("options") if isinstance(data.get("options"), dict) else None),
            BoardConfig.from_dict(data.get("board_config") if isinstance(data.get("board_config"), dict) else BoardConfig.standard().to_dict()),
        )


def resolve_base_seed(
    value: str | int | None,
    random_source: random.Random | None = None,
) -> int:
    """Résout une seed saisie ou en génère une lorsqu'elle est vide.

    Entrées:
        value (str | int | None): Seed explicite ou texte vide.
        random_source (random.Random | None): Générateur injectable pour les tests.

    Sortie:
        int: Seed entière effectivement utilisée par toute la campagne.

    Lève:
        ValueError: Si une valeur non vide n'est pas un entier valide.
    """
    if isinstance(value, int):
        return value
    text = "" if value is None else str(value).strip()
    if text:
        try:
            return int(text)
        except ValueError as error:
            raise ValueError("La seed doit être un entier ou rester vide.") from error
    if random_source is not None:
        return random_source.randint(0, 2_147_483_647)
    return random.SystemRandom().randint(0, 2_147_483_647)


@dataclass(frozen=True)
class SimulationConfig:
    """Décrit la taille et les garde-fous d'une campagne.

    Entrées:
        games_per_scenario (int): Nombre de parties pour chaque scénario.
        player_count (int): Nombre de joueurs neutres par partie.
        max_rounds (int): Limite de tours ; ``0`` active le mode sans limite de tours.
        base_seed (int): Première graine utilisée pour les parties reproductibles.
        parallel_workers (int): Nombre de processus de calcul ; ``0`` choisit automatiquement.

    Sortie:
        SimulationConfig: Paramètres validables d'une campagne.
    """

    games_per_scenario: int = 100
    player_count: int = 4
    max_rounds: int = 250
    base_seed: int = 12345
    parallel_workers: int = 1

    def validate(self) -> None:
        """Vérifie les bornes raisonnables du laboratoire.

        Entrées:
            Aucune.

        Sortie:
            None: La configuration est valide.

        Lève:
            ValueError: Si une valeur sort des bornes supportées.
        """
        if not 1 <= self.games_per_scenario <= 10000:
            raise ValueError("Le nombre de parties doit être compris entre 1 et 10000.")
        if not 2 <= self.player_count <= 4:
            raise ValueError("Le nombre de joueurs doit être compris entre 2 et 4.")
        if not 0 <= self.max_rounds <= 10000:
            raise ValueError("La limite de tours doit être comprise entre 0 et 10000 ; 0 signifie illimité.")
        if not 0 <= self.parallel_workers <= 32:
            raise ValueError("Le nombre de processus doit être compris entre 0 (auto) et 32.")


@dataclass(frozen=True)
class SimulationGameResult:
    """Résume une seule partie simulée.

    Entrées:
        seed (int): Graine exacte de la partie.
        rounds (int): Tours de table complètement terminés.
        actions (int): Actions de dés exécutées, doubles compris.
        winner_name (str | None): Vainqueur naturel ou leader déterminé au cutoff.
        finished (bool): Fin obtenue par les règles de la partie.
        truncated (bool): Arrêt par garde-fou du laboratoire.
        stop_reason (str): Cause exacte de fin ou de cutoff.
        bankruptcies (int): Faillites enregistrées.
        rent_transferred (int): Loyers cumulés.
        buildings_built (int): Bâtiments construits.
        jail_visits (int): Entrées en prison.
        free_parking_peak (int): Pic de cagnotte Parc Gratuit.
        final_net_worth (dict[str, int]): Patrimoine final par siège de joueur.
        property_rent (dict[str, int]): Loyers cumulés par propriété.

    Sortie:
        SimulationGameResult: Ligne détaillée exploitable par agrégation ou export.
    """

    seed: int
    rounds: int
    actions: int
    winner_name: str | None
    finished: bool
    truncated: bool
    stop_reason: str
    bankruptcies: int
    rent_transferred: int
    buildings_built: int
    jail_visits: int
    free_parking_peak: int
    final_net_worth: dict[str, int]
    property_rent: dict[str, int]
    property_rent_events: dict[str, int] = field(default_factory=dict)
    property_biggest_rent: dict[str, int] = field(default_factory=dict)
    cards_drawn: int = 0
    purchases: int = 0
    auctions_won: int = 0
    mortgages: int = 0
    biggest_rent: int = 0
    free_parking_collected: int = 0
    final_cash: dict[str, int] = field(default_factory=dict)
    final_property_count: dict[str, int] = field(default_factory=dict)
    rent_paid_by_player: dict[str, int] = field(default_factory=dict)
    rent_received_by_player: dict[str, int] = field(default_factory=dict)
    bankrupt_by_player: dict[str, bool] = field(default_factory=dict)
    jail_visits_by_player: dict[str, int] = field(default_factory=dict)
    winner_at_cutoff: bool = False
    space_names: dict[int, str] = field(default_factory=dict)
    space_landings: dict[int, int] = field(default_factory=dict)
    property_investment: dict[int, int] = field(default_factory=dict)
    property_rent_by_index: dict[int, int] = field(default_factory=dict)
    property_level_rent: dict[int, dict[int, int]] = field(default_factory=dict)
    property_level_rent_events: dict[int, dict[int, int]] = field(default_factory=dict)
    property_level_investment: dict[int, dict[int, int]] = field(default_factory=dict)
    card_metrics: dict[str, dict[str, object]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Sérialise le résultat d'une partie.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Structure JSON portable.
        """
        return {
            "seed": self.seed,
            "rounds": self.rounds,
            "actions": self.actions,
            "winner_name": self.winner_name,
            "finished": self.finished,
            "truncated": self.truncated,
            "stop_reason": self.stop_reason,
            "bankruptcies": self.bankruptcies,
            "rent_transferred": self.rent_transferred,
            "buildings_built": self.buildings_built,
            "jail_visits": self.jail_visits,
            "free_parking_peak": self.free_parking_peak,
            "final_net_worth": dict(self.final_net_worth),
            "property_rent": dict(self.property_rent),
            "property_rent_events": dict(self.property_rent_events),
            "property_biggest_rent": dict(self.property_biggest_rent),
            "cards_drawn": self.cards_drawn,
            "purchases": self.purchases,
            "auctions_won": self.auctions_won,
            "mortgages": self.mortgages,
            "biggest_rent": self.biggest_rent,
            "free_parking_collected": self.free_parking_collected,
            "final_cash": dict(self.final_cash),
            "final_property_count": dict(self.final_property_count),
            "rent_paid_by_player": dict(self.rent_paid_by_player),
            "rent_received_by_player": dict(self.rent_received_by_player),
            "bankrupt_by_player": dict(self.bankrupt_by_player),
            "jail_visits_by_player": dict(self.jail_visits_by_player),
            "winner_at_cutoff": self.winner_at_cutoff,
            "space_names": dict(self.space_names),
            "space_landings": dict(self.space_landings),
            "property_investment": dict(self.property_investment),
            "property_rent_by_index": dict(self.property_rent_by_index),
            "property_level_rent": {
                str(index): dict(levels)
                for index, levels in self.property_level_rent.items()
            },
            "property_level_rent_events": {
                str(index): dict(levels)
                for index, levels in self.property_level_rent_events.items()
            },
            "property_level_investment": {
                str(index): dict(levels)
                for index, levels in self.property_level_investment.items()
            },
            "card_metrics": {
                key: dict(value) for key, value in self.card_metrics.items()
            },
        }


@dataclass(frozen=True)
class SpaceSimulationSummary:
    """Agrège la fréquentation d'une case sur une campagne.

    Entrées:
        index (int): Position de la case sur le plateau.
        name (str): Nom de la case.
        total_landings (int): Nombre total d'arrêts/résolutions observés.
        games (int): Nombre de parties de la campagne.
        all_landings (int): Nombre total d'arrêts enregistrés sur toutes les cases.

    Sortie:
        SpaceSimulationSummary: Fréquentation moyenne et part des arrêts.
    """

    index: int
    name: str
    total_landings: int
    games: int
    all_landings: int

    @property
    def average_landings_per_game(self) -> float:
        """Calcule le nombre moyen d'arrêts sur cette case par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Arrêts moyens par partie.
        """
        return self.total_landings / self.games if self.games else 0.0

    @property
    def landing_share_percent(self) -> float:
        """Calcule la part de cette case parmi tous les arrêts enregistrés.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage d'arrêts attribué à cette case.
        """
        return (
            100.0 * self.total_landings / self.all_landings
            if self.all_landings
            else 0.0
        )

    def to_dict(self) -> dict[str, object]:
        """Sérialise les indicateurs de fréquentation.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Données exportables.
        """
        return {
            "index": self.index,
            "name": self.name,
            "total_landings": self.total_landings,
            "average_landings_per_game": self.average_landings_per_game,
            "landing_share_percent": self.landing_share_percent,
        }


@dataclass(frozen=True)
class PropertyInvestmentSummary:
    """Compare l'argent investi et les loyers générés par un bien.

    Entrées:
        index (int): Position du bien.
        name (str): Nom du bien.
        total_investment (int): Achats/enchères/constructions cumulés.
        total_rent (int): Loyers cumulés.
        total_landings (int): Arrêts cumulés sur la case.
        games (int): Nombre de parties de campagne.

    Sortie:
        PropertyInvestmentSummary: Rendement brut et efficacité par arrêt.
    """

    index: int
    name: str
    total_investment: int
    total_rent: int
    total_landings: int
    games: int

    @property
    def roi_percent(self) -> float:
        """Calcule ``loyers / investissement × 100``.

        Entrées:
            Aucune.

        Sortie:
            float: Rendement brut en pourcentage, zéro sans investissement.
        """
        return 100.0 * self.total_rent / self.total_investment if self.total_investment else 0.0

    @property
    def net_return(self) -> int:
        """Calcule loyers moins investissement brut.

        Entrées:
            Aucune.

        Sortie:
            int: Solde brut historique du bien.
        """
        return self.total_rent - self.total_investment

    @property
    def average_investment_per_game(self) -> float:
        """Calcule l'investissement moyen par partie de campagne.

        Entrées:
            Aucune.

        Sortie:
            float: Argent investi moyen.
        """
        return self.total_investment / self.games if self.games else 0.0

    @property
    def rent_per_landing(self) -> float:
        """Calcule les loyers générés par arrêt observé sur la case.

        Entrées:
            Aucune.

        Sortie:
            float: Loyer historique moyen par arrêt, tous états confondus.
        """
        return self.total_rent / self.total_landings if self.total_landings else 0.0

    def to_dict(self) -> dict[str, object]:
        """Sérialise investissement, gains et rendement.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Données exportables.
        """
        return {
            "index": self.index,
            "name": self.name,
            "total_investment": self.total_investment,
            "total_rent": self.total_rent,
            "roi_percent": self.roi_percent,
            "net_return": self.net_return,
            "average_investment_per_game": self.average_investment_per_game,
            "total_landings": self.total_landings,
            "rent_per_landing": self.rent_per_landing,
        }


@dataclass(frozen=True)
class PropertyDevelopmentSummary:
    """Mesure le rendement d'un terrain pour un niveau de construction précis.

    Entrées:
        property_index (int): Position du terrain.
        property_name (str): Nom du terrain.
        level (int): Niveau 0 à 4 maisons ou 5 pour hôtel.
        total_rent (int): Loyers produits pendant ce niveau.
        total_investment_basis (int): Capital cumulé observé lors de l'atteinte du niveau.
        rent_events (int): Nombre d'événements de loyer à ce niveau.
        reached_count (int): Nombre de fois où ce niveau a été atteint dans les parties.

    Sortie:
        PropertyDevelopmentSummary: Rendement historique par niveau.
    """

    property_index: int
    property_name: str
    level: int
    total_rent: int
    total_investment_basis: int
    rent_events: int
    reached_count: int

    @property
    def level_label(self) -> str:
        """Retourne un libellé lisible pour le niveau de développement.

        Entrées:
            Aucune.

        Sortie:
            str: ``0 maison`` à ``4 maisons`` ou ``Hôtel``.
        """
        if self.level == 5:
            return "Hôtel"
        if self.level == 1:
            return "1 maison"
        return f"{self.level} maisons"

    @property
    def roi_percent(self) -> float:
        """Calcule le rendement du niveau par rapport au capital historique associé.

        Entrées:
            Aucune.

        Sortie:
            float: ``loyers / base d'investissement × 100``.
        """
        if self.total_investment_basis <= 0:
            return 0.0
        return 100.0 * self.total_rent / self.total_investment_basis

    @property
    def average_rent_per_event(self) -> float:
        """Calcule le loyer moyen payé à ce niveau.

        Entrées:
            Aucune.

        Sortie:
            float: Loyer moyen par événement.
        """
        return self.total_rent / self.rent_events if self.rent_events else 0.0

    def to_dict(self) -> dict[str, object]:
        """Sérialise le rendement du niveau de construction.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Données exportables.
        """
        return {
            "property_index": self.property_index,
            "property_name": self.property_name,
            "level": self.level,
            "level_label": self.level_label,
            "total_rent": self.total_rent,
            "total_investment_basis": self.total_investment_basis,
            "rent_events": self.rent_events,
            "reached_count": self.reached_count,
            "roi_percent": self.roi_percent,
            "average_rent_per_event": self.average_rent_per_event,
        }


@dataclass(frozen=True)
class PropertySimulationSummary:
    """Agrège la rentabilité d'un bien sur une campagne.

    Entrées:
        name (str): Nom de la propriété.
        total_rent (int): Loyers cumulés sur toutes les parties.
        games_with_rent (int): Parties où le bien a produit au moins un loyer.
        average_rent_per_game (float): Loyer moyen par partie de campagne.

    Sortie:
        PropertySimulationSummary: Indicateur de rentabilité multi-parties.
    """

    name: str
    total_rent: int
    games_with_rent: int
    average_rent_per_game: float
    total_rent_events: int = 0
    biggest_rent: int = 0

    @property
    def average_rent_per_event(self) -> float:
        """Calcule le loyer moyen lorsque le bien produit effectivement un loyer.

        Entrées:
            Aucune.

        Sortie:
            float: Montant moyen par événement de loyer.
        """
        if self.total_rent_events <= 0:
            return 0.0
        return self.total_rent / self.total_rent_events

    def to_dict(self) -> dict[str, object]:
        """Sérialise l'indicateur de propriété.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Données JSON simples.
        """
        return {
            "name": self.name,
            "total_rent": self.total_rent,
            "games_with_rent": self.games_with_rent,
            "average_rent_per_game": self.average_rent_per_game,
            "total_rent_events": self.total_rent_events,
            "average_rent_per_event": self.average_rent_per_event,
            "biggest_rent": self.biggest_rent,
        }


@dataclass(frozen=True)
class PlayerSimulationSummary:
    """Agrège les résultats d'un siège de joueur sur toute une campagne.

    Entrées:
        name (str): Nom neutre du siège.
        games (int): Nombre de parties observées.
        wins (int): Victoires du siège.
        bankruptcies (int): Parties terminées en faillite pour ce siège.
        average_final_cash (float): Cash final moyen.
        average_final_net_worth (float): Patrimoine final moyen.
        average_final_properties (float): Nombre moyen de biens finaux.
        average_rent_paid (float): Loyers moyens payés par partie.
        average_rent_received (float): Loyers moyens reçus par partie.
        average_jail_visits (float): Passages en prison moyens par partie.

    Sortie:
        PlayerSimulationSummary: Profil statistique d'un siège, sans stratégie.
    """

    name: str
    games: int
    wins: int
    bankruptcies: int
    average_final_cash: float
    average_final_net_worth: float
    average_final_properties: float
    average_rent_paid: float
    average_rent_received: float
    average_jail_visits: float
    finished_games: int = 0
    finished_wins: int = 0
    cutoff_leads: int = 0

    @property
    def win_rate(self) -> float:
        """Retourne le taux de première place sur toutes les simulations.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage de parties où le siège est vainqueur naturel ou
            leader déterministe au moment d'un cutoff. Les sièges totalisent 100 %.
        """
        return 100.0 * self.wins / self.games if self.games else 0.0

    @property
    def finished_win_rate(self) -> float:
        """Retourne le taux de victoire parmi les seules parties naturellement finies.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage de victoires réelles parmi les parties finies.
        """
        if self.finished_games <= 0:
            return 0.0
        return 100.0 * self.finished_wins / self.finished_games

    @property
    def bankruptcy_rate(self) -> float:
        """Retourne le taux de faillite du siège en pourcentage.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage de parties terminées en faillite.
        """
        return 100.0 * self.bankruptcies / self.games if self.games else 0.0

    def to_dict(self) -> dict[str, object]:
        """Sérialise le profil statistique du siège.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Données primitives exportables.
        """
        return {
            "name": self.name,
            "games": self.games,
            "wins": self.wins,
            "win_rate": self.win_rate,
            "bankruptcies": self.bankruptcies,
            "bankruptcy_rate": self.bankruptcy_rate,
            "average_final_cash": self.average_final_cash,
            "average_final_net_worth": self.average_final_net_worth,
            "average_final_properties": self.average_final_properties,
            "average_rent_paid": self.average_rent_paid,
            "average_rent_received": self.average_rent_received,
            "average_jail_visits": self.average_jail_visits,
            "finished_games": self.finished_games,
            "finished_wins": self.finished_wins,
            "finished_win_rate": self.finished_win_rate,
            "cutoff_leads": self.cutoff_leads,
        }



@dataclass(frozen=True)
class CardSimulationSummary:
    """Agrège les effets observés d'une carte sur une campagne neutre.

    Entrées:
        deck (str): Paquet interne, ``chance`` ou ``community_chest``.
        card_type (str): Classe concrète de la carte.
        card_text (str): Texte lisible de la carte.
        draws (int): Nombre total de tirages.
        games_with_draw (int): Parties où la carte est sortie au moins une fois.
        games (int): Nombre total de parties de la campagne.
        deck_draws (int): Nombre total de tirages du paquet concerné.
        drawer_cash_delta (int): Variation nette cumulée du joueur qui pioche.
        other_players_cash_delta (int): Variation cumulée des autres joueurs.
        total_player_cash_delta (int): Variation cumulée de tout le cash joueur.
        free_parking_pot_delta (int): Variation cumulée de cagnotte provoquée.
        movements (int): Tirages ayant changé la position du joueur.
        jail_sends (int): Tirages ayant envoyé le joueur en prison.
        get_out_cards (int): Cartes Sortie de prison effectivement reçues.
        biggest_gain (int): Plus grand gain net observé sur un tirage.
        biggest_loss (int): Plus grande perte nette absolue observée sur un tirage.

    Sortie:
        CardSimulationSummary: Ligne statistique exploitable par l'UI et les exports.
    """

    deck: str
    card_type: str
    card_text: str
    draws: int
    games_with_draw: int
    games: int
    deck_draws: int
    drawer_cash_delta: int
    other_players_cash_delta: int
    total_player_cash_delta: int
    free_parking_pot_delta: int
    movements: int
    jail_sends: int
    get_out_cards: int
    biggest_gain: int
    biggest_loss: int

    @property
    def average_draws_per_game(self) -> float:
        """Calcule le nombre moyen de tirages de cette carte par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Tirages moyens par partie.
        """
        return self.draws / self.games if self.games else 0.0

    @property
    def deck_share_percent(self) -> float:
        """Calcule la part de cette carte parmi les tirages de son paquet.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage des tirages du paquet.
        """
        return 100.0 * self.draws / self.deck_draws if self.deck_draws else 0.0

    @property
    def average_drawer_cash_delta(self) -> float:
        """Calcule l'impact cash moyen sur le joueur qui pioche.

        Entrées:
            Aucune.

        Sortie:
            float: Gain positif ou perte négative moyenne par tirage.
        """
        return self.drawer_cash_delta / self.draws if self.draws else 0.0

    @property
    def average_other_players_cash_delta(self) -> float:
        """Calcule l'impact cash moyen sur les autres joueurs.

        Entrées:
            Aucune.

        Sortie:
            float: Variation moyenne cumulée des autres joueurs par tirage.
        """
        return self.other_players_cash_delta / self.draws if self.draws else 0.0

    @property
    def movement_rate(self) -> float:
        """Calcule la fréquence des déplacements provoqués par la carte.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage de tirages changeant la position.
        """
        return 100.0 * self.movements / self.draws if self.draws else 0.0

    @property
    def jail_rate(self) -> float:
        """Calcule la fréquence d'envoi en prison.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage de tirages envoyant en prison.
        """
        return 100.0 * self.jail_sends / self.draws if self.draws else 0.0

    @property
    def get_out_rate(self) -> float:
        """Calcule la fréquence d'obtention d'une carte Sortie de prison.

        Entrées:
            Aucune.

        Sortie:
            float: Pourcentage de tirages donnant une carte conservable.
        """
        return 100.0 * self.get_out_cards / self.draws if self.draws else 0.0

    @property
    def average_pot_delta(self) -> float:
        """Calcule la contribution moyenne à la cagnotte Parc Gratuit.

        Entrées:
            Aucune.

        Sortie:
            float: Variation moyenne de cagnotte par tirage.
        """
        return self.free_parking_pot_delta / self.draws if self.draws else 0.0

    def to_dict(self) -> dict[str, object]:
        """Sérialise les métriques calculées de la carte.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Ligne JSON complète.
        """
        return {
            "deck": self.deck,
            "card_type": self.card_type,
            "card_text": self.card_text,
            "draws": self.draws,
            "games_with_draw": self.games_with_draw,
            "average_draws_per_game": self.average_draws_per_game,
            "deck_share_percent": self.deck_share_percent,
            "drawer_cash_delta": self.drawer_cash_delta,
            "average_drawer_cash_delta": self.average_drawer_cash_delta,
            "other_players_cash_delta": self.other_players_cash_delta,
            "average_other_players_cash_delta": self.average_other_players_cash_delta,
            "total_player_cash_delta": self.total_player_cash_delta,
            "free_parking_pot_delta": self.free_parking_pot_delta,
            "average_pot_delta": self.average_pot_delta,
            "movements": self.movements,
            "movement_rate": self.movement_rate,
            "jail_sends": self.jail_sends,
            "jail_rate": self.jail_rate,
            "get_out_cards": self.get_out_cards,
            "get_out_rate": self.get_out_rate,
            "biggest_gain": self.biggest_gain,
            "biggest_loss": self.biggest_loss,
        }


@dataclass
class SimulationCampaignResult:
    """Agrège toutes les parties d'un même scénario.

    Entrées:
        scenario_name (str): Nom du scénario.
        config (SimulationConfig): Paramètres communs de campagne.
        games (list[SimulationGameResult]): Résultats détaillés.
        property_summary (list[PropertySimulationSummary]): Rentabilité agrégée.

    Sortie:
        SimulationCampaignResult: Résumé et détails d'un scénario simulé.
    """

    scenario_name: str
    config: SimulationConfig
    games: list[SimulationGameResult] = field(default_factory=list)
    property_summary: list[PropertySimulationSummary] = field(default_factory=list)
    player_summary: list[PlayerSimulationSummary] = field(default_factory=list)
    space_summary: list[SpaceSimulationSummary] = field(default_factory=list)
    property_investment_summary: list[PropertyInvestmentSummary] = field(default_factory=list)
    property_development_summary: list[PropertyDevelopmentSummary] = field(default_factory=list)
    card_summary: list[CardSimulationSummary] = field(default_factory=list)

    @property
    def finished_games(self) -> int:
        """Compte les parties terminées par leurs propres règles.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de parties non tronquées.
        """
        return sum(game.finished for game in self.games)

    @property
    def truncated_games(self) -> int:
        """Compte les parties arrêtées par le garde-fou de simulation.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de parties anormalement longues ou non terminées.
        """
        return sum(game.truncated for game in self.games)

    def stop_reason_count(self, reason: str) -> int:
        """Compte les parties terminées pour une cause précise.

        Entrées:
            reason (str): Identifiant de cause, par exemple ``action_watchdog``.

        Sortie:
            int: Nombre de parties correspondant à cette cause.
        """
        return sum(game.stop_reason == reason for game in self.games)


    @property
    def action_watchdog_games(self) -> int:
        """Compte les arrêts déclenchés par le watchdog technique d'actions.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de cutoffs techniques extrêmes.
        """
        return self.stop_reason_count("action_watchdog")

    @property
    def round_limit_games(self) -> int:
        """Compte les arrêts dus à la limite explicite de tours.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de cutoffs par tours max.
        """
        return self.stop_reason_count("round_limit")

    @property
    def average_rounds(self) -> float:
        """Calcule la durée moyenne en tours de table.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne arrondie implicitement par l'affichage.
        """
        return mean([game.rounds for game in self.games]) if self.games else 0.0

    @property
    def median_rounds(self) -> float:
        """Calcule la médiane de durée des parties.

        Entrées:
            Aucune.

        Sortie:
            float: Médiane des tours de table.
        """
        return float(median([game.rounds for game in self.games])) if self.games else 0.0

    @property
    def average_bankruptcies(self) -> float:
        """Calcule le nombre moyen de faillites par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des faillites.
        """
        return mean([game.bankruptcies for game in self.games]) if self.games else 0.0

    @property
    def average_rent(self) -> float:
        """Calcule les loyers moyens transférés par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des loyers cumulés.
        """
        return mean([game.rent_transferred for game in self.games]) if self.games else 0.0

    @property
    def average_jail_visits(self) -> float:
        """Calcule les passages en prison moyens par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des entrées en prison.
        """
        return mean([game.jail_visits for game in self.games]) if self.games else 0.0

    @property
    def average_buildings(self) -> float:
        """Calcule le nombre moyen de constructions par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des bâtiments construits.
        """
        return mean([game.buildings_built for game in self.games]) if self.games else 0.0

    @property
    def average_free_parking_peak(self) -> float:
        """Calcule le pic moyen de cagnotte Parc Gratuit.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des pics observés.
        """
        return mean([game.free_parking_peak for game in self.games]) if self.games else 0.0

    @property
    def finish_rate(self) -> float:
        """Calcule le pourcentage de parties terminées sans garde-fou.

        Entrées:
            Aucune.

        Sortie:
            float: Taux de fin compris entre zéro et cent.
        """
        return 100.0 * self.finished_games / len(self.games) if self.games else 0.0

    @property
    def average_actions(self) -> float:
        """Calcule le nombre moyen d'actions de dés par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des actions exécutées.
        """
        return mean([game.actions for game in self.games]) if self.games else 0.0

    @property
    def median_actions(self) -> float:
        """Calcule la médiane du nombre d'actions par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Médiane des actions.
        """
        return float(median([game.actions for game in self.games])) if self.games else 0.0

    @property
    def round_stddev(self) -> float:
        """Mesure la dispersion des durées de parties en tours.

        Entrées:
            Aucune.

        Sortie:
            float: Écart-type population des tours de table.
        """
        values = [game.rounds for game in self.games]
        return pstdev(values) if len(values) >= 2 else 0.0

    def round_percentile(self, percentile: float) -> float:
        """Calcule un percentile linéaire de la durée des parties.

        Entrées:
            percentile (float): Quantile demandé entre zéro et cent.

        Sortie:
            float: Nombre de tours interpolé au percentile demandé.
        """
        if not self.games:
            return 0.0
        values = sorted(game.rounds for game in self.games)
        if len(values) == 1:
            return float(values[0])
        ratio = min(100.0, max(0.0, percentile)) / 100.0
        position = ratio * (len(values) - 1)
        lower = int(position)
        upper = min(len(values) - 1, lower + 1)
        fraction = position - lower
        return values[lower] * (1.0 - fraction) + values[upper] * fraction

    @property
    def average_cards_drawn(self) -> float:
        """Calcule le nombre moyen de cartes piochées par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des pioches.
        """
        return mean([game.cards_drawn for game in self.games]) if self.games else 0.0

    @property
    def average_purchases(self) -> float:
        """Calcule le nombre moyen d'achats directs par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des achats.
        """
        return mean([game.purchases for game in self.games]) if self.games else 0.0

    @property
    def average_auctions_won(self) -> float:
        """Calcule le nombre moyen d'enchères immobilières remportées.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des enchères remportées.
        """
        return mean([game.auctions_won for game in self.games]) if self.games else 0.0

    @property
    def average_mortgages(self) -> float:
        """Calcule le nombre moyen d'hypothèques par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des hypothèques.
        """
        return mean([game.mortgages for game in self.games]) if self.games else 0.0

    @property
    def average_free_parking_collected(self) -> float:
        """Calcule le montant moyen réellement récupéré au Parc Gratuit.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne des montants collectés par partie.
        """
        return mean([game.free_parking_collected for game in self.games]) if self.games else 0.0

    @property
    def maximum_single_rent(self) -> int:
        """Retourne le plus gros loyer unique observé dans la campagne.

        Entrées:
            Aucune.

        Sortie:
            int: Montant maximal d'un événement de loyer.
        """
        return max((game.biggest_rent for game in self.games), default=0)

    @property
    def average_recorded_landings(self) -> float:
        """Calcule le nombre moyen d'arrêts/résolutions enregistrés par partie.

        Entrées:
            Aucune.

        Sortie:
            float: Moyenne incluant les déplacements supplémentaires provoqués par cartes.
        """
        total = sum(item.total_landings for item in self.space_summary)
        return total / len(self.games) if self.games else 0.0

    @property
    def global_property_roi_percent(self) -> float:
        """Calcule le rendement brut cumulé de tous les biens achetables.

        Entrées:
            Aucune.

        Sortie:
            float: Loyers cumulés divisés par investissements cumulés, en pourcentage.
        """
        investment = sum(item.total_investment for item in self.property_investment_summary)
        rent = sum(item.total_rent for item in self.property_investment_summary)
        return 100.0 * rent / investment if investment else 0.0

    @property
    def most_landed_space(self) -> str:
        """Retourne la case la plus fréquemment résolue de la campagne.

        Entrées:
            Aucune.

        Sortie:
            str: Nom et index de la case la plus fréquentée.
        """
        if not self.space_summary:
            return "—"
        item = max(self.space_summary, key=lambda value: value.total_landings)
        return f"{item.index} — {item.name}"

    @property
    def best_roi_property(self) -> str:
        """Retourne le bien au meilleur ROI brut parmi ceux avec investissement positif.

        Entrées:
            Aucune.

        Sortie:
            str: Nom et index du meilleur rendement, ou tiret sans données.
        """
        candidates = [
            item for item in self.property_investment_summary
            if item.total_investment > 0
        ]
        if not candidates:
            return "—"
        item = max(candidates, key=lambda value: value.roi_percent)
        return f"{item.index} — {item.name} ({item.roi_percent:.1f} %)"

    def duration_histogram(self, bins: int = 8) -> list[tuple[str, int]]:
        """Répartit les durées de parties dans des classes lisibles.

        Entrées:
            bins (int): Nombre maximal de classes souhaité.

        Sortie:
            list[tuple[str, int]]: Libellé de classe et nombre de parties.
        """
        if not self.games:
            return []
        values = [game.rounds for game in self.games]
        low = min(values)
        high = max(values)
        if low == high:
            return [(str(low), len(values))]
        bins = max(2, min(12, bins))
        width = max(1, (high - low + bins) // bins)
        edges = list(range(low, high + 1, width))
        if edges[-1] <= high:
            edges.append(high + 1)
        counts = [0] * (len(edges) - 1)
        for value in values:
            index = min(len(counts) - 1, max(0, (value - low) // width))
            counts[index] += 1
        result: list[tuple[str, int]] = []
        for index, count in enumerate(counts):
            start = edges[index]
            stop = edges[index + 1] - 1
            label = str(start) if start == stop else f"{start}-{stop}"
            result.append((label, count))
        return result

    @property
    def winner_counts(self) -> dict[str, int]:
        """Compte les victoires par siège de joueur.

        Entrées:
            Aucune.

        Sortie:
            dict[str, int]: Nombre de victoires de chaque nom neutre.
        """
        counts: dict[str, int] = {}
        for game in self.games:
            if game.winner_name is None:
                continue
            counts[game.winner_name] = counts.get(game.winner_name, 0) + 1
        return counts

    def summary_dict(self) -> dict[str, object]:
        """Construit les principaux indicateurs de campagne.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Résumé adapté à l'interface et aux exports.
        """
        return {
            "scenario": self.scenario_name,
            "games": len(self.games),
            "finished": self.finished_games,
            "truncated": self.truncated_games,
            "round_limit_stops": self.round_limit_games,
            "action_watchdog_stops": self.action_watchdog_games,
            "average_rounds": self.average_rounds,
            "median_rounds": self.median_rounds,
            "round_stddev": self.round_stddev,
            "round_p10": self.round_percentile(10),
            "round_p25": self.round_percentile(25),
            "round_p75": self.round_percentile(75),
            "round_p90": self.round_percentile(90),
            "finish_rate": self.finish_rate,
            "average_actions": self.average_actions,
            "median_actions": self.median_actions,
            "average_bankruptcies": self.average_bankruptcies,
            "average_rent": self.average_rent,
            "average_buildings": self.average_buildings,
            "average_jail_visits": self.average_jail_visits,
            "average_free_parking_peak": self.average_free_parking_peak,
            "average_free_parking_collected": self.average_free_parking_collected,
            "average_cards_drawn": self.average_cards_drawn,
            "average_purchases": self.average_purchases,
            "average_auctions_won": self.average_auctions_won,
            "average_mortgages": self.average_mortgages,
            "maximum_single_rent": self.maximum_single_rent,
            "average_recorded_landings": self.average_recorded_landings,
            "global_property_roi_percent": self.global_property_roi_percent,
            "most_landed_space": self.most_landed_space,
            "best_roi_property": self.best_roi_property,
            "winner_counts": self.winner_counts,
        }


    def cards_for_deck(self, deck: str) -> list[CardSimulationSummary]:
        """Retourne les statistiques des cartes d'un paquet précis.

        Entrées:
            deck (str): ``chance`` ou ``community_chest``.

        Sortie:
            list[CardSimulationSummary]: Cartes triées par nombre de tirages.
        """
        items = [item for item in self.card_summary if item.deck == deck]
        return sorted(items, key=lambda item: (item.draws, item.card_text), reverse=True)

    @property
    def chance_draws(self) -> int:
        """Compte les tirages Chance de la campagne.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de tirages Chance.
        """
        return sum(item.draws for item in self.card_summary if item.deck == "chance")

    @property
    def community_draws(self) -> int:
        """Compte les tirages Caisse de communauté de la campagne.

        Entrées:
            Aucune.

        Sortie:
            int: Nombre de tirages Communauté.
        """
        return sum(item.draws for item in self.card_summary if item.deck == "community_chest")

    @property
    def average_card_cash_impact(self) -> float:
        """Calcule l'impact cash moyen de tous les tirages sur le joueur concerné.

        Entrées:
            Aucune.

        Sortie:
            float: Gain ou perte moyenne par carte piochée.
        """
        draws = sum(item.draws for item in self.card_summary)
        total = sum(item.drawer_cash_delta for item in self.card_summary)
        return total / draws if draws else 0.0

    @property
    def total_card_pot_contribution(self) -> int:
        """Additionne les variations de cagnotte provoquées par les cartes.

        Entrées:
            Aucune.

        Sortie:
            int: Contribution nette cumulée à la cagnotte.
        """
        return sum(item.free_parking_pot_delta for item in self.card_summary)

    def to_dict(self) -> dict[str, object]:
        """Sérialise campagne, paramètres, propriétés et parties détaillées.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Structure JSON complète.
        """
        return {
            "scenario": self.scenario_name,
            "config": {
                "games_per_scenario": self.config.games_per_scenario,
                "player_count": self.config.player_count,
                "max_rounds": self.config.max_rounds,
                "base_seed": self.config.base_seed,
                "parallel_workers": self.config.parallel_workers,
            },
            "summary": self.summary_dict(),
            "properties": [item.to_dict() for item in self.property_summary],
            "players": [item.to_dict() for item in self.player_summary],
            "spaces": [item.to_dict() for item in self.space_summary],
            "property_investment": [
                item.to_dict() for item in self.property_investment_summary
            ],
            "property_development": [
                item.to_dict() for item in self.property_development_summary
            ],
            "cards": [item.to_dict() for item in self.card_summary],
            "duration_histogram": [
                {"range": label, "games": count}
                for label, count in self.duration_histogram()
            ],
            "games": [game.to_dict() for game in self.games],
        }


@dataclass
class SimulationComparisonResult:
    """Regroupe plusieurs campagnes pour comparer des presets ou packs.

    Entrées:
        config (SimulationConfig): Paramètres identiques utilisés pour tous les scénarios.
        campaigns (list[SimulationCampaignResult]): Une campagne par scénario.
        scenarios (list[SimulationScenario]): Définitions complètes des scénarios du rapport.

    Sortie:
        SimulationComparisonResult: Comparaison exportable en JSON ou CSV.
    """

    config: SimulationConfig
    campaigns: list[SimulationCampaignResult] = field(default_factory=list)
    scenarios: list[SimulationScenario] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Sérialise toute la comparaison.

        Entrées:
            Aucune.

        Sortie:
            dict[str, object]: Structure complète de comparaison.
        """
        return {
            "format": "monopoly-simulation-report",
            "version": 4,
            "config": {
                "games_per_scenario": self.config.games_per_scenario,
                "player_count": self.config.player_count,
                "max_rounds": self.config.max_rounds,
                "base_seed": self.config.base_seed,
                "parallel_workers": self.config.parallel_workers,
            },
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
            "campaigns": [campaign.to_dict() for campaign in self.campaigns],
        }

    def export_json(self, path: str | Path) -> Path:
        """Exporte le rapport complet au format JSON.

        Entrées:
            path (str | Path): Fichier de destination.

        Sortie:
            Path: Chemin écrit.
        """
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return destination

    def export_csv(self, path: str | Path) -> Path:
        """Exporte une ligne par partie au format CSV tabulaire.

        Entrées:
            path (str | Path): Fichier de destination.

        Sortie:
            Path: Chemin écrit.
        """
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "scenario",
                    "seed",
                    "rounds",
                    "actions",
                    "winner",
                    "winner_at_cutoff",
                    "finished",
                    "truncated",
                    "stop_reason",
                    "bankruptcies",
                    "rent_transferred",
                    "buildings_built",
                    "jail_visits",
                    "free_parking_peak",
                    "free_parking_collected",
                    "cards_drawn",
                    "purchases",
                    "auctions_won",
                    "mortgages",
                    "biggest_rent",
                ]
            )
            for campaign in self.campaigns:
                for game in campaign.games:
                    writer.writerow(
                        [
                            campaign.scenario_name,
                            game.seed,
                            game.rounds,
                            game.actions,
                            game.winner_name or "",
                            int(game.winner_at_cutoff),
                            int(game.finished),
                            int(game.truncated),
                            game.stop_reason,
                            game.bankruptcies,
                            game.rent_transferred,
                            game.buildings_built,
                            game.jail_visits,
                            game.free_parking_peak,
                            game.free_parking_collected,
                            game.cards_drawn,
                            game.purchases,
                            game.auctions_won,
                            game.mortgages,
                            game.biggest_rent,
                        ]
                    )
        return destination

    def export_summary_csv(self, path: str | Path) -> Path:
        """Exporte une ligne synthétique par scénario au format CSV.

        Entrées:
            path (str | Path): Fichier de destination.

        Sortie:
            Path: Chemin écrit avec les principaux indicateurs comparatifs.
        """
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "scenario", "games", "finished", "truncated", "finish_rate",
            "round_limit_stops", "action_watchdog_stops",
            "average_rounds", "median_rounds", "round_stddev", "round_p90",
            "average_actions", "average_bankruptcies", "average_rent",
            "maximum_single_rent", "average_buildings", "average_jail_visits",
            "average_cards_drawn", "average_purchases", "average_auctions_won",
            "average_mortgages", "average_free_parking_peak",
            "average_free_parking_collected", "average_recorded_landings",
            "global_property_roi_percent", "most_landed_space",
            "best_roi_property",
        ]
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for campaign in self.campaigns:
                summary = campaign.summary_dict()
                writer.writerow({field: summary.get(field, "") for field in fields})
        return destination

    def export_board_csv(self, path: str | Path) -> Path:
        """Exporte une ligne par case et scénario avec fréquentation et rendement.

        Entrées:
            path (str | Path): Fichier CSV de destination.

        Sortie:
            Path: Chemin effectivement écrit.
        """
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "scenario", "index", "name", "total_landings",
            "average_landings_per_game", "landing_share_percent",
            "total_investment", "total_rent", "roi_percent",
            "net_return", "rent_per_landing",
        ]
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for campaign in self.campaigns:
                investments = {
                    item.index: item
                    for item in campaign.property_investment_summary
                }
                for space in campaign.space_summary:
                    investment = investments.get(space.index)
                    writer.writerow(
                        {
                            "scenario": campaign.scenario_name,
                            "index": space.index,
                            "name": space.name,
                            "total_landings": space.total_landings,
                            "average_landings_per_game": space.average_landings_per_game,
                            "landing_share_percent": space.landing_share_percent,
                            "total_investment": "" if investment is None else investment.total_investment,
                            "total_rent": "" if investment is None else investment.total_rent,
                            "roi_percent": "" if investment is None else investment.roi_percent,
                            "net_return": "" if investment is None else investment.net_return,
                            "rent_per_landing": "" if investment is None else investment.rent_per_landing,
                        }
                    )
        return destination

    def export_development_csv(self, path: str | Path) -> Path:
        """Exporte le ROI par terrain et niveau de construction.

        Entrées:
            path (str | Path): Fichier CSV de destination.

        Sortie:
            Path: Chemin effectivement écrit.
        """
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "scenario", "property_index", "property_name", "level",
            "level_label", "total_rent", "total_investment_basis",
            "rent_events", "reached_count", "roi_percent",
            "average_rent_per_event",
        ]
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for campaign in self.campaigns:
                for item in campaign.property_development_summary:
                    row = item.to_dict()
                    row["scenario"] = campaign.scenario_name
                    writer.writerow({field: row.get(field, "") for field in fields})
        return destination



    def export_cards_csv(self, path: str | Path) -> Path:
        """Exporte une ligne par carte et scénario avec fréquence et impact observé.

        Entrées:
            path (str | Path): Fichier CSV de destination.

        Sortie:
            Path: Chemin effectivement écrit.
        """
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "scenario", "deck", "card_type", "card_text", "draws",
            "games_with_draw", "average_draws_per_game", "deck_share_percent",
            "drawer_cash_delta", "average_drawer_cash_delta",
            "other_players_cash_delta", "average_other_players_cash_delta",
            "total_player_cash_delta", "free_parking_pot_delta", "average_pot_delta",
            "movements", "movement_rate", "jail_sends", "jail_rate",
            "get_out_cards", "get_out_rate", "biggest_gain", "biggest_loss",
        ]
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for campaign in self.campaigns:
                for item in campaign.card_summary:
                    row = item.to_dict()
                    row["scenario"] = campaign.scenario_name
                    writer.writerow({field: row.get(field, "") for field in fields})
        return destination



class NeutralSimulationPolicy:
    """Prend des décisions aléatoires fixes, sans optimisation ni stratégie adaptative.

    Entrées:
        rng (random.Random): Générateur reproductible propre à la partie simulée.

    Sortie:
        NeutralSimulationPolicy: Politique opérationnelle neutre du laboratoire.

    Notes:
        Les probabilités sont volontairement fixes dans le code et ne sont pas exposées
        comme paramètres de stratégie. La V21 mesure le moteur ; elle ne cherche pas à gagner.
    """

    PURCHASE_PROBABILITY = 0.50
    MANUAL_RENT_CLAIM_PROBABILITY = 0.50
    BUILD_PROBABILITY = 0.35
    UNMORTGAGE_PROBABILITY = 0.20

    def __init__(self, rng: random.Random) -> None:
        """Mémorise le générateur aléatoire de la partie.

        Entrées:
            rng (random.Random): Générateur déterministe.

        Sortie:
            None: La politique est prête.
        """
        self.rng = rng

    def choose_jail_action(self, game: Game) -> str:
        """Choisit l'action de prison neutre du laboratoire.

        Entrées:
            game (Game): Partie courante.

        Sortie:
            str: Toujours ``roll`` pour ne pas introduire une préférence économique.
        """
        return "roll"

    def should_buy(self, player_cash: int, price: int) -> bool:
        """Décide aléatoirement d'un achat direct parmi les achats payables.

        Entrées:
            player_cash (int): Cash actuel du joueur.
            price (int): Prix demandé.

        Sortie:
            bool: Tirage à 50 % si l'achat est financièrement possible.
        """
        return player_cash >= price and self.rng.random() < self.PURCHASE_PROBABILITY

    def resolve_manual_rent(self, game: Game) -> None:
        """Résout immédiatement un loyer manuel par tirage neutre.

        Entrées:
            game (Game): Partie pouvant contenir un loyer en attente.

        Sortie:
            None: Le loyer est réclamé ou abandonné à probabilité égale.
        """
        if game.pending_rent_claim is None:
            return
        if self.rng.random() < self.MANUAL_RENT_CLAIM_PROBABILITY:
            game.claim_pending_rent()
        else:
            game.waive_pending_rent()

    def run_property_auction(self, game: Game, space: OwnableSpace) -> None:
        """Résout une enchère par budgets privés aléatoires, sans tactique d'enchère.

        Entrées:
            game (Game): Partie contenant les joueurs actifs.
            space (OwnableSpace): Bien libre à vendre.

        Sortie:
            None: Le bien est vendu au meilleur budget aléatoire ou reste à la banque.
        """
        if space.owner is not None:
            return
        auction = game.start_auction(space)
        budgets: list[tuple[int, object]] = []
        for player in list(auction.active_bidders):
            if player.cash <= 0:
                budget = 0
            else:
                budget = self.rng.randint(0, player.cash)
            budgets.append((budget, player))

        positive = [(budget, player) for budget, player in budgets if budget > 0]
        if not positive:
            for _, player in list(budgets):
                auction.withdraw(player)
            auction.finish()
            return

        positive.sort(key=lambda item: (item[0], -item[1].player_id), reverse=True)
        winner_budget, winner = positive[0]
        second_budget = positive[1][0] if len(positive) > 1 else 0
        price = min(winner_budget, max(1, second_budget + 1))
        auction.place_bid(winner, price)
        for player in list(auction.active_bidders):
            if player is not winner:
                auction.withdraw(player)
        result = auction.finish()
        if result.sold and result.winner is not None:
            game.record_event(
                "auction_win",
                f"{result.winner.name} remporte {space.name} pour {result.amount} $ en simulation.",
                result.winner,
                property_index=space.index,
                amount=result.amount,
                simulated=True,
            )

    def maybe_unmortgage(self, game: Game, player: object) -> None:
        """Tente rarement de lever une hypothèque payable.

        Entrées:
            game (Game): Partie courante.
            player (object): Joueur actif, typé souplement pour éviter un import circulaire.

        Sortie:
            None: Au plus une hypothèque est levée.
        """
        if player.bankrupt or self.rng.random() >= self.UNMORTGAGE_PROBABILITY:
            return
        candidates = [
            space
            for space in player.properties
            if game.rules.can_unmortgage(player, space)
        ]
        if not candidates:
            return
        game.rules.unmortgage_property(player, self.rng.choice(candidates))

    def maybe_build(
        self,
        game: Game,
        player: object,
        landed_space: object,
        owned_on_landing: bool,
    ) -> None:
        """Tente une construction aléatoire parmi les placements légalement possibles.

        Entrées:
            game (Game): Partie et règles de construction.
            player (object): Joueur qui vient d'agir.
            landed_space (object): Case finale du déplacement.
            owned_on_landing (bool): Indique que le terrain appartenait déjà au joueur
                au moment de l'atterrissage, avant tout achat direct ou enchère.

        Sortie:
            None: Au plus une décision de construction est exécutée.
        """
        if player.bankrupt or self.rng.random() >= self.BUILD_PROBABILITY:
            return

        if not game.options.construction_anywhere:
            if not owned_on_landing or not isinstance(landed_space, Property):
                return
            game.set_landing_build_context(player, landed_space)

        owned_properties = sorted(
            (
                space
                for space in player.properties
                if isinstance(space, Property)
            ),
            key=lambda space: space.index,
        )
        hotel_targets = [
            space
            for space in owned_properties
            if game.rules.can_build_hotel(player, space)
        ]
        house_targets = [
            space
            for space in owned_properties
            if game.rules.can_build_house(player, space)
        ]

        if hotel_targets and (not house_targets or self.rng.random() < 0.25):
            game.rules.build_hotel(player, self.rng.choice(hotel_targets))
        elif house_targets:
            target = self.rng.choice(house_targets)
            max_count = game.rules.max_landing_house_purchase(
                player,
                target,
                limit=game.options.max_buildings_per_action,
            )
            if max_count > 0:
                count = self.rng.randint(1, max_count)
                game.rules.build_houses(player, target, count)

        game.clear_landing_build_context()


def _run_game_batch_process_task(
    scenario: SimulationScenario,
    player_count: int,
    indexed_seeds: list[tuple[int, int]],
    max_rounds: int,
) -> list[tuple[int, SimulationGameResult]]:
    """Exécute un lot de parties dans un processus de calcul indépendant.

    Entrées:
        scenario (SimulationScenario): Scénario sérialisable à simuler.
        player_count (int): Nombre de joueurs neutres.
        indexed_seeds (list[tuple[int, int]]): Indices d'ordre et seeds du lot.
        max_rounds (int): Limite de tours, ou zéro pour le mode illimité.

    Sortie:
        list[tuple[int, SimulationGameResult]]: Résultats indexés dans l'ordre global.
    """
    runner = SimulationRunner()
    return [
        (
            game_index,
            runner.run_game(scenario, player_count, seed, max_rounds),
        )
        for game_index, seed in indexed_seeds
    ]


class SimulationRunner:
    """Exécute des parties neutres et agrège les résultats de plusieurs scénarios.

    Entrées:
        progress_callback (Callable[[int, int, str], None] | None): Callback facultatif
            recevant progression actuelle, total et nom du scénario.

    Sortie:
        SimulationRunner: Moteur de laboratoire indépendant de Tkinter.
    """

    def __init__(
        self,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> None:
        """Mémorise le callback de progression.

        Entrées:
            progress_callback (Callable | None): Fonction d'actualisation éventuelle.

        Sortie:
            None: Le runner est prêt.
        """
        self.progress_callback = progress_callback
        self.last_worker_count = 1

    def run(
        self,
        scenarios: list[SimulationScenario],
        config: SimulationConfig,
    ) -> SimulationComparisonResult:
        """Exécute la même campagne sur chaque scénario fourni.

        Entrées:
            scenarios (list[SimulationScenario]): Scénarios à comparer.
            config (SimulationConfig): Taille, joueurs, seeds et garde-fou.

        Sortie:
            SimulationComparisonResult: Toutes les campagnes agrégées.

        Lève:
            ValueError: Si aucun scénario n'est fourni ou si la configuration est invalide.
        """
        config.validate()
        if not scenarios:
            raise ValueError("Ajoutez au moins un scénario de simulation.")

        total = len(scenarios) * config.games_per_scenario
        completed = 0
        campaigns: list[SimulationCampaignResult] = []
        worker_count = self._resolve_worker_count(config, total)
        self.last_worker_count = worker_count

        for scenario in scenarios:
            seeds = [
                config.base_seed + game_index
                for game_index in range(config.games_per_scenario)
            ]
            if worker_count <= 1:
                game_results = []
                for seed in seeds:
                    game_results.append(
                        self.run_game(
                            scenario,
                            config.player_count,
                            seed,
                            config.max_rounds,
                        )
                    )
                    completed += 1
                    self._emit_progress(completed, total, scenario.name)
            else:
                indexed_results: list[SimulationGameResult | None] = [
                    None for _ in seeds
                ]
                indexed_seeds = list(enumerate(seeds))
                target_batches = max(worker_count, worker_count * 6)
                batch_size = max(
                    4,
                    min(
                        25,
                        (len(indexed_seeds) + target_batches - 1) // target_batches,
                    ),
                )
                chunks = [
                    indexed_seeds[offset : offset + batch_size]
                    for offset in range(0, len(indexed_seeds), batch_size)
                ]
                with ProcessPoolExecutor(
                    max_workers=worker_count,
                    mp_context=multiprocessing.get_context(
                        "forkserver" if os.name != "nt" else "spawn"
                    ),
                ) as executor:
                    futures = {
                        executor.submit(
                            _run_game_batch_process_task,
                            scenario,
                            config.player_count,
                            chunk,
                            config.max_rounds,
                        ): len(chunk)
                        for chunk in chunks
                    }
                    for future in as_completed(futures):
                        batch = future.result()
                        for game_index, result in batch:
                            indexed_results[game_index] = result
                            completed += 1
                            self._emit_progress(completed, total, scenario.name)
                game_results = [
                    result for result in indexed_results if result is not None
                ]

            campaigns.append(
                self._aggregate_campaign(scenario.name, config, game_results)
            )

        return SimulationComparisonResult(
            config,
            campaigns,
            [scenario.clone() for scenario in scenarios],
        )

    def _resolve_worker_count(
        self,
        config: SimulationConfig,
        total_games: int,
    ) -> int:
        """Choisit le nombre de processus réellement utile pour la campagne.

        Entrées:
            config (SimulationConfig): Configuration contenant le choix utilisateur.
            total_games (int): Nombre total de parties prévues.

        Sortie:
            int: Nombre de processus compris entre 1 et le nombre de parties.
        """
        if config.parallel_workers == 1 or total_games < 8:
            return 1
        if config.parallel_workers > 1:
            return max(1, min(config.parallel_workers, total_games))
        automatic_threshold = 16 if config.max_rounds == 0 else 250
        if config.games_per_scenario < automatic_threshold:
            return 1
        available = os.cpu_count() or 2
        automatic = max(1, min(8, available - 1 if available > 1 else 1))
        return max(1, min(automatic, total_games))

    def _emit_progress(self, completed: int, total: int, scenario_name: str) -> None:
        """Transmet une progression de campagne si un callback est configuré.

        Entrées:
            completed (int): Parties terminées.
            total (int): Parties prévues.
            scenario_name (str): Scénario ayant produit le dernier résultat.

        Sortie:
            None: Le callback éventuel est invoqué une seule fois.
        """
        if self.progress_callback is not None:
            self.progress_callback(completed, total, scenario_name)

    def run_game(
        self,
        scenario: SimulationScenario,
        player_count: int,
        seed: int,
        max_rounds: int,
    ) -> SimulationGameResult:
        """Exécute une seule partie neutre jusqu'à sa fin ou au garde-fou.

        Entrées:
            scenario (SimulationScenario): Règles et plateau.
            player_count (int): Nombre de joueurs neutres.
            seed (int): Graine reproductible.
            max_rounds (int): Limite de tours ; ``0`` active le mode illimité protégé.

        Sortie:
            SimulationGameResult: Résultat détaillé de la partie.
        """
        names = [f"Joueur {index + 1}" for index in range(player_count)]
        game = Game(
            names,
            seed=seed,
            options=GameOptions.from_dict(scenario.options.to_dict()),
            board_config=scenario.board_config.clone(),
            capture_replay=False,
        )
        game.capture_landing_events = True
        policy = NeutralSimulationPolicy(random.Random(seed ^ 0x5F3759DF))
        actions = 0
        unlimited_rounds = max_rounds == 0
        max_actions = (
            UNLIMITED_ACTION_WATCHDOG
            if unlimited_rounds
            else max(100, max_rounds * player_count * 12)
        )
        stop_reason = "natural"

        while not game.is_over:
            if not unlimited_rounds and game.completed_rounds >= max_rounds:
                stop_reason = "round_limit"
                break
            if actions >= max_actions:
                stop_reason = "action_watchdog"
                break

            actor = game.current_player
            jail_action = policy.choose_jail_action(game)
            result = game.take_turn(jail_action=jail_action)
            actions += 1

            landed_space = game.get_current_space(result.player)
            unowned_on_landing = (
                isinstance(landed_space, OwnableSpace)
                and landed_space.owner is None
            )
            owned_on_landing = (
                isinstance(landed_space, Property)
                and landed_space.owner is result.player
            )

            policy.resolve_manual_rent(game)

            if (
                not result.player.bankrupt
                and unowned_on_landing
                and isinstance(landed_space, OwnableSpace)
            ):
                if policy.should_buy(result.player.cash, landed_space.price):
                    game.rules.buy_property(result.player, landed_space)
                elif game.options.auctions_enabled:
                    policy.run_property_auction(game, landed_space)

            self._process_bank_auctions(game, policy)

            if not result.player.bankrupt:
                policy.maybe_unmortgage(game, result.player)
                policy.maybe_build(
                    game,
                    result.player,
                    landed_space,
                    owned_on_landing,
                )

        truncated = not game.is_over
        stats = GameStatistics.from_game(game, include_round_series=False)
        winner = game.winner
        winner_at_cutoff = False
        if winner is None:
            candidates = [player for player in game.players if not player.bankrupt]
            if not candidates:
                candidates = list(game.players)
            winner = max(
                candidates,
                key=lambda player: (
                    game.player_net_worth(player),
                    player.cash,
                    -player.player_id,
                ),
            )
            winner_at_cutoff = True

        (
            space_names,
            space_landings,
            property_investment,
            property_rent_by_index,
            property_level_rent,
            property_level_rent_events,
            property_level_investment,
        ) = self._extract_board_metrics(game)

        final_worth = {
            player.name: game.player_net_worth(player)
            for player in game.players
        }
        property_rent = {
            item.name: item.rent_received
            for item in stats.properties
            if item.rent_received > 0
        }
        property_rent_events = {
            item.name: item.rent_events
            for item in stats.properties
            if item.rent_events > 0
        }
        property_biggest_rent = {
            item.name: item.biggest_rent
            for item in stats.properties
            if item.biggest_rent > 0
        }
        final_cash = {player.name: player.cash for player in game.players}
        final_property_count = {
            player.name: len(player.properties) for player in game.players
        }
        rent_paid_by_player = {item.name: item.rent_paid for item in stats.players}
        rent_received_by_player = {
            item.name: item.rent_received for item in stats.players
        }
        bankrupt_by_player = {item.name: item.bankrupt for item in stats.players}
        jail_visits_by_player = {
            item.name: item.jail_visits for item in stats.players
        }
        card_metrics = self._extract_card_metrics(game)

        return SimulationGameResult(
            seed=seed,
            rounds=game.completed_rounds,
            actions=actions,
            winner_name=None if winner is None else winner.name,
            finished=game.is_over,
            truncated=truncated,
            stop_reason=stop_reason,
            bankruptcies=stats.bankruptcies,
            rent_transferred=stats.rent_transferred,
            buildings_built=stats.buildings_built,
            jail_visits=stats.jail_visits,
            free_parking_peak=stats.free_parking_peak,
            final_net_worth=final_worth,
            property_rent=property_rent,
            property_rent_events=property_rent_events,
            property_biggest_rent=property_biggest_rent,
            cards_drawn=stats.cards_drawn,
            purchases=stats.purchases,
            auctions_won=stats.auctions_won,
            mortgages=stats.mortgages,
            biggest_rent=stats.biggest_rent,
            free_parking_collected=stats.free_parking_collected,
            final_cash=final_cash,
            final_property_count=final_property_count,
            rent_paid_by_player=rent_paid_by_player,
            rent_received_by_player=rent_received_by_player,
            bankrupt_by_player=bankrupt_by_player,
            jail_visits_by_player=jail_visits_by_player,
            winner_at_cutoff=winner_at_cutoff,
            space_names=space_names,
            space_landings=space_landings,
            property_investment=property_investment,
            property_rent_by_index=property_rent_by_index,
            property_level_rent=property_level_rent,
            property_level_rent_events=property_level_rent_events,
            property_level_investment=property_level_investment,
            card_metrics=card_metrics,
        )

    def _extract_card_metrics(self, game: Game) -> dict[str, dict[str, object]]:
        """Agrège les événements ``card_draw`` d'une seule partie.

        Entrées:
            game (Game): Partie simulée dont l'historique contient les tirages.

        Sortie:
            dict[str, dict[str, object]]: Métriques par identité deck/type/texte.
        """
        metrics: dict[str, dict[str, object]] = {}
        for event in game.history.events:
            if event.event_type != "card_draw":
                continue
            deck = str(event.data.get("deck", ""))
            card_type = str(event.data.get("card_type", "Card"))
            card_text = str(event.data.get("card_text", ""))
            key = f"{deck}|{card_type}|{card_text}"
            item = metrics.setdefault(
                key,
                {
                    "deck": deck,
                    "card_type": card_type,
                    "card_text": card_text,
                    "draws": 0,
                    "drawer_cash_delta": 0,
                    "other_players_cash_delta": 0,
                    "total_player_cash_delta": 0,
                    "free_parking_pot_delta": 0,
                    "movements": 0,
                    "jail_sends": 0,
                    "get_out_cards": 0,
                    "biggest_gain": 0,
                    "biggest_loss": 0,
                },
            )
            drawer_delta = int(event.data.get("drawer_cash_delta", 0))
            item["draws"] = int(item["draws"]) + 1
            item["drawer_cash_delta"] = int(item["drawer_cash_delta"]) + drawer_delta
            item["other_players_cash_delta"] = (
                int(item["other_players_cash_delta"])
                + int(event.data.get("other_players_cash_delta", 0))
            )
            item["total_player_cash_delta"] = (
                int(item["total_player_cash_delta"])
                + int(event.data.get("total_player_cash_delta", 0))
            )
            item["free_parking_pot_delta"] = (
                int(item["free_parking_pot_delta"])
                + int(event.data.get("free_parking_pot_delta", 0))
            )
            item["movements"] = int(item["movements"]) + int(
                bool(event.data.get("moved", False))
            )
            item["jail_sends"] = int(item["jail_sends"]) + int(
                bool(event.data.get("sent_to_jail", False))
            )
            item["get_out_cards"] = int(item["get_out_cards"]) + int(
                bool(event.data.get("get_out_card_received", False))
            )
            item["biggest_gain"] = max(int(item["biggest_gain"]), drawer_delta)
            item["biggest_loss"] = max(int(item["biggest_loss"]), -drawer_delta)
        return metrics

    def _extract_board_metrics(
        self,
        game: Game,
    ) -> tuple[
        dict[int, str],
        dict[int, int],
        dict[int, int],
        dict[int, int],
        dict[int, dict[int, int]],
        dict[int, dict[int, int]],
        dict[int, dict[int, int]],
    ]:
        """Extrait fréquentation, investissements et rendement par niveau de construction.

        Entrées:
            game (Game): Partie simulée terminée ou arrêtée par le garde-fou.

        Sortie:
            tuple: Noms des cases, arrêts, investissements, loyers par index,
            loyers par niveau, événements de loyer par niveau et bases d'investissement.

        Notes:
            L'investissement est volontairement brut : achats, enchères et constructions
            effectivement payés. Les reventes et hypothèques ne sont pas soustraites,
            afin de mesurer l'argent réellement engagé dans la case.
        """
        space_names = {space.index: space.name for space in game.board.spaces}
        space_landings: dict[int, int] = {}
        property_investment: dict[int, int] = {}
        property_rent_by_index: dict[int, int] = {}
        property_level_rent: dict[int, dict[int, int]] = {}
        property_level_rent_events: dict[int, dict[int, int]] = {}
        property_level_investment: dict[int, dict[int, int]] = {}
        cycle_investment: dict[int, int] = {}

        for event in game.history.events:
            if event.event_type == "landing":
                index = int(event.data.get("space_index", -1))
                if index >= 0:
                    space_landings[index] = space_landings.get(index, 0) + 1
                continue

            if event.event_type in {"purchase", "auction_win"}:
                raw_index = event.data.get("property_index")
                if raw_index is None:
                    continue
                index = int(raw_index)
                amount = int(
                    event.data.get(
                        "price",
                        event.data.get("amount", 0),
                    )
                )
                property_investment[index] = (
                    property_investment.get(index, 0) + amount
                )
                cycle_investment[index] = amount
                space = game.board[index]
                if isinstance(space, Property):
                    levels = property_level_investment.setdefault(index, {})
                    levels[0] = levels.get(0, 0) + amount
                continue

            if event.event_type == "debt_property_transfer":
                raw_index = event.data.get("property_index")
                if raw_index is not None:
                    cycle_investment[int(raw_index)] = 0
                continue

            if event.event_type == "building":
                raw_index = event.data.get("property_index")
                if raw_index is None:
                    continue
                index = int(raw_index)
                amount = int(event.data.get("price", 0))
                property_investment[index] = (
                    property_investment.get(index, 0) + amount
                )
                cycle_investment[index] = cycle_investment.get(index, 0) + amount
                level = event.data.get("development_level")
                if level is not None:
                    level_int = int(level)
                    levels = property_level_investment.setdefault(index, {})
                    levels[level_int] = (
                        levels.get(level_int, 0) + cycle_investment[index]
                    )
                continue

            if event.event_type == "rent":
                raw_index = event.data.get("property_index")
                if raw_index is None:
                    continue
                index = int(raw_index)
                amount = int(event.data.get("amount", 0))
                property_rent_by_index[index] = (
                    property_rent_by_index.get(index, 0) + amount
                )
                level = event.data.get("development_level")
                if level is not None:
                    level_int = int(level)
                    rents = property_level_rent.setdefault(index, {})
                    rents[level_int] = rents.get(level_int, 0) + amount
                    events = property_level_rent_events.setdefault(index, {})
                    events[level_int] = events.get(level_int, 0) + 1

        return (
            space_names,
            space_landings,
            property_investment,
            property_rent_by_index,
            property_level_rent,
            property_level_rent_events,
            property_level_investment,
        )

    def _process_bank_auctions(
        self,
        game: Game,
        policy: NeutralSimulationPolicy,
    ) -> None:
        """Résout les enchères de biens rendus à la banque après faillite.

        Entrées:
            game (Game): Partie pouvant contenir une file d'enchères.
            policy (NeutralSimulationPolicy): Politique neutre d'enchère.

        Sortie:
            None: La file est vidée tant que la partie possède des joueurs actifs.
        """
        while game.pending_bank_auctions and len(game.active_players) >= 2:
            space = game.pop_next_bank_auction()
            if space is None:
                break
            policy.run_property_auction(game, space)

    def _aggregate_campaign(
        self,
        scenario_name: str,
        config: SimulationConfig,
        games: list[SimulationGameResult],
    ) -> SimulationCampaignResult:
        """Agrège résultats, fréquentation et rendement d'un scénario.

        Entrées:
            scenario_name (str): Nom du scénario.
            config (SimulationConfig): Paramètres communs.
            games (list[SimulationGameResult]): Parties terminées ou tronquées.

        Sortie:
            SimulationCampaignResult: Résumé complet du scénario sans stratégie.
        """
        totals: dict[str, int] = {}
        games_with_rent: dict[str, int] = {}
        rent_events: dict[str, int] = {}
        biggest_rents: dict[str, int] = {}
        player_names: set[str] = set()
        space_names: dict[int, str] = {}
        space_landings: dict[int, int] = {}
        investment_totals: dict[int, int] = {}
        rent_by_index: dict[int, int] = {}
        level_rents: dict[int, dict[int, int]] = {}
        level_events: dict[int, dict[int, int]] = {}
        level_investment: dict[int, dict[int, int]] = {}
        level_reached: dict[int, dict[int, int]] = {}
        card_totals: dict[str, dict[str, object]] = {}
        card_games_with_draw: dict[str, int] = {}

        for game in games:
            player_names.update(game.final_net_worth)
            space_names.update(game.space_names)
            for index, count in game.space_landings.items():
                space_landings[index] = space_landings.get(index, 0) + count
            for index, amount in game.property_investment.items():
                investment_totals[index] = investment_totals.get(index, 0) + amount
            for index, amount in game.property_rent_by_index.items():
                rent_by_index[index] = rent_by_index.get(index, 0) + amount

            for index, levels in game.property_level_rent.items():
                target = level_rents.setdefault(index, {})
                for level, amount in levels.items():
                    target[level] = target.get(level, 0) + amount
            for index, levels in game.property_level_rent_events.items():
                target = level_events.setdefault(index, {})
                for level, count in levels.items():
                    target[level] = target.get(level, 0) + count
            for index, levels in game.property_level_investment.items():
                target = level_investment.setdefault(index, {})
                reached = level_reached.setdefault(index, {})
                for level, amount in levels.items():
                    target[level] = target.get(level, 0) + amount
                    reached[level] = reached.get(level, 0) + 1

            for name, rent in game.property_rent.items():
                totals[name] = totals.get(name, 0) + rent
                if rent > 0:
                    games_with_rent[name] = games_with_rent.get(name, 0) + 1
            for name, count in game.property_rent_events.items():
                rent_events[name] = rent_events.get(name, 0) + count
            for name, amount in game.property_biggest_rent.items():
                biggest_rents[name] = max(biggest_rents.get(name, 0), amount)

            for key, raw in game.card_metrics.items():
                target = card_totals.setdefault(
                    key,
                    {
                        "deck": raw.get("deck", ""),
                        "card_type": raw.get("card_type", "Card"),
                        "card_text": raw.get("card_text", ""),
                        "draws": 0,
                        "drawer_cash_delta": 0,
                        "other_players_cash_delta": 0,
                        "total_player_cash_delta": 0,
                        "free_parking_pot_delta": 0,
                        "movements": 0,
                        "jail_sends": 0,
                        "get_out_cards": 0,
                        "biggest_gain": 0,
                        "biggest_loss": 0,
                    },
                )
                for field_name in (
                    "draws",
                    "drawer_cash_delta",
                    "other_players_cash_delta",
                    "total_player_cash_delta",
                    "free_parking_pot_delta",
                    "movements",
                    "jail_sends",
                    "get_out_cards",
                ):
                    target[field_name] = int(target[field_name]) + int(
                        raw.get(field_name, 0)
                    )
                target["biggest_gain"] = max(
                    int(target["biggest_gain"]),
                    int(raw.get("biggest_gain", 0)),
                )
                target["biggest_loss"] = max(
                    int(target["biggest_loss"]),
                    int(raw.get("biggest_loss", 0)),
                )
                card_games_with_draw[key] = card_games_with_draw.get(key, 0) + 1

        denominator = max(1, len(games))
        properties = [
            PropertySimulationSummary(
                name=name,
                total_rent=total,
                games_with_rent=games_with_rent.get(name, 0),
                average_rent_per_game=total / denominator,
                total_rent_events=rent_events.get(name, 0),
                biggest_rent=biggest_rents.get(name, 0),
            )
            for name, total in totals.items()
        ]
        properties.sort(
            key=lambda item: (item.average_rent_per_game, item.total_rent),
            reverse=True,
        )

        all_landings = sum(space_landings.values())
        spaces = [
            SpaceSimulationSummary(
                index=index,
                name=space_names.get(index, f"Case {index}"),
                total_landings=space_landings.get(index, 0),
                games=len(games),
                all_landings=all_landings,
            )
            for index in sorted(space_names)
        ]

        investment_indices = sorted(
            set(investment_totals) | set(rent_by_index)
        )
        investments = [
            PropertyInvestmentSummary(
                index=index,
                name=space_names.get(index, f"Case {index}"),
                total_investment=investment_totals.get(index, 0),
                total_rent=rent_by_index.get(index, 0),
                total_landings=space_landings.get(index, 0),
                games=len(games),
            )
            for index in investment_indices
        ]
        investments.sort(
            key=lambda item: (item.roi_percent, item.total_rent),
            reverse=True,
        )

        development: list[PropertyDevelopmentSummary] = []
        development_indices = sorted(
            set(level_rents) | set(level_investment)
        )
        for index in development_indices:
            levels = sorted(
                set(level_rents.get(index, {}))
                | set(level_investment.get(index, {}))
            )
            for level in levels:
                development.append(
                    PropertyDevelopmentSummary(
                        property_index=index,
                        property_name=space_names.get(index, f"Case {index}"),
                        level=level,
                        total_rent=level_rents.get(index, {}).get(level, 0),
                        total_investment_basis=(
                            level_investment.get(index, {}).get(level, 0)
                        ),
                        rent_events=level_events.get(index, {}).get(level, 0),
                        reached_count=level_reached.get(index, {}).get(level, 0),
                    )
                )


        deck_draw_totals: dict[str, int] = {}
        for raw in card_totals.values():
            deck = str(raw.get("deck", ""))
            deck_draw_totals[deck] = (
                deck_draw_totals.get(deck, 0) + int(raw.get("draws", 0))
            )

        cards = [
            CardSimulationSummary(
                deck=str(raw.get("deck", "")),
                card_type=str(raw.get("card_type", "Card")),
                card_text=str(raw.get("card_text", "")),
                draws=int(raw.get("draws", 0)),
                games_with_draw=card_games_with_draw.get(key, 0),
                games=len(games),
                deck_draws=deck_draw_totals.get(str(raw.get("deck", "")), 0),
                drawer_cash_delta=int(raw.get("drawer_cash_delta", 0)),
                other_players_cash_delta=int(raw.get("other_players_cash_delta", 0)),
                total_player_cash_delta=int(raw.get("total_player_cash_delta", 0)),
                free_parking_pot_delta=int(raw.get("free_parking_pot_delta", 0)),
                movements=int(raw.get("movements", 0)),
                jail_sends=int(raw.get("jail_sends", 0)),
                get_out_cards=int(raw.get("get_out_cards", 0)),
                biggest_gain=int(raw.get("biggest_gain", 0)),
                biggest_loss=int(raw.get("biggest_loss", 0)),
            )
            for key, raw in card_totals.items()
        ]
        cards.sort(
            key=lambda item: (item.deck, item.draws, item.card_text),
            reverse=True,
        )

        players: list[PlayerSimulationSummary] = []
        finished_games = sum(game.finished for game in games)
        for name in sorted(player_names):
            first_places = sum(game.winner_name == name for game in games)
            natural_wins = sum(
                game.winner_name == name and game.finished and not game.winner_at_cutoff
                for game in games
            )
            cutoff_leads = sum(
                game.winner_name == name and game.winner_at_cutoff
                for game in games
            )
            bankruptcies = sum(
                bool(game.bankrupt_by_player.get(name, False)) for game in games
            )
            players.append(
                PlayerSimulationSummary(
                    name=name,
                    games=len(games),
                    wins=first_places,
                    bankruptcies=bankruptcies,
                    average_final_cash=mean(
                        [game.final_cash.get(name, 0) for game in games]
                    ) if games else 0.0,
                    average_final_net_worth=mean(
                        [game.final_net_worth.get(name, 0) for game in games]
                    ) if games else 0.0,
                    average_final_properties=mean(
                        [game.final_property_count.get(name, 0) for game in games]
                    ) if games else 0.0,
                    average_rent_paid=mean(
                        [game.rent_paid_by_player.get(name, 0) for game in games]
                    ) if games else 0.0,
                    average_rent_received=mean(
                        [game.rent_received_by_player.get(name, 0) for game in games]
                    ) if games else 0.0,
                    average_jail_visits=mean(
                        [game.jail_visits_by_player.get(name, 0) for game in games]
                    ) if games else 0.0,
                    finished_games=finished_games,
                    finished_wins=natural_wins,
                    cutoff_leads=cutoff_leads,
                )
            )

        return SimulationCampaignResult(
            scenario_name=scenario_name,
            config=config,
            games=games,
            property_summary=properties,
            player_summary=players,
            space_summary=spaces,
            property_investment_summary=investments,
            property_development_summary=development,
            card_summary=cards,
        )

