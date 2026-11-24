mod language;
mod layout;
mod lexicon;
use std::collections::HashSet;

#[derive(Clone, Copy)]
pub struct Options {
    pub layout: bool,
    pub typos: bool,
    pub threshold: f32,
    pub min_length: usize,
}
impl Default for Options {
    fn default() -> Self {
        Self {
            layout: true,
            typos: true,
            threshold: 0.90,
            min_length: 3,
        }
    }
}
pub struct Engine {
    words: HashSet<String>,
    exceptions: HashSet<String>,
    profiles: [language::Profile; 2],
    options: Options,
}
fn vocabulary(raw: &str) -> HashSet<String> {
    raw.split_whitespace().map(str::to_lowercase).collect()
}
// One adjacent transposition, substitution, insertion or deletion (OSA distance <= 1).
fn one_edit(a: &[char], b: &[char]) -> bool {
    if a.len() > b.len() {
        return one_edit(b, a);
    }
    if b.len() - a.len() > 1 {
        return false;
    }
    let i = a.iter().zip(b).position(|(x, y)| x != y).unwrap_or(a.len());
    if a.len() != b.len() {
        return a[i..] == b[i + 1..];
    }
    if i == a.len() {
        return false;
    }
    a[i + 1..] == b[i + 1..]
        || (i + 1 < a.len() && a[i] == b[i + 1] && a[i + 1] == b[i] && a[i + 2..] == b[i + 2..])
}
fn case_like(original: &str, lower: &str) -> Option<String> {
    if original.chars().all(char::is_lowercase) {
        Some(lower.into())
    } else if original.chars().next()?.is_uppercase()
        && original.chars().skip(1).all(char::is_lowercase)
    {
        let mut chars = lower.chars();
        Some(chars.next()?.to_uppercase().chain(chars).collect())
    } else {
        None
    }
}
impl Engine {
    pub fn new(options: Options) -> Self {
        let mut words = vocabulary(include_str!("../dictionaries/ru.txt"));
        words.extend(vocabulary(include_str!("../dictionaries/en.txt")));
        Self {
            profiles: [
                language::Profile::train(include_str!("../dictionaries/en.txt")),
                language::Profile::train(include_str!("../dictionaries/ru.txt")),
            ],
            words,
            exceptions: vocabulary(include_str!("../dictionaries/exceptions.txt")),
            options,
        }
    }
    pub fn exclude(&mut self, word: &str) {
        self.exceptions.insert(word.to_lowercase());
    }
    fn candidate(&self, token: &str, contextual: bool) -> Option<String> {
        let lower = token.to_lowercase();
        if self.words.contains(&lower) || self.exceptions.contains(&lower) {
            return None;
        }
        let n = token.chars().count();
        if n < self.options.min_length && !(contextual && n == 1) {
            return None;
        }
        if token.chars().filter(|c| c.is_alphabetic()).count() > 1
            && token
                .chars()
                .filter(|c| c.is_alphabetic())
                .all(char::is_uppercase)
        {
            return None;
        }
        if self.options.layout {
            let ru = token.chars().any(|c| c.is_ascii_alphabetic());
            if let Some(other) = layout::convert(token, ru) {
                let converted = other.to_lowercase();
                let confidence = 0.93 + 0.05 * self.profiles[ru as usize].evidence(&converted)
                    - 0.02 * self.profiles[!ru as usize].evidence(&lower);
                if (self.words.contains(&converted)
                    || (n >= 4 && !lexicon::contains(&lower) && lexicon::contains(&converted)))
                    && self.options.threshold <= confidence
                {
                    return Some(other);
                }
            }
        }
        if !self.options.typos || n < 3 || !token.chars().all(char::is_alphabetic) {
            return None;
        }
        // Explicitly reviewed frequent errors are stronger evidence than an arbitrary nearby word.
        for (wrong, right) in [
            ("привте", "привет"),
            ("здраствуйте", "здравствуйте"),
            ("teh", "the"),
            ("helo", "hello"),
            ("recieve", "receive"),
            ("thier", "their"),
        ] {
            if lower == wrong && self.options.threshold <= 0.98 {
                return case_like(token, right);
            }
        }
        if lexicon::contains(&lower) {
            return None;
        }
        if (5..=48).contains(&n) && self.options.threshold <= 0.90 {
            let mut letters: Vec<_> = lower.chars().collect();
            let mut best = None;
            for i in 1..letters.len() {
                letters.swap(i - 1, i);
                let candidate: String = letters.iter().collect();
                letters.swap(i - 1, i);
                if candidate != lower
                    && (lexicon::contains(&candidate) || self.words.contains(&candidate))
                {
                    if best.is_some() {
                        return None;
                    }
                    best = Some(candidate);
                }
            }
            if let Some(candidate) = best {
                return case_like(token, &candidate);
            }
        }
        if n < 5 || self.options.threshold > 0.84 {
            return None;
        }
        let letters: Vec<_> = lower.chars().collect();
        let mut candidates = self
            .words
            .iter()
            .filter(|w| one_edit(&letters, &w.chars().collect::<Vec<_>>()));
        let first = candidates.next()?;
        if candidates.next().is_some() {
            None
        } else {
            case_like(token, first)
        }
    }
    fn change(&self, token: &str, contextual: bool) -> Option<String> {
        if token.contains("://")
            || token.contains(['@', '/', '\\', '_', '=', '*', '(', ')', '#', '$'])
            || token.chars().any(|c| c.is_ascii_digit())
        {
            return None;
        }
        let word = token.trim_end_matches(['!', '?', ':', ';', ',', '.', '…']);
        // Prefer a complete known conversion (period and comma are letters on Russian keys).
        self.candidate(token, contextual).or_else(|| {
            if word.len() == token.len() {
                return None;
            }
            let mut out = self.candidate(word, contextual)?;
            out.push_str(&token[word.len()..]);
            Some(out)
        })
    }
    pub fn correct(&self, text: &str) -> String {
        let mut result = String::with_capacity(text.len());
        for line in text.split_inclusive('\n') {
            let first = line.split_whitespace().next().unwrap_or("");
            if matches!(
                first,
                "sudo"
                    | "systemctl"
                    | "git"
                    | "cargo"
                    | "curl"
                    | "bash"
                    | "ssh"
                    | "SELECT"
                    | "fn"
                    | "let"
                    | "def"
                    | "import"
            ) || line.contains('`')
            {
                result.push_str(line);
                continue;
            }
            let mut tokens = line.split_inclusive(char::is_whitespace).peekable();
            while let Some(chunk) = tokens.next() {
                let word = chunk.trim_end_matches(char::is_whitespace);
                // A single Z is Я only with corroboration from the following converted word.
                let context = matches!(word, "Z" | "z")
                    && tokens.peek().and_then(|next| {
                        let next = next.trim_end();
                        let value = layout::convert(next, true)?;
                        Some(self.options.layout && self.words.contains(&value.to_lowercase()))
                    }) == Some(true);
                result.push_str(self.change(word, context).as_deref().unwrap_or(word));
                result.push_str(&chunk[word.len()..]);
            }
        }
        result
    }
}
