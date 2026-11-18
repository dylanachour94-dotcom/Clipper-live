"""Mise au format vertical 9:16 (fond flou + vidéo au centre) et sous-titres facultatifs."""
import os, subprocess


def vertical(entree, sortie):
    filtre = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2,eq=brightness=-0.15[fond];"
              "[0:v]scale=1080:-2[avant];[fond][avant]overlay=(W-w)/2:(H-h)/2[v]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", entree, "-filter_complex", filtre, "-map", "[v]", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "copy", "-movflags", "+faststart", sortie],
                   check=True)
    return sortie


def sous_titres(entree, sortie):
    """Transcrit en français (faster-whisper) et incruste les sous-titres en gros, au centre bas. Optionnel."""
    from faster_whisper import WhisperModel
    modele = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = modele.transcribe(entree, language="fr", vad_filter=True)
    srt = os.path.splitext(sortie)[0] + ".srt"
    def ts(x):
        h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    with open(srt, "w") as f:
        for i, s in enumerate(segments, 1):
            f.write(f"{i}\n{ts(s.start)} --> {ts(s.end)}\n{s.text.strip().upper()}\n\n")
    style = "Fontname=DejaVu Sans,Fontsize=16,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Alignment=2,MarginV=110"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", entree, "-vf", f"subtitles={srt}:force_style='{style}'",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "copy", "-movflags", "+faststart", sortie],
                   check=True)
    return sortie


def taille_telegram(entree, sortie, max_mo=48):
    """Les bots Telegram n'acceptent pas plus de 50 Mo : on réduit si besoin."""
    if os.path.getsize(entree) <= max_mo * 1e6:
        return entree
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", entree, "-vf", "scale=-2:1280", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "26", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", sortie],
                   check=True)
    return sortie
