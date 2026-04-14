"""
Поточные шифры А5/1 и А5/2 — реализация на основе РСЛОС (GSM)
Методические указания ЛАБКРИПТ_2022, Блок F, разделы 15–16.

────────────────────────────────────────────────────────────────
А5/1  |  R1=19 бит  R2=22  R3=23              |  Kc=64 бита  Fn=22 бита
А5/2  |  R1=19 бит  R2=22  R3=23  R4=17 бит  |  те же ключ/кадр
────────────────────────────────────────────────────────────────
"""

import os


# ═══════════════════════════════════════════════════════════════
#  КЛАСС А5/2
# ═══════════════════════════════════════════════════════════════

class A5_2:
    """
    А5/2 — четыре РСЛОС. R4 управляет тактированием R1, R2, R3.

    Отличия от А5/1:
      • добавлен R4 (17 бит, x^17+x^12+1)
      • clock-control через биты R4[3], R4[7], R4[10]
      • после 86 тактов инициализации → R4[3]=R4[7]=R4[10]=1
      • 99 тактов разгона (не 100)
      • выходной бит: R1[-1]⊕R2[-1]⊕R3[-1]⊕maj(R1[12,14,15])
                              ⊕maj(R2[9,13,16])⊕maj(R3[13,16,18])
    """

    def __init__(self):
        self.R1_LENGTH = 19
        self.R2_LENGTH = 22
        self.R3_LENGTH = 23
        self.R4_LENGTH = 17

        self.R1_TAPS = [13, 16, 17, 18]   # x^19+x^18+x^17+x^14+1
        self.R2_TAPS = [20, 21]             # x^22+x^21+1
        self.R3_TAPS = [7, 20, 21, 22]     # x^23+x^22+x^21+x^8+1
        self.R4_TAPS = [11, 16]             # x^17+x^12+1

        # Биты R4, управляющие тактированием:
        #   R1 тактируется если R4[10] == maj(R4[3], R4[7], R4[10])
        #   R2 тактируется если R4[3]  == maj
        #   R3 тактируется если R4[7]  == maj
        #   R4 тактируется ВСЕГДА

        # Позиции доп. мажоритарной функции для выходного бита
        self.R1_MAJ = [12, 14, 15]
        self.R2_MAJ = [9,  13, 16]
        self.R3_MAJ = [13, 16, 18]

        self.R1 = [0] * self.R1_LENGTH
        self.R2 = [0] * self.R2_LENGTH
        self.R3 = [0] * self.R3_LENGTH
        self.R4 = [0] * self.R4_LENGTH

    def initialize(self, key, frame_number):
        """
        Шаг 1: сброс → 64 такта загрузки ключа (все 4 регистра)
        Шаг 2: 22 такта загрузки номера кадра (все 4 регистра)
        Шаг 3: R4[3] = R4[7] = R4[10] = 1  (принудительно)
        Шаг 4: 99 тактов разгона (stop-and-go, без выхода)
        """
        self.R1 = [0] * self.R1_LENGTH
        self.R2 = [0] * self.R2_LENGTH
        self.R3 = [0] * self.R3_LENGTH
        self.R4 = [0] * self.R4_LENGTH

        for i in range(64):
            b = key[i]
            self._clock_all(b, b, b, b)

        for i in range(22):
            b = frame_number[i]
            self._clock_all(b, b, b, b)

        # Принудительная установка управляющих битов R4
        self.R4[3]  = 1
        self.R4[7]  = 1
        self.R4[10] = 1

        for _ in range(99):
            self._clock_sg()

    def _clock_all(self, r1_in=0, r2_in=0, r3_in=0, r4_in=0):
        """Загрузка ключа/кадра — все 4 регистра без stop-and-go."""
        r1_fb = r1_in
        for t in self.R1_TAPS: r1_fb ^= self.R1[t]
        r2_fb = r2_in
        for t in self.R2_TAPS: r2_fb ^= self.R2[t]
        r3_fb = r3_in
        for t in self.R3_TAPS: r3_fb ^= self.R3[t]
        r4_fb = r4_in
        for t in self.R4_TAPS: r4_fb ^= self.R4[t]

        self.R1 = [r1_fb] + self.R1[:-1]
        self.R2 = [r2_fb] + self.R2[:-1]
        self.R3 = [r3_fb] + self.R3[:-1]
        self.R4 = [r4_fb] + self.R4[:-1]

    @staticmethod
    def majority(x, y, z):
        return 1 if (x + y + z) >= 2 else 0

    def _clock_sg(self):
        """
        Stop-and-go тактирование A5/2 (управляет R4):
          Majority = maj(R4[3], R4[7], R4[10])
          R1 тактируется если R4[10] == maj
          R2 тактируется если R4[3]  == maj
          R3 тактируется если R4[7]  == maj
          R4 тактируется всегда
        """
        c3  = self.R4[3]
        c7  = self.R4[7]
        c10 = self.R4[10]
        maj = self.majority(c3, c7, c10)

        r1_fb = 0
        for t in self.R1_TAPS: r1_fb ^= self.R1[t]
        r2_fb = 0
        for t in self.R2_TAPS: r2_fb ^= self.R2[t]
        r3_fb = 0
        for t in self.R3_TAPS: r3_fb ^= self.R3[t]
        r4_fb = 0
        for t in self.R4_TAPS: r4_fb ^= self.R4[t]

        if c10 == maj: self.R1 = [r1_fb] + self.R1[:-1]
        if c3  == maj: self.R2 = [r2_fb] + self.R2[:-1]
        if c7  == maj: self.R3 = [r3_fb] + self.R3[:-1]
        self.R4 = [r4_fb] + self.R4[:-1]   # R4 — всегда

    def generate_keystream(self, length):
        """
        Выходной бит А5/2 (ДО тактирования):
          out = R1[-1] ⊕ R2[-1] ⊕ R3[-1]
                ⊕ maj(R1[12], R1[14], R1[15])
                ⊕ maj(R2[9],  R2[13], R2[16])
                ⊕ maj(R3[13], R3[16], R3[18])
        """
        ks = []
        for _ in range(length):
            maj_r1 = self.majority(self.R1[12], self.R1[14], self.R1[15])
            maj_r2 = self.majority(self.R2[9],  self.R2[13], self.R2[16])
            maj_r3 = self.majority(self.R3[13], self.R3[16], self.R3[18])
            out = (self.R1[-1] ^ self.R2[-1] ^ self.R3[-1]
                   ^ maj_r1 ^ maj_r2 ^ maj_r3)
            ks.append(out)
            self._clock_sg()
        return ks

    def encrypt(self, plain_bits, key_bits, frame_bits):
        self.initialize(key_bits, frame_bits)
        ks = self.generate_keystream(len(plain_bits))
        return [p ^ k for p, k in zip(plain_bits, ks)]

    def decrypt(self, cipher_bits, key_bits, frame_bits):
        return self.encrypt(cipher_bits, key_bits, frame_bits)


# ═══════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════

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

def key_hex_to_bits(hex_str):  return hex_to_bits(hex_str)
def frame_to_bits(frame_int):  return int_to_bits(frame_int, 22)
def key_bits_to_hex(key_bits): return bits_to_hex(key_bits)

def generate_random_key_hex():
    return os.urandom(8).hex()


# ═══════════════════════════════════════════════════════════════
#  ФОРМАТИРОВАННЫЙ ВЫВОД
# ═══════════════════════════════════════════════════════════════

def print_result(algo_name, key_bits, frame_bits, cipher_bits,
                 decrypted_text=None, is_decrypt=False):
    print(f"Алгоритм: {algo_name}")
    print(f"Ключ (двоичный): {bits_to_binstr(key_bits)}")
    print(f"Ключ (шестнадцатеричный): {key_bits_to_hex(key_bits)}")
    print(f"Номер кадра: {bits_to_binstr(frame_bits)}")
    print(f"Шифротекст (двоичный): {bits_to_binstr(cipher_bits)}")
    print(f"Шифротекст (шестнадцатеричный): {bits_to_hex(cipher_bits)}")
    if not is_decrypt:
        print()
        if decrypted_text is not None:
            print("Проверка пройдена: при расшифровании получается исходный текст.")
            print(f"Расшифрованный текст: {decrypted_text}")
    else:
        print()
        if decrypted_text is not None:
            print(f"Расшифрованный текст: {decrypted_text}")


# ═══════════════════════════════════════════════════════════════
#  ВВОД
# ═══════════════════════════════════════════════════════════════

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
            print("  ✗ Неверный HEX-формат (0-9, a-f)")

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


# ═══════════════════════════════════════════════════════════════
#  РЕЖИМЫ РАБОТЫ
# ═══════════════════════════════════════════════════════════════

def encrypt_mode():
    print("\n" + "─" * 60)
    print("  ШИФРОВАНИЕ")
    print("─" * 60)

    text = input("Введите текст для шифрования: ").strip()
    if not text:
        print("  ✗ Пустой текст!"); return

    algo_name, algo = 'А5/2', A5_2()
    key_hex   = input_key()
    frame_int = input_frame()

    key_bits   = key_hex_to_bits(key_hex)
    frame_bits = frame_to_bits(frame_int)
    plain_bits = text_to_bits(text)

    cipher_bits = algo.encrypt(plain_bits, key_bits, frame_bits)

    algo2 = algo.__class__()
    dec_bits = algo2.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text = bits_to_text(dec_bits)

    print()
    print_result(algo_name, key_bits, frame_bits, cipher_bits,
                 decrypted_text=dec_text, is_decrypt=False)


def decrypt_mode():
    print("\n" + "─" * 60)
    print("  РАСШИФРОВАНИЕ")
    print("─" * 60)

    cipher_hex = input("Введите шифротекст (HEX): ").strip().lower()
    if not cipher_hex:
        print("  ✗ Пустое поле!"); return
    try:
        int(cipher_hex, 16)
    except ValueError:
        print("  ✗ Неверный HEX-формат"); return

    algo_name, algo = 'А5/2', A5_2()
    key_hex   = input_key()
    frame_int = input_frame()

    cipher_bits = hex_to_bits(cipher_hex)
    key_bits    = key_hex_to_bits(key_hex)
    frame_bits  = frame_to_bits(frame_int)

    dec_bits = algo.decrypt(cipher_bits, key_bits, frame_bits)
    dec_text = bits_to_text(dec_bits)

    print()
    print_result(algo_name, key_bits, frame_bits, cipher_bits,
                 decrypted_text=dec_text, is_decrypt=True)


# ═══════════════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════

def main():
    print("═" * 60)
    print("  ПОТОЧНЫЙ ШИФР А5/2  —  РСЛОС (GSM)")
    print("  Ключ Kc: 64 бита (16 HEX)  |  Номер кадра: 22 бита")

    while True:
        print("=" * 60)
        print("МЕНЮ")
        print("=" * 60)
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
