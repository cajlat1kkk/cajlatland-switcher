"""Controls for the Cajlatland Wayland input method."""
import configparser
import os
import subprocess
import tempfile
from pathlib import Path

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, GLib, Gdk, Gio

unit = "cajlatland-switcher.service"
path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config"))/"cajlatland-switcher"/"switcher.ini"


def preferences():
    cfg = configparser.ConfigParser()
    try:
        cfg.read(path)
        return {k:cfg.getboolean("Switcher", k, fallback=True) for k in ("enabled", "layout", "typos","single","double","chord")}
    except (ValueError, configparser.Error):
        return dict(enabled=False, layout=True, typos=True,single=True,double=True,chord=True)


def save(values):
    cfg = configparser.ConfigParser()
    cfg["Switcher"] = {key:str(value).lower() for key,value in values.items()}
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as f:
        cfg.write(f, space_around_delimiters=False)
    os.replace(f.name,path)


def active():
    return subprocess.run(["systemctl","--user","is-active","--quiet",unit]).returncode == 0


import json
import tomllib
import excluded

REPO = "https://github.com/cajlat1kkk/cajlatland-switcher"
try:
    with Path(__file__).with_name("Cargo.toml").open("rb") as manifest:
        VERSION = tomllib.load(manifest)["package"]["version"]
except FileNotFoundError:
    VERSION = "0.1.0"

CSS = b"""
.switcher {background: #fff; color:#262b28;}
headerbar.banner {background:#106b57; color:#e0f5ef; box-shadow:none; border:0;}
.banner button {background:transparent;color:#e0f5ef;box-shadow:none;}
.wordmark {background:#106b57;color:#e0f5ef;font-size:29px;font-weight:400;
           letter-spacing:2px;padding:8px 4px 30px;}
.switcher button {border-radius:9px;}
.switcher .tile {background:transparent;color:#323831;box-shadow:none;border:0;padding:16px 5px;}
.switcher .tile:hover {background:#f4f6f2;}
.tile image {color:#667369;}
.tile.on image {color:#168342;}
.switcher .footer {background:#f6f7f4;color:#455148;padding:8px 18px;}
.switcher .footer button, .switcher .back {background:transparent;color:#25573b;box-shadow:none;border:0;}
.switcher .page-title {font-size:20px;font-weight:600;}
.switcher .hint {color:#535e56;}
.switcher entry, .switcher textview, .switcher textview text {background:#f6f7f4;color:#202922;caret-color:#135d35;}
.switcher .test-box {border:1px solid #c1cbc3;border-radius:8px;}
.switcher .form-row {padding:5px 0;}
.switcher .list {background:#f6f7f4;color:#273429;border-radius:8px;}
.switcher link {color:#146a3b;}
"""


def label(text, cls=None):
    return Gtk.Label(label=text, xalign=0, wrap=True, css_classes=[cls] if cls else [])


def pad(widget, amount):
    for edge in ("top", "bottom", "start", "end"):
        getattr(widget, "set_margin_"+edge)(amount)


def show(app):
    if app.get_active_window():
        app.get_active_window().present()
        return
    values=preferences()
    win=Gtk.ApplicationWindow(application=app, title="Cajlatland Switcher")
    win.set_icon_name("cajlatland-switcher")
    win.set_default_size(620,480)
    css=Gtk.CssProvider()
    css.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    header=Gtk.HeaderBar(css_classes=["banner"])
    header.set_title_widget(Gtk.Box())
    win.set_titlebar(header)
    shell=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,css_classes=["switcher"])
    win.set_child(shell)
    shell.append(Gtk.Label(label="CAJLATLAND SWITCHER",css_classes=["wordmark"]))
    pages=Gtk.Stack(vexpand=True,hhomogeneous=False,vhomogeneous=False,
                    transition_type=Gtk.StackTransitionType.CROSSFADE)
    shell.append(pages)

    def page(name, title=None):
        content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        pad(content,22)
        scroll=Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.set_child(content)
        pages.add_named(scroll,name)
        if title:
            row=Gtk.Box(spacing=10)
            back=Gtk.Button(icon_name="go-previous-symbolic",tooltip_text="На главную",css_classes=["back"])
            back.connect("clicked",lambda *_:pages.set_visible_child_name("home"))
            row.append(back)
            row.append(label(title,"page-title"))
            content.append(row)
        return content

    home=page("home")
    tiles=Gtk.Box(spacing=8,homogeneous=True)
    home.append(tiles)
    def tile(title,icon,callback):
        button=Gtk.Button(css_classes=["tile"])
        col=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        col.append(Gtk.Image(icon_name=icon,pixel_size=42))
        col.append(Gtk.Label(label=title,wrap=True,justify=Gtk.Justification.CENTER))
        button.set_child(col)
        button.connect("clicked",callback)
        tiles.append(button)
        return button

    def power(*_):
        values["enabled"]=not active()
        save(values)
        subprocess.run(["systemctl","--user","restart" if values["enabled"] else "stop",unit])
        refresh()

    master=tile("Автокоррекция","emblem-ok-symbolic",power)
    tile("Проверить ввод","input-keyboard-symbolic",lambda *_:open_test())
    tile("Настройки","preferences-system-symbolic",lambda *_:open_settings())
    home.append(Gtk.Separator())
    home.append(label("Один Shift меняет раскладку. Удерживай Shift для ввода заглавных букв.","hint"))
    home.append(label("Дважды нажми Shift, чтобы преобразовать последнее слово или выделенный текст.","hint"))

    test=page("test","Проверить ввод")
    test.append(label("В английской раскладке набери ghbdtn и нажми пробел. При включённой коррекции получится «привет».","hint"))
    field=Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR,left_margin=12,right_margin=12,top_margin=10,bottom_margin=10)
    sc=Gtk.ScrolledWindow(min_content_height=90,css_classes=["test-box"])
    sc.set_child(field)
    test.append(sc)
    clear=Gtk.Button(label="Очистить",halign=Gtk.Align.END)
    clear.connect("clicked",lambda *_:field.get_buffer().set_text(""))
    test.append(clear)
    def open_test():
        pages.set_visible_child_name("test")
        field.grab_focus()

    settings=page("settings","Настройки")
    for key,title in (("layout","Исправлять раскладку"),("typos","Исправлять опечатки"),("single","Один Shift — смена раскладки"),
                      ("double","Двойной Shift — преобразование текста"),("chord","Оба Shift — пауза автопереключения")):
        row=Gtk.Box(spacing=10,css_classes=["form-row"])
        caption=label(title);caption.set_hexpand(True);row.append(caption)
        switch=Gtk.Switch(active=values[key],valign=Gtk.Align.CENTER)
        def change(widget,_property,key=key):
            values[key]=widget.get_active()
            save(values)
        switch.connect("notify::active",change)
        row.append(switch);settings.append(row)
    manage=Gtk.Button(label="Приложения-исключения")
    settings.append(manage)
    def open_settings():
        pages.set_visible_child_name("settings")

    exceptions=page("exceptions","Приложения-исключения")
    exceptions.append(label("Найди приложение по названию или добавь класс окна Hyprland.","hint"))
    entry=Gtk.SearchEntry(placeholder_text="Поиск приложений")
    exceptions.append(entry)
    notice=label("Включённый переключатель исключает приложение из коррекции.","hint")
    exceptions.append(notice)
    listing=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3)
    exceptions.append(listing)
    catalog={}
    def search(*_):
        while child:=listing.get_first_child():
            listing.remove(child)
        try:
            items=excluded.load()
        except (OSError,ValueError):
            notice.set_text("Не удалось прочитать исключения.")
            return
        enabled={k.casefold() for k in items}
        names={**{k.casefold():k for k in items},**catalog}
        term=entry.get_text().strip().casefold()
        matches=[(key,name) for key,name in names.items() if term in (key+" "+name).casefold()]
        if not matches and term and not any(c.isspace() for c in term):
            matches=[(term,term)]
        for key,name in sorted(matches,key=lambda pair:pair[1].casefold()):
            locked=excluded.protected(key) or (key!="jetbrains-*" and key.startswith("jetbrains-") and "jetbrains-*" in enabled)
            line=Gtk.Box(spacing=8,css_classes=["form-row"])
            caption=label(name);caption.set_hexpand(True);line.append(caption)
            switch=Gtk.Switch(active=locked or key in enabled,sensitive=not locked,valign=Gtk.Align.CENTER)
            switch.set_tooltip_text("Защищено отдельным правилом" if locked else "Исключить "+name)
            def toggle(widget,_prop,value=key):
                try:
                    saved=[i for i in excluded.load() if i.casefold()!=value]
                    if widget.get_active():saved.append(value)
                    excluded.store(saved)
                    if value=="jetbrains-*":GLib.idle_add(search)
                except (OSError,ValueError):
                    notice.set_text("Не удалось сохранить исключение.");GLib.idle_add(search)
            switch.connect("notify::active",toggle)
            line.append(switch);listing.append(line)
    entry.connect("search-changed",search)
    def open_exceptions(*_):
        catalog.clear()
        for item in Gio.AppInfo.get_all():
            if item.get_nodisplay():continue
            ident=item.get_id()
            if not ident:continue
            wm=getattr(item,"get_startup_wm_class",lambda:None)()
            catalog[(wm or ident.removesuffix(".desktop")).casefold()]=item.get_display_name()
        catalog.update(excluded.DEFAULTS)
        try:
            clients=json.loads(subprocess.check_output(["hyprctl","-j","clients"],timeout=1))
            for w in clients:
                if w.get("class"):catalog.setdefault(w["class"].casefold(),w["class"])
        except (ValueError,OSError,subprocess.SubprocessError):pass
        pages.set_visible_child_name("exceptions")
        entry.set_text("");notice.set_text("")
        try:search()
        except (ValueError,OSError):notice.set_text("Не удалось прочитать список исключений.")
        entry.grab_focus()
    manage.connect("clicked",open_exceptions)

    about=page("about","О программе")
    about.append(label("Cajlatland Switcher · "+VERSION,"heading"))
    about.append(label("Автор — cajlat1kk. Он собирает cajlatland — русскоязычное окружение Hyprland для Arch Linux. Switcher входит в эту сборку и локально исправляет раскладку и опечатки."))
    about.append(label("В репозитории cajlatland опубликованы конфигурация рабочего стола, скрипты установки и инструкции по сборке."))
    for name,url in (("Репозиторий Switcher",REPO),("GitHub · @cajlat1kkk","https://github.com/cajlat1kkk"),("VK · ilyshalaev","https://vk.ru/ilyshalaev"),("Telegram · @IlyShalaev","https://t.me/IlyShalaev")):
        about.append(Gtk.LinkButton(uri=url,label=name,halign=Gtk.Align.START))
    footer=Gtk.Box(spacing=10,css_classes=["footer"])
    shell.append(footer)
    footer.append(label("v"+VERSION))
    state=Gtk.Label(hexpand=True,xalign=0)
    footer.append(state)
    info=Gtk.Button(label="О программе")
    info.connect("clicked",lambda *_:pages.set_visible_child_name("about"))
    footer.append(info)
    def refresh():
        running=active()
        paused=(Path(GLib.get_user_runtime_dir())/"cajlatland-switcher.paused").exists()
        state.set_text(("На паузе" if paused else "Включено") if running else "Выключено")
        if running and not paused:master.add_css_class("on")
        else:master.remove_css_class("on")
        return True
    refresh()
    timer=GLib.timeout_add_seconds(4,refresh)
    win.connect("close-request",lambda *_:(GLib.source_remove(timer),False)[1])
    pages.set_visible_child_name("home")
    win.present()


if __name__=="__main__":
    app=Gtk.Application(application_id="org.cajlatland.Switcher")
    app.connect("activate",show)
    app.run([])
