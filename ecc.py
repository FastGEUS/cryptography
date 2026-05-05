#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================================
#                       ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

# Алфавит и таблицы соответствия
alf = ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н',
       'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я']

char_to_num = {
    'а': 1, 'б': 2, 'в': 3, 'г': 4, 'д': 5,
    'е': 6, 'ж': 7, 'з': 8, 'и': 9, 'й': 10,
    'к': 11, 'л': 12, 'м': 13, 'н': 14, 'о': 15,
    'п': 16, 'р': 17, 'с': 18, 'т': 19, 'у': 20,
    'ф': 21, 'х': 22, 'ц': 23, 'ч': 24, 'ш': 25,
    'щ': 26, 'ъ': 27, 'ы': 28, 'ь': 29, 'э': 30,
    'ю': 31, 'я': 32
}

num_to_char = {v: k for k, v in char_to_num.items()}


def preprocess_text(text, encrypt_mode=True):
    text = text.lower()
    if encrypt_mode:
        replacements = {
            '.': 'тчк', ',': 'зпт', '-': 'трр', ':': 'двт',
            ';': 'тсз', '!': 'вск', '?': 'врс', ' ': 'прб'
        }
        for symbol, replacement in replacements.items():
            text = text.replace(symbol, replacement)
    return text


def postprocess_text(text):
    text = text.lower()
    replacements = {
        'тчк': '.', 'зпт': ',', 'трр': '-', 'двт': ':',
        'тсз': ';', 'вск': '!', 'врс': '?', 'прб': ' '
    }
    for sequence, symbol in replacements.items():
        text = text.replace(sequence, symbol)
    return text


def text_to_numbers(text):
    numbers = []
    for ch in text:
        if ch in char_to_num:
            numbers.append(char_to_num[ch])
        else:
            print(f"  ⚠️ Предупреждение: символ '{ch}' пропущен")
    return numbers


def numbers_to_text(numbers):
    text = ""
    for num in numbers:
        if num in num_to_char:
            text += num_to_char[num]
        else:
            text += f"[{num}]"
    return text


def mod_inverse(k, p):
    return pow(k, p - 2, p)


# ============================================================================
#                     ФУНКЦИИ ДЛЯ ЭЛЛИПТИЧЕСКИХ КРИВЫХ
# ============================================================================

def add_points(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if x1 == x2 and y1 == y2:
        numerator = (3 * x1 * x1 + a) % p
        denominator = (2 * y1) % p
    else:
        numerator = (y2 - y1) % p
        denominator = (x2 - x1) % p
    lam = (numerator * mod_inverse(denominator, p)) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def multiply_point(k, P, a, p):
    if P is None or k == 0:
        return None
    result = None
    current = P
    while k:
        if k & 1:
            result = add_points(result, current, a, p)
        current = add_points(current, current, a, p)
        k >>= 1
    return result


def find_point_order(P, a, p):
    if P is None:
        return 1
    current = P
    order = 1
    while current is not None:
        current = add_points(current, P, a, p)
        order += 1
        if order > p * 2:
            break
    return order


def find_all_points(a, b, p):
    points = []
    for x in range(p):
        right_side = (pow(x, 3, p) + a * x + b) % p
        for y in range(p):
            if pow(y, 2, p) == right_side:
                points.append((x, y))
    return points


def factorize(n):
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def find_subgroup_order(a, b, p):
    points = find_all_points(a, b, p)
    n = len(points) + 1
    factors = factorize(n)
    q = max(factors)
    return q


def find_points_orders(points, a, p):
    orders = {}
    for point in points:
        orders[point] = find_point_order(point, a, p)
    return orders


def find_cryptographic_points(points, orders):
    suitable = []
    for point in points:
        order = orders[point]
        if order > 2:
            factors = factorize(order)
            if len(factors) == 1 and order > 1:
                suitable.append(point)
    return suitable


def encrypt_ecc(message, public_key, G, a, p, k):
    if message >= p:
        raise ValueError(f"Число {message} должно быть меньше {p}")
    R = multiply_point(k, G, a, p)
    P = multiply_point(k, public_key, a, p)
    x = P[0]
    e = (message * x) % p
    return R, e


def decrypt_ecc(ciphertext, private_key, a, p):
    R, e = ciphertext
    Q = multiply_point(private_key, R, a, p)
    x = Q[0]
    x_inv = mod_inverse(x, p)
    message = (e * x_inv) % p
    return message


def parse_cipher_input_for_text_mode(input_str):
    input_str = input_str.strip()
    if ' ' in input_str:
        parts = input_str.split()
        numbers = []
        for part in parts:
            try:
                numbers.append(int(part))
            except ValueError:
                print(f"   Ошибка: неверное число '{part}'")
                return None
        return numbers
    else:
        numbers = []
        for i in range(0, len(input_str), 2):
            if i + 2 <= len(input_str):
                try:
                    numbers.append(int(input_str[i:i+2]))
                except ValueError:
                    print(f"   Ошибка: неверное число '{input_str[i:i+2]}'")
                    return None
        return numbers


# ============================================================================
#                           ГЛАВНАЯ ПРОГРАММА
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("          КРИПТОСИСТЕМА НА ЭЛЛИПТИЧЕСКИХ КРИВЫХ (ECC)          ")
    print("               Шифрование по схеме Эль-Гамаля на кривой          ")
    print("=" * 80)

    while True:
        print("\n" + "=" * 40 + " МЕНЮ " + "=" * 40)
        print("1  Зашифровать текст/число")
        print("2  Расшифровать текст/число")
        print("0️  Выход")
        print("=" * 86)

        action_choice = input(" Ваш выбор: ").strip()

        if action_choice == '0':
            print("\n До свидания!")
            break
        if action_choice not in ('1', '2'):
            print(" Неверный выбор. Введите 0, 1 или 2.")
            continue

        encrypt_mode = (action_choice == '1')

        # Выбор режима ввода/вывода
        print("\nВыберите режим ввода/вывода:")
        print("1️  Текст (русские буквы, знаки заменяются)")
        print("2️  Параметры (целые числа)")
        mode_choice = input(" Ваш выбор (1-2): ").strip()
        text_input_mode = (mode_choice == '1')
        if mode_choice not in ('1', '2'):
            print(" Неверный выбор.")
            continue

        try:
            # Ввод параметров кривой
            print("\n--- Параметры эллиптической кривой ---")
            a = int(input("  a: "))
            b = int(input("  b: "))
            p = int(input("  p (простое число): "))

            # Находим подходящую подгруппу
            all_points = find_all_points(a, b, p)
            orders = find_points_orders(all_points, a, p)
            crypto_points = find_cryptographic_points(all_points, orders)
            q = find_subgroup_order(a, b, p)
            print(f"\n  ! Порядок подгруппы q = {q}")

            if encrypt_mode:
                # Ввод базовой точки G
                Gx, Gy = map(int, input("\nВведите базовую точку G (x y): ").split())
                G = (Gx, Gy)
                c_B = int(input(f"Введите секретный ключ получателя c_B (1..{q-1}): "))
                if c_B < 1 or c_B >= q:
                    print(f" Ошибка: c_B должно быть в диапазоне 1..{q-1}")
                    continue
                public_key = multiply_point(c_B, G, a, p)
                print(f"\n Открытый ключ D_B = {public_key}")

                if text_input_mode:
                    # Шифрование текста
                    text = input("\n Введите текст для шифрования: ")
                    processed = preprocess_text(text, encrypt_mode=True)
                    numbers = text_to_numbers(processed)
                    if not numbers:
                        print(" Нет допустимых символов.")
                        continue

                    import random
                    cipher_blocks = []
                    print("\n  Генерация случайных чисел k для каждого символа:")
                    for i, num in enumerate(numbers):
                        k = random.randint(1, q - 1)
                        print(f"    Символ '{text[i]}' (число {num}): k = {k}")
                        R, e = encrypt_ecc(num, public_key, G, a, p, k)
                        cipher_blocks.append(((R[0], R[1]), e))

                    # Формируем результат
                    all_numbers = []
                    for (Rx, Ry), e in cipher_blocks:
                        all_numbers.extend([Rx, Ry, e])

                    print("\n" + "=" * 80)
                    print(" РЕЗУЛЬТАТ ШИФРОВАНИЯ")
                    print("=" * 80)
                    for i, ((Rx, Ry), e) in enumerate(cipher_blocks):
                        print(f"  Блок {i+1}: R=({Rx}, {Ry}), e={e}")
                    numbers_string = ''.join(f"{num:02d}" for num in all_numbers)
                    numbers_grouped = ' '.join(numbers_string[i:i+5] for i in range(0, len(numbers_string), 5))
                    print(f"\n Шифротекст (скопируйте строку):\n  {numbers_grouped}")

                else:
                    # Шифрование одного числа
                    m = int(input("\nЧисло m для шифрования (< p): "))
                    k = int(input(f"Введите k (1..{q-1}): "))
                    R, e = encrypt_ecc(m, public_key, G, a, p, k)
                    print("\n" + "=" * 80)
                    print(" РЕЗУЛЬТАТ ШИФРОВАНИЯ")
                    print("=" * 80)
                    print(f"  R = ({R[0]}, {R[1]})")
                    print(f"  e = {e}")

            else:
                # Расшифрование
                c_B = int(input(f"\nВведите секретный ключ c_B (1..{q-1}): "))
                if c_B < 1 or c_B >= q:
                    print(f" Ошибка: c_B должно быть в диапазоне 1..{q-1}")
                    continue

                if text_input_mode:
                    # Расшифрование текста из строки
                    cipher_str = input("Введите шифротекст (строка вида '10 6 9' или '100609'): ").strip()
                    all_numbers = parse_cipher_input_for_text_mode(cipher_str)
                    if all_numbers is None or len(all_numbers) % 3 != 0:
                        print(" Ошибка: неверный формат (ожидается кратное 3 числам).")
                        continue
                    cipher_blocks = []
                    for i in range(0, len(all_numbers), 3):
                        Rx, Ry, e = all_numbers[i], all_numbers[i+1], all_numbers[i+2]
                        cipher_blocks.append(((Rx, Ry), e))

                    print(f"\n  Получено {len(cipher_blocks)} блоков.")
                    decrypted_numbers = []
                    for (R, e) in cipher_blocks:
                        m = decrypt_ecc((R, e), c_B, a, p)
                        decrypted_numbers.append(m)

                    decrypted_text = numbers_to_text(decrypted_numbers)
                    result = postprocess_text(decrypted_text)
                    print("\n" + "=" * 80)
                    print(" РЕЗУЛЬТАТ РАСШИФРОВАНИЯ")
                    print("=" * 80)
                    print(f" Расшифрованный текст: {result}")

                else:
                    # Расшифрование одного блока
                    Rx, Ry = map(int, input("Введите R (x y): ").split())
                    e = int(input("Введите e: "))
                    R = (Rx, Ry)
                    m = decrypt_ecc((R, e), c_B, a, p)
                    print("\n" + "=" * 80)
                    print(" РЕЗУЛЬТАТ РАСШИФРОВАНИЯ")
                    print("=" * 80)
                    print(f"  Расшифрованное число m = {m}")

        except Exception as e:
            print(f"\n ОШИБКА: {e}")

        print("=" * 50)
        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()