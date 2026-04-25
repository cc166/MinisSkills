#!/usr/bin/env python3
"""Generate/edit images through an OpenAI-compatible Images API.

Env:
  OPENAI_API_KEY       required unless --api-key is passed
  OPENAI_BASE_URL      default: https://api.openai.com/v1
  OPENAI_IMAGE_MODEL   default: gpt-image-2

Examples:
  python3 openai_image_api.py gen "a rabbit" -o /var/minis/attachments/rabbit.png
  python3 openai_image_api.py edit --image in.png "remove the logo" -o out.png
"""
import argparse
import base64
import json
import mimetypes
import os
import ssl
import sys
import time
import uuid
import urllib.parse
import urllib.request
import http.client
import http.client as _http_client
import subprocess
import tempfile


def die(msg, code=1):
    print(json.dumps({"success": False, "error": msg}, ensure_ascii=False, indent=2), file=sys.stderr)
    raise SystemExit(code)


def load_profile_env():
    """Best-effort load /etc/profile exports for non-login subprocesses.

    Minis environment variables are commonly materialized there. Do not print
    values; only populate os.environ when missing.
    """
    path = "/etc/profile"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("export ") or "=" not in line:
                    continue
                part = line[len("export "):]
                name, val = part.split("=", 1)
                name = name.strip()
                if not name or name in os.environ:
                    continue
                val = val.strip()
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                    val = val[1:-1]
                os.environ[name] = val
    except Exception:
        pass


def shutil_which(cmd):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = os.path.join(d, cmd)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return None


def endpoint_url(base_url, endpoint):
    base = (base_url or "https://api.openai.com/v1").rstrip("/")
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return base + endpoint


def request_json(url, api_key, payload, timeout=240, retries=2):
    """POST JSON and return (status, raw_text).

    Prefer curl when available: it handles this gateway's large chunked image
    responses reliably in iSH, while Python http.client/urllib can sometimes
    return empty output or raise IncompleteRead for valid responses.
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_status, last_raw = None, ""
    org = os.environ.get("OPENAI_ORG_ID")
    project = os.environ.get("OPENAI_PROJECT")
    if shutil_which("curl"):
        for attempt in range(retries + 1):
            fd, payload_path = tempfile.mkstemp(prefix="image2_payload_", suffix=".json")
            os.close(fd)
            out_fd, out_path = tempfile.mkstemp(prefix="image2_response_", suffix=".json")
            os.close(out_fd)
            try:
                with open(payload_path, "wb") as f:
                    f.write(body)
                cmd = [
                    "curl", "-sS", "-L",
                    "--max-time", str(timeout),
                    "-o", out_path,
                    "-w", "%{http_code}",
                    "-H", "Authorization: Bearer " + api_key,
                    "-H", "Content-Type: application/json",
                    "-H", "Accept: application/json",
                ]
                if org:
                    cmd += ["-H", "OpenAI-Organization: " + org]
                if project:
                    cmd += ["-H", "OpenAI-Project: " + project]
                cmd += ["--data", "@" + payload_path, url]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
                status_text = (r.stdout or "").strip()[-3:]
                status = int(status_text) if status_text.isdigit() else 0
                try:
                    with open(out_path, "rb") as f:
                        raw = f.read().decode("utf-8", errors="replace")
                except Exception:
                    raw = ""
                if status >= 200 and status < 300:
                    return status, raw
                last_status, last_raw = status, raw or r.stderr
                if status not in (408, 409, 425, 429, 500, 502, 503, 504) or attempt >= retries:
                    return last_status, last_raw
            except Exception as e:
                last_status = 0
                last_raw = type(e).__name__ + ": " + str(e)
                if attempt >= retries:
                    return last_status, last_raw
            finally:
                for p in (payload_path, out_path):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            time.sleep(2 * (attempt + 1))
        return last_status or 0, last_raw

    # Fallback pure Python path.
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", "Bearer " + api_key)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        if org:
            req.add_header("OpenAI-Organization", org)
        if project:
            req.add_header("OpenAI-Project", project)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
                try:
                    raw_bytes = r.read()
                except _http_client.IncompleteRead as e:
                    raw_bytes = e.partial or b""
                return r.status, raw_bytes.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last_status = e.code
            try:
                last_raw = e.read().decode("utf-8", errors="replace")
            except _http_client.IncompleteRead as ir:
                last_raw = (ir.partial or b"").decode("utf-8", errors="replace")
            if e.code not in (408, 409, 425, 429, 500, 502, 503, 504) or attempt >= retries:
                return last_status, last_raw
        except Exception as e:
            partial = getattr(e, "partial", None)
            if partial:
                try:
                    return 200, partial.decode("utf-8", errors="replace")
                except Exception:
                    pass
            last_status = 0
            last_raw = type(e).__name__ + ": " + str(e)
            if attempt >= retries:
                return last_status, last_raw
        time.sleep(2 * (attempt + 1))
    return last_status or 0, last_raw


def multipart_body(fields, files):
    boundary = "----minis-" + uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        if value is None:
            continue
        chunks.append(("--%s\r\n" % boundary).encode())
        chunks.append(('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode())
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    for name, path in files.items():
        filename = os.path.basename(path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            data = f.read()
        chunks.append(("--%s\r\n" % boundary).encode())
        chunks.append(('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (name, filename)).encode())
        chunks.append(("Content-Type: %s\r\n\r\n" % ctype).encode())
        chunks.append(data)
        chunks.append(b"\r\n")
    chunks.append(("--%s--\r\n" % boundary).encode())
    return boundary, b"".join(chunks)


def request_multipart(url, api_key, fields, files, timeout=300):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    boundary, body = multipart_body(fields, files)
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "multipart/form-data; boundary=" + boundary,
        "Accept": "application/json",
    }
    org = os.environ.get("OPENAI_ORG_ID")
    project = os.environ.get("OPENAI_PROJECT")
    if org:
        headers["OpenAI-Organization"] = org
    if project:
        headers["OpenAI-Project"] = project
    conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(parsed.netloc, timeout=timeout, context=ssl.create_default_context()) if parsed.scheme == "https" else conn_cls(parsed.netloc, timeout=timeout)
    conn.request("POST", path, body=body, headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8", errors="replace")
    status = resp.status
    conn.close()
    return status, raw


def salvage_image_from_partial(raw, output):
    """Extract b64_json from a truncated JSON response if possible."""
    marker = '"b64_json":"'
    start = raw.find(marker)
    if start < 0:
        return None
    start += len(marker)
    chars = []
    alphabet = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    for ch in raw[start:]:
        if ch in alphabet:
            chars.append(ch)
        else:
            break
    b64 = "".join(chars)
    # Trim to valid base64 length. If response is too truncated, decode may still fail.
    b64 = b64[:len(b64) - (len(b64) % 4)]
    if len(b64) < 1000:
        return None
    try:
        img = base64.b64decode(b64, validate=False)
    except Exception:
        return None
    # Basic PNG/JPEG/WebP sanity check.
    if not (img.startswith(b"\x89PNG") or img.startswith(b"\xff\xd8") or img.startswith(b"RIFF")):
        return None
    with open(output, "wb") as f:
        f.write(img)
    return len(img)


def write_output_from_response(raw, output, api_key=None):
    try:
        data = json.loads(raw)
    except Exception:
        salvaged = salvage_image_from_partial(raw, output)
        if salvaged:
            return salvaged, {"data": [{"revised_prompt": ""}], "partial_salvaged": True}
        die("API returned non-JSON response: " + raw[:800])
    if "error" in data:
        err = data.get("error")
        if isinstance(err, dict):
            msg = err.get("message") or json.dumps(err, ensure_ascii=False)
        else:
            msg = str(err)
        die(msg)
    items = data.get("data") or []
    if not items:
        # Some Responses-compatible gateways may return output content.
        text = json.dumps(data, ensure_ascii=False)[:1200]
        die("No image data found in API response: " + text)
    item = items[0]
    b64 = item.get("b64_json") or item.get("base64") or item.get("image_base64")
    if b64:
        if "," in b64 and b64.strip().startswith("data:"):
            b64 = b64.split(",", 1)[1]
        img = base64.b64decode(b64)
        with open(output, "wb") as f:
            f.write(img)
        return len(img), data
    url = item.get("url")
    if url:
        req = urllib.request.Request(url)
        if api_key:
            # Harmless for signed URLs; useful for gateways serving protected files.
            req.add_header("Authorization", "Bearer " + api_key)
        with urllib.request.urlopen(req, timeout=240, context=ssl.create_default_context()) as r:
            img = r.read()
        with open(output, "wb") as f:
            f.write(img)
        return len(img), data
    die("First data item has neither b64_json nor url: " + json.dumps(item, ensure_ascii=False)[:800])


def add_common_image_params(payload, args):
    if args.size:
        payload["size"] = args.size
    if args.quality:
        payload["quality"] = args.quality
    if args.background:
        payload["background"] = args.background
    if args.output_format:
        payload["output_format"] = args.output_format
    if args.n is not None:
        payload["n"] = args.n
    return payload


def cmd_gen(args):
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        die("OPENAI_API_KEY is not set. Set it in Minis Environment Variables or pass --api-key.")
    base_url = args.base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = args.model or os.environ.get("OPENAI_IMAGE_MODEL") or "gpt-image-2"
    url = endpoint_url(base_url, "/images/generations")
    payload = add_common_image_params({"model": model, "prompt": args.prompt}, args)
    status, raw = request_json(url, api_key, payload, timeout=args.timeout, retries=args.retries)
    if status < 200 or status >= 300:
        die("HTTP %s from %s: %s" % (status, url, raw[:1200]))
    size, data = write_output_from_response(raw, args.output, api_key=api_key)
    print(json.dumps({
        "success": True,
        "mode": "openai_images_api_generation",
        "model": model,
        "path": args.output,
        "size": size,
        "revised_prompt": (data.get("data") or [{}])[0].get("revised_prompt", ""),
    }, ensure_ascii=False, indent=2))


def cmd_edit(args):
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        die("OPENAI_API_KEY is not set. Set it in Minis Environment Variables or pass --api-key.")
    if not os.path.exists(args.image):
        die("Input image not found: " + args.image)
    base_url = args.base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = args.model or os.environ.get("OPENAI_IMAGE_MODEL") or "gpt-image-2"
    url = endpoint_url(base_url, "/images/edits")
    fields = add_common_image_params({"model": model, "prompt": args.prompt}, args)
    status, raw = request_multipart(url, api_key, fields, {"image": args.image}, timeout=args.timeout)
    if status < 200 or status >= 300:
        die("HTTP %s from %s: %s" % (status, url, raw[:1200]))
    size, data = write_output_from_response(raw, args.output, api_key=api_key)
    print(json.dumps({
        "success": True,
        "mode": "openai_images_api_edit",
        "model": model,
        "path": args.output,
        "size": size,
        "revised_prompt": (data.get("data") or [{}])[0].get("revised_prompt", ""),
    }, ensure_ascii=False, indent=2))


def add_shared(ap):
    ap.add_argument("-o", "--output", default="/var/minis/attachments/openai_image.png")
    ap.add_argument("--model", help="default: env OPENAI_IMAGE_MODEL or gpt-image-2")
    ap.add_argument("--base-url", help="default: env OPENAI_BASE_URL or https://api.openai.com/v1")
    ap.add_argument("--api-key", help="API key; prefer OPENAI_API_KEY env to avoid shell history")
    ap.add_argument("--size", default="auto", help="auto, 1024x1024, 1536x1024, 1024x1536, etc.; use empty string to omit")
    ap.add_argument("--quality", default="auto", help="auto/low/medium/high/hd; use empty string to omit")
    ap.add_argument("--background", default=None, help="transparent/opaque/auto if supported")
    ap.add_argument("--output-format", default=None, help="png/jpeg/webp if supported")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--retries", type=int, default=2, help="retry transient gateway errors for JSON image generation")


def main():
    load_profile_env()
    parser = argparse.ArgumentParser(description="OpenAI-compatible gpt-image generation/editing")
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("gen", help="text to image")
    gen.add_argument("prompt")
    add_shared(gen)
    gen.set_defaults(func=cmd_gen)
    edit = sub.add_parser("edit", help="image edit")
    edit.add_argument("prompt")
    edit.add_argument("--image", required=True)
    add_shared(edit)
    edit.set_defaults(func=cmd_edit)
    args = parser.parse_args()
    if getattr(args, "size", None) == "":
        args.size = None
    if getattr(args, "quality", None) == "":
        args.quality = None
    args.func(args)


if __name__ == "__main__":
    main()
