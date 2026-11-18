"""Lecture du chat Twitch en anonyme (aucun compte nécessaire), via IRC sécurisé."""
import asyncio, random, ssl, time

HOTE, PORT = "irc.chat.twitch.tv", 6697


async def ecouter(chaines, sur_message, journal=print):
    """Appelle sur_message(chaine, texte, horodatage) pour chaque message ; se reconnecte tout seul."""
    attente = 2
    while True:
        try:
            ctx = ssl.create_default_context()
            r, w = await asyncio.open_connection(HOTE, PORT, ssl=ctx)
            pseudo = f"justinfan{random.randint(10000, 99999)}"   # pseudo anonyme en lecture seule
            w.write(f"NICK {pseudo}\r\n".encode())
            for c in chaines:
                w.write(f"JOIN #{c}\r\n".encode())
            await w.drain()
            journal(f"chat : connecté ({', '.join(chaines)})")
            attente = 2
            while True:
                ligne = await asyncio.wait_for(r.readline(), timeout=360)
                if not ligne:
                    raise ConnectionError("connexion fermée")
                ligne = ligne.decode("utf-8", "ignore").rstrip("\r\n")
                if ligne.startswith("PING"):
                    w.write(("PONG" + ligne[4:] + "\r\n").encode()); await w.drain()
                    continue
                # :pseudo!pseudo@pseudo.tmi.twitch.tv PRIVMSG #chaine :message
                if " PRIVMSG #" in ligne:
                    tete, _, texte = ligne.partition(" PRIVMSG #")
                    chaine, _, msg = texte.partition(" :")
                    sur_message(chaine.lower(), msg, time.time())
        except Exception as e:
            journal(f"chat : coupure ({e}), reconnexion dans {attente} s")
            await asyncio.sleep(attente)
            attente = min(attente * 2, 60)
