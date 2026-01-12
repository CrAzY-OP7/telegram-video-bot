from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import uuid
import subprocess

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route("/create", methods=["POST"])
def create():
    data = request.json
    url = data.get("url")
    mode = data.get("mode")  # "video" or "audio"
    quality = data.get("quality")

    file_id = str(uuid.uuid4())
    output = f"{DOWNLOAD_DIR}/{file_id}.%(ext)s"

    ydl_opts = {
        "outtmpl": output,
        "quiet": True
    }

    if mode == "audio":
        ydl_opts["format"] = "bestaudio"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    else:
        ydl_opts["format"] = quality

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the real file
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(file_id):
            return jsonify({"file": f})

    return "Error", 500

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
