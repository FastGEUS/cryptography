#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AES-128 на Python по FIPS-197.

Реализованы:
- KeyExpansion
- SubBytes / InvSubBytes
- ShiftRows / InvShiftRows
- MixColumns / InvMixColumns
- AddRoundKey
- Encrypt / Decrypt одного блока 128 бит
- Меню для ручного шифрования и расшифрования

Согласно FIPS-197, для AES-128: Nk = 4, Nb = 4, Nr = 10. [file:18]
Контрольный пример из приложения:
key       = 000102030405060708090a0b0c0d0e0f
plaintext = 00112233445566778899aabbccddeeff
cipher    = 69c4e0d86a7b0430d8cdb78070b4c55a [file:18]
"""

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

INV_S_BOX = [
    0x52,0x09,0x6a,0xd5,0x30,0x36,0xa5,0x38,0xbf,0x40,0xa3,0x9e,0x81,0xf3,0xd7,0xfb,
    0x7c,0xe3,0x39,0x82,0x9b,0x2f,0xff,0x87,0x34,0x8e,0x43,0x44,0xc4,0xde,0xe9,0xcb,
    0x54,0x7b,0x94,0x32,0xa6,0xc2,0x23,0x3d,0xee,0x4c,0x95,0x0b,0x42,0xfa,0xc3,0x4e,
    0x08,0x2e,0xa1,0x66,0x28,0xd9,0x24,0xb2,0x76,0x5b,0xa2,0x49,0x6d,0x8b,0xd1,0x25,
    0x72,0xf8,0xf6,0x64,0x86,0x68,0x98,0x16,0xd4,0xa4,0x5c,0xcc,0x5d,0x65,0xb6,0x92,
    0x6c,0x70,0x48,0x50,0xfd,0xed,0xb9,0xda,0x5e,0x15,0x46,0x57,0xa7,0x8d,0x9d,0x84,
    0x90,0xd8,0xab,0x00,0x8c,0xbc,0xd3,0x0a,0xf7,0xe4,0x58,0x05,0xb8,0xb3,0x45,0x06,
    0xd0,0x2c,0x1e,0x8f,0xca,0x3f,0x0f,0x02,0xc1,0xaf,0xbd,0x03,0x01,0x13,0x8a,0x6b,
    0x3a,0x91,0x11,0x41,0x4f,0x67,0xdc,0xea,0x97,0xf2,0xcf,0xce,0xf0,0xb4,0xe6,0x73,
    0x96,0xac,0x74,0x22,0xe7,0xad,0x35,0x85,0xe2,0xf9,0x37,0xe8,0x1c,0x75,0xdf,0x6e,
    0x47,0xf1,0x1a,0x71,0x1d,0x29,0xc5,0x89,0x6f,0xb7,0x62,0x0e,0xaa,0x18,0xbe,0x1b,
    0xfc,0x56,0x3e,0x4b,0xc6,0xd2,0x79,0x20,0x9a,0xdb,0xc0,0xfe,0x78,0xcd,0x5a,0xf4,
    0x1f,0xdd,0xa8,0x33,0x88,0x07,0xc7,0x31,0xb1,0x12,0x10,0x59,0x27,0x80,0xec,0x5f,
    0x60,0x51,0x7f,0xa9,0x19,0xb5,0x4a,0x0d,0x2d,0xe5,0x7a,0x9f,0x93,0xc9,0x9c,0xef,
    0xa0,0xe0,0x3b,0x4d,0xae,0x2a,0xf5,0xb0,0xc8,0xeb,0xbb,0x3c,0x83,0x53,0x99,0x61,
    0x17,0x2b,0x04,0x7e,0xba,0x77,0xd6,0x26,0xe1,0x69,0x14,0x63,0x55,0x21,0x0c,0x7d,
]

RCON = [0x00,0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1B,0x36]


def bytes_to_state(block: bytes):
    return [[block[r + 4*c] for c in range(4)] for r in range(4)]


def state_to_bytes(state):
    return bytes(state[r][c] for c in range(4) for r in range(4))


def sub_bytes(state):
    for r in range(4):
        for c in range(4):
            state[r][c] = S_BOX[state[r][c]]


def inv_sub_bytes(state):
    for r in range(4):
        for c in range(4):
            state[r][c] = INV_S_BOX[state[r][c]]


def shift_rows(state):
    state[1] = state[1][1:] + state[1][:1]
    state[2] = state[2][2:] + state[2][:2]
    state[3] = state[3][3:] + state[3][:3]


def inv_shift_rows(state):
    state[1] = state[1][-1:] + state[1][:-1]
    state[2] = state[2][-2:] + state[2][:-2]
    state[3] = state[3][-3:] + state[3][:-3]


def xtime(a):
    return (((a << 1) ^ 0x1B) & 0xFF) if (a & 0x80) else ((a << 1) & 0xFF)


def gf_mul(a, b):
    res = 0
    for _ in range(8):
        if b & 1:
            res ^= a
        a = xtime(a)
        b >>= 1
    return res


def mix_single_column(col):
    a0, a1, a2, a3 = col
    return [
        gf_mul(a0, 2) ^ gf_mul(a1, 3) ^ a2 ^ a3,
        a0 ^ gf_mul(a1, 2) ^ gf_mul(a2, 3) ^ a3,
        a0 ^ a1 ^ gf_mul(a2, 2) ^ gf_mul(a3, 3),
        gf_mul(a0, 3) ^ a1 ^ a2 ^ gf_mul(a3, 2),
    ]


def inv_mix_single_column(col):
    a0, a1, a2, a3 = col
    return [
        gf_mul(a0, 0x0e) ^ gf_mul(a1, 0x0b) ^ gf_mul(a2, 0x0d) ^ gf_mul(a3, 0x09),
        gf_mul(a0, 0x09) ^ gf_mul(a1, 0x0e) ^ gf_mul(a2, 0x0b) ^ gf_mul(a3, 0x0d),
        gf_mul(a0, 0x0d) ^ gf_mul(a1, 0x09) ^ gf_mul(a2, 0x0e) ^ gf_mul(a3, 0x0b),
        gf_mul(a0, 0x0b) ^ gf_mul(a1, 0x0d) ^ gf_mul(a2, 0x09) ^ gf_mul(a3, 0x0e),
    ]


def mix_columns(state):
    for c in range(4):
        col = [state[r][c] for r in range(4)]
        mixed = mix_single_column(col)
        for r in range(4):
            state[r][c] = mixed[r]


def inv_mix_columns(state):
    for c in range(4):
        col = [state[r][c] for r in range(4)]
        mixed = inv_mix_single_column(col)
        for r in range(4):
            state[r][c] = mixed[r]


def add_round_key(state, round_key):
    for c in range(4):
        word = round_key[c]
        for r in range(4):
            state[r][c] ^= word[r]


def rot_word(word):
    return word[1:] + word[:1]


def sub_word(word):
    return [S_BOX[b] for b in word]


def key_expansion(key: bytes):
    Nk, Nb, Nr = 4, 4, 10
    w = []
    for i in range(Nk):
        w.append([key[4*i], key[4*i+1], key[4*i+2], key[4*i+3]])
    for i in range(Nk, Nb * (Nr + 1)):
        temp = w[i - 1][:]
        if i % Nk == 0:
            temp = sub_word(rot_word(temp))
            temp[0] ^= RCON[i // Nk]
        w.append([w[i - Nk][j] ^ temp[j] for j in range(4)])
    return w


def encrypt_block(block: bytes, key: bytes, verbose=False) -> bytes:
    Nk, Nb, Nr = 4, 4, 10
    state = bytes_to_state(block)
    w = key_expansion(key)

    if verbose:
        print(f'round 0.input  {block.hex()}')
        print(f'round 0.ksch   {key.hex()}')

    add_round_key(state, w[0:Nb])

    for round_num in range(1, Nr):
        if verbose:
            print(f'round {round_num}.start  {state_to_bytes(state).hex()}')
        sub_bytes(state)
        if verbose:
            print(f'round {round_num}.sbox   {state_to_bytes(state).hex()}')
        shift_rows(state)
        if verbose:
            print(f'round {round_num}.srow   {state_to_bytes(state).hex()}')
        mix_columns(state)
        if verbose:
            print(f'round {round_num}.mcol   {state_to_bytes(state).hex()}')
        round_key_bytes = b''.join(bytes(word) for word in w[round_num*Nb:(round_num+1)*Nb])
        if verbose:
            print(f'round {round_num}.ksch   {round_key_bytes.hex()}')
        add_round_key(state, w[round_num*Nb:(round_num+1)*Nb])

    if verbose:
        print(f'round {Nr}.start  {state_to_bytes(state).hex()}')
    sub_bytes(state)
    if verbose:
        print(f'round {Nr}.sbox   {state_to_bytes(state).hex()}')
    shift_rows(state)
    if verbose:
        print(f'round {Nr}.srow   {state_to_bytes(state).hex()}')
    round_key_bytes = b''.join(bytes(word) for word in w[Nr*Nb:(Nr+1)*Nb])
    if verbose:
        print(f'round {Nr}.ksch   {round_key_bytes.hex()}')
    add_round_key(state, w[Nr*Nb:(Nr+1)*Nb])
    out = state_to_bytes(state)
    if verbose:
        print(f'round {Nr}.output {out.hex()}')
    return out


def decrypt_block(block: bytes, key: bytes, verbose=False) -> bytes:
    Nk, Nb, Nr = 4, 4, 10
    state = bytes_to_state(block)
    w = key_expansion(key)

    if verbose:
        print(f'round 0.iinput  {block.hex()}')
        print(f'round 0.iksch   {b"".join(bytes(word) for word in w[Nr*Nb:(Nr+1)*Nb]).hex()}')

    add_round_key(state, w[Nr*Nb:(Nr+1)*Nb])

    for round_num in range(Nr - 1, 0, -1):
        step = Nr - round_num
        if verbose:
            print(f'round {step}.istart {state_to_bytes(state).hex()}')
        inv_shift_rows(state)
        if verbose:
            print(f'round {step}.isrow  {state_to_bytes(state).hex()}')
        inv_sub_bytes(state)
        if verbose:
            print(f'round {step}.isbox  {state_to_bytes(state).hex()}')
        round_key_bytes = b''.join(bytes(word) for word in w[round_num*Nb:(round_num+1)*Nb])
        if verbose:
            print(f'round {step}.iksch  {round_key_bytes.hex()}')
        add_round_key(state, w[round_num*Nb:(round_num+1)*Nb])
        if verbose:
            print(f'round {step}.ikadd  {state_to_bytes(state).hex()}')
        inv_mix_columns(state)

    inv_shift_rows(state)
    if verbose:
        print(f'round {Nr}.isrow  {state_to_bytes(state).hex()}')
    inv_sub_bytes(state)
    if verbose:
        print(f'round {Nr}.isbox  {state_to_bytes(state).hex()}')
        print(f'round {Nr}.iksch  {b"".join(bytes(word) for word in w[0:Nb]).hex()}')
    add_round_key(state, w[0:Nb])
    out = state_to_bytes(state)
    if verbose:
        print(f'round {Nr}.ioutput {out.hex()}')
    return out


def test_aes_example() -> bool:
    print('\n' + '=' * 72)
    print('ТЕСТ AES-128 ПО FIPS-197')
    print('=' * 72)

    key = bytes.fromhex('000102030405060708090a0b0c0d0e0f')
    plaintext = bytes.fromhex('00112233445566778899aabbccddeeff')
    expected_cipher = '69c4e0d86a7b0430d8cdb78070b4c55a'

    ciphertext = encrypt_block(plaintext, key, verbose=False)
    decrypted = decrypt_block(ciphertext, key, verbose=False)

    enc_ok = ciphertext.hex() == expected_cipher
    dec_ok = decrypted == plaintext

    print(f'Ключ            : {key.hex()}')
    print(f'Открытый текст  : {plaintext.hex()}')
    print(f'Шифртекст       : {ciphertext.hex()}')
    print(f'Эталон          : {expected_cipher}')
    print(f'Шифрование      : {'✓ OK' if enc_ok else '✗ ОШИБКА'}')
    print(f'Расшифрование   : {'✓ OK' if dec_ok else '✗ ОШИБКА'}')
    print('=' * 72)

    return enc_ok and dec_ok


def main():
    print('=' * 72)
    print('AES-128 ПО FIPS-197')
    print('=' * 72)

    test_aes_example()

    while True:
        print('\n' + '=' * 72)
        print('МЕНЮ:')
        print('1 - Зашифровать блок')
        print('2 - Расшифровать блок')
        print('3 - Запустить тест')
        print('4 - Показать подробный разбор шифрования')
        print('5 - Показать подробный разбор расшифрования')
        print('0 - Выход')
        print('=' * 72)

        choice = input('\nВаш выбор: ').strip()

        if choice == '0':
            print('\nДо свидания!')
            break

        elif choice in ['1', '2']:
            is_encrypt = (choice == '1')
            key_hex = input('Введите ключ AES-128 (32 HEX символа): ').strip().replace(' ', '')
            data_hex = input('Введите блок данных (32 HEX символа): ').strip().replace(' ', '')

            if len(key_hex) != 32:
                print('✗ Ошибка: ключ должен содержать ровно 32 HEX символа.')
                continue
            if len(data_hex) != 32:
                print('✗ Ошибка: блок должен содержать ровно 32 HEX символа.')
                continue

            try:
                key = bytes.fromhex(key_hex)
                data = bytes.fromhex(data_hex)
                if is_encrypt:
                    result = encrypt_block(data, key, verbose=False)
                    print('\nРЕЗУЛЬТАТ ШИФРОВАНИЯ:')
                    print('Открытый текст :', data.hex())
                    print('Шифртекст      :', result.hex())
                else:
                    result = decrypt_block(data, key, verbose=False)
                    print('\nРЕЗУЛЬТАТ РАСШИФРОВАНИЯ:')
                    print('Шифртекст      :', data.hex())
                    print('Открытый текст :', result.hex())
            except Exception as e:
                print(f'✗ Ошибка: {e}')

        elif choice == '3':
            test_aes_example()

        elif choice == '4':
            key = bytes.fromhex('000102030405060708090a0b0c0d0e0f')
            plaintext = bytes.fromhex('00112233445566778899aabbccddeeff')
            print('\nПОДРОБНЫЙ РАЗБОР ШИФРОВАНИЯ:')
            encrypt_block(plaintext, key, verbose=True)

        elif choice == '5':
            key = bytes.fromhex('000102030405060708090a0b0c0d0e0f')
            ciphertext = bytes.fromhex('69c4e0d86a7b0430d8cdb78070b4c55a')
            print('\nПОДРОБНЫЙ РАЗБОР РАСШИФРОВАНИЯ:')
            decrypt_block(ciphertext, key, verbose=True)

        else:
            print('⚠ Неверный выбор. Попробуйте снова.')


if __name__ == '__main__':
    main()
