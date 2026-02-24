# Русский алфавит без Ё (32 буквы)
ALPHABET = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'


def clean_text(text):
    """Очищает текст, оставляя только буквы русского алфавита"""
    text = text.upper().replace('Ё', 'Е')
    cleaned = ''
    for char in text:
        if char in ALPHABET:
            cleaned += char
    return cleaned


def generate_key_order(keyword):
    """
    Генерирует порядок столбцов на основе ключевого слова
    
    Например: КЛЮЧ -> [1, 3, 4, 2]
    К=1, Л=3, Ю=4, Ч=2 (по алфавитному порядку)
    """
    # Очищаем ключевое слово
    keyword = clean_text(keyword)
    
    # Создаем список кортежей (буква, исходная_позиция)
    indexed_chars = [(char, i) for i, char in enumerate(keyword)]
    
    # Сортируем по буквам
    sorted_chars = sorted(indexed_chars, key=lambda x: x[0])
    
    # Создаем массив порядка
    order = [0] * len(keyword)
    for rank, (char, original_pos) in enumerate(sorted_chars):
        order[original_pos] = rank + 1
    
    return order


def get_padding_chars(num_needed):
    """
    Запрашивает у пользователя дополняющие символы
    
    num_needed - сколько символов нужно
    """
    print(f"\nТекст нужно дополнить до кратности количеству столбцов!")
    print(f"Требуется добавить {num_needed} символ(ов)")
    
    while True:
        padding = input(f"Введите {num_needed} букву(-ы) для заполнения: ").upper().replace('Ё', 'Е')
        
        # Оставляем только буквы алфавита
        clean_padding = ''
        for char in padding:
            if char in ALPHABET:
                clean_padding += char
        
        if len(clean_padding) == num_needed:
            return clean_padding
        elif len(clean_padding) < num_needed:
            print(f"Недостаточно символов! Нужно {num_needed}, введено {len(clean_padding)}")
        else:
            print(f"Слишком много символов! Нужно {num_needed}, введено {len(clean_padding)}")
            print(f"  Будут использованы первые {num_needed} символа: {clean_padding[:num_needed]}")
            confirm = input("Продолжить? (да/нет): ")
            if confirm.lower() in ['да', 'yes', 'y', 'д']:
                return clean_padding[:num_needed]


def vertical_permutation_encrypt(text, keyword):
    """
    Шифрует текст методом вертикальной перестановки
    
    text - открытый текст
    keyword - ключевое слово
    """
    # Очищаем текст
    original_text = text
    text = clean_text(text)
    keyword = clean_text(keyword)
    
    if not keyword:
        return "Ошибка: ключевое слово пустое!"
    
    if not text:
        return "Ошибка: текст пустой!"
    
    # Получаем порядок столбцов
    key_order = generate_key_order(keyword)
    num_cols = len(keyword)
    
    print(f"\nДлина текста: {len(text)} символов")
    print(f"Количество столбцов: {num_cols}")
    
    # Проверяем, нужно ли дополнение
    remainder = len(text) % num_cols
    if remainder != 0:
        num_needed = num_cols - remainder
        padding = get_padding_chars(num_needed)
        text += padding
        print(f"✓ Текст дополнен: '{padding}'")
        print(f"Новая длина текста: {len(text)} символов")
    else:
        print("✓ Дополнение не требуется")
    
    # Вычисляем количество строк
    num_rows = len(text) // num_cols
    
    # Создаем таблицу
    table = []
    index = 0
    for row in range(num_rows):
        table_row = []
        for col in range(num_cols):
            table_row.append(text[index])
            index += 1
        table.append(table_row)
    
    # Выводим таблицу ДО перестановки
    print("\n" + "=" * 80)
    print("ТАБЛИЦА ШИФРОВАНИЯ (запись построчно)")
    print("=" * 80)
    print("\nКлючевое слово: " + keyword)
    print("Порядок столбцов: " + str(key_order))
    print("\nТаблица:")
    
    # Заголовок
    header = "     "
    for col in range(num_cols):
        header += f"{keyword[col]:^5}"
    print(header)
    
    header2 = "     "
    for col in range(num_cols):
        header2 += f"({col+1}){' '*2}"
    print(header2)
    
    print("     " + "─" * (num_cols * 5))
    
    # Строки таблицы
    for i, row in enumerate(table):
        row_str = f"{i+1:3d} │ "
        for cell in row:
            row_str += f"{cell:^5}"
        print(row_str)
    
    print("=" * 80)
    
    # Читаем столбцы в порядке ключа
    encrypted = ""
    
    print("\nПроцесс шифрования (чтение столбцов в порядке номеров):")
    print("-" * 80)
    
    # Создаем список (позиция_в_порядке, индекс_столбца)
    column_positions = [(key_order[i], i) for i in range(num_cols)]
    # Сортируем по позиции в порядке
    column_positions.sort(key=lambda x: x[0])
    
    for rank, col_index in column_positions:
        column_text = ""
        for row in range(num_rows):
            column_text += table[row][col_index]
        encrypted += column_text
        print(f"Столбец №{rank} - '{keyword[col_index]}' (позиция {col_index+1}): {column_text}")
    
    print("-" * 80)
    
    return encrypted


def vertical_permutation_decrypt(encrypted_text, keyword):
    """
    Расшифровывает текст методом вертикальной перестановки
    
    encrypted_text - зашифрованный текст
    keyword - ключевое слово
    """
    # Очищаем текст
    encrypted_text = clean_text(encrypted_text)
    keyword = clean_text(keyword)
    
    if not keyword:
        return "Ошибка: ключевое слово пустое!"
    
    if not encrypted_text:
        return "Ошибка: текст пустой!"
    
    # Получаем порядок столбцов
    key_order = generate_key_order(keyword)
    num_cols = len(keyword)
    
    print(f"\nДлина зашифрованного текста: {len(encrypted_text)} символов")
    print(f"Количество столбцов: {num_cols}")
    
    # Вычисляем количество строк
    if len(encrypted_text) % num_cols != 0:
        print(f"ПРЕДУПРЕЖДЕНИЕ: длина текста ({len(encrypted_text)}) не кратна количеству столбцов ({num_cols})")
        print(f"  Возможно, текст поврежден или использован неверный ключ")
    
    num_rows = len(encrypted_text) // num_cols
    print(f"Количество строк: {num_rows}")
    
    # Создаем пустую таблицу
    table = [['' for _ in range(num_cols)] for _ in range(num_rows)]
    
    # Заполняем таблицу по столбцам в порядке ключа
    print("\n" + "=" * 80)
    print("ТАБЛИЦА РАСШИФРОВАНИЯ")
    print("=" * 80)
    print("\nКлючевое слово: " + keyword)
    print("Порядок столбцов: " + str(key_order))
    print("\nПроцесс расшифрования (запись в столбцы по порядку номеров):")
    print("-" * 80)
    
    # Создаем список (позиция_в_порядке, индекс_столбца)
    column_positions = [(key_order[i], i) for i in range(num_cols)]
    # Сортируем по позиции в порядке
    column_positions.sort(key=lambda x: x[0])
    
    text_index = 0
    for rank, col_index in column_positions:
        column_text = ""
        for row in range(num_rows):
            if text_index < len(encrypted_text):
                table[row][col_index] = encrypted_text[text_index]
                column_text += encrypted_text[text_index]
                text_index += 1
        print(f"Столбец №{rank} - '{keyword[col_index]}' (позиция {col_index+1}): {column_text}")
    
    print("-" * 80)
    
    # Выводим таблицу
    print("\nТаблица:")
    
    # Заголовок
    header = "     "
    for col in range(num_cols):
        header += f"{keyword[col]:^5}"
    print(header)
    
    header2 = "     "
    for col in range(num_cols):
        header2 += f"({col+1}){' '*2}"
    print(header2)
    
    print("     " + "─" * (num_cols * 5))
    
    # Строки таблицы
    for i, row in enumerate(table):
        row_str = f"{i+1:3d} │ "
        for cell in row:
            row_str += f"{cell:^5}"
        print(row_str)
    
    print("=" * 80)
    
    # Читаем таблицу построчно
    decrypted = ""
    print("\nЧтение расшифрованного текста построчно:")
    print("-" * 80)
    for i, row in enumerate(table):
        row_text = ''.join(row)
        decrypted += row_text
        print(f"Строка {i+1}: {row_text}")
    print("-" * 80)
    
    return decrypted


# Главная программа
print("=" * 80)
print("Шифр вертикальной перестановки для русского языка")
print("=" * 80)

print(f"\nАлфавит ({len(ALPHABET)} букв): {ALPHABET}")
print("Примечание: буква Ё заменяется на Е")

print("\nПринцип работы:")
print("1. Текст записывается в таблицу построчно")
print("2. Столбцы нумеруются по алфавитному порядку букв ключевого слова")
print("3. Шифртекст читается по столбцам в порядке их номеров")

while True:
    print("\n" + "=" * 80)
    print("Выберите действие:")
    print("1 - Зашифровать текст")
    print("2 - Расшифровать текст")
    print("0 - Выход")
    
    choice = input("\nВаш выбор: ")
    
    if choice == '0':
        print("\nДо свидания!")
        break
    
    elif choice == '1':
        print("\n" + "-" * 80)
        print("ШИФРОВАНИЕ ТЕКСТА")
        print("-" * 80)
        
        # Ввод текста
        text = input("\nВведите текст для шифрования: ")
        
        if not text.strip():
            print("Текст не может быть пустым!")
            continue
        
        # Ввод ключевого слова
        keyword = input("Введите ключевое слово: ")
        
        if not keyword.strip():
            print("Ключевое слово не может быть пустым!")
            continue
        
        # Очищаем для проверки
        clean_keyword = clean_text(keyword)
        if len(clean_keyword) < 2:
            print("Ключевое слово должно содержать минимум 2 буквы!")
            continue
        
        # Шифруем
        encrypted = vertical_permutation_encrypt(text, keyword)
        
        if encrypted and not encrypted.startswith("Ошибка"):
            print(f"\n{'='*80}")
            print("РЕЗУЛЬТАТ ШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Исходный текст:       {text}")
            print(f"Ключевое слово:       {keyword}")
            print(f"Зашифрованный текст:  {encrypted}")
            print(f"Длина:                {len(encrypted)} символов")
            print(f"{'='*80}")
        else:
            print(f"\n{encrypted}")
    
    elif choice == '2':
        print("\n" + "-" * 80)
        print("РАСШИФРОВАНИЕ ТЕКСТА")
        print("-" * 80)
        
        # Ввод зашифрованного текста
        encrypted_text = input("\nВведите зашифрованный текст: ")
        
        if not encrypted_text.strip():
            print("Текст не может быть пустым!")
            continue
        
        # Ввод ключевого слова
        keyword = input("Введите ключевое слово: ")
        
        if not keyword.strip():
            print("Ключевое слово не может быть пустым!")
            continue
        
        # Очищаем для проверки
        clean_keyword = clean_text(keyword)
        if len(clean_keyword) < 2:
            print("Ключевое слово должно содержать минимум 2 буквы!")
            continue
        
        # Расшифровываем
        decrypted = vertical_permutation_decrypt(encrypted_text, keyword)
        
        if decrypted and not decrypted.startswith("Ошибка"):
            print(f"\n{'='*80}")
            print("РЕЗУЛЬТАТ РАСШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Зашифрованный текст:  {encrypted_text}")
            print(f"Ключевое слово:       {keyword}")
            print(f"Расшифрованный текст: {decrypted}")
            print(f"Длина:                {len(decrypted)} символов")
            print(f"{'='*80}")
        else:
            print(f"\n{decrypted}")
    
    else:
        print("\nНеверный выбор. Попробуйте снова.")