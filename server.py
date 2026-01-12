from flask import Flask, redirect
import secrets
import os

app = Flask(__name__)

link_map = {}

@app.route("/dl/<token>")
def download(token):
    url = link_map.get(token)
    if not url:
        return "Invalid or expired link", 404

    return redirect(url, code=302)


def create_redirect_link(real_url, base_url):
    token = secrets.token_urlsafe(8)
    link_map[token] = real_url
    return f"{base_url}/dl/{token}"


# VERY IMPORTANT for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
