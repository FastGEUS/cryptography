#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
  МАГМА — Блочный шифр (64 бита)
  ГОСТ Р 34.12-2018 (раздел 5) + ГОСТ 28147-89
═══════════════════════════════════════════════════════════════════════════

  Структура алгоритма (ГОСТ Р 34.12-2018, формулы 14-20):
  ─────────────────────────────────────────────────────────
  t(a)         : замена по 8 S-блокам (формула 14)
  g[k](a)      : Rot₁₁( t( a ⊞ k mod 2³² ) ) (формула 15)
  G[k](a₁,a₀) : (a₀, g[k](a₀) ⊕ a₁) (формула 16)
  G*[k](a₁,a₀): (g[k](a₀) ⊕ a₁) ‖ a₀ (формула 17)

  Разворот ключа (формула 18):
    K₁–K₈ → повторяются трижды (раунды 1–24)
    K₈–K₁ → в обратном порядке (раунды 25–32)

  Шифрование (формула 19):
    E = G*[K₃₂] · G[K₃₁] · … · G[K₂] · G[K₁](a₁, a₀)

  Расшифрование (формула 20):
    D = G*[K₁] · G[K₂] · … · G[K₃₁] · G[K₃₂](b₁, b₀)

  Ввод:  русский текст (кодировка Windows-1251)
  Блок:  64 бита (8 байт) — сеть Фейстеля
  Ключ:  256 бит (32 байта, 64 HEX-символа)
  Режим: ECB (простая замена)
"""

# ═══════════════════════════════════════════════════════════════════════════
# 1. S-БЛОКИ  (ГОСТ Р 34.12-2018, раздел 5.1.1)
# ═══════════════════════════════════════════════════════════════════════════

PI = [
    [12,  4,  6,  2, 10,  5, 11,  9, 14,  8, 13,  7,  0,  3, 15,  1],  # π₀
    [ 6,  8,  2,  3,  9, 10,  5, 12,  1, 14,  4,  7, 11, 13,  0, 15],  # π₁
    [11,  3,  5,  8,  2, 15, 10, 13, 14,  1,  7,  4, 12,  9,  6,  0],  # π₂
    [12,  8,  2,  1, 13,  4, 15,  6,  7,  0, 10,  5,  3, 14,  9, 11],  # π₃
    [ 7, 15,  5, 10,  8,  1,  6, 13,  0,  9,  3, 14, 11,  4,  2, 12],  # π₄
    [ 5, 13, 15,  6,  9,  2, 12, 10, 11,  7,  8,  1,  4,  3, 14,  0],  # π₅
    [ 8, 14,  2,  5,  6,  9,  1, 12, 15,  4, 11,  0, 13, 10,  3,  7],  # π₆
    [ 1,  7, 14, 13,  0,  5,  8,  3,  4, 15, 10,  6,  9, 12, 11,  2],  # π₇
]

# ═══════════════════════════════════════════════════════════════════════════
# 2. БАЗОВЫЕ ПРЕОБРАЗОВАНИЯ
# ═══════════════════════════════════════════════════════════════════════════

def t_transform(a: int) -> int:
    """
    Преобразование t: V₃₂ → V₃₂  (формула 14)
    32-битное слово разбивается на 8 тетрад по 4 бита.
    Каждая тетрада заменяется через свою строку S-блока.
    """
    result = 0
    for i in range(8):
        nibble = (a >> (4 * i)) & 0x0F      # извлекаем тетраду i
        result |= PI[i][nibble] << (4 * i)  # заменяем и ставим обратно
    return result


def rot11(v: int) -> int:
    """Циклический сдвиг 32-битного слова влево на 11 позиций."""
    v &= 0xFFFFFFFF
    return ((v << 11) | (v >> 21)) & 0xFFFFFFFF


def g_transform(k: int, a: int) -> int:
    """
    Преобразование g[k]: V₃₂ → V₃₂  (формула 15)
    g[k](a) = Rot₁₁( t( a ⊞ k mod 2³² ) )
    """
    return rot11(t_transform((a + k) & 0xFFFFFFFF))


def G_transform(k: int, a1: int, a0: int):
    """
    Преобразование G[k]: V₃₂ × V₃₂ → V₃₂ × V₃₂  (формула 16)
    G[k](a₁, a₀) = ( a₀,  g[k](a₀) ⊕ a₁ )
    Используется в раундах 1–31.
    """
    return a0, g_transform(k, a0) ^ a1


def G_star_transform(k: int, a1: int, a0: int):
    """
    Преобразование G*[k]: V₃₂ × V₃₂ → V₃₂ × V₃₂  (формула 17)
    G*[k](a₁, a₀) = ( g[k](a₀) ⊕ a₁,  a₀ )
    Используется только в финальном (32-м) раунде.
    Отличие от G: части НЕ переставляются (левая часть обновляется).
    """
    return g_transform(k, a0) ^ a1, a0

# ═══════════════════════════════════════════════════════════════════════════
# 3. РАЗВОРОТ КЛЮЧА
# ═══════════════════════════════════════════════════════════════════════════

def key_schedule(key_bytes: bytes) -> list:
    """
    Генерация 32 раундовых ключей из 256-битного ключа (формула 18).

    Ключ K = k₂₅₅…k₀ разбивается на 8 подключей K₁…K₈ по 32 бита:
      K₁ = k₂₅₅…k₂₂₄   (самые старшие 4 байта)
      K₂ = k₂₂₃…k₁₉₂
      …
      K₈ = k³¹…k⁰      (самые младшие 4 байта)

    Расписание:
      Раунды  1– 8 : K₁  K₂  K₃  K₄  K₅  K₆  K₇  K₈
      Раунды  9–16 : K₁  K₂  K₃  K₄  K₅  K₆  K₇  K₈  (повтор)
      Раунды 17–24 : K₁  K₂  K₃  K₄  K₅  K₆  K₇  K₈  (повтор)
      Раунды 25–32 : K₈  K₇  K₆  K₅  K₄  K₃  K₂  K₁  (обратный порядок)
    """
    if len(key_bytes) != 32:
        raise ValueError("Ключ должен быть 32 байта (256 бит).")
    # Разбиваем ключ на 8 подключей; ГОСТ использует big-endian
    K = [int.from_bytes(key_bytes[i*4:(i+1)*4], 'big') for i in range(8)]
    return K * 3 + list(reversed(K))  # 24 + 8 = 32 ключа

# ═══════════════════════════════════════════════════════════════════════════
# 4. ШИФРОВАНИЕ / РАСШИФРОВАНИЕ ОДНОГО БЛОКА
# ═══════════════════════════════════════════════════════════════════════════

def _split_block(block8: bytes):
    """
    Разбиваем 8 байт на (a1, a0) согласно ГОСТ Р 34.12-2018:
      a = a₁ ‖ a₀, где a₁ — старшие (левые) 32 бита, a₀ — младшие (правые).
    Используем big-endian — совпадает с нотацией стандарта и его тест-векторами.
    """
    a1 = int.from_bytes(block8[0:4], 'big')   # a₁ — старшие 32 бита
    a0 = int.from_bytes(block8[4:8], 'big')   # a₀ — младшие 32 бита
    return a1, a0


def _merge_block(b1: int, b0: int) -> bytes:
    """Собираем блок обратно: b = b₁ ‖ b₀ (big-endian)."""
    return b1.to_bytes(4, 'big') + b0.to_bytes(4, 'big')


def magma_encrypt_block(block8: bytes, rk: list) -> bytes:
    """
    Шифрование одного 64-битного блока (формула 19):
    E(K, a) = G*[K₃₂] · G[K₃₁] · … · G[K₂] · G[K₁](a₁, a₀)

    Раунды 1–31 — преобразование G (Фейстель со сменой сторон).
    Раунд 32    — преобразование G* (без смены сторон).
    """
    a1, a0 = _split_block(block8)
    for i in range(31):                        # раунды 1–31
        a1, a0 = G_transform(rk[i], a1, a0)
    b1, b0 = G_star_transform(rk[31], a1, a0) # раунд 32
    return _merge_block(b1, b0)


def magma_decrypt_block(block8: bytes, rk: list) -> bytes:
    """
    Расшифрование одного 64-битного блока (формула 20):
    D(K, b) = G*[K₁] · G[K₂] · … · G[K₃₁] · G[K₃₂](b₁, b₀)

    Ключи применяются в ОБРАТНОМ порядке (K₃₂ → K₁).
    Раунды 1–31 — G, финальный — G*.
    """
    a1, a0 = _split_block(block8)
    for i in range(31, 0, -1):                 # ключи K₃₂…K₂
        a1, a0 = G_transform(rk[i], a1, a0)
    b1, b0 = G_star_transform(rk[0], a1, a0)  # финальный G* с K₁
    return _merge_block(b1, b0)

# ═══════════════════════════════════════════════════════════════════════════
# 5. РЕЖИМ ECB — РАБОТА С ПРОИЗВОЛЬНЫМ ТЕКСТОМ
# ═══════════════════════════════════════════════════════════════════════════

def _pkcs5_pad(data: bytes) -> bytes:
    """PKCS#5-дополнение до кратности 8 байт."""
    pad = 8 - (len(data) % 8)
    return data + bytes([pad] * pad)


def _pkcs5_unpad(data: bytes) -> bytes:
    """Удаление PKCS#5-дополнения."""
    if not data:
        return data
    pad = data[-1]
    if 1 <= pad <= 8 and data[-pad:] == bytes([pad] * pad):
        return data[:-pad]
    return data   # дополнение не найдено — возвращаем как есть


def magma_ecb_encrypt(plaintext: str, key_hex: str, verbose: bool = False) -> str:
    """
    Шифрование строки в режиме ECB.
    Текст → Windows-1251 → дополнение → 64-бит блоки → МАГМА → HEX.
    Возвращает шифртекст в виде HEX-строки.
    """
    key_bytes = bytes.fromhex(key_hex)
    rk = key_schedule(key_bytes)

    data = plaintext.encode('windows-1251', errors='replace')
    data = _pkcs5_pad(data)

    if verbose:
        print(f"  Ключ (256 бит)   : {key_hex.upper()}")
        print(f"  Раундовые ключи  :")
        for i in range(0, 32, 8):
            row = "  ".join(f"K{i+j+1:02d}={rk[i+j]:08X}" for j in range(8))
            print(f"    {row}")
        print(f"  Блоков           : {len(data)//8}")
        print(f"  {'─'*66}")

    ciphertext = bytearray()
    for i in range(0, len(data), 8):
        block = data[i:i+8]
        enc   = magma_encrypt_block(block, rk)
        ciphertext.extend(enc)

        if verbose:
            print(f"  Блок {i//8 + 1:2d} | PT: {block.hex().upper()}"
                  f"  →  CT: {enc.hex().upper()}")

    return ciphertext.hex().upper()


def magma_ecb_decrypt(ciphertext_hex: str, key_hex: str, verbose: bool = False) -> str:
    """
    Расшифрование HEX-строки в режиме ECB.
    HEX → 64-бит блоки → МАГМА (обратный порядок ключей) → Windows-1251 → строка.
    """
    key_bytes = bytes.fromhex(key_hex)
    rk = key_schedule(key_bytes)

    try:
        data = bytes.fromhex(ciphertext_hex.replace(' ', ''))
    except ValueError:
        return "Ошибка: неверный HEX-формат шифртекста."

    if len(data) % 8 != 0:
        return "Ошибка: длина шифртекста должна быть кратна 8 байтам."

    if verbose:
        print(f"  Ключ (256 бит)   : {key_hex.upper()}")
        print(f"  Блоков           : {len(data)//8}")
        print(f"  {'─'*66}")

    plaintext_bytes = bytearray()
    for i in range(0, len(data), 8):
        block = data[i:i+8]
        dec   = magma_decrypt_block(block, rk)
        plaintext_bytes.extend(dec)

        if verbose:
            print(f"  Блок {i//8 + 1:2d} | CT: {block.hex().upper()}"
                  f"  →  PT: {dec.hex().upper()}")

    plaintext_bytes = _pkcs5_unpad(bytes(plaintext_bytes))
    try:
        return plaintext_bytes.decode('windows-1251', errors='replace')
    except Exception:
        return plaintext_bytes.decode('latin-1', errors='replace')

# ═══════════════════════════════════════════════════════════════════════════
# 6. САМОТЕСТИРОВАНИЕ — КОНТРОЛЬНЫЙ ПРИМЕР ИЗ ГОСТ Р 34.12-2018, ПР. А.2
# ═══════════════════════════════════════════════════════════════════════════

def run_self_test() -> bool:
    """
    Контрольный пример А.2 из ГОСТ Р 34.12-2018:
      Ключ : ffeeddccbbaa9988 7766554433221100 f0f1f2f3f4f5f6f7 f8f9fafbfcfdfeff
      Вход : fedcba9876543210
      Выход: 4ee901e5c2d8ca3d
    """
    K = "ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    a = bytes.fromhex("fedcba9876543210")
    expected_enc = bytes.fromhex("4ee901e5c2d8ca3d")

    rk = key_schedule(bytes.fromhex(K))

    # Проверяем раундовые ключи (приложение А.2.3)
    expected_rk = [
        0xffeeddcc, 0xbbaa9988, 0x77665544, 0x33221100,
        0xf0f1f2f3, 0xf4f5f6f7, 0xf8f9fafb, 0xfcfdfeff,
    ]
    for i in range(3):
        if rk[i*8:(i+1)*8] != expected_rk:
            return False
    if rk[24:32] != list(reversed(expected_rk)):
        return False

    enc = magma_encrypt_block(a, rk)
    if enc != expected_enc:
        return False

    dec = magma_decrypt_block(enc, rk)
    return dec == a

# ═══════════════════════════════════════════════════════════════════════════
# 7. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_KEY = "ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"

BANNER = """
╔══════════════════════════════════════════════════════════════════════════╗
║         МАГМА — блочный шифр 64 бита (ГОСТ Р 34.12-2018)               ║
║         Реализация: чистый Python, без сторонних библиотек              ║
║                                                                          ║
║  Параметры:  блок = 64 бит · ключ = 256 бит · 32 раунда Фейстеля       ║
║  Режим:      ECB (простая замена по блокам)                              ║
║  Кодировка:  Windows-1251 (Кириллица), Ё → Е не заменяется              ║
╚══════════════════════════════════════════════════════════════════════════╝"""


def print_menu():
    print("\n" + "─" * 74)
    print("  Главное меню")
    print("─" * 74)
    print("  1 — Зашифровать текст")
    print("  2 — Расшифровать текст")
    print("  3 — Контрольный пример (ГОСТ Р 34.12-2018, приложение А.2)")
    print("  0 — Выход")
    print("─" * 74)


def ask_key() -> str:
    """Запрашивает 256-битный ключ; Enter = тестовый ключ ГОСТ."""
    while True:
        raw = input(f"  Ключ (64 HEX, Enter = тестовый ГОСТ): ").strip()
        if not raw:
            print(f"  ✓ Используется тестовый ключ: {DEFAULT_KEY}")
            return DEFAULT_KEY
        raw = raw.replace(' ', '').lower()
        if len(raw) != 64:
            print(f"  ✗ Нужно ровно 64 HEX-символа (введено {len(raw)}). Повторите.")
            continue
        try:
            bytes.fromhex(raw)
            return raw
        except ValueError:
            print("  ✗ Неверные символы. Разрешены: 0-9, a-f.")


def ask_verbose() -> bool:
    ans = input("  Показать раундовые блоки? (д/н): ").strip().lower()
    return ans in ('д', 'да', 'y', 'yes', '1')

# ═══════════════════════════════════════════════════════════════════════════
# 8. ГЛАВНАЯ ПРОГРАММА
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(BANNER)

    # Самотест при запуске
    ok = run_self_test()
    status = "✓ ГОСТ-тест пройден" if ok else "✗ ОШИБКА САМОТЕСТА"
    print(f"\n  {status}")

    while True:
        print_menu()
        choice = input("  Ваш выбор: ").strip()

        # ── Шифрование ──────────────────────────────────────────────────────
        if choice == '1':
            print("\n  ═══ ШИФРОВАНИЕ ═══")
            text = input("  Введите текст: ")
            if not text:
                print("  ✗ Пустой текст.")
                continue

            key = ask_key()
            verbose = ask_verbose()

            print()
            ct = magma_ecb_encrypt(text, key, verbose=verbose)

            print("\n" + "═" * 74)
            print("  РЕЗУЛЬТАТ ШИФРОВАНИЯ")
            print("═" * 74)
            print(f"  Открытый текст : {text}")
            print(f"  Ключ           : {key.upper()}")
            print(f"  Шифртекст (HEX): {ct}")
            print(f"  Длина          : {len(ct)//2} байт ({len(ct)//2*8} бит, {len(ct)//16} блоков)")
            print("═" * 74)

        # ── Расшифрование ───────────────────────────────────────────────────
        elif choice == '2':
            print("\n  ═══ РАСШИФРОВАНИЕ ═══")
            ct_input = input("  Введите шифртекст (HEX): ").strip()
            if not ct_input:
                print("  ✗ Пустой шифртекст.")
                continue

            key = ask_key()
            verbose = ask_verbose()

            print()
            pt = magma_ecb_decrypt(ct_input, key, verbose=verbose)

            print("\n" + "═" * 74)
            print("  РЕЗУЛЬТАТ РАСШИФРОВАНИЯ")
            print("═" * 74)
            print(f"  Шифртекст (HEX): {ct_input.upper()}")
            print(f"  Ключ           : {key.upper()}")
            print(f"  Открытый текст : {pt}")
            print("═" * 74)

        # ── ГОСТ-тест ───────────────────────────────────────────────────────
        elif choice == '3':
            print("\n  ═══ КОНТРОЛЬНЫЙ ПРИМЕР (ГОСТ Р 34.12-2018, А.2) ═══")
            K  = "ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
            a  = bytes.fromhex("fedcba9876543210")
            rk = key_schedule(bytes.fromhex(K))

            print(f"  Ключ      : {K}")
            print()

            # Раундовые ключи
            print("  Раундовые ключи (формула 18):")
            for i in range(0, 32, 8):
                row = "  ".join(f"K{i+j+1:02d}={rk[i+j]:08X}" for j in range(8))
                print(f"    {row}")

            print()
            print(f"  Открытый текст a : {a.hex().upper()}")
            enc = magma_encrypt_block(a, rk)
            dec = magma_decrypt_block(enc, rk)

            exp = "4EE901E5C2D8CA3D"
            enc_ok = enc.hex().upper() == exp
            dec_ok = dec == a

            print(f"  Шифртекст b      : {enc.hex().upper()}")
            print(f"  Ожидается        : {exp}  {'✓' if enc_ok else '✗'}")
            print(f"  Расшифровано     : {dec.hex().upper()}")
            print(f"  Совпадает с a    : {'✓ ДА' if dec_ok else '✗ НЕТ'}")

        elif choice == '0':
            print("\n  До свидания!")
            break
        else:
            print("  ✗ Неверный выбор. Введите 0, 1, 2 или 3.")
