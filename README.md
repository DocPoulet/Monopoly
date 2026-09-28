# Monopoly POO — V22.2.6

Projet Python de Monopoly orienté objet avec interface Tkinter. La V22 est une **refonte graphique et ergonomique complète** construite au-dessus du même moteur POO : aucune règle de jeu n'est déplacée dans l'interface. Cette nouvelle base visuelle prépare les futurs modes alternatifs (Empire, Business Tour, Builder, Gamer, Deal…) sans introduire encore de stratégie ni d'IA.





### Ajustement fin des rotations — V22.2.4

- les noms des terrains sont désormais alignés exactement sur l'axe de leur bande de couleur, soit environ 37° de correction supplémentaire par rapport à V22.2.3 ;
- les coins 0, 10, 20 et 30 restent horizontaux ;
- les prix utilisent le sens de rotation du côté précédent du plateau : `1–9 ← 31–39`, `11–19 ← 1–9`, `21–29 ← 11–19`, `31–39 ← 21–29`.

## Uniformisation des cases, options globales et retour au menu — V22.2.4

La V22.2.4 corrige la lecture des tuiles isométriques et déplace les préférences visuelles hors de
la création de partie. Les numéros `0–39` deviennent un **overlay de debug** placé tout autour du
plateau, au-delà du bord extérieur réel de chaque tuile. Ils sont **masqués par défaut** et peuvent
être activés depuis **Accueil → Options → Afficher les numéros 0–39 autour du plateau**.

Les côtés du plateau suivent maintenant une convention uniforme :

- **cases 1–9 et 31–39** : bande de groupe + nom vers l'intérieur, prix vers l'extérieur ;
- **cases 11–19 et 21–29** : disposition retournée, bande de groupe + nom vers l'extérieur, prix
  vers l'intérieur ;
- les maisons/hôtels suivent la bande de groupe sur les côtés retournés ;
- le nom de la case reste toujours imprimé et parallèle au bord correspondant, sans troncature
  arbitraire ;
- une propriété possédée n'affiche plus le nom de son propriétaire sur la tuile : le **fond entier**
  prend la couleur du joueur ; une hypothèque utilise une variante plus sombre de la même couleur.

Le menu principal possède désormais une entrée **Options**. Elle regroupe le style du plateau, le
thème clair/sombre des menus et arrière-plans, la vitesse des animations, l'affichage du patrimoine,
les sons et les numéros de debug. La création de partie ne demande plus le style ni le thème : elle
ne conserve que le choix des **pions**, qui dépend réellement des joueurs présents. Les options
choisies sont réutilisées par les nouvelles parties de la session.

Enfin, confirmer **Retour au menu** pendant une partie n'abandonne plus brutalement l'écran de jeu.
Un **bilan de fin de partie interrompue** s'affiche d'abord avec les statistiques courantes ; le
bouton de fermeture/retour de ce bilan déclenche ensuite la navigation vers l'accueil.

---

## Coins du plateau — V22.2.6

Les quatre cases de coin ont maintenant une orientation volontairement distincte du reste du
plateau : **Prison (10)**, **Parc Gratuit (20)** et **Allez en prison (30)** affichent leur contenu
strictement à **0° écran**, sans suivre la diagonale isométrique. Sur la case **Départ (0)**, le texte
« Départ » n'est plus dessiné : seul le pictogramme **GO** reste visible et il est désormais
à **0° écran**, dans le bon sens de lecture. Les orientations des noms de propriétés et des prix introduites en V22.2.4 restent
inchangées.

---


## Finition du plateau et limite joueurs — V22.2.1

Cette révision nettoie la typographie du diorama isométrique : les noms des cases sont maintenant
équilibrés sur une ou deux lignes, les icônes restent du côté intérieur et les informations
financières gardent leur zone dédiée. Les **numéros 0 à 39 sont déplacés à l’extérieur du plateau**,
dans le prolongement radial de chaque tuile, afin de ne plus concurrencer le contenu imprimé.

Les nouvelles parties et les campagnes du laboratoire sont désormais limitées à **2 à 4 joueurs**.
Cette limite correspond au nouveau HUD V22.2, conçu autour des quatre coins de la scène. Les anciennes
sauvegardes comportant davantage de joueurs restent chargeables pour ne pas casser la compatibilité.

---

## Diorama isométrique — V22.2

La V22.2 remplace la perspective trapézoïdale de V22/V22.1 par une **vraie composition
isométrique en losange**, inspirée de la lecture visuelle des jeux de plateau numériques type
Business Tour sans reprendre leurs assets. Le plateau est maintenant présenté comme un objet posé
dans la scène : une face supérieure, deux chants visibles, une ombre portée et un centre beaucoup
plus dégagé.

La géométrie logique 11 × 11 reste inchangée. Chaque point est projeté sur deux axes diagonaux,
ce qui signifie que les clics, les animations de pions, les bandes de couleur et les constructions
continuent d'utiliser les vraies cases du moteur. Le plateau est volontairement aplati verticalement
pour conserver une bonne lisibilité sur écran tout en donnant une impression de profondeur.

### Composition proche d'un vrai jeu numérique

Le rail vertical des joueurs a disparu. Les cartes joueur flottent désormais autour de la scène :
les quatre joueurs maximum occupent les quatre coins de la scène. Le plateau récupère ainsi la majorité de la largeur de la fenêtre. Le dock de droite
est plus étroit et ses commandes ont été compactées pour garder les dés, les actions et le journal
sans écraser la scène.

Le joueur actif reste davantage mis en avant. Le bouton **Patrimoine : ON/OFF** flotte au-dessus de
la scène et les cartes joueur utilisent une barre de couleur plus franche ainsi que des libellés plus
courts, afin de réduire l'effet « panneau générique » de la première V22.

### Cases, constructions et centre

Les textes des cases suivent l'angle de leur côté du plateau. Depuis V22.2.3, les côtés 11–29 sont
retournés : leur bande de groupe est extérieure, tandis que les côtés 31–09 conservent leur bande
vers l'intérieur. Lorsqu'un terrain est construit, maisons et hôtel sont dessinés sous forme de **petits volumes
pseudo-3D** posés sur la case, ce qui prépare visuellement les futurs modes Builder et Empire.

Le centre est volontairement plus vide : nom du plateau, tour courant, cagnotte éventuelle et deux
petits paquets projetés. Les grandes cartes Chance/Communauté continuent d'apparaître en overlay
animé ; les petits paquets centraux servent seulement de repère et signalent lorsqu'un tirage récent
existe.

### Thèmes et séquencement conservés

Le thème **Clair/Sombre** contrôle maintenant réellement le fond de la scène et les menus, tandis que
le plateau conserve les couleurs du style choisi. Les cinq styles et les vingt pions de V22 restent
disponibles, avec des previews elles aussi passées au rendu isométrique.

Le pipeline corrigé en V22.1 est conservé strictement :

1. animation complète des dés ;
2. résultat final ;
3. déplacement case par case ;
4. arrivée du pion ;
5. résolution visuelle de la case et affichage des actions.

V22.2 reste une projection 2D calculée dans Tkinter, pas un moteur 3D. Cette base est volontaire :
elle donne déjà le rendu diorama recherché tout en restant simple à tester, portable et compatible
avec tout le moteur de simulation actuel.

## Ajustements visuels et séquencement — V22.1

La V22.1 affine la refonte graphique sans toucher au moteur de règles. Le plateau conserve la projection
2.5D mais reçoit désormais une **légère rotation d’environ 3,5°**, inspirée d’une vue de jeu de plateau
numérique à la Business Tour. La rotation reste volontairement modérée afin de préserver la lisibilité
des cases et du texte sur les petits écrans. Les mini-previews de l’accueil et du sélecteur de style ont
été inclinées dans le même esprit.

Les propriétés latérales des séries **11–19** et **31–39** avaient la bonne couleur mais la bande était
interpolée dans le mauvais sens : elle recouvrait une grande partie de la case au lieu de rester sur le
bord intérieur. Les deux côtés utilisent maintenant une bande étroite cohérente avec les côtés haut et
bas.

Le déroulement visuel d’un lancer est maintenant strictement séquencé :

1. les deux dés tournent et les contrôles sont verrouillés ;
2. les dés s’arrêtent sur le résultat moteur ;
3. le pion se déplace case par case ;
4. seulement après l’arrivée, le journal, les variations de cash, les cartes et les panneaux d’achat /
   construction / loyer deviennent visibles.

Le pion reste visuellement figé sur sa case de départ pendant l’animation des dés, même si le moteur a
déjà calculé le résultat en mémoire. Cela évite tout spoiler visuel du résultat. Le titre central a aussi
été simplifié : la mention technique « V22 • style • plateau 2.5D » a disparu au profit du nom réel du
plateau, afin de donner un rendu moins démonstratif et plus proche d’un jeu fini.

## Refonte graphique — V22

### Cinq styles avec preview

Le menu **Options** propose cinq identités visuelles avec une miniature du plateau avant validation :

- **Classique modernisé** : crème, vert et codes proches d'un plateau physique ;
- **Premium** : bois sombre, doré et ambiance plus élégante ;
- **Arcade / jeu vidéo** : contrastes francs et accents électriques ;
- **Familial / cartoon** : couleurs douces et rendu plus ludique ;
- **Hybride** : plateau traditionnel avec interface numérique moderne.

Le style ne modifie jamais les règles. Le choix **Clair / Sombre** ne change que les menus, panneaux et arrière-plans ; les couleurs fonctionnelles du plateau restent reconnaissables.

### Plateau 2.5D en perspective

V22 avait introduit une première projection trapézoïdale 2.5D. **V22.2 la remplace par le diorama
isométrique décrit plus haut**, plus proche de la direction visuelle retenue pour les futurs modes.

Les clics ne reposent plus sur une grille rectangulaire approximative : chaque case mémorise son quadrilatère projeté et le hit-test souris utilise ce polygone réel.

Les cases disposent aussi de pictogrammes dédiés pour mieux identifier gares, compagnies, Chance, Communauté, prison, taxes, Parc Gratuit, Départ et Aller en prison.

### Vingt pions dessinés

V22 fournit **20 pions vectoriels** sans asset externe : Voiture, Bateau, Chapeau, Chat, Chien, Fusée, Avion, Train, Canard, Couronne, Dé, Robot, Dragon, Étoile, Diamant, Guitare, Tasse, Clé, Lune et Fantôme.

Chaque joueur choisit son pion avant la partie avec une preview. Deux joueurs actifs ne peuvent pas sélectionner le même pion. Le pion reprend la couleur du joueur, ce qui conserve une lecture claire même avec plusieurs formes.

### Animations

Les animations disposent de trois vitesses :

- `normal` ;
- `fast` ;
- `off`.

Les dés affichent plusieurs faces avant de s'arrêter sur le résultat réel du moteur. Les pions se déplacent **case par case avec interpolation fluide** pour les déplacements de type lancer de dés et le recul de trois cases. Les téléportations longues restent volontairement directes afin de ne pas ralentir la partie.

Ces animations sont purement visuelles et utilisent leur propre hasard pour les faces intermédiaires des dés : elles ne consomment jamais le générateur aléatoire du moteur et ne changent donc pas la reproductibilité des parties.

### Cartes joueur autour du plateau

Depuis V22.2, les cartes ne sont plus enfermées dans un rail gauche : elles flottent **dans les coins
et sur les bords de la scène isométrique**, tandis que le dock d'actions reste compact à droite.
Le joueur actif est visuellement développé tandis que les autres restent compacts. Les cartes
affichent cash, case, nombre de biens, cartes conservées, prison/faillite et patrimoine estimé.

Un bouton **Patrimoine : ON/OFF** permet de masquer cette valeur sans changer la partie.

### Chance et Communauté en grande carte

Après un tirage, une grande carte intégrée apparaît au centre du plateau avec une animation courte. Le joueur valide **Continuer** avant de reprendre les décisions du tour. Les tirages en cascade sont montrés dans leur ordre réel.

La dernière carte reste ensuite visible sur le paquet central, comme auparavant.

### Panneaux intégrés

Achat de propriété, enchères, construction après atterrissage, gestion des propriétés, échanges, replay/statistiques, règles et écran de fin restent des **overlays intégrés au plateau**. V22 harmonise leur environnement avec le nouveau plateau et les nouveaux thèmes au lieu de multiplier les fenêtres secondaires.

Les dialogues spécialisés de dette et de traitement d'hypothèques restent modaux pour l'instant car le moteur attend un résultat synchrone ; ils seront candidats à une conversion en panneaux asynchrones lors de l'architecture multi-modes.

### Nouvel écran d'accueil

L'accueil est entièrement réorganisé avec :

- un grand aperçu de plateau en perspective ;
- **Nouvelle partie** ;
- **Charger une partie** ;
- **Laboratoire** ;
- **Quitter** ;
- un rappel du futur chantier multi-modes.

La fenêtre tente de démarrer **maximisée mais fenêtrée**. Elle reste redimensionnable et le layout a été compacté pour rester utilisable autour de `1366×768`, tout en profitant davantage d'un écran `1920×1080`.

### Audio drag & drop

Aucun fichier sonore n'est livré. La couche `AudioManager` ignore silencieusement tout fichier absent. Il suffit plus tard de déposer des fichiers WAV dans `assets/sounds/` avec les noms suivants :

```text
assets/sounds/
├── dice_roll.wav
├── pawn_move.wav
├── cash_gain.wav
├── cash_loss.wav
├── property_buy.wav
├── house_build.wav
├── hotel_build.wav
├── jail.wav
├── card_draw.wav
├── auction.wav
└── victory.wav
```

Le sous-dossier contient son propre README. Sous Windows, la lecture utilise `winsound`. Sur les autres systèmes, V22 essaie `paplay`, `aplay` ou `ffplay` lorsqu'un de ces lecteurs est disponible.

### Apparence conservée dans les sauvegardes

La séparation moteur/UI reste intacte : `monopoly.persistence` n'a aucune dépendance graphique. Après l'écriture normale de la sauvegarde moteur, l'application ajoute simplement une clé top-level optionnelle `ui_v22` contenant style, thème, animations, affichage du patrimoine, pions, audio et visibilité des numéros de debug.

Une ancienne sauvegarde sans cette clé reste totalement valide et utilise le profil visuel V22 par défaut.

### Roadmap décalée

Le plan convenu devient :

```text
V22  — refonte graphique complète
V23  — architecture moteur multi-modes
V24  — Monopoly Empire
V25  — Business Tour / mode tour économique
V26  — Monopoly Builder
V27  — Monopoly Gamer
V28  — Monopoly Deal
V29+ — autres variantes et modes originaux
```

Les stratégies codées restent reportées : la priorité est maintenant de transformer proprement le projet en moteur multi-modes après cette base graphique.

---

## Analyse croisée et rapports — V21.8.1

Un nouvel onglet **Analyse croisée** permet d'étudier plusieurs scénarios sur les mêmes seeds sans
devoir ouvrir chaque scénario séparément.

### Comparaison des 40 cases

Le sélecteur de métrique propose :

- **Arrêts / partie** ;
- **ROI brut (%)** ;
- **$/arrêt**.

Le graphique principal trace une courbe par scénario sur les indexes `0` à `39`. Il devient donc
possible de voir immédiatement si un preset modifie la fréquentation ou la rentabilité de certaines
zones du plateau. Les valeurs restent alignées par index, même si les noms ou types de cases ont été
personnalisés.

Une **heatmap scénario × 40 cases** complète cette vue. Chaque ligne correspond à un scénario et
chaque colonne à une case. La palette suit désormais une logique de **capteur de température**,
du **bleu foncé** pour les valeurs faibles au **rouge foncé** pour les valeurs fortes, avec une
transition froide → chaude plus lisible. Le survol d'une cellule affiche le scénario, l'index et
la valeur exacte.

### Chance et Communauté entre presets

L'onglet croisé compare aussi les deux paquets pour chaque scénario :

- tirages Chance moyens par partie ;
- impact cash moyen d'une Chance ;
- tirages Communauté moyens par partie ;
- impact cash moyen d'une Communauté ;
- contribution cumulée des cartes à la cagnotte ;
- nombre total moyen de cartes par partie.

Deux graphiques affichent les **tirages par partie** et l'**impact cash moyen par tirage**. Le tableau
associé bénéficie du même tri multi-colonnes `↑ / ↓ / aucun` que les autres statistiques du labo.

### Rapports JSON rechargeables

Le bouton **Charger rapport JSON** permet de rouvrir un rapport exporté sans relancer la moindre
partie. Le rapport V21.8 passe au **format version 4** et embarque désormais :

- la configuration de campagne ;
- les résultats détaillés et agrégés ;
- les règles complètes de chaque scénario ;
- le plateau et les cartes de chaque scénario.

Cela permet de restaurer les couleurs, fiches de cases, cartes personnalisées et analyses croisées
exactement comme au moment de la simulation. Les rapports V1 à V3 restent lisibles ; lorsqu'ils ne
contiennent pas le plateau d'origine, l'application utilise un plateau classique de secours pour les
éléments visuels tout en conservant les statistiques enregistrées.

### Rapport HTML autonome

Le bouton **Rapport HTML** génère un fichier unique consultable dans un navigateur, sans Python et
sans dépendance internet. Il contient :

- tableau comparatif des scénarios ;
- durée moyenne, taux de fin, ROI global et loyers moyens ;
- heatmap des 40 cases ;
- comparaison Chance / Communauté ;
- rappel méthodologique du protocole neutre.

Les graphiques sont intégrés directement en **SVG** dans le fichier HTML : aucun CDN, JavaScript ou
service externe n'est requis.

---

## Performance du laboratoire — V21.7

La V21.7 conserve exactement le même protocole neutre et les mêmes seeds : les optimisations ne
modifient pas les décisions simulées. Une campagne séquentielle et une campagne parallèle produisent
les mêmes résultats partie par partie à seed identique.

Les principales optimisations sont :

- **cache des groupes de couleur dans `Board`** : les règles de construction ne rescannent plus les
  40 cases du plateau à chaque vérification ;
- la politique neutre cherche désormais les constructions uniquement parmi les **biens réellement
  possédés** par le joueur actif ;
- `GameStatistics` peut ignorer la série temporelle de replay pendant les simulations, puisqu'elle
  n'est pas utilisée dans les rapports du laboratoire ;
- les grandes campagnes peuvent être réparties sur plusieurs **processus Python indépendants** ;
- les tâches parallèles sont envoyées par petits lots pour limiter le coût de sérialisation tout en
  gardant une progression suffisamment régulière ;
- la barre de progression est rafraîchie avec un throttle temporel, ce qui évite de redessiner
  Tkinter après chaque partie tout en gardant la fenêtre réactive.

Le nouveau champ **Processus** accepte `Auto`, `1`, `2`, `4` ou `8` :

- `Auto` reste séquentiel pour les campagnes finies relativement petites, où démarrer plusieurs
  processus coûterait plus cher que le calcul lui-même ;
- `Auto` active plus tôt le multi-processus en mode **Tours max = 0/vide**, car une partie illimitée
  peut être beaucoup plus lourde ;
- les campagnes finies d'au moins environ **250 parties par scénario** sont candidates au calcul
  parallèle automatique ;
- une valeur explicite `2`, `4` ou `8` force le nombre demandé, dans la limite du nombre de parties ;
- `1` permet de forcer le mode strictement séquentiel pour benchmark ou diagnostic.

L'interface affiche à la fin le **temps écoulé**, le nombre de processus réellement utilisés et la
seed. Sur le benchmark de validation de cette version, 100 parties classiques avec la même série de
seeds sont passées d'environ **7,2 s en V21.6.2 à 3,1 s en V21.7** en mode séquentiel, avec des
résultats de partie identiques. Sur un lot de 500 parties limitées à 120 tours, le mode Auto à
4 processus est passé d'environ **9,7 s en séquentiel à 5,3 s en parallèle**. Ces chiffres sont
indicatifs : les performances exactes dépendent du CPU, du preset et de la durée des parties.

---

## Mode sans limite de tours — V21.6.2

Le champ **Tours max** accepte deux formes équivalentes pour activer le mode illimité :

- champ vide ;
- valeur `0`.

Dans ces deux cas, le laboratoire ne fixe **aucune limite en nombre de tours** et ne coupe plus
une partie en fonction du cash d'un joueur. La partie continue jusqu'à une fin naturelle du moteur.

Il reste un seul garde-fou technique : **20 000 actions exécutées dans une même partie**. Si ce
watchdog est atteint, la simulation est interrompue et le leader patrimoine/cash est enregistré au
cutoff. Cette borne protège la machine contre un preset pathologique sans réintroduire une limite en
nombre de tours. Elle est fixe et déterministe, donc une seed explicite reste reproductible.

Les causes d'arrêt pertinentes sont désormais :

- `natural` : fin normale du moteur ;
- `round_limit` : limite de tours explicite supérieure à zéro ;
- `action_watchdog` : plafond technique de 20 000 actions en mode illimité.

La valeur par défaut de l'interface reste `250` tours : le mode illimité est donc volontaire, en
vidant le champ ou en saisissant `0`. La seed reste vide par défaut et est générée aléatoirement
comme depuis V21.1.

---


### Ajustement de performance — V21.6.2

Le watchdog du mode illimité passe de **100 000 à 20 000 actions par partie**. Cette borne réduit
fortement le temps nécessaire aux campagnes de 100 parties ou plus tout en restant largement
supérieure à la durée d'une partie ordinaire. Elle ne s'applique que lorsque **Tours max** est vide
ou égal à `0` ; une limite de tours explicite continue d'utiliser uniquement `round_limit`.

## Interactions statistiques — V21.5

La page **Cases & rendement** devient interactive. Le survol d'une barre des graphiques
**arrêts moyens**, **ROI**, **loyer par arrêt** ou **ROI par niveau de construction** affiche une
fiche flottante correspondant à la case concernée.

Pour une case ordinaire, la fiche indique son index, son type et son nom. Pour un bien achetable,
elle reprend autant que possible une **carte de propriété** : prix effectif avec les règles du
scénario, valeur hypothécaire, loyers, loyers avec maisons/hôtel, coût de construction, loyers de
gare ou multiplicateurs de compagnie. La valeur statistique exacte de la barre survolée reste
affichée en tête de fiche. Les cartes personnalisées utilisent naturellement les données du plateau
chargé dans le scénario.

Tous les principaux **tableaux statistiques** sont maintenant triables en cliquant sur leurs titres :

1. premier clic : tri **croissant** ;
2. deuxième clic : tri **décroissant** ;
3. troisième clic : suppression de ce critère.

Le tri est **multi-colonnes** et respecte l'ordre des clics. Par exemple, un utilisateur peut obtenir
`Loyers ①↓`, puis `Investi ②↑`, puis `$/arrêt ③↑`. Le premier critère reste prioritaire, le second
sert à départager les égalités, puis le troisième. Lorsqu'un critère est retiré, les priorités restantes
sont automatiquement renumérotées. Sans aucun critère actif, le tableau revient à son ordre naturel.

Cette interaction est disponible dans les tableaux **Comparaison**, **Rentabilité des propriétés**,
**Profil par siège**, **Cases & rendement**, **Cartes**, **Analyse croisée** et **Parties**. Les valeurs formatées en dollars
ou pourcentages sont triées numériquement et non comme du texte.

---

## Statistiques Chance et Communauté — V21.4

Le laboratoire possède maintenant un onglet **Cartes** entièrement dédié aux paquets
**Chance** et **Caisse de communauté**, toujours sans stratégie ni IA.

Chaque tirage mesure l'effet **réel après résolution complète** de la carte. Cela signifie
qu'une carte de déplacement qui provoque ensuite un loyer, une taxe, un passage par Départ
ou une autre dépense est mesurée avec son impact final, pas seulement avec le texte imprimé.

Pour chaque carte, le laboratoire calcule :

- nombre total de tirages ;
- tirages moyens par partie ;
- part de la carte parmi les tirages de son propre paquet ;
- nombre de parties où la carte est apparue ;
- impact cash cumulé et moyen sur le joueur qui pioche ;
- variation cumulée du cash des autres joueurs ;
- variation totale de cash de l'ensemble des joueurs ;
- contribution nette à la cagnotte Parc Gratuit ;
- fréquence de déplacement ;
- fréquence d'envoi en prison ;
- fréquence d'obtention d'une carte Sortie de prison ;
- plus grand gain et plus grande perte observés sur un tirage.

L'onglet propose un filtre **Tous / Chance / Communauté** et quatre graphiques :

1. **Fréquence de tirage par carte** ;
2. **Impact cash moyen sur le joueur** avec valeurs positives et négatives ;
3. **Contribution cumulée à la cagnotte** ;
4. **Effets observés** : déplacement, prison et sortie de prison.

Les barres Chance utilisent la couleur orangée du plateau et les cartes Communauté la
couleur bleue correspondante.

Un nouvel export **Exporter cartes CSV** ajoute une ligne par carte et scénario avec toutes
ces métriques. Le JSON complet contient également une section `cards` dans chaque campagne.

---

## Couleurs des cases dans les graphiques — V21.3

Les graphiques de l'onglet **Cases & rendement** reprennent maintenant directement la
couleur de chaque case afin de rendre les 40 positions beaucoup plus faciles à reconnaître.

Pour les terrains, les barres utilisent la couleur de leur groupe : marron, bleu clair, rose,
orange, rouge, jaune, vert ou bleu foncé. Les autres types utilisent une couleur dédiée
cohérente avec le plateau : gare grise, compagnie bleu clair, Chance orangée, Communauté
bleue, taxe rouge pâle, Parc Gratuit jaune, etc.

Cette coloration s'applique à :

- la **fréquentation moyenne par case** ;
- le **ROI par bien** ;
- le **loyer généré par arrêt** ;
- le **ROI par niveau de construction**.

Pour le dernier graphique, tous les niveaux `0 / 1 / 2 / 3 / 4 maisons / hôtel` reprennent
la couleur du terrain sélectionné.

---

## Analyse des cases, ROI et première place — V21.2

La V21.2 corrige d'abord la lecture des résultats lorsqu'une partie est interrompue par le
**garde-fou du laboratoire**. Une partie réellement terminée conserve son vainqueur normal.
Une partie tronquée reçoit désormais un **leader au cutoff**, déterminé de façon stable par :

1. patrimoine final ;
2. cash final en cas d'égalité ;
3. ordre de siège comme dernier départage déterministe.

La colonne par joueur devient donc **1re place %**. Sur une campagne complète, les pourcentages
de première place totalisent toujours **100 %**, même si de nombreuses parties sont tronquées.
Le laboratoire conserve séparément le **taux de parties finies** et le **taux de victoire parmi
les parties réellement finies**, afin de ne jamais confondre un leader au cutoff avec une victoire
naturelle.

### Que signifie P90 ?

`P90` est le **90e percentile** de la durée. Par exemple, `P90 = 74 tours` signifie que
**90 % des parties ont duré 74 tours ou moins**, tandis que les 10 % les plus longues ont dépassé
74 tours. La médiane `P50` décrit le centre de la distribution ; P90 est surtout utile pour repérer
les longues traînes et les variantes qui produisent parfois des parties exceptionnellement longues.

### Nouvel onglet « Cases & rendement »

Le laboratoire enregistre désormais chaque résolution de case, y compris les déplacements
supplémentaires provoqués par les cartes. L'onglet **Cases & rendement** ajoute quatre graphiques :

1. **Arrêts moyens par case et par partie** sur les 40 positions du plateau ;
2. **Rendement brut par bien** : `loyers cumulés / investissement cumulé × 100` ;
3. **Loyer généré par arrêt** sur chaque bien ;
4. **Rendement par niveau de construction** pour un terrain sélectionné : 0, 1, 2, 3, 4 maisons
   ou hôtel.

Le tableau détaillé affiche aussi, pour chaque case : fréquence moyenne, part des arrêts, argent
investi, loyers produits, ROI brut, solde `loyers - investissement` et loyer moyen par arrêt.

L'**investissement brut** correspond à l'argent réellement engagé dans les achats directs, les
enchères et les constructions. Les reventes et hypothèques ne sont pas soustraites : cette mesure
répond à la question « combien d'argent a été engagé dans cette case par rapport aux loyers qu'elle
a produits ? ».

Pour les terrains, les événements de loyer mémorisent maintenant le niveau de développement au
moment exact du paiement. On peut donc comparer le rendement observé à 0 maison, 1 maison, etc.

### Indicateurs complémentaires

Le laboratoire calcule également :

- case la plus fréquentée ;
- ROI global de tous les biens ;
- bien au meilleur ROI brut ;
- nombre moyen d'arrêts/résolutions par partie ;
- leads au cutoff par siège ;
- victoires naturelles parmi les seules parties finies.

### Exports V21.2

Le JSON complet passe au schéma `monopoly-simulation-report` **version 3**. Deux exports CSV
s'ajoutent aux exports existants :

- **CSV cases / ROI** : une ligne par case et scénario ;
- **CSV constructions** : une ligne par terrain, scénario et niveau de développement.

Les exports existants conservent aussi l'indication `winner_at_cutoff` afin de distinguer les
premières places de sécurité des victoires naturelles.

**Aucune stratégie n'est utilisée dans ces calculs.** `monopoly/strategies.py` reste totalement
indépendant du laboratoire.

---

## Base du laboratoire statistique — V21.1

Le bouton **Laboratoire de simulation** lance toujours des parties automatiques avec une politique
neutre/aléatoire fixe. Cette politique ne cherche jamais à gagner : elle sert uniquement à faire
travailler le moteur, les règles et les plateaux sur de nombreuses répétitions.

Le protocole reste volontairement transparent :

- achat direct tiré au sort à 50 % lorsqu'il est payable ;
- enchères résolues par budgets privés aléatoires reproductibles ;
- loyers manuels réclamés ou abandonnés à probabilité égale ;
- constructions tirées uniquement parmi les constructions légalement possibles ;
- levées d'hypothèque occasionnelles ;
- aucune proposition d'échange spontanée ;
- sortie de prison par les dés, sans préférence économique ;
- aucun import ni appel à `monopoly/strategies.py`.

### Seed vide par défaut

Le champ **Seed** est maintenant **vide par défaut**.

- si une seed entière est saisie, elle est utilisée telle quelle ;
- si le champ reste vide, une seed aléatoire est générée au lancement ;
- la seed réellement utilisée est immédiatement réaffichée dans le champ et dans le statut final ;
- relancer ensuite sans modifier cette valeur reproduit exactement la même campagne ;
- effacer à nouveau le champ demande une nouvelle seed aléatoire.

Lors d'une comparaison, la partie numéro `N` de chaque scénario utilise la même seed. Cela permet
de comparer plus proprement deux variantes sans introduire volontairement une différence de hasard.

### Comparaison enrichie entre scénarios

L'onglet **Comparaison** affiche maintenant pour chaque scénario :

- nombre de parties ;
- taux de parties terminées normalement ;
- tours moyens ;
- médiane ;
- percentile P90 ;
- écart-type de durée ;
- actions moyennes ;
- loyers moyens transférés ;
- plus gros loyer unique observé ;
- faillites moyennes.

Quatre graphiques restent visibles simultanément :

1. **durée moyenne + P90** ;
2. **taux de fin** ;
3. **loyer moyen + plus gros loyer** ;
4. **activité moyenne** : bâtiments, prison, cartes et hypothèques.

Cela permet de voir immédiatement une variante qui augmente seulement la moyenne, mais aussi une
variante produisant une longue traîne de parties extrêmes.

### Distribution des durées

Le laboratoire calcule désormais :

- P10 ;
- P25 ;
- médiane / P50 ;
- P75 ;
- P90 ;
- écart-type ;
- histogramme automatique des durées.

L'onglet **Détail scénario** affiche cet histogramme afin de distinguer une campagne homogène
d'une campagne où quelques parties exceptionnellement longues faussent la moyenne.

### Statistiques par siège

Chaque siège neutre (`Joueur 1`, `Joueur 2`, etc.) dispose maintenant de :

- taux de victoire ;
- taux de faillite ;
- cash final moyen ;
- patrimoine final moyen ;
- nombre moyen de biens finaux ;
- loyers moyens reçus ;
- loyers moyens payés ;
- passages en prison moyens.

Un graphique permet de basculer entre ces mesures. Ces données servent notamment à repérer un
éventuel biais structurel lié à l'ordre des joueurs ; elles ne représentent pas des stratégies.

### Rentabilité des propriétés enrichie

Pour chaque bien ayant généré un loyer, le laboratoire conserve désormais :

- loyer total sur la campagne ;
- loyer moyen par partie ;
- nombre total d'événements de loyer ;
- loyer moyen lorsqu'un paiement a effectivement lieu ;
- nombre de parties où le bien a rapporté ;
- plus gros loyer unique du bien.

### Détail partie par partie

L'onglet **Parties** expose une ligne par seed avec :

- tours et actions ;
- vainqueur et état `finie / tronquée` ;
- loyers totaux et loyer maximal ;
- faillites ;
- bâtiments ;
- prison ;
- cartes piochées ;
- achats directs ;
- enchères gagnées ;
- hypothèques ;
- pic de cagnotte Parc Gratuit ;
- cagnotte effectivement récupérée.

Les parties sont présentées des plus longues aux plus courtes pour retrouver rapidement une seed
intéressante à reproduire ou à examiner.

### Exports V21.1

Trois exports sont disponibles :

- **JSON complet** : schéma `monopoly-simulation-report` version `2`, avec campagnes, distributions,
  profils par siège, propriétés et détail de chaque partie ;
- **CSV parties** : une ligne enrichie par partie simulée ;
- **CSV résumé** : une ligne par scénario avec les principaux indicateurs comparatifs.

### Performance et isolation

Le laboratoire utilise toujours le moteur réel `Game` / `Rules`. Les snapshots de replay restent
désactivés pendant une campagne pour éviter de stocker des milliers d'états inutiles. L'historique
structuré reste actif pour calculer les statistiques.

**La V21.1 n'utilise toujours aucune stratégie.** Le futur travail sur des stratégies explicites
reste un chantier séparé et n'est pas commencé ici.

---

## Éditeur complet, validation et packs — V20

La V20 transforme l'éditeur de plateau en véritable outil de création et de gestion de variantes.
Les presets de règles et de plateau restent séparés, mais un **pack complet** peut maintenant
regrouper les deux dans un seul fichier portable.

### Assistant « nouveau plateau »

Le bouton **Nouveau…** de l'éditeur de plateau ouvre un assistant proposant deux points de départ :

- **Structure Monopoly vierge** : 40 positions compatibles avec le moteur, noms génériques,
  économie simple et une carte neutre dans chaque paquet ;
- **Copie du plateau standard** : toutes les valeurs classiques sont copiées avant édition.

Les quatre positions structurelles restent protégées : Départ, Prison, Parc Gratuit et
Allez en prison. Le reste peut ensuite être édité comme dans la V17.

### Validation visuelle

Un panneau **Validation du plateau** analyse toute la définition sans s'arrêter au premier
problème. Il distingue :

- **Erreur** : incohérence bloquante empêchant l'utilisation du plateau ;
- **Avertissement** : configuration jouable mais potentiellement suspecte.

Exemples d'avertissements : groupe de couleur avec un seul terrain, terrain gratuit,
barème de loyer qui diminue lorsqu'un bâtiment supplémentaire est ajouté ou nom économique
dupliqué. Les erreurs de cartes, de types structurels et les dépendances
« prochaine gare / prochaine compagnie » restent bloquantes.

Un double-clic ou **Aller au problème** ouvre directement la case ou la carte concernée.

### Duplication

L'éditeur possède maintenant :

- **Dupliquer vers…** pour copier une case économique vers une autre position non structurelle ;
- **Dupliquer** dans les onglets Chance et Communauté pour cloner une carte avant modification.

L'index de la case cible est toujours conservé et les quatre positions structurelles ne peuvent
pas être écrasées.

### Bibliothèques de presets

Les éditeurs de règles et de plateau disposent d'un bouton **Bibliothèque…**. La fenêtre de
bibliothèque offre :

- aperçu détaillé avant chargement ;
- chargement ;
- renommage du preset et de son fichier local ;
- suppression définitive après confirmation.

La bibliothèque de plateaux affiche notamment le nombre de cartes, la structure des types de
cases et le résultat de la validation. La bibliothèque de règles rappelle les principaux
paramètres économiques et de construction.

### Pack complet règles + plateau

L'écran de préparation contient maintenant un bloc **Pack complet** avec :

- **Importer règles + plateau** ;
- **Exporter règles + plateau**.

Le fichier JSON versionné contient l'intégralité de `GameOptions` et de `BoardConfig`, donc les
40 cases et les deux paquets de cartes. Un pack importé remplace simultanément les règles et le
plateau du brouillon courant sans toucher aux noms de joueurs déjà saisis.

Les formats restent volontairement distincts :

```text
Preset règles     -> uniquement GameOptions
Preset plateau    -> uniquement BoardConfig + cartes
Pack complet      -> GameOptions + BoardConfig + cartes
Sauvegarde partie -> état vivant de la partie + configuration embarquée
```

---

## Confort de jeu local et polish — V19

La V19 améliore l'utilisation en partie locale sans modifier les règles métier ni les
simulations. Les nouveautés restent donc dans la couche Tkinter.

### Écran privé entre joueurs

Le bouton **Écran privé : ON/OFF** active un rideau de confidentialité entre deux joueurs.
Lorsqu'une décision du joueur précédent est terminée et que la main change réellement,
l'interface masque tout le plateau, les soldes et les propriétés puis affiche uniquement :

- le nom du prochain joueur ;
- le numéro du tour de table ;
- un bouton **Je suis … — continuer**.

`Entrée` ou `Espace` permettent également de révéler la partie. Le rideau attend la fin
des achats, constructions, enchères et autres décisions du joueur sortant avant de changer
de main. En mode loyer manuel, il sait aussi passer l'écran au propriétaire qui doit
**Réclamer** ou **Renoncer** au loyer avant de poursuivre vers le joueur suivant.

Le mode privé est un confort d'interface et non une règle Monopoly : il peut être désactivé
à tout moment sans modifier la partie ou la sauvegarde.

### Indication de l'action attendue

Sous les dés, un bandeau vert indique l'action principale du moment, par exemple :

```text
ACTION : lancer les dés • Espace
ACTION : acheter la propriété ou passer / enchérir
ACTION : réclamer le loyer ou y renoncer
ACTION : choisir les bâtiments ou passer
ACTION : terminer l'enchère
```

Cela complète les messages de statut existants et rend les états bloquants plus faciles à
identifier pendant une partie avec beaucoup de variantes.

### Raccourcis clavier

Les raccourcis disponibles sont rappelés dans le panneau **Gestion** :

```text
Espace    lancer les dés / continuer l'écran privé
G         gérer les propriétés
E         ouvrir un échange
H         Replay / Stats
R         règles de la partie
Ctrl+S    sauvegarder
```

Les raccourcis globaux sont ignorés lorsqu'un champ de texte ou une combobox possède le
focus afin de ne pas perturber les formulaires et éditeurs.

### Lisibilité du plateau et micro-animations

Les maisons sont maintenant dessinées comme de petits bâtiments verts distincts et l'hôtel
comme un bâtiment rouge plus large. Le niveau de développement est donc plus lisible sans
ouvrir la fiche de propriété.

Deux animations légères, purement graphiques, ont été ajoutées :

- le pion qui vient de changer de case effectue une courte pulsation à l'arrivée ;
- les variations de liquidités apparaissent brièvement au-dessus du plateau, par exemple
  `Alice -50 $ • Bob +50 $`.

Ces effets n'altèrent jamais le moteur, le RNG, les snapshots de replay ni les sauvegardes.

---

## Replay de partie et statistiques avancées — V18

La V18 transforme l'ancien panneau **Historique / Stats** en **Replay / Stats** avec trois
onglets complémentaires :

- **Replay** : snapshots historiques du plateau et journal du tour sélectionné ;
- **Statistiques avancées** : évolution financière, rentabilité et indicateurs détaillés ;
- **Journal** : historique structuré filtrable conservé des versions précédentes.

### Replay en lecture seule

Le moteur capture un snapshot initial puis un snapshot de **fin de tour de table** avant le
début du tour suivant. L'état courant est également proposé comme aperçu vivant.

Un snapshot conserve notamment :

- cash et patrimoine estimé de chaque joueur ;
- position, faillite et prison ;
- nombre de biens possédés ;
- propriétaire de chaque bien ;
- hypothèques ;
- maisons et hôtels ;
- cagnotte Parc Gratuit ;
- stock bancaire de bâtiments ;
- numéro du dernier événement inclus.

Le replay dessine un mini-plateau indépendant avec les pions et propriétaires historiques.
Les boutons **Tour précédent / Tour suivant** permettent de naviguer dans la timeline. Pour
le tour sélectionné, son journal est affiché dans l'ordre et peut être parcouru
**événement par événement**.

Le snapshot reste volontairement immuable : consulter le tour 4 pendant le tour 15 ne
modifie jamais la partie réelle et ne relance aucune logique du moteur.

Les snapshots sont inclus dans les sauvegardes JSON. Une ancienne sauvegarde sans replay
reste chargeable ; elle démarre simplement sa timeline à partir de l'état restauré.

### Statistiques avancées

L'onglet statistique ajoute :

- cash actuel et patrimoine actuel par joueur ;
- biens possédés ;
- loyers payés et reçus ;
- nombre de passages en prison ;
- nombre d'échanges ;
- plus gros loyer de la partie et propriété concernée ;
- propriété ayant généré le plus de loyers cumulés ;
- pic de cagnotte Parc Gratuit ;
- plus gros montant cash impliqué dans un échange ;
- tableau de rentabilité des propriétés avec total encaissé, nombre de loyers et record.

Un graphique intégré permet de changer de métrique entre :

```text
Cash
Patrimoine
Biens
Cagnotte
```

Les points du graphique proviennent des snapshots de replay, ce qui permet d'étudier
l'évolution de la partie tour après tour sans recalculer rétrospectivement un état fictif.

### Événements supplémentaires

L'entrée en prison est maintenant journalisée explicitement avec le type `jail_enter`, ce
qui permet de compter précisément les passages en prison dans les statistiques.

---

## Éditeur de plateau et presets — V17

La préparation d'une nouvelle partie possède maintenant deux personnalisations indépendantes :

- **Personnaliser les règles** pour les variantes globales ;
- **Personnaliser le plateau** pour le contenu des cases et des paquets de cartes.

Les deux profils peuvent être combinés librement. Par exemple, un plateau avec des loyers et
cartes entièrement modifiés peut être joué avec les règles classiques ou avec n'importe quel
preset de règles.

### Édition des 40 cases

L'onglet **40 cases** permet de modifier chaque position du plateau.

Pour les cases ordinaires, le type peut être changé entre :

- terrain ;
- gare ;
- compagnie ;
- taxe ;
- Chance ;
- Caisse de communauté.

Les quatre positions structurelles restent volontairement fixes afin de préserver les
invariants du moteur :

```text
0  = Départ
10 = Prison / Simple visite
20 = Parc Gratuit
30 = Allez en prison
```

Toutes les cases peuvent être renommées. Selon leur type, l'éditeur expose également :

- prix d'achat ;
- groupe de couleur ;
- loyer sans bâtiment ;
- loyers avec 1, 2, 3 et 4 maisons ;
- loyer avec hôtel ;
- coût d'une maison / d'un hôtel ;
- quatre niveaux de loyers pour les gares ;
- multiplicateurs de dés des compagnies ;
- montant des taxes.

Les pourcentages globaux définis dans les règles continuent ensuite à s'appliquer **par-dessus**
ces valeurs de base. Un terrain réglé à `200 $` dans le plateau avec une règle
`Prix des propriétés = 150 %` coûte donc `300 $` pendant la partie.

### Éditeur Chance et Communauté

Les deux autres onglets permettent de modifier les paquets **Chance** et
**Caisse de communauté** carte par carte. Une carte peut changer de type et de paramètres.

Types disponibles :

- gain ou paiement à la banque ;
- déplacement vers une case précise ;
- recul d'un nombre de cases ;
- aller en prison ;
- carte Sortie de prison ;
- prochaine gare ;
- prochaine compagnie ;
- réparations par maison / hôtel ;
- paiement ou encaissement par autre joueur.

Les cartes peuvent aussi être **ajoutées ou supprimées**. Un paquet doit conserver au moins une
carte. La validation empêche les incohérences évidentes : par exemple une carte
**Prochaine gare** est refusée si le plateau ne contient plus aucune gare.

### Presets de plateau

L'éditeur possède sa propre bibliothèque, séparée des presets de règles :

- **Charger** un preset local ;
- **Sauvegarder** le plateau courant ;
- **Importer JSON** depuis un autre fichier ;
- **Exporter** le plateau et ses cartes dans un JSON portable ;
- revenir en un clic au **Plateau standard**.

Les presets utilisent le format versionné `monopoly-board-preset`. Une partie sauvegardée
embarque aussi sa définition complète de plateau dans le JSON de sauvegarde : le preset externe
n'est donc pas nécessaire pour reprendre une partie plus tard.

### Affichage en jeu

Les noms, prix, taxes et barèmes personnalisés sont utilisés directement par le moteur et les
fiches de propriété. Les gares et compagnies affichent également leurs nouveaux loyers ou
multiplicateurs. Les groupes de couleur standard gardent leurs couleurs habituelles ; un nom de
groupe personnalisé reste fonctionnel dans le moteur et utilise une couleur neutre sur le
plateau.

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
de la banque. Depuis la V16.3, acheter une propriété libre ne déclenche plus ce menu : il faut
retomber sur cette propriété lors d'un déplacement futur.

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
  │    ├─ 2 à 4 joueurs
  │    ├─ Règles / presets de règles
  │    └─ Plateau + cartes / presets de plateau
  │          ↓
  │       Partie
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
- 2 à 4 joueurs ;
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
monopoly_poo_gui_v22/
├── main.py
├── console.py
├── README.md
│
├── monopoly/
│   ├── __init__.py
│   ├── game.py
│   ├── options.py
│   ├── board.py
│   ├── board_config.py
│   ├── board_presets.py
│   ├── profile_packs.py
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
│   ├── replay.py
│   ├── statistics.py
│   ├── simulation.py
│   ├── simulation_reports.py
│   └── strategies.py
│
├── ui/
│   ├── app.py
│   ├── theme.py
│   ├── pawns.py
│   ├── audio.py
│   ├── visual_customization.py
│   ├── player_card.py
│   ├── card_reveal.py
│   ├── home.py
│   ├── rule_customization.py
│   ├── board_customization.py
│   ├── board_creation_wizard.py
│   ├── preset_library.py
│   ├── rules_panel.py
│   ├── simulation_lab.py
│   ├── game_window.py
│   ├── board_view.py
│   ├── property_card.py
│   ├── property_manager.py
│   ├── auction_panel.py
│   ├── building_auction_panel.py
│   ├── trade_panel.py
│   ├── turn_transition.py
│   ├── debt_dialog.py
│   ├── mortgage_transfer_dialog.py
│   ├── history_panel.py
│   ├── replay_panel.py
│   ├── landing_build_panel.py
│   ├── end_game_panel.py
│   └── widgets.py
│
├── assets/
│   └── sounds/
│       └── README.md
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

# Prochaines étapes

La prochaine version prévue est **V23 — architecture multi-modes**. Le Monopoly classique actuel deviendra le premier mode d'un système capable de brancher des conditions de victoire, économies, types de cases et mécaniques distinctes. Les premières variantes prévues ensuite sont Empire, Business Tour, Builder, Gamer et Deal.
