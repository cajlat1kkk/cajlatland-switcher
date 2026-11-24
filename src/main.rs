use cajlatland_switcher::{Engine, Options};
use std::{
    env, fs,
    io::{self, Read, Write},
};
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args().skip(1);
    match args.next().as_deref() {
        None | Some("--help") => {
            println!("cajlatland-switcher correct [--no-layout] [--no-typos] [--threshold 0..1] [--min-length N] [--exclude-file PATH]\nUTF-8: stdin → stdout");
            return Ok(());
        }
        Some("--version") => {
            println!("cajlatland-switcher {}", env!("CARGO_PKG_VERSION"));
            return Ok(());
        }
        Some("correct") => (),
        _ => return Err("unknown command; see --help".into()),
    }
    let mut options = Options::default();
    let mut file = None;
    while let Some(flag) = args.next() {
        match flag.as_str() {
            "--no-layout" => options.layout = false,
            "--no-typos" => options.typos = false,
            "--threshold" => {
                options.threshold = args.next().ok_or("missing threshold")?.parse()?;
                if !(0.0..=1.0).contains(&options.threshold) {
                    return Err("threshold outside 0..1".into());
                }
            }
            "--min-length" => options.min_length = args.next().ok_or("missing length")?.parse()?,
            "--exclude-file" => file = Some(args.next().ok_or("missing path")?),
            _ => return Err("unknown option".into()),
        }
    }
    let mut engine = Engine::new(options);
    if let Some(path) = file {
        for word in fs::read_to_string(path)?.split_whitespace() {
            engine.exclude(word);
        }
    }
    let mut input = String::new();
    io::stdin()
        .take(1024 * 1024 + 1)
        .read_to_string(&mut input)?;
    if input.len() > 1024 * 1024 {
        return Err("input exceeds 1 MiB".into());
    }
    io::stdout().write_all(engine.correct(&input).as_bytes())?;
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("cajlatland-switcher: {e}");
        std::process::exit(1);
    }
}
