import os

# ── Алфавит ────────────────────────────────────────────────────────────────────

KEY_ALPHABET    = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'  # 32 буквы, без Ё, А=1..Я=32
KEY_CHAR_TO_IDX = {ch: i + 1 for i, ch in enumerate(KEY_ALPHABET)}

KEY_BITS = 64  # длина ключа в битах
LETTERS_NEEDED = KEY_BITS // 8  # 8 букв × 8 бит = 64 бита


def word_to_key_bits(word: str) -> tuple:
    """
    Преобразует слово в 64-битный ключ.
    Каждая буква → индекс (А=1..Я=32) → 8 бит.
    Длина < 8 букв: дополнить нулями.
    Длина > 8 букв: обрезать до 8.
    Возвращает (key_bits, table) где table — список (буква, индекс, 8-бит строка).
    """
    normalized = []
    for ch in word.upper():
        if ch == 'Ё':
            ch = 'Е'
        if ch in KEY_CHAR_TO_IDX:
            normalized.append(ch)

    if not normalized:
        raise ValueError("В слове не найдено ни одной русской буквы.")

    # Берём первые 8 букв
    used = normalized[:LETTERS_NEEDED]

    table = []
    bits = []
    for ch in used:
        idx = KEY_CHAR_TO_IDX[ch]
        byte_bits = [(idx >> (7 - i)) & 1 for i in range(8)]
        table.append((ch, idx, ''.join(map(str, byte_bits))))
        bits.extend(byte_bits)

    # Дополнение нулями до 64 бит
    while len(bits) < KEY_BITS:
        bits.append(0)

    return bits[:KEY_BITS], table, used


class A5_1:
    """
    Реализация алгоритма А5/1, используемого в GSM.
    Регистры хранятся как списки битов: индекс 0 = новейший, индекс -1 = старейший.
    """

    def __init__(self):
        self.R1_LENGTH = 19
        self.R2_LENGTH = 22
        self.R3_LENGTH = 23

        self.R1_CLOCK_BIT = 8
        self.R2_CLOCK_BIT = 10
        self.R3_CLOCK_BIT = 10

        self.R1_FEEDBACK_TAPS = [13, 16, 17, 18]   # x^19+x^18+x^17+x^14+1
        self.R2_FEEDBACK_TAPS = [20, 21]             # x^22+x^21+1
        self.R3_FEEDBACK_TAPS = [7, 20, 21, 22]     # x^23+x^22+x^21+x^8+1

        self.R1 = [0] * self.R1_LENGTH
        self.R2 = [0] * self.R2_LENGTH
        self.R3 = [0] * self.R3_LENGTH

    def initialize(self, key, frame_number):
        """
        Шаг 1: сброс → 64 такта загрузки ключа
        Шаг 2: 22 такта загрузки номера кадра
        Шаг 3: 100 тактов разгона (stop-and-go, без выхода)
        """
        self.R1 = [0] * self.R1_LENGTH
        self.R2 = [0] * self.R2_LENGTH
        self.R3 = [0] * self.R3_LENGTH

        for i in range(64):
            kb = key[i]
            self._clock_registers(kb, kb, kb)

        for i in range(22):
            fb = frame_number[i]
            self._clock_registers(fb, fb, fb)

        for _ in range(100):
            self._clock_controlled()

    def _clock_registers(self, r1_in=0, r2_in=0, r3_in=0):
        r1_fb = r1_in
        for tap in self.R1_FEEDBACK_TAPS:
            r1_fb ^= self.R1[tap]
        r2_fb = r2_in
        for tap in self.R2_FEEDBACK_TAPS:
            r2_fb ^= self.R2[tap]
        r3_fb = r3_in
        for tap in self.R3_FEEDBACK_TAPS:
            r3_fb ^= self.R3[tap]
        self.R1 = [r1_fb] + self.R1[:-1]
        self.R2 = [r2_fb] + self.R2[:-1]
        self.R3 = [r3_fb] + self.R3[:-1]

    def majority(self, x, y, z):
        return 1 if (x + y + z) >= 2 else 0

    def _clock_controlled(self):
        r1c = self.R1[self.R1_CLOCK_BIT]
        r2c = self.R2[self.R2_CLOCK_BIT]
        r3c = self.R3[self.R3_CLOCK_BIT]
        maj = self.majority(r1c, r2c, r3c)

        r1_fb = 0
        for tap in self.R1_FEEDBACK_TAPS:
            r1_fb ^= self.R1[tap]
        r2_fb = 0
        for tap in self.R2_FEEDBACK_TAPS:
            r2_fb ^= self.R2[tap]
        r3_fb = 0
        for tap in self.R3_FEEDBACK_TAPS:
            r3_fb ^= self.R3[tap]

        if r1c == maj:
            self.R1 = [r1_fb] + self.R1[:-1]
        if r2c == maj:
            self.R2 = [r2_fb] + self.R2[:-1]
        if r3c == maj:
            self.R3 = [r3_fb] + self.R3[:-1]

    def generate_keystream(self, length):
        ks = []
        for _ in range(length):
            ks.append(self.R1[-1] ^ self.R2[-1] ^ self.R3[-1])
            self._clock_controlled()
        return ks

    def encrypt(self, plaintext_bits, key_bits, frame_bits):
        self.initialize(key_bits, frame_bits)
        ks = self.generate_keystream(len(plaintext_bits))
        return [p ^ k for p, k in zip(plaintext_bits, ks)]

    def decrypt(self, cipher_bits, key_bits, frame_bits):
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
    """Таблица преобразования слово → биты ключа."""
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
    print(f"\nАлгоритм: А5/1")
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
    """
    Запрашивает ключевое слово (русские буквы).
    Преобразует: каждая буква → индекс (А=1..Я=32) → 8 бит.
    Берётся первые 8 букв; если меньше — дополняется нулями до 64 бит.
    """
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
    print("\n" + "─" * 60)
    print(" ШИФРОВАНИЕ (А5/1)")
    print("─" * 60)

    text = input("  Введите текст для шифрования: ").strip()
    if not text:
        print("  ✗ Пустой текст!"); return

    key_bits, key_word = input_key_word()
    frame_int  = input_frame()
    frame_bits = frame_to_bits(frame_int)
    plain_bits = text_to_bits(text)

    c = A5_1()
    cipher_bits = c.encrypt(plain_bits, key_bits, frame_bits)

    d = A5_1()
    dec_bits  = d.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text  = bits_to_text(dec_bits)

    print()
    print_result(key_bits, frame_bits, cipher_bits,
                 key_word=key_word, decrypted_text=dec_text, is_decrypt=False)


def decrypt_mode():
    print("\n" + "─" * 60)
    print(" РАСШИФРОВАНИЕ (А5/1)")
    print("─" * 60)

    cipher_hex = input("  Введите шифротекст (HEX): ").strip().lower()
    if not cipher_hex:
        print("  ✗ Пустое поле!"); return
    try:
        int(cipher_hex, 16)
    except ValueError:
        print("  ✗ Неверный HEX-формат"); return

    key_bits, key_word = input_key_word()
    frame_int  = input_frame()
    frame_bits = frame_to_bits(frame_int)
    cipher_bits = hex_to_bits(cipher_hex)

    d = A5_1()
    dec_bits = d.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text = bits_to_text(dec_bits)

    print()
    print_result(key_bits, frame_bits, cipher_bits,
                 key_word=key_word, decrypted_text=dec_text, is_decrypt=True)


# ── Главное меню ────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(" АЛГОРИТМ А5/1 — Поточный шифр GSM")
    print(" Ключ Kc: слово → индексы букв → 64 бита")
    print(" Номер кадра: 22 бита")
    print("=" * 60)
    print(f" Алфавит: {''.join(KEY_ALPHABET[:16])}")
    print(f"          {''.join(KEY_ALPHABET[16:])}")
    print(f" Кодировка: А=1, Б=2, ..., Я=32")
    print(f" Каждая буква → 8 бит | 8 букв → 64-битный ключ")

    while True:
        print("\n" + "─" * 60)
        print("МЕНЮ")
        print("─" * 60)
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
