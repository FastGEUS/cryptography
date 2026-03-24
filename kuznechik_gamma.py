#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КУЗНЕЧИК (ГОСТ Р 34.12-2015) в режиме гаммирования (CTR)
по ГОСТ Р 34.13-2015, s = n = 128.

Программа основана на структуре magma_gamma.py (гаммирование МАГМА),
но переписана под блочный шифр КУЗНЕЧИК (128 бит, LPS-преобразование)
и режим гаммирования по 128 бит.

Контрольный пример (по условию):
  s = n = 128
  IV = 1234567890abcef
  i      1                                   2
  Pi     1122334455667700ffeeddccbbaa9988    00112233445566778899aabbcceeff0a
  Вход   1234567890abcef00000000000000000    1234567890abcef00000000000000001
  Выход  e0b7ebfa9468a6db2a95826efb173830    85ffc500b2f4582a7ba54e08f0ab21ee
  Ci     f195d8bec10ed1dbd57b5fa240bda1b8    85eee733f6a13e5df33ce4b33c45dee4

Здесь "Входной блок" — значение CTR, которое шифруется КУЗНЕЧИКОМ для
получения гаммы (Выходной блок), а затем XOR-ится с Pi, давая Ci.
"""

from __future__ import annotations
import os
from typing import List

# ────────────────────────────────────────────────────────────────
#  Константы КУЗНЕЧИКА (ГОСТ Р 34.12-2015, раздел 5.1)
# ────────────────────────────────────────────────────────────────

# Таблица замен π (S-блок), 16×16
PI = [
    0xFC, 0xEE, 0xDD, 0x11, 0xCF, 0x6E, 0x31, 0x16,
    0xFB, 0xC4, 0xFA, 0xDA, 0x23, 0xC5, 0x04, 0x4D,
    0xE9, 0x77, 0xF0, 0xDB, 0x93, 0x2E, 0x99, 0xBA,
    0x17, 0x36, 0xF1, 0xBB, 0x14, 0xCD, 0x5F, 0xC1,
    0xF9, 0x18, 0x65, 0x5A, 0xE2, 0x5C, 0xEF, 0x21,
    0x81, 0x1C, 0x3C, 0x42, 0x8B, 0x01, 0x8E, 0x4F,
    0x05, 0x84, 0x02, 0xAE, 0xE3, 0x6A, 0x8F, 0xA0,
    0x06, 0x0B, 0xED, 0x98, 0x7F, 0xD4, 0xD3, 0x1F,
    0xEB, 0x34, 0x2C, 0x51, 0xEA, 0xC8, 0x48, 0xAB,
    0xF2, 0x2A, 0x68, 0xA2, 0xFD, 0x3A, 0xCE, 0xCC,
    0xB5, 0x70, 0x0E, 0x56, 0x08, 0x0C, 0x76, 0x12,
    0xBF, 0x72, 0x13, 0x47, 0x9C, 0xB7, 0x5D, 0x87,
    0x15, 0xA1, 0x96, 0x29, 0x10, 0x7B, 0x9A, 0xC7,
    0xF3, 0x91, 0x78, 0x6F, 0x9D, 0x9E, 0xB2, 0xB1,
    0x32, 0x75, 0x19, 0x3D, 0xFF, 0x35, 0x8A, 0x7E,
    0x6D, 0x54, 0xC6, 0x80, 0xC3, 0xBD, 0x0D, 0x57,
    0xDF, 0xF5, 0x24, 0xA9, 0x3E, 0xA8, 0x43, 0xC9,
    0xD7, 0x79, 0xD6, 0xF6, 0x7C, 0x22, 0xB9, 0x03,
    0xE0, 0x0F, 0xEC, 0xDE, 0x7A, 0x94, 0xB0, 0xBC,
    0xDC, 0xE8, 0x28, 0x50, 0x4E, 0x33, 0x0A, 0x4A,
    0xA7, 0x97, 0x60, 0x73, 0x1E, 0x00, 0x62, 0x44,
    0x1A, 0xB8, 0x38, 0x82, 0x64, 0x9F, 0x26, 0x41,
    0xAD, 0x45, 0x46, 0x92, 0x27, 0x5E, 0x55, 0x2F,
    0x8C, 0xA3, 0xA5, 0x7D, 0x69, 0xD5, 0x95, 0x3B,
    0x07, 0x58, 0xB3, 0x40, 0x86, 0xAC, 0x1D, 0xF7,
    0x30, 0x37, 0x6B, 0xE4, 0x88, 0xD9, 0xE7, 0x89,
    0xE1, 0x1B, 0x83, 0x49, 0x4C, 0x3F, 0xF8, 0xFE,
    0x8D, 0x53, 0xAA, 0x90, 0xCA, 0xD8, 0x85, 0x61,
    0x20, 0x71, 0x67, 0xA4, 0x2D, 0x2B, 0x09, 0x5B,
    0xCB, 0x9B, 0x25, 0xD0, 0xBE, 0xE5, 0x6C, 0x52,
    0x59, 0xA6, 0x74, 0xD2, 0xE6, 0xF4, 0xB4, 0xC0,
    0xD1, 0x66, 0xAF, 0xC2, 0x39, 0x4B, 0x63, 0xB6,
]

# Вектор констант для L-преобразования
L_VEC = [
    0x94, 0x20, 0x85, 0x10, 0xC2, 0xC0, 0x01, 0xFB,
    0x01, 0xC0, 0xC2, 0x10, 0x85, 0x20, 0x94, 0x01,
]

# ────────────────────────────────────────────────────────────────
#  Поле GF(2^8), умножение по модулю x^8 + x^7 + x^6 + x + 1 (0xC3)
# ────────────────────────────────────────────────────────────────

def gf_mul(a: int, b: int) -> int:
    res = 0
    for _ in range(8):
        if b & 1:
            res ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0xC3
        b >>= 1
    return res


# ────────────────────────────────────────────────────────────────
#  Базовые преобразования S, R, L, LSX, LS
# ────────────────────────────────────────────────────────────────

def S_transform(state: bytes) -> bytes:
    return bytes(PI[b] for b in state)


def R_transform(state: bytes) -> bytes:
    """Линейное R-преобразование (сдвиг + умножение на L_VEC)."""
    assert len(state) == 16
    x15 = 0
    for i in range(16):
        x15 ^= gf_mul(state[i], L_VEC[i])
    return bytes([x15]) + state[:-1]


def L_transform(state: bytes) -> bytes:
    """Полное L-преобразование = 16 последовательных R."""
    for _ in range(16):
        state = R_transform(state)
    return state


def LSX_transform(k: bytes, state: bytes) -> bytes:
    """Преобразование LSX: L(S(state XOR k))."""
    x = bytes(a ^ b for a, b in zip(state, k))
    x = S_transform(x)
    x = L_transform(x)
    return x


def LS_transform(state: bytes) -> bytes:
    return L_transform(S_transform(state))


# ────────────────────────────────────────────────────────────────
#  Генерация раундовых ключей КУЗНЕЧИКА
# ────────────────────────────────────────────────────────────────

def generate_C_constants() -> List[bytes]:
    """32 константы C_i = L( (i || 0^120) )."""
    consts: List[bytes] = []
    for i in range(1, 33):
        v = bytes([i] + [0] * 15)
        consts.append(L_transform(v))
    return consts


C_CONSTANTS = generate_C_constants()


def F_function(k1: bytes, k2: bytes, c: bytes) -> (bytes, bytes):
    """F(k1, k2, C) из ГОСТ: k1' = k1, k2' = LSX(C, k1) XOR k2."""
    x = LSX_transform(c, k1)
    return x ^ k2, k1  # вернём (k1_next, k2_next)


def generate_round_keys(master_key: bytes) -> List[bytes]:
    """Генерация 10 раундовых ключей КУЗНЕЧИКА (K1..K10)."""
    if len(master_key) != 32:
        raise ValueError("Ключ КУЗНЕЧИКА должен быть 32 байта (256 бит)")

    k1 = master_key[:16]
    k2 = master_key[16:]

    round_keys = [k1, k2]

    for j in range(4):  # всего 4 группы по 8 констант = 32 константы
        for i in range(8):
            idx = j * 8 + i
            c = C_CONSTANTS[idx]
            new_k1 = LSX_transform(c, k1)
            new_k1 = bytes(a ^ b for a, b in zip(new_k1, k2))
            k1, k2 = new_k1, k1
        round_keys.append(k1)
        round_keys.append(k2)

    return round_keys[:10]


# ────────────────────────────────────────────────────────────────
#  Шифрование одного блока КУЗНЕЧИКОМ
# ────────────────────────────────────────────────────────────────

def kuznechik_encrypt_block(block: bytes, round_keys: List[bytes]) -> bytes:
    """Шифрует один 128-битный блок (16 байт)."""
    if len(block) != 16:
        raise ValueError("Блок должен быть 16 байт (128 бит)")
    if len(round_keys) != 10:
        raise ValueError("Нужно ровно 10 раундовых ключей")

    state = bytes(a ^ b for a, b in zip(block, round_keys[0]))

    for i in range(1, 9):
        state = LS_transform(bytes(a ^ b for a, b in zip(state, round_keys[i])))

    state = bytes(a ^ b for a, b in zip(state, round_keys[9]))
    return state


# ────────────────────────────────────────────────────────────────
#  Режим гаммирования (CTR) для КУЗНЕЧИКА, n = s = 128
# ────────────────────────────────────────────────────────────────

def kuznechik_ctr_process(data: bytes, key: bytes, iv: bytes, verbose: bool = False) -> bytes:
    """Режим гаммирования (CTR) по ГОСТ Р 34.13-2015 для КУЗНЕЧИКА.

    s = n = 128, CTR_i = IV || counter, counter инкрементируется на 1.
    """
    if len(iv) != 8:
        raise ValueError("IV должен быть 8 байт (64 бита)")

    round_keys = generate_round_keys(key)

    # Начальное значение счётчика: CTR1 = IV || 0^64
    counter = 0

    result = bytearray()
    total_blocks = (len(data) + 15) // 16

    if verbose:
        print("\n" + "=" * 80)
        print("КУЗНЕЧИК в режиме гаммирования (CTR), n = s = 128")
        print("=" * 80)
        print(f"Длина данных: {len(data)} байт ({len(data) * 8} бит)")
        print(f"IV: {iv.hex()}")
        print("=" * 80)

    for block_index in range(total_blocks):
        block = data[block_index * 16:(block_index + 1) * 16]

        # Формируем 128-битный CTR-блок: IV (старшие 64 бита) || counter (младшие 64 бита)
        ctr_value = int.from_bytes(iv, 'big') << 64 | (counter & 0xFFFFFFFFFFFFFFFF)
        ctr_block = ctr_value.to_bytes(16, 'big')

        gamma = kuznechik_encrypt_block(ctr_block, round_keys)
        gamma_trunc = gamma[:len(block)]

        res_block = bytes(a ^ b for a, b in zip(block, gamma_trunc))
        result.extend(res_block)

        if verbose:
            print(f"Блок {block_index + 1}:")
            print(f"  CTR (входной блок): {ctr_block.hex()}")
            print(f"  Гамма (E_K(CTR)):  {gamma.hex()}")
            print(f"  Открытый/шифр-блок: {block.hex()}")
            print(f"  Результат:          {res_block.hex()}\n")

        counter += 1

    if verbose:
        print("=" * 80)

    return bytes(result)


# ────────────────────────────────────────────────────────────────
#  Вспомогательные функции ввода/вывода
# ────────────────────────────────────────────────────────────────

def pad_iv_64(iv_hex: str) -> str:
    iv_hex = iv_hex.strip().replace(' ', '')
    if len(iv_hex) > 16:
        print(f"⚠ IV слишком длинный ({len(iv_hex)}), обрежем до 16 HEX")
        iv_hex = iv_hex[:16]
    elif len(iv_hex) < 16:
        iv_hex = iv_hex + '0' * (16 - len(iv_hex))
        print(f"✓ IV дополнен нулями до 16 HEX: {iv_hex}")
    return iv_hex


# ────────────────────────────────────────────────────────────────
#  Контрольный пример из условия
# ────────────────────────────────────────────────────────────────

def test_task_example():
    print("\n" + "=" * 80)
    print("Тест по условию задачи: гаммирование КУЗНЕЧИК, n = s = 128")
    print("=" * 80)

    # Используем стандартный ключ из ГОСТ Р 34.12-2015, прил. А.2
    key_hex = "8899aabbccddeeff0011223344556677fedcba98765432100123456789abcdef"
    key = bytes.fromhex(key_hex)

    iv_hex = "1234567890abcef"
    iv_hex = pad_iv_64(iv_hex)
    iv = bytes.fromhex(iv_hex)

    P1 = bytes.fromhex("1122334455667700ffeeddccbbaa9988")
    P2 = bytes.fromhex("00112233445566778899aabbcceeff0a")

    expected_ctr1 = "1234567890abcef0000000000000000"
    expected_ctr2 = "1234567890abcef0000000000000001"

    expected_gamma1 = "e0b7ebfa9468a6db2a95826efb173830"
    expected_gamma2 = "85ffc500b2f4582a7ba54e08f0ab21ee"

    expected_c1 = "f195d8bec10ed1dbd57b5fa240bda1b8"
    expected_c2 = "85eee733f6a13e5df33ce4b33c45dee4"

    data = P1 + P2

    C = kuznechik_ctr_process(data, key, iv, verbose=True)

    C1 = C[:16].hex()
    C2 = C[16:32].hex()

    print("\nОжидаемые CTR-блоки:")
    print("  CTR1:", expected_ctr1)
    print("  CTR2:", expected_ctr2)

    print("\nОжидаемая гамма:")
    print("  gamma1:", expected_gamma1)
    print("  gamma2:", expected_gamma2)

    print("\nОжидаемый шифртекст:")
    print("  C1:", expected_c1)
    print("  C2:", expected_c2)

    print("\nПолученный шифртекст:")
    print("  C1:", C1)
    print("  C2:", C2)


# ────────────────────────────────────────────────────────────────
#  Интерактивный режим
# ────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("КУЗНЕЧИК (ГОСТ Р 34.12-2015) — режим гаммирования (CTR), n = s = 128")
    print("ГОСТ Р 34.13-2015")
    print("=" * 80)

    # Тест из условия
    test_task_example()

    print("\n" + "=" * 80)
    print("ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("=" * 80)

    default_key = "8899aabbccddeeff0011223344556677fedcba98765432100123456789abcdef"
    default_iv = "1234567890abcef"
    default_data = "1122334455667700ffeeddccbbaa9988"

    print("Если оставить строку пустой — используется значение по умолчанию.")

    key_hex = input(f"\nВведите ключ (64 HEX, Enter для {default_key[:16]}...): ").strip()
    if not key_hex:
        key_hex = default_key
        print(f"Используется ключ по умолчанию: {key_hex}")

    iv_hex = input(f"Введите IV (до 16 HEX, Enter для {default_iv}): ").strip()
    if not iv_hex:
        iv_hex = default_iv
        print(f"Используется IV по умолчанию: {iv_hex}")

    iv_hex = pad_iv_64(iv_hex)

    data_hex = input(f"Введите данные (HEX, кратно 32, Enter для {default_data}): ").strip()
    if not data_hex:
        data_hex = default_data
        print(f"Используются данные по умолчанию: {data_hex}")

    try:
        key = bytes.fromhex(key_hex)
        iv = bytes.fromhex(iv_hex)
        data = bytes.fromhex(data_hex)

        if len(key) != 32:
            print(f"✗ Ключ должен быть 32 байта (64 HEX), сейчас {len(key)} байт")
            return
        if len(iv) != 8:
            print(f"✗ IV должен быть 8 байт (16 HEX), сейчас {len(iv)} байт")
            return

        result = kuznechik_ctr_process(data, key, iv, verbose=True)

        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТ")
        print("=" * 80)
        print(f"Ключ   : {key.hex()}")
        print(f"IV     : {iv.hex()}")
        print(f"Данные : {data.hex()}")
        print(f"Выход  : {result.hex()}")
        print("=" * 80)

    except ValueError as e:
        print(f"✗ Ошибка HEX: {e}")
    except Exception as e:
        print(f"✗ Ошибка: {e}")


if __name__ == "__main__":
    main()
