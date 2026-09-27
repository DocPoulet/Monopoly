"""Objets structurés utilisés pendant la résolution d'une dette."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DebtManagementResult:
    """Résume les ressources préparées pour régler une dette.

    Entrées:
        cash_ready (bool): Indique si les liquidités restantes suffisent après
            prise en compte des biens éventuellement cédés au créancier.
        property_credit (int): Valeur de dette déjà éteinte par cession de biens.
        bankruptcy_requested (bool): Indique que le joueur a choisi la faillite
            immédiate parce que le remboursement maximal reste insuffisant.

    Sortie:
        DebtManagementResult: Résultat immuable exploitable par les règles de paiement.
    """

    cash_ready: bool
    property_credit: int = 0
    bankruptcy_requested: bool = False

    def __bool__(self) -> bool:
        """Expose ``cash_ready`` pour conserver la compatibilité avec les anciens booléens.

        Entrées:
            Aucune.

        Sortie:
            bool: Valeur de ``cash_ready``.
        """
        return self.cash_ready
