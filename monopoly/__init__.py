"""Expose les principales classes publiques du moteur Monopoly."""

from .auction import Auction, AuctionResult
from .board import Board
from .bank import Bank
from .debt import DebtManagementResult
from .building_auction import BuildingAuction, BuildingAuctionResult
from .game import Game, TurnResult
from .history import GameEvent, GameHistory
from .options import GameOptions
from .rules_audit import RuleAuditItem, AUDITED_RULES
from .rule_presets import RulePreset, RulePresetError
from .statistics import GameStatistics, PlayerStatistics
from .player import Player
from .rules import Rules
from .trade import TradeOffer, TradeResult

__all__ = [
    "Auction", "AuctionResult", "Bank", "Board", "BuildingAuction",
    "BuildingAuctionResult", "DebtManagementResult", "Game", "GameEvent", "GameHistory",
    "AUDITED_RULES", "GameOptions", "GameStatistics", "Player", "PlayerStatistics",
    "RuleAuditItem", "RulePreset", "RulePresetError", "Rules", "TurnResult",
    "TradeOffer", "TradeResult",
]
