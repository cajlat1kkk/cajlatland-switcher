import json
import subprocess
import sys
import excluded


def query(name):
    return json.loads(subprocess.check_output(["hyprctl", "-j", name], timeout=1))


def set_group(keyboards,target):
    for k in keyboards:
        groups=k.get("layout","").split(",")
        if target in groups and k.get("active_layout_index")!=groups.index(target):
            subprocess.run(["hyprctl","switchxkblayout",k["name"],str(groups.index(target))],
                           stdout=subprocess.DEVNULL,check=True,timeout=1)


def main():
    win=query("activewindow")
    if not win or excluded.blocked(win):
        return
    if sys.argv[1] == "permitted":
        print("yes",end="")
        return
    if sys.argv[1] == "next":
        keyboards=query("devices")["keyboards"]
        current=next((k for k in keyboards if k.get("main")),None)
        if current:
            groups=current["layout"].split(",")
            target=groups[(current.get("active_layout_index",0)+1)%len(groups)]
            set_group(keyboards,target)
        return
    app = win.get("class", "").casefold()
    if (not app or win.get("xwayland") or
            excluded.protected(app)):
        return
    address = win.get("address")
    if not address:
        return
    if sys.argv[1] == "check":
        print(address, end="")
    elif address == sys.argv[2]:
        set_group(query("devices")["keyboards"],sys.argv[1])


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError, subprocess.SubprocessError):
        sys.exit(1)
