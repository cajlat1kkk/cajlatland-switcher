<p align="center"><img src="integration/cajlatland-switcher.svg" width="96" alt="Логотип Cajlatland Switcher"></p>

<h1 align="center">Cajlatland Switcher</h1>

<p align="center">
  Локальное переключение раскладки (<code>US</code> / <code>ЙЦУКЕН</code>) и исправление опечаток для <strong>Hyprland</strong> на Arch Linux.
</p>

<p align="center">
  <a href="README.md">English version</a> ·
  <a href="#installation">Установка</a> ·
  <a href="#gestures">Жесты</a> ·
  <a href="#configuration">Настройка</a> ·
  <a href="#cli-and-diagnostics">CLI и диагностика</a>
</p>

---

## Возможности

- **Автоисправление раскладки** — ввод `ghbdtn` + `Пробел` автоматически превращается в **привет** (и наоборот).
- **Локальная коррекция опечаток** — быстрый Rust-движок со словарями (`en`, `ru`, исключения), работающий полностью офлайн без обращения к сети.
- **Умные жесты Shift** — короткое нажатие `Shift` переключает раскладку, двойное нажатие преобразует выделенный текст или последнее слово, одновременное нажатие левого и правого `Shift` ставит автопереключение на паузу.
- **Поддержка Wayland и IBus** — нативный метод ввода Wayland (`method.c`) и IBus-адаптер (`ibus_engine.py`) для приложений GTK/XWayland/Electron.
- **Окно настроек на GTK4** — проверка ввода, управление параметрами и гибкий список приложений-исключений.
- **Встроенная безопасность** — поля ввода паролей, терминалы и менеджеры паролей защищены от автозамены по умолчанию.

> [!NOTE]
> Полная сборка рабочего стола [cajlatland](https://github.com/cajlat1kkk/cajlatland) уже включает Cajlatland Switcher из коробки.

---

<h2 id="installation">Установка на Arch Linux / CachyOS</h2>

### Требования

- **Hyprland** с поддержкой конфигурации на Lua
- Раскладки клавиатуры `us,ru`
- `git`, `sudo` и доступ к стандартным репозиториям `pacman`

### Установка

```bash
git clone https://github.com/cajlat1kkk/cajlatland-switcher.git
cd cajlatland-switcher
./install.sh
```

Установщик автоматически:
1. Установит зависимости через `pacman`: `rust`, `gcc`, `pkgconf`, `wayland`, `glib2`, `gtk4`, `python-gobject`, `ibus`, `hunspell-ru`, `hunspell-en_us`, `xorg-xwayland` (флаг `--no-packages` позволяет пропустить шаг `pacman`).
2. Скопирует файлы в `~/.local/share/cajlatland-switcher/` и соберёт release-бинарник Rust и Wayland-модуль.
3. Установит команду `cajlatland-switcher` (`~/.local/bin/cajlatland-switcher`), ярлык меню приложений, иконку, user-службы systemd и модуль для Hyprland (`~/.config/hypr/modules/switcher-shift.lua`).

### Подключение в Hyprland

Добавьте в `~/.config/hypr/hyprland.lua` один раз и перезайдите в сеанс:

```lua
require("modules.switcher-shift")

hl.on("hyprland.start", function()
    hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE && systemctl --user start cajlatland-switcher.service")
end)
```

### Обновление

```bash
cd cajlatland-switcher
git pull --ff-only && ./install.sh
```

---

<h2 id="gestures">Жесты</h2>

| Жест | Действие |
| --- | --- |
| **Коротко нажать `Shift`** | Сменить раскладку (`US` ↔ `RU`) |
| **Дважды нажать `Shift`** | Преобразовать выделение или последнее слово |
| **Левый `Shift` + Правый `Shift`** | Приостановить или возобновить автопереключение |
| **Удерживать `Shift`** | Обычный ввод заглавных букв и сочетаний клавиш |

---

<h2 id="configuration">Настройка и поддержка приложений</h2>

Откройте **Cajlatland Switcher** из меню приложений (или выполните `cajlatland-switcher gui`):
- **Проверить ввод**: введите `ghbdtn` и нажмите `Пробел` для проверки работы.
- **Приложения-исключения**: настройка списка исключений (Visual Studio Code исключён по умолчанию; терминалы и менеджеры паролей защищены отдельным неактивным переключателем). Список сохраняется в `~/.config/cajlatland-switcher/excluded-apps.json` и применяется без перезапуска службы.
- **Конфиг параметров**: `~/.config/cajlatland-switcher/switcher.ini`.

### Яндекс Браузер

```bash
python3 ~/.local/share/cajlatland-switcher/configure_yandex.py
```

После выполнения полностью закройте браузер и откройте его заново из меню приложений.

### Visual Studio Code и расширение Codex

1. Выключите исключение **Visual Studio Code** в **Cajlatland Switcher → Настройки → Приложения-исключения**.
2. Выполните:
   ```bash
   python3 ~/.local/share/cajlatland-switcher/configure_code.py
   ```
3. Полностью закройте все окна VS Code и запустите его из меню приложений.

---

<h2 id="cli-and-diagnostics">CLI, диагностика и тесты</h2>

### Отдельный CLI

Можно собрать и установить только CLI-движок через Cargo:

```bash
cargo install --locked --path .
printf 'Ghbdtn!' | cajlatland-switcher correct
```

Справка по опциям: `cajlatland-switcher --help`.

### Состояние служб

```bash
systemctl --user status cajlatland-switcher.service
systemctl --user status cajlatland-switcher-ibus.service
journalctl --user -u cajlatland-switcher.service -n 50
```

### Тесты и проверки

```bash
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
```

---

## Лицензия

MIT — подробнее в [LICENSE](LICENSE).
