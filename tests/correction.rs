use cajlatland_switcher::{Engine, Options};
#[test]
fn acceptance() {
    let e = Engine::new(Options::default());
    for (s, t) in [
        ("ghbdtn", "привет"),
        ("руддщ", "hello"),
        ("rfr ltkf", "как дела"),
        ("цщкдв", "world"),
        ("vjkjrj", "молоко"),
        ("Ghbdtn!", "Привет!"),
        ("Z jxtym k.,k. Linux", "Я очень люблю Linux"),
        (
            "привте здраствуйте teh helo recieve thier",
            "привет здравствуйте the hello receive their",
        ),
        ("  ghbdtn,\tруддщ!\n", "  привет,\thello!\n"),
    ] {
        assert_eq!(e.correct(s), t);
        assert_eq!(e.correct(t), t);
    }
}
#[test]
fn protected() {
    let mut e = Engine::new(Options::default());
    e.exclude("ghbdtn");
    for s in [
        "GitHub ghbdtn XJG",
        "https://site/ghbdtn a@ghbdtn.ru 10.0.0.1 /tmp/ghbdtn",
        "sudo echo руддщ",
        "git commit -m ghbdtn",
        "`ghbdtn`",
        "world HELLO ssh qzmx",
    ] {
        assert_eq!(e.correct(s), s);
    }
}
#[test]
fn controls() {
    let e = Engine::new(Options {
        typos: false,
        ..Default::default()
    });
    assert_eq!(e.correct("ghbdtn teh"), "привет teh");
    let e = Engine::new(Options {
        layout: false,
        ..Default::default()
    });
    assert_eq!(e.correct("ghbdtn teh"), "ghbdtn the");
    let e = Engine::new(Options {
        threshold: 1.0,
        ..Default::default()
    });
    assert_eq!(e.correct("ghbdtn teh"), "ghbdtn teh");
}

#[test]
fn fix_unambiguous_transposition_and_preserve_case() {
    let e = Engine::new(Options::default());
    assert_eq!(e.correct("Клавиатуар"), "Клавиатура");
    assert_eq!(e.correct("клавиатура"), "клавиатура");
}
