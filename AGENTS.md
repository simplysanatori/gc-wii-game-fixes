# AGENTS.md

Technical detail kept out of the README: how the repo is laid out and how a fix or an entry is added. The layout follows [3ds-game-fixes](https://github.com/simplysanatori/3ds-game-fixes) wherever the systems allow it.

## Layout

```
entries/mods/<game id>.json        mods, patches and cheats of one game (a list of entries)
entries/textures/<game id>.json    texture packs of one game (a list of entries)
catalog/mods.json                  built from entries/ by tools/build.py; what an app reads
catalog/textures.json              the same for texture packs
games/<game>-<region>/             our own fixes: README.md, AGENTS.md, the code file, images/
docs/USER_GUIDE.md                 how codes, mods and texture packs are installed
tools/build.py                     checks every entry and writes catalog/
```

- Folder names are lowercase, with the region last.
- A game is named by its 6-character game ID (`GFEE01`). An entry file is named after its first one.
- Texture packs and other people's mods are never in this repo: they are downloaded from their authors.

## An entry (both lists)

| Field | |
|---|---|
| `id` | `[a-z0-9-]`, unique |
| `name` | what the list shows: short, title case, no game name |
| `title` | the game's name |
| `game_ids` | every 6-character game ID it works on |
| `revisions` | optional: the disc revisions it works on (`[0]`). Codes nearly always need it |
| `author`, `author_url` | as the source credits them |
| `licence` | as stated by the author, else `Not stated` |
| `homepage` | the page the entry came from |
| `updated` | `YYYY-MM` or `YYYY-MM-DD` |
| `notes` | one or two short sentences: what it does, what it needs |
| `verified` | true only when tested here: booted, with before/after pictures of the same scene. Default false |
| `recommended` | the maintainer's pick. Default false |

## mods.json: `kind`

- `codes`: `code_type` (`gecko`, `ar` or `onframe`) and `lines`, the code as Dolphin's game INIs have it. Optional `settings`.
- `builtin`: a code Dolphin ships in its own game INI: `code_type` and `code_name`, exactly as there, without the `$` and the `[author]`.
- `settings`: only `settings`.
- `riivolution`: `source` (below) and `xml`, the path pattern of the Riivolution XML inside the download.

`category`: `widescreen`, `framerate`, `fix`, `graphics`, `controls`, `gameplay`, `cheat`, `translation`, `mod`.

`aspect`: `16:9` for anything that makes the picture wide. A GameCube widescreen code also needs `{"section": "Video_Settings", "key": "SuggestedAspectRatio", "value": "1"}` in `settings` (Force 16:9), or the picture stays 4:3.

`settings`: `{"section", "key", "value"}`. Allowed: `Video_Settings` (`wideScreenHack`, `SuggestedAspectRatio`, `AspectRatio`, `SafeTextureCacheColorSamples`), `Video_Hacks` (any key), `Video_Enhancements` (`ForceTextureFiltering`, `DisableCopyFilter`, `ArbitraryMipmapDetection`), `Core` (`CPUThread`, `SyncGPU`, `FPRF`, `MMU`, `Overclock`, `OverclockEnable`).

## textures.json

`source` or `parts` (a list, joined in order), `size` (bytes), `sha256` (optional), `format` (`zip`, `7z`, `rar`), `layout`: `single` (the folder that holds the textures, wrapper folders are dropped) or `variants` (its folders are choices), `textures` (`png` or `dds`), `downloads` (optional count).

## `source`

```
{"type": "github_release", "repo": "owner/name", "tag": "latest", "asset_pattern": "Name-*.zip"}
{"type": "github_repo_path", "repo": "owner/name", "ref": "main", "path": "dir/"}
{"type": "gamebanana", "mod": 12345, "file_pattern": "*.zip"}
{"type": "gdrive", "file_id": "..."}
{"type": "gdrive_folder", "folder_id": "...", "file_pattern": "*.zip"}
{"type": "mega", "link": "https://mega.nz/file/<handle>#<key>"}
{"type": "https", "url": "https://..."}
{"type": "link"}                     can only be opened in a browser (homepage)
```

## Rules

- Open every address before adding an entry. No guesses: no page, no entry.
- Codes: copied exactly, with their revision. Where the source gives none, `notes` say so.
- Other people's work: link to the author. A file is copied here only with the author's permission or a licence that allows it. Codes are credited.
- No game files, and nothing that carries a game's own data.

## How this was made

I started this project and used AI (Claude) to speed up development. I write, review and fix code by hand all the way through, keep the AI's work checked and reined in, and aim to keep the patches as lightweight as possible.
