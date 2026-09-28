# Sons optionnels — V22

Aucun son propriétaire n'est livré avec le projet. Pour activer un effet, glissez simplement un fichier **WAV** dans ce dossier avec le nom exact attendu :

- `dice_roll.wav`
- `pawn_move.wav`
- `cash_gain.wav`
- `cash_loss.wav`
- `property_buy.wav`
- `house_build.wav`
- `hotel_build.wav`
- `jail.wav`
- `card_draw.wav`
- `auction.wav`
- `victory.wav`

Les fichiers absents sont ignorés silencieusement. Le jeu reste entièrement fonctionnel sans audio.

Sur Windows, la lecture utilise `winsound`. Sur Linux/macOS, la couche essaie un lecteur système disponible (`paplay`, `aplay` ou `ffplay`).
