"""Set up VS Code's local launchers for the GTK/IBus input method."""
import os
from pathlib import Path
import tempfile


def install():
    data = Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))
    for name in ("code.desktop", "code-url-handler.desktop"):
        vendor = Path("/usr/share/applications")/name
        if not vendor.is_file():
            continue
        target = data/"applications"/name
        original = (target if target.exists() else vendor).read_text()
        lines = []
        for line in original.splitlines(keepends=True):
            previous = "Exec=/usr/bin/env GTK_IM_MODULE=ibus "
            prefix = "Exec=/usr/bin/env -u NO_AT_BRIDGE ACCESSIBILITY_ENABLED=1 GTK_IM_MODULE=ibus "
            if line.startswith(previous):
                line = prefix + line[len(previous):].replace("--ozone-platform=x11 ", "--force-renderer-accessibility --ozone-platform=x11 ", 1)
            elif line.startswith("Exec="):
                parts = line[5:].split(maxsplit=1)
                if parts and parts[0] in ("code", "/usr/bin/code"):
                    args = parts[1].rstrip("\n") if len(parts)>1 else ""
                    line = (f"{prefix}{parts[0]} --force-renderer-accessibility "
                            f"--ozone-platform=x11 --gtk-version=4 --disable-wayland-ime {args}\n")
            lines.append(line)
        updated = "".join(lines)
        if updated != original:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False) as f:
                f.write(updated)
            os.chmod(f.name, 0o644)
            os.replace(f.name, target)


if __name__ == "__main__":
    install()
