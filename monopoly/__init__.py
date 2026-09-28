"""Expose les principales classes publiques du moteur Monopoly."""

from .auction import Auction, AuctionResult
from .board import Board
from .board_config import BoardConfig, BoardValidationIssue, CardConfig, SpaceConfig
from .bank import Bank
from .debt import DebtManagementResult
from .building_auction import BuildingAuction, BuildingAuctionResult
from .game import Game, TurnResult
from .history import GameEvent, GameHistory
from .options import GameOptions
from .rules_audit import RuleAuditItem, AUDITED_RULES
from .replay import ReplayPlayerState, ReplayPropertyState, ReplaySnapshot, ReplayTimeline
from .rule_presets import RulePreset, RulePresetError
from .profile_packs import ProfilePack, ProfilePackError
from .statistics import GameStatistics, PlayerStatistics
from .player import Player
from .rules import Rules
from .simulation import (
    CardSimulationSummary,
    NeutralSimulationPolicy,
    PlayerSimulationSummary,
    PropertySimulationSummary,
    SimulationCampaignResult,
    SimulationComparisonResult,
    SimulationConfig,
    SimulationGameResult,
    SimulationRunner,
    SimulationScenario,
    resolve_base_seed,
)
from .simulation_reports import (
    SimulationReportError,
    export_html_report,
    load_simulation_report,
    simulation_report_from_dict,
)
from .trade import TradeOffer, TradeResult

__all__ = [
    "Auction", "AuctionResult", "Bank", "Board", "BuildingAuction",
    "BuildingAuctionResult", "DebtManagementResult", "Game", "GameEvent", "GameHistory",
    "AUDITED_RULES", "BoardConfig", "BoardValidationIssue", "CardConfig", "GameOptions", "GameStatistics", "Player", "PlayerStatistics",
    "ProfilePack", "ProfilePackError", "RuleAuditItem", "RulePreset", "RulePresetError", "Rules", "SpaceConfig", "TurnResult",
    "TradeOffer", "TradeResult",
    "CardSimulationSummary", "NeutralSimulationPolicy", "PlayerSimulationSummary", "PropertySimulationSummary",
    "SimulationCampaignResult", "SimulationComparisonResult", "SimulationConfig",
    "SimulationGameResult", "SimulationRunner", "SimulationScenario", "resolve_base_seed",
    "SimulationReportError", "export_html_report", "load_simulation_report", "simulation_report_from_dict",
    "ReplayPlayerState", "ReplayPropertyState", "ReplaySnapshot", "ReplayTimeline",
]
