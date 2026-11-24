"""Opt installed Yandex launchers into the verified GTK/IBus path."""
from pathlib import Path
import os
import re
import tempfile


def install():
    data = Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))/"applications"
    for name in ("ru.yandex.desktop.browser.desktop","yandex-browser.desktop"):
        vendor=Path("/usr/share/applications")/name
        dest=data/name
        if not vendor.is_file():
            continue
        original=(dest if dest.exists() else vendor).read_text()
        updated=re.sub(r"(?m)^Exec=(/usr/bin/yandex-browser(?:-stable)?)(?= |$)",
                       r"Exec=/usr/bin/env GTK_IM_MODULE=ibus \1 --ozone-platform=x11 --gtk-version=4 --disable-wayland-ime",
                       original)
        # The vendor's hidden alias ships with the same NoDisplay key twice.
        if name=="ru.yandex.desktop.browser.desktop" and updated.count("\nNoDisplay=true\n")==2:
            updated=updated.replace("\nNoDisplay=true\n","\n",1)
        if updated==original:
            continue
        data.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile("w",dir=data,delete=False) as tmp:
            tmp.write(updated)
        os.chmod(tmp.name,0o644)
        os.replace(tmp.name,dest)

if __name__=="__main__":
    install()
