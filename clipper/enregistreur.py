"""Enregistre le live en continu par morceaux de 2 s, et ne garde que les dernières minutes (mémoire tournante)."""
import asyncio, glob, os, shutil, subprocess, time

SEG = 2  # durée d'un morceau, en secondes


class Enregistreur:
    def __init__(self, chaine, reglages, journal=print, source=None):
        self.chaine, self.r, self.journal = chaine, reglages, journal
        self.dossier = os.path.join(reglages.dossier, "memoire", chaine)
        self.source = source            # pour les tests : une commande qui écrit un flux vidéo sur la sortie
        self.en_ligne = False

    def morceaux(self):
        """[(heure de début, chemin)] triés ; le nom du fichier est l'heure (epoch) de début du morceau."""
        res = []
        for p in glob.glob(os.path.join(self.dossier, "*.ts")):
            try:
                res.append((int(os.path.basename(p)[:-3]), p))
            except ValueError:
                pass
        return sorted(res)

    def _nettoyer(self):
        limite = time.time() - self.r.memoire_video_s
        for t, p in self.morceaux():
            if t < limite:
                try: os.remove(p)
                except OSError: pass

    async def tourner(self):
        os.makedirs(self.dossier, exist_ok=True)
        while True:
            for p in glob.glob(os.path.join(self.dossier, "*.ts")):
                os.remove(p)
            lecteur = self.source or ["streamlink", "--stdout", "--twitch-disable-ads", "--hls-live-edge", "2",
                                      "--loglevel", "error", f"https://www.twitch.tv/{self.chaine}", self.r.qualite]
            seg = ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-map", "0", "-c", "copy", "-f", "segment",
                   "-segment_time", str(SEG), "-reset_timestamps", "1", "-strftime", "1",
                   os.path.join(self.dossier, "%s.ts")]
            lire, ecrire = os.pipe()   # tuyau entre le lecteur du live et le découpeur
            p1 = await asyncio.create_subprocess_exec(*lecteur, stdout=ecrire, stderr=subprocess.DEVNULL)
            p2 = await asyncio.create_subprocess_exec(*seg, stdin=lire, stderr=subprocess.DEVNULL)
            os.close(lire); os.close(ecrire)
            debut = time.time()
            while p2.returncode is None and p1.returncode is None:
                await asyncio.sleep(2)
                self._nettoyer()
                if not self.en_ligne and self.morceaux():
                    self.en_ligne = True
                    self.journal(f"{self.chaine} : en live, enregistrement en cours")
            for p in (p1, p2):
                if p.returncode is None:
                    p.kill()
                await p.wait()
            if self.en_ligne:
                self.journal(f"{self.chaine} : fin du live ou coupure")
            self.en_ligne = False
            await asyncio.sleep(60 if time.time() - debut < 30 else 5)   # hors ligne : on revérifie chaque minute

    def couper(self, debut, fin, sortie):
        """Assemble les morceaux qui couvrent [debut, fin] (heures epoch) puis coupe précisément."""
        choix = [(t, p) for t, p in self.morceaux() if t + SEG + 1 >= debut and t <= fin]
        if not choix:
            return None
        os.makedirs(os.path.dirname(sortie), exist_ok=True)
        liste = sortie + ".txt"
        with open(liste, "w") as f:
            for _, p in choix:
                f.write(f"file '{p}'\n")
        decalage = max(0.0, debut - choix[0][0])
        duree = fin - debut
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", liste,
                        "-ss", f"{decalage:.2f}", "-t", f"{duree:.2f}", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", sortie], check=True)
        os.remove(liste)
        return sortie
