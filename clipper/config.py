"""Lecture des réglages (reglages.toml) et des secrets (.env)."""
import os, tomllib
from dataclasses import dataclass, field

ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class Reglages:
    streamers: list
    fenetre_s: int = 10              # on compte les messages du chat par tranches de 10 s
    reference_min: int = 5           # moyenne de référence : les 5 dernières minutes
    multiplicateur: float = 2.5      # pic = 2,5 fois plus de messages que la normale
    minimum_messages: int = 25       # et au moins 25 messages dans la tranche de 10 s
    mots_cles: list = field(default_factory=lambda: ["mdr", "ptdr", "kekw", "lul", "omg", "???", "wtf", "ahah", "pog"])
    part_mots_cles: float = 0.35     # ou : plus de 35 % des messages contiennent un mot clé (avec au moins le minimum)
    avant_s: int = 20                # vidéo gardée avant le pic
    apres_s: int = 10                # vidéo gardée après le pic
    latence_video_s: int = 8         # retard de la vidéo sur le chat (réglable si les clips arrivent trop tôt/tard)
    pause_entre_clips_s: int = 60    # pas deux clips du même streamer à moins d'1 min
    memoire_video_s: int = 180       # vidéo gardée en mémoire (rolling buffer)
    qualite: str = "720p60,720p,best"
    vertical: bool = True            # mettre le clip au format 9:16 (fond flou + vidéo au centre)
    sous_titres: bool = False        # sous-titres automatiques (version 2, plus lent)
    dossier: str = os.path.join(ICI, "donnees")


def charger(chemin=None):
    chemin = chemin or os.path.join(ICI, "reglages.toml")
    with open(chemin, "rb") as f:
        d = tomllib.load(f)
    r = Reglages(**d)
    r.streamers = [s.strip().lower() for s in r.streamers if s.strip()]
    return r


def secrets():
    """TELEGRAM_TOKEN et TELEGRAM_CHAT_ID, lus dans .env (jamais dans le code ni sur GitHub)."""
    env = {}
    p = os.path.join(ICI, ".env")
    if os.path.exists(p):
        for ligne in open(p):
            if "=" in ligne and not ligne.strip().startswith("#"):
                k, v = ligne.split("=", 1)
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k.startswith("TELEGRAM_")})
    return env
