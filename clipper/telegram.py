"""Envoi des clips sur Telegram (bot personnel)."""
import json, os, uuid, urllib.request

API = "https://api.telegram.org/bot{token}/{methode}"


def _appel(token, methode, champs=None, fichier=None, delai=120):
    url = API.format(token=token, methode=methode)
    if fichier is None:
        data = json.dumps(champs or {}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        borne = uuid.uuid4().hex
        corps = b""
        for k, v in (champs or {}).items():
            corps += f"--{borne}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        nom_champ, chemin = fichier
        corps += (f"--{borne}\r\nContent-Disposition: form-data; name=\"{nom_champ}\"; filename=\"{os.path.basename(chemin)}\"\r\n"
                  f"Content-Type: video/mp4\r\n\r\n").encode() + open(chemin, "rb").read() + f"\r\n--{borne}--\r\n".encode()
        req = urllib.request.Request(url, data=corps, headers={"Content-Type": f"multipart/form-data; boundary={borne}"})
    with urllib.request.urlopen(req, timeout=delai) as r:
        return json.load(r)


def trouver_chat_id(token):
    """Après que l'utilisateur a écrit à son bot : récupère l'identifiant de la conversation."""
    res = _appel(token, "getUpdates")
    for u in reversed(res.get("result", [])):
        m = u.get("message") or u.get("edited_message")
        if m:
            return str(m["chat"]["id"])
    return None


def texte(token, chat_id, message):
    return _appel(token, "sendMessage", {"chat_id": chat_id, "text": message})


def video(token, chat_id, chemin, legende):
    return _appel(token, "sendVideo", {"chat_id": chat_id, "caption": legende[:1000], "supports_streaming": "true"},
                  fichier=("video", chemin))
