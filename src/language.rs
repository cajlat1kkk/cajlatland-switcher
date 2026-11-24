// Character and adjacent-letter evidence estimated from our small seed lexicons.
// Counts are evidence about spelling, not calibrated posterior probabilities.
use std::collections::HashMap;
#[derive(Default)]
pub struct Profile {
    letters: HashMap<char, u32>,
    pairs: HashMap<(char, char), u32>,
}
impl Profile {
    pub fn train(text: &str) -> Self {
        let mut profile = Self::default();
        for word in text.split_whitespace() {
            let mut prev = None;
            for ch in word.chars() {
                *profile.letters.entry(ch).or_default() += 1;
                if let Some(p) = prev {
                    *profile.pairs.entry((p, ch)).or_default() += 1;
                }
                prev = Some(ch);
            }
        }
        profile
    }
    pub fn evidence(&self, word: &str) -> f32 {
        let mut prev = None;
        let mut total = 0.0;
        let mut weight = 0.0;
        for c in word.chars() {
            let n = *self.letters.get(&c).unwrap_or(&0) as f32;
            total += n / (n + 8.0);
            weight += 1.0;
            if let Some(p) = prev {
                let n = *self.pairs.get(&(p, c)).unwrap_or(&0) as f32;
                total += 2.0 * n / (n + 2.0);
                weight += 2.0;
            }
            prev = Some(c);
        }
        if weight > 0.0 {
            total / weight
        } else {
            0.0
        }
    }
}
