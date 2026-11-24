<p align="center"><img src="integration/cajlatland-switcher.svg" width="96" alt="Cajlatland Switcher logo"></p>

<h1 align="center">Cajlatland Switcher</h1>

<p align="center">
  An offline Russian/English (<code>US</code> / <code>ЙЦУКЕН</code>) keyboard layout switcher and typo corrector for <strong>Hyprland</strong> on Arch Linux.
</p>

<p align="center">
  <a href="README.ru.md">Русская версия</a> ·
  <a href="#installation">Installation</a> ·
  <a href="#gestures">Gestures</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#cli-and-diagnostics">CLI & Diagnostics</a>
</p>

---

## Features

- **Automatic Wrong-Layout Correction** — typing `ghbdtn` followed by `Space` automatically turns into **привет** (and vice versa).
- **Offline Typo Correction** — fast local Rust engine with bilingual dictionaries (`en`, `ru`, and exceptions) requiring zero cloud access or external APIs.
- **Smart Shift Gestures** — tap `Shift` to switch layouts, double-tap `Shift` to convert the selected text or last typed word, press both `Shift` keys to pause/resume auto-switching.
- **Wayland & IBus Integration** — native Wayland input-method daemon (`method.c`) plus an IBus adapter (`ibus_engine.py`) for XWayland/GTK/Electron apps.
- **GTK4 Settings Window** — visual preferences editor (`cajlatland-switcher`), live input test box, and per-application exclusion toggles.
- **Built-in Safety** — password fields, terminals, and password managers are automatically protected from unintended replacement.

> [!NOTE]
> If you install the full [cajlatland](https://github.com/cajlat1kkk/cajlatland) desktop, Cajlatland Switcher is already bundled and preconfigured out of the box.

---

<h2 id="installation">Installation (Arch Linux / CachyOS)</h2>

### Requirements

- **Hyprland** with Lua configuration support (`hyprland-lua` / cajlatland setup)
- Keyboard layouts configured as `us,ru`
- `git`, `sudo`, and standard Arch repositories (`pacman`)

### Install

```bash
git clone https://github.com/cajlat1kkk/cajlatland-switcher.git
cd cajlatland-switcher
./install.sh
```

The installer will:
1. Install required dependencies via `pacman`: `rust`, `gcc`, `pkgconf`, `wayland`, `glib2`, `gtk4`, `python-gobject`, `ibus`, `hunspell-ru`, `hunspell-en_us`, `xorg-xwayland` (pass `--no-packages` to skip `pacman`).
2. Copy files to `~/.local/share/cajlatland-switcher/` and build the Rust release binary + Wayland helper cleanly offline.
3. Install the `cajlatland-switcher` command (`~/.local/bin/cajlatland-switcher`), desktop entry, icon, systemd user units, and Hyprland Shift module (`~/.config/hypr/modules/switcher-shift.lua`).

### Connect to Your Hyprland Config

Add the following once to `~/.config/hypr/hyprland.lua` and log back in:

```lua
require("modules.switcher-shift")

hl.on("hyprland.start", function()
    hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE && systemctl --user start cajlatland-switcher.service")
end)
```

### Update

```bash
cd cajlatland-switcher
git pull --ff-only && ./install.sh
```

---

<h2 id="gestures">Gestures</h2>

| Gesture | Action |
| --- | --- |
| **Tap `Shift`** (left or right) | Switch keyboard layout (`US` ↔ `RU`) |
| **Double-tap `Shift`** | Convert the selected text or last typed word |
| **Left `Shift` + Right `Shift`** | Pause or resume automatic layout correction |
| **Hold `Shift`** | Type uppercase letters or keybindings as usual |

---

<h2 id="configuration">Configuration & App Support</h2>

Open **Cajlatland Switcher** from your application launcher (or run `cajlatland-switcher gui`) to access:
- **Test Input**: type `ghbdtn` + `Space` to test instant conversion.
- **Excluded Applications**: view built-in protections (Visual Studio Code, terminals, password managers) or toggle exclusions per application. Saved to `~/.config/cajlatland-switcher/excluded-apps.json` and applied immediately without restarting the service.
- **Settings file**: `~/.config/cajlatland-switcher/switcher.ini`.

### Yandex Browser

```bash
python3 ~/.local/share/cajlatland-switcher/configure_yandex.py
```

Restart Yandex Browser completely from the application launcher to enable GTK/IBus support under XWayland.

### Visual Studio Code / Electron Apps (e.g., Codex extension)

1. Turn off the **Visual Studio Code** exclusion in **Cajlatland Switcher → Settings → Excluded Apps**.
2. Run:
   ```bash
   python3 ~/.local/share/cajlatland-switcher/configure_code.py
   ```
3. Fully close all VS Code windows and relaunch it from the application menu (for other Wayland Electron apps, `--enable-wayland-ime` may also be required).

---

<h2 id="cli-and-diagnostics">CLI, Diagnostics & Tests</h2>

### Standalone CLI

You can install only the Rust CLI binary with Cargo:

```bash
cargo install --locked --path .
printf 'Ghbdtn!' | cajlatland-switcher correct
```

Run `cajlatland-switcher --help` for all CLI flags.

### Service Status & Logs

```bash
systemctl --user status cajlatland-switcher.service
systemctl --user status cajlatland-switcher-ibus.service
journalctl --user -u cajlatland-switcher.service -n 50
```

### Running Tests & Lint

```bash
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
```

---

## License

MIT — see [LICENSE](LICENSE).
