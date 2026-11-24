"""Low-latency modifier-only channel. Carries no text or character events."""
import configparser
import json
import os
from pathlib import Path
import socket
import stat

import excluded


def request(path, message):
    with socket.socket(socket.AF_UNIX) as conn:
        conn.settimeout(0.3)
        conn.connect(str(path))
        conn.sendall(message.encode())
        data = bytearray()
        while piece := conn.recv(8192):
            data.extend(piece)
        return data


def switch(path, config):
    cfg = configparser.ConfigParser()
    cfg.read(config)
    if not all(cfg.getboolean("Switcher", k, fallback=True) for k in ("enabled","single")):
        return
    window = json.loads(request(path, "j/activewindow"))
    if not window or excluded.blocked(window):
        return
    keyboards = json.loads(request(path,"j/devices"))["keyboards"]
    main = next((k for k in keyboards if k.get("main")), None)
    if not main:
        return
    layout = main["layout"].split(",")
    if len(layout)<2:
        return
    index = (main["active_layout_index"]+1)%len(layout)
    if all(k["layout"]==main["layout"] for k in keyboards):
        request(path,f"/switchxkblayout all {index}")
    else:
        for k in keyboards:
            groups=k["layout"].split(",")
            if layout[index] in groups:
                request(path,f"/switchxkblayout {k['name']} {groups.index(layout[index])}")


def main():
    runtime=Path(os.environ["XDG_RUNTIME_DIR"])
    path=runtime/"hypr"/os.environ["HYPRLAND_INSTANCE_SIGNATURE"]/".socket.sock"
    fifo=runtime/"cajlatland-switcher.shift"
    config=excluded.location().with_name("switcher.ini")
    try:
        os.mkfifo(fifo,0o600)
    except FileExistsError:
        if not stat.S_ISFIFO(fifo.lstat().st_mode):
            raise
    fd=os.open(fifo,os.O_RDWR|os.O_NOFOLLOW)
    while True:
        for char in os.read(fd,64):
            if char==ord("s"):
                try:
                    switch(path,config)
                except (OSError,ValueError,KeyError,configparser.Error):
                    continue


if __name__=="__main__":
    main()
