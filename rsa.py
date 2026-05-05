import math

# ── Алфавит ──────────────────────────────────────────────────────────────────
ALPHABET = list('АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')  # 32 буквы
CHAR_TO_IDX = {ch: i + 1 for i, ch in enumerate(ALPHABET)}  # А=1 … Я=32
IDX_TO_CHAR = {i + 1: ch for i, ch in enumerate(ALPHABET)}

# ── Математика ────────────────────────────────────────────────────────────────

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def mod_inverse(e: int, phi: int) -> int:
    """Расширенный алгоритм Евклида: e*d ≡ 1 (mod phi)."""
    old_r, r = e, phi
    old_s, s = 1, 0
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    if old_r != 1:
        raise ValueError(f"НОД({e}, {phi}) ≠ 1 — обратного элемента не существует.")
    return old_s % phi


def generate_keys(p: int, q: int, e: int) -> tuple:
    """Возвращает (n, e, d, phi). Проверяет, что d != e."""
    n = p * q
    phi = (p - 1) * (q - 1)

    if not (1 < e < phi):
        raise ValueError(f"e={e} должно быть в диапазоне (1, {phi}).")
    if math.gcd(e, phi) != 1:
        raise ValueError(f"НОД(e={e}, φ(n)={phi}) ≠ 1. Выберите другое e.")

    d = mod_inverse(e, phi)

    if d == e:
        raise ValueError(
            f"Получилось d = e = {e}. Для RSA нужно выбрать другое значение e."
        )

    return n, e, d, phi


# ── Подсказка: допустимые значения e ─────────────────────────────────────────

def suggest_e(phi: int, count: int = 10) -> list:
    """
    Возвращает список допустимых e: взаимно простых с phi.
    Дополнительно исключает значения, для которых d = e.
    """
    candidates = []

    for cand in [65537, 257, 17, 13, 11, 7, 5, 3]:
        if 1 < cand < phi and math.gcd(cand, phi) == 1:
            try:
                if mod_inverse(cand, phi) != cand:
                    candidates.append(cand)
            except ValueError:
                pass

    val = 3
    while len(candidates) < count and val < phi:
        if val not in candidates and math.gcd(val, phi) == 1:
            try:
                if mod_inverse(val, phi) != val:
                    candidates.append(val)
            except ValueError:
                pass
        val += 2

    return sorted(candidates[:count])


# ── Шифрование / расшифрование ────────────────────────────────────────────────

def text_to_indices(text: str) -> list:
    result = []
    for ch in text.upper():
        if ch == 'Ё':
            ch = 'Е'
        if ch in CHAR_TO_IDX:
            result.append(CHAR_TO_IDX[ch])
    return result


def encrypt_rsa(indices: list, e: int, n: int) -> list:
    """c = m^e mod n для каждого индекса m."""
    return [pow(m, e, n) for m in indices]


def decrypt_rsa(cipher: list, d: int, n: int) -> list:
    """m = c^d mod n для каждого зашифрованного числа c."""
    return [pow(c, d, n) for c in cipher]


# ── Ввод параметров ───────────────────────────────────────────────────────────

def input_rsa_params() -> tuple:
    """Запрашивает p, q, e у пользователя. Возвращает (p, q, e)."""
    print("\n─── Параметры ключа RSA ──────────────────────────────")

    while True:
        try:
            p = int(input(" Введите простое число p: "))
            if not is_prime(p):
                print(f" ✗ {p} не является простым. Попробуйте снова.")
                continue
            break
        except ValueError:
            print(" ✗ Введите целое число.")

    while True:
        try:
            q = int(input(" Введите простое число q (q ≠ p): "))
            if not is_prime(q):
                print(f" ✗ {q} не является простым. Попробуйте снова.")
                continue
            if q == p:
                print(" ✗ q должно отличаться от p.")
                continue
            break
        except ValueError:
            print(" ✗ Введите целое число.")

    phi = (p - 1) * (q - 1)
    print(f"\n n = p × q = {p} × {q} = {p * q}")
    print(f" φ(n) = (p-1)(q-1) = {p - 1} × {q - 1} = {phi}")

    suggestions = suggest_e(phi)
    if not suggestions:
        raise ValueError("Не удалось подобрать допустимые значения e для этих p и q.")

    print(f"\n Допустимые значения e (взаимно простые с φ(n)={phi} и такие, что d ≠ e):")
    print(f" {suggestions}")
    print(f" (Enter — автоматически выбрать e={suggestions[0]})")

    while True:
        try:
            raw = input(" Введите e: ").strip()
            if raw == "":
                e = suggestions[0]
                print(f" ✓ Выбрано e = {e}")
            else:
                e = int(raw)

            if not (1 < e < phi):
                print(f" ✗ e должно быть в диапазоне (1, {phi}).")
                continue

            if math.gcd(e, phi) != 1:
                print(f" ✗ НОД({e}, {phi}) = {math.gcd(e, phi)} ≠ 1. Выберите из списка выше.")
                continue

            d = mod_inverse(e, phi)
            if d == e:
                print(f" ✗ Для e = {e} получается d = {d}, то есть закрытый ключ равен открытому. Выберите другое e.")
                continue

            break
        except ValueError:
            print(" ✗ Введите целое число.")

    return p, q, e


# ── Форматированный вывод ─────────────────────────────────────────────────────

def print_keys(p, q, n, e, d, phi):
    print("\n╔══════════════════════════════════════════════╗")
    print("║                 Ключи RSA                    ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║ p = {p:<8} q = {q:<8}                 ║")
    print(f"║ n = {n:<12} φ(n) = {phi:<12}     ║")
    print(f"║ Открытый ключ: (e = {e}, n = {n}){' ' * max(0, 8 - len(str(e)) - len(str(n)))}║")
    print(f"║ Закрытый ключ: (d = {d}, n = {n}){' ' * max(0, 8 - len(str(d)) - len(str(n)))}║")
    print("╚══════════════════════════════════════════════╝")


def print_encryption_table(indices, cipher, d, n, max_rows=10):
    """Таблица: буква → m → c → расшифровка."""
    print("\n─── Таблица шифрования ──────────────────────────────────")
    print(f" {'Буква':^6} {'m':^5} {'c = m^e mod n':^16} {'расшифр. m':^12}")
    print(" " + "─" * 44)
    decrypted = decrypt_rsa(cipher[:max_rows], d, n)
    for i in range(min(max_rows, len(indices))):
        ch = IDX_TO_CHAR.get(indices[i], '?')
        print(f" {ch:^6} {indices[i]:^5} {cipher[i]:^16} {decrypted[i]:^12}")
    if len(indices) > max_rows:
        print(f" ... (показаны первые {max_rows} из {len(indices)} символов)")


# ── Режим шифрования ──────────────────────────────────────────────────────────

def encrypt_mode():
    print("\n" + "═" * 50)
    print(" РЕЖИМ ШИФРОВАНИЯ")
    print("═" * 50)

    try:
        p, q, e = input_rsa_params()
        n, e, d, phi = generate_keys(p, q, e)
    except ValueError as err:
        print(f"\n ✗ Ошибка: {err}")
        return None

    print_keys(p, q, n, e, d, phi)

    if n <= 32:
        print(f"\n ⚠ n={n} ≤ 32. Некоторые буквы зашифруются некорректно.")
        return None

    plaintext = input("\n Введите открытый текст:\n > ").strip()
    if not plaintext:
        print(" ✗ Текст не введён.")
        return None

    indices = text_to_indices(plaintext)
    if not indices:
        print(" ✗ В тексте не найдено русских букв.")
        return None

    cipher = encrypt_rsa(indices, e, n)
    print_encryption_table(indices, cipher, d, n)

    cipher_str = ' '.join(str(c) for c in cipher)
    print(f"\n Шифртекст:\n {cipher_str}")

    dec_indices = decrypt_rsa(cipher, d, n)
    dec_text = ''.join(IDX_TO_CHAR.get(m, '?') for m in dec_indices)
    orig_text = ''.join(IDX_TO_CHAR.get(m, '?') for m in indices)
    ok = dec_text == orig_text
    print(f"\n Проверка расшифровки: {dec_text} [{'✓ совпадает' if ok else '✗ НЕ совпадает'}]")

    print("\n Сохраните для расшифровки:")
    print(f" n = {n}, d = {d}")

    return {"n": n, "d": d, "cipher": cipher}


# ── Режим расшифрования ───────────────────────────────────────────────────────

def decrypt_mode():
    print("\n" + "═" * 50)
    print(" РЕЖИМ РАСШИФРОВАНИЯ")
    print("═" * 50)

    try:
        n = int(input("\n Введите n: ").strip())
        d = int(input(" Введите d (закрытый ключ): ").strip())
    except ValueError:
        print(" ✗ n и d должны быть целыми числами.")
        return

    print("\n Введите шифртекст (числа через пробел, пустая строка — конец):")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)

    try:
        cipher = [int(x) for x in " ".join(lines).split()]
    except ValueError:
        print(" ✗ Шифртекст должен содержать только целые числа.")
        return

    if not cipher:
        print(" ✗ Шифртекст пуст.")
        return

    dec_indices = decrypt_rsa(cipher, d, n)
    dec_text = ''.join(IDX_TO_CHAR.get(m, '?') for m in dec_indices)

    print("\n─── Таблица расшифрования ───────────────────────────────")
    print(f" {'i':^5} {'c':^12} {'m = c^d mod n':^16} {'буква':^6}")
    print(" " + "─" * 42)
    for i, (c, m) in enumerate(zip(cipher[:20], dec_indices[:20]), 1):
        ch = IDX_TO_CHAR.get(m, '?')
        print(f" {i:^5} {c:^12} {m:^16} {ch:^6}")
    if len(cipher) > 20:
        print(f" ... (показаны первые 20 из {len(cipher)})")

    print(f"\n Расшифрованный текст:\n {dec_text}")


# ── Главное меню ──────────────────────────────────────────────────────────────

def main():
    print("════════════════════════════════════════════")
    print(" Шифр RSA (Блок H, №21) ")
    print("════════════════════════════════════════════")
    print(f"Алфавит: {''.join(ALPHABET[:16])}")
    print(f"         {''.join(ALPHABET[16:])}")
    print("Индексы: А=1, Б=2, …, Я=32")
    print("Шифрование: c = m^e mod n")
    print("Расшифровка: m = c^d mod n")

    while True:
        print("\n─── Меню ──────────────────────────────────")
        print(" 1 — Зашифровать текст")
        print(" 2 — Расшифровать шифртекст")
        print(" 0 — Выход")

        choice = input("\n Выбор: ").strip()
        if choice == "1":
            encrypt_mode()
        elif choice == "2":
            decrypt_mode()
        elif choice == "0":
            print(" Выход.")
            break
        else:
            print(" ✗ Неверный пункт меню.")


if __name__ == '__main__':
    main()
