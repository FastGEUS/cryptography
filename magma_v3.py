#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МАГМА (ГОСТ Р 34.12-2015)
Режим простой замены (ECB) по ГОСТ Р 34.13-2015, п. 5.1

Контрольный пример:
K = ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff
P1 = 92def06b3c130a59 -> 2b073f0494f372a0
P2 = db54c704f8189d20 -> de70e715d3556e48
P3 = 4a98fb2e67a8024c -> 11d8d9e9eacfbc1e
P4 = 8912409b17b57e41 -> 7c68260996c67efb
"""

# Таблицы замен (S-блоки) из ГОСТ Р 34.12-2015, раздел 5.1.1
PI = [
    [12, 4, 6, 2, 10, 5, 11, 9, 14, 8, 13, 7, 0, 3, 15, 1],      # π0
    [6, 8, 2, 3, 9, 10, 5, 12, 1, 14, 4, 7, 11, 13, 0, 15],      # π1
    [11, 3, 5, 8, 2, 15, 10, 13, 14, 1, 7, 4, 12, 9, 6, 0],      # π2
    [12, 8, 2, 1, 13, 4, 15, 6, 7, 0, 10, 5, 3, 14, 9, 11],      # π3
    [7, 15, 5, 10, 8, 1, 6, 13, 0, 9, 3, 14, 11, 4, 2, 12],      # π4
    [5, 13, 15, 6, 9, 2, 12, 10, 11, 7, 8, 1, 4, 3, 14, 0],      # π5
    [8, 14, 2, 5, 6, 9, 1, 12, 15, 4, 11, 0, 13, 10, 3, 7],      # π6
    [1, 7, 14, 13, 0, 5, 8, 3, 4, 15, 10, 6, 9, 12, 11, 2]       # π7
]


def t_transform(a):
    """Нелинейное преобразование t (формула 14)"""
    result = 0
    for i in range(8):
        nibble = (a >> (4 * i)) & 0x0F
        substituted = PI[i][nibble]
        result |= (substituted << (4 * i))
    return result


def rotate_left_11(value):
    """Циклический сдвиг влево на 11 бит"""
    value &= 0xFFFFFFFF
    return ((value << 11) | (value >> 21)) & 0xFFFFFFFF


def g_transform(k, a):
    """Преобразование g[k] (формула 15)"""
    temp = (a + k) & 0xFFFFFFFF
    temp = t_transform(temp)
    temp = rotate_left_11(temp)
    return temp


def G_transform(k, a1, a0):
    """Преобразование G[k] (формула 16)"""
    new_a1 = a0
    new_a0 = g_transform(k, a0) ^ a1
    return new_a1, new_a0


def G_star_transform(k, a1, a0):
    """Преобразование G*[k] (формула 17)"""
    result_high = g_transform(k, a0) ^ a1
    result_low = a0
    return result_high, result_low


def generate_round_keys(key_bytes):
    """
    Генерирует 32 раундовых ключа из 256-битного ключа
    согласно формуле (18) ГОСТ Р 34.12-2015
    """
    if len(key_bytes) != 32:
        raise ValueError("Ключ должен быть длиной 32 байта (256 бит)")
    
    # Разбиваем ключ на 8 подключей по 32 бита (Big-endian)
    K = []
    for i in range(8):
        k_bytes = key_bytes[i*4:(i+1)*4]
        K.append(int.from_bytes(k_bytes, byteorder='big'))
    
    # Формируем 32 раундовых ключа согласно формуле (18)
    round_keys = []
    round_keys.extend(K)           # K1...K8
    round_keys.extend(K)           # K9...K16
    round_keys.extend(K)           # K17...K24
    round_keys.extend(reversed(K)) # K25...K32
    
    return round_keys


def magma_encrypt_block(plaintext, round_keys):
    """
    Шифрует один 64-битный блок
    Согласно формуле (19): E = G*[K32]G[K31]...G[K2]G[K1](a1, a0)
    """
    # Разбиваем на две 32-битные половины (Big-endian)
    a1 = (plaintext >> 32) & 0xFFFFFFFF  # Старшие 32 бита
    a0 = plaintext & 0xFFFFFFFF           # Младшие 32 бита
    
    # 31 раунд с преобразованием G
    for i in range(31):
        a1, a0 = G_transform(round_keys[i], a1, a0)
    
    # 32-й раунд с преобразованием G*
    b1, b0 = G_star_transform(round_keys[31], a1, a0)
    
    # Объединяем результат
    ciphertext = (b1 << 32) | b0
    
    return ciphertext


def magma_decrypt_block(ciphertext, round_keys):
    """
    Расшифровывает один 64-битный блок
    Согласно формуле (20): D = G*[K1]G[K2]...G[K31]G[K32](b1, b0)
    """
    # Разбиваем на две 32-битные половины (Big-endian)
    b1 = (ciphertext >> 32) & 0xFFFFFFFF
    b0 = ciphertext & 0xFFFFFFFF
    
    # 31 раунд с преобразованием G (ключи K32, K31, ..., K2)
    for i in range(31, 0, -1):
        b1, b0 = G_transform(round_keys[i], b1, b0)
    
    # 32-й раунд с преобразованием G* (ключ K1)
    a1, a0 = G_star_transform(round_keys[0], b1, b0)
    
    # Объединяем результат
    plaintext = (a1 << 32) | a0
    
    return plaintext


def magma_encrypt_ecb(data, key):
    """
    Шифрует данные в режиме простой замены (ECB)
    
    data - данные (длина должна быть кратна 8 байтам)
    key - 256-битный ключ (32 байта)
    """
    if len(data) % 8 != 0:
        raise ValueError("Длина данных должна быть кратна 8 байтам (64 битам)")
    
    if len(key) != 32:
        raise ValueError("Ключ должен быть 32 байта (256 бит)")
    
    # Генерируем раундовые ключи
    round_keys = generate_round_keys(key)
    
    result = bytearray()
    
    # Шифруем блоками по 8 байт
    for i in range(0, len(data), 8):
        # Берем блок (Big-endian)
        block_bytes = data[i:i+8]
        plaintext_block = int.from_bytes(block_bytes, byteorder='big')
        
        # Шифруем
        ciphertext_block = magma_encrypt_block(plaintext_block, round_keys)
        
        # Преобразуем обратно в байты (Big-endian)
        result.extend(ciphertext_block.to_bytes(8, byteorder='big'))
    
    return bytes(result)


def magma_decrypt_ecb(data, key):
    """
    Расшифровывает данные в режиме простой замены (ECB)
    
    data - зашифрованные данные (длина должна быть кратна 8 байтам)
    key - 256-битный ключ (32 байта)
    """
    if len(data) % 8 != 0:
        raise ValueError("Длина данных должна быть кратна 8 байтам (64 битам)")
    
    if len(key) != 32:
        raise ValueError("Ключ должен быть 32 байта (256 бит)")
    
    # Генерируем раундовые ключи
    round_keys = generate_round_keys(key)
    
    result = bytearray()
    
    # Расшифровываем блоками по 8 байт
    for i in range(0, len(data), 8):
        # Берем блок (Big-endian)
        block_bytes = data[i:i+8]
        ciphertext_block = int.from_bytes(block_bytes, byteorder='big')
        
        # Расшифровываем
        plaintext_block = magma_decrypt_block(ciphertext_block, round_keys)
        
        # Преобразуем обратно в байты (Big-endian)
        result.extend(plaintext_block.to_bytes(8, byteorder='big'))
    
    return bytes(result)


def test_magma_ecb():
    """Тестирует МАГМА ECB на контрольных примерах"""
    print("\n" + "=" * 80)
    print("ТЕСТ: МАГМА в режиме простой замены (ECB)")
    print("=" * 80)
    
    # Ключ
    key = bytes.fromhex("ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
    
    # Тестовые блоки
    test_data = [
        ("92def06b3c130a59", "2b073f0494f372a0"),
        ("db54c704f8189d20", "de70e715d3556e48"),
        ("4a98fb2e67a8024c", "11d8d9e9eacfbc1e"),
        ("8912409b17b57e41", "7c68260996c67efb"),
    ]
    
    print(f"\nКлюч: {key.hex().upper()}")
    print("\n" + "-" * 80)
    
    all_passed = True
    
    for i, (plaintext_hex, expected_hex) in enumerate(test_data, 1):
        plaintext = bytes.fromhex(plaintext_hex)
        expected = bytes.fromhex(expected_hex)
        
        # Шифруем
        ciphertext = magma_encrypt_ecb(plaintext, key)
        
        # Расшифровываем
        decrypted = magma_decrypt_ecb(ciphertext, key)
        
        # Проверяем
        encrypt_ok = (ciphertext == expected)
        decrypt_ok = (decrypted == plaintext)
        
        print(f"Блок {i}:")
        print(f"  Открытый текст:  {plaintext_hex.upper()}")
        print(f"  Зашифрованный:   {ciphertext.hex().upper()}")
        print(f"  Ожидается:       {expected_hex.upper()}")
        print(f"  Шифрование:      {'✓ OK' if encrypt_ok else '✗ ОШИБКА'}")
        print(f"  Расшифрование:   {'✓ OK' if decrypt_ok else '✗ ОШИБКА'}")
        print("-" * 80)
        
        if not (encrypt_ok and decrypt_ok):
            all_passed = False
    
    if all_passed:
        print("✓✓✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ✓✓✓")
    else:
        print("✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
    
    print("=" * 80)
    
    return all_passed


def main():
    print("=" * 80)
    print("МАГМА (ГОСТ Р 34.12-2015) - Режим простой замены (ECB)")
    print("=" * 80)
    
    # Запускаем тест
    test_magma_ecb()
    
    while True:
        print("\n" + "=" * 80)
        print("МЕНЮ:")
        print("1 - Зашифровать данные")
        print("2 - Расшифровать данные")
        print("3 - Запустить тест")
        print("0 - Выход")
        print("=" * 80)
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == '0':
            print("\nДо свидания!")
            break
        
        elif choice == '1' or choice == '2':
            is_encrypt = (choice == '1')
            operation = "шифрования" if is_encrypt else "расшифрования"
            
            print(f"\n{'-' * 80}")
            print(f"РЕЖИМ {operation.upper()}")
            print(f"{'-' * 80}")
            
            # Ввод ключа
            key_hex = input("\nВведите ключ (64 HEX символа, 256 бит): ").strip().replace(' ', '')
            
            if len(key_hex) != 64:
                print(f"✗ Ошибка: нужно 64 HEX символа, введено {len(key_hex)}")
                continue
            
            try:
                key = bytes.fromhex(key_hex)
            except ValueError:
                print("✗ Ошибка: некорректный HEX формат!")
                continue
            
            # Ввод данных
            data_hex = input(f"Введите данные в HEX (кратно 16 символам = 8 байтам): ").strip().replace(' ', '')
            
            if len(data_hex) % 16 != 0:
                print(f"✗ Ошибка: длина должна быть кратна 16 HEX символам (8 байтам), введено {len(data_hex)}")
                continue
            
            try:
                data = bytes.fromhex(data_hex)
            except ValueError:
                print("✗ Ошибка: некорректный HEX формат!")
                continue
            
            # Обработка
            try:
                if is_encrypt:
                    result = magma_encrypt_ecb(data, key)
                    print(f"\n{'=' * 80}")
                    print("РЕЗУЛЬТАТ ШИФРОВАНИЯ:")
                    print(f"{'=' * 80}")
                    print(f"Открытый текст (HEX):  {data.hex().upper()}")
                    print(f"Зашифрованный (HEX):   {result.hex().upper()}")
                else:
                    result = magma_decrypt_ecb(data, key)
                    print(f"\n{'=' * 80}")
                    print("РЕЗУЛЬТАТ РАСШИФРОВАНИЯ:")
                    print(f"{'=' * 80}")
                    print(f"Зашифрованный (HEX):   {data.hex().upper()}")
                    print(f"Расшифрованный (HEX):  {result.hex().upper()}")
                
                print(f"Длина: {len(result)} байт")
                print(f"{'=' * 80}")
            
            except Exception as e:
                print(f"\n✗ Ошибка: {e}")
        
        elif choice == '3':
            test_magma_ecb()
        
        else:
            print("\n⚠ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()