import sys
import time

def check_keyword_duplicates(keyword):
    """
    Проверяет ключевое слово на наличие повторяющихся символов
    после выполнения всех замен (Ё->Е, Й->И, Ь->Ъ).
    """
    # Нормализуем ключ так же, как это делает основная программа
    clean_key = keyword.upper().replace("Ё", "Е").replace("Й", "И").replace("Ь", "Ъ")
    # Убираем все символы, не входящие в рабочий алфавит (пробелы и т.д.)
    alphabet = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЫЬЭЮЯ"
    clean_key = "".join([c for c in clean_key if c in alphabet])
    
    seen = set()
    duplicates = []
    for char in clean_key:
        if char in seen:
            if char not in duplicates:
                duplicates.append(char)
        else:
            seen.add(char)
    
    return duplicates

def create_playfair_matrix(keyword):
    """Создает матрицу 5x6 на основе ключевого слова."""
    alphabet = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЫЬЭЮЯ"
    keyword = keyword.upper().replace("Ё", "Е").replace("Й", "И").replace("Ь", "Ъ")
    
    matrix_string = ""
    for char in keyword:
        if char in alphabet and char not in matrix_string:
            matrix_string += char
            
    for char in alphabet:
        if char not in matrix_string:
            matrix_string += char
            
    return [list(matrix_string[i:i+6]) for i in range(0, 30, 6)]

def prepare_text(text):
    """Подготавливает текст: удаляет мусор, делает замены, разбивает на биграммы."""
    alphabet = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЫЬЭЮЯ"
    text = text.upper().replace("Ё", "Е").replace("Й", "И").replace("Ь", "Ъ")
    text = ''.join([c for c in text if c in alphabet])
    
    prepared = ""
    i = 0
    while i < len(text):
        char1 = text[i]
        if i + 1 < len(text):
            char2 = text[i+1]
            if char1 == char2:
                prepared += char1 + 'Х'
                i += 1
            else:
                prepared += char1 + char2
                i += 2
        else:
            prepared += char1 + 'Х'
            i += 1
            
    return prepared

def get_coordinates(matrix, char):
    """Находит строку и столбец буквы в матрице."""
    for row in range(5):
        for col in range(6):
            if matrix[row][col] == char:
                return row, col
    return None, None

def playfair_encrypt(text, keyword):
    """Основная функция шифрования Плейфера."""
    matrix = create_playfair_matrix(keyword)
    prepared_text = prepare_text(text)
    encrypted_text = ""
    
    print("Сгенерированная матрица (5x6):")
    print("\n" + "=" * 30)
    for row in matrix:
        print(" ".join(row))
    print("=" * 30)
    print(f"Текст, разбитый на биграммы: {prepared_text}")
    
    for i in range(0, len(prepared_text), 2):
        r1, c1 = get_coordinates(matrix, prepared_text[i])
        r2, c2 = get_coordinates(matrix, prepared_text[i+1])
        
        if r1 == r2:
            encrypted_text += matrix[r1][(c1 + 1) % 6]
            encrypted_text += matrix[r2][(c2 + 1) % 6]
        elif c1 == c2:
            encrypted_text += matrix[(r1 + 1) % 5][c1]
            encrypted_text += matrix[(r2 + 1) % 5][c2]
        else:
            encrypted_text += matrix[r1][c2]
            encrypted_text += matrix[r2][c1]
            
    return encrypted_text

def playfair_decrypt(ciphertext, keyword):
    """Функция для расшифрования текста Плейфера."""
    matrix = create_playfair_matrix(keyword)
    decrypted_text = ""
    
    # Текст уже должен состоять из биграмм
    for i in range(0, len(ciphertext), 2):
        r1, c1 = get_coordinates(matrix, ciphertext[i])
        r2, c2 = get_coordinates(matrix, ciphertext[i+1])
        
        # Правило 1: Буквы в одной строке — сдвиг ВЛЕВО (-1)
        if r1 == r2:
            decrypted_text += matrix[r1][(c1 - 1) % 6]
            decrypted_text += matrix[r2][(c2 - 1) % 6]
        # Правило 2: Буквы в одном столбце — сдвиг ВВЕРХ (-1)
        elif c1 == c2:
            decrypted_text += matrix[(r1 - 1) % 5][c1]
            decrypted_text += matrix[(r2 - 1) % 5][c2]
        # Правило 3: Прямоугольник — остается как при шифровании
        else:
            decrypted_text += matrix[r1][c2]
            decrypted_text += matrix[r2][c1]
            
    return decrypted_text

if __name__ == "__main__":
    while True:
        print("\n" + "="*50)
        print("ШИФР ПЛЕЙФЕРА (5x6, РУССКИЙ ЯЗЫК)")
        print("1 - Зашифровать")
        print("2 - Расшифровать")
        print("0 - Выход")
        
        choice = input("\nВаш выбор: ")
        
        if choice in ['1', '2']:
            key = input("Введите ключевое слово: ")
            
            # ПРОВЕРКА КЛЮЧА
            duplicates = check_keyword_duplicates(key)
            if duplicates:
                print(f"\nВНИМАНИЕ: Ключевое слово содержит повторяющиеся буквы: {', '.join(duplicates)}")
                print("Операция отменена. Введите другой ключ.")
                time.sleep(4)
                continue
            
            text = input("Введите текст: ")
            
            if choice == '1':
                result = playfair_encrypt(text, key)
                print(f"\n[Зашифровано]: {result}")
            else:
                clean_text = text.upper().replace(" ", "")
                result = playfair_decrypt(clean_text, key)
                print(f"\n[Расшифровано]: {result}")
                
        elif choice == '0':
            print("Программа завершена.")
            break