<p align="center"><img src="integration/cajlatland-switcher.svg" width="96" alt="Логотип Cajlatland Switcher"></p>

# Cajlatland Switcher

Локальное переключение раскладки US/ЙЦУКЕН и исправление опечаток в Hyprland. Rust-движок работает с пользовательским методом ввода Wayland, а GTK-окно управляет настройками.

## Установка на Arch Linux

Нужны Git, Hyprland с конфигурацией на Lua, раскладки `us,ru` и право использовать sudo. Полная сборка [Cajlatland](https://github.com/cajlat1kkk/cajlatland) уже включает приложение.

```bash
git clone https://github.com/cajlat1kkk/cajlatland-switcher.git && cd cajlatland-switcher && ./install.sh
```

Установщик скачивает зависимости и словари через pacman, собирает приложение и добавляет его в меню. В собственной конфигурации добавь в `~/.config/hypr/hyprland.lua` один раз и перезайди в сеанс:

```lua
require("modules.switcher-shift")
hl.on("hyprland.start", function()
    hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE && systemctl --user start cajlatland-switcher.service")
end)
```

Для Яндекс Браузера выполни `python3 ~/.local/share/cajlatland-switcher/configure_yandex.py`, полностью закрой браузер и открой его из меню. Для обновления выполни `git pull --ff-only && ./install.sh` в каталоге репозитория.

## Проверка и настройки

Открой **Cajlatland Switcher → Проверить ввод**, набери `ghbdtn` и нажми пробел. Короткий Shift меняет раскладку. Двойной Shift преобразует выделение или последнее слово. Оба Shift вместе ставят автопереключение на паузу. Удержанный Shift работает как модификатор.

В **Настройки → Приложения-исключения** видны встроенные и добавленные вручную исключения. Visual Studio Code исключён по умолчанию. Поиск находит установленные приложения по имени и классу окна. В списке всех приложений включи переключатель, чтобы исключить приложение, или выключи его, чтобы разрешить коррекцию. Защита терминалов и менеджеров паролей показана неактивным переключателем. Список хранится в `~/.config/cajlatland-switcher/excluded-apps.json` и применяется без перезапуска.

## Установка и диагностика

Полный установщик [cajlatland](https://github.com/cajlat1kkk/cajlatland) устанавливает Rust-движок, панель, сочетания клавиш и службу. Состояние можно проверить командой `systemctl --user status cajlatland-switcher.service`. Фоновая коррекция работает в совместимых текстовых полях через Wayland или IBus. Для Яндекс Браузера установщик настраивает запуск через GTK и IBus в XWayland. Чтобы применить настройку, полностью закрой браузер и открой его из меню. Коррекция отключена в полях паролей.

Отдельный CLI можно установить из этой папки командой `cargo install --locked --path .`. Пример: `printf 'Ghbdtn!' | cajlatland-switcher correct`. Опции перечислены в `cajlatland-switcher --help`. Тесты движка: `cargo test --locked`. Лицензия MIT.

В редакторах на Electron под Wayland может потребоваться флаг запуска `--enable-wayland-ime` и полный перезапуск редактора. Для Visual Studio Code также выключи исключение в настройках Switcher. Реакция на двойной Shift зависит от доступности выделения или текущего слова через метод ввода.
