#!/usr/bin/env python3
"""Check every entry and write catalog/mods.json and catalog/textures.json.
--fetch also opens every homepage and source. FILE... checks only those files and writes nothing."""
import argparse
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
KINDS = {"codes", "builtin", "settings", "riivolution"}
CATEGORIES = {"widescreen", "framerate", "fix", "graphics", "controls", "gameplay", "cheat",
              "translation", "mod"}
SETTINGS = {
    "Video_Settings": {"wideScreenHack", "SuggestedAspectRatio", "AspectRatio",
                       "SafeTextureCacheColorSamples"},
    "Video_Hacks": None,
    "Video_Enhancements": {"ForceTextureFiltering", "DisableCopyFilter",
                           "ArbitraryMipmapDetection"},
    "Core": {"CPUThread", "SyncGPU", "FPRF", "MMU", "Overclock", "OverclockEnable"},
}
SOURCES = {"github_release": ["repo", "tag", "asset_pattern"],
           "github_repo_path": ["repo", "ref", "path"], "gamebanana": ["mod"],
           "gdrive": ["file_id"], "gdrive_folder": ["folder_id", "file_pattern"],
           "mega": ["link"], "https": ["url"], "link": []}
COMMON = {"id": str, "name": str, "title": str, "game_ids": list, "author": str, "licence": str,
          "homepage": str, "notes": str}
OPTIONAL = {"revisions", "author_url", "updated", "verified", "recommended", "version"}
MOD = {"kind", "category", "aspect", "settings", "code_type", "lines", "code_name", "source", "xml"}
TEX = {"source", "parts", "size", "sha256", "format", "layout", "textures", "downloads", "folder"}
HEX = re.compile(r"^[0-9A-Fa-f]{8} [0-9A-Fa-f]{8}$")
ONFRAME = re.compile(
    r"^0x[0-9A-Fa-f]{8}:(byte|word|dword):0x[0-9A-Fa-f]{1,8}(:0x[0-9A-Fa-f]{1,8})?$")
URL = re.compile(r"^https?://\S+$")


def check_source(source, bad):
    kind = source.get("type")
    if kind not in SOURCES:
        bad(f"source type {kind}")
        return
    for key in SOURCES[kind]:
        if key not in source:
            bad(f"source {kind} needs {key}")
    for key in ("url", "link"):
        if key in source and not source[key].startswith("https://"):
            bad(f"source {key} must be https")
    if ".." in str(source.get("path", "")):
        bad("source path")


def check(entry, textures, bad):
    for key, kind in COMMON.items():
        if not isinstance(entry.get(key), kind) or not entry[key]:
            bad(f"{key} is missing or not a {kind.__name__}")
            return
    for key in entry.keys() - COMMON.keys() - OPTIONAL - (TEX if textures else MOD):
        bad(f"unknown field {key}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", entry["id"]):
        bad("id must be [a-z0-9-]")
    for game in entry["game_ids"]:
        if not re.fullmatch(r"[A-Z0-9]{6}", game):
            bad(f"game ID {game}")
    if not URL.match(entry["homepage"]):
        bad("homepage is not an address")
    if entry.get("updated") and not re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", entry["updated"]):
        bad("updated must be YYYY-MM or YYYY-MM-DD")
    if len(entry["notes"]) > 300:
        bad("notes are over 300 characters")
    if len(entry["name"]) > 48:
        bad("name is over 48 characters")

    linked = (entry.get("source") or {}).get("type") == "link"
    if textures:
        for source in entry.get("parts") or [entry.get("source") or {}]:
            check_source(source, bad)
        if not linked and entry.get("format") not in ("zip", "7z", "rar"):
            bad("format must be zip, 7z or rar")
        if entry.get("layout", "single") not in ("single", "variants"):
            bad("layout")
        if not linked and entry.get("textures") not in ("png", "dds"):
            bad("textures must be png or dds")
        return

    kind = entry.get("kind")
    if kind not in KINDS:
        bad(f"kind {kind}")
        return
    if entry.get("category") not in CATEGORIES:
        bad(f"category {entry.get('category')}")
    for setting in entry.get("settings", []):
        allowed = SETTINGS.get(setting.get("section"), set())
        if allowed is not None and setting.get("key") not in allowed:
            bad(f"setting {setting.get('section')}/{setting.get('key')} is not allowed")
        if not isinstance(setting.get("value"), str):
            bad("a setting's value must be a string")
    if kind == "settings" and not entry.get("settings"):
        bad("no settings")
    if kind in ("codes", "builtin") and entry.get("code_type") not in ("gecko", "ar", "onframe"):
        bad("code_type")
    if kind == "codes":
        lines = entry.get("lines") or []
        if not lines:
            bad("no lines")
        for line in lines:
            if not (ONFRAME if entry.get("code_type") == "onframe" else HEX).match(line):
                bad(f"code line {line!r}")
    if kind == "builtin" and not entry.get("code_name"):
        bad("no code_name")
    if kind == "riivolution":
        check_source(entry.get("source") or {}, bad)
        if not linked and not entry.get("xml"):
            bad("no xml")
    if entry.get("category") == "widescreen" and entry.get("aspect") != "16:9":
        bad("a widescreen entry needs aspect 16:9")
    if entry.get("category") == "widescreen" and entry["game_ids"][0][0] == "G":
        if not any(x.get("key") in ("SuggestedAspectRatio", "AspectRatio") and x["value"] == "1"
                   for x in entry.get("settings", [])):
            bad("a GameCube widescreen entry needs SuggestedAspectRatio 1")


def address(source):
    kind = source.get("type")
    if kind == "github_release":
        return f"https://github.com/{source['repo']}/releases"
    if kind == "github_repo_path":
        return f"https://github.com/{source['repo']}"
    if kind == "gamebanana":
        return f"https://gamebanana.com/mods/{source['mod']}"
    if kind == "gdrive":
        return f"https://drive.google.com/file/d/{source['file_id']}/view"
    if kind == "gdrive_folder":
        return f"https://drive.google.com/drive/folders/{source['folder_id']}"
    if kind == "https":
        return source["url"]
    return None


def opens(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as reply:
            reply.read(400)
            return reply.status, ""
    except Exception as error:  # every failure is reported the same way
        return getattr(error, "code", None), str(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    errors, ids, count = [], set(), 0
    out = {"mods": [], "textures": []}
    files = [pathlib.Path(f).resolve() for f in args.files]
    for path in files or sorted(ROOT.glob("entries/*/*.json")):
        try:
            entries = json.loads(path.read_text())
        except ValueError as error:
            errors.append(f"{path.name}: {error}")
            continue
        for entry in entries:
            count += 1
            name = entry.get("id", "?")
            check(entry, path.parent.name == "textures",
                  lambda text, name=name: errors.append(f"{name}: {text}"))
            if name in ids:
                errors.append(f"{name}: used twice")
            ids.add(name)
            out[path.parent.name].append(entry)
            if not args.fetch:
                continue
            urls = [entry.get("homepage")]
            urls += [address(s) for s in entry.get("parts") or [entry.get("source") or {}]]
            for url in filter(None, urls):
                status, why = opens(url)
                if status != 200:
                    errors.append(f"{name}: {url} answered {status} {why[:80]}")

    for error in errors:
        print("ERROR", error)
    print(f"{count} entries, {len(errors)} errors")
    if errors:
        sys.exit(1)
    if not args.files:
        for kind, key in (("mods", "mods"), ("textures", "packs")):
            (ROOT / "catalog" / f"{kind}.json").write_text(
                json.dumps({"schema": 1, key: out[kind]}, indent=1, ensure_ascii=False) + "\n")


main()
