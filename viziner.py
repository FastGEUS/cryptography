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


def create_vigenere_table():
    """
    Создает таблицу Виженера для русского алфавита без Ё.
    """
    table = []
    for shift in range(ALPHABET_LEN):
        row = ALPHABET[shift:] + ALPHABET[:shift]
        table.append(row)
    return ALPHABET, table


def convert_punctuation(text: str, to_word: bool = True) -> str:
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
    preserve_unknown: bool = True
) -> str:
    text = text.upper().replace('Ё', 'Е')

    if convert_punct:
        text = convert_punctuation(text, to_word=True)

    if preserve_unknown:
        return text

    return ''.join(ch for ch in text if ch in ALPHABET)


def validate_single_key(key: str) -> str:
    if not key:
        raise ValueError("Ключ не должен быть пустым.")

    key = key.upper().replace('Ё', 'Е')

    if len(key) != 1:
        raise ValueError("Ключ должен состоять ровно из одной русской буквы.")

    if key not in ALPHABET:
        raise ValueError("Ключ должен быть русской буквой из алфавита без Ё.")

    return key


def _encrypt_symbol(text_char: str, gamma_char: str) -> str:
    text_idx = ALPHABET.index(text_char)
    gamma_idx = ALPHABET.index(gamma_char)
    enc_idx = (text_idx + gamma_idx) % ALPHABET_LEN
    return ALPHABET[enc_idx]


def _decrypt_symbol(cipher_char: str, gamma_char: str) -> str:
    cipher_idx = ALPHABET.index(cipher_char)
    gamma_idx = ALPHABET.index(gamma_char)
    dec_idx = (cipher_idx - gamma_idx) % ALPHABET_LEN
    return ALPHABET[dec_idx]


def vigenere_process(
    text: str,
    key: str,
    mode: str = "encrypt",
    variant: str = "autokey",
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    """
    Универсальная функция для двух вариантов:
    1. autokey    -> гамма = ключ + открытый текст
    2. ciphertext -> гамма = ключ + шифртекст
    """
    try:
        key = validate_single_key(key)
        processed_text = normalize_text(
            text,
            convert_punct=convert_punct,
            preserve_unknown=preserve_unknown
        )

        result_chars: List[str] = []
        gamma_stream: List[str] = [key]
        steps: List[Dict[str, Any]] = []

        gamma_index = 0

        for pos, char in enumerate(processed_text):
            if char in ALPHABET:
                gamma_char = gamma_stream[gamma_index]

                if mode == "encrypt":
                    result_char = _encrypt_symbol(char, gamma_char)

                    if variant == "autokey":
                        gamma_stream.append(char)
                    elif variant == "ciphertext":
                        gamma_stream.append(result_char)
                    else:
                        raise ValueError("variant должен быть 'autokey' или 'ciphertext'.")

                    source_char = char

                elif mode == "decrypt":
                    result_char = _decrypt_symbol(char, gamma_char)

                    if variant == "autokey":
                        gamma_stream.append(result_char)
                    elif variant == "ciphertext":
                        gamma_stream.append(char)
                    else:
                        raise ValueError("variant должен быть 'autokey' или 'ciphertext'.")

                    source_char = char

                else:
                    raise ValueError("mode должен быть 'encrypt' или 'decrypt'.")

                result_chars.append(result_char)

                if return_steps:
                    steps.append({
                        "input_pos": pos,
                        "input_char": source_char,
                        "gamma_char": gamma_char,
                        "input_index": ALPHABET.index(source_char),
                        "gamma_index": ALPHABET.index(gamma_char),
                        "result_index": ALPHABET.index(result_char),
                        "result_char": result_char,
                        "mode": mode,
                        "variant": variant
                    })

                gamma_index += 1
            else:
                if preserve_unknown:
                    result_chars.append(char)
                    if return_steps:
                        steps.append({
                            "input_pos": pos,
                            "input_char": char,
                            "gamma_char": None,
                            "input_index": None,
                            "gamma_index": None,
                            "result_index": None,
                            "result_char": char,
                            "mode": "preserve",
                            "variant": variant
                        })

        result_text = ''.join(result_chars)

        used_gamma = ''.join(gamma_stream[:gamma_index])

        return {
            "success": True,
            "algorithm": "vigenere",
            "mode": mode,
            "variant": variant,
            "key": key,
            "alphabet": ALPHABET,
            "input_text": text,
            "normalized_text": processed_text,
            "gamma": used_gamma,
            "result_text": result_text,
            "steps": steps
        }

    except Exception as e:
        return {
            "success": False,
            "algorithm": "vigenere",
            "mode": mode,
            "variant": variant,
            "error": str(e),
            "input_text": text,
            "key": key
        }


def vigenere_encrypt_autokey(
    text: str,
    key: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    return vigenere_process(
        text=text,
        key=key,
        mode="encrypt",
        variant="autokey",
        preserve_unknown=preserve_unknown,
        convert_punct=convert_punct,
        return_steps=return_steps
    )


def vigenere_decrypt_autokey(
    text: str,
    key: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    return vigenere_process(
        text=text,
        key=key,
        mode="decrypt",
        variant="autokey",
        preserve_unknown=preserve_unknown,
        convert_punct=convert_punct,
        return_steps=return_steps
    )


def vigenere_encrypt_ciphertext(
    text: str,
    key: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    return vigenere_process(
        text=text,
        key=key,
        mode="encrypt",
        variant="ciphertext",
        preserve_unknown=preserve_unknown,
        convert_punct=convert_punct,
        return_steps=return_steps
    )


def vigenere_decrypt_ciphertext(
    text: str,
    key: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    return vigenere_process(
        text=text,
        key=key,
        mode="decrypt",
        variant="ciphertext",
        preserve_unknown=preserve_unknown,
        convert_punct=convert_punct,
        return_steps=return_steps
    )


def run_vigenere(
    mode: str,
    variant: str,
    text: str,
    key: str,
    preserve_unknown: bool = True,
    convert_punct: bool = False,
    return_steps: bool = False
) -> Dict[str, Any]:
    return vigenere_process(
        text=text,
        key=key,
        mode=mode,
        variant=variant,
        preserve_unknown=preserve_unknown,
        convert_punct=convert_punct,
        return_steps=return_steps
    )


def format_steps(steps: List[Dict[str, Any]]) -> str:
    if not steps:
        return "Шаги отсутствуют."

    lines = []
    lines.append("№ | Вход | Гамма | idx(вход) | idx(гамма) | idx(рез) | Результат | Режим")
    lines.append("-" * 95)

    for i, step in enumerate(steps, start=1):
        lines.append(
            f"{i:>2} | "
            f"{str(step['input_char']):^4} | "
            f"{str(step['gamma_char']):^5} | "
            f"{str(step['input_index']):^9} | "
            f"{str(step['gamma_index']):^10} | "
            f"{str(step['result_index']):^8} | "
            f"{str(step['result_char']):^8} | "
            f"{step['mode']}"
        )
    return '\n'.join(lines)


def print_result_block(result: Dict[str, Any]) -> None:
    if not result["success"]:
        print(f"\nОшибка: {result['error']}")
        return

    variant_name = "САМОКЛЮЧ" if result["variant"] == "autokey" else "ШИФР-ТЕКСТ"
    mode_name = "ШИФРОВАНИЕ" if result["mode"] == "encrypt" else "РАСШИФРОВАНИЕ"

    print("\n" + "=" * 80)
    print(f"Виженер | {variant_name} | {mode_name}")
    print("=" * 80)
    print(f"Исходный текст:        {result['input_text']}")
    print(f"Нормализованный текст: {result['normalized_text']}")
    print(f"Ключ:                  {result['key']}")
    print(f"Гамма:                 {result['gamma']}")
    print(f"Результат:             {result['result_text']}")
    print("=" * 80)


def main():
    alphabet, table = create_vigenere_table()

    print("=" * 80)
    print("ШИФР ВИЖЕНЕРА ДЛЯ РУССКОГО ЯЗЫКА")
    print("=" * 80)
    print(f"Используемый алфавит ({len(alphabet)} букв):")
    print(alphabet)
    print("Примечание: буква Ё заменяется на Е")
    print("=" * 80)

    while True:
        print("\nВыберите действие:")
        print("1 - Зашифровать текст (САМОКЛЮЧ)")
        print("2 - Расшифровать текст (САМОКЛЮЧ)")
        print("3 - Зашифровать текст (ШИФР-ТЕКСТ)")
        print("4 - Расшифровать текст (ШИФР-ТЕКСТ)")
        print("5 - Показать таблицу Виженера")
        print("0 - Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == '0':
            print("\nДо свидания!")
            break

        elif choice in ('1', '2', '3', '4'):
            text = input("\nВведите текст: ")
            key = input("Введите ключ (одна буква): ")
            show_steps = input("Показать пошаговый разбор? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')
            convert_punct = input("Преобразовывать знаки препинания в коды? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')

            if choice == '1':
                result = vigenere_encrypt_autokey(
                    text, key,
                    preserve_unknown=True,
                    convert_punct=convert_punct,
                    return_steps=show_steps
                )
            elif choice == '2':
                result = vigenere_decrypt_autokey(
                    text, key,
                    preserve_unknown=True,
                    convert_punct=convert_punct,
                    return_steps=show_steps
                )
            elif choice == '3':
                result = vigenere_encrypt_ciphertext(
                    text, key,
                    preserve_unknown=True,
                    convert_punct=convert_punct,
                    return_steps=show_steps
                )
            else:
                result = vigenere_decrypt_ciphertext(
                    text, key,
                    preserve_unknown=True,
                    convert_punct=convert_punct,
                    return_steps=show_steps
                )

            print_result_block(result)

            if result["success"] and show_steps:
                print("\nПошаговый разбор:")
                print(format_steps(result["steps"]))

        elif choice == '5':
            print("\nТаблица Виженера:")
            print("   " + " ".join(alphabet))
            for i, row in enumerate(table):
                print(f"{i:>2}: {' '.join(row)}")

        else:
            print("\nНеверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()