#!/usr/bin/env python3
"""
codex-image: generate/edit images via /responses streaming only.
No /v1/images/generations and no minis-model-use image endpoint in the default path.
"""
import argparse
import base64
import json
import mimetypes
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_BASE_URL = "https://ai.input.im"
DEFAULT_MODEL = "gpt-5.4"
APP_MODEL_CACHE = None
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_KEY_ENV_ORDER = [
    "IMAGE2_API_KEY",
    "OPENAI_API_KEY",
    "INPUT_API_KEY",
    "CODEX_API_KEY",
]
PROMPT_PRESETS = {
    "character": "单人角色设定插画，全身像，面容清晰，服装与气质贴合原作氛围，干净背景，高细节。",
    "portrait": "单人肖像，面容清晰，构图稳定，电影感光影，高细节。",
    "scene": "场景概念图，主体明确，空间层次清晰，电影感光影，高细节。",
}


def load_profile_env():
    try:
        with open("/etc/profile", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("export ") or "=" not in line:
                    continue
                name, val = line[len("export "):].split("=", 1)
                name = name.strip()
                val = val.strip()
                if not name or name in os.environ:
                    continue
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                    val = val[1:-1]
                os.environ[name] = val
    except Exception:
        pass


def env_truthy(name):
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def current_app_model(default=DEFAULT_MODEL):
    """Best-effort use the model currently exposed by Minis app model list.

    The CLI does not expose a dedicated "current selected model" variable, so
    we follow the app-visible order from `minis-model-use list`: first model
    with image_output wins. IMAGE2_MODEL can still explicitly override this.
    """
    global APP_MODEL_CACHE
    if APP_MODEL_CACHE:
        return APP_MODEL_CACHE
    try:
        proc = subprocess.run(
            ["minis-model-use", "list"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        text = (proc.stdout or "").strip()
        if proc.returncode == 0 and text:
            data = json.loads(text)
            models = data.get("data", {}).get("models", [])
            for item in models:
                modalities = item.get("modalities") or []
                model_id = item.get("model_id")
                if model_id and "image_output" in modalities:
                    APP_MODEL_CACHE = model_id
                    return APP_MODEL_CACHE
            for item in models:
                model_id = item.get("model_id")
                if model_id:
                    APP_MODEL_CACHE = model_id
                    return APP_MODEL_CACHE
    except Exception:
        pass
    return default


def split_env_names(value):
    if not value:
        return []
    names = []
    for part in value.replace(",", " ").split():
        p = part.strip()
        if p:
            names.append(p)
    return names


def resolve_api_key(cli_env=None):
    env_names = []
    env_names.extend(split_env_names(cli_env))
    env_names.extend(split_env_names(os.environ.get("IMAGE2_API_KEY_ENV")))
    env_names.extend(DEFAULT_KEY_ENV_ORDER)
    seen = set()
    for name in env_names:
        if name in seen:
            continue
        seen.add(name)
        value = os.environ.get(name)
        if value:
            return value, name
    raise RuntimeError(
        "Missing API key for /responses streaming. Set IMAGE2_API_KEY, OPENAI_API_KEY, "
        "INPUT_API_KEY, CODEX_API_KEY, or set IMAGE2_API_KEY_ENV=<existing_env_name>."
    )


def responses_url(base_url=None):
    full = os.environ.get("IMAGE2_RESPONSES_URL")
    if full:
        return full.rstrip("/")
    base = (base_url or os.environ.get("IMAGE2_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    return base + "/responses"


def origin_from_url(url):
    p = urllib.parse.urlparse(url)
    if not p.scheme or not p.netloc:
        return DEFAULT_BASE_URL
    return f"{p.scheme}://{p.netloc}"


def sse_events(resp):
    event_type = None
    data_lines = []
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data_lines:
                yield event_type, "\n".join(data_lines)
            event_type = None
            data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_type = line[len("event:"):].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())
    if data_lines:
        yield event_type, "\n".join(data_lines)


def iter_sse_events_from_file(path):
    event_type = None
    data_lines = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.rstrip("\r\n")
            if not line:
                if data_lines:
                    yield event_type, "\n".join(data_lines)
                event_type = None
                data_lines = []
                continue
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                event_type = line[len("event:"):].strip()
                continue
            if line.startswith("data:"):
                data_lines.append(line[len("data:"):].lstrip())
    if data_lines:
        yield event_type, "\n".join(data_lines)


def write_debug_event(handle, event_type, data):
    handle.write(f"event: {event_type or ''}\n")
    for line in data.split("\n"):
        handle.write(f"data: {line}\n")
    handle.write("\n")


def looks_like_b64_image(text):
    if not isinstance(text, str):
        return False
    s = text.strip()
    if s.startswith("data:image"):
        return True
    return len(s) > 1000 and (s.startswith("iVBOR") or s.startswith("/9j/") or s.startswith("UklGR"))


def find_image_b64(obj):
    if isinstance(obj, dict):
        for key in ("partial_image_b64", "result", "b64_json", "image_base64", "base64"):
            val = obj.get(key)
            if looks_like_b64_image(val):
                return val
        if isinstance(obj.get("image_url"), dict):
            val = obj["image_url"].get("url")
            if looks_like_b64_image(val):
                return val
        for val in obj.values():
            found = find_image_b64(val)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_image_b64(item)
            if found:
                return found
    elif looks_like_b64_image(obj):
        return obj
    return None


def consume_events(events, debug_handle=None):
    image_b64 = None
    revised_prompt = None
    completion_error = None
    last_text = None

    for event_type, data in events:
        if debug_handle is not None:
            write_debug_event(debug_handle, event_type, data)
        if data.strip() == "[DONE]":
            break
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            continue

        found = find_image_b64(obj)
        if found:
            image_b64 = found
        if isinstance(obj, dict):
            revised_prompt = obj.get("revised_prompt") or revised_prompt
            if event_type in {"response.failed", "response.incomplete"}:
                completion_error = obj.get("error") or obj.get("response", {}).get("error") or obj
            elif event_type == "response.completed":
                completion_error = obj.get("response", {}).get("error") or completion_error
            txt = obj.get("text") or obj.get("output_text")
            if isinstance(txt, str) and txt.strip():
                last_text = txt.strip()

    return image_b64, revised_prompt, completion_error, last_text


def image_to_data_url(path):
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")
    mime, _ = mimetypes.guess_type(str(image_path))
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    with image_path.open("rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{image_b64}"


def build_input_content(prompt, input_image=None):
    preset_name = os.environ.get("IMAGE2_PROMPT_PRESET", "character").strip()
    preset = PROMPT_PRESETS.get(preset_name, "") if preset_name else ""
    final_prompt = prompt if not preset else (prompt.rstrip() + "。" + preset)
    if not input_image:
        return final_prompt
    return [
        {"type": "input_text", "text": final_prompt},
        {"type": "input_image", "image_url": image_to_data_url(input_image)},
    ]


def build_payload(prompt, model, input_image=None):
    payload = {
        "model": model,
        "input": [{"role": "user", "content": build_input_content(prompt, input_image)}],
        "store": False,
        "tools": [{"type": "image_generation"}],
        "tool_choice": "auto",
        "stream": True,
    }

    # Keep default payload lean. Do not add reasoning/include/parallel_tool_calls
    # or a per-request prompt_cache_key; those inflate token usage and can defeat
    # provider-side prompt caching. Add only when explicitly requested.
    instructions = os.environ.get("IMAGE2_INSTRUCTIONS", "").strip()
    if instructions:
        payload["instructions"] = instructions

    effort = os.environ.get("IMAGE2_REASONING_EFFORT", "").strip()
    if effort and effort.lower() not in {"0", "off", "none", "false"}:
        payload["reasoning"] = {"effort": effort}

    cache_key = os.environ.get("IMAGE2_PROMPT_CACHE_KEY", "").strip()
    if cache_key:
        payload["prompt_cache_key"] = cache_key

    return payload


def save_b64_image(image_b64, output_file):
    if image_b64.startswith("data:image"):
        image_b64 = image_b64.split(",", 1)[1]
    img = base64.b64decode(image_b64)
    with open(output_file, "wb") as f:
        f.write(img)
    return len(img)


def run_responses_stream(prompt, output_file, model, input_image=None, debug_log=None, api_key_env=None, base_url=None, show_payload=False):
    api_key, key_env = resolve_api_key(api_key_env)
    url = responses_url(base_url)
    origin = origin_from_url(url)
    payload = build_payload(prompt, model, input_image=input_image)

    if env_truthy("IMAGE2_DRY_RUN"):
        result = {
            "success": True,
            "dry_run": True,
            "backend": "responses-stream",
            "endpoint": url,
            "model": model,
            "api_key_env": key_env,
            "payload_keys": sorted(payload.keys()),
            "prompt_chars": len(prompt),
            "uses_images_generations": False,
        }
        if show_payload:
            result["payload"] = payload
        return result

    debug_handle = None
    if debug_log:
        Path(debug_log).parent.mkdir(parents=True, exist_ok=True)
        debug_handle = open(debug_log, "w", encoding="utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
                "OpenAI-Beta": "responses=experimental",
                "Accept": "text/event-stream",
                "User-Agent": os.environ.get("IMAGE2_USER_AGENT") or os.environ.get("INPUT_IM_USER_AGENT") or DEFAULT_USER_AGENT,
                "Origin": origin,
                "Referer": origin + "/",
            },
        )
        timeout = int(os.environ.get("IMAGE2_TIMEOUT", "900"))
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            image_b64, revised_prompt, completion_error, last_text = consume_events(
                sse_events(resp), debug_handle=debug_handle
            )

        if not image_b64:
            if completion_error:
                raise RuntimeError("responses stream error: " + json.dumps(completion_error, ensure_ascii=False)[:1200])
            if last_text:
                raise RuntimeError("model returned text instead of image: " + last_text[:1200])
            raise RuntimeError("Did not find image data in streamed /responses output")

        size = save_b64_image(image_b64, output_file)
        result = {
            "success": True,
            "path": output_file,
            "size": size,
            "backend": "responses-stream",
            "endpoint": url,
            "model": model,
            "api_key_env": key_env,
            "uses_images_generations": False,
        }
        if revised_prompt:
            result["revised_prompt"] = revised_prompt
        if debug_log:
            result["debug_log"] = debug_log
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:1200]}")
    finally:
        if debug_handle is not None:
            debug_handle.close()


def resolve_output_file(args):
    if args.output:
        return args.output
    ts = time.strftime("%Y%m%d_%H%M%S")
    return f"/var/minis/attachments/image2_{ts}.png"


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Generate/edit images via streaming /responses only")
    parser.add_argument("prompt", help="Prompt, or output file when --from-sse-log is used")
    parser.add_argument("output", nargs="?", help="Output image path")
    parser.add_argument("--input-image", help="Input image for image-to-image editing")
    parser.add_argument("--model", default=os.environ.get("IMAGE2_MODEL") or current_app_model())
    parser.add_argument("--base-url", default=os.environ.get("IMAGE2_BASE_URL"))
    parser.add_argument("--api-key-env", help="Read API key from this env var; also supports IMAGE2_API_KEY_ENV")
    parser.add_argument("--debug-log", "--debug-sse-log", dest="debug_log")
    parser.add_argument("--from-sse-log", help="Replay image extraction from an SSE debug log; no network/API key needed")
    parser.add_argument("--show-payload", action="store_true", help="Debug only: include request payload in dry-run output")
    return parser.parse_args(argv)


def main():
    load_profile_env()
    args = parse_args(sys.argv[1:])
    output_file = resolve_output_file(args)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    try:
        if args.from_sse_log:
            image_b64, revised_prompt, completion_error, last_text = consume_events(
                iter_sse_events_from_file(args.from_sse_log)
            )
            if not image_b64:
                msg = completion_error or last_text or "No image data in SSE log"
                raise RuntimeError(str(msg)[:1200])
            size = save_b64_image(image_b64, output_file)
            result = {
                "success": True,
                "path": output_file,
                "size": size,
                "backend": "responses-stream-log-replay",
                "uses_images_generations": False,
            }
            if revised_prompt:
                result["revised_prompt"] = revised_prompt
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.input_image and not Path(args.input_image).is_file():
            raise RuntimeError(f"Input image not found: {args.input_image}")

        result = run_responses_stream(
            args.prompt,
            output_file,
            model=args.model,
            input_image=args.input_image,
            debug_log=args.debug_log,
            api_key_env=args.api_key_env,
            base_url=args.base_url,
            show_payload=args.show_payload,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
