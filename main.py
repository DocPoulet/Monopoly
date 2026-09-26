"""Point d'entrée graphique principal du projet Monopoly."""

from ui import MonopolyApp


def main() -> None:
    """Lance l'application graphique Tkinter.

    Entrées:
        Aucune.

    Sortie:
        None: L'application reste active jusqu'à la fermeture de sa fenêtre.
    """
    MonopolyApp().run()


if __name__ == "__main__":
    main()
