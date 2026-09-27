# Monopoly POO — V16.3

Projet Python de Monopoly orienté objet avec interface Tkinter. Le projet privilégie
actuellement le **gameplay humain, la fidélité des règles et la qualité de l'interface**.
Les couches simulation/IA existent comme points d'extension, mais ne sont pas la priorité
pour le moment.

---

## Presets de règles et limite de construction — V16.3

### Achat d’une propriété en mode construction à l’atterrissage

Lorsque **Construction partout** est désactivée, acheter une propriété libre sur laquelle le
joueur vient de tomber **ne permet plus de construire immédiatement**. L’achat termine la
décision immobilière de cet atterrissage. Pour construire sur cette propriété, il faudra y
retomber lors d’un futur déplacement.

Cette correction évite également de pouvoir construire simplement parce que le pion était déjà
stationné sur la case avant le lancer de dés.

### Maximum de constructions à la fois

Une nouvelle règle **Max constructions à la fois** accepte une valeur de `1` à `4`. Elle limite
le nombre de maisons proposées dans une décision groupée après atterrissage.

- `1` : une seule maison maximum par décision ;
- `2` ou `3` : quantité groupée plafonnée à cette valeur ;
- `4` : comportement V16.1 ;
- un hôtel reste toujours une construction unique et séparée.

L’équilibre des constructions, le stock bancaire et l’argent disponible peuvent encore réduire
ce maximum.

### Presets de paramètres

L’écran **Personnaliser les règles** possède désormais une section **Presets de règles**.

Elle permet de :

- **Charger** un preset enregistré localement ;
- **Sauvegarder preset** pour mémoriser le profil courant entre plusieurs parties ;
- **Importer JSON** pour ajouter un preset provenant d’un autre fichier ;
- **Exporter le profil courant** dans un JSON portable.

Les presets utilisent un format versionné distinct des sauvegardes de partie et contiennent
l’intégralité de `GameOptions`, y compris les règles avancées. Les imports sont copiés dans la
bibliothèque locale afin de rester disponibles même si le fichier d’origine est supprimé.

---

## Paiement d'une dette en propriétés — V16.2

Une nouvelle option **Paiement de dette en propriétés** est disponible dans
**Personnaliser les règles**. Elle est désactivée dans le profil classique.

Quand elle est active et qu'une dette est due **à un autre joueur**, le panneau de dette
possède une troisième colonne **Céder au créancier à 100 %**.

### Valeur d'une cession

Un bien non hypothéqué cédé directement compte dans la dette pour :

```text
100 % du prix actuel du bien
+ 100 % du coût d'achat des bâtiments encore présents
```

Exemple : un terrain à `100 $` avec deux maisons coûtant `50 $` chacune compte pour
`200 $` dans la dette.

Les maisons ou l'hôtel encore présents restent sur la propriété lorsqu'elle passe au
créancier. Le stock de la banque n'est donc pas modifié.

Avant de céder le bien, le débiteur peut toujours revendre légalement des bâtiments avec
le bouton de revente existant. Ces bâtiments rapportent alors le **pourcentage de revente**
configuré, puis la propriété avec les bâtiments restants est valorisée à 100 %.

Un bien déjà hypothéqué n'est pas cessible par cette règle : sa valeur a déjà été
monétisée par l'hypothèque et ne peut donc pas être comptée une seconde fois.

Si la valeur d'un bien dépasse le solde de la dette, le bien est tout de même transféré
en entier ; aucun rendu de monnaie n'est créé.

### Faillite détectée immédiatement

Le panneau calcule maintenant la **capacité maximale de remboursement restante** avant
d'obliger le joueur à liquider ses actifs un par un. Ce calcul tient compte :

- du cash disponible ;
- de la revente possible des bâtiments ;
- des hypothèques encore possibles ;
- des cessions de propriétés au créancier lorsque l'option est active.

Si cette capacité maximale reste inférieure à la dette, le bouton **Faillite** est activé
immédiatement, même s'il reste encore des bâtiments ou des biens qui pourraient être
vendus individuellement. Le joueur n'est donc plus obligé d'effectuer des opérations
inutiles avant une faillite déjà certaine.

---

## Corrections visuelles et construction à l'atterrissage — V16.1

### Cagnotte Parc Gratuit au centre du plateau

Lorsque l'option **Cagnotte cartes Parc Gratuit** est active, le centre du plateau affiche
maintenant :

- une petite pile de billets ;
- une pile qui grandit par paliers selon le montant contenu ;
- le montant exact de la cagnotte juste en dessous.

Les paliers visuels sont bornés pour garder le plateau lisible, mais le montant affiché reste
toujours exact.

### Construction uniquement après être tombé sur la propriété

La variante **Construction partout = non** a été corrigée. Être simplement stationné sur une
propriété avant le lancer ne donne plus le droit d'y construire.

Le droit de construire existe uniquement après un véritable atterrissage pendant le tour.
Un menu intégré, similaire à la décision d'achat d'une propriété, apparaît alors si une
construction est possible.

Ce menu permet :

- de choisir le nombre de maisons à acheter en une seule décision ;
- au maximum **4 maisons** dans cette décision ;
- ou, si quatre maisons sont déjà présentes, d'acheter **1 hôtel** ;
- de ne jamais acheter `4 maisons + 1 hôtel` dans la même décision ;
- de passer sans construire.

Le moteur continue à respecter l'équilibre des constructions, l'argent disponible et le stock
de la banque. Si l'achat de la propriété sur laquelle le joueur vient de tomber complète les
conditions de construction, le même menu peut apparaître juste après cet achat.

### Cartes de propriété

Les fiches de propriété affichent maintenant explicitement **LOYER ACTUEL**. Cette valeur suit
les maisons, l'hôtel, le monopole, l'hypothèque et le pourcentage global de loyer. La ligne du
niveau de développement courant est également mise en évidence dans le barème.

---

## Lancer le jeu

```bash
python main.py
```

Mode console historique :

```bash
python console.py
```

Tests :

```bash
python -m unittest discover -s tests -v
```

---

## Parcours principal

```text
Accueil
  ├─ Nouvelle partie
  │    ├─ 2 à 6 joueurs
  │    └─ Options de partie
  │          ↓
  │       Plateau
  │
  └─ Charger une partie
       ├─ liste des sauvegardes locales
       ├─ aperçu joueurs / tour / date
       └─ chargement du JSON sélectionné
```

Tout le parcours principal reste dans la même fenêtre. Les panneaux importants du jeu
(propriétés, échanges, enchères, historique et fin de partie) sont intégrés au plateau.

---

# Nouveautés V13

## Consultation directe du plateau

Une case achetable peut maintenant être **cliquée directement**.

La fiche de consultation affiche notamment :

- prix d'achat ;
- valeur hypothécaire ;
- barème des loyers ;
- propriétaire actuel ;
- loyer actuel ;
- maisons ou hôtel ;
- état hypothéqué et coût de levée.

Cette consultation est en lecture seule et ne remplace pas le menu de gestion du
patrimoine.

## Dette entièrement gérée par le joueur

Lorsqu'un paiement dépasse l'argent liquide disponible, l'interface ne choisit plus les
actifs à liquider à la place du joueur.

Le dialogue de dette indique :

- argent disponible ;
- somme nécessaire ;
- manque restant ;
- bâtiments actuellement vendables ;
- remboursement obtenu pour chaque vente ;
- biens actuellement hypothécables ;
- valeur obtenue pour chaque hypothèque.

Le joueur choisit **chaque bâtiment vendu** et **chaque propriété hypothéquée**. Les listes
sont recalculées après chaque opération afin de respecter automatiquement les règles de
construction/vente uniforme.

La faillite n'est proposée que lorsqu'il n'existe plus de bâtiment légalement vendable ni
de bien hypothécable permettant de poursuivre la liquidation.

Le moteur reste indépendant de Tkinter : sans interface, le comportement automatique
historique reste disponible pour les tests et les futurs traitements sans GUI.

## Propriétés hypothéquées reçues

Lorsqu'un joueur reçoit une propriété hypothéquée après un échange ou une faillite envers
un joueur, il choisit désormais pour chaque bien entre :

- **conserver l'hypothèque** : paiement immédiat de 10 % de la valeur hypothécaire ;
- **lever immédiatement l'hypothèque** : paiement du principal + 10 %.

Si l'hypothèque est conservée puis levée plus tard, le coût normal de levée applique à
nouveau les intérêts prévus.

## Fin de partie enrichie

La fin de partie n'utilise plus une simple boîte d'information. Un panneau intégré affiche :

- vainqueur ;
- raison de la fin de partie ;
- nombre de tours ;
- cartes tirées ;
- achats ;
- constructions ;
- échanges ;
- plus gros loyer enregistré ;
- argent final par joueur ;
- valeur nette estimée ;
- nombre de propriétés ;
- loyers payés et reçus ;
- bâtiments construits.

Depuis ce bilan, il est possible d'ouvrir directement l'historique détaillé puis de revenir
au résultat final.

## Historique filtrable

Le panneau **Historique / Stats** possède maintenant :

- filtre par catégorie d'événement ;
- navigation `Précédent` / `Suivant` ;
- détail des données structurées de chaque événement ;
- statistiques globales ;
- statistiques par joueur.

Catégories suivies notamment : tours, cartes, achats, enchères, loyers, constructions,
ventes de bâtiments, hypothèques, échanges et faillites.

Il s'agit pour l'instant d'une **relecture structurée du journal** ; le plateau n'est pas
encore reconstruit visuellement à chaque ancien tour.

## Sauvegardes avec aperçu

Les sauvegardes JSON contiennent désormais des métadonnées :

- date de sauvegarde ;
- joueurs ;
- numéro de tour ;
- nombre de joueurs actifs ;
- vainqueur éventuel.

L'écran **Charger une partie** liste les fichiers présents dans le dossier local `saves/`
et affiche un aperçu avant chargement. Un bouton permet également de parcourir un fichier
JSON situé ailleurs.

La sauvegarde complète conserve :

- joueurs, argent, position, prison et faillite ;
- propriétés, hypothèques, maisons et hôtels ;
- stock de la banque ;
- joueur courant et série de doubles ;
- ordre exact des cartes ;
- cartes Sortie de prison détenues ;
- file d'enchères de faillite ;
- état du générateur aléatoire ;
- historique structuré ;
- options de partie.

La sauvegarde reste désactivée pendant une décision intermédiaire afin de ne pas figer une
interface dans un état incomplet.

## Numérotation des tours — V14.1

Un **tour** correspond maintenant à un tour de table complet, et non à l'action d'un seul joueur.

Exemple à deux joueurs :

```text
Alice joue — Tour 1
Bob joue   — Tour 1
Alice joue — Tour 2
Bob joue   — Tour 2
Alice joue — Tour 3
```

Un lancer supplémentaire obtenu grâce à un double reste dans le **même** numéro de tour.
La limite optionnelle de tours utilise également cette définition : une limite de 20 signifie
20 tours de table complets. Les statistiques globales et l'historique utilisent le même comptage.

---

## Règles avancées configurables — V16

La personnalisation pré-partie couvre maintenant aussi l'économie et plusieurs variantes
de fonctionnement du moteur :

- **prix des propriétés (%)** : modifie le prix des titres, donc aussi leur valeur hypothécaire ;
- **prix des loyers (%)** : multiplicateur global appliqué aux terrains, gares, compagnies et loyers spéciaux ;
- **monopole nécessaire pour construire** : désactivé, un joueur peut développer uniquement les terrains qu'il possède dans le groupe ;
- **stock maisons / hôtels** : réglages séparés, avec `0 = illimité` ;
- **hypothèques** : possibilité d'interdire toute nouvelle hypothèque ;
- **taxe de déshypothèque (%)** : remplace le taux fixe de 10 % ;
- **hypothèques transférées** : désactivé, un bien transféré arrive non hypothéqué et sans frais de transfert ;
- **prix de revente des bâtiments (%)** : remplace le remboursement classique de 50 % ;
- **loyer automatique** : désactivé, le propriétaire doit cliquer sur **Réclamer** ou **Renoncer** ;
- **construction partout** : désactivé, on ne peut construire que sur la propriété actuellement occupée par son pion ;
- **cagnotte Parc Gratuit** : les paiements à la banque provoqués pendant la résolution d'une carte Chance/Caisse de communauté alimentent une cagnotte. Les transferts vers un autre joueur n'y entrent jamais. Le joueur qui tombe sur Parc Gratuit récupère toute la cagnotte, qui revient ensuite à zéro.

Le bonus fixe de Parc Gratuit existant peut être combiné à cette cagnotte. Les stocks, la
cagnotte et toutes ces règles sont conservés dans les sauvegardes JSON.

---

## Audit des règles et panneau en partie — V15

La V15 consolide le moteur avant toute nouvelle fonctionnalité majeure.

Un bouton **Règles de la partie** est disponible dans la zone de gestion pendant une
partie. Il ouvre un panneau intégré qui présente :

- le profil `Classique` ou `Personnalisé` ;
- toutes les valeurs actives : argent de départ, Départ, prison, doubles, enchères,
  Parc Gratuit et limite de tours ;
- les mécaniques vérifiées pendant l'audit ;
- les adaptations logicielles encore assumées explicitement.

L'audit a notamment vérifié et testé :

- enchère ouverte à tous les joueurs actifs, y compris celui ayant refusé l'achat direct ;
- aucun loyer sur un bien hypothéqué ;
- double loyer d'un terrain nu d'un monopole même si un autre terrain du groupe est hypothéqué ;
- perception des loyers et gestion du patrimoine pendant la prison ;
- sortie de prison par double sans lancer supplémentaire ;
- paiement obligatoire et déplacement après le dernier échec de prison ;
- construction et revente uniformes ;
- stocks physiques de 32 maisons et 12 hôtels ;
- intérêts sur les hypothèques transférées ;
- transfert des cartes Sortie de prison au créancier lors d'une faillite.

### Corrections issues de l'audit

Deux comportements ont été corrigés :

1. **Paiement volontaire de sortie de prison** : un joueur qui manque de liquidités peut
   maintenant vendre/hypothéquer légalement des actifs pour réunir l'amende avant de lancer.
2. **Carte prochaine compagnie** : le lancer spécial n'est effectué que si une compagnie
   adverse non hypothéquée doit réellement facturer le loyer `10× les dés`. Une compagnie
   libre, personnelle ou hypothéquée ne consomme plus un lancer aléatoire inutile.

### Adaptations logicielles documentées

Le panneau signale aussi les différences intentionnelles avec un jeu physique :

- les loyers sont perçus automatiquement ;
- les transactions et constructions passent par l'interface du joueur courant ;
- la pénurie de bâtiments invite les joueurs éligibles à l'enchère, qui peuvent ensuite
  abandonner s'ils ne souhaitent pas construire ;
- la vente normale d'un hôtel vers quatre maisons reste conditionnée par la disponibilité
  de quatre maisons à la banque ; la liquidation de faillite est traitée séparément.

Références d'audit : règles classiques Hasbro/Parker Brothers, notamment les sections
`BUYING PROPERTY`, `PAYING RENT`, `JAIL`, `HOUSES`, `HOTELS`, `BUILDING SHORTAGES`,
`MORTGAGES` et `BANKRUPTCY`.

---

## Personnaliser les règles avant la partie — V14

L'écran **Nouvelle partie** contient maintenant un bouton **Personnaliser les règles**.
Il ouvre un écran dédié dans la même fenêtre, sans perdre les noms de joueurs déjà saisis.

Les règles modifiables sont :

- argent de départ ;
- salaire reçu en passant par Départ ;
- amende de prison ;
- nombre maximal de tentatives en prison ;
- nombre de doubles consécutifs avant envoi en prison ;
- enchères immobilières activées ou désactivées ;
- bonus optionnel du Parc Gratuit ;
- limite optionnelle de tours.

Le bouton **Règles classiques** restaure immédiatement le profil standard :

```text
Argent de départ            1500 $
Passage par Départ           200 $
Amende de prison              50 $
Tentatives max en prison       3
Doubles avant prison           3
Enchères                     oui
Bonus Parc Gratuit             0 $
Limite de tours                0
```

Au retour sur le choix des joueurs, un résumé indique si la partie utilise le profil
**Règles classiques** ou un profil **Personnalisé**. Les réglages sont utilisés directement
par le moteur et conservés dans les sauvegardes JSON.

---

## Plateau

- 40 cases ;
- 2 à 6 joueurs ;
- pions colorés ;
- groupes de couleur ;
- propriétaires visibles ;
- loyer actuel visible sur chaque bien possédé ;
- `4× dés` / `10× dés` pour les compagnies ;
- maisons et hôtels visibles ;
- hypothèques visibles ;
- clic sur les propriétés pour consulter leur fiche ;
- zones Chance et Caisse de communauté ;
- dernière carte tirée affichée au centre.

## Dés et prison

Les dés sont cliquables.

- lancer normal en cliquant sur un dé ;
- tentative de double depuis la prison ;
- paiement volontaire de 50 $ ;
- utilisation d'une carte Sortie de prison ;
- sortie obligatoire après la troisième tentative ratée ;
- pas de lancer supplémentaire lorsqu'un double sert à sortir de prison.

## Achat et enchères

Lorsqu'un joueur arrive sur un bien libre, sa fiche apparaît au centre.

Avec les règles classiques :

```text
Acheter
   ou
Enchères
```

Si l'option d'enchères immobilières est désactivée :

```text
Acheter
   ou
Passer
```

Les enchères de propriétés et les enchères dues à une faillite sont intégrées au plateau.

## Gestion du patrimoine

Le bouton **Gérer mes propriétés** ouvre un panneau intégré, pas une nouvelle fenêtre.

Il permet :

- construction ;
- vente de bâtiment ;
- hypothèque ;
- déshypothèque ;
- consultation détaillée du groupe ;
- contrôle du stock de la banque.

## Échanges

Un échange peut contenir dans les deux sens :

- argent ;
- terrains ;
- gares ;
- compagnies ;
- cartes Sortie de prison.

Un terrain appartenant à un groupe comportant encore un bâtiment ne peut pas être cédé.

---

# Règles implémentées

## Déplacements

- deux dés ;
- salaire de 200 $ au passage par Départ ;
- doubles ;
- trois doubles consécutifs → prison ;
- déplacements absolus et relatifs par cartes ;
- recul de trois cases ;
- résolution en chaîne lorsqu'une carte mène vers une nouvelle case à effet.

## Propriétés et loyers

- achat direct ;
- loyers des terrains ;
- loyers des gares ;
- loyers des compagnies ;
- double loyer nu avec groupe complet ;
- aucun loyer sur un bien hypothéqué ;
- le double loyer reste applicable à une propriété non hypothéquée d'un groupe complet même
  si une autre propriété du groupe est hypothéquée.

## Maisons et hôtels

- constructions uniformes ;
- ventes uniformes en sens inverse ;
- 32 maisons ;
- 12 hôtels ;
- conversion de quatre maisons vers un hôtel ;
- retour des bâtiments à la banque ;
- impossibilité de casser un hôtel si les maisons nécessaires ne sont pas disponibles ;
- enchères de bâtiments en cas de pénurie disputée.

## Hypothèques

- hypothèque uniquement après retrait de tous les bâtiments du groupe ;
- aucun loyer sur le bien hypothéqué ;
- levée avec principal + 10 % ;
- transfert d'un bien hypothéqué avec traitement immédiat des intérêts ;
- choix de déshypothèque immédiate après transfert.

## Faillite

### Dette envers un joueur

- liquidation des bâtiments à moitié prix ;
- argent restant transmis au créancier ;
- propriétés transférées au créancier ;
- cartes Sortie de prison transférées ;
- traitement des hypothèques reçues par le créancier.

### Dette envers la banque

Avec les enchères immobilières classiques activées :

- bâtiments retournés à la banque ;
- cartes Sortie de prison retournées aux paquets ;
- propriétés libérées ;
- propriétés revendues successivement aux enchères.

Si la variante **enchères immobilières désactivées** est utilisée, ces propriétés restent
simplement à la banque.

## Cartes

Deux paquets de 16 cartes gèrent notamment :

- gains et paiements ;
- Départ ;
- prison ;
- recul ;
- réparations ;
- paiements entre joueurs ;
- prochaine gare ;
- prochaine compagnie ;
- loyers spéciaux ;
- cartes Sortie de prison conservables.

---

# Audit des règles V13

Une passe de vérification a été faite sur les règles classiques Hasbro pour les points les
plus sensibles :

- faillite envers joueur et banque ;
- transfert de propriétés hypothéquées ;
- 10 % d'intérêts à la réception ;
- déshypothèque immédiate ou différée ;
- double loyer de groupe complet malgré une autre propriété hypothéquée ;
- vente uniforme des bâtiments ;
- pénurie de maisons/hôtels ;
- enchères des propriétés refusées ;
- Départ, prison et doubles.

### Simplifications / variantes assumées

Le projet n'essaie pas d'imiter chaque détail social d'une partie physique :

- le loyer est prélevé automatiquement au lieu d'exiger que le propriétaire le réclame ;
- les actions patrimoniales sont organisées autour du joueur dont c'est le tour ;
- les variantes de Parc Gratuit et de limite de tours sont optionnelles et désactivées par
  défaut ;
- les noms de cases sont génériques afin de garder le projet indépendant des éditions
  commerciales spécifiques.

---

# Architecture

```text
monopoly_poo_gui_v16_3/
├── main.py
├── console.py
├── README.md
│
├── monopoly/
│   ├── __init__.py
│   ├── game.py
│   ├── options.py
│   ├── board.py
│   ├── bank.py
│   ├── player.py
│   ├── properties.py
│   ├── spaces.py
│   ├── rules.py
│   ├── rules_audit.py
│   ├── rule_presets.py
│   ├── cards.py
│   ├── debt.py
│   ├── auction.py
│   ├── building_auction.py
│   ├── trade.py
│   ├── history.py
│   ├── persistence.py
│   ├── statistics.py
│   ├── simulation.py
│   └── strategies.py
│
├── ui/
│   ├── app.py
│   ├── home.py
│   ├── rule_customization.py
│   ├── rules_panel.py
│   ├── game_window.py
│   ├── board_view.py
│   ├── property_card.py
│   ├── property_manager.py
│   ├── auction_panel.py
│   ├── building_auction_panel.py
│   ├── trade_panel.py
│   ├── debt_dialog.py
│   ├── mortgage_transfer_dialog.py
│   ├── history_panel.py
│   ├── landing_build_panel.py
│   ├── end_game_panel.py
│   └── widgets.py
│
└── tests/
```

## Séparation moteur / interface

`monopoly/` ne dépend pas de Tkinter. Les choix humains sont injectés dans le moteur par
des callbacks configurables :

- gestion de dette ;
- choix des hypothèques à lever après transfert.

Sans ces callbacks, le moteur conserve des comportements utilisables sans GUI.

---

# Documentation du code

Chaque classe, fonction et méthode doit posséder une docstring en français avec son rôle,
ses entrées et sa sortie. `tests/test_documentation.py` contrôle automatiquement cette
contrainte.

---

# Prochaines pistes — toujours côté jeu

Avant toute stratégie ou IA, les améliorations possibles sont maintenant surtout du polish :

- vraie relecture visuelle du plateau tour par tour à partir de snapshots ;
- renommage/suppression de sauvegardes directement dans le navigateur ;
- écran de paramètres plus riche pour les variantes maison ;
- animations discrètes des déplacements et constructions ;
- sons optionnels ;
- meilleure adaptation aux petits écrans ;
- export d'un résumé de partie en JSON/CSV ;
- poursuite de l'audit des cartes et des variantes selon l'édition choisie.
