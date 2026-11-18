# Robot de clips Twitch

Surveille le chat de plusieurs streamers Twitch, compte les messages toutes les 10 secondes, repère les pics (beaucoup plus de messages que la normale, ou une vague de « MDR », « KEKW », « ??? »), coupe la vidéo **20 s avant le pic → 10 s après**, la met au **format vertical** et l'envoie sur **Telegram** en moins d'une minute.

## Installer sur le serveur (Ubuntu 24.04)
```bash
apt-get update && apt-get install -y git
git clone https://github.com/<ton-compte>/clipper-live.git
cd clipper-live && ./installer.sh
```
Le script demande la clé du bot Telegram (donnée par @BotFather) : elle reste sur le serveur, dans le fichier `.env`.

## Régler
Tout est dans `reglages.toml` (streamers, seuil des pics, secondes avant/après, vertical, sous-titres). Après un changement :
```bash
sudo systemctl restart clipper
```

## Commandes utiles
- Voir ce que fait le robot : `journalctl -u clipper -f`
- Arrêter / relancer : `sudo systemctl stop clipper` / `sudo systemctl start clipper`
- Mettre à jour : `git pull && sudo systemctl restart clipper`

## Fonctionnement
| Fichier | Rôle |
|---|---|
| `clipper/chat.py` | lit le chat Twitch en anonyme (aucun compte nécessaire) |
| `clipper/detecteur.py` | compte par tranches de 10 s et repère les pics |
| `clipper/enregistreur.py` | enregistre chaque live en continu (mémoire des 3 dernières minutes) et coupe les clips |
| `clipper/montage.py` | format vertical, sous-titres (optionnels), taille compatible Telegram |
| `clipper/telegram.py` | envoi des clips |
| `tests/test_robot.py` | test complet sans Twitch ni Telegram |

Rappel : publier les clips d'un streamer demande son accord (ou son programme de clippeurs), et un montage personnel (titre, sous-titres, recadrage) pour être monétisable.
