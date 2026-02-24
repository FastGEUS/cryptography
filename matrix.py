import numpy as np

# Русский алфавит без Ё (32 буквы)
ALPHABET = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
ALPHABET_SIZE = len(ALPHABET)


def text_to_indices(text):
    """Преобразует текст в последовательность индексов"""
    text = text.upper().replace('Ё', 'Е')
    indices = []
    for char in text:
        if char in ALPHABET:
            indices.append(ALPHABET.index(char)+1)
    return indices


def indices_to_text(indices):
    """Преобразует индексы обратно в текст"""
    text = ''
    for idx in indices:
        text += ALPHABET[idx % 32 - 1]
    return text


def parse_key_matrix(key_string, rows, cols):
    """
    Парсит строку с числами в матрицу
    
    key_string - строка с числами (например: "1 2 3 4 5 6")
    rows - количество строк
    cols - количество столбцов
    """
    # Разбиваем строку на числа
    numbers = key_string.replace(',', ' ').split()
    
    # Преобразуем в целые числа
    try:
        numbers = [int(num) for num in numbers if num]
    except ValueError:
        return None
    
    # Проверяем количество
    if len(numbers) != rows * cols:
        return None
    
    # Создаем матрицу
    matrix = np.array(numbers).reshape(rows, cols)
    
    return matrix


def matrix_encrypt(text, key_matrix):
    """
    Шифрует текст матричным шифром (вектор-столбцы)
    """
    rows, cols = key_matrix.shape
    indices = text_to_indices(text)
    
    # Дополняем до кратности cols
    while len(indices) % cols != 0:
        indices.append(0)  
    
    encrypted_indices = []
    
    print(f"\nПроцесс шифрования:")
    print("=" * 80)
    
    for i in range(0, len(indices), cols):
        # Создаем вертикальный вектор-столбец: cols строк, 1 столбец
        block = np.array(indices[i:i+cols]).reshape(cols, 1)
        
        print(f"\nБлок {i//cols + 1}:")
        print(f"  Вектор-столбец {cols}×1:\n{block}")
        
        # Классическое умножение: Матрица (rows×cols) × Вектор (cols×1) = Вектор (rows×1)
        result = np.dot(key_matrix, block)
        
        print(f"  Матрица-ключ {rows}×{cols}:")
        for row in key_matrix:
            print(f"    {row}")
        print(f"  Результат умножения {rows}×1:\n{result}")
        
        # Разворачиваем вертикальный вектор обратно в плоский список
        encrypted_indices.extend(result.flatten().tolist())
    
    print("=" * 80)
    return encrypted_indices


def matrix_decrypt(encrypted_indices, key_matrix):
    """
    Расшифровывает последовательность индексов (вектор-столбцы)
    """
    rows, cols = key_matrix.shape
    
    # Поиск обратной матрицы по модулю ALPHABET_SIZE
    try:
        det = int(np.round(np.linalg.det(key_matrix)))
        
        det_inv = None
        for x in range(1, ALPHABET_SIZE):
            if (det * x) % ALPHABET_SIZE == 1:
                det_inv = x
                break
        
        if det_inv is None:
            print("ОШИБКА: Невозможно найти обратную матрицу!")
            print(f"  Определитель {det} не имеет обратного по модулю {ALPHABET_SIZE}")
            return None
        
        matrix_inv = np.linalg.inv(key_matrix)
        matrix_inv = np.round(matrix_inv * det).astype(int)
        matrix_inv = (matrix_inv * det_inv) % ALPHABET_SIZE
        
    except np.linalg.LinAlgError:
        print("ОШИБКА: Матрица вырожденная!")
        return None
    
    encrypted_indices = list(encrypted_indices)
    while len(encrypted_indices) % rows != 0:
        encrypted_indices.append(0)
    
    decrypted_indices = []
    
    print(f"\nПроцесс расшифрования:")
    print("=" * 80)
    
    for i in range(0, len(encrypted_indices), rows):
        # Создаем зашифрованный вертикальный вектор-столбец: rows строк, 1 столбец
        block = np.array(encrypted_indices[i:i+rows]).reshape(rows, 1)
        
        print(f"\nБлок {i//rows + 1}:")
        print(f"  Зашифрованный вектор-столбец {rows}×1:\n{block}")
        
        # Умножение: Обратная матрица (cols×rows) × Вектор (rows×1) = Вектор (cols×1)
        result = np.dot(matrix_inv, block) % ALPHABET_SIZE
        
        print(f"  Обратная матрица {cols}×{rows}:")
        for row in matrix_inv:
            print(f"    {row}")
        print(f"  Результат умножения {cols}×1:\n{result}")
        
        decrypted_indices.extend(result.flatten().tolist())
    
    print("=" * 80)
    return decrypted_indices


def print_matrix(matrix, title="Матрица"):
    """Красиво выводит матрицу"""
    print(f"\n{title}:")
    print("-" * 40)
    for row in matrix:
        print("  ", end="")
        for val in row:
            print(f"{val:4d}", end=" ")
        print()
    print("-" * 40)


# Главная программа
print("=" * 80)
print("Матричный шифр для русского языка")
print("=" * 80)

print(f"\nАлфавит ({ALPHABET_SIZE} букв):")
for i in range(0, ALPHABET_SIZE, 8):
    line = "  "
    for j in range(i, min(i+8, ALPHABET_SIZE)):
        line += f"{ALPHABET[j]}={j+1:2d}  "
    print(line)

print("\nПримечание: буква Ё заменяется на Е")

while True:
    print("\n" + "=" * 80)
    print("Выберите действие:")
    print("1 - Зашифровать текст")
    print("2 - Расшифровать последовательность индексов")
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
        
        # Показываем индексы
        indices = text_to_indices(text)
        print(f"\nТекст в виде индексов: {indices}")
        
        # Ввод размеров матрицы
        while True:
            try:
                rows = int(input("\nВведите количество строк матрицы (минимум 3): "))
                if rows >= 3:
                    break
                else:
                    print("Количество строк должно быть не меньше 3!")
            except ValueError:
                print("Введите целое число!")
        
        while True:
            try:
                cols = int(input(f"Введите количество столбцов матрицы (минимум 3): "))
                if cols >= 3:
                    break
                else:
                    print("Количество столбцов должно быть не меньше 3!")
            except ValueError:
                print("Введите целое число!")
        
        # Ввод матрицы-ключа
        print(f"\nВведите {rows*cols} чисел для матрицы {rows}×{cols}")
        print("(числа через пробел или запятую):")
        key_string = input()
        
        # Парсим матрицу
        key_matrix = parse_key_matrix(key_string, rows, cols)
        
        if key_matrix is None:
            print(f"ОШИБКА: Нужно ввести ровно {rows*cols} чисел!")
            continue
        
        # Показываем матрицу
        print_matrix(key_matrix, f"Матрица-ключ {rows}×{cols}")
        
        # Шифруем
        encrypted_indices = matrix_encrypt(text, key_matrix)
        #encrypted_text = indices_to_text(encrypted_indices)
        
        print(f"\n{'='*80}")
        print(f"Исходный текст:           {text}")
        print(f"Исходные индексы:         {indices}")
        print(f"Размер матрицы-ключа:     {rows}×{cols}")
        print(f"Зашифрованные индексы:    {encrypted_indices}")
        #print(f"Зашифрованный текст:      {encrypted_text}")
        print(f"{'='*80}")
    
    elif choice == '2':
        print("\n" + "-" * 80)
        print("РАСШИФРОВАНИЕ")
        print("-" * 80)
        
        # Ввод зашифрованных индексов
        print("\nВведите зашифрованные индексы (числа через пробел):")
        encrypted_string = input()
        
        # Парсим индексы
        try:
            encrypted_indices = [int(x) for x in encrypted_string.replace(',', ' ').split() if x]
        except ValueError:
            print("ОШИБКА: Введите числа!")
            continue
        
        print(f"Зашифрованные индексы: {encrypted_indices}")
        #encrypted_text = indices_to_text(encrypted_indices)
        #print(f"Зашифрованный текст: {encrypted_text}")
        
        # Ввод размеров матрицы
        while True:
            try:
                rows = int(input("\nВведите количество строк матрицы (минимум 3): "))
                if rows >= 3:
                    break
                else:
                    print("Количество строк должно быть не меньше 3!")
            except ValueError:
                print("Введите целое число!")
        
        while True:
            try:
                cols = int(input(f"Введите количество столбцов матрицы (минимум 3): "))
                if cols >= 3:
                    break
                else:
                    print("Количество столбцов должно быть не меньше 3!")
            except ValueError:
                print("Введите целое число!")
        
        # Ввод матрицы-ключа
        print(f"\nВведите {rows*cols} чисел для матрицы {rows}×{cols}")
        print("(числа через пробел или запятую):")
        key_string = input()
        
        # Парсим матрицу
        key_matrix = parse_key_matrix(key_string, rows, cols)
        
        if key_matrix is None:
            print(f"ОШИБКА: Нужно ввести ровно {rows*cols} чисел!")
            continue
        
        # Показываем матрицу
        print_matrix(key_matrix, f"Матрица-ключ {rows}×{cols}")
        
        # Расшифровываем
        decrypted_indices = matrix_decrypt(encrypted_indices, key_matrix)
        
        if decrypted_indices is not None:
            decrypted_text = indices_to_text(decrypted_indices)
            
            print(f"\n{'='*80}")
            print(f"Зашифрованные индексы:    {encrypted_indices}")
            print(f"Размер матрицы-ключа:     {rows}×{cols}")
            print(f"Расшифрованные индексы:   {decrypted_indices}")
            print(f"Расшифрованный текст:     {decrypted_text}")
            print(f"{'='*80}")
    
    else:
        print("\nНеверный выбор. Попробуйте снова.")