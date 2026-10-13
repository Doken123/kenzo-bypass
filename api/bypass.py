def bypass_safelink(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Cek meta refresh
        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta:
            m = re.search(r'url=(.+)', meta.get("content", ""), re.I)
            if m:
                return m.group(1).strip().strip('"\'')

        # 2. Cek semua script — cari url / link
        for s in soup.find_all("script"):
            if not s.string:
                continue
            txt = s.string

            # Pattern: window.location = "https://..."
            m = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', txt)
            if m: return m.group(1)

            # Pattern: var url = "https://..."
            m = re.search(r'(?:var|let|const)\s+(?:url|link|target|redirect)\s*=\s*["\']([^"\']+)["\']', txt)
            if m: return m.group(1)

            # Pattern: .replace("...","...") base64 decode
            m = re.search(r'atob\(["\']([^"\']+)["\']\)', txt)
            if m:
                try:
                    decoded = base64.b64decode(m.group(1)).decode("utf-8", "ignore")
                    m2 = re.search(r'(https?://[^\s"\']+)', decoded)
                    if m2: return m2.group(1)
                except: pass

            # Pattern: cari URL mentah di script
            m = re.search(r'(https?://[^\s"\']+\.(?:html|php|apk|zip|mp4|pdf|rar))', txt)
            if m: return m.group(1)

        # 3. Cek hidden input / data attribute
        for el in soup.find_all(attrs={"data-url": True}):
            return el["data-url"]
        for el in soup.find_all(attrs={"data-href": True}):
            return el["data-href"]

        # 4. Cek iframe
        iframe = soup.find("iframe", src=True)
        if iframe and iframe["src"].startswith("http"):
            return iframe["src"]

        return "LINK TIDAK DITEMUKAN — coba provider lain atau cek manual."
    except Exception as e:
        return f"ERROR: {str(e)}"
