const WORDS: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/words"));
const OFFSETS: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/offsets"));

fn offset(index: usize) -> usize {
    u32::from_le_bytes(OFFSETS[index * 4..index * 4 + 4].try_into().unwrap()) as usize
}

pub fn contains(word: &str) -> bool {
    let (mut low, mut high) = (0, OFFSETS.len() / 4 - 1);
    while low < high {
        let mid = low + (high - low) / 2;
        match WORDS[offset(mid)..offset(mid + 1)].cmp(word.as_bytes()) {
            std::cmp::Ordering::Equal => return true,
            std::cmp::Ordering::Less => low = mid + 1,
            std::cmp::Ordering::Greater => high = mid,
        }
    }
    false
}
