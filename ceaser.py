def caesar_encrypt(text, shift):
    """Шифрует текст шифром Цезаря"""
    russian_lower = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
    russian_upper = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    
    result = ''

    if shift >= 32 or shift == 0:
        return 0
    
    for char in text:
        if char in russian_lower:
            # Находим индекс буквы
            index = russian_lower.index(char)
            # Сдвигаем на shift позиций с циклическим переносом
            new_index = (index + shift) % len(russian_lower)
            result += russian_lower[new_index]
        elif char in russian_upper:
            index = russian_upper.index(char)
            new_index = (index + shift) % len(russian_upper)
            result += russian_upper[new_index]
        else:
            # Оставляем пробелы, знаки препинания без изменений
            result += char
    
    return result


def caesar_decrypt(text, shift):
    """Расшифровывает текст шифра Цезаря"""
    # Расшифровка = шифрование с отрицательным сдвигом
    return caesar_encrypt(text, -shift)


def brute_force(encrypted_text):
    """Перебирает все возможные сдвиги для взлома шифра"""
    print("\n" + "=" * 60)
    print("ПЕРЕБОР ВСЕХ ВОЗМОЖНЫХ СДВИГОВ:")
    print("=" * 60)
    
    for shift in range(1, 32):
        decrypted = caesar_decrypt(encrypted_text, shift)
        print(f"Сдвиг {shift:2d}: {decrypted}")

# Основная программа
print("=" * 60)
print("Шифр Цезаря для русского языка")
print("=" * 60)

while True:
    print("\nВыберите действие:")
    print("1 - Зашифровать текст")
    print("2 - Расшифровать текст")
    print("0 - Выход")
    
    choice = input("\nВаш выбор: ")
    
    if choice == '0':
        print("До свидания!")
        break
    
    elif choice == '1':
        text = input("\nВведите текст для шифрования: ")
        shift = int(input("Введите величину сдвига (1-31): "))
        
        encrypted = caesar_encrypt(text, shift)
        if encrypted == 0:
            print("Ключ не находится в диапазоне 1-31, пожалуйста, поменяйте ключ")
        else:
            print(f"\nИсходный текст: {text}")
            print(f"Сдвиг: {shift}")
            print(f"Зашифрованный текст: {encrypted}")
    
    elif choice == '2':
        text = input("\nВведите зашифрованный текст: ")
        shift = int(input("Введите величину сдвига (1-31): "))
        
        decrypted = caesar_decrypt(text, shift)
        print(f"\nЗашифрованный текст: {text}")
        print(f"Сдвиг: {shift}")
        print(f"Расшифрованный текст: {decrypted}")
    
    else:
        print("Неверный выбор. Попробуйте снова.")