# -*- coding: utf-8 -*-

from typing import Dict, Any, List

ALPHABET = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
ALPHABET_LEN = len(ALPHABET)

PUNCT_TO_WORD = {
    '.': 'ТЧК',
    ',': 'ЗПТ',
    '?': 'ВПР',
    '!': 'ВСК',
    ':': 'ДВТ',
    ';': 'ТСЗ',
    '-': 'ТИР',
    '—': 'ТИР',
    '«': 'КВЫ',
    '»': 'КВЗ',
    '"': 'КВЫ',
    '(': 'ЛСК',
    ')': 'ПСК'
}

WORD_TO_PUNCT = {v: k for k, v in PUNCT_TO_WORD.items()}


def create_trithemius_table():
    """
    Создаёт таблицу Тритемия для русского алфавита из 32 букв.
    """
    table = []
    for shift in range(ALPHABET_LEN):
        row = ALPHABET[shift:] + ALPHABET[:shift]
        table.append(row)
    return ALPHABET, table


def convert_punctuation(text: str, to_word: bool = True) -> str:
    """
    Преобразует знаки препинания в словесные коды и обратно.
    """
    if to_word:
        result = []
        for ch in text:
            result.append(PUNCT_TO_WORD.get(ch, ch))
        return ''.join(result)

    result = text
    for word, punct in WORD_TO_PUNCT.items():
        result = result.replace(word, punct)
    return result


def normalize_text(
    text: str,
    convert_punct: bool = False,
    keep_unknown: bool = True
) -> str:
    """
    Нормализация текста:
    - верхний регистр,
    - Ё -> Е,
    - опционально преобразование пунктуации в словесные коды.
    """
    text = text.upper().replace('Ё', 'Е')

    if convert_punct:
        text = convert_punctuation(text, to_word=True)

    if keep_unknown:
        return text

    return ''.join(ch for ch in text if ch in ALPHABET)


def trithemius_process(
    text: str,
    encrypt: bool = True,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    """
    Универсальная функция шифрования/расшифрования шифром Тритемия.

    Логика:
    - для i-го обрабатываемого символа сдвиг равен i mod 32;
    - при шифровании: C = (M + i) mod 32;
    - при расшифровании: M = (C - i) mod 32.
    """
    processed_text = normalize_text(
        text,
        convert_punct=convert_punct,
        keep_unknown=preserve_unknown
    )

    result_chars: List[str] = []
    steps: List[Dict[str, Any]] = []

    position = 0

    for idx, char in enumerate(processed_text):
        if char in ALPHABET:
            shift = position % ALPHABET_LEN
            char_index = ALPHABET.index(char)

            if encrypt:
                new_index = (char_index + shift) % ALPHABET_LEN
                new_char = ALPHABET[new_index]
                operation = "encrypt"
            else:
                new_index = (char_index - shift) % ALPHABET_LEN
                new_char = ALPHABET[new_index]
                operation = "decrypt"

            result_chars.append(new_char)

            if return_steps:
                steps.append({
                    "input_pos": idx,
                    "letter_pos": position,
                    "char": char,
                    "char_index": char_index,
                    "shift": shift,
                    "result_index": new_index,
                    "result_char": new_char,
                    "operation": operation
                })

            position += 1
        else:
            if preserve_unknown:
                result_chars.append(char)
                if return_steps:
                    steps.append({
                        "input_pos": idx,
                        "letter_pos": None,
                        "char": char,
                        "char_index": None,
                        "shift": None,
                        "result_index": None,
                        "result_char": char,
                        "operation": "preserve"
                    })

    result_text = ''.join(result_chars)

    return {
        "success": True,
        "mode": "encrypt" if encrypt else "decrypt",
        "alphabet": ALPHABET,
        "input_text": text,
        "normalized_text": processed_text,
        "result_text": result_text,
        "steps": steps
    }


def trithemius_encrypt(
    text: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    return trithemius_process(
        text=text,
        encrypt=True,
        preserve_unknown=preserve_unknown,
        convert_punct=convert_punct,
        return_steps=return_steps
    )


def trithemius_decrypt(
    text: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    return trithemius_process(
        text=text,
        encrypt=False,
        preserve_unknown=preserve_unknown,
        convert_punct=convert_punct,
        return_steps=return_steps
    )


def format_steps(steps: List[Dict[str, Any]]) -> str:
    """
    Красивое текстовое представление шагов для консоли или GUI.
    """
    if not steps:
        return "Шаги отсутствуют."

    lines = []
    lines.append(
        "№ | Вход | Индекс | Сдвиг | Результат | Индекс результата | Действие"
    )
    lines.append("-" * 72)

    for i, step in enumerate(steps, start=1):
        lines.append(
            f"{i:>2} | "
            f"{str(step['char']):^4} | "
            f"{str(step['char_index']):^6} | "
            f"{str(step['shift']):^5} | "
            f"{str(step['result_char']):^8} | "
            f"{str(step['result_index']):^16} | "
            f"{step['operation']}"
        )

    return '\n'.join(lines)


def run_trithemius(
    mode: str,
    text: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    """
    Единая точка входа для GUI.
    mode: 'encrypt' или 'decrypt'
    """
    if mode == "encrypt":
        return trithemius_encrypt(
            text=text,
            preserve_unknown=preserve_unknown,
            convert_punct=convert_punct,
            return_steps=return_steps
        )
    elif mode == "decrypt":
        return trithemius_decrypt(
            text=text,
            preserve_unknown=preserve_unknown,
            convert_punct=convert_punct,
            return_steps=return_steps
        )
    else:
        raise ValueError("mode должен быть 'encrypt' или 'decrypt'.")


def main():
    alphabet, table = create_trithemius_table()

    print("=" * 60)
    print("ПРОГРАММА: ШИФР ТРИТЕМИЯ (РУССКИЙ ЯЗЫК)")
    print("Особенности: алфавит 32 буквы, Й включена, Ё -> Е")
    print(f"Алфавит: {alphabet}")
    print("=" * 60)

    while True:
        print("\nДоступные действия:")
        print("1 - Зашифровать сообщение")
        print("2 - Расшифровать сообщение")
        print("3 - Показать таблицу Тритемия")
        print("0 - Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == '1':
            user_text = input("Введите текст для зашифрования: ")
            show_steps = input("Показать пошаговый разбор? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')
            convert_punct = input("Преобразовывать знаки препинания в коды? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')

            res = trithemius_encrypt(
                user_text,
                preserve_unknown=True,
                convert_punct=convert_punct,
                return_steps=show_steps
            )

            print(f"\nНормализованный текст: {res['normalized_text']}")
            print(f"Результат: {res['result_text']}")

            if show_steps:
                print("\nПошаговый разбор:")
                print(format_steps(res["steps"]))

        elif choice == '2':
            user_text = input("Введите текст для расшифрования: ")
            show_steps = input("Показать пошаговый разбор? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')
            convert_punct = input("Преобразовывать знаки препинания в коды? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')

            res = trithemius_decrypt(
                user_text,
                preserve_unknown=True,
                convert_punct=convert_punct,
                return_steps=show_steps
            )

            print(f"\nНормализованный текст: {res['normalized_text']}")
            print(f"Результат: {res['result_text']}")

            if show_steps:
                print("\nПошаговый разбор:")
                print(format_steps(res["steps"]))

        elif choice == '3':
            print("\nТаблица Тритемия:")
            print("   " + " ".join(ALPHABET))
            for i, row in enumerate(table):
                print(f"{i:>2}: {' '.join(row)}")

        elif choice == '0':
            print("Программа завершена.")
            break

        else:
            print("Ошибка: введите 1, 2, 3 или 0.")


if __name__ == "__main__":
    main()