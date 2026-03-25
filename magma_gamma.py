#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МАГМА (ГОСТ Р 34.12-2015) в режиме гаммирования CTR
ГОСТ Р 34.13-2015, Раздел A.2.2

Поддерживает длинный текст: блоки разделяются пробелом,
каждый блок — 16 HEX-символов (64 бита).
"""

# ── S-блоки ГОСТ Р 34.12-2015, раздел 5.1.1 ──────────────────────────────────

PI = [
    [12, 4,  6,  2, 10,  5, 11,  9, 14,  8, 13,  7,  0,  3, 15,  1],  # π0
    [ 6, 8,  2,  3,  9, 10,  5, 12,  1, 14,  4,  7, 11, 13,  0, 15],  # π1
    [11, 3,  5,  8,  2, 15, 10, 13, 14,  1,  7,  4, 12,  9,  6,  0],  # π2
    [12, 8,  2,  1, 13,  4, 15,  6,  7,  0, 10,  5,  3, 14,  9, 11],  # π3
    [ 7,15,  5, 10,  8,  1,  6, 13,  0,  9,  3, 14, 11,  4,  2, 12],  # π4
    [ 5,13, 15,  6,  9,  2, 12, 10, 11,  7,  8,  1,  4,  3, 14,  0],  # π5
    [ 8,14,  2,  5,  6,  9,  1, 12, 15,  4, 11,  0, 13, 10,  3,  7],  # π6
    [ 1, 7, 14, 13,  0,  5,  8,  3,  4, 15, 10,  6,  9, 12, 11,  2],  # π7
]


# ── Преобразования Магмы ──────────────────────────────────────────────────────

def t_transform(a):
    result = 0
    for i in range(8):
        result |= (PI[i][(a >> (4 * i)) & 0x0F] << (4 * i))
    return result

def rotate_left_11(value):
    value &= 0xFFFFFFFF
    return ((value << 11) | (value >> 21)) & 0xFFFFFFFF

def g_transform(k, a):
    return rotate_left_11(t_transform((a + k) & 0xFFFFFFFF))

def G_transform(k, a1, a0):
    return a0, g_transform(k, a0) ^ a1

def G_star_transform(k, a1, a0):
    return g_transform(k, a0) ^ a1, a0

def generate_round_keys(key_bytes):
    if len(key_bytes) != 32:
        raise ValueError("Ключ должен быть 32 байта (256 бит)")
    K = [int.from_bytes(key_bytes[i*4:(i+1)*4], 'big') for i in range(8)]
    return K * 3 + list(reversed(K))

def magma_encrypt_block(block_64bit, round_keys):
    a1 = (block_64bit >> 32) & 0xFFFFFFFF
    a0 =  block_64bit        & 0xFFFFFFFF
    for i in range(31):
        a1, a0 = G_transform(round_keys[i], a1, a0)
    b1, b0 = G_star_transform(round_keys[31], a1, a0)
    return (b1 << 32) | b0


# ── Вспомогательные функции ───────────────────────────────────────────────────

def pad_iv(iv_str):
    """Дополняет IV нулями справа до 16 HEX-символов (8 байт)"""
    iv_str = iv_str.strip().upper().replace(' ', '')
    if len(iv_str) > 16:
        print(f"  ⚠ IV обрезан до 16 символов")
        return iv_str[:16]
    if len(iv_str) < 16:
        iv_str = iv_str + '0' * (16 - len(iv_str))
        print(f"  ✓ IV дополнен нулями: {iv_str}")
    return iv_str


def parse_blocks(hex_input):
    """
    Разбирает строку с пробелами на список 8-байтных блоков.
    Каждый токен — 16 HEX-символов (64 бита).
    """
    tokens = hex_input.strip().split()
    blocks = []
    print(blocks)
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        if len(tok) % 2:
            tok = tok + '0'
        for i in range(0, len(tok), 16):
            chunk = tok[i:i+16].ljust(16, '0')
            blocks.append(bytes.fromhex(chunk))
    return blocks


# ── Режим CTR ─────────────────────────────────────────────────────────────────

def magma_ctr_process(blocks, key_bytes, iv_bytes, verbose=False):
    """
    Шифрование/расшифрование списка 64-битных блоков в режиме CTR.
    Возвращает (список результирующих блоков, список строк таблицы).
    """
    round_keys = generate_round_keys(key_bytes)
    counter    = int.from_bytes(iv_bytes, 'big')

    result_blocks = []
    table_rows    = []

    for i, data_block in enumerate(blocks):
        gamma_int   = magma_encrypt_block(counter, round_keys)
        gamma_bytes = gamma_int.to_bytes(8, 'big')[:len(data_block)]
        cipher_block = bytes(a ^ b for a, b in zip(data_block, gamma_bytes))
        result_blocks.append(cipher_block)

        # Безопасное HEX-форматирование счётчика через hex()
        ctr_hex = hex(counter)[2:].upper().zfill(16)

        table_rows.append({
            'i'       : i + 1,
            'P_i'     : data_block.hex().upper(),
            'counter' : ctr_hex,
            'gamma'   : gamma_bytes.hex().upper(),
            'C_i'     : cipher_block.hex().upper(),
        })

        if verbose:
            print(f"\n  Итерация {i+1}:")
            print(f"    P_{i+1}           : {data_block.hex().upper()}")
            print(f"    Входной блок   : {ctr_hex}")
            print(f"    Гамма E(CTR)   : {gamma_bytes.hex().upper()}")
            print(f"    C_{i+1}           : {cipher_block.hex().upper()}")

        counter = (counter + 1) & 0xFFFFFFFFFFFFFFFF

    return result_blocks, table_rows


# ── Форматирование таблицы (ГОСТ А.8) ────────────────────────────────────────

def print_table(table_rows, title="Таблица итераций гаммирования"):
    W = 20
    print("\n" + "=" * 90)
    print(f"  {title}")
    print("=" * 90)
    print(f"{'i':>{W}} {'P_i':>{W}} {'Входной блок':>{W}} {'Гамма':>{W}} {'C_i':>{W}}")
    print("-" * 90)
    for row in table_rows:
        print(f"{row['i']:>{W}} "
              f"{row['P_i']:>{W}} "
              f"{row['counter']:>{W}} "
              f"{row['gamma']:>{W}} "
              f"{row['C_i']:>{W}}")
    print("=" * 90)

# ── Главное меню ──────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("  МАГМА (ГОСТ Р 34.12-2015) — Режим гаммирования CTR")
    print("  ГОСТ Р 34.13-2015, Приложение А.2.2")
    print("  Текст вводится блоками по 64 бита, разделёнными пробелами")
    print("=" * 80)

    DEF_KEY  = "ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    DEF_IV   = "12345678"
    DEF_TEXT = ("92def06b3c130a59db54c704f8189d204a98fb2e67a8024c8912409b17b57e41")
    #DEF_TEXT = ("4E98110C97B7B93C3E250D93D6E85D69136D868807B2DBEF568EB680AB52A12")

    while True:
        print("\n" + "=" * 80)
        print("ГЛАВНОЕ МЕНЮ")
        print("=" * 80)
        print("1 — Зашифровать текст (HEX-блоки через пробел)")
        print("2 — Расшифровать шифртекст")
        print("0 — Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == '0':
            print("До свидания!")
            break

        elif choice in ('1', '2'):
            mode = "ЗАШИФРОВАНИЕ" if choice == '1' else "РАСШИФРОВАНИЕ"
            print(f"\n{'─'*80}\n{mode}\n{'─'*80}")
            print("  Подсказка: блоки через пробел, каждый — 16 HEX-символов (64 бита)")
            print(f"  Пример: {DEF_TEXT}\n")

            # Ключ
            while True:
                k_in = input("Ключ (64 HEX, Enter = по умолчанию): ").strip()
                if not k_in:
                    k_in = DEF_KEY
                    print(f"  Используется: {k_in}")
                k_in = k_in.replace(' ', '')
                if len(k_in) != 64:
                    print(f"  ✗ Нужно 64 HEX-символа (введено {len(k_in)})")
                    continue
                try:
                    key_bytes = bytes.fromhex(k_in); break
                except ValueError:
                    print("  ✗ Неверный HEX-формат")

            # IV
            while True:
                iv_in = input(f"IV (до 16 HEX, Enter = '{DEF_IV}'): ").strip()
                if not iv_in:
                    iv_in = DEF_IV
                    print(f"  Используется: {iv_in}")
                iv_in = pad_iv(iv_in)
                try:
                    iv_bytes = bytes.fromhex(iv_in); break
                except ValueError:
                    print("  ✗ Неверный HEX-формат")

            # Данные
            data_in = input("Текст (HEX-блоки через пробел, Enter = пример):2").strip()
            if not data_in:
                data_in = DEF_TEXT
                print(f"  Используется: {data_in}")

            try:
                blocks = parse_blocks(data_in)
                if not blocks:
                    print("  ✗ Не удалось разобрать блоки")
                    continue

                total_bytes = sum(len(b) for b in blocks)
                print(f"\n  Блоков: {len(blocks)}  |  "
                      f"Данных: {total_bytes} байт ({total_bytes*8} бит)  |  "
                      f"IV: {iv_bytes.hex().upper()}")

                verbose = input(
                    "Показать каждую итерацию подробно? (да/нет): "
                ).strip().lower() in ('да', 'д', 'y', 'yes')

                result_blocks, rows = magma_ctr_process(
                    blocks, key_bytes, iv_bytes, verbose=verbose)

                print_table(rows,
                    f"{'Зашифрованные' if choice=='1' else 'Расшифрованные'} блоки (CTR)")

                all_p = " ".join(r['P_i'] for r in rows)
                all_c = " ".join(r['C_i'] for r in rows)
                print("\n" + "=" * 80)
                print("ИТОГ")
                print("=" * 80)
                print(f"  Исходные блоки : {all_p}")
                print(f"  Результат      : {all_c}")
                print(f"  IV             : {iv_bytes.hex().upper()}")
                print("=" * 80)

            except Exception as e:
                print(f"  ✗ Ошибка: {e}")
        else:
            print("  ⚠ Неверный выбор")


if __name__ == "__main__":
    main()
