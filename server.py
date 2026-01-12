from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import uuid
import glob

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_PATH = "./ffmpeg"   # Render will download this in build step


@app.route("/create", methods=["POST"])
def create():
    data = request.json
    url = data.get("url")
    mode = data.get("mode")   # "video" or "audio"
    quality = data.get("quality")

    file_id = str(uuid.uuid4())
    output = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output,
        "quiet": True,
        "ffmpeg_location": FFMPEG_PATH,
        "noplaylist": True
    }

    if mode == "audio":
        ydl_opts["format"] = "bestaudio"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    else:
        ydl_opts["format"] = quality or "bestvideo+bestaudio/best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # find the created file
    files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{file_id}*"))
    if not files:
        return "Download failed", 500

    filename = os.path.basename(files[0])
    return jsonify({
        "file": filename,
        "url": f"/download/{filename}"
    })


@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
