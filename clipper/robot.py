"""Le robot : chat + détection des pics + enregistrement + découpe + envoi sur Telegram.

Lancement : python3 -m clipper.robot
"""
import asyncio, datetime, os, sys, time
from . import config, telegram, montage
from .chat import ecouter
from .detecteur import Detecteur
from .enregistreur import Enregistreur, SEG


def journal(msg):
    ligne = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(ligne, flush=True)


class Robot:
    def __init__(self, reglages, secrets, sources=None, envoyer=True):
        self.r = reglages
        self.token = secrets.get("TELEGRAM_TOKEN")
        self.chat_id = secrets.get("TELEGRAM_CHAT_ID")
        self.envoyer = envoyer and bool(self.token and self.chat_id)
        self.det = Detecteur(reglages)
        sources = sources or {}
        self.enr = {c: Enregistreur(c, reglages, journal, sources.get(c)) for c in reglages.streamers}
        self.clips_faits = []

    async def _tic(self):
        while True:
            await asyncio.sleep(1)
            for pic in self.det.tic():
                asyncio.create_task(self._clip(*pic))

    async def _clip(self, chaine, debut, fin, n, ref, exemples):
        e = self.enr.get(chaine)
        heure = datetime.datetime.fromtimestamp(debut).strftime("%H:%M:%S")
        if not e or not e.en_ligne:
            journal(f"{chaine} : pic à {heure} ({n} messages, normale {ref:.0f}) mais pas de vidéo en mémoire")
            return
        lat = self.r.latence_video_s
        v_debut, v_fin = debut - self.r.avant_s + lat, fin + self.r.apres_s + lat
        journal(f"{chaine} : PIC à {heure} ({n} messages en {self.r.fenetre_s} s, normale {ref:.0f}) → clip en préparation")
        await asyncio.sleep(max(0, v_fin + 2 * SEG + 1 - time.time()))   # on attend que la vidéo après le pic soit arrivée
        base = os.path.join(self.r.dossier, "clips", f"{chaine}_{datetime.datetime.fromtimestamp(debut):%Y%m%d_%H%M%S}")
        try:
            brut = await asyncio.to_thread(e.couper, v_debut, v_fin, base + "_brut.mp4")
            if not brut:
                journal(f"{chaine} : vidéo introuvable pour ce pic"); return
            final = brut
            if self.r.vertical:
                final = await asyncio.to_thread(montage.vertical, brut, base + "_vertical.mp4")
            if self.r.sous_titres:
                try:
                    final = await asyncio.to_thread(montage.sous_titres, final, base + "_st.mp4")
                except Exception as ex:
                    journal(f"sous-titres impossibles ({ex}), envoi sans")
            final = await asyncio.to_thread(montage.taille_telegram, final, base + "_tg.mp4")
            self.clips_faits.append(final)
            legende = (f"🔥 {chaine.upper()} · pic à {heure}\n"
                       f"{n} messages en {self.r.fenetre_s} s (normale : {ref:.0f})\n"
                       + ("Chat : " + " | ".join(exemples[:4]) + "\n" if exemples else "")
                       + f"Clip : {self.r.avant_s} s avant → {self.r.apres_s} s après · prêt {time.time() - fin:.0f} s après le pic")
            if self.envoyer:
                await asyncio.to_thread(telegram.video, self.token, self.chat_id, final, legende)
            journal(f"{chaine} : clip envoyé ({os.path.basename(final)})")
            for p in (brut,):
                if p != final and os.path.exists(p):
                    os.remove(p)
        except Exception as ex:
            journal(f"{chaine} : erreur pendant le clip ({ex})")

    async def tourner(self):
        journal(f"robot démarré : {', '.join(self.r.streamers)}")
        if self.envoyer:
            try:
                await asyncio.to_thread(telegram.texte, self.token, self.chat_id,
                                        "🤖 Robot de clips démarré. Je surveille : " + ", ".join(self.r.streamers))
            except Exception as ex:
                journal(f"Telegram injoignable au démarrage ({ex})")
        taches = [asyncio.create_task(e.tourner()) for e in self.enr.values()]
        taches.append(asyncio.create_task(ecouter(self.r.streamers, self.det.message, journal)))
        taches.append(asyncio.create_task(self._tic()))
        await asyncio.gather(*taches)


def main():
    r = config.charger()
    s = config.secrets()
    if not (s.get("TELEGRAM_TOKEN") and s.get("TELEGRAM_CHAT_ID")):
        journal("ATTENTION : TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID manquant dans .env : les clips restent dans donnees/clips/")
    asyncio.run(Robot(r, s).tourner())


if __name__ == "__main__":
    main()
