#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КУЗНЕЧИК (ГОСТ 34.12-2018)
Режим простой замены (ECB)

Исправленная реализация с контрольным примером из ГОСТ Р 34.13-2015.
Для шифра «Кузнечик» стандарт задаёт блок 128 бит и ключ 256 бит. [file:5]
Преобразования шифрования строятся из X, S, R, L, где L(a)=R^16(a). [file:5]
"""

from typing import List, Tuple

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

PI_INV = [0] * 256
for i, v in enumerate(PI):
    PI_INV[v] = i

L_VEC = [
    0x94, 0x20, 0x85, 0x10, 0xC2, 0xC0, 0x01, 0xFB,
    0x01, 0xC0, 0xC2, 0x10, 0x85, 0x20, 0x94, 0x01,
]


def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def gf_mul(a: int, b: int) -> int:
    res = 0
    for _ in range(8):
        if b & 1:
            res ^= a
        if a & 0x80:
            a = ((a << 1) ^ 0xC3) & 0xFF
        else:
            a = (a << 1) & 0xFF
        b >>= 1
    return res


def S_transform(state: bytes) -> bytes:
    return bytes(PI[x] for x in state)


def S_inverse(state: bytes) -> bytes:
    return bytes(PI_INV[x] for x in state)


def R_transform(state: bytes) -> bytes:
    # R(a15||...||a0)=l(a15,...,a0)||a15||...||a1 [file:5]
    x = 0
    for i in range(16):
        x ^= gf_mul(state[i], L_VEC[i])
    return bytes([x]) + state[:15]


def R_inverse(state: bytes) -> bytes:
    # Если state = b15||b14||...||b0, то исходный вектор a = a15||...||a0,
    # где b15=l(a15,...,a0), b14..b0 = a15..a1, значит a0 восстанавливаем из l. [file:5]
    a = list(state[1:]) + [0]
    x = state[0]
    for i in range(15):
        x ^= gf_mul(a[i], L_VEC[i])
    a[15] = x
    return bytes(a)


def L_transform(state: bytes) -> bytes:
    for _ in range(16):
        state = R_transform(state)
    return state


def L_inverse(state: bytes) -> bytes:
    for _ in range(16):
        state = R_inverse(state)
    return state


def X_transform(k: bytes, state: bytes) -> bytes:
    return xor_bytes(k, state)


def LSX_transform(k: bytes, state: bytes) -> bytes:
    return L_transform(S_transform(X_transform(k, state)))


def generate_constants() -> List[bytes]:
    # C_i = L(Vec_128(i)), где ненулевой байт стоит справа. [file:5]
    constants = []
    for i in range(1, 33):
        c = bytes([0] * 15 + [i])
        constants.append(L_transform(c))
    return constants


def F(c: bytes, k1: bytes, k2: bytes) -> Tuple[bytes, bytes]:
    # F[c](k1, k2) = (LSX[c](k1) xor k2, k1) [file:20]
    return xor_bytes(LSX_transform(c, k1), k2), k1


def generate_round_keys(master_key: bytes) -> List[bytes]:
    if len(master_key) != 32:
        raise ValueError('Мастер-ключ должен быть 32 байта (256 бит)')

    constants = generate_constants()
    k1 = master_key[:16]
    k2 = master_key[16:]
    round_keys = [k1, k2]

    for j in range(4):
        for i in range(8):
            k1, k2 = F(constants[8 * j + i], k1, k2)
        round_keys.extend([k1, k2])

    return round_keys


def kuznechik_encrypt_block(block: bytes, round_keys: List[bytes]) -> bytes:
    if len(block) != 16:
        raise ValueError('Блок должен быть 16 байт')
    state = block
    for i in range(9):
        state = LSX_transform(round_keys[i], state)
    state = X_transform(round_keys[9], state)
    return state


def kuznechik_decrypt_block(block: bytes, round_keys: List[bytes]) -> bytes:
    if len(block) != 16:
        raise ValueError('Блок должен быть 16 байт')
    state = X_transform(round_keys[9], block)
    for i in range(8, -1, -1):
        state = X_transform(round_keys[i], S_inverse(L_inverse(state)))
    return state


def encrypt_ecb(data: bytes, key: bytes) -> bytes:
    if len(data) % 16 != 0:
        raise ValueError('Для ECB длина данных должна быть кратна 16 байтам')
    round_keys = generate_round_keys(key)
    result = bytearray()
    for i in range(0, len(data), 16):
        result.extend(kuznechik_encrypt_block(data[i:i+16], round_keys))
    return bytes(result)


def decrypt_ecb(data: bytes, key: bytes) -> bytes:
    if len(data) % 16 != 0:
        raise ValueError('Для ECB длина данных должна быть кратна 16 байтам')
    round_keys = generate_round_keys(key)
    result = bytearray()
    for i in range(0, len(data), 16):
        result.extend(kuznechik_decrypt_block(data[i:i+16], round_keys))
    return bytes(result)


def test_gost_example() -> bool:
    print('\n' + '=' * 80)
    print('ТЕСТ: КУЗНЕЧИК в режиме простой замены (ECB)')
    print('=' * 80)

    key = bytes.fromhex('8899aabbccddeeff0011223344556677fedcba98765432100123456789abcdef')
    plaintext = bytes.fromhex(
        '1122334455667700ffeeddccbbaa9988'
        '00112233445566778899aabbcceeff0a'
        '112233445566778899aabbcceeff0a00'
        '2233445566778899aabbcceeff0a0011'
    )
    expected = bytes.fromhex(
        '7f679d90bebc24305a468d42b9d4edcd'
        'b429912c6e0032f9285452d76718d08b'
        'f0ca33549d247ceef3f5a5313bd4b157'
        'd0b09ccde830b9eb3a02c4c5aa8ada98'
    )

    encrypted = encrypt_ecb(plaintext, key)
    decrypted = decrypt_ecb(encrypted, key)

    print(f'\nКлюч: {key.hex().upper()}')
    print('\n' + '-' * 80)

    all_passed = True
    for i in range(4):
        p = plaintext[i*16:(i+1)*16].hex().upper()
        c = encrypted[i*16:(i+1)*16].hex().upper()
        e = expected[i*16:(i+1)*16].hex().upper()
        match = (c == e)
        print(f'Блок {i+1}:')
        print(f'  Открытый текст:  {p}')
        print(f'  Зашифрованный:   {c}')
        print(f'  Ожидается:       {e}')
        print(f'  Совпадение:      {'✓ OK' if match else '✗ ОШИБКА'}')
        print('-' * 80)
        if not match:
            all_passed = False

    decrypt_ok = (decrypted == plaintext)
    print(f'Расшифрование:     {'✓ OK' if decrypt_ok else '✗ ОШИБКА'}')

    if all_passed and decrypt_ok:
        print('\n✓✓✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ✓✓✓')
    else:
        print('\n✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!')
    print('=' * 80)
    return all_passed and decrypt_ok


def main():
    print('=' * 80)
    print('КУЗНЕЧИК (ГОСТ 34.12-2018) - Режим простой замены (ECB)')
    print('=' * 80)

    test_gost_example()

    while True:
        print('\n' + '=' * 80)
        print('МЕНЮ:')
        print('1 - Зашифровать данные')
        print('2 - Расшифровать данные')
        print('3 - Запустить тест')
        print('0 - Выход')
        print('=' * 80)

        choice = input('\nВаш выбор: ').strip()

        if choice == '0':
            print('\nДо свидания!')
            break
        elif choice in ['1', '2']:
            is_encrypt = (choice == '1')
            operation = 'ШИФРОВАНИЯ' if is_encrypt else 'РАСШИФРОВАНИЯ'
            print('\n' + '-' * 80)
            print(f'РЕЖИМ {operation}')
            print('-' * 80)

            key_hex = input('\nВведите ключ (64 HEX символа, 256 бит): ').strip().replace(' ', '')
            if len(key_hex) != 64:
                print(f'✗ Ошибка: нужно 64 HEX символа, введено {len(key_hex)}')
                continue

            data_hex = input('Введите данные в HEX (кратно 32 символам = 16 байтам): ').strip().replace(' ', '')
            if len(data_hex) % 32 != 0:
                print(f'✗ Ошибка: длина должна быть кратна 32 HEX символам, введено {len(data_hex)}')
                continue

            try:
                key = bytes.fromhex(key_hex)
                data = bytes.fromhex(data_hex)
                if is_encrypt:
                    result = encrypt_ecb(data, key)
                    print('\n' + '=' * 80)
                    print('РЕЗУЛЬТАТ ШИФРОВАНИЯ:')
                    print('=' * 80)
                    print(f'Открытый текст (HEX): {data.hex().upper()}')
                    print(f'Зашифрованный (HEX): {result.hex().upper()}')
                else:
                    result = decrypt_ecb(data, key)
                    print('\n' + '=' * 80)
                    print('РЕЗУЛЬТАТ РАСШИФРОВАНИЯ:')
                    print('=' * 80)
                    print(f'Зашифрованный (HEX): {data.hex().upper()}')
                    print(f'Расшифрованный (HEX): {result.hex().upper()}')
                print(f'Длина: {len(result)} байт')
                print('=' * 80)
            except Exception as e:
                print(f'\n✗ Ошибка: {e}')
        elif choice == '3':
            test_gost_example()
        else:
            print('\n⚠ Неверный выбор. Попробуйте снова.')


if __name__ == '__main__':
    main()
