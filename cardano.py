import random

ALPHABET = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

def normalize_text(text):
    text = text.upper().replace('Ё', 'Е')
    return ''.join(c for c in text if c in ALPHABET)

def get_symmetric_coords(r, c, rows, cols):
    """Возвращает 4 симметричные координаты для ячейки (r, c)."""
    return [
        (r, c),                          # 1-е положение
        (r, cols - 1 - c),               # 2-е положение (отражение по гориз.)
        (rows - 1 - r, c),               # 3-е положение (отражение по вертик.)
        (rows - 1 - r, cols - 1 - c)     # 4-е положение (180 градусов)
    ]

def print_grid(grid, title):
    """Красивый вывод таблицы в консоль."""
    print(f"\n--- {title} ---")
    rows = len(grid)
    cols = len(grid[0])
    print("┌" + "───┬" * (cols - 1) + "───┐")
    for i, row in enumerate(grid):
        row_str = "│ " + " │ ".join([str(cell) if cell != '' else ' ' for cell in row]) + " │"
        print(row_str)
        if i < rows - 1:
            print("├" + "───┼" * (cols - 1) + "───┤")
    print("└" + "───┴" * (cols - 1) + "───┘")

def generate_auto_holes(rows, cols):
    """Автогенерация отверстий."""
    if rows % 2 != 0 or cols % 2 != 0:
        raise ValueError("Размеры должны быть четными!")
    
    holes = []
    holes_grid = [['.' for _ in range(cols)] for _ in range(rows)]
    
    for r in range(rows // 2):
        for c in range(cols // 2):
            coords = get_symmetric_coords(r, c, rows, cols)
            chosen = random.choice(coords)
            holes.append(chosen)
            holes_grid[chosen[0]][chosen[1]] = 'O'
            
    return holes, holes_grid

def get_all_states(holes, rows, cols):
    """Вычисляет 4 набора координат (состояния решетки)."""
    states = []
    for i in range(4):
        state_holes = []
        for r, c in holes:
            sym_points = get_symmetric_coords(r, c, rows, cols)
            state_holes.append(sym_points[i])
        state_holes.sort() # Важно для порядка чтения/записи
        states.append(state_holes)
    return states

def encrypt_cardano(text, rows, cols, holes):
    """Шифрование."""
    text = normalize_text(text)
    grid = [['' for _ in range(cols)] for _ in range(rows)]
    states = get_all_states(holes, rows, cols)

    text_idx = 0
    for current_holes in states:
        for r, c in current_holes:
            if text_idx < len(text):
                grid[r][c] = text[text_idx]
                text_idx += 1
            else:
                grid[r][c] = random.choice(ALPHABET)

    cipher_text = ''.join([''.join(row) for row in grid])
    return cipher_text, grid

def decrypt_cardano(cipher_text, rows, cols, holes):
    """Расшифрование."""
    # Восстанавливаем таблицу из зашифрованной строки
    grid = []
    for i in range(0, len(cipher_text), cols):
        grid.append(list(cipher_text[i:i+cols]))
    
    states = get_all_states(holes, rows, cols)
    result = ""
    
    # Последовательно вынимаем буквы через отверстия в 4-х состояниях
    for current_holes in states:
        for r, c in current_holes:
            result += grid[r][c]
            
    return result

# --- Основной блок программы ---
if __name__ == "__main__":
    print("=== ПОЛНЫЙ ЦИКЛ: РЕШЕТКА КАРДАНО (СИММЕТРИЯ) ===")
    try:
        R = int(input("Введите количество строк (четное): "))
        C = int(input("Введите количество столбцов (четное): "))
        
        # 1. Генерация ключа (отверстий)
        holes, holes_display = generate_auto_holes(R, C)
        print_grid(holes_display, "МАСКА (ТРАФАРЕТ) С ОТВЕРСТИЯМИ 'O'")
        
        # 2. Ввод текста
        message = input("Введите текст для шифрования: ")
        
        # 3. Шифрование
        encrypted_str, final_grid = encrypt_cardano(message, R, C, holes)
        print_grid(final_grid, "ИТОГОВАЯ РЕШЕТКА (ЗАШИФРОВАНО)")
        print(f"\nЗашифрованная строка: {encrypted_str}")
        
        # 4. Расшифрование
        decrypted_msg = decrypt_cardano(encrypted_str, R, C, holes)
        print(f"\nРезультат расшифровки: {decrypted_msg}")
        print(f"\nОчищенный результат (без гаммы): {decrypted_msg[:len(normalize_text(message))]}")
        
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")