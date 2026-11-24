"""Forced physical-key translation; punctuation between words is preserved."""
import sys

english = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
russian = "ёйцукенгшщзхъфывапролджэячсмитьбю."
shift_en = '~QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?'
shift_ru = "ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,"
def convert(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return text
    ru = sum(c in russian + shift_ru for c in letters)
    src, dst = (russian + shift_ru, english + shift_en) if ru > len(letters)/2 else (english + shift_en, russian + shift_ru)
    return text.translate(str.maketrans(src, dst))

if __name__ == "__main__":
    sys.stdout.write(convert(sys.stdin.read()))
