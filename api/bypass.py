from flask import Flask, request, jsonify
import requests
import re
import base64
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def bypass_safelink(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Meta refresh
        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta:
            m = re.search(r'url=(.+)', meta.get("content", ""), re.I)
            if m:
                return m.group(1).strip().strip('"\'')

        # 2. Scan semua script
        for s in soup.find_all("script"):
            if not s.string:
                continue
            txt = s.string

            # window.location = "https://..."
            m = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', txt)
            if m:
                return m.group(1)

            # var url = "https://..."
            m = re.search(r'(?:var|let|const)\s+(?:url|link|target|redirect|dest)\s*=\s*["\']([^"\']+)["\']', txt)
            if m:
                return m.group(1)

            # atob base64
            m = re.search(r'atob\(["\']([^"\']+)["\']\)', txt)
            if m:
                try:
                    decoded = base64.b64decode(m.group(1) + "==").decode("utf-8", "ignore")
                    m2 = re.search(r'(https?://[^\s"\']+)', decoded)
                    if m2:
                        return m2.group(1)
                except Exception:
                    pass

            # URL mentah di script
            m = re.search(r'(https?://[^\s"\']+\.(?:html|php|apk|zip|mp4|pdf|rar|jpg|png))', txt)
            if m:
                return m.group(1)

        # 3. Data attribute
        for el in soup.find_all(attrs={"data-url": True}):
            v = el.get("data-url")
            if v and v.startswith("http"):
                return v
        for el in soup.find_all(attrs={"data-href": True}):
            v = el.get("data-href")
            if v and v.startswith("http"):
                return v

        # 4. Iframe
        iframe = soup.find("iframe", src=True)
        if iframe and iframe["src"].startswith("http"):
            return iframe["src"]

        # 5. Anchor link yang bukan domain safelink
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and "sfl.gl" not in href and "safelinku" not in href:
                return href

        return "LINK TIDAK DITEMUKAN — coba provider lain atau cek manual."
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.route("/api/bypass", methods=["GET"])
def bypass():
    target = request.args.get("url")
    provider = request.args.get("provider", "safelinku")

    if not target:
        return jsonify({"error": "Parameter 'url' wajib diisi."}), 400

    handlers = {
        "safelinku": bypass_safelink,
        "tinyurl": bypass_safelink,
        "linkvertise": bypass_safelink,
        "sub4unlock": bypass_safelink,
        "clksh": bypass_safelink,
        "bitly": bypass_safelink,
        "shrinkme": bypass_safelink,
        "tpili": bypass_safelink,
    }

    fn = handlers.get(provider, bypass_safelink)
    result = fn(target)
    return jsonify({"bypass": result})


# Handler wajib buat Vercel
handler = app
