# Cajlatland Switcher

A local Russian/English layout and typo corrector for Hyprland. The full cajlatland installer includes the Rust engine, Wayland input method, GTK controls, Shift bindings and user service. Open **Cajlatland Switcher** from the application menu to test typing or change preferences. Text replacement requires a cooperating Wayland application; supported GTK/IBus clients can also run under XWayland. Password fields are excluded.

A short Shift changes the layout. Double Shift converts the selection or last word. Pressing both Shift keys pauses or resumes automatic layout correction. Settings lists effective application exclusions, including Visual Studio Code. Each application has a switch. Turn it on to exclude the application and off to allow correction. Search filters the list.

Install only the command-line engine with `cargo install --locked --path .`. Run `printf 'ghbdtn' | cajlatland-switcher correct` or `cargo test --locked`. License: MIT.
