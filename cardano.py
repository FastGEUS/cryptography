# -*- coding: utf-8 -*-

import random
from typing import List, Tuple, Optional, Dict, Any

ALPHABET = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

PUNCT_TO_WORD = {
    '.': 'ТЧК',
    ',': 'ЗПТ',
    '?': 'ВПР',
    '!': 'ВСК',
    ':': 'ДВТ',
    ';': 'ТСЗ',
    '-': 'ТИР',
    '—': 'ТИР',
    '«': 'КВЫ',
    '»': 'КВЗ',
    '"': 'КВЫ',
    '(': 'ЛСК',
    ')': 'ПСК'
}

WORD_TO_PUNCT = {v: k for k, v in PUNCT_TO_WORD.items()}


def convert_punctuation(text: str, to_word: bool = True) -> str:
    if to_word:
        result = []
        for ch in text:
            result.append(PUNCT_TO_WORD.get(ch, ch))
        return ''.join(result)

    result = text
    for word, punct in WORD_TO_PUNCT.items():
        result = result.replace(word, punct)
    return result


def normalize_text(text: str, convert_punct: bool = False, keep_only_letters: bool = True) -> str:
    text = text.upper().replace('Ё', 'Е')

    if convert_punct:
        text = convert_punctuation(text, to_word=True)

    if keep_only_letters:
        text = ''.join(c for c in text if c in ALPHABET)

    return text


def get_symmetric_coords(r: int, c: int, rows: int, cols: int) -> List[Tuple[int, int]]:
    """
    Возвращает 4 симметричные координаты для ячейки.
    В данной реализации используется симметричная четверка.
    """
    return [
        (r, c),
        (r, cols - 1 - c),
        (rows - 1 - r, c),
        (rows - 1 - r, cols - 1 - c)
    ]


def grid_to_string(grid: List[List[str]]) -> str:
    return ''.join(''.join(row) for row in grid)


def string_to_grid(text: str, rows: int, cols: int) -> List[List[str]]:
    return [list(text[i:i + cols]) for i in range(0, len(text), cols)]


def printable_grid(grid: List[List[str]]) -> str:
    rows = len(grid)
    cols = len(grid[0])
    lines = []
    lines.append("┌" + "───┬" * (cols - 1) + "───┐")
    for i, row in enumerate(grid):
        line = "│ " + " │ ".join(cell if cell else ' ' for cell in row) + " │"
        lines.append(line)
        if i < rows - 1:
            lines.append("├" + "───┼" * (cols - 1) + "───┤")
    lines.append("└" + "───┴" * (cols - 1) + "───┘")
    return '\n'.join(lines)


def generate_auto_holes(rows: int, cols: int, rng: Optional[random.Random] = None):
    if rows % 2 != 0 or cols % 2 != 0:
        raise ValueError("Размеры решетки должны быть четными.")

    rng = rng or random.Random()

    holes = []
    holes_grid = [['.' for _ in range(cols)] for _ in range(rows)]

    for r in range(rows // 2):
        for c in range(cols // 2):
            coords = get_symmetric_coords(r, c, rows, cols)
            chosen = rng.choice(coords)
            holes.append(chosen)
            holes_grid[chosen[0]][chosen[1]] = 'O'

    validate_holes(rows, cols, holes)
    return holes, holes_grid


def validate_holes(rows: int, cols: int, holes: List[Tuple[int, int]]) -> None:
    if rows % 2 != 0 or cols % 2 != 0:
        raise ValueError("Размеры решетки должны быть четными.")

    expected = (rows * cols) // 4
    if len(holes) != expected:
        raise ValueError(f"Количество отверстий должно быть равно {expected}.")

    if len(set(holes)) != len(holes):
        raise ValueError("Отверстия не должны повторяться.")

    covered = set()

    for r, c in holes:
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"Координата {(r, c)} выходит за границы решетки.")

        sym_group = get_symmetric_coords(r, c, rows, cols)
        for pos in sym_group:
            if pos in covered:
                raise ValueError("Некорректный ключ: некоторые клетки перекрываются в разных состояниях.")
            covered.add(pos)

    if len(covered) != rows * cols:
        raise ValueError("Некорректный ключ: решетка не покрывает все клетки.")


def get_all_states(holes: List[Tuple[int, int]], rows: int, cols: int) -> List[List[Tuple[int, int]]]:
    validate_holes(rows, cols, holes)

    states = []
    for i in range(4):
        state_holes = []
        for r, c in holes:
            sym_points = get_symmetric_coords(r, c, rows, cols)
            state_holes.append(sym_points[i])
        state_holes.sort()
        states.append(state_holes)

    return states


def build_mask_grid(rows: int, cols: int, holes: List[Tuple[int, int]]) -> List[List[str]]:
    grid = [['.' for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 'O'
    return grid


def encrypt_cardano(
    text: str,
    rows: int,
    cols: int,
    holes: List[Tuple[int, int]],
    convert_punct: bool = False,
    keep_only_letters: bool = True,
    filler_mode: str = "random",
    filler_char: str = "Х",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    validate_holes(rows, cols, holes)

    norm_text = normalize_text(text, convert_punct=convert_punct, keep_only_letters=keep_only_letters)
    capacity = rows * cols

    rng = random.Random(seed)
    states = get_all_states(holes, rows, cols)
    grid = [['' for _ in range(cols)] for _ in range(rows)]

    text_idx = 0
    for current_holes in states:
        for r, c in current_holes:
            if text_idx < len(norm_text):
                grid[r][c] = norm_text[text_idx]
                text_idx += 1
            else:
                if filler_mode == "random":
                    grid[r][c] = rng.choice(ALPHABET)
                elif filler_mode == "fixed":
                    fill = filler_char.upper().replace('Ё', 'Е')
                    if fill not in ALPHABET:
                        raise ValueError("Символ заполнения должен быть русской буквой.")
                    grid[r][c] = fill
                else:
                    raise ValueError("filler_mode должен быть 'random' или 'fixed'.")

    cipher_text = grid_to_string(grid)

    return {
        "success": True,
        "input_text": text,
        "normalized_text": norm_text,
        "rows": rows,
        "cols": cols,
        "holes": holes,
        "states": states,
        "mask_grid": build_mask_grid(rows, cols, holes),
        "encrypted_grid": grid,
        "cipher_text": cipher_text,
        "capacity": capacity,
        "original_length": len(norm_text)
    }


def decrypt_cardano(
    cipher_text: str,
    rows: int,
    cols: int,
    holes: List[Tuple[int, int]],
    original_length: Optional[int] = None
) -> Dict[str, Any]:
    validate_holes(rows, cols, holes)

    if len(cipher_text) != rows * cols:
        raise ValueError("Длина шифртекста должна быть равна rows * cols.")

    grid = string_to_grid(cipher_text, rows, cols)
    states = get_all_states(holes, rows, cols)

    result = []
    for current_holes in states:
        for r, c in current_holes:
            result.append(grid[r][c])

    raw_text = ''.join(result)
    clean_text = raw_text[:original_length] if original_length is not None else raw_text

    return {
        "success": True,
        "cipher_text": cipher_text,
        "rows": rows,
        "cols": cols,
        "holes": holes,
        "states": states,
        "grid": grid,
        "decrypted_raw": raw_text,
        "decrypted_clean": clean_text
    }


def run_cardano(
    mode: str,
    text: str = "",
    rows: int = 4,
    cols: int = 4,
    holes: Optional[List[Tuple[int, int]]] = None,
    auto_generate: bool = True,
    convert_punct: bool = False,
    keep_only_letters: bool = True,
    filler_mode: str = "random",
    filler_char: str = "Х",
    seed: Optional[int] = None,
    original_length: Optional[int] = None
) -> Dict[str, Any]:
    if rows <= 0 or cols <= 0:
        raise ValueError("Размеры решетки должны быть положительными.")

    rng = random.Random(seed)

    if auto_generate:
        holes, _ = generate_auto_holes(rows, cols, rng=rng)
    else:
        if holes is None:
            raise ValueError("Для ручного режима необходимо передать список отверстий.")
        validate_holes(rows, cols, holes)

    if mode == "encrypt":
        return encrypt_cardano(
            text=text,
            rows=rows,
            cols=cols,
            holes=holes,
            convert_punct=convert_punct,
            keep_only_letters=keep_only_letters,
            filler_mode=filler_mode,
            filler_char=filler_char,
            seed=seed
        )

    elif mode == "decrypt":
        return decrypt_cardano(
            cipher_text=text,
            rows=rows,
            cols=cols,
            holes=holes,
            original_length=original_length
        )

    else:
        raise ValueError("mode должен быть 'encrypt' или 'decrypt'.")


def main():
    print("=" * 72)
    print("РЕШЕТКА КАРДАНО")
    print("=" * 72)

    try:
        rows = int(input("Введите количество строк (четное): ").strip())
        cols = int(input("Введите количество столбцов (четное): ").strip())

        key_mode = input("Автогенерация отверстий? (y/n): ").strip().lower()
        auto_generate = key_mode in ('y', 'yes', 'д', 'да')

        seed_input = input("Введите seed для генератора (или Enter): ").strip()
        seed = int(seed_input) if seed_input else None

        holes = None
        if not auto_generate:
            print("Введите координаты отверстий в формате: r,c;r,c;...")
            raw = input("Отверстия: ").strip()
            holes = []
            if raw:
                parts = raw.split(';')
                for part in parts:
                    r, c = part.split(',')
                    holes.append((int(r.strip()), int(c.strip())))

        message = input("Введите текст для шифрования: ")
        punct_mode = input("Преобразовать знаки препинания в словесные коды? (y/n): ").strip().lower()
        convert_punct = punct_mode in ('y', 'yes', 'д', 'да')

        enc = run_cardano(
            mode="encrypt",
            text=message,
            rows=rows,
            cols=cols,
            holes=holes,
            auto_generate=auto_generate,
            convert_punct=convert_punct,
            keep_only_letters=True,
            filler_mode="random",
            seed=seed
        )

        print("\nМАСКА:")
        print(printable_grid(enc["mask_grid"]))

        print("\nИТОГОВАЯ РЕШЕТКА:")
        print(printable_grid(enc["encrypted_grid"]))

        print(f"\nНормализованный текст: {enc['normalized_text']}")
        print(f"Шифртекст: {enc['cipher_text']}")
        print(f"Ключ-отверстия: {enc['holes']}")

        dec = run_cardano(
            mode="decrypt",
            text=enc["cipher_text"],
            rows=rows,
            cols=cols,
            holes=enc["holes"],
            auto_generate=False,
            original_length=enc["original_length"]
        )

        print(f"\nРасшифровка полная: {dec['decrypted_raw']}")
        print(f"Расшифровка без добивки: {dec['decrypted_clean']}")

    except Exception as e:
        print(f"\nОшибка: {e}")


if __name__ == "__main__":
    main()