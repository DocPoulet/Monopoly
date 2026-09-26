# Monopoly POO — V3 avec interface graphique

Cette version ajoute une interface graphique **Tkinter** au moteur POO existant.

Le moteur et l'interface restent séparés :

```text
monopoly_poo_gui/
├── main.py                 # lance l'interface graphique
├── console.py              # ancienne interface terminal, toujours disponible
├── monopoly/               # moteur du jeu indépendant de l'affichage
│   ├── game.py
│   ├── board.py
│   ├── player.py
│   ├── properties.py
│   ├── spaces.py
│   ├── rules.py
│   ├── auction.py
│   ├── cards.py
│   ├── strategies.py
│   ├── simulation.py
│   └── statistics.py
├── ui/
│   ├── __init__.py
│   ├── app.py              # cycle de vie de l'application
│   ├── game_window.py      # écran principal et boutons d'action
│   ├── board_view.py       # dessin du plateau et des pions
│   └── dialogs.py          # nouvelle partie, enchères, propriétés
└── tests/
```

## Lancer l'interface

Tkinter est inclus dans la plupart des installations Python classiques.

```bash
python main.py
```

## Mode console

L'ancienne interface console reste disponible :

```bash
python console.py
```

## Ce que permet l'interface

- création d'une partie de 2 à 6 joueurs ;
- plateau graphique complet de 40 cases ;
- pions visibles sur le plateau ;
- affichage de l'argent, position, biens, cartes et état de chaque joueur ;
- lancer des dés ;
- affichage des doubles et passages par Départ ;
- choix de prison :
  - tenter un double ;
  - payer 50 ;
  - utiliser une carte de sortie de prison ;
- achat d'une propriété libre ;
- enchères entre les joueurs ;
- gestion des propriétés :
  - construire ;
  - vendre un bâtiment ;
  - hypothéquer ;
  - déshypothéquer ;
- journal détaillé des événements ;
- affichage du vainqueur.

## Architecture

L'interface ne contient pas les règles du Monopoly.

Par exemple, un clic sur « Acheter » appelle le moteur :

```python
game.rules.buy_property(player, space)
```

Le calcul du loyer reste dans les classes de biens, la prison reste dans `Game` et
`Rules`, et le dessin du plateau reste dans `ui/`.

Cette séparation est importante pour la suite : les futures simulations et IA
pourront continuer à utiliser directement le moteur sans ouvrir de fenêtre.

## Documentation

Comme dans la version précédente, chaque classe, fonction et méthode possède
une docstring en français expliquant son rôle, ses entrées et ses sorties.
Le test `tests/test_documentation.py` contrôle automatiquement cette règle.


## Améliorations graphiques V2

Cette révision de l'interface ajoute :

- des dés graphiques avec leurs points ;
- une fiche de propriété avant chaque achat avec le barème complet ;
- des boutons Acheter / Enchères directement sous la fiche ;
- une révélation graphique des cartes Chance ;
- une révélation graphique des cartes Caisse de communauté ;
- la prise en charge des enchaînements de cartes dans l'ordre réel de pioche ;
- des couleurs différenciées pour les cases spéciales ;
- des piles Chance / Caisse décoratives au centre du plateau ;
- des ombres légères et un plateau mieux détaché du fond ;
- un marqueur coloré du propriétaire sur les biens ;
- une mise en évidence du joueur courant dans le tableau ;
- une présentation plus homogène des panneaux et boutons.

Le moteur expose désormais `game.drawn_cards_this_turn`, une liste d'événements
structurés permettant à une interface, un replay ou de futures statistiques de
savoir exactement quelles cartes ont été piochées pendant le tour.


## Interface intégrée V3

Cette révision retire plusieurs fenêtres et boutons redondants :

- il n'existe plus de bouton **Lancer les dés** : les deux dés sont eux-mêmes cliquables ;
- en prison, cliquer sur les dés correspond à la tentative de double ;
- **Payer 50 $** et **Utiliser carte sortie de prison** apparaissent uniquement sous les dés lorsqu'ils sont utiles ;
- les boutons **Acheter** et **Enchères** ont disparu de la barre latérale ;
- la fiche de propriété apparaît directement au centre du plateau et contient seule ces deux décisions ;
- aucune fenêtre séparée n'est ouverte pour présenter la propriété ;
- Chance et Caisse de communauté ne déclenchent plus de popup ;
- le dernier tirage de chaque paquet est affiché directement dans sa zone centrale sur le plateau.

La fenêtre d'enchère elle-même reste modale pour le moment car plusieurs joueurs doivent y enchérir successivement ; le déclenchement de cette enchère se fait uniquement depuis la fiche de propriété intégrée.


## Ajustements GUI V4

- correction du débordement horizontal des zones Chance et Caisse de communauté ;
- calcul des cartes centrales à partir des limites réelles de la zone intérieure ;
- enchères entièrement intégrées au plateau, sans fenêtre secondaire ;
- affichage dans le panneau d'enchère du meilleur prix, du joueur courant, de son budget et des participants encore en lice ;
- validation des offres directement dans le panneau ;
- dés et gestion des propriétés bloqués pendant une enchère.

## Amélioration graphique V5 — enchères

La page d'enchère a été harmonisée avec les fiches de propriétés :

- le bandeau du panneau d'enchère reprend automatiquement la couleur du bien ;
- la fiche complète de la propriété reste visible à gauche pendant toute l'enchère ;
- cette fiche passe en lecture seule et conserve le prix, les loyers, le coût des maisons et l'hypothèque ;
- le panneau interactif d'enchère reste à droite avec les offres et les joueurs encore en lice ;
- aucun dialogue ou nouvelle fenêtre n'est ouvert.
