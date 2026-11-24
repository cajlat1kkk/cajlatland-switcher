// Columns correspond to the same physical key in XKB us and ru (йцукен).
const ROWS: [(&str, &str); 2] = [
    (
        "`qwertyuiop[]asdfghjkl;'zxcvbnm,./",
        "ёйцукенгшщзхъфывапролджэячсмитьбю.",
    ),
    (
        "~QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?",
        "ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,",
    ),
];

pub fn convert(word: &str, to_russian: bool) -> Option<String> {
    word.chars()
        .map(|c| {
            ROWS.iter().find_map(|&(en, ru)| {
                let (from, to) = if to_russian { (en, ru) } else { (ru, en) };
                from.chars()
                    .zip(to.chars())
                    .find_map(|(a, b)| (a == c).then_some(b))
            })
        })
        .collect()
}
