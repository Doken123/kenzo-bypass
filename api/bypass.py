from flask import Flask, request, jsonify
import requests, re
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
}

def bypass_safelink(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")

        # Cari meta refresh
        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta:
            m = re.search(r'url=(.+)', meta.get("content", ""))
            if m:
                return m.group(1).strip()

        # Cari script redirect
        for s in soup.find_all("script"):
            if s.string:
                m = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)', s.string)
                if m:
                    return m.group(1)
                m2 = re.search(r'(https?://[^\s"\']+\.(?:html|php|mp4|zip|apk))', s.string)
                if m2:
                    return m2.group(1)

        return "GAK KETEMU ANJING, LINKNYA OBFUSCATED! 🖕"
    except Exception as e:
        return f"ERROR KONTOL: {str(e)}"

@app.route("/api/bypass", methods=["GET"])
def bypass():
    target = request.args.get("url")
    if not target:
        return jsonify({"error": "MANA URL NYA KONTOL! 🖕"}), 400
    return jsonify({"bypass": bypass_safelink(target)})

# Vercel handler
def handler(request):
    return app(request.environ, lambda *a: None)
