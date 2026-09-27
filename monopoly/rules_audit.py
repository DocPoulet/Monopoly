"""Catalogue lisible des règles auditées et des simplifications assumées."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleAuditItem:
    """Décrit une règle vérifiée ou une simplification connue.

    Entrées:
        title (str): Nom court de la règle.
        detail (str): Comportement appliqué par le moteur.
        status (str): ``"ok"`` pour une règle couverte ou ``"simplified"`` pour
            une adaptation logicielle explicitement assumée.

    Sortie:
        RuleAuditItem: Élément immuable affichable dans le panneau de règles.
    """

    title: str
    detail: str
    status: str = "ok"

    @property
    def status_label(self) -> str:
        """Retourne le libellé français associé au statut d'audit.

        Entrées:
            Aucune.

        Sortie:
            str: ``Vérifié`` ou ``Adaptation``.
        """
        return "Vérifié" if self.status == "ok" else "Adaptation"


AUDITED_RULES: tuple[RuleAuditItem, ...] = (
    RuleAuditItem(
        "Achat et enchères",
        (
            "Un bien libre peut être acheté au prix indiqué. Avec les enchères "
            "activées, un bien refusé est proposé à tous les joueurs actifs, y compris "
            "celui qui l'a refusé."
        ),
    ),
    RuleAuditItem(
        "Loyers et hypothèques",
        (
            "Aucun loyer n'est dû sur un bien hypothéqué. Un terrain non hypothéqué "
            "d'un monopole conserve son double loyer de base même si un autre terrain "
            "du groupe est hypothéqué."
        ),
    ),
    RuleAuditItem(
        "Prison",
        (
            "Un double permet de sortir sans lancer supplémentaire. Après le nombre "
            "maximal de tentatives, l'amende est obligatoire puis le joueur avance avec "
            "le lancer effectué. Les loyers et la gestion patrimoniale restent possibles."
        ),
    ),
    RuleAuditItem(
        "Maisons et hôtels",
        (
            "La construction et la revente se font uniformément dans le groupe. "
            "Un hôtel exige quatre maisons sur chaque terrain du groupe."
        ),
    ),
    RuleAuditItem(
        "Stock de bâtiments",
        (
            "Le profil classique possède 32 maisons et 12 hôtels. Le stock peut être "
            "personnalisé ou rendu illimité ; une pénurie limitée peut déclencher une enchère."
        ),
    ),
    RuleAuditItem(
        "Hypothèques transférées",
        (
            "Le profil classique applique 10 % d'intérêt aux hypothèques transférées. "
            "Le taux et le maintien de l'hypothèque lors du transfert sont configurables."
        ),
    ),
    RuleAuditItem(
        "Faillite",
        (
            "Les bâtiments sont rendus à moitié prix. Envers un joueur, les actifs lui "
            "sont transférés ; envers la banque, les biens reviennent à la banque et sont "
            "mis aux enchères lorsque les enchères sont actives."
        ),
    ),
    RuleAuditItem(
        "Parc Gratuit classique",
        (
            "Le Parc Gratuit ne verse rien avec le profil classique. Un bonus éventuel "
            "est clairement traité comme une variante personnalisée."
        ),
    ),
    RuleAuditItem(
        "Perception du loyer",
        (
            "Le loyer peut être automatique ou manuel. En mode manuel, le propriétaire "
            "doit explicitement réclamer le montant ou y renoncer."
        ),
    ),
    RuleAuditItem(
        "Moment des transactions",
        (
            "Les constructions, hypothèques et échanges sont réalisés via les panneaux "
            "du joueur courant plutôt qu'à n'importe quel instant entre deux lancers."
        ),
        status="simplified",
    ),
    RuleAuditItem(
        "Pénurie de bâtiments",
        (
            "Le logiciel détecte les joueurs légalement capables de construire puis "
            "leur permet d'abandonner l'enchère ; il ne demande pas leurs intentions "
            "avant de constater la pénurie."
        ),
        status="simplified",
    ),
    RuleAuditItem(
        "Vente normale d'un hôtel",
        (
            "La descente hôtel → quatre maisons exige quatre maisons disponibles à la "
            "banque. La liquidation complète spéciale d'une faillite est gérée séparément."
        ),
        status="simplified",
    ),
)


def audited_rule_count() -> int:
    """Compte les règles marquées comme vérifiées.

    Entrées:
        Aucune.

    Sortie:
        int: Nombre d'éléments dont le statut vaut ``ok``.
    """
    return sum(item.status == "ok" for item in AUDITED_RULES)


def simplified_rule_count() -> int:
    """Compte les adaptations logicielles explicitement documentées.

    Entrées:
        Aucune.

    Sortie:
        int: Nombre d'éléments dont le statut vaut ``simplified``.
    """
    return sum(item.status == "simplified" for item in AUDITED_RULES)
