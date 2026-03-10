#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Блочный шифр «Магма» (ГОСТ Р 34.12-2015) в режиме гаммирования (CTR)
по ГОСТ Р 34.13-2015, раздел 5.2

Проверено по контрольным примерам Приложения А.2.2 (Таблица А.8)
"""

# ===============================
# S-БЛОКИ ПО ГОСТ Р 34.12-2015
# ===============================

SBOX = [
    [12, 4, 6, 2, 10, 5, 11, 9, 14, 8, 13, 7, 0, 3, 15, 1],
    [6, 8, 2, 3, 9, 10, 5, 12, 1, 14, 4, 7, 11, 13, 0, 15],
    [11, 3, 5, 8, 2, 15, 10, 13, 14, 1, 7, 4, 12, 9, 6, 0],
    [12, 8, 2, 1, 13, 4, 15, 6, 7, 0, 10, 5, 3, 14, 9, 11],
    [7, 15, 5, 10, 8, 1, 6, 13, 0, 9, 3, 14, 11, 4, 2, 12],
    [5, 13, 15, 6, 9, 2, 12, 10, 11, 7, 8, 1, 4, 3, 14, 0],
    [8, 14, 2, 5, 6, 9, 1, 12, 15, 4, 11, 0, 13, 10, 3, 7],
    [1, 7, 14, 13, 0, 5, 8, 3, 4, 15, 10, 6, 9, 12, 11, 2],
]


def sbox_substitute(value: int) -> int:
    """Применить таблицу замен (S-блок) к 32-битному значению"""
    result = 0
    for i in range(8):
        nibble = (value >> (4 * i)) & 0xF
        result |= SBOX[i][nibble] << (4 * i)
    return result


def rotate_left_11(value: int) -> int:
    """Циклический сдвиг влево на 11 бит (32-битное значение)"""
    return ((value << 11) | (value >> 21)) & 0xFFFFFFFF


# ===============================
# БАЗОВЫЙ АЛГОРИТМ МАГМА
# ГОСТ Р 34.12-2015
# ===============================

def magma_round(a1: int, a0: int, round_key: int) -> tuple:
    """
    Один раунд шифра Магма.
    a1 — старшая 32-битная половина блока
    a0 — младшая 32-битная половина блока
    """
    temp = (a0 + round_key) & 0xFFFFFFFF
    temp = sbox_substitute(temp)
    temp = rotate_left_11(temp)
    return a0, a1 ^ temp


def magma_encrypt_block(block: bytes, key: bytes) -> bytes:
    """
    Зашифрование одного 64-битного блока алгоритмом Магма.

    block: 8 байт (big-endian)
    key:  32 байта (big-endian)
    return: 8 байт шифртекста
    """
    # 8 подключей по 32 бита (big-endian)
    subkeys = []
    for i in range(8):
        sk = int.from_bytes(key[i * 4:(i + 1) * 4], byteorder='big')
        subkeys.append(sk)

    # Разделяем блок на две 32-битные половины (big-endian)
    a1 = int.from_bytes(block[0:4], byteorder='big')  # старшая
    a0 = int.from_bytes(block[4:8], byteorder='big')  # младшая

    # Раунды 1–24: ключи K1..K8, повторить 3 раза
    for _ in range(3):
        for i in range(8):
            a1, a0 = magma_round(a1, a0, subkeys[i])

    # Раунды 25–32: ключи K8..K1 (обратный порядок)
    for i in range(7, -1, -1):
        a1, a0 = magma_round(a1, a0, subkeys[i])

    # Результат (отменяем последний swap)
    return a0.to_bytes(4, byteorder='big') + a1.to_bytes(4, byteorder='big')


# ===============================
# РЕЖИМ ГАММИРОВАНИЯ (CTR)
# ГОСТ Р 34.13-2015, раздел 5.2
# ===============================

def magma_ctr_full_iv(data: bytes, key: bytes, ctr1: bytes) -> bytes:
    """
    Режим CTR, когда пользователь задаёт полный CTR1 (8 байт).
    ctr1: 8 байт (64 бита) — начальное значение счётчика CTR1.
    """
    if len(key) != 32:
        raise ValueError("Ключ должен быть 32 байта (256 бит)")
    if len(ctr1) != 8:
        raise ValueError("CTR1/IV должен быть 8 байт (16 HEX символов)")

    result = bytearray()
    ctr = int.from_bytes(ctr1, byteorder='big')

    for i in range(0, len(data), 8):
        ctr_bytes = ctr.to_bytes(8, byteorder='big')
        gamma = magma_encrypt_block(ctr_bytes, key)

        block = data[i:i+8]
        for j in range(len(block)):
            result.append(block[j] ^ gamma[j])

        ctr = (ctr + 1) & 0xFFFFFFFFFFFFFFFF

    return bytes(result)


# ===============================
# ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ
# ===============================

def main():
    print("=" * 60)
    print("  Магма (ГОСТ Р 34.12-2015), режим CTR (полный CTR1)")
    print("=" * 60)
    print()

    key_hex = input("Введите ключ (64 HEX символа): ").strip()
    if len(key_hex) != 64:
        print(f"Ошибка: ключ — 64 HEX символа (введено {len(key_hex)})")
        return
    try:
        key = bytes.fromhex(key_hex)
    except ValueError:
        print("Ошибка: неверный HEX ключ")
        return

    ctr_hex = input("Введите начальный CTR1/IV (16 HEX символов): ").strip()
    if len(ctr_hex) != 16:
        print(f"Ошибка: CTR1/IV — 16 HEX символов (введено {len(ctr_hex)})")
        return
    try:
        ctr1 = bytes.fromhex(ctr_hex)
    except ValueError:
        print("Ошибка: неверный HEX CTR1/IV")
        return

    data_hex = input("Введите HEX-данные: ").strip()
    try:
        data = bytes.fromhex(data_hex)
    except ValueError:
        print("Ошибка: неверный HEX данных")
        return

    result = magma_ctr_full_iv(data, key, ctr1)

    print()
    print("=" * 60)
    print(f"Результат: {result.hex()}")
    print("=" * 60)



if __name__ == "__main__":
    main()