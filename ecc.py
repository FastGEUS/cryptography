#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECC — шифрование числа по методичке (абсцисса точки)
====================================================
Кривая: E_p(a,b): y² ≡ x³ + a x + b (mod p)

Ключи Боба:
  секретный ключ: c_B, 0 < c_B < q
  открытый ключ:  D_B = [c_B]G

Шифрование (Алиса):
  1) выбирает k, 0 < k < q
  2) R = [k]G
     P = [k]D_B = (x_P, y_P)
  3) e = m · x_P mod p
  4) шифртекст: (R, e)

Расшифрование (Боб):
  1) Q = [c_B]R = (x_Q, y_Q)
  2) m' = e · x_Q^(-1) mod p
"""

import math

INF = None  # точка бесконечности O


# ────────────────────────────────────────────────────────────────
#  МАТЕМАТИКА
# ────────────────────────────────────────────────────────────────

def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = extended_gcd(b % a, a)
    return g, y1 - (b // a) * x1, x1


def mod_inverse(a, m):
    a %= m
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise ValueError(f"НОД({a}, {m}) ≠ 1 — обратного элемента не существует")
    return (x % m + m) % m


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


# ────────────────────────────────────────────────────────────────
#  ЭЛЛИПТИЧЕСКАЯ КРИВАЯ
# ────────────────────────────────────────────────────────────────

def on_curve(P, a, b, p) -> bool:
    if P is INF:
        return True
    x, y = P
    return (y * y - (x * x * x + a * x + b)) % p == 0


def ec_add(P, Q, a, p):
    """Сложение точек P + Q на E_p(a,b)."""
    if P is INF:
        return Q
    if Q is INF:
        return P

    x1, y1 = P
    x2, y2 = Q

    if x1 == x2:
        if (y1 + y2) % p == 0:
            return INF  # P + (-P) = O
        # удвоение: P == Q
        num = (3 * x1 * x1 + a) % p
        den = (2 * y1) % p
        lam = num * mod_inverse(den, p) % p
    else:
        num = (y2 - y1) % p
        den = (x2 - x1) % p
        lam = num * mod_inverse(den, p) % p

    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def ec_mul(k: int, P, a: int, p: int, verbose: bool = False):
    """Скалярное умножение [k]P методом double-and-add (MSB first)."""
    if k == 0 or P is INF:
        return INF

    result = INF
    bits = bin(k)[2:]

    if verbose:
        print(f"\n    k = {k} → двоичное: {bits}")
        print(f"    {'шаг':>4} {'бит':>4} {'после удвоения':>24} {'после сложения':>24}")
        print("    " + "─" * 64)

    for i, bit in enumerate(bits):
        doubled = ec_add(result, result, a, p) if result is not INF else INF
        new_res = ec_add(doubled, P, a, p) if bit == '1' else doubled

        if verbose:
            dbl = 'O' if doubled is INF else str(doubled)
            res = 'O' if new_res is INF else str(new_res)
            print(f"    {i+1:>4} {bit:>4} {dbl:>24} {res:>24}")

        result = new_res

    return result


# ────────────────────────────────────────────────────────────────
#  ВВОД С ПРОВЕРКАМИ
# ────────────────────────────────────────────────────────────────

def input_int(prompt: str, lo=None, hi=None) -> int:
    while True:
        try:
            n = int(input(prompt).strip())
            if lo is not None and n < lo:
                print(f"  ✗ Значение должно быть ≥ {lo}.")
                continue
            if hi is not None and n > hi:
                print(f"  ✗ Значение должно быть ≤ {hi}.")
                continue
            return n
        except ValueError:
            print("  ✗ Введите целое число.")


def input_prime(prompt: str) -> int:
    while True:
        n = input_int(prompt, lo=2)
        if not is_prime(n):
            print(f"  ✗ {n} не является простым числом.")
            continue
        return n


def input_curve():
    print("\n─── Параметры кривой E_p(a,b): y² ≡ x³ + ax + b (mod p) ──")
    p = input_prime("  Простое p: ")
    a = input_int("  a: ")
    b = input_int("  b: ")
    disc = (4 * a**3 + 27 * b**2) % p
    if disc == 0:
        print(f"  ⚠ Внимание: дискриминант 4a³+27b² ≡ 0 (mod {p}), кривая вырождена.")
    else:
        print(f"  Дискриминант 4a³+27b² mod {p} = {disc} (≠ 0) — кривая допустима.")
    return p, a, b


def input_point(prompt: str, a: int, b: int, p: int):
    while True:
        raw = input(prompt).strip()
        try:
            txt = raw.replace("(", "").replace(")", "")
            xs, ys = txt.split(",")
            x = int(xs.strip())
            y = int(ys.strip())
        except Exception:
            print("  ✗ Формат точки: x,y  или  (x,y)")
            continue
        P = (x, y)
        if not on_curve(P, a, b, p):
            lhs = (y * y) % p
            rhs = (x * x * x + a * x + b) % p
            print(f"  ✗ Точка {P} не на кривой: y²={lhs} ≠ x³+ax+b={rhs} (mod {p}).")
            continue
        return P


def print_header(title: str):
    print("\n" + "═" * 70)
    print(title.center(70))
    print("═" * 70)


# ────────────────────────────────────────────────────────────────
#  РЕЖИМ ШИФРОВАНИЯ (АЛИСА)
# ────────────────────────────────────────────────────────────────

def encrypt_mode():
    print_header("РЕЖИМ ШИФРОВАНИЯ (ECC, число m)")

    # 1. Кривая
    p, a, b = input_curve()

    # 2. Генератор и порядок
    print("\n─── Точка-генератор G и её порядок q ───────────────────")
    G = input_point("  G (x,y): ", a, b, p)
    q = input_int("  Порядок q точки G (простое число): ", lo=2)

    # 3. Ключи Боба
    print("\n─── Ключи Боба ─────────────────────────────────────────")
    c_B = input_int(f"  Секретный ключ c_B (0 < c_B < q={q}): ", lo=1, hi=q-1)
    print(f"\n  Вычисляем D_B = [c_B]G = [{c_B}]{G}:")
    D_B = ec_mul(c_B, G, a, p, verbose=True)
    if D_B is INF:
        print("  ✗ D_B = O. Выберите другой c_B.")
        return
    print(f"\n  Открытый ключ Боба: D_B = {D_B}")

    # 4. Число m
    print("\n─── Сообщение ───────────────────────────────────────────")
    m = input_int(f"  Число m (0 < m < p={p}): ", lo=1, hi=p-1)

    # 5. Параметр k
    print("\n─── Параметр Алисы k ───────────────────────────────────")
    k = input_int(f"  k (0 < k < q={q}): ", lo=1, hi=q-1)

    # 6. R = [k]G
    print(f"\n  Вычисление R = [k]G = [{k}]{G}:")
    R = ec_mul(k, G, a, p, verbose=True)
    if R is INF:
        print("  ✗ R = O. Выберите другое k.")
        return

    # 7. P = [k]D_B
    print(f"\n  Вычисление P = [k]D_B = [{k}]{D_B}:")
    P = ec_mul(k, D_B, a, p, verbose=True)
    if P is INF:
        print("  ✗ P = O. Выберите другое k.")
        return

    x_P, y_P = P
    print(f"\n  R = {R}")
    print(f"  P = {P}")
    print(f"  x_P = {x_P}")

    if x_P == 0:
        print("  ✗ x_P = 0 — деление по модулю p невозможно. Выберите другое k.")
        return

    # 8. Шифрование e = m · x_P mod p
    e = (m * x_P) % p

    print_header("РЕЗУЛЬТАТ ШИФРОВАНИЯ")
    print(f"  m   = {m}")
    print(f"  x_P = {x_P}")
    print(f"  e   = m · x_P mod p = {m} · {x_P} mod {p} = {e}")
    print(f"\n  Шифртекст:  (R, e) = ({R}, {e})")

    print("\n─── Данные для проверки ────────────────────────────────")
    print(f"  p={p}, a={a}, b={b}")
    print(f"  G={G}, q={q}")
    print(f"  c_B={c_B}")
    print(f"  R={R}")
    print(f"  e={e}")


# ────────────────────────────────────────────────────────────────
#  РЕЖИМ РАСШИФРОВАНИЯ (БОБ)
# ────────────────────────────────────────────────────────────────

def decrypt_mode():
    print_header("РЕЖИМ РАСШИФРОВАНИЯ (ECC, число m)")

    # 1. Кривая
    p, a, b = input_curve()

    # 2. Секретный ключ Боба
    c_B = input_int("\n  Секретный ключ c_B: ", lo=1)

    # 3. Точка R и число e
    print("\n─── Шифртекст (R, e) ───────────────────────────────────")
    R = input_point("  R (x,y): ", a, b, p)
    e = input_int("  e: ", lo=0, hi=p-1)

    # 4. Q = [c_B]R
    print(f"\n  Вычисление Q = [c_B]R = [{c_B}]{R}:")
    Q = ec_mul(c_B, R, a, p, verbose=True)
    if Q is INF:
        print("  ✗ Q = O. Расшифровка невозможна.")
        return

    x_Q, y_Q = Q
    print(f"\n  Q = {Q}")
    print(f"  x_Q = {x_Q}")

    if x_Q == 0:
        print("  ✗ x_Q = 0 — нельзя найти обратный элемент. Шифртекст некорректен.")
        return

    x_inv = mod_inverse(x_Q, p)
    m = (e * x_inv) % p

    print_header("РЕЗУЛЬТАТ РАСШИФРОВАНИЯ")
    print(f"  x_Q^(-1) mod {p} = {x_inv}")
    print(f"  m' = e · x_Q^(-1) mod p = {e} · {x_inv} mod {p} = {m}\n")


# ────────────────────────────────────────────────────────────────
#  ГЛАВНОЕ МЕНЮ
# ────────────────────────────────────────────────────────────────

def main():
    print("═" * 70)
    print("  ECC — шифрование числа m по абсциссе точки (алг. 23)  ".center(70))
    print("═" * 70)
    print("  Алгоритм строго по методичке:")
    print("    R = [k]G,  P = [k]D_B = (x,y),  e = m·x mod p")
    print("    Q = [c_B]R = (x,y),  m' = e·x^(-1) mod p")

    while True:
        print("\n" + "─" * 70)
        print("  1 — Зашифровать число m")
        print("  2 — Расшифровать (R, e)")
        print("  0 — Выход")
        choice = input("\n  Выбор: ").strip()
        if choice == "1":
            encrypt_mode()
        elif choice == "2":
            decrypt_mode()
        elif choice == "0":
            print("  Выход.")
            break
        else:
            print("  ✗ Неверный пункт меню.")


if __name__ == "__main__":
    main()
