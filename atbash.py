# -*- coding: utf-8 -*-

ALPHABET = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
REVERSED_ALPHABET = ALPHABET[::-1]

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
    to_word=True  -> '.' -> 'тчк', ',' -> 'зпт'
    to_word=False -> 'тчк' -> '.', 'зпт' -> ','
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
    """Нормализация русской буквы: ё -> е."""
    if ch.lower() == 'ё':
        return 'е'
    return ch.lower()


def atbash(text: str, convert_punct: bool = False) -> str:
    """
    Шифрование/дешифрование шифром Атбаш для русского алфавита.
    Шифр симметричен: одна и та же функция подходит и для шифрования, и для расшифрования.
    """
    if convert_punct:
        text = convert_punctuation(text, to_word=True)

    result = []

    for ch in text:
        normalized = normalize_russian_char(ch)

        if normalized in ALPHABET:
            index = ALPHABET.index(normalized)
            new_char = REVERSED_ALPHABET[index]

            if ch.isupper():
                result.append(new_char.upper())
            else:
                result.append(new_char)
        else:
            result.append(ch)

    return ''.join(result)


def run_atbash(text: str, convert_punct: bool = False, restore_punct: bool = False) -> dict:
    """
    Унифицированная обёртка для GUI.
    
    Параметры:
    - text: исходный текст
    - convert_punct: перед шифрованием заменить знаки препинания на словесные коды
    - restore_punct: после преобразования восстановить знаки препинания
    
    Возвращает словарь с результатом.
    """
    result = atbash(text, convert_punct=convert_punct)

    if restore_punct:
        result = convert_punctuation(result, to_word=False)

    return {
        "success": True,
        "cipher": "Атбаш",
        "input_text": text,
        "output_text": result,
        "convert_punct": convert_punct,
        "restore_punct": restore_punct
    }


def main():
    print("=" * 60)
    print("Шифр Атбаш для русского языка")
    print("=" * 60)

    while True:
        print("\n1 - Преобразовать текст")
        print("0 - Выход")

        choice = input("Ваш выбор: ").strip()

        if choice == '0':
            print("Выход.")
            break

        elif choice == '1':
            text = input("Введите текст: ")
            punct_mode = input("Преобразовать знаки препинания в слова? (y/n): ").strip().lower()
            convert_punct = punct_mode in ('y', 'yes', 'д', 'да')

            result = atbash(text, convert_punct=convert_punct)

            print(f"\nИсходный текст:      {text}")
            print(f"Преобразованный:     {result}")
            print(f"Обратная проверка:   {atbash(result, convert_punct=False)}")

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()