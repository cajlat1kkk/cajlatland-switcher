"""IBus adapter for plain editable fields. No key history or clipboard access."""
import configparser
import os
from pathlib import Path
import re
import signal
from manual import convert
import subprocess
import sys
import time

import gi
gi.require_version("IBus", "1.0")
from gi.repository import GLib, IBus

import excluded
from app_scope import query, set_group

NAME = "cajlatland-switcher"
BASE = Path(excluded.__file__).parent
ENGINE = Path(os.environ.get("XDG_CACHE_HOME", Path.home()/".cache"))/"cajlatland-switcher/build/release/cajlatland-switcher"
PRIVATE = int(IBus.InputHints.PRIVATE | IBus.InputHints.HIDDEN_TEXT | IBus.InputHints.NO_SPELLCHECK)
def uses_preedit(ident):
    return ident.casefold() in {"code", "code-oss", "code-insiders", "vscodium", "codium"} or ident.casefold().startswith(("yandex-browser", "ru.yandex.desktop.browser"))


BOUNDARY = {ord(c):c for c in " !?:;,."}


class Switcher(IBus.Engine):
    __gtype_name__ = "CajlatlandSwitcherInputEngine"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trusted_client=False
        self.word=""
        self.browser=None

    def do_focus_in_id(self, object_path, client):
        # GTK's IBus module only sends SetContentType for non-default purposes.
        # Restrict the default case to toolkits that implement that contract.
        self.trusted_client=client.split(":",1)[0] in {"gtk3-im","gtk4-im","qt"}
        self.word=""
        self.browser=None
        if self.trusted_client:
            self.get_surrounding_text()

    def do_focus_out_id(self, object_path):
        self.trusted_client=False
        self.word=""
        self.browser=None

    def do_reset(self):
        self.word=""

    def preedit(self):
        self.update_preedit_text_with_mode(IBus.Text.new_from_string(self.word),len(self.word),bool(self.word),IBus.PreeditFocusMode.COMMIT)

    def flush(self):
        word=self.word
        self.word=""
        self.preedit()
        if word:self.commit_text(IBus.Text.new_from_string(word))

    def do_set_content_type(self,purpose,hints):
        if self.trusted_client and purpose in (IBus.InputPurpose.FREE_FORM,IBus.InputPurpose.ALPHA) and not hints & PRIVATE:
            self.get_surrounding_text()

    def do_process_key_event(self, key, code, modifiers):
        purpose,hints=self.get_content_type()
        if not self.trusted_client or modifiers & IBus.ModifierType.RELEASE_MASK:
            return False
        if purpose not in (IBus.InputPurpose.FREE_FORM,IBus.InputPurpose.ALPHA) or hints & PRIVATE:
            self.word=""
            return False
        shortcut=modifiers & (IBus.ModifierType.CONTROL_MASK|IBus.ModifierType.MOD1_MASK|IBus.ModifierType.SUPER_MASK)
        if self.browser is None:
            try:
                window=query("activewindow")
                ident=window.get("class","")
                if not ident or excluded.blocked(window) or excluded.protected(ident):
                    return False
                self.browser=uses_preedit(ident)
            except (OSError,ValueError,subprocess.SubprocessError):
                return False
        if self.browser:
            if key in (IBus.KEY_Shift_L,IBus.KEY_Shift_R):return False
            char=IBus.keyval_to_unicode(key)
            if not shortcut and char and re.fullmatch("[a-zA-Zа-яА-ЯёЁ]",char) and len(self.word)<64:
                if not self.word:
                    try:
                        current=query("activewindow")
                        if excluded.blocked(current) or not uses_preedit(current.get("class","")):
                            return False
                    except (OSError,ValueError,subprocess.SubprocessError):
                        return False
                self.word+=char;self.preedit();return True
            if key==IBus.KEY_BackSpace and self.word and not shortcut:
                self.word=self.word[:-1];self.preedit();return True
            if shortcut or key not in BOUNDARY:
                if self.word:self.flush()
                return False
            if not self.word:return False
        if shortcut or key not in BOUNDARY:return False
        try:
            handled=self.correct_boundary(key)
        except (OSError,KeyError,ValueError,GLib.Error,subprocess.SubprocessError,configparser.Error):
            handled=False
        if not handled and self.word:self.flush()
        return handled

    def manual_switch(self):
        purpose,hints=self.get_content_type()
        if not self.trusted_client or purpose not in (IBus.InputPurpose.FREE_FORM,IBus.InputPurpose.ALPHA) or hints & PRIVATE:
            return
        cfg=configparser.ConfigParser()
        cfg.read(excluded.location().with_name("switcher.ini"))
        if not all(cfg.getboolean("Switcher", key, fallback=True) for key in ("enabled","double")):
            return
        window=query("activewindow")
        ident=window.get("class","")
        if not ident or excluded.blocked(window) or excluded.protected(ident):
            return
        selection=""
        if ident.casefold() in {"code","code-oss","code-insiders","vscodium","codium"}:
            selection=subprocess.run(
                [sys.executable, BASE/"selected_text.py", str(window["pid"])],
                capture_output=True, text=True, timeout=2,
            ).stdout
        if selection:
            if query("activewindow").get("address")!=window.get("address"):
                return
            converted=convert(selection)
            if selection==converted:
                return
            self.word=""
            self.commit_text(IBus.Text.new_from_string(converted))
        elif self.word:
            converted=convert(self.word)
            self.word=converted
            self.flush()
        else:
            context,cursor,anchor=self.get_surrounding_text()
            if not context:
                return
            text=context.get_text()
            start,end=sorted((cursor,anchor))
            if start==end:
                match=re.search(r"[^\s]+[ \t]*$",text[:cursor])
                if not match:
                    return
                start=match.start()
            original=text[start:end]
            if not original or len(original)>2000:
                return
            converted=convert(original)
            if converted==original:
                return
            if cursor==anchor:
                self.delete_surrounding_text(start-cursor,end-start)
            self.commit_text(IBus.Text.new_from_string(converted))
        letter=next((ch for ch in converted if ch.isalpha()),None)
        if letter and query("activewindow").get("address")==window.get("address"):
            set_group(query("devices")["keyboards"],"us" if letter.isascii() else "ru")

    def correct_boundary(self,key):
        try:
            window = query("activewindow")
            ident = window.get("class","")
            if not ident or excluded.blocked(window) or excluded.protected(ident):
                return False
            cfg = configparser.ConfigParser()
            cfg.read(excluded.location().with_name("switcher.ini"))
            if not cfg.getboolean("Switcher","enabled",fallback=False):
                return False
            layout = cfg.getboolean("Switcher","layout",fallback=True) and not (Path(os.environ["XDG_RUNTIME_DIR"])/"cajlatland-switcher.paused").exists()
            typos = cfg.getboolean("Switcher","typos",fallback=True)
            if not (layout or typos):
                return False
            context,cursor,anchor = self.get_surrounding_text()
            if not self.word and (cursor!=anchor or not context):
                return False
            prefix=self.word or context.get_text()[max(0,cursor-72):cursor]
            match=re.search(r"(?:^|\s)([A-Za-zА-Яа-яЁё]{3,64})$",prefix)
            if not match:
                return False
            word=match[1]
            flags=[] if layout and typos else ["--no-layout" if typos else "--no-typos"]
            out=subprocess.run([ENGINE,"correct",*flags],input=word,text=True,capture_output=True,check=True,timeout=.3).stdout
            if not out or out==word:
                return False
            if subprocess.run([sys.executable,BASE/"learning.py","check"],input=word,text=True,
                              capture_output=True,timeout=.4).stdout!="ok":
                return False
            if query("activewindow").get("address")!=window.get("address"):
                return False
            if self.word:
                self.word="";self.preedit()
            else:
                self.delete_surrounding_text(-len(word),len(word))
            self.commit_text(IBus.Text.new_from_string(out+BOUNDARY[key]))
            if layout and word[0].isascii()!=out[0].isascii():
                try:
                    set_group(query("devices")["keyboards"],"us" if out[0].isascii() else "ru")
                except (OSError,ValueError,subprocess.SubprocessError):
                    pass  # The text transaction has already committed.

            return True
        except (OSError,KeyError,ValueError,GLib.Error,subprocess.SubprocessError,configparser.Error):
            return False


def main():
    IBus.init()
    if subprocess.run(["ibus","list-engine"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
        subprocess.run(["ibus-daemon","--daemonize","--panel=disable","--emoji-extension=disable","--config=disable"],check=True,timeout=6)
        for _ in range(20):
            if not subprocess.run(["ibus","list-engine"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
                break
            time.sleep(.1)
    bus=IBus.Bus()
    if not bus.is_connected():
        return 1
    registry=IBus.Component.new("org.cajlatland.Switcher.Input","Cajlatland Switcher","0.1","MIT","cajlat1kk","","","")
    registry.add_engine(IBus.EngineDesc.new(NAME,"Cajlatland Switcher","Local layout correction","en","MIT","cajlat1kk","cajlatland-switcher","default"))
    factory=IBus.Factory.new(bus.get_connection())
    engines=[]
    serial=0
    def create_engine(factory,name):
        nonlocal serial
        if name!=NAME:
            return None
        serial+=1
        engine=Switcher(engine_name=NAME,object_path=f"/org/cajlatland/Input/{serial}",connection=bus.get_connection(),has_focus_id=True,active_surrounding_text=True)
        engines.append(engine)
        engine.connect("destroy",lambda obj:engines.remove(obj) if obj in engines else None)
        return engine
    factory.connect("create-engine",create_engine)
    prev=bus.get_global_engine()
    if not bus.register_component(registry):
        return 1
    if prev is None or prev.get_name().startswith("xkb:") or prev.get_name()==NAME:
        subprocess.Popen(["ibus","engine",NAME],stdout=subprocess.DEVNULL)
    loop=GLib.MainLoop()
    bus.connect("disconnected",lambda *_:loop.quit())
    def manual_request():
        for engine in reversed(engines):
            if engine.trusted_client:
                try:
                    engine.manual_switch()
                except (OSError,ValueError,KeyError,GLib.Error,subprocess.SubprocessError,configparser.Error):
                    pass
                break
        return GLib.SOURCE_CONTINUE
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGUSR1,manual_request)
    loop.run()

if __name__=="__main__":
    sys.exit(main())
