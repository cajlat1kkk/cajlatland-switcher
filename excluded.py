"""User exclusions are exact, case-insensitive Hyprland window classes."""
import json
import os
import tempfile
from pathlib import Path


DEFAULTS = {"code": "Visual Studio Code", "code-insiders": "Visual Studio Code Insiders",
            "codium": "VSCodium", "jetbrains-*": "Среды JetBrains"}
PROTECTED = ("term", "kitty", "foot", "alacritty", "wezterm", "password", "keepass", "bitwarden", "pinentry")


def protected(identifier):
    return any(part in identifier.casefold() for part in PROTECTED)


def location():
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config"))/"cajlatland-switcher"/"excluded-apps.json"


def load():
    try:
        items = json.loads(location().read_text())
    except FileNotFoundError:
        return list(DEFAULTS)
    if isinstance(items, list):
        # Older versions kept built-in exclusions outside the user's list.
        if not all(isinstance(i, str) for i in items):
            raise ValueError("Invalid application list")
        items = list(dict.fromkeys([*DEFAULTS, *items]))
    elif isinstance(items, dict):
        items = items.get("applications")
    if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
        raise ValueError("Invalid application list")
    return items


def store(items):
    path = location()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as tmp:
        json.dump({"applications": sorted(items, key=str.casefold)}, tmp, ensure_ascii=False, indent=2)
    os.replace(tmp.name, path)


def blocked(window):
    identifiers = {window.get(k, "").casefold() for k in ("class", "initialClass")}
    rules = {item.casefold() for item in load()}
    return bool(identifiers & rules) or ("jetbrains-*" in rules and
        any(identifier.startswith("jetbrains-") for identifier in identifiers))
