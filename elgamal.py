import math
import re


# ═══════════════════════════════════════════════════════════════
#  АЛФАВИТ
# ═══════════════════════════════════════════════════════════════

ALPHABET    = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
CHAR_TO_IDX = {ch: i + 1 for i, ch in enumerate(ALPHABET)}
IDX_TO_CHAR = {i + 1: ch for i, ch in enumerate(ALPHABET)}


def letter_to_code(ch: str) -> int:
    ch = ch.lower()
    if ch == 'ё':
        ch = 'е'
    return CHAR_TO_IDX.get(ch, 0)


def code_to_letter(code: int) -> str:
    if code == 0:
        return ' '
    return IDX_TO_CHAR.get(code, '?')


# ═══════════════════════════════════════════════════════════════
#  МАТЕМАТИКА
# ═══════════════════════════════════════════════════════════════

def is_prime(n: int) -> bool:
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def extended_gcd(a: int, b: int):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = extended_gcd(b % a, a)
    return g, y1 - (b // a) * x1, x1


def mod_inverse(a: int, m: int) -> int:
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        raise ValueError(f"НОД({a}, {m}) ≠ 1 — обратный элемент не существует")
    return (x % m + m) % m


# ═══════════════════════════════════════════════════════════════
#  ПОДСКАЗКА: допустимые ki
# ═══════════════════════════════════════════════════════════════

def suggest_ki(p: int, count: int = 15) -> list:
    phi = p - 1
    result = []
    for ki in range(2, p - 1):
        if math.gcd(ki, phi) == 1:
            result.append(ki)
        if len(result) >= count:
            break
    return result
def is_primitive_root(g: int, p: int) -> bool:
    """Проверяет, является ли g примитивным корнем по модулю p (p — простое).
    По методичке: g — примитивный корень, т.е. порядок g равен φ(p) = p-1.
    Метод: g^((p-1)/q) ≢ 1 (mod p) для всех простых делителей q числа (p-1).
    """
    phi = p - 1
    if pow(g, phi, p) != 1:
        return False
    # Факторизация phi
    factors = set()
    n = phi
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.add(d)
            n //= d
        d += 1
    if n > 1:
        factors.add(n)
    for q in factors:
        if pow(g, phi // q, p) == 1:
            return False
    return True

def suggest_primitive_roots(p: int, count: int = 10) -> list:
    """Находит первые count примитивных корней по модулю p."""
    result = []
    for g in range(2, p):
        if is_primitive_root(g, p):
            result.append(g)
        if len(result) >= count:
            break
    return result




# ═══════════════════════════════════════════════════════════════
#  ВВОД ПАРАМЕТРОВ
# ═══════════════════════════════════════════════════════════════

def input_prime(prompt: str) -> int:
    while True:
        try:
            n = int(input(prompt).strip())
            if not is_prime(n):
                print(f"  ✗ {n} не является простым числом.")
                continue
            return n
        except ValueError:
            print("  ✗ Введите целое число.")


def input_int_in_range(prompt: str, lo: int, hi: int) -> int:
    while True:
        try:
            n = int(input(prompt).strip())
            if not (lo < n < hi):
                print(f"  ✗ Значение должно быть в диапазоне ({lo}, {hi}).")
                continue
            return n
        except ValueError:
            print("  ✗ Введите целое число.")


def input_keys() -> tuple:
    print("\n─── Параметры ключа Эль-Гамаля ──────────────────────")
    p = input_prime("  Введите простое число p (p > 32): ")
    if p <= 32:
        print(f"  ⚠ p={p} ≤ 32 — некоторые буквы алфавита (Mi > p) зашифруются некорректно.")
    g = input_int_in_range(f"  Введите g (1 < g < {p}): ", 1, p)
    x = input_int_in_range(f"  Введите секретный ключ x (1 < x < {p}): ", 1, p)
    y = pow(g, x, p)
    print(f"\n  y = g^x mod p = {g}^{x} mod {p} = {y}")
    print(f"  Открытый ключ:  (p={p}, g={g}, y={y})")
    print(f"  Секретный ключ: x={x}")
    return p, g, x, y


def select_ki(p: int, need: int = 3) -> list:
    phi = p - 1
    candidates = suggest_ki(p, count=15)

    print(f"\n─── Выбор рандомизаторов ki ──────────────────────────")
    print(f"  Условие: 1 < ki < {p},  НОД(ki, φ(p)) = НОД(ki, {phi}) = 1")
    print(f"\n  Допустимые значения ki:")
    row = "  "
    for i, k in enumerate(candidates):
        row += f"{k:>4}"
        if (i + 1) % 10 == 0:
            print(row); row = "  "
    if row.strip():
        print(row)

    print(f"\n  Введите {need} значения ki через пробел (из списка выше):")
    while True:
        try:
            raw = input("  ki: ").strip().split()
            if len(raw) != need:
                print(f"  ✗ Нужно ровно {need} значения.")
                continue
            chosen = [int(v) for v in raw]
            errors = []
            for k in chosen:
                if not (1 < k < p):
                    errors.append(f"{k} не в диапазоне (1, {p})")
                elif math.gcd(k, phi) != 1:
                    errors.append(f"НОД({k}, {phi}) = {math.gcd(k, phi)} ≠ 1")
            if errors:
                for e in errors: print(f"  ✗ {e}")
                continue
            print(f"  ✓ Выбраны ki: {chosen}")
            return chosen
        except ValueError:
            print("  ✗ Введите целые числа через пробел.")


# ═══════════════════════════════════════════════════════════════
#  ШИФРОВАНИЕ / РАСШИФРОВАНИЕ
# ═══════════════════════════════════════════════════════════════

def encrypt_text(text: str, p: int, g: int, y: int, ki_list: list) -> tuple:
    """ki_list — 3 рандомизатора, для i-го символа: ki = ki_list[i % 3]."""
    enc_data, ciphertext = [], []
    for idx, char in enumerate(text):
        M  = letter_to_code(char)
        ki = ki_list[idx % len(ki_list)]
        a  = pow(g, ki, p)
        b  = (pow(y, ki, p) * M) % p
        enc_data.append({'idx': idx, 'char': char, 'M': M, 'ki': ki, 'a': a, 'b': b})
        ciphertext.append((a, b))
    return enc_data, ciphertext


def decrypt_ciphertext(ciphertext: list, p: int, x: int) -> tuple:
    """Mi = bi × (ai^x)^(-1) mod p."""
    dec_text, dec_data = "", []
    for idx, (a, b) in enumerate(ciphertext):
        a_pow_x = pow(a, x, p)
        try:
            a_inv = mod_inverse(a_pow_x, p)
            M     = (b * a_inv) % p
            err   = None
        except ValueError as e:
            a_inv, M, err = None, 0, str(e)
        ch = code_to_letter(M)
        dec_text += ch
        dec_data.append({'idx': idx, 'a': a, 'b': b, 'a_pow_x': a_pow_x,
                         'a_inv': a_inv, 'M': M, 'char': ch, 'error': err})
    return dec_text, dec_data


# ═══════════════════════════════════════════════════════════════
#  ФОРМАТИРОВАННЫЙ ВЫВОД
# ═══════════════════════════════════════════════════════════════

def print_header(title: str):
    print("\n" + "═" * 70)
    print(title.center(70))
    print("═" * 70)


def print_key_info(p, g, x, y):
    print("\n┌──────────────────────────────────────────────────┐")
    print("│          Параметры Эль-Гамаля                    │")
    print("├──────────────────────────────────────────────────┤")
    print(f"│  p = {p:<10}  (простое, p > Mi)               │")
    print(f"│  g = {g:<10}  (1 < g < p)                     │")
    print(f"│  x = {x:<10}  (секретный ключ)                │")
    print(f"│  y = g^x mod p = {y:<10}  (открытый ключ)    │")
    print("├──────────────────────────────────────────────────┤")
    print(f"│  Открытый ключ:  (p={p}, g={g}, y={y})")
    print(f"│  Секретный ключ: x={x}")
    print("└──────────────────────────────────────────────────┘")


def print_encryption_table(enc_data: list, max_rows: int = 30):
    print(f"\n  {'№':>4}  {'симв':>5}  {'Mi':>4}  {'ki':>4}  "
          f"{'ai=g^ki mod p':>14}  {'bi=y^ki·Mi mod p':>18}  {'пара (ai,bi)':>14}")
    print("  " + "─" * 72)
    for d in enc_data[:max_rows]:
        ch = '[пр]' if d['char'] == ' ' else f"'{d['char']}'"
        print(f"  {d['idx']:>4}  {ch:>5}  {d['M']:>4}  {d['ki']:>4}  "
              f"{d['a']:>14}  {d['b']:>18}  ({d['a']},{d['b']})")
    if len(enc_data) > max_rows:
        print(f"  ... (показаны первые {max_rows} из {len(enc_data)} символов)")


def print_decryption_table(dec_data: list, max_rows: int = 30):
    print(f"\n  {'№':>4}  {'(ai,bi)':>12}  {'ai^x mod p':>11}  "
          f"{'(ai^x)^-1':>11}  {'Mi':>4}  {'буква':>6}")
    print("  " + "─" * 60)
    for d in dec_data[:max_rows]:
        ch = '[пр]' if d['char'] == ' ' else f"'{d['char']}'"
        a_inv_str = str(d['a_inv']) if d['a_inv'] is not None else 'нет'
        print(f"  {d['idx']:>4}  ({d['a']},{d['b']:<3})  {d['a_pow_x']:>11}  "
              f"{a_inv_str:>11}  {d['M']:>4}  {ch:>6}")
    if len(dec_data) > max_rows:
        print(f"  ... (показаны первые {max_rows} из {len(dec_data)})")


def format_ciphertext(ciphertext: list) -> str:
    return '  ' + ' '.join(f"({a},{b})" for a, b in ciphertext)


def parse_ciphertext(raw: str) -> list:
    pairs = re.findall(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', raw)
    if not pairs:
        raise ValueError("Не найдено ни одной пары (a,b). Формат: (3,15) (7,22) ...")
    return [(int(a), int(b)) for a, b in pairs]


# ═══════════════════════════════════════════════════════════════
#  РЕЖИМ ШИФРОВАНИЯ
# ═══════════════════════════════════════════════════════════════

def encrypt_mode():
    print_header("РЕЖИМ ШИФРОВАНИЯ  (Эль-Гамаль)")

    p, g, x, y = input_keys()
    print_key_info(p, g, x, y)
    ki_list = select_ki(p, need=3)

    text = input("\n  Введите текст (только русские буквы):\n  > ").strip().lower()
    if not text:
        print("  ✗ Текст не введён."); return

    enc_data, ciphertext = encrypt_text(text, p, g, y, ki_list)

    print_header("ТАБЛИЦА ШИФРОВАНИЯ")
    print(f"  Формулы:  ai = g^ki mod p      bi = y^ki × Mi mod p")
    print(f"  ki циклически: позиция i → ki_list[i mod 3] = {ki_list}")
    print_encryption_table(enc_data)

    print_header("ШИФРТЕКСТ")
    print(f"\n{format_ciphertext(ciphertext)}\n")
    print(f"  Длина открытого текста: {len(enc_data)} символов")
    print(f"  Длина шифртекста:       {len(ciphertext) * 2} чисел ({len(ciphertext)} пар)")

    dec_text, _ = decrypt_ciphertext(ciphertext, p, x)
    orig = ''.join(d['char'] for d in enc_data)
    print(f"\n  Проверка расшифровки: {'✓ совпадает' if dec_text == orig else '✗ НЕ совпадает'}")
    print(f"\n  Сохраните для расшифровки:  p={p},  x={x}")


# ═══════════════════════════════════════════════════════════════
#  РЕЖИМ РАСШИФРОВАНИЯ
# ═══════════════════════════════════════════════════════════════

def decrypt_mode():
    print_header("РЕЖИМ РАСШИФРОВАНИЯ  (Эль-Гамаль)")

    p = input_prime("\n  Введите простое число p: ")
    x = input_int_in_range(f"  Введите секретный ключ x (1 < x < {p}): ", 1, p)

    print("\n  Введите шифртекст в формате пар: (a1,b1) (a2,b2) ...")
    print("  Пустая строка — конец ввода:")
    lines = []
    while True:
        line = input()
        if line.strip() == "": break
        lines.append(line)

    try:
        ciphertext = parse_ciphertext(" ".join(lines))
    except ValueError as err:
        print(f"  ✗ Ошибка: {err}"); return

    dec_text, dec_data = decrypt_ciphertext(ciphertext, p, x)

    print_header("ТАБЛИЦА РАСШИФРОВАНИЯ")
    print(f"  Формула:  Mi = bi × (ai^x)^(-1) mod p")
    print_decryption_table(dec_data)

    print_header("РАСШИФРОВАННЫЙ ТЕКСТ")
    print(f"\n  {dec_text}\n")


# ═══════════════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════

def main():
    print("═" * 70)
    print("      КРИПТОСИСТЕМА ЭЛЬ-ГАМАЛЯ  (Блок H, алгоритм 22)".center(70))
    print("═" * 70)
    print(f"  Алфавит: {''.join(ALPHABET[:16])}")
    print(f"           {''.join(ALPHABET[16:])}")
    print("  Кодировка: а=1, б=2, ..., я=32, пробел/прочее=0")
    print("  Шифрование:    ai = g^ki mod p;   bi = y^ki × Mi mod p")
    print("  Расшифрование: Mi = bi × (ai^x)^(-1) mod p")

    while True:
        print("\n" + "─" * 70)
        print("  1 — Зашифровать текст")
        print("  2 — Расшифровать шифртекст")
        print("  0 — Выход")
        choice = input("\n  Выбор: ").strip()
        if choice == "1":
            encrypt_mode()
        elif choice == "2":
            decrypt_mode()
        elif choice == "0":
            print("  Выход."); break
        else:
            print("  ✗ Неверный пункт меню.")


if __name__ == "__main__":
    main()
