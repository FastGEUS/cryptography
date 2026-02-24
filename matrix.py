import numpy as np
import time

# Русский алфавит без Ё (32 буквы)
ALPHABET = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
ALPHABET_SIZE = len(ALPHABET)


def text_to_indices(text):
    """Преобразует текст в последовательность индексов (начиная с 1)"""
    text = text.upper().replace('Ё', 'Е')
    indices = []
    for char in text:
        if char in ALPHABET:
            indices.append(ALPHABET.index(char) + 1)  # Индексы с 1
    return indices


def indices_to_text(indices):
    """Преобразует индексы обратно в текст"""
    text = ''
    for idx in indices:
        # Приводим к диапазону 1-32
        idx = ((idx - 1) % ALPHABET_SIZE) + 1
        text += ALPHABET[idx - 1]
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


def gcd(a, b):
    """Наибольший общий делитель"""
    while b:
        a, b = b, a % b
    return abs(a)


def mod_inverse(a, m):
    """Находит обратный элемент по модулю m"""
    a = a % m
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return None


def matrix_mod_inverse(matrix, mod):
    """
    Находит обратную матрицу по модулю
    Возвращает (обратная_матрица, успех)
    """
    size = matrix.shape[0]
    
    # Матрица должна быть квадратной
    if matrix.shape[0] != matrix.shape[1]:
        return None, False
    
    # Вычисляем определитель
    det = int(np.round(np.linalg.det(matrix)))
    det_mod = det % mod
    
    # Проверяем, что определитель взаимно прост с модулем
    if gcd(det_mod, mod) != 1:
        return None, False
    
    # Находим обратный элемент к определителю
    det_inv = mod_inverse(det_mod, mod)
    if det_inv is None:
        return None, False
    
    # Вычисляем обратную матрицу
    try:
        # Используем стандартную обратную матрицу
        matrix_inv_float = np.linalg.inv(matrix)
        
        # Умножаем на определитель и округляем
        adjugate = np.round(matrix_inv_float * det).astype(int)
        
        # Умножаем на обратный определитель по модулю
        matrix_inv = (adjugate * det_inv) % mod
        
        return matrix_inv, True
        
    except np.linalg.LinAlgError:
        return None, False


def check_matrix_invertible(matrix, mod):
    """
    Проверяет, существует ли обратная матрица
    Возвращает (существует, определитель, НОД)
    """
    if matrix.shape[0] != matrix.shape[1]:
        return False, None, None
    
    det = int(np.round(np.linalg.det(matrix)))
    det_mod = det % mod
    gcd_value = gcd(det_mod, mod)
    
    return gcd_value == 1, det_mod, gcd_value


def matrix_encrypt(text, key_matrix):
    """
    Шифрует текст матричным шифром
    
    Согласно примеру из скриншота:
    C = A · B
    где A - матрица-ключ (m×n)
        B - вертикальный вектор индексов (n×1)
        C - результат (m×1)
    
    Компоненты вектора C вычисляются так:
    c_i = a_i1·b_1 + a_i2·b_2 + ... + a_in·b_n
    
    ВАЖНО: результат НЕ берется по модулю!
    """
    # Определяем размеры матрицы
    m, n = key_matrix.shape  # m строк, n столбцов
    
    # Преобразуем текст в индексы (с 1)
    indices = text_to_indices(text)
    
    # Дополняем до кратности n
    while len(indices) % n != 0:
        indices.append(1)  # Дополняем буквой 'А' (индекс 1)
    
    # Шифруем блоками
    encrypted_indices = []
    
    print(f"\nПроцесс шифрования:")
    print("=" * 80)
    print(f"Размер матрицы-ключа A: {m}×{n}")
    print(f"Размер вектора открытого текста B: {n}×1 (вертикальный)")
    print(f"Размер вектора зашифрованного текста C: {m}×1 (вертикальный)")
    print(f"Формула: C = A · B")
    print("=" * 80)
    
    for block_num in range(0, len(indices), n):
        # Берем блок размером n×1 (вертикальная матрица)
        B = np.array(indices[block_num:block_num+n]).reshape(n, 1)
        
        print(f"\n{'─'*80}")
        print(f"Блок {block_num//n + 1}:")
        print(f"\nВектор B ({n}×1) - открытый текст:")
        for i, val in enumerate(B):
            print(f"  b_{i+1} = {val[0]:3d}  (буква '{ALPHABET[val[0]-1]}')")
        
        # Умножаем: A (m×n) · B (n×1) = C (m×1)
        C = np.dot(key_matrix, B)
        
        print(f"\nМатрица-ключ A ({m}×{n}):")
        for i in range(m):
            row_str = "  "
            for j in range(n):
                row_str += f"{key_matrix[i][j]:4d} "
            print(row_str)
        
        print(f"\nВычисление компонентов вектора C ({m}×1):")
        for i in range(m):
            calculation = ""
            terms = []
            result = 0
            for j in range(n):
                a_ij = key_matrix[i][j]
                b_j = B[j][0]
                product = a_ij * b_j
                result += product
                terms.append(f"{a_ij}·{b_j}")
            
            calculation = " + ".join(terms)
            print(f"  c_{i+1} = {calculation}")
            print(f"      = {' + '.join([str(key_matrix[i][j] * B[j][0]) for j in range(n)])}")
            print(f"      = {result}")
        
        print(f"\nРезультат C ({m}×1):")
        for i, val in enumerate(C):
            print(f"  c_{i+1} = {val[0]:3d}")
        
        encrypted_indices.extend(C.flatten().tolist())
    
    print("=" * 80)
    
    return encrypted_indices


def matrix_decrypt(encrypted_indices, key_matrix):
    """
    Расшифровывает последовательность индексов
    
    Для расшифрования нужна обратная матрица A^(-1)
    B = A^(-1) · C (по модулю 32)
    """
    # Определяем размеры матрицы
    m, n = key_matrix.shape
    
    # Проверяем, что матрица квадратная
    if m != n:
        print("ОШИБКА: Для расшифрования матрица должна быть квадратной!")
        return None
    
    # Находим обратную матрицу по модулю 32
    matrix_inv, success = matrix_mod_inverse(key_matrix, ALPHABET_SIZE)
    
    if not success:
        print("ОШИБКА: Невозможно найти обратную матрицу!")
        return None
    
    print(f"\nОбратная матрица A^(-1) ({n}×{n}) по модулю {ALPHABET_SIZE}:")
    for row in matrix_inv:
        row_str = "  "
        for val in row:
            row_str += f"{val:4d} "
        print(row_str)
    
    # Дополняем до кратности m
    encrypted_indices = list(encrypted_indices)
    while len(encrypted_indices) % m != 0:
        encrypted_indices.append(1)
    
    # Расшифровываем блоками
    decrypted_indices = []
    
    print(f"\nПроцесс расшифрования:")
    print("=" * 80)
    
    for block_num in range(0, len(encrypted_indices), m):
        # Берем блок размером m×1
        C = np.array(encrypted_indices[block_num:block_num+m]).reshape(m, 1)
        
        print(f"\nБлок {block_num//m + 1}:")
        print(f"  Зашифрованный вектор C ({m}×1):")
        for i, val in enumerate(C):
            print(f"    c_{i+1} = {val[0]:3d}")
        
        # Умножаем: A^(-1) (n×m) · C (m×1) = B (n×1)
        B = np.dot(matrix_inv, C) % ALPHABET_SIZE
        
        # Приводим к диапазону 1-32
        B = ((B - 1) % ALPHABET_SIZE) + 1
        
        print(f"  Расшифрованный вектор B ({n}×1):")
        for i, val in enumerate(B):
            print(f"    b_{i+1} = {val[0]:3d}  (буква '{ALPHABET[val[0]-1]}')")
        
        decrypted_indices.extend(B.flatten().tolist())
    
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

print(f"\nАлфавит ({ALPHABET_SIZE} букв, индексация с 1):")
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
        print(f"\nТекст в виде индексов (начиная с 1): {indices}")
        print(f"Текст: {' '.join([f'{ALPHABET[i-1]}({i})' for i in indices])}")
        
        # Ввод размеров матрицы
        while True:
            try:
                rows = int(input("\nВведите количество строк матрицы-ключа (минимум 3): "))
                if rows >= 3:
                    break
                else:
                    print("Количество строк должно быть не меньше 3!")
            except ValueError:
                print("Введите целое число!")
        
        while True:
            try:
                cols = int(input(f"Введите количество столбцов матрицы-ключа (минимум 3): "))
                if cols >= 3:
                    break
                else:
                    print("Количество столбцов должно быть не меньше 3!")
            except ValueError:
                print("Введите целое число!")
        
        # Ввод матрицы-ключа
        print(f"\nВведите {rows*cols} чисел для матрицы-ключа {rows}×{cols}")
        print("(числа через пробел или запятую, построчно):")
        key_string = input()
        
        # Парсим матрицу
        key_matrix = parse_key_matrix(key_string, rows, cols)
        
        if key_matrix is None:
            print(f"ОШИБКА: Нужно ввести ровно {rows*cols} чисел!")
            continue
        
        # Показываем матрицу
        print_matrix(key_matrix, f"Матрица-ключ A ({rows}×{cols})")
        
        # Проверяем на обратимость (только для квадратных матриц)
        if rows == cols:
            print("\nПроверка возможности расшифрования:")
            invertible, det, gcd_value = check_matrix_invertible(key_matrix, ALPHABET_SIZE)
            
            print(f"Определитель матрицы: {det}")
            print(f"Определитель по модулю {ALPHABET_SIZE}: {det % ALPHABET_SIZE}")
            print(f"НОД(определитель, {ALPHABET_SIZE}): {gcd_value}")
            
            if invertible:
                print("✓ Матрица подходит для шифрования (обратная матрица существует)!")
            else:
                print("ПРЕДУПРЕЖДЕНИЕ: Матрица НЕ подходит для расшифрования!")
                print(f"  Определитель ({det % ALPHABET_SIZE}) не взаимно прост с {ALPHABET_SIZE}")
                print("  Расшифрование будет невозможно!")
                time.sleep(3)
                continue
        else:
            print("\nВнимание: Матрица не квадратная, расшифрование невозможно!")
        
        # Шифруем
        encrypted_indices = matrix_encrypt(text, key_matrix)
        
        print(f"\n{'='*80}")
        print(f"РЕЗУЛЬТАТ ШИФРОВАНИЯ:")
        print(f"{'='*80}")
        print(f"Исходный текст:           {text}")
        print(f"Исходные индексы:         {indices}")
        print(f"Размер матрицы-ключа:     {rows}×{cols}")
        print(f"Зашифрованные индексы:    {encrypted_indices}")
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
        
        print(f"\nЗашифрованные индексы: {encrypted_indices}")
        
        # Ввод размеров матрицы (должна быть квадратной)
        while True:
            try:
                size = int(input("\nВведите размер квадратной матрицы-ключа (минимум 3): "))
                if size >= 3:
                    break
                else:
                    print("Размер должен быть не меньше 3!")
            except ValueError:
                print("Введите целое число!")
        
        rows = cols = size
        
        # Ввод матрицы-ключа
        print(f"\nВведите {rows*cols} чисел для матрицы-ключа {rows}×{cols}")
        print("(числа через пробел или запятую, построчно):")
        key_string = input()
        
        # Парсим матрицу
        key_matrix = parse_key_matrix(key_string, rows, cols)
        
        if key_matrix is None:
            print(f"ОШИБКА: Нужно ввести ровно {rows*cols} чисел!")
            continue
        
        # Показываем матрицу
        print_matrix(key_matrix, f"Матрица-ключ A ({rows}×{cols})")
        
        # Расшифровываем
        decrypted_indices = matrix_decrypt(encrypted_indices, key_matrix)
        
        if decrypted_indices is not None:
            decrypted_text = indices_to_text(decrypted_indices)
            
            print(f"\n{'='*80}")
            print(f"РЕЗУЛЬТАТ РАСШИФРОВАНИЯ:")
            print(f"{'='*80}")
            print(f"Зашифрованные индексы:    {encrypted_indices}")
            print(f"Размер матрицы-ключа:     {rows}×{cols}")
            print(f"Расшифрованные индексы:   {decrypted_indices}")
            print(f"Расшифрованный текст:     {decrypted_text}")
            print(f"{'='*80}")
    
    else:
        print("\nНеверный выбор. Попробуйте снова.")
