"""Recharge et exporte les rapports du laboratoire de simulation V21.8."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any

from .simulation import (
    CardSimulationSummary,
    PlayerSimulationSummary,
    PropertyDevelopmentSummary,
    PropertyInvestmentSummary,
    PropertySimulationSummary,
    SimulationCampaignResult,
    SimulationComparisonResult,
    SimulationConfig,
    SimulationGameResult,
    SimulationScenario,
    SpaceSimulationSummary,
)


class SimulationReportError(ValueError):
    """Signale qu'un rapport de laboratoire est absent, invalide ou incompatible.

    Entrées:
        message (str): Explication transmise à ``ValueError``.

    Sortie:
        SimulationReportError: Exception métier affichable par l'interface.
    """


def _int_key_dict(value: Any) -> dict[int, int]:
    """Convertit un dictionnaire JSON à clés texte en dictionnaire entier.

    Entrées:
        value (Any): Valeur JSON éventuellement dictionnaire.

    Sortie:
        dict[int, int]: Clés et valeurs entières valides uniquement.
    """
    if not isinstance(value, dict):
        return {}
    result: dict[int, int] = {}
    for key, item in value.items():
        try:
            result[int(key)] = int(item)
        except (TypeError, ValueError):
            continue
    return result



def _int_string_dict(value: Any) -> dict[int, str]:
    """Normalise un dictionnaire JSON index entier vers texte.

    Entrées:
        value (Any): Valeur JSON éventuelle.

    Sortie:
        dict[int, str]: Noms de cases indexés par position.
    """
    if not isinstance(value, dict):
        return {}
    result: dict[int, str] = {}
    for key, item in value.items():
        try:
            result[int(key)] = str(item)
        except (TypeError, ValueError):
            continue
    return result

def _nested_int_key_dict(value: Any) -> dict[int, dict[int, int]]:
    """Convertit une structure JSON imbriquée index/niveau en entiers.

    Entrées:
        value (Any): Dictionnaire sérialisé à deux niveaux.

    Sortie:
        dict[int, dict[int, int]]: Structure normalisée pour un résultat de partie.
    """
    if not isinstance(value, dict):
        return {}
    result: dict[int, dict[int, int]] = {}
    for key, levels in value.items():
        try:
            index = int(key)
        except (TypeError, ValueError):
            continue
        result[index] = _int_key_dict(levels)
    return result


def _string_int_dict(value: Any) -> dict[str, int]:
    """Normalise un dictionnaire JSON texte vers entier.

    Entrées:
        value (Any): Valeur JSON éventuelle.

    Sortie:
        dict[str, int]: Dictionnaire sans valeur non numérique.
    """
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        try:
            result[str(key)] = int(item)
        except (TypeError, ValueError):
            continue
    return result


def _string_bool_dict(value: Any) -> dict[str, bool]:
    """Normalise un dictionnaire JSON texte vers booléen.

    Entrées:
        value (Any): Valeur JSON éventuelle.

    Sortie:
        dict[str, bool]: Dictionnaire booléen exploitable par les statistiques.
    """
    if not isinstance(value, dict):
        return {}
    return {str(key): bool(item) for key, item in value.items()}


def _game_from_dict(data: dict[str, Any]) -> SimulationGameResult:
    """Reconstruit une partie détaillée depuis son export JSON.

    Entrées:
        data (dict[str, Any]): Ligne de partie du rapport.

    Sortie:
        SimulationGameResult: Résultat compatible avec les agrégats V21.8.
    """
    return SimulationGameResult(
        seed=int(data.get("seed", 0)),
        rounds=int(data.get("rounds", 0)),
        actions=int(data.get("actions", 0)),
        winner_name=None if data.get("winner_name") is None else str(data.get("winner_name")),
        finished=bool(data.get("finished", False)),
        truncated=bool(data.get("truncated", False)),
        stop_reason=str(data.get("stop_reason", "natural")),
        bankruptcies=int(data.get("bankruptcies", 0)),
        rent_transferred=int(data.get("rent_transferred", 0)),
        buildings_built=int(data.get("buildings_built", 0)),
        jail_visits=int(data.get("jail_visits", 0)),
        free_parking_peak=int(data.get("free_parking_peak", 0)),
        final_net_worth=_string_int_dict(data.get("final_net_worth")),
        property_rent=_string_int_dict(data.get("property_rent")),
        property_rent_events=_string_int_dict(data.get("property_rent_events")),
        property_biggest_rent=_string_int_dict(data.get("property_biggest_rent")),
        cards_drawn=int(data.get("cards_drawn", 0)),
        purchases=int(data.get("purchases", 0)),
        auctions_won=int(data.get("auctions_won", 0)),
        mortgages=int(data.get("mortgages", 0)),
        biggest_rent=int(data.get("biggest_rent", 0)),
        free_parking_collected=int(data.get("free_parking_collected", 0)),
        final_cash=_string_int_dict(data.get("final_cash")),
        final_property_count=_string_int_dict(data.get("final_property_count")),
        rent_paid_by_player=_string_int_dict(data.get("rent_paid_by_player")),
        rent_received_by_player=_string_int_dict(data.get("rent_received_by_player")),
        bankrupt_by_player=_string_bool_dict(data.get("bankrupt_by_player")),
        jail_visits_by_player=_string_int_dict(data.get("jail_visits_by_player")),
        winner_at_cutoff=bool(data.get("winner_at_cutoff", False)),
        space_names=_int_string_dict(data.get("space_names")),
        space_landings=_int_key_dict(data.get("space_landings")),
        property_investment=_int_key_dict(data.get("property_investment")),
        property_rent_by_index=_int_key_dict(data.get("property_rent_by_index")),
        property_level_rent=_nested_int_key_dict(data.get("property_level_rent")),
        property_level_rent_events=_nested_int_key_dict(data.get("property_level_rent_events")),
        property_level_investment=_nested_int_key_dict(data.get("property_level_investment")),
        card_metrics={str(key): dict(value) for key, value in data.get("card_metrics", {}).items()} if isinstance(data.get("card_metrics"), dict) else {},
    )


def _campaign_from_dict(data: dict[str, Any], config: SimulationConfig) -> SimulationCampaignResult:
    """Reconstruit les agrégats d'un scénario sans lancer de simulation.

    Entrées:
        data (dict[str, Any]): Campagne sérialisée.
        config (SimulationConfig): Configuration commune du rapport.

    Sortie:
        SimulationCampaignResult: Campagne immédiatement analysable par l'UI.
    """
    games = [
        _game_from_dict(item)
        for item in data.get("games", [])
        if isinstance(item, dict)
    ]
    game_count = len(games)

    raw_spaces = data.get("spaces", [])
    all_landings = sum(
        int(item.get("total_landings", 0))
        for item in raw_spaces
        if isinstance(item, dict)
    )
    spaces = [
        SpaceSimulationSummary(
            index=int(item.get("index", 0)),
            name=str(item.get("name", "")),
            total_landings=int(item.get("total_landings", 0)),
            games=game_count,
            all_landings=all_landings,
        )
        for item in raw_spaces
        if isinstance(item, dict)
    ]

    investments = [
        PropertyInvestmentSummary(
            index=int(item.get("index", 0)),
            name=str(item.get("name", "")),
            total_investment=int(item.get("total_investment", 0)),
            total_rent=int(item.get("total_rent", 0)),
            total_landings=int(item.get("total_landings", 0)),
            games=game_count,
        )
        for item in data.get("property_investment", [])
        if isinstance(item, dict)
    ]
    developments = [
        PropertyDevelopmentSummary(
            property_index=int(item.get("property_index", 0)),
            property_name=str(item.get("property_name", "")),
            level=int(item.get("level", 0)),
            total_rent=int(item.get("total_rent", 0)),
            total_investment_basis=int(item.get("total_investment_basis", 0)),
            rent_events=int(item.get("rent_events", 0)),
            reached_count=int(item.get("reached_count", 0)),
        )
        for item in data.get("property_development", [])
        if isinstance(item, dict)
    ]
    properties = [
        PropertySimulationSummary(
            name=str(item.get("name", "")),
            total_rent=int(item.get("total_rent", 0)),
            games_with_rent=int(item.get("games_with_rent", 0)),
            average_rent_per_game=float(item.get("average_rent_per_game", 0.0)),
            total_rent_events=int(item.get("total_rent_events", 0)),
            biggest_rent=int(item.get("biggest_rent", 0)),
        )
        for item in data.get("properties", [])
        if isinstance(item, dict)
    ]
    players = [
        PlayerSimulationSummary(
            name=str(item.get("name", "")),
            games=int(item.get("games", game_count)),
            wins=int(item.get("wins", 0)),
            bankruptcies=int(item.get("bankruptcies", 0)),
            average_final_cash=float(item.get("average_final_cash", 0.0)),
            average_final_net_worth=float(item.get("average_final_net_worth", 0.0)),
            average_final_properties=float(item.get("average_final_properties", 0.0)),
            average_rent_paid=float(item.get("average_rent_paid", 0.0)),
            average_rent_received=float(item.get("average_rent_received", 0.0)),
            average_jail_visits=float(item.get("average_jail_visits", 0.0)),
            finished_games=int(item.get("finished_games", 0)),
            finished_wins=int(item.get("finished_wins", 0)),
            cutoff_leads=int(item.get("cutoff_leads", 0)),
        )
        for item in data.get("players", [])
        if isinstance(item, dict)
    ]

    raw_cards = [item for item in data.get("cards", []) if isinstance(item, dict)]
    deck_draws: dict[str, int] = {}
    for item in raw_cards:
        deck = str(item.get("deck", ""))
        deck_draws[deck] = deck_draws.get(deck, 0) + int(item.get("draws", 0))
    cards = [
        CardSimulationSummary(
            deck=str(item.get("deck", "")),
            card_type=str(item.get("card_type", "Card")),
            card_text=str(item.get("card_text", "")),
            draws=int(item.get("draws", 0)),
            games_with_draw=int(item.get("games_with_draw", 0)),
            games=game_count,
            deck_draws=deck_draws.get(str(item.get("deck", "")), 0),
            drawer_cash_delta=int(item.get("drawer_cash_delta", 0)),
            other_players_cash_delta=int(item.get("other_players_cash_delta", 0)),
            total_player_cash_delta=int(item.get("total_player_cash_delta", 0)),
            free_parking_pot_delta=int(item.get("free_parking_pot_delta", 0)),
            movements=int(item.get("movements", 0)),
            jail_sends=int(item.get("jail_sends", 0)),
            get_out_cards=int(item.get("get_out_cards", 0)),
            biggest_gain=int(item.get("biggest_gain", 0)),
            biggest_loss=int(item.get("biggest_loss", 0)),
        )
        for item in raw_cards
    ]

    return SimulationCampaignResult(
        scenario_name=str(data.get("scenario", "Scénario")),
        config=config,
        games=games,
        property_summary=properties,
        player_summary=players,
        space_summary=spaces,
        property_investment_summary=investments,
        property_development_summary=developments,
        card_summary=cards,
    )


def simulation_report_from_dict(data: dict[str, Any]) -> SimulationComparisonResult:
    """Reconstruit un rapport complet de laboratoire depuis des données JSON.

    Entrées:
        data (dict[str, Any]): Objet JSON au format ``monopoly-simulation-report``.

    Sortie:
        SimulationComparisonResult: Rapport rechargeable sans resimulation.

    Lève:
        SimulationReportError: Si le format ou la structure principale est invalide.
    """
    if data.get("format") != "monopoly-simulation-report":
        raise SimulationReportError("Ce fichier n'est pas un rapport du laboratoire Monopoly.")
    try:
        version = int(data.get("version", 1))
    except (TypeError, ValueError) as error:
        raise SimulationReportError("Version de rapport invalide.") from error
    if version < 1 or version > 4:
        raise SimulationReportError(f"Version de rapport non prise en charge : {version}.")

    raw_config = data.get("config", {})
    if not isinstance(raw_config, dict):
        raise SimulationReportError("La configuration du rapport est invalide.")
    config = SimulationConfig(
        games_per_scenario=int(raw_config.get("games_per_scenario", 1)),
        player_count=int(raw_config.get("player_count", 4)),
        max_rounds=int(raw_config.get("max_rounds", 250)),
        base_seed=int(raw_config.get("base_seed", 0)),
        parallel_workers=int(raw_config.get("parallel_workers", 1)),
    )
    raw_campaigns = data.get("campaigns", [])
    if not isinstance(raw_campaigns, list) or not raw_campaigns:
        raise SimulationReportError("Le rapport ne contient aucune campagne.")
    campaigns = [
        _campaign_from_dict(item, config)
        for item in raw_campaigns
        if isinstance(item, dict)
    ]
    if not campaigns:
        raise SimulationReportError("Aucune campagne exploitable n'a été trouvée.")

    scenarios: list[SimulationScenario] = []
    raw_scenarios = data.get("scenarios", [])
    if isinstance(raw_scenarios, list):
        for item in raw_scenarios:
            if isinstance(item, dict):
                try:
                    scenarios.append(SimulationScenario.from_dict(item))
                except (TypeError, ValueError, KeyError):
                    continue
    if len(scenarios) != len(campaigns):
        scenarios = []
        for campaign in campaigns:
            scenario = SimulationScenario.standard()
            scenario.name = campaign.scenario_name
            scenarios.append(scenario)

    return SimulationComparisonResult(config, campaigns, scenarios)


def load_simulation_report(path: str | Path) -> SimulationComparisonResult:
    """Charge un rapport JSON précédemment exporté par le laboratoire.

    Entrées:
        path (str | Path): Fichier JSON à lire.

    Sortie:
        SimulationComparisonResult: Rapport restauré en mémoire.

    Lève:
        SimulationReportError: Si le JSON est illisible ou structurellement invalide.
    """
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SimulationReportError(f"Impossible de lire le rapport : {error}") from error
    if not isinstance(data, dict):
        raise SimulationReportError("La racine du rapport doit être un objet JSON.")
    return simulation_report_from_dict(data)


def _bar_svg(labels: list[str], values: list[float], title: str, suffix: str = "") -> str:
    """Produit un histogramme SVG autonome pour le rapport HTML.

    Entrées:
        labels (list[str]): Catégories horizontales.
        values (list[float]): Valeurs numériques correspondantes.
        title (str): Titre du graphique.
        suffix (str): Unité ajoutée dans les infobulles textuelles.

    Sortie:
        str: Fragment HTML contenant le SVG et ses libellés.
    """
    if not labels or not values:
        return f"<section class='chart'><h3>{escape(title)}</h3><p>Aucune donnée.</p></section>"
    width = 880
    height = 280
    left = 52
    top = 30
    bottom = 62
    usable_h = height - top - bottom
    usable_w = width - left - 16
    max_value = max(max(values), 1.0)
    bar_w = usable_w / max(1, len(values))
    pieces = [f"<section class='chart'><h3>{escape(title)}</h3><svg viewBox='0 0 {width} {height}' role='img'>"]
    pieces.append(f"<line x1='{left}' y1='{top}' x2='{left}' y2='{height-bottom}' class='axis'/>")
    pieces.append(f"<line x1='{left}' y1='{height-bottom}' x2='{width-12}' y2='{height-bottom}' class='axis'/>")
    for index, (label, value) in enumerate(zip(labels, values)):
        h = usable_h * max(0.0, value) / max_value
        x = left + index * bar_w + bar_w * 0.14
        y = height - bottom - h
        w = max(2.0, bar_w * 0.72)
        pieces.append(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' class='bar'>"
            f"<title>{escape(label)} : {value:.2f}{escape(suffix)}</title></rect>"
        )
        if len(labels) <= 12:
            pieces.append(
                f"<text x='{x+w/2:.1f}' y='{height-bottom+17}' text-anchor='middle' class='tick'>{escape(label[:16])}</text>"
            )
    pieces.append(f"<text x='{left-8}' y='{top+8}' text-anchor='end' class='tick'>{max_value:.1f}{escape(suffix)}</text>")
    pieces.append("</svg></section>")
    return "".join(pieces)


def _temperature_heat_color(ratio: float) -> str:
    """Convertit une intensité normalisée en couleur de heatmap type capteur.

    Entrées:
        ratio (float): Intensité normalisée entre 0.0 et 1.0.

    Sortie:
        str: Couleur hexadécimale allant du bleu foncé au rouge foncé.
    """
    value = min(1.0, max(0.0, ratio))
    stops = [
        (0.00, (8, 48, 107)),
        (0.25, (33, 113, 181)),
        (0.50, (107, 174, 214)),
        (0.68, (255, 237, 160)),
        (0.84, (253, 141, 60)),
        (1.00, (103, 0, 13)),
    ]
    for (left_pos, left_rgb), (right_pos, right_rgb) in zip(stops, stops[1:]):
        if value <= right_pos:
            span = max(1e-9, right_pos - left_pos)
            local = (value - left_pos) / span
            red = round(left_rgb[0] + (right_rgb[0] - left_rgb[0]) * local)
            green = round(left_rgb[1] + (right_rgb[1] - left_rgb[1]) * local)
            blue = round(left_rgb[2] + (right_rgb[2] - left_rgb[2]) * local)
            return f"#{red:02x}{green:02x}{blue:02x}"
    return "#67000d"


def _heatmap_svg(result: SimulationComparisonResult) -> str:
    """Produit une heatmap SVG des arrêts moyens sur les 40 cases.

    Entrées:
        result (SimulationComparisonResult): Comparaison de scénarios à représenter.

    Sortie:
        str: Fragment HTML autonome de heatmap.
    """
    if not result.campaigns:
        return ""
    rows = len(result.campaigns)
    values = [
        item.average_landings_per_game
        for campaign in result.campaigns
        for item in campaign.space_summary
    ]
    max_value = max(values, default=1.0) or 1.0
    width = 940
    left = 170
    cell_w = (width - left - 16) / 40
    row_h = 30
    height = 54 + rows * row_h
    parts = [f"<section class='chart wide'><h3>Heatmap — arrêts moyens par case</h3><svg viewBox='0 0 {width} {height}'>"]
    for case in range(40):
        x = left + case * cell_w + cell_w / 2
        parts.append(f"<text x='{x:.1f}' y='22' text-anchor='middle' class='tick'>{case}</text>")
    for row, campaign in enumerate(result.campaigns):
        y = 34 + row * row_h
        parts.append(f"<text x='{left-8}' y='{y+18}' text-anchor='end' class='rowlabel'>{escape(campaign.scenario_name[:24])}</text>")
        by_index = {item.index: item for item in campaign.space_summary}
        for case in range(40):
            value = by_index.get(case).average_landings_per_game if case in by_index else 0.0
            ratio = min(1.0, max(0.0, value / max_value))
            color = _temperature_heat_color(ratio)
            x = left + case * cell_w
            parts.append(
                f"<rect x='{x:.1f}' y='{y:.1f}' width='{cell_w-1:.1f}' height='{row_h-3}' "
                f"fill='{color}'><title>{escape(campaign.scenario_name)} • case {case} : {value:.2f} arrêts/partie</title></rect>"
            )
    parts.append("</svg></section>")
    return "".join(parts)


def export_html_report(result: SimulationComparisonResult, path: str | Path) -> Path:
    """Exporte un rapport HTML autonome avec tableaux et graphiques SVG.

    Entrées:
        result (SimulationComparisonResult): Rapport courant du laboratoire.
        path (str | Path): Destination ``.html``.

    Sortie:
        Path: Chemin du rapport HTML créé.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    summaries = [campaign.summary_dict() for campaign in result.campaigns]
    labels = [campaign.scenario_name for campaign in result.campaigns]

    summary_rows = "".join(
        "<tr>"
        f"<td>{escape(campaign.scenario_name)}</td>"
        f"<td>{len(campaign.games)}</td>"
        f"<td>{campaign.finish_rate:.1f}%</td>"
        f"<td>{campaign.average_rounds:.1f}</td>"
        f"<td>{campaign.round_percentile(90):.1f}</td>"
        f"<td>{campaign.average_rent:.0f}$</td>"
        f"<td>{campaign.global_property_roi_percent:.1f}%</td>"
        f"<td>{escape(campaign.most_landed_space)}</td>"
        "</tr>"
        for campaign in result.campaigns
    )

    deck_rows: list[str] = []
    for campaign in result.campaigns:
        for deck, label in (("chance", "Chance"), ("community_chest", "Communauté")):
            cards = [item for item in campaign.card_summary if item.deck == deck]
            draws = sum(item.draws for item in cards)
            delta = sum(item.drawer_cash_delta for item in cards)
            pot = sum(item.free_parking_pot_delta for item in cards)
            per_game = draws / len(campaign.games) if campaign.games else 0.0
            per_draw = delta / draws if draws else 0.0
            deck_rows.append(
                "<tr>"
                f"<td>{escape(campaign.scenario_name)}</td><td>{label}</td>"
                f"<td>{draws}</td><td>{per_game:.2f}</td><td>{per_draw:+.1f}$</td><td>{pot:+d}$</td>"
                "</tr>"
            )

    generated = (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Rapport laboratoire Monopoly</title><style>"
        "body{font-family:Arial,sans-serif;margin:0;background:#f4f6f5;color:#1f2933}"
        "main{max-width:1180px;margin:auto;padding:28px}h1{margin-bottom:6px}"
        ".muted{color:#66737d}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}"
        ".card,.chart{background:white;border:1px solid #d8dfdc;border-radius:10px;padding:16px;margin:16px 0;box-shadow:0 2px 8px #0000000c}"
        ".wide{grid-column:1/-1}table{width:100%;border-collapse:collapse;background:white}"
        "th,td{padding:8px 10px;border-bottom:1px solid #e5e9e7;text-align:right;font-size:13px}"
        "th:first-child,td:first-child{text-align:left}th{background:#edf3f0}"
        "svg{width:100%;height:auto}.axis{stroke:#8b9791;stroke-width:1}.bar{fill:#4d9471}"
        ".tick{font-size:10px;fill:#53615a}.rowlabel{font-size:11px;fill:#25332c;font-weight:bold}"
        "@media(max-width:800px){.grid{grid-template-columns:1fr}}"
        "</style></head><body><main>"
        "<h1>Laboratoire Monopoly — rapport V21.8</h1>"
        f"<p class='muted'>{result.config.games_per_scenario} parties/scénario • {result.config.player_count} joueurs • seed {result.config.base_seed} • "
        + ("tours illimités" if result.config.max_rounds == 0 else f"{result.config.max_rounds} tours max")
        + "</p>"
        "<section class='card'><h2>Comparaison des scénarios</h2><table><thead><tr>"
        "<th>Scénario</th><th>Parties</th><th>Fin</th><th>Tours moy.</th><th>P90</th><th>Loyers moy.</th><th>ROI global</th><th>Case la + fréquentée</th>"
        "</tr></thead><tbody>" + summary_rows + "</tbody></table></section>"
        "<div class='grid'>"
        + _bar_svg(labels, [float(item["average_rounds"]) for item in summaries], "Durée moyenne", " tours")
        + _bar_svg(labels, [float(item["finish_rate"]) for item in summaries], "Parties terminées", " %")
        + _bar_svg(labels, [float(item["global_property_roi_percent"]) for item in summaries], "ROI global des biens", " %")
        + _bar_svg(labels, [float(item["average_rent"]) for item in summaries], "Loyers moyens", " $")
        + _heatmap_svg(result)
        + "</div>"
        "<section class='card'><h2>Chance &amp; Communauté entre scénarios</h2><table><thead><tr>"
        "<th>Scénario</th><th>Paquet</th><th>Tirages</th><th>Tirages/partie</th><th>Impact cash/tirage</th><th>Cagnotte cumulée</th>"
        "</tr></thead><tbody>" + "".join(deck_rows) + "</tbody></table></section>"
        "<section class='card'><h2>Méthodologie</h2><p>Les décisions du laboratoire restent neutres/aléatoires et reproductibles. Ce rapport ne contient aucune stratégie ni IA. Les rapports JSON V21.8 peuvent être rechargés dans l'application sans resimuler.</p></section>"
        "</main></body></html>"
    )
    destination.write_text(generated, encoding="utf-8")
    return destination
