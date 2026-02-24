import sys

# Таблицы замен (S-блоки) согласно ГОСТ Р 34.12-2015
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

def sub_bytes(value_32bit):
    """Преобразование в S-блоках (32 бита -> 32 бита)"""
    res = 0
    for i in range(8):
        # Извлекаем 4 бита (тетраду)
        nibble = (value_32bit >> (4 * i)) & 0xF
        # Заменяем по соответствующей таблице и сдвигаем обратно
        res |= (PI[i][nibble] << (4 * i))
    return res

def l_transformation(value_32bit):
    """Циклический сдвиг влево на 11 бит"""
    return ((value_32bit << 11) & 0xFFFFFFFF) | (value_32bit >> 21)

def g_transformation(a, k):
    """Преобразование g[k](a) = Rot11(S(a + k mod 2^32))"""
    # 1. Сложение по модулю 2^32
    internal_sum = (a + k) & 0xFFFFFFFF
    # 2. Табличная замена
    s_box_res = sub_bytes(internal_sum)
    # 3. Циклический сдвиг
    return l_transformation(s_box_res)

def G_transformation(key_32bit, data_64bit):
    """Преобразование G[k](a1, a0) = (a0, g[k](a0) ^ a1)"""
    a1 = (data_64bit >> 32) & 0xFFFFFFFF
    a0 = data_64bit & 0xFFFFFFFF
    
    g_res = g_transformation(a0, key_32bit)
    
    new_a1 = a0
    new_a0 = g_res ^ a1
    
    return (new_a1 << 32) | new_a0

def input_hex(prompt, length):
    """Ввод и проверка hex-значения"""
    while True:
        val = input(prompt).strip().replace(" ", "")
        try:
            if len(val) != length:
                raise ValueError(f"Ожидалось {length} символов (HEX)")
            return int(val, 16)
        except ValueError as e:
            print(f"Ошибка: {e}. Попробуйте снова.")

# --- Основной интерфейс ---
if __name__ == "__main__":
    print("="*60)
    print("ТЕСТИРОВАНИЕ ПРЕОБРАЗОВАНИЙ МАГМА (ГОСТ Р 34.12-2015)")
    print("="*60)

    while True:
        print("\nВыберите тип операции:")
        print("1 - Преобразование g[k] (32 бита)")
        print("2 - Преобразование G[k] (раунд Фейстеля, 64 бита)")
        print("0 - Выход")
        
        choice = input("\nВаш выбор: ")

        if choice == '1':
            a = input_hex("Введите аргумент 'a' (8 HEX симв, 32 бита): ", 8)
            k = input_hex("Введите ключ 'k'     (8 HEX симв, 32 бита): ", 8)
            
            res = g_transformation(a, k)
            print(f"\nРезультат g[k](a): {res:08x}")

        elif choice == '2':
            data = input_hex("Введите блок данных  (16 HEX симв, 64 бита): ", 16)
            k = input_hex("Введите раундовый ключ (8 HEX симв, 32 бита): ", 8)
            
            res = G_transformation(k, data)
            print(f"\nРезультат G[k](data): {res:016x}")
            
            # Пояснение структуры Фейстеля
            new_a1 = res >> 32
            new_a0 = res & 0xFFFFFFFF
            print(f"  Левая часть (L'):  {new_a1:08x}")
            print(f"  Правая часть (R'): {new_a0:08x}")

        elif choice == '0':
            break
        else:
            print("Неверный ввод.")