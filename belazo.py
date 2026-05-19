# -*- coding: utf-8 -*-

ALPHABET = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'

PUNCT_TO_WORD = {
    '.': 'тчк',
    ',': 'зпт',
    '?': 'впр',
    '!': 'вск',
    ':': 'двт',
    ';': 'тсз',
    '-': 'тир',
    '—': 'тир',
    '«': 'квы',
    '»': 'квз',
    '"': 'квы',
    '(': 'лск',
    ')': 'пск'
}

WORD_TO_PUNCT = {v: k for k, v in PUNCT_TO_WORD.items()}


def convert_punctuation(text: str, to_word: bool = True) -> str:
    """
    Преобразование знаков препинания:
    to_word=True  -> '.' -> 'тчк', ',' -> 'зпт' и т.д.
    to_word=False -> 'тчк' -> '.', 'зпт' -> ',' и т.д.
    """
    if to_word:
        result = []
        for ch in text:
            result.append(PUNCT_TO_WORD.get(ch, ch))
        return ''.join(result)

    result = text
    for word, punct in WORD_TO_PUNCT.items():
        result = result.replace(word, punct)
        result = result.replace(word.upper(), punct)
    return result


def normalize_russian_char(ch: str) -> str:
    """Нормализует русскую букву: ё -> е."""
    if ch.lower() == 'ё':
        return 'е'
    return ch.lower()


def create_bellaso_table():
    """
    Создаёт таблицу Белазо 32x32 для русского алфавита без 'ё'.
    Каждая следующая строка - циклический сдвиг алфавита.
    """
    table = []
    for shift in range(len(ALPHABET)):
        row = ALPHABET[shift:] + ALPHABET[:shift]
        table.append(row)
    return table


def sanitize_key(key: str) -> str:
    """
    Оставляет в ключе только русские буквы.
    Буква ё заменяется на е.
    """
    cleaned = []
    for ch in key:
        ch_norm = normalize_russian_char(ch)
        if ch_norm in ALPHABET:
            cleaned.append(ch_norm)
    return ''.join(cleaned)


def prepare_key(text: str, key: str) -> str:
    """
    Подготавливает ключ под длину текста:
    ключевая буква ставится только напротив русской буквы текста.
    Остальные символы сохраняются как есть.
    """
    clean_key = sanitize_key(key)
    if not clean_key:
        raise ValueError("Ключ должен содержать хотя бы одну русскую букву.")

    prepared = []
    key_index = 0

    for ch in text:
        ch_norm = normalize_russian_char(ch)
        if ch_norm in ALPHABET:
            prepared.append(clean_key[key_index % len(clean_key)])
            key_index += 1
        else:
            prepared.append(ch)

    return ''.join(prepared)


def bellaso_encrypt(text: str, key: str, convert_punct: bool = False) -> str:
    """
    Шифрование шифром Белазо.
    """
    if convert_punct:
        text = convert_punctuation(text, to_word=True)

    table = create_bellaso_table()
    prepared_key = prepare_key(text, key)

    result = []

    for i, ch in enumerate(text):
        ch_norm = normalize_russian_char(ch)

        if ch_norm in ALPHABET:
            text_index = ALPHABET.index(ch_norm)
            key_char = normalize_russian_char(prepared_key[i])
            key_index = ALPHABET.index(key_char)

            enc_char = table[key_index][text_index]

            if ch.isupper():
                result.append(enc_char.upper())
            else:
                result.append(enc_char)
        else:
            result.append(ch)

    return ''.join(result)


def bellaso_decrypt(text: str, key: str, convert_punct: bool = False) -> str:
    """
    Расшифрование шифра Белазо.
    """
    table = create_bellaso_table()
    prepared_key = prepare_key(text, key)

    result = []

    for i, ch in enumerate(text):
        ch_norm = normalize_russian_char(ch)

        if ch_norm in ALPHABET:
            key_char = normalize_russian_char(prepared_key[i])
            key_index = ALPHABET.index(key_char)

            text_index = table[key_index].index(ch_norm)
            dec_char = ALPHABET[text_index]

            if ch.isupper():
                result.append(dec_char.upper())
            else:
                result.append(dec_char)
        else:
            result.append(ch)

    decrypted = ''.join(result)

    if convert_punct:
        decrypted = convert_punctuation(decrypted, to_word=False)

    return decrypted


def main():
    print("=" * 70)
    print("Шифр Белазо")
    print("=" * 70)

    while True:
        print("\n1 - Зашифровать")
        print("2 - Расшифровать")
        print("0 - Выход")

        choice = input("Ваш выбор: ").strip()

        if choice == '0':
            print("Выход.")
            break

        elif choice in ('1', '2'):
            text = input("Введите текст: ")
            key = input("Введите ключ: ")
            punct_mode = input("Преобразовать знаки препинания в слова? (y/n): ").strip().lower()
            convert_punct = punct_mode in ('y', 'yes', 'д', 'да')

            try:
                if choice == '1':
                    result = bellaso_encrypt(text, key, convert_punct=convert_punct)
                    print(f"\nЗашифрованный текст:\n{result}")
                else:
                    result = bellaso_decrypt(text, key, convert_punct=convert_punct)
                    print(f"\nРасшифрованный текст:\n{result}")
            except ValueError as e:
                print(f"\nОшибка: {e}")

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()