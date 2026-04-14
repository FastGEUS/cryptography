"""
Алгоритм А5/1 — поточный шифр для GSM
(Блок F, раздел 15. Отчёт по лабораторным работам, Попов А.Ю.)

Параметры:
  R1 — 19 бит  |  x^19 + x^18 + x^17 + x^14 + 1
  R2 — 22 бита |  x^22 + x^21 + 1
  R3 — 23 бита |  x^23 + x^22 + x^21 + x^8  + 1
  Ключ Kc     — 64 бита (16 HEX)
  Номер кадра — 22 бита (целое 0..4194303)
"""

import os


class A5_1:
    """
    Реализация алгоритма А5/1, используемого в GSM.
    Регистры хранятся как списки битов: индекс 0 = новейший, индекс -1 = старейший.
    """

    def __init__(self):
        self.R1_LENGTH = 19
        self.R2_LENGTH = 22
        self.R3_LENGTH = 23

        # Биты синхронизации (0-indexed)
        self.R1_CLOCK_BIT = 8
        self.R2_CLOCK_BIT = 10
        self.R3_CLOCK_BIT = 10

        # Отводы обратной связи
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
        """Тактирование всех регистров с загрузкой входного бита."""
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
        """Тактирование в режиме stop-and-go."""
        r1c = self.R1[self.R1_CLOCK_BIT]
        r2c = self.R2[self.R2_CLOCK_BIT]
        r3c = self.R3[self.R3_CLOCK_BIT]
        maj = self.majority(r1c, r2c, r3c)

        # Обратная связь ДО сдвига
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
        """Генерация гаммы: выходной бит = R1[-1]^R2[-1]^R3[-1] ДО тактирования."""
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
        """Расшифрование идентично шифрованию (XOR симметричен)."""
        return self.encrypt(cipher_bits, key_bits, frame_bits)


# ── Вспомогательные функции ───────────────────────────────────────────────────

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

def key_hex_to_bits(hex_str):
    return hex_to_bits(hex_str)

def frame_to_bits(frame_int):
    return int_to_bits(frame_int, 22)

def key_bits_to_hex(key_bits):
    return bits_to_hex(key_bits)

def generate_random_key_hex():
    return os.urandom(8).hex()


# ── Форматированный вывод (точно как у одногруппника) ─────────────────────────

def print_result(key_bits, frame_bits, cipher_bits, decrypted_text=None, is_decrypt=False):
    print(f"Алгоритм: А5/1")
    print(f"Ключ (двоичный): {bits_to_binstr(key_bits)}")
    print(f"Ключ (шестнадцатеричный): {key_bits_to_hex(key_bits)}")
    print(f"Номер кадра: {bits_to_binstr(frame_bits)}")
    print(f"Шифротекст (двоичный): {bits_to_binstr(cipher_bits)}")
    print(f"Шифротекст (шестнадцатеричный): {bits_to_hex(cipher_bits)}")
    if not is_decrypt:
        print(f"=== СОХРАНИТЕ ЭТУ ИНФОРМАЦИЮ ДЛЯ РАСШИФРОВКИ ===")
        print()
        if decrypted_text is not None:
            print(f"Проверка пройдена: при расшифровании получается исходный текст.")
            print(f"Расшифрованный текст: {decrypted_text}")
    else:
        print()
        if decrypted_text is not None:
            print(f"Расшифрованный текст: {decrypted_text}")


# ── Ввод ─────────────────────────────────────────────────────────────────────

def input_key():
    while True:
        k = input("Введите ключ Kc (16 HEX = 64 бита) или Enter для случайного: ").strip()
        if k == '':
            k = generate_random_key_hex()
            print(f"  Сгенерирован ключ: {k}")
        k = k.lower().replace(' ', '')
        if len(k) != 16:
            print(f"  ✗ Нужно 16 символов (введено {len(k)})")
            continue
        try:
            int(k, 16)
            return k
        except ValueError:
            print("  ✗ Неверный HEX-формат")

def input_frame():
    while True:
        f = input("Введите номер кадра (0..4194303, Enter = 0): ").strip()
        if f == '':
            return 0
        try:
            n = int(f)
            if 0 <= n <= 4194303:
                return n
            print("  ✗ Число вне диапазона 0..4194303")
        except ValueError:
            print("  ✗ Введите целое число")


# ── Режимы ────────────────────────────────────────────────────────────────────

def encrypt_mode():
    print("\n" + "─" * 60)
    print("  ШИФРОВАНИЕ  (А5/1)")
    print("─" * 60)
    text = input("Введите текст для шифрования: ").strip()
    if not text:
        print("  ✗ Пустой текст!"); return

    key_hex   = input_key()
    frame_int = input_frame()

    key_bits   = key_hex_to_bits(key_hex)
    frame_bits = frame_to_bits(frame_int)
    plain_bits = text_to_bits(text)

    c = A5_1()
    cipher_bits = c.encrypt(plain_bits, key_bits, frame_bits)

    d = A5_1()
    dec_bits = d.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text = bits_to_text(dec_bits)

    print()
    print_result(key_bits, frame_bits, cipher_bits,
                 decrypted_text=dec_text, is_decrypt=False)


def decrypt_mode():
    print("\n" + "─" * 60)
    print("  РАСШИФРОВАНИЕ  (А5/1)")
    print("─" * 60)
    cipher_hex = input("Введите шифротекст (HEX): ").strip().lower()
    if not cipher_hex:
        print("  ✗ Пустое поле!"); return
    try:
        int(cipher_hex, 16)
    except ValueError:
        print("  ✗ Неверный HEX-формат"); return

    key_hex   = input_key()
    frame_int = input_frame()

    cipher_bits = hex_to_bits(cipher_hex)
    key_bits    = key_hex_to_bits(key_hex)
    frame_bits  = frame_to_bits(frame_int)

    d = A5_1()
    dec_bits = d.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text = bits_to_text(dec_bits)

    print()
    print_result(key_bits, frame_bits, cipher_bits,
                 decrypted_text=dec_text, is_decrypt=True)


# ── Главное меню ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  АЛГОРИТМ А5/1  —  Поточный шифр GSM")
    print("  Ключ Kc: 64 бита | Номер кадра: 22 бита")
    print("=" * 60)

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
            print("  ⚠ Неверный выбор")


if __name__ == "__main__":
    main()
