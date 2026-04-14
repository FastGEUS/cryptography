#!/usr/bin/env python3
"""
Шифрование/расшифрование русского текста (без Ё) — AES-128, режим CBC.
Полная реализация на чистом Python, без сторонних библиотек.

Алфавит (32 буквы, А=0 ... Я=31):
  А  Б  В  Г  Д  Е  Ж  З  И  Й  К  Л  М  Н  О  П
  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16
  Р  С  Т  У  Ф  Х  Ц  Ч  Ш  Щ  Ъ  Ы  Ь  Э  Ю  Я
  17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
"""

# ═══════════════════════════════════════════════════════════════
#  РУССКИЙ АЛФАВИТ
# ═══════════════════════════════════════════════════════════════

ALPHABET    = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
CHAR_TO_IDX = {ch: i for i, ch in enumerate(ALPHABET)}


def text_to_indices(text: str) -> list:
    """Текст → список индексов 0–31. Ё→Е, остальное игнорируется."""
    text = text.upper().replace("Ё", "Е")
    return [CHAR_TO_IDX[ch] + 1 for ch in text if ch in CHAR_TO_IDX]


def indices_to_text(indices: list) -> str:
    return "".join(ALPHABET[i - 1] for i in indices)


# ═══════════════════════════════════════════════════════════════
#  УПАКОВКА / РАСПАКОВКА БАЙТОВ
#  Первые 2 байта — длина данных (little-endian).
#  Дополнение до кратности 16 — байты 0x00 (вне диапазона 1–32, т.к. А=1...Я=32).
# ═══════════════════════════════════════════════════════════════

def pack(indices: list) -> bytes:
    n       = len(indices)
    header  = n.to_bytes(2, "little")
    body    = bytes(indices)
    payload = header + body
    rem     = len(payload) % 16
    if rem:
        payload += bytes([0x00] * (16 - rem))  # 0x00 вне диапазона 1–32
    return payload


def unpack(data: bytes) -> list:
    n = int.from_bytes(data[:2], "little")
    return list(data[2 : 2 + n])


# ═══════════════════════════════════════════════════════════════
#  S-BOX, INV S-BOX, RCON
# ═══════════════════════════════════════════════════════════════

S_BOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

INV_S_BOX = [0] * 256
for _i, _v in enumerate(S_BOX):
    INV_S_BOX[_v] = _i

RCON = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1B,0x36]


# ═══════════════════════════════════════════════════════════════
#  АРИФМЕТИКА В GF(2^8)
# ═══════════════════════════════════════════════════════════════

def xtime(a: int) -> int:
    return ((a << 1) ^ 0x1B) & 0xFF if (a & 0x80) else (a << 1) & 0xFF


def gf_mul(a: int, b: int) -> int:
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        a = xtime(a)
        b >>= 1
    return result


# ═══════════════════════════════════════════════════════════════
#  МАТРИЦА СОСТОЯНИЯ 4×4
# ═══════════════════════════════════════════════════════════════

def bytes_to_state(block: bytes) -> list:
    return [[block[r + 4*c] for c in range(4)] for r in range(4)]


def state_to_bytes(state: list) -> bytes:
    return bytes(state[r][c] for c in range(4) for r in range(4))


# ═══════════════════════════════════════════════════════════════
#  ОПЕРАЦИИ РАУНДА
# ═══════════════════════════════════════════════════════════════

def sub_bytes(s):
    return [[S_BOX[s[r][c]] for c in range(4)] for r in range(4)]

def inv_sub_bytes(s):
    return [[INV_S_BOX[s[r][c]] for c in range(4)] for r in range(4)]

def shift_rows(s):
    return [s[r][r:] + s[r][:r] for r in range(4)]

def inv_shift_rows(s):
    return [s[r][(4-r):] + s[r][:(4-r)] for r in range(4)]

def mix_columns(s):
    ns = [row[:] for row in s]
    for c in range(4):
        a = [s[r][c] for r in range(4)]
        ns[0][c] = gf_mul(2,a[0])^gf_mul(3,a[1])^a[2]       ^a[3]
        ns[1][c] = a[0]          ^gf_mul(2,a[1])^gf_mul(3,a[2])^a[3]
        ns[2][c] = a[0]          ^a[1]          ^gf_mul(2,a[2])^gf_mul(3,a[3])
        ns[3][c] = gf_mul(3,a[0])^a[1]          ^a[2]          ^gf_mul(2,a[3])
    return ns

def inv_mix_columns(s):
    ns = [row[:] for row in s]
    for c in range(4):
        a = [s[r][c] for r in range(4)]
        ns[0][c] = gf_mul(14,a[0])^gf_mul(11,a[1])^gf_mul(13,a[2])^gf_mul(9, a[3])
        ns[1][c] = gf_mul(9, a[0])^gf_mul(14,a[1])^gf_mul(11,a[2])^gf_mul(13,a[3])
        ns[2][c] = gf_mul(13,a[0])^gf_mul(9, a[1])^gf_mul(14,a[2])^gf_mul(11,a[3])
        ns[3][c] = gf_mul(11,a[0])^gf_mul(13,a[1])^gf_mul(9, a[2])^gf_mul(14,a[3])
    return ns

def add_round_key(s, rk):
    return [[s[r][c] ^ rk[r][c] for c in range(4)] for r in range(4)]


# ═══════════════════════════════════════════════════════════════
#  РАСШИРЕНИЕ КЛЮЧА
# ═══════════════════════════════════════════════════════════════

def key_expansion(key: bytes) -> list:
    W = [list(key[4*i : 4*i+4]) for i in range(4)]
    for i in range(4, 44):
        temp = W[i-1][:]
        if i % 4 == 0:
            temp = [S_BOX[b] for b in temp[1:] + temp[:1]]
            temp[0] ^= RCON[i // 4 - 1]
        W.append([W[i-4][j] ^ temp[j] for j in range(4)])
    round_keys = []
    for rnd in range(11):
        rk = [[0]*4 for _ in range(4)]
        for c in range(4):
            for r in range(4):
                rk[r][c] = W[rnd*4 + c][r]
        round_keys.append(rk)
    return round_keys


# ═══════════════════════════════════════════════════════════════
#  ШИФРОВАНИЕ / РАСШИФРОВАНИЕ БЛОКА
# ═══════════════════════════════════════════════════════════════

def aes_encrypt_block(block: bytes, rks: list) -> bytes:
    s = bytes_to_state(block)
    s = add_round_key(s, rks[0])
    for i in range(1, 10):
        s = sub_bytes(s)
        s = shift_rows(s)
        s = mix_columns(s)
        s = add_round_key(s, rks[i])
    s = sub_bytes(s)
    s = shift_rows(s)
    s = add_round_key(s, rks[10])
    return state_to_bytes(s)


def aes_decrypt_block(block: bytes, rks: list) -> bytes:
    s = bytes_to_state(block)
    s = add_round_key(s, rks[10])
    for i in range(9, 0, -1):
        s = inv_shift_rows(s)
        s = inv_sub_bytes(s)
        s = add_round_key(s, rks[i])
        s = inv_mix_columns(s)
    s = inv_shift_rows(s)
    s = inv_sub_bytes(s)
    s = add_round_key(s, rks[0])
    return state_to_bytes(s)


# ═══════════════════════════════════════════════════════════════
#  РЕЖИМ CBC
# ═══════════════════════════════════════════════════════════════

def cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    rks = key_expansion(key)
    ct, prev = b"", iv
    for i in range(0, len(data), 16):
        block  = bytes(a ^ b for a, b in zip(data[i:i+16], prev))
        cipher = aes_encrypt_block(block, rks)
        ct    += cipher
        prev   = cipher
    return ct


def cbc_decrypt(ct: bytes, key: bytes, iv: bytes) -> bytes:
    rks = key_expansion(key)
    pt, prev = b"", iv
    for i in range(0, len(ct), 16):
        block = ct[i:i+16]
        plain = aes_decrypt_block(block, rks)
        pt   += bytes(a ^ b for a, b in zip(plain, prev))
        prev  = block
    return pt


# ═══════════════════════════════════════════════════════════════
#  ПУБЛИЧНЫЙ ИНТЕРФЕЙС
# ═══════════════════════════════════════════════════════════════

def encrypt(plaintext: str, key: bytes, iv: bytes):
    """Русский текст → шифртекст (bytes) + числовое представление."""
    indices    = text_to_indices(plaintext)
    ciphertext = cbc_encrypt(pack(indices), key, iv)
    return ciphertext, indices


def decrypt(ciphertext_hex: str, key: bytes, iv: bytes) -> str:
    """Шифртекст (hex-строка) → расшифрованный русский текст."""
    ct      = bytes.fromhex(ciphertext_hex)
    payload = cbc_decrypt(ct, key, iv)
    return indices_to_text(unpack(payload))


# ═══════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЙ ВВОД
# ═══════════════════════════════════════════════════════════════

def input_key() -> bytes:
    """Запрашивает ключ: ввод hex-строки или Enter для значения по умолчанию."""
    default = "2b7e151628aed2a6abf7158809cf4f3c"
    raw = input(f"  Ключ (32 hex-символа) [Enter = {default}]: ").strip()
    raw = raw if raw else default
    if len(raw) != 32 or not all(c in "0123456789abcdefABCDEF" for c in raw):
        print("  [!] Неверный формат ключа, используется значение по умолчанию.")
        raw = default
    return bytes.fromhex(raw)


def input_iv() -> bytes:
    """Запрашивает вектор инициализации IV."""
    default = "000102030405060708090a0b0c0d0e0f"
    raw = input(f"  IV  (32 hex-символа) [Enter = {default}]: ").strip()
    raw = raw if raw else default
    if len(raw) != 32 or not all(c in "0123456789abcdefABCDEF" for c in raw):
        print("  [!] Неверный формат IV, используется значение по умолчанию.")
        raw = default
    return bytes.fromhex(raw)


# ═══════════════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════

def menu_encrypt():
    print("\n--- ШИФРОВАНИЕ ---")
    text = input("  Введите текст (русский, без Ё): ").strip()
    if not text:
        print("  [!] Пустой ввод.")
        return
    key = input_key()
    iv  = input_iv()

    ct, indices = encrypt(text, key, iv)

    clean = "".join(ch for ch in text.upper().replace("Ё","Е") if ch in CHAR_TO_IDX)
    print(f"\n  Открытый текст  : {clean}")
    print(f"  Числовой вид    : {indices}")
    print(f"  Ключ            : {key.hex()}")
    print(f"  IV              : {iv.hex()}")
    print(f"  Шифртекст (hex) : {ct.hex()}")
    print(f"  Числа шифртекста: {list(ct)}")


def menu_decrypt():
    print("\n--- РАСШИФРОВАНИЕ ---")
    ct_hex = input("  Введите шифртекст (hex): ").strip()
    if not ct_hex:
        print("  [!] Пустой ввод.")
        return
    if len(ct_hex) % 32 != 0 or not all(c in "0123456789abcdefABCDEF" for c in ct_hex):
        print("  [!] Ошибка: шифртекст должен быть hex-строкой, кратной 32 символам.")
        return
    key = input_key()
    iv  = input_iv()

    try:
        result = decrypt(ct_hex, key, iv)
        print(f"\n  Шифртекст       : {ct_hex}")
        print(f"  Ключ            : {key.hex()}")
        print(f"  IV              : {iv.hex()}")
        print(f"  Расшифрованный  : {result}")
        print(f"  Числовой вид    : {text_to_indices(result)}")
    except Exception as e:
        print(f"  [!] Ошибка расшифрования: {e}")


def main():
    print("=" * 60)
    print("  AES-128 CBC | Русский алфавит без Ё | Pure Python")
    print("=" * 60)

    print("\nТаблица алфавита (А=0 ... Я=31):")
    for i, ch in enumerate(ALPHABET):
        print(f"  {ch}={i:2d}", end="  " if (i + 1) % 8 else "\n")

    while True:
        print("\n" + "─" * 60)
        print("  Выберите операцию:")
        print("  1 — Зашифровать текст")
        print("  2 — Расшифровать текст")
        print("  0 — Выход")
        print("─" * 60)

        choice = input("  Ваш выбор [0/1/2]: ").strip()

        if choice == "1":
            menu_encrypt()
        elif choice == "2":
            menu_decrypt()
        elif choice == "0":
            print("\n  Выход из программы.")
            break
        else:
            print("  [!] Неверный выбор. Введите 0, 1 или 2.")


if __name__ == "__main__":
    main()
