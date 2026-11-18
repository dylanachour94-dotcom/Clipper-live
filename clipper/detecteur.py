"""Repère les pics du chat : on compte les messages par tranches de 10 s et on compare à la normale."""
import statistics, time
from collections import deque


class Detecteur:
    def __init__(self, reglages):
        self.r = reglages
        self.taille_ref = max(3, reglages.reference_min * 60 // reglages.fenetre_s)
        self.historique = {}      # chaîne -> deque des comptes des tranches passées
        self.courant = {}         # chaîne -> [début de tranche, nb messages, nb avec mot clé, exemples]
        self.dernier_clip = {}    # chaîne -> heure du dernier pic

    def message(self, chaine, texte, t):
        c = self.courant.setdefault(chaine, [self._debut(t), 0, 0, []])
        if t >= c[0] + self.r.fenetre_s:   # la tranche est finie : elle sera évaluée par tic()
            return
        c[1] += 1
        bas = texte.lower()
        if any(m in bas for m in self.r.mots_cles):
            c[2] += 1
        if len(c[3]) < 6 and len(texte) <= 60:
            c[3].append(texte)

    def _debut(self, t):
        return t - (t % self.r.fenetre_s)

    def tic(self, maintenant=None):
        """À appeler régulièrement : renvoie la liste des pics [(chaîne, début, fin, n, référence, exemples)]."""
        maintenant = maintenant or time.time()
        pics = []
        for chaine, c in list(self.courant.items()):
            if maintenant < c[0] + self.r.fenetre_s:
                continue
            debut, n, n_mots, exemples = c
            h = self.historique.setdefault(chaine, deque(maxlen=self.taille_ref))
            ref = statistics.median(h) if len(h) >= 3 else None
            if ref is not None and n >= self.r.minimum_messages:
                fort = n >= self.r.multiplicateur * max(ref, 1)
                rieur = n_mots / n >= self.r.part_mots_cles and n >= 1.5 * max(ref, 1)
                libre = debut - self.dernier_clip.get(chaine, 0) >= self.r.pause_entre_clips_s
                if (fort or rieur) and libre:
                    self.dernier_clip[chaine] = debut
                    pics.append((chaine, debut, debut + self.r.fenetre_s, n, ref, exemples))
            h.append(n)
            self.courant[chaine] = [self._debut(maintenant), 0, 0, []]
        return pics
