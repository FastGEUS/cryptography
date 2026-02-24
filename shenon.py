import random

# Русский алфавит без Ё (32 буквы)
ALPHABET = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


def generate_key(length):
    """Генерирует случайный ключ заданной длины"""
    return "".join(random.choice(ALPHABET) for _ in range(length))


def normalize_text(text):
    """Нормализует текст: убирает пробелы, приводит к верхнему регистру"""
    text = text.upper().replace("Ё", "Е")
    # Убираем все символы кроме букв алфавита
    normalized = ""
    for char in text:
        if char in ALPHABET:
            normalized += char
    return normalized


def encrypt_otp(text, key):
    """
    Шифрование текста методом гаммирования (шифр Вернама/Шеннона)
    
    Формула: C = (P + K) mod 32
    где P - индекс буквы открытого текста,
        K - индекс буквы ключа,
        C - индекс буквы шифртекста
    """
    if len(text) != len(key):
        raise ValueError(f"Длина текста ({len(text)}) должна равняться длине ключа ({len(key)})")
    
    result = ""
    
    print("\n" + "=" * 80)
    print("ПРОЦЕСС ШИФРОВАНИЯ")
    print("=" * 80)
    print(f"\nФормула: C = (P + K) mod {len(ALPHABET)}")
    print("\nПосимвольное шифрование:")
    print("-" * 80)
    
    for i in range(len(text)):
        # Находим индексы буквы текста и буквы ключа
        p_char = text[i]
        k_char = key[i]
        
        p_idx = ALPHABET.find(p_char)
        k_idx = ALPHABET.find(k_char)
        
        # Складываем индексы по модулю 32
        c_idx = (p_idx + k_idx) % len(ALPHABET)
        c_char = ALPHABET[c_idx]
        
        result += c_char
        
        # Выводим подробную информацию (первые 10 символов)
        if i < 10 or i >= len(text) - 3:
            print(f"  [{i+1:3d}] {p_char}({p_idx:2d}) + {k_char}({k_idx:2d}) = {c_char}({c_idx:2d})  "
                  f"[({p_idx} + {k_idx}) mod 32 = {c_idx}]")
        elif i == 10:
            print("  ...")
    
    print("-" * 80)
    
    return result


def decrypt_otp(cipher, key):
    """
    Дешифрование текста методом гаммирования
    
    Формула: P = (C - K) mod 32
    где C - индекс буквы шифртекста,
        K - индекс буквы ключа,
        P - индекс буквы открытого текста
    """
    if len(cipher) != len(key):
        raise ValueError(f"Длина шифртекста ({len(cipher)}) должна равняться длине ключа ({len(key)})")
    
    result = ""
    
    print("\n" + "=" * 80)
    print("ПРОЦЕСС РАСШИФРОВАНИЯ")
    print("=" * 80)
    print(f"\nФормула: P = (C - K) mod {len(ALPHABET)}")
    print("\nПосимвольное расшифрование:")
    print("-" * 80)
    
    for i in range(len(cipher)):
        # Находим индексы буквы шифртекста и буквы ключа
        c_char = cipher[i]
        k_char = key[i]
        
        c_idx = ALPHABET.find(c_char)
        k_idx = ALPHABET.find(k_char)
        
        # Вычитаем индекс ключа по модулю 32
        p_idx = (c_idx - k_idx) % len(ALPHABET)
        p_char = ALPHABET[p_idx]
        
        result += p_char
        
        # Выводим подробную информацию (первые 10 символов)
        if i < 10 or i >= len(cipher) - 3:
            print(f"  [{i+1:3d}] {c_char}({c_idx:2d}) - {k_char}({k_idx:2d}) = {p_char}({p_idx:2d})  "
                  f"[({c_idx} - {k_idx}) mod 32 = {p_idx}]")
        elif i == 10:
            print("  ...")
    
    print("-" * 80)
    
    return result


# Главная программа
print("=" * 80)
print("Шифр гаммирования (Шифр Вернама/Шеннона)")
print("=" * 80)

print(f"\nАлфавит ({len(ALPHABET)} букв): {ALPHABET}")
print("Примечание: буква Ё заменяется на Е")

print("\nПринцип работы:")
print("• Шифрование: C = (P + K) mod 32")
print("• Расшифрование: P = (C - K) mod 32")
print("• Ключ должен быть равен длине текста")
print("• Ключ используется только один раз (One-Time Pad)")

# Глобальная переменная для текущего ключа
current_key = None

while True:
    print("\n" + "=" * 80)
    print("ГЛАВНОЕ МЕНЮ")
    print("=" * 80)
    print("1 - Зашифровать текст (с генерацией нового ключа)")
    print("2 - Зашифровать текст (с вводом своего ключа)")
    print("3 - Расшифровать текст")
    print("0 - Выход")
    
    choice = input("\nВаш выбор: ")
    
    if choice == '0':
        print("\nДо свидания!")
        break
    
    elif choice == '1':
        print("\n" + "-" * 80)
        print("ШИФРОВАНИЕ С ГЕНЕРАЦИЕЙ КЛЮЧА")
        print("-" * 80)
        
        # Ввод текста
        text = input("\nВведите текст для шифрования: ")
        
        if not text.strip():
            print("✗ Текст не может быть пустым!")
            continue
        
        # Нормализуем текст
        normalized_text = normalize_text(text)
        
        if not normalized_text:
            print("✗ Текст не содержит русских букв!")
            continue
        
        print(f"\nИсходный текст:      {text}")
        print(f"Длина текста:        {len(normalized_text)} символов")
        
        # Генерируем ключ
        current_key = generate_key(len(normalized_text))
        print(f"\n✓ Сгенерирован случайный ключ длиной {len(current_key)} символов")
        print(f"Ключ: {current_key}")
        
        # Шифруем
        try:
            ciphertext = encrypt_otp(normalized_text, current_key)
            
            print(f"\n{'='*80}")
            print("РЕЗУЛЬТАТ ШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Открытый текст:      {normalized_text}")
            print(f"Ключ:                {current_key}")
            print(f"Зашифрованный текст: {ciphertext}")
            print(f"Длина:               {len(ciphertext)} символов")
            print(f"{'='*80}")
        
        except Exception as e:
            print(f"\n✗ Ошибка при шифровании: {e}")
    
    elif choice == '2':
        print("\n" + "-" * 80)
        print("ШИФРОВАНИЕ С ВВОДОМ СВОЕГО КЛЮЧА")
        print("-" * 80)
        
        # Ввод текста
        text = input("\nВведите текст для шифрования: ")
        
        if not text.strip():
            print("✗ Текст не может быть пустым!")
            continue
        
        # Нормализуем текст
        normalized_text = normalize_text(text)
        
        if not normalized_text:
            print("✗ Текст не содержит русских букв!")
            continue
        
        print(f"\nИсходный текст:        {text}")
        print(f"Длина текста:          {len(normalized_text)} символов")
        
        # Ввод ключа
        key_input = input(f"\nВведите ключ ({len(normalized_text)} символов): ")
        current_key = normalize_text(key_input)
        
        if len(current_key) != len(normalized_text):
            print(f"\n✗ ОШИБКА: Длина ключа ({len(current_key)}) не равна длине текста ({len(normalized_text)})")
            print(f"  Ключ должен содержать ровно {len(normalized_text)} русских букв")
            continue
        
        print(f"Нормализованный ключ: {current_key}")
        
        # Шифруем
        try:
            ciphertext = encrypt_otp(normalized_text, current_key)
            
            print(f"\n{'='*80}")
            print("РЕЗУЛЬТАТ ШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Открытый текст:      {normalized_text}")
            print(f"Ключ:                {current_key}")
            print(f"Зашифрованный текст: {ciphertext}")
            print(f"Длина:               {len(ciphertext)} символов")
            print(f"{'='*80}")
        
        except Exception as e:
            print(f"\n✗ Ошибка при шифровании: {e}")
    
    elif choice == '3':
        print("\n" + "-" * 80)
        print("РАСШИФРОВАНИЕ ТЕКСТА")
        print("-" * 80)
        
        # Ввод зашифрованного текста
        cipher_input = input("\nВведите зашифрованный текст: ")
        
        if not cipher_input.strip():
            print("✗ Текст не может быть пустым!")
            continue
        
        # Нормализуем текст
        ciphertext = normalize_text(cipher_input)
        
        if not ciphertext:
            print("✗ Текст не содержит русских букв!")
            continue
        
        print(f"\nЗашифрованный текст: {ciphertext}")
        print(f"Длина текста:        {len(ciphertext)} символов")
        
        key_input = input(f"\nВведите ключ ({len(ciphertext)} символов): ")
        key = normalize_text(key_input)
        
        if len(key) != len(ciphertext):
            print(f"\n✗ ОШИБКА: Длина ключа ({len(key)}) не равна длине шифртекста ({len(ciphertext)})")
            print(f"  Ключ должен содержать ровно {len(ciphertext)} русских букв")
            continue
        
        # Расшифровываем
        try:
            plaintext = decrypt_otp(ciphertext, key)
            
            print(f"\n{'='*80}")
            print("РЕЗУЛЬТАТ РАСШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Зашифрованный текст: {ciphertext}")
            print(f"Ключ:                {key}")
            print(f"Расшифрованный текст: {plaintext}")
            print(f"Длина:               {len(plaintext)} символов")
            print(f"{'='*80}")
        
        except Exception as e:
            print(f"\n✗ Ошибка при расшифровании: {e}")
    else:
        print("\n⚠ Неверный выбор. Попробуйте снова.")