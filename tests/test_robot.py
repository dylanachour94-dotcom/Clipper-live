"""Test de bout en bout sans Twitch ni Telegram : faux live (mire ffmpeg) + faux chat avec un pic."""
import asyncio, os, shutil, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clipper import config, robot
from clipper.detecteur import Detecteur

def test_detecteur():
    r = config.Reglages(streamers=["x"])
    d = Detecteur(r); t0 = 1_000_000
    for w in range(30):                      # 5 minutes « normales » : 8 messages / 10 s
        for i in range(8): d.message("x", "salut", t0 + w * 10 + i)
        assert d.tic(t0 + (w + 1) * 10) == []
    for i in range(60): d.message("x", "MDR", t0 + 300 + i * 0.1)   # pic : 60 messages
    pics = d.tic(t0 + 310)
    assert len(pics) == 1 and pics[0][3] == 60, pics
    for i in range(60): d.message("x", "MDR", t0 + 310 + i * 0.1)   # 2e pic trop proche : ignoré (pause 60 s)
    assert d.tic(t0 + 320) == []
    print("détecteur : OK")

async def bout_en_bout():
    dossier = tempfile.mkdtemp()
    r = config.Reglages(streamers=["test"], dossier=dossier, avant_s=6, apres_s=3, latence_video_s=0, vertical=True)
    faux_live = ["ffmpeg", "-loglevel", "error", "-re", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
                 "-f", "lavfi", "-i", "sine=frequency=440", "-c:v", "libx264", "-preset", "ultrafast", "-g", "30",
                 "-c:a", "aac", "-f", "mpegts", "pipe:1"]
    rb = robot.Robot(r, {}, sources={"test": faux_live}, envoyer=False)
    taches = [asyncio.create_task(rb.enr["test"].tourner()), asyncio.create_task(rb._tic())]
    t0 = time.time()
    while time.time() - t0 < 32:             # 3 « minutes » accélérées : on remplit l'historique à la main
        await asyncio.sleep(1)
    h = rb.det.historique.setdefault("test", __import__("collections").deque(maxlen=30))
    h.extend([5] * 10)
    t = time.time()
    for i in range(80): rb.det.message("test", "MDR 😂", t)
    for _ in range(60):
        await asyncio.sleep(1)
        if rb.clips_faits: break
    for x in taches: x.cancel()
    clips = rb.clips_faits
    assert clips, "aucun clip produit"
    import subprocess, json
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                                      "-of", "json", clips[0]], capture_output=True, text=True).stdout)
    print("clip :", clips[0], info["format"]["duration"], "s", info["streams"][0].get("width"), "x", info["streams"][0].get("height"))
    shutil.copy(clips[0], sys.argv[1] if len(sys.argv) > 1 else "/tmp/clip_test.mp4")

test_detecteur()
asyncio.run(bout_en_bout())
