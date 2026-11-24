#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
(( EUID != 0 )) || { echo 'Запустите установщик от обычного пользователя.' >&2; exit 1; }
if [[ ${1:-} != --no-packages ]]; then
    sudo pacman -S --needed rust gcc pkgconf wayland glib2 gtk4 python-gobject ibus hunspell-ru hunspell-en_us xorg-xwayland
fi
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
app="$HOME/.local/share/cajlatland-switcher"
build="${XDG_CACHE_HOME:-$HOME/.cache}/cajlatland-switcher/build"
mkdir -p "$app"
cp -R Cargo.toml Cargo.lock build.rs LICENSE README.md src dictionaries tests ./*.py build-method input-method.xml method.c switcher.ini "$app/"
cargo build --release --locked --offline --manifest-path "$app/Cargo.toml" --target-dir "$build"
bash "$app/build-method" "$build/wayland"
install -Dm755 integration/cajlatland-switcher "$HOME/.local/bin/cajlatland-switcher"
for unit in integration/*.service; do install -Dm644 "$unit" "$cfg/systemd/user/${unit##*/}"; done
install -Dm644 integration/switcher-shift.lua "$cfg/hypr/modules/switcher-shift.lua"
install -Dm644 integration/cajlatland-switcher.desktop "$HOME/.local/share/applications/cajlatland-switcher.desktop"
install -Dm644 integration/cajlatland-switcher.svg "$HOME/.local/share/icons/hicolor/scalable/apps/cajlatland-switcher.svg"
systemctl --user daemon-reload
if [[ -n ${WAYLAND_DISPLAY:-} && -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
    systemctl --user import-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE
    systemctl --user restart cajlatland-switcher.service
fi
echo 'Установлено. Подключите модуль Hyprland по инструкции в README.'
