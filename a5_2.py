#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Алгоритм А5/2 — поточный шифр GSM (ослабленная экспортная версия)

Параметры:
R1 — 19 бит | x^19 + x^18 + x^17 + x^14 + 1
R2 — 22 бита | x^22 + x^21 + 1
R3 — 23 бита | x^23 + x^22 + x^21 + x^8 + 1
R4 — 17 бит  | x^17 + x^12 + 1  (управляющий, всегда тактируется)

Отличия от А5/1:
  - Добавлен R4, который ВСЕГДА тактируется и управляет R1, R2, R3
  - Мажоритарная функция вычисляется по битам R4 (а не R1/R2/R3)
  - Выходной бит «усилен»: XOR с мажоритарным битом от буст-битов

Ключ Kc — 64 бита, задаётся словом (буквы → индексы → биты)
Номер кадра — 22 бита (целое 0..4194303)

Преобразование слова в ключ:
  Алфавит: А=1, Б=2, В=3, ..., Я=32 (без Ё)
  Каждая буква → 8-битное представление её индекса
  8 букв → 64 бита ключа (меньше — дополняется нулями, больше — обрезается)
"""

import os

# ── Алфавит ────────────────────────────────────────────────────────────────────

KEY_ALPHABET    = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'  # 32 буквы, без Ё
KEY_CHAR_TO_IDX = {ch: i + 1 for i, ch in enumerate(KEY_ALPHABET)}

KEY_BITS       = 64
LETTERS_NEEDED = KEY_BITS // 8   # 8 букв × 8 бит = 64 бита


def word_to_key_bits(word: str) -> tuple:
    """
    Слово → 64-битный ключ.
    Каждая буква → индекс (А=1..Я=32) → 8 бит.
    До 8 букв — дополнить нулями; больше 8 — обрезать.
    Возвращает (key_bits, table, used_letters).
    """
    normalized = []
    for ch in word.upper():
        if ch == 'Ё':
            ch = 'Е'
        if ch in KEY_CHAR_TO_IDX:
            normalized.append(ch)

    if not normalized:
        raise ValueError("В слове не найдено ни одной русской буквы.")

    used = normalized[:LETTERS_NEEDED]

    table = []
    bits  = []
    for ch in used:
        idx       = KEY_CHAR_TO_IDX[ch]
        byte_bits = [(idx >> (7 - i)) & 1 for i in range(8)]
        table.append((ch, idx, ''.join(map(str, byte_bits))))
        bits.extend(byte_bits)

    while len(bits) < KEY_BITS:
        bits.append(0)

    return bits[:KEY_BITS], table, used


# ── Класс А5/2 ─────────────────────────────────────────────────────────────────

class A5_2:
    """
    Реализация алгоритма А5/2 (экспортная версия GSM).
    Регистры: список битов, индекс 0 = старший (MSB), индекс -1 = младший (LSB).

    Управление тактированием:
      R4 всегда тактируется.
      Мажоритарная функция maj вычисляется по битам R4 (индексы 3, 7, 10).
      R1 тактируется если R1[R1_CLOCK_BIT] == maj
      R2 тактируется если R2[R2_CLOCK_BIT] == maj
      R3 тактируется если R3[R3_CLOCK_BIT] == maj

    Выходной бит (буст-вариант):
      out = R1[-1] ^ R2[-1] ^ R3[-1] ^ majority(R1[15], R2[16], R3[18])
    """

    def __init__(self):
        self.R1_LENGTH = 19
        self.R2_LENGTH = 22
        self.R3_LENGTH = 23
        self.R4_LENGTH = 17

        # Биты тактирования (0-indexed от MSB)
        self.R1_CLOCK_BIT = 8
        self.R2_CLOCK_BIT = 10
        self.R3_CLOCK_BIT = 10

        # Отводы обратной связи (0-indexed от MSB)
        self.R1_FEEDBACK_TAPS = [13, 16, 17, 18]   # x^19+x^18+x^17+x^14+1
        self.R2_FEEDBACK_TAPS = [20, 21]             # x^22+x^21+1
        self.R3_FEEDBACK_TAPS = [7, 20, 21, 22]     # x^23+x^22+x^21+x^8+1
        self.R4_FEEDBACK_TAPS = [11, 16]             # x^17+x^12+1

        # Биты управления R4 (0-indexed от MSB), по ним считается majority
        self.R4_CONTROL_BITS = [3, 7, 10]

        # Буст-биты: конкретные позиции в R1, R2, R3 (0-indexed от MSB)
        # Используются для усиления выходного бита
        self.R1_BOOST_BIT = 15   # позиция 15 в 19-битном R1
        self.R2_BOOST_BIT = 16   # позиция 16 в 22-битном R2
        self.R3_BOOST_BIT = 18   # позиция 18 в 23-битном R3

        self._reset()

    def _reset(self):
        self.R1 = [0] * self.R1_LENGTH
        self.R2 = [0] * self.R2_LENGTH
        self.R3 = [0] * self.R3_LENGTH
        self.R4 = [0] * self.R4_LENGTH

    def majority(self, x, y, z) -> int:
        return 1 if (x + y + z) >= 2 else 0

    def _feedback(self, reg, taps, in_bit=0) -> int:
        fb = in_bit
        for t in taps:
            fb ^= reg[t]
        return fb

    def _shift(self, reg, fb) -> list:
        return [fb] + reg[:-1]

    def _clock_all_forced(self, bit: int):
        """Тактирование всех 4 регистров с загрузкой бита (без stop-and-go)."""
        r1_fb = self._feedback(self.R1, self.R1_FEEDBACK_TAPS, bit)
        r2_fb = self._feedback(self.R2, self.R2_FEEDBACK_TAPS, bit)
        r3_fb = self._feedback(self.R3, self.R3_FEEDBACK_TAPS, bit)
        r4_fb = self._feedback(self.R4, self.R4_FEEDBACK_TAPS, bit)

        self.R1 = self._shift(self.R1, r1_fb)
        self.R2 = self._shift(self.R2, r2_fb)
        self.R3 = self._shift(self.R3, r3_fb)
        self.R4 = self._shift(self.R4, r4_fb)

    def _clock_controlled(self):
        """Тактирование в режиме stop-and-go (управляет R4)."""
        # R4 всегда тактируется первым — вычисляем его следующий бит до сдвига
        r4_fb = self._feedback(self.R4, self.R4_FEEDBACK_TAPS)

        # Majority по битам управления R4 (до сдвига)
        maj = self.majority(
            self.R4[self.R4_CONTROL_BITS[0]],
            self.R4[self.R4_CONTROL_BITS[1]],
            self.R4[self.R4_CONTROL_BITS[2]]
        )

        # Вычисляем обратную связь R1/R2/R3 до сдвига
        r1_fb = self._feedback(self.R1, self.R1_FEEDBACK_TAPS)
        r2_fb = self._feedback(self.R2, self.R2_FEEDBACK_TAPS)
        r3_fb = self._feedback(self.R3, self.R3_FEEDBACK_TAPS)

        # Сдвиг R1/R2/R3 только если clock_bit совпадает с majority
        if self.R1[self.R1_CLOCK_BIT] == maj:
            self.R1 = self._shift(self.R1, r1_fb)
        if self.R2[self.R2_CLOCK_BIT] == maj:
            self.R2 = self._shift(self.R2, r2_fb)
        if self.R3[self.R3_CLOCK_BIT] == maj:
            self.R3 = self._shift(self.R3, r3_fb)

        # R4 сдвигается всегда
        self.R4 = self._shift(self.R4, r4_fb)

    def initialize(self, key_bits: list, frame_bits: list):
        """
        Инициализация по алгоритму А5/2:
          1. Сброс всех регистров в 0.
          2. 64 такта загрузки ключа (все регистры, без stop-and-go).
          3. 22 такта загрузки номера кадра.
          4. Принудительная установка буст-битов в 1.
          5. 99 тактов разгона (stop-and-go, без выхода).
        """
        self._reset()

        # Шаг 2: загрузка ключа
        for bit in key_bits:
            self._clock_all_forced(bit)

        # Шаг 3: загрузка номера кадра
        for bit in frame_bits:
            self._clock_all_forced(bit)

        # Шаг 4: установка буст-битов (защита от вырожденных ключей)
        self.R1[self.R1_BOOST_BIT] = 1
        self.R2[self.R2_BOOST_BIT] = 1
        self.R3[self.R3_BOOST_BIT] = 1
        self.R4[-1] = 1  # LSB R4

        # Шаг 5: разгон
        for _ in range(99):
            self._clock_controlled()

    def _output_bit(self) -> int:
        """
        Выходной бит А5/2:
          основа: R1[-1] ^ R2[-1] ^ R3[-1]
          усиление: ^ majority(R1[boost], R2[boost], R3[boost])
        """
        base  = self.R1[-1] ^ self.R2[-1] ^ self.R3[-1]
        boost = self.majority(
            self.R1[self.R1_BOOST_BIT],
            self.R2[self.R2_BOOST_BIT],
            self.R3[self.R3_BOOST_BIT]
        )
        return base ^ boost

    def generate_keystream(self, length: int) -> list:
        """Генерация гаммы заданной длины."""
        ks = []
        for _ in range(length):
            ks.append(self._output_bit())
            self._clock_controlled()
        return ks

    def encrypt(self, plaintext_bits: list, key_bits: list, frame_bits: list) -> list:
        self.initialize(key_bits, frame_bits)
        ks = self.generate_keystream(len(plaintext_bits))
        return [p ^ k for p, k in zip(plaintext_bits, ks)]

    def decrypt(self, cipher_bits: list, key_bits: list, frame_bits: list) -> list:
        """Расшифрование идентично шифрованию (XOR симметричен)."""
        return self.encrypt(cipher_bits, key_bits, frame_bits)


# ── Вспомогательные функции ────────────────────────────────────────────────────

def int_to_bits(n, length):
    return [(n >> (length - 1 - i)) & 1 for i in range(length)]

def text_to_bits(text):
    bits = []
    for byte in text.encode('utf-8'):
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits

def bits_to_text(bits):
    if len(bits) % 8:
        bits = bits + [0] * (8 - len(bits) % 8)
    data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        data.append(byte)
    return data.decode('utf-8', errors='replace')

def bits_to_hex(bits):
    if len(bits) % 8:
        bits = bits + [0] * (8 - len(bits) % 8)
    result = ''
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        result += format(byte, '02x')
    return result

def hex_to_bits(hex_str):
    bits = []
    for ch in hex_str:
        val = int(ch, 16)
        for i in range(4):
            bits.append((val >> (3 - i)) & 1)
    return bits

def bits_to_binstr(bits):
    return ''.join(map(str, bits))

def frame_to_bits(frame_int):
    return int_to_bits(frame_int, 22)

def key_bits_to_hex(key_bits):
    return bits_to_hex(key_bits)


# ── Форматированный вывод ──────────────────────────────────────────────────────

def print_key_table(table, used_letters, key_bits):
    print(f"\n  Ключевое слово: {''.join(used_letters)}")
    if len(used_letters) < LETTERS_NEEDED:
        print(f"  ⚠ Слово короче {LETTERS_NEEDED} букв — ключ дополнен нулями.")
    print(f"\n  {'Буква':^7} {'Индекс':^8} {'8-битное представление':^24}")
    print("  " + "─" * 42)
    for ch, idx, bstr in table:
        print(f"  {ch:^7} {idx:^8} {bstr:^24}")
    if len(used_letters) < LETTERS_NEEDED:
        for _ in range(LETTERS_NEEDED - len(used_letters)):
            print(f"  {'(0)':^7} {'0':^8} {'00000000':^24}")
    print(f"\n  Ключ (64 бита): {bits_to_binstr(key_bits)}")
    print(f"  Ключ (HEX):     {key_bits_to_hex(key_bits)}")


def print_result(key_bits, frame_bits, cipher_bits,
                 key_word='', decrypted_text=None, is_decrypt=False):
    print(f"\nАлгоритм: А5/2")
    print(f"Ключевое слово: {key_word}")
    print(f"Ключ (двоичный): {bits_to_binstr(key_bits)}")
    print(f"Ключ (шестнадцатеричный): {key_bits_to_hex(key_bits)}")
    print(f"Номер кадра: {bits_to_binstr(frame_bits)}")
    print(f"Шифротекст (двоичный): {bits_to_binstr(cipher_bits)}")
    print(f"Шифротекст (шестнадцатеричный): {bits_to_hex(cipher_bits)}")
    if not is_decrypt:
        print(f"=== СОХРАНИТЕ ЭТУ ИНФОРМАЦИЮ ДЛЯ РАСШИФРОВКИ ===")
    print()
    if decrypted_text is not None:
        if not is_decrypt:
            print(f"Проверка пройдена: при расшифровании получается исходный текст.")
        print(f"Расшифрованный текст: {decrypted_text}")


# ── Ввод ────────────────────────────────────────────────────────────────────────

def input_key_word():
    print(f"\n  Алфавит ключа: А=1, Б=2, ..., Я=32  (без Ё)")
    print(f"  Используется до {LETTERS_NEEDED} букв × 8 бит = 64-битный ключ Kc")

    while True:
        word = input("  Введите ключевое слово (русские буквы): ").strip()
        if not word:
            print("  ✗ Слово не введено.")
            continue
        try:
            key_bits, table, used = word_to_key_bits(word)
        except ValueError as e:
            print(f"  ✗ {e}")
            continue

        print_key_table(table, used, key_bits)
        return key_bits, ''.join(used)


def input_frame():
    while True:
        f = input("  Введите номер кадра (0..4194303, Enter = 0): ").strip()
        if f == '':
            return 0
        try:
            n = int(f)
            if 0 <= n <= 4194303:
                return n
            print("  ✗ Число вне диапазона 0..4194303")
        except ValueError:
            print("  ✗ Введите целое число")


# ── Режимы ─────────────────────────────────────────────────────────────────────

def encrypt_mode():
    print("\n" + "─" * 65)
    print(" ШИФРОВАНИЕ (А5/2)")
    print("─" * 65)

    text = input("  Введите текст для шифрования: ").strip()
    if not text:
        print("  ✗ Пустой текст!"); return

    key_bits, key_word = input_key_word()
    frame_int  = input_frame()
    frame_bits = frame_to_bits(frame_int)
    plain_bits = text_to_bits(text)

    c = A5_2()
    cipher_bits = c.encrypt(plain_bits, key_bits, frame_bits)

    d = A5_2()
    dec_bits = d.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text = bits_to_text(dec_bits)

    print()
    print_result(key_bits, frame_bits, cipher_bits,
                 key_word=key_word, decrypted_text=dec_text, is_decrypt=False)


def decrypt_mode():
    print("\n" + "─" * 65)
    print(" РАСШИФРОВАНИЕ (А5/2)")
    print("─" * 65)

    cipher_hex = input("  Введите шифротекст (HEX): ").strip().lower()
    if not cipher_hex:
        print("  ✗ Пустое поле!"); return
    try:
        int(cipher_hex, 16)
    except ValueError:
        print("  ✗ Неверный HEX-формат"); return

    key_bits, key_word = input_key_word()
    frame_int   = input_frame()
    frame_bits  = frame_to_bits(frame_int)
    cipher_bits = hex_to_bits(cipher_hex)

    d = A5_2()
    dec_bits = d.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text = bits_to_text(dec_bits)

    print()
    print_result(key_bits, frame_bits, cipher_bits,
                 key_word=key_word, decrypted_text=dec_text, is_decrypt=True)


# ── Главное меню ────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print(" АЛГОРИТМ А5/2 — Экспортный поточный шифр GSM")
    print(" Ключ Kc: слово → индексы букв → 64 бита")
    print(" Номер кадра: 22 бита")
    print("=" * 65)
    print(f" Алфавит: {''.join(KEY_ALPHABET[:16])}")
    print(f"          {''.join(KEY_ALPHABET[16:])}")
    print(f" Кодировка: А=1, Б=2, ..., Я=32")
    print(f" Каждая буква → 8 бит | 8 букв → 64-битный ключ")
    print()
    print(" Структура А5/2:")
    print("   R1 (19 бит) ─┐")
    print("   R2 (22 бита) ─┼─ XOR + majority(буст-биты) → выход")
    print("   R3 (23 бита) ─┘")
    print("   R4 (17 бит)  — управляющий, всегда тактируется")

    while True:
        print("\n" + "─" * 65)
        print("МЕНЮ")
        print("─" * 65)
        print("1 — Зашифровать текст")
        print("2 — Расшифровать шифротекст (HEX)")
        print("0 — Выход")

        choice = input("\nВаш выбор: ").strip()
        if choice == '1':
            encrypt_mode()
        elif choice == '2':
            decrypt_mode()
        elif choice == '0':
            print("До свидания!")
            break
        else:
            print(" ⚠ Неверный выбор")


if __name__ == "__main__":
    main()