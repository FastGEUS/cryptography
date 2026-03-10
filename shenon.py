import random
import math

# Русский алфавит без Ё (32 буквы)
ALPHABET = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
M = len(ALPHABET)  # Модуль = размер алфавита = 32


def gcd(a, b):
    """Наибольший общий делитель (алгоритм Евклида)"""
    while b:
        a, b = b, a % b
    return abs(a)


def is_coprime(a, b):
    """Проверяет, являются ли числа взаимно простыми"""
    return gcd(a, b) == 1


def get_prime_factors(n):
    """Возвращает список простых делителей числа n"""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            if d not in factors:
                factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def validate_lcg_parameters(a, c, m):
    """
    Проверяет параметры линейного конгруэнтного генератора
    для максимального периода согласно теореме Халла-Доббелла
    
    Для максимального периода m требуется:
    1. c должно быть взаимно просто с m
    2. a - 1 должно делиться на все простые делители m
    3. если m кратно 4, то (a - 1) должно делиться на 4
    4. a должно быть нечетным (для символьной гаммы)
    
    Возвращает (валидность, список ошибок)
    """
    errors = []
    
    # Проверка 1: a должно быть нечетным
    if a % 2 == 0:
        errors.append(f"• a = {a} должно быть нечетным")
    
    # Проверка 2: c должно быть взаимно просто с m
    if not is_coprime(c, m):
        errors.append(f"• c = {c} должно быть взаимно просто с m = {m} (НОД = {gcd(c, m)})")
    
    # Проверка 3: (a - 1) должно делиться на все простые делители m
    b = a - 1
    prime_factors = get_prime_factors(m)
    
    for p in prime_factors:
        if b % p != 0:
            errors.append(f"• (a - 1) = {b} должно делиться на простой делитель {p} числа m = {m}")
    
    # Проверка 4: если m кратно 4, то (a - 1) должно делиться на 4
    if m % 4 == 0:
        if b % 4 != 0:
            errors.append(f"• m = {m} кратно 4, поэтому (a - 1) = {b} должно делиться на 4")
    
    return len(errors) == 0, errors


def generate_key_lcg(length, T0, a, c, m=M, verbose=False):
    """
    Генерирует ключ с помощью линейного конгруэнтного генератора (ЛКГ)
    
    Формула: T(i+1) = (a * T(i) + c) mod m
    
    length - длина ключа (количество символов)
    T0 - начальное значение (seed)
    a - множитель
    c - приращение
    m - модуль (размер алфавита, по умолчанию 32)
    verbose - выводить процесс генерации
    
    Возвращает строку ключа
    """
    key = ""
    T = T0
    
    if verbose:
        print("\n" + "=" * 80)
        print("ГЕНЕРАЦИЯ КЛЮЧА С ПОМОЩЬЮ ЛКГ")
        print("=" * 80)
        print(f"Формула: T(i+1) = (a·T(i) + c) mod m")
        print(f"Параметры: T(0) = {T0}, a = {a}, c = {c}, m = {m}")
        print("=" * 80)
        
        # Проверяем параметры
        valid, errors = validate_lcg_parameters(a, c, m)
        
        if valid:
            print("✓ Параметры обеспечивают МАКСИМАЛЬНЫЙ период генератора!")
        else:
            print("⚠ ВНИМАНИЕ: Параметры НЕ обеспечивают максимальный период:")
            for error in errors:
                print(error)
            print(f"\nМаксимальный возможный период: {m}")
            print("Текущие параметры дадут МЕНЬШИЙ период!\n")
        
        print("\nПроцесс генерации:")
        print("-" * 80)
    
    for i in range(length):
        # Генерируем следующее значение
        T_next = (a * T + c) % m
        
        # Преобразуем в символ алфавита
        char = ALPHABET[T_next]
        key += char
        
        if verbose and (i < 10 or i >= length - 3):
            print(f"  T({i}) = {T:2d} → T({i+1}) = ({a}·{T} + {c}) mod {m} = {T_next:2d} → '{char}'")
        elif verbose and i == 10:
            print("  ...")
        
        T = T_next
    
    if verbose:
        print("-" * 80)
        print(f"✓ Сгенерирован ключ длиной {length} символов")
        print("=" * 80)
    
    return key


def suggest_good_parameters(m=M):
    """
    Предлагает хорошие параметры для ЛКГ
    """
    print("\n" + "=" * 80)
    print("РЕКОМЕНДУЕМЫЕ ПАРАМЕТРЫ ДЛЯ МАКСИМАЛЬНОГО ПЕРИОДА")
    print("=" * 80)
    print(f"Модуль m = {m} = 2^5")
    print(f"Простые делители m: {get_prime_factors(m)}")
    print("\nУсловия для максимального периода {m}:")
    print("  1. a должно быть нечетным")
    print("  2. c должно быть взаимно просто с m")
    print("  3. (a - 1) должно делиться на 2 (единственный простой делитель 32)")
    print("  4. (a - 1) должно делиться на 4 (так как 32 кратно 4)")
    print("\nИз условий 1, 3, 4 следует: a = 4k + 1, где k - любое целое число")
    print("\nПРИМЕРЫ ХОРОШИХ ПАРАМЕТРОВ:")
    print("-" * 80)
    
    examples = [
        (5, 1, "a = 4·1 + 1 = 5, c нечетное и взаимно простое с 32"),
        (9, 3, "a = 4·2 + 1 = 9, c нечетное и взаимно простое с 32"),
        (13, 5, "a = 4·3 + 1 = 13, c нечетное и взаимно простое с 32"),
        (17, 7, "a = 4·4 + 1 = 17, c нечетное и взаимно простое с 32"),
        (21, 9, "a = 4·5 + 1 = 21, c нечетное и взаимно простое с 32"),
        (25, 11, "a = 4·6 + 1 = 25, c нечетное и взаимно простое с 32"),
    ]
    
    for i, (a, c, desc) in enumerate(examples, 1):
        valid, _ = validate_lcg_parameters(a, c, m)
        status = "✓" if valid else "✗"
        print(f"{status} Пример {i}: a = {a:2d}, c = {c:2d}  ({desc})")
    
    print("=" * 80)


def normalize_text(text):
    """Нормализует текст: убирает пробелы, приводит к верхнему регистру"""
    text = text.upper().replace("Ё", "Е")
    normalized = ""
    for char in text:
        if char in ALPHABET:
            normalized += char
    return normalized


def encrypt_otp(text, key, verbose=True):
    """
    Шифрование текста методом гаммирования (шифр Вернама/Шеннона)
    
    Формула: C = (P + K) mod 32
    """
    if len(text) != len(key):
        raise ValueError(f"Длина текста ({len(text)}) должна равняться длине ключа ({len(key)})")
    
    result = ""
    
    if verbose:
        print("\n" + "=" * 80)
        print("ПРОЦЕСС ШИФРОВАНИЯ")
        print("=" * 80)
        print(f"Формула: C = (P + K) mod {M}")
        print("\nПосимвольное шифрование:")
        print("-" * 80)
    
    for i in range(len(text)):
        p_char = text[i]
        k_char = key[i]
        
        p_idx = ALPHABET.find(p_char)
        k_idx = ALPHABET.find(k_char)
        
        c_idx = (p_idx + k_idx) % M
        c_char = ALPHABET[c_idx]
        
        result += c_char
        
        if verbose and (i < 10 or i >= len(text) - 3):
            print(f"  [{i+1:3d}] {p_char}({p_idx:2d}) + {k_char}({k_idx:2d}) = {c_char}({c_idx:2d})  "
                  f"[({p_idx} + {k_idx}) mod 32 = {c_idx}]")
        elif verbose and i == 10:
            print("  ...")
    
    if verbose:
        print("-" * 80)
    
    return result


def decrypt_otp(cipher, key, verbose=True):
    """
    Дешифрование текста методом гаммирования
    
    Формула: P = (C - K) mod 32
    """
    if len(cipher) != len(key):
        raise ValueError(f"Длина шифртекста ({len(cipher)}) должна равняться длине ключа ({len(key)})")
    
    result = ""
    
    if verbose:
        print("\n" + "=" * 80)
        print("ПРОЦЕСС РАСШИФРОВАНИЯ")
        print("=" * 80)
        print(f"Формула: P = (C - K) mod {M}")
        print("\nПосимвольное расшифрование:")
        print("-" * 80)
    
    for i in range(len(cipher)):
        c_char = cipher[i]
        k_char = key[i]
        
        c_idx = ALPHABET.find(c_char)
        k_idx = ALPHABET.find(k_char)
        
        p_idx = (c_idx - k_idx) % M
        p_char = ALPHABET[p_idx]
        
        result += p_char
        
        if verbose and (i < 10 or i >= len(cipher) - 3):
            print(f"  [{i+1:3d}] {c_char}({c_idx:2d}) - {k_char}({k_idx:2d}) = {p_char}({p_idx:2d})  "
                  f"[({c_idx} - {k_idx}) mod 32 = {p_idx}]")
        elif verbose and i == 10:
            print("  ...")
    
    if verbose:
        print("-" * 80)
    
    return result


# ============================================================================
# ГЛАВНАЯ ПРОГРАММА
# ============================================================================

print("=" * 80)
print("Шифр гаммирования с блокнотом Шеннона (ЛКГ)")
print("=" * 80)

print(f"\nАлфавит ({M} букв): {ALPHABET}")
print("Примечание: буква Ё заменяется на Е")

print("\nПринцип работы:")
print("• Ключ генерируется с помощью ЛКГ: T(i+1) = (a·T(i) + c) mod m")
print("• Шифрование: C = (P + K) mod 32")
print("• Расшифрование: P = (C - K) mod 32")
print("• Ключ должен быть равен длине текста")

current_key = None
current_params = None  # (T0, a, c)

while True:
    print("\n" + "=" * 80)
    print("ГЛАВНОЕ МЕНЮ")
    print("=" * 80)
    print("1 - Зашифровать текст (генерация ключа с помощью ЛКГ)")
    print("2 - Расшифровать текст (с использованием тех же параметров ЛКГ)")
    print("3 - Показать рекомендуемые параметры для ЛКГ")
    print("0 - Выход")
    
    choice = input("\nВаш выбор: ")
    
    if choice == '0':
        print("\nДо свидания!")
        break
    
    elif choice == '1':
        print("\n" + "-" * 80)
        print("ШИФРОВАНИЕ С ГЕНЕРАЦИЕЙ КЛЮЧА (ЛКГ)")
        print("-" * 80)
        
        # Ввод текста
        text = input("\nВведите текст для шифрования: ")
        
        if not text.strip():
            print("✗ Текст не может быть пустым!")
            continue
        
        normalized_text = normalize_text(text)
        
        if not normalized_text:
            print("✗ Текст не содержит русских букв!")
            continue
        
        print(f"\nИсходный текст:      {text}")
        print(f"Нормализованный:     {normalized_text}")
        print(f"Длина:               {len(normalized_text)} символов")
        
        # Ввод параметров ЛКГ
        print("\n" + "-" * 80)
        print("ПАРАМЕТРЫ ЛИНЕЙНОГО КОНГРУЭНТНОГО ГЕНЕРАТОРА (ЛКГ)")
        print("-" * 80)
        print(f"Формула: T(i+1) = (a·T(i) + c) mod {M}")
        print(f"Модуль m = {M} (размер алфавита)")
        
        # T0
        while True:
            try:
                T0 = int(input(f"\nВведите начальное значение T(0) (0-{M-1}): "))
                if 0 <= T0 < M:
                    break
                else:
                    print(f"✗ T(0) должно быть в диапазоне 0-{M-1}")
            except ValueError:
                print("✗ Введите целое число!")
        
        # a
        while True:
            try:
                a = int(input("Введите множитель a (рекомендуется: 5, 9, 13, 17, 21, 25): "))
                if a > 0:
                    break
                else:
                    print("✗ a должно быть положительным")
            except ValueError:
                print("✗ Введите целое число!")
        
        # c
        while True:
            try:
                c = int(input("Введите приращение c (рекомендуется нечетное число): "))
                if c >= 0:
                    break
                else:
                    print("✗ c должно быть неотрицательным")
            except ValueError:
                print("✗ Введите целое число!")
        
        # Сохраняем параметры
        current_params = (T0, a, c)
        
        # Генерируем ключ
        current_key = generate_key_lcg(len(normalized_text), T0, a, c, M, verbose=True)
        
        print(f"\nСгенерированный ключ: {current_key}")
        
        # Шифруем
        try:
            ciphertext = encrypt_otp(normalized_text, current_key, verbose=True)
            
            print(f"\n{'='*80}")
            print("РЕЗУЛЬТАТ ШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Открытый текст:      {normalized_text}")
            print(f"Ключ (ЛКГ):          {current_key}")
            print(f"Параметры ЛКГ:       T(0)={T0}, a={a}, c={c}, m={M}")
            print(f"Зашифрованный текст: {ciphertext}")
            print(f"Длина:               {len(ciphertext)} символов")
            print(f"\n💾 Сохраните параметры для расшифрования!")
            print(f"{'='*80}")
        
        except Exception as e:
            print(f"\n✗ Ошибка при шифровании: {e}")
    
    elif choice == '2':
        print("\n" + "-" * 80)
        print("РАСШИФРОВАНИЕ ТЕКСТА")
        print("-" * 80)
        
        # Ввод зашифрованного текста
        cipher_input = input("\nВведите зашифрованный текст: ")
        
        if not cipher_input.strip():
            print("✗ Текст не может быть пустым!")
            continue
        
        ciphertext = normalize_text(cipher_input)
        
        if not ciphertext:
            print("✗ Текст не содержит русских букв!")
            continue
        
        print(f"\nЗашифрованный текст: {ciphertext}")
        print(f"Длина:               {len(ciphertext)} символов")
        
        # Ввод параметров ЛКГ
        print("\n" + "-" * 80)
        print("ПАРАМЕТРЫ ЛКГ ДЛЯ ГЕНЕРАЦИИ КЛЮЧА")
        print("-" * 80)
        
        if current_params:
            print(f"Есть сохраненные параметры: T(0)={current_params[0]}, a={current_params[1]}, c={current_params[2]}")
            use_saved = input("Использовать сохраненные параметры? (да/нет): ")
            
            if use_saved.lower() in ['да', 'yes', 'y', 'д']:
                T0, a, c = current_params
                print(f"Используются параметры: T(0)={T0}, a={a}, c={c}")
            else:
                # Ввод параметров вручную
                T0 = int(input(f"Введите T(0) (0-{M-1}): "))
                a = int(input("Введите a: "))
                c = int(input("Введите c: "))
        else:
            T0 = int(input(f"Введите T(0) (0-{M-1}): "))
            a = int(input("Введите a: "))
            c = int(input("Введите c: "))
        
        # Генерируем ключ
        key = generate_key_lcg(len(ciphertext), T0, a, c, M, verbose=True)
        
        print(f"\nСгенерированный ключ: {key}")
        
        # Расшифровываем
        try:
            plaintext = decrypt_otp(ciphertext, key, verbose=True)
            
            print(f"\n{'='*80}")
            print("РЕЗУЛЬТАТ РАСШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Зашифрованный текст: {ciphertext}")
            print(f"Ключ (ЛКГ):          {key}")
            print(f"Параметры ЛКГ:       T(0)={T0}, a={a}, c={c}, m={M}")
            print(f"Расшифрованный текст: {plaintext}")
            print(f"Длина:               {len(plaintext)} символов")
            print(f"{'='*80}")
        
        except Exception as e:
            print(f"\n✗ Ошибка при расшифровании: {e}")
    
    elif choice == '3':
        suggest_good_parameters(M)
    
    else:
        print("\n⚠ Неверный выбор. Попробуйте снова.")