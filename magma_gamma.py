import struct

# Таблицы замен (S-блоки) ГОСТ Р 34.12-2015, раздел 5.1.1
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
    Генерирует 32 раундовых ключа согласно формуле (18)
    
    ВАЖНО: Ключ интерпретируется как K = k255||...||k0
    где первые 4 байта (биты 255-224) = K1
    """
    if len(key_bytes) != 32:
        raise ValueError("Ключ должен быть длиной 32 байта (256 бит)")
    
    # Разбиваем ключ на 8 подключей по 32 бита
    # K1 = старшие 32 бита (первые 4 байта)
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


def magma_encrypt_block(plaintext_block, round_keys):
    """
    Шифрует один 64-битный блок
    Согласно формуле (19): E = G*[K32]G[K31]...G[K2]G[K1](a1, a0)
    """
    # Разбиваем на две 32-битные половины (Big-endian)
    a1 = (plaintext_block >> 32) & 0xFFFFFFFF
    a0 = plaintext_block & 0xFFFFFFFF
    
    # 31 раунд с преобразованием G
    for i in range(31):
        a1, a0 = G_transform(round_keys[i], a1, a0)
    
    # 32-й раунд с преобразованием G*
    b1, b0 = G_star_transform(round_keys[31], a1, a0)
    
    # Объединяем результат
    ciphertext_block = (b1 << 32) | b0
    
    return ciphertext_block


def pad_iv(iv_str):
    """
    Дополняет IV до 16 HEX символов (8 байт)
    
    Примеры:
    - "12345678" → "1234567800000000"
    - "ABCD" → "ABCD000000000000"
    - "1234567890ABCDEF" → "1234567890ABCDEF" (без изменений)
    """
    iv_str = iv_str.strip().upper()
    
    # Убираем возможные пробелы
    iv_str = iv_str.replace(' ', '')
    
    if len(iv_str) > 16:
        print(f"⚠ ВНИМАНИЕ: IV слишком длинный ({len(iv_str)} символов), обрезан до 16")
        iv_str = iv_str[:16]
    elif len(iv_str) < 16:
        # Дополняем нулями справа
        padding_needed = 16 - len(iv_str)
        iv_str = iv_str + '0' * padding_needed
        print(f"✓ IV дополнен нулями: {iv_str}")
    
    return iv_str


def magma_ctr_process(data, key, iv, verbose=False):
    """
    Шифрует/расшифровывает данные в режиме CTR
    согласно ГОСТ Р 34.13-2015
    """
    # Генерируем раундовые ключи
    round_keys = generate_round_keys(key)
    
    # Преобразуем IV в 64-битное число (счетчик)
    # ГОСТ использует Big-endian для счетчика
    counter = int.from_bytes(iv, byteorder='big')
    
    result = bytearray()
    
    if verbose:
        print("\n" + "=" * 80)
        print("РЕЖИМ ГАММИРОВАНИЯ (CTR) - ГОСТ Р 34.13-2015")
        print("=" * 80)
        print(f"Длина данных: {len(data)} байт ({len(data) * 8} бит)")
        print(f"Начальный счетчик (IV): {counter:016X}")
        print(f"IV (байты): {iv.hex().upper()}")
        print("=" * 80)
    
    # Обрабатываем данные блоками по 8 байт
    for block_num in range(0, len(data), 8):
        # Берем блок данных (может быть неполным)
        data_block = data[block_num:block_num + 8]
        
        # Генерируем гамму: зашифровываем текущее значение счетчика
        gamma_block = magma_encrypt_block(counter, round_keys)
        
        # Преобразуем гамму в байты (Big-endian)
        gamma_bytes = gamma_block.to_bytes(8, byteorder='big')
        
        # Обрезаем гамму до длины блока данных (для последнего неполного блока)
        gamma_bytes = gamma_bytes[:len(data_block)]
        
        # XOR данных с гаммой
        result_block = bytes(a ^ b for a, b in zip(data_block, gamma_bytes))
        result.extend(result_block)
        
        if verbose:
            print(f"\nБлок {block_num // 8 + 1}:")
            print(f"  Счетчик (CTR):       {counter:016X}")
            print(f"  Гамма E(CTR):        {gamma_bytes.hex().upper()}")
            print(f"  Данные (HEX):        {data_block.hex().upper()}")
            print(f"  Результат (HEX):     {result_block.hex().upper()}")
        
        # Увеличиваем счетчик по модулю 2^64
        counter = (counter + 1) & 0xFFFFFFFFFFFFFFFF
    
    if verbose:
        print("=" * 80)
    
    return bytes(result)


def test_gost_example():
    """
    Тестирует на контрольном примере из ГОСТ Р 34.12-2015
    Приложение А.2
    """
    print("\n" + "=" * 80)
    print("ТЕСТ: Контрольный пример из ГОСТ Р 34.12-2015, А.2")
    print("=" * 80)
    
    # Ключ из А.2.3
    key = bytes.fromhex("ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
    
    # Открытый текст из А.2.4
    plaintext = 0xfedcba9876543210
    
    # Ожидаемый результат
    expected = 0x4ee901e5c2d8ca3d
    
    print(f"Ключ:     {key.hex().upper()}")
    print(f"Текст:    {plaintext:016X}")
    print(f"Ожидается: {expected:016X}")
    
    round_keys = generate_round_keys(key)
    result = magma_encrypt_block(plaintext, round_keys)
    
    print(f"Получено:  {result:016X}")
    
    if result == expected:
        print("✓ ТЕСТ ПРОЙДЕН!")
        return True
    else:
        print("✗ ТЕСТ НЕ ПРОЙДЕН!")
        return False


def main():
    print("=" * 80)
    print("МАГМА (ГОСТ Р 34.12-2015) в режиме гаммирования CTR")
    print("ГОСТ Р 34.13-2015")
    print("=" * 80)
    
    # Сначала запускаем тест
    test_gost_example()
    
    print("\n" + "=" * 80)
    print("ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("=" * 80)
    
    # Параметры по умолчанию
    default_key = "ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    default_iv = "12345678"
    default_data = "92def06b3c130a59"
    
    print("\nПримечание: если ввести пустую строку, будут использованы значения по умолчанию")
    
    # Ввод ключа
    k_hex = input(f"\nВведите ключ (64 HEX символа, Enter для '{default_key[:16]}...'): ").strip()
    if not k_hex:
        k_hex = default_key
        print(f"Используется ключ по умолчанию: {k_hex}")
    
    # Ввод IV
    i_hex = input(f"Введите IV (до 16 HEX символов, Enter для '{default_iv}'): ").strip()
    if not i_hex:
        i_hex = default_iv
        print(f"Используется IV по умолчанию: {i_hex}")
    
    # Дополняем IV до 16 символов (8 байт)
    i_hex = pad_iv(i_hex)
    
    # Ввод данных
    d_hex = input(f"Введите данные в HEX (Enter для '{default_data}'): ").strip()
    if not d_hex:
        d_hex = default_data
        print(f"Используются данные по умолчанию: {d_hex}")
    
    try:
        key = bytes.fromhex(k_hex)
        iv = bytes.fromhex(i_hex)
        data = bytes.fromhex(d_hex)
        
        if len(key) != 32:
            print(f"\n✗ Ошибка: ключ должен быть 32 байта (64 HEX символа), получено {len(key)} байт")
            return
        
        if len(iv) != 8:
            print(f"\n✗ Ошибка: IV должен быть 8 байт (16 HEX символов), получено {len(iv)} байт")
            return
        
        # Обработка в режиме CTR
        result = magma_ctr_process(data, key, iv, verbose=True)
        
        print("\n" + "=" * 80)
        print("ИТОГОВЫЙ РЕЗУЛЬТАТ")
        print("=" * 80)
        print(f"Ключ (HEX):      {key.hex().upper()}")
        print(f"IV (HEX):        {iv.hex().upper()}")
        print(f"Данные (HEX):    {data.hex().upper()}")
        print(f"Результат (HEX): {result.hex().upper()}")
        print("=" * 80)
        
        # Ожидаемый результат для контрольного примера
        if (k_hex.lower() == default_key.lower() and 
            i_hex.lower() == "1234567800000000" and 
            d_hex.lower() == default_data.lower()):
            print(f"\nОЖИДАЕМЫЙ РЕЗУЛЬТАТ (ГОСТ): 4E98110C97B7B93C")
            if result.hex().upper() == "4E98110C97B7B93C":
                print("✓ Результат совпадает с ГОСТ!")
            else:
                print("✗ Результат НЕ совпадает с ГОСТ!")
    
    except ValueError as e:
        print(f"\n✗ Ошибка: некорректный HEX формат - {e}")
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")


if __name__ == "__main__":
    main()