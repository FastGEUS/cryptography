def atbash_russian(text):
    """Шифрует текст шифром АТБАШ для русского алфавита"""
    russian_lower = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
    russian_upper = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    
    # Создаём обратный алфавит
    reversed_lower = russian_lower[::-1]
    reversed_upper = russian_upper[::-1]
    
    result = ''
    
    for char in text:
        if char in russian_lower:
            # Находим индекс буквы и заменяем на соответствующую из обратного алфавита
            index = russian_lower.index(char)
            result += reversed_lower[index]
        elif char in russian_upper:
            index = russian_upper.index(char)
            result += reversed_upper[index]
        else:
            # Оставляем все остальные символы без изменений (пробелы, знаки препинания)
            result += char
    
    return result


# Основная программа
print("Шифр АТБАШ для русского языка")
print("-" * 40)

poslovitsa = input("Введите пословицу: ")
encrypted = atbash_russian(poslovitsa)

print(f"\nИсходная пословица: {poslovitsa}")
print(f"Зашифрованная: {encrypted}")

# Проверка - дешифровка (АТБАШ симметричен)
decrypted = atbash_russian(encrypted)
print(f"Расшифрованная: {decrypted}")
