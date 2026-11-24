use std::{collections::BTreeSet, env, fs, io::Write, path::PathBuf};

fn main() {
    let out = PathBuf::from(env::var_os("OUT_DIR").unwrap());
    let mut words = BTreeSet::new();
    println!("cargo:rerun-if-env-changed=CAJLATLAND_DICT_DIR");
    let system = PathBuf::from("/usr/share/hunspell");
    let local =
        PathBuf::from(env::var_os("HOME").unwrap()).join(".local/share/cajlatland-switcher/dicts");
    let dir = env::var_os("CAJLATLAND_DICT_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            if system.join("ru_RU.dic").is_file() {
                system
            } else {
                local
            }
        });
    for lang in ["ru_RU", "en_US"] {
        let dict = dir.join(format!("{lang}.dic"));
        println!("cargo:rerun-if-changed={}", dict.display());
        if let Ok(text) = fs::read_to_string(dict) {
            for entry in text.lines().skip(1) {
                let word = entry.split(['/', ' ', '\t']).next().unwrap_or("");
                if word.chars().count() >= 3 && word.chars().all(char::is_lowercase) {
                    words.insert(word.to_owned());
                }
            }
        }
    }
    let mut data = fs::File::create(out.join("words")).unwrap();
    let mut index = fs::File::create(out.join("offsets")).unwrap();
    let mut offset = 0u32;
    for word in words {
        index.write_all(&offset.to_le_bytes()).unwrap();
        data.write_all(word.as_bytes()).unwrap();
        offset += word.len() as u32;
    }
    index.write_all(&offset.to_le_bytes()).unwrap();
}
