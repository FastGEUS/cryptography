# Таблицы замен (S-блоки) для алгоритма МАГМА согласно ГОСТ Р 34.12-2015
PI = [
    [12, 4, 6, 2, 10, 5, 11, 9, 14, 8, 13, 7, 0, 3, 15, 1],
    [6, 8, 2, 3, 9, 10, 5, 12, 1, 14, 4, 7, 11, 13, 0, 15],
    [11, 3, 5, 8, 2, 15, 10, 13, 14, 1, 7, 4, 12, 9, 6, 0],
    [12, 8, 2, 1, 13, 4, 15, 6, 7, 0, 10, 5, 3, 14, 9, 11],
    [7, 15, 5, 10, 8, 1, 6, 13, 0, 9, 3, 14, 11, 4, 2, 12],
    [5, 13, 15, 6, 9, 2, 12, 10, 11, 7, 8, 1, 4, 3, 14, 0],
    [8, 14, 2, 5, 6, 9, 1, 12, 15, 4, 11, 0, 13, 10, 3, 7],
    [1, 7, 14, 13, 0, 5, 8, 3, 4, 15, 10, 6, 9, 12, 11, 2]
]


def is_valid_hex(text, expected_length):
    """Проверяет, является ли строка валидной HEX строкой нужной длины"""
    if len(text) != expected_length:
        return False
    try:
        int(text, 16)
        return True
    except ValueError:
        return False


def input_hex(prompt, expected_length, description):
    """
    Запрашивает HEX строку с немедленной проверкой
    
    prompt - текст приглашения
    expected_length - ожидаемая длина в символах
    description - описание для сообщений об ошибке
    """
    while True:
        value = input(prompt).strip().lower()
        
        # Проверка длины
        if len(value) != expected_length:
            print(f"Ошибка: {description} должен быть {expected_length} HEX символов!")
            print(f"  Вы ввели {len(value)} символов. Попробуйте снова.")
            continue
        
        # Проверка на валидность HEX
        try:
            int(value, 16)
            return value
        except ValueError:
            print(f"Ошибка: {description} должен содержать только HEX символы (0-9, a-f)!")
            print(f"  Недопустимые символы в строке: '{value}'")
            continue


def t_transform(a):
    """
    Преобразование t: V32 → V32
    Применяет таблицы замен (S-блоки) согласно формуле (14)
    """
    result = 0
    for i in range(8):
        nibble = (a >> (4 * i)) & 0x0F
        substituted = PI[i][nibble]
        result |= (substituted << (4 * i))
    return result


def rotate_left_11(value):
    """Циклический сдвиг влево на 11 бит для 32-битного числа"""
    value &= 0xFFFFFFFF
    return ((value << 11) | (value >> 21)) & 0xFFFFFFFF


def g_transform(k, a):
    """
    Преобразование g[k]: V32 → V32 согласно формуле (15)
    g[k](a) = (t(Vec32(Int32(a) ⊞ Int32(k)))) ⋘11
    """
    temp = (a + k) & 0xFFFFFFFF
    temp = t_transform(temp)
    temp = rotate_left_11(temp)
    return temp


def G_transform(k, a1, a0):
    """
    Преобразование G[k]: V32 × V32 → V32 × V32 согласно формуле (16)
    G[k](a1, a0) = (a0, g[k](a0) ⊕ a1)
    """
    new_a1 = a0
    new_a0 = g_transform(k, a0) ^ a1
    return new_a1, new_a0


def G_star_transform(k, a1, a0):
    """
    Преобразование G*[k]: V32 × V32 → V64 согласно формуле (17)
    G*[k](a1, a0) = (g[k](a0) ⊕ a1)||a0
    """
    result_high = g_transform(k, a0) ^ a1
    result_low = a0
    return result_high, result_low


def generate_round_keys(key_hex):
    """
    Генерирует 32 итерационных ключа из 256-битного ключа (HEX)
    согласно формуле (18) ГОСТ Р 34.12-2015
    """
    key_bytes = bytes.fromhex(key_hex)
    
    if len(key_bytes) != 32:
        raise ValueError("Ключ должен быть длиной 64 символа HEX (256 бит)")
    
    # Разбиваем ключ на 8 подключей по 32 бита
    K = []
    for i in range(8):
        k_bytes = key_bytes[i*4:(i+1)*4]
        K.append(int.from_bytes(k_bytes, byteorder='big'))
    
    # Формируем 32 итерационных ключа согласно формуле (18)
    round_keys = []
    
    # K1...K8
    for i in range(8):
        round_keys.append(K[i])
    
    # K9...K16 = K1...K8
    for i in range(8):
        round_keys.append(K[i])
    
    # K17...K24 = K1...K8
    for i in range(8):
        round_keys.append(K[i])
    
    # K25...K32 = K8...K1 (в обратном порядке)
    for i in range(7, -1, -1):
        round_keys.append(K[i])
    
    return round_keys


def magma_encrypt(a, round_keys):
    """
    Шифрует 64-битное число алгоритмом МАГМА
    Согласно формуле (19): E = G*[K32]G[K31]...G[K2]G[K1](a1, a0)
    """
    if isinstance(a, str):
        a = int(a, 16)
    
    # Разбиваем на две 32-битные части
    a1 = (a >> 32) & 0xFFFFFFFF
    a0 = a & 0xFFFFFFFF
    
    # 31 раунд с преобразованием G
    for i in range(31):
        a1, a0 = G_transform(round_keys[i], a1, a0)
    
    # 32-й раунд с преобразованием G*
    b1, b0 = G_star_transform(round_keys[31], a1, a0)
    
    # Объединяем результат
    b = (b1 << 32) | b0
    
    return b


def magma_decrypt(b, round_keys):
    """
    Расшифровывает 64-битное число алгоритмом МАГМА
    Согласно формуле (20): D = G*[K1]G[K2]...G[K31]G[K32](a1, a0)
    """
    if isinstance(b, str):
        b = int(b, 16)
    
    # Разбиваем на две 32-битные части
    b1 = (b >> 32) & 0xFFFFFFFF
    b0 = b & 0xFFFFFFFF
    
    # 31 раунд с преобразованием G (ключи K32, K31, ..., K2)
    for i in range(31, 0, -1):
        b1, b0 = G_transform(round_keys[i], b1, b0)
    
    # 32-й раунд с преобразованием G* (ключ K1)
    a1, a0 = G_star_transform(round_keys[0], b1, b0)
    
    # Объединяем результат
    a = (a1 << 32) | a0
    
    return a


def test_gost_example():
    """
    Тестирует алгоритм на контрольном примере из ГОСТ Р 34.12-2015
    Приложение А.2
    """
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ НА КОНТРОЛЬНОМ ПРИМЕРЕ ИЗ ГОСТ Р 34.12-2015 (А.2)")
    print("=" * 80)
    
    # Ключ из примера A.2.3
    K = "ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    
    print(f"\nКлюч (256 бит):\n{K}")
    
    # Генерируем раундовые ключи
    round_keys = generate_round_keys(K)
    
    # Проверяем раундовые ключи (A.2.3)
    expected_keys = {
        1: 0xffeeddcc, 9: 0xffeeddcc, 17: 0xffeeddcc, 25: 0xfcfdfeff,
        2: 0xbbaa9988, 10: 0xbbaa9988, 18: 0xbbaa9988, 26: 0xf8f9fafb,
        3: 0x77665544, 11: 0x77665544, 19: 0x77665544, 27: 0xf4f5f6f7,
        4: 0x33221100, 12: 0x33221100, 20: 0x33221100, 28: 0xf0f1f2f3,
        5: 0xf0f1f2f3, 13: 0xf0f1f2f3, 21: 0xf0f1f2f3, 29: 0x33221100,
        6: 0xf4f5f6f7, 14: 0xf4f5f6f7, 22: 0xf4f5f6f7, 30: 0x77665544,
        7: 0xf8f9fafb, 15: 0xf8f9fafb, 23: 0xf8f9fafb, 31: 0xbbaa9988,
        8: 0xfcfdfeff, 16: 0xfcfdfeff, 24: 0xfcfdfeff, 32: 0xffeeddcc
    }
    
    print("\nПроверка раундовых ключей:")
    all_correct = True
    for i in sorted(expected_keys.keys()):
        expected = expected_keys[i]
        actual = round_keys[i-1]
        status = "✓" if actual == expected else "✗"
        print(f"  K{i:2d} = {actual:08x} (ожидается {expected:08x}) {status}")
        if actual != expected:
            all_correct = False
    
    if not all_correct:
        print("\nОШИБКА: Раундовые ключи не совпадают!")
        return False
    
    print("\nВсе раундовые ключи совпадают!")
    
    # Открытый текст из примера A.2.4
    a = 0xfedcba9876543210
    
    print(f"\n{'-'*80}")
    print("ШИФРОВАНИЕ:")
    print(f"Открытый текст (64 бит):    {a:016x}")
    
    a1 = (a >> 32) & 0xFFFFFFFF
    a0 = a & 0xFFFFFFFF
    print(f"  (a1, a0) = ({a1:08x}, {a0:08x})")
    
    # Шифрование
    b = magma_encrypt(a, round_keys)
    
    print(f"\nЗашифрованный текст:        {b:016x}")
    print(f"Ожидается по ГОСТ:          4ee901e5c2d8ca3d")
    
    if b == 0x4ee901e5c2d8ca3d:
        print("ШИФРОВАНИЕ УСПЕШНО!")
    else:
        print("ОШИБКА ШИФРОВАНИЯ!")
        return False
    
    # Расшифрование
    print(f"\n{'-'*80}")
    print("РАСШИФРОВАНИЕ:")
    print(f"Зашифрованный текст:        {b:016x}")
    
    d = magma_decrypt(b, round_keys)
    
    print(f"Расшифрованный текст:       {d:016x}")
    print(f"Ожидается (исходный текст): {a:016x}")
    
    if d == a:
        print("РАСШИФРОВАНИЕ УСПЕШНО!")
        print("\n" + "=" * 80)
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ! АЛГОРИТМ РАБОТАЕТ КОРРЕКТНО!")
        print("=" * 80)
        return True
    else:
        print("ОШИБКА РАСШИФРОВАНИЯ!")
        return False


# Главная программа
print("=" * 80)
print("Шифр МАГМА (ГОСТ Р 34.12-2015)")
print("Шифрование 64-битных чисел")
print("=" * 80)

while True:
    print("\n" + "=" * 80)
    print("Выберите действие:")
    print("1 - Преобразование T") # - Для МАГМА print("1 - Зашифровать 64-битное число")
    #print("2 - Расшифровать 64-битное число") - Для МАГМА
    #print("3 - Запустить тест на примере из ГОСТ (А.2)") - Для МАГМА
    print("0 - Выход")
    
    choice = input("\nВаш выбор: ")
    
    if choice == '0':
        print("\nДо свидания!")
        break
    
    elif choice == '1':
        print("\n" + "-" * 80)
        print("S-блок замены ГОСТ 34.12-2015")
        print("-" * 80)
        
        # Ввод открытого текста с проверкой
        plaintext = input_hex(
            "Введите открытый текст (8 HEX символов): ",
            8,
            "Открытый текст"
        )
        ''' 
        # Ввод ключа с проверкой - Для МАГМА
        key = input_hex(
            "Введите ключ (64 HEX символа, 256 бит): ",
            64,
            "Ключ"
        )
        
        # Генерируем раундовые ключи
        round_keys = generate_round_keys(key)
        '''
        # Шифруем
        plaintext_int = int(plaintext, 16)
        ciphertext_int = t_transform(plaintext_int) # - Для МАГМА magma_encrypt(plaintext_int, round_keys) 
        
        print(f"\n{'='*80}")
        print(f"Открытый текст:      {plaintext_int:08x}") # - Для МАГМА {plaintext_int:016x}
        #print(f"Ключ:                {key}") - Для МАГМА 
        print(f"Зашифрованный текст: {ciphertext_int:08x}") #  - Для МАГМА {ciphertext_int:016x}
        print(f"{'='*80}")
        
        ''' - Для МАГМА
    elif choice == '2':  
        print("\n" + "-" * 80)
        print("РАСШИФРОВАНИЕ 64-БИТНОГО ЧИСЛА")
        print("-" * 80)
        
        # Ввод зашифрованного текста с проверкой
        ciphertext = input_hex(
            "Введите зашифрованный текст (16 HEX символов, 64 бита): ",
            16,
            "Зашифрованный текст"
        )
        
        # Ввод ключа с проверкой
        key = input_hex(
            "Введите ключ (64 HEX символа, 256 бит): ",
            64,
            "Ключ"
        )
        
        # Генерируем раундовые ключи
        round_keys = generate_round_keys(key)
        
        # Расшифровываем
        ciphertext_int = int(ciphertext, 16)
        plaintext_int = magma_decrypt(ciphertext_int, round_keys)
        
        print(f"\n{'='*80}")
        print(f"Зашифрованный текст:  {ciphertext_int:016x}")
        print(f"Ключ:                 {key}")
        print(f"Расшифрованный текст: {plaintext_int:016x}")
        print(f"{'='*80}")
    
    elif choice == '3':
        test_gost_example()'''
        
    else:
        print("\nНеверный выбор. Попробуйте снова.")