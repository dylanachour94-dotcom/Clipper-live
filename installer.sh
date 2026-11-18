#!/usr/bin/env bash
# Installation du robot de clips sur un serveur Ubuntu 24.04 (à lancer en root, depuis le dossier du robot).
set -e
cd "$(dirname "$0")"
echo "== 1/4 Logiciels (ffmpeg, Python)…"
apt-get update -qq && apt-get install -y -qq ffmpeg python3-venv python3-pip fonts-dejavu-core >/dev/null
echo "== 2/4 Streamlink (lecture des lives Twitch)…"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip streamlink
ln -sf "$PWD/.venv/bin/streamlink" /usr/local/bin/streamlink
echo "== 3/4 Telegram…"
if ! grep -q TELEGRAM_CHAT_ID .env 2>/dev/null; then
  echo "Colle la clé (token) donnée par @BotFather, puis Entrée (elle ne s'affiche pas) :"
  read -rs TOKEN; echo
  echo "Maintenant, sur ton téléphone, envoie « salut » à ton bot Telegram, puis appuie sur Entrée ici."
  read -r _
  CHAT_ID=$(TELEGRAM_TOKEN="$TOKEN" python3 -c "
import os; from clipper import telegram
print(telegram.trouver_chat_id(os.environ['TELEGRAM_TOKEN']) or '')")
  if [ -z "$CHAT_ID" ]; then echo "Je n'ai pas trouvé ton message : envoie « salut » au bot et relance ./installer.sh"; exit 1; fi
  printf "TELEGRAM_TOKEN=%s\nTELEGRAM_CHAT_ID=%s\n" "$TOKEN" "$CHAT_ID" > .env
  chmod 600 .env
  echo "Telegram OK."
fi
echo "== 4/4 Démarrage automatique (service « clipper »)…"
cat > /etc/systemd/system/clipper.service <<UNIT
[Unit]
Description=Robot de clips Twitch
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=$PWD
ExecStart=/usr/bin/python3 -m clipper.robot
Environment=PATH=$PWD/.venv/bin:/usr/local/bin:/usr/bin:/bin
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now clipper
sleep 3
systemctl --no-pager status clipper | head -5
echo
echo "Terminé ! Tu dois recevoir « Robot de clips démarré » sur Telegram."
echo "Voir ce que fait le robot : journalctl -u clipper -f      (Ctrl+C pour quitter)"
