#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Цифровая подпись ГОСТ Р 34.10-94 — алгоритм 26, блок J, методичка.

ПАРАМЕТРЫ СИСТЕМЫ (открытые):
  p — большое простое число (509-512 или 1020-1024 бит)
  q — простой сомножитель (p-1), длина 254-256 бит
  a — число: 1 < a < p-1, a^q mod p = 1
  y = a^x mod p — открытый ключ

СЕКРЕТНЫЙ КЛЮЧ:
  x — случайное число: 0 < x < q

ВЫРАБОТКА ПОДПИСИ (сообщение m):
  1. Сгенерировать случайное k: 0 < k < q
  2. r = (a^k mod p) mod q;   если r=0 — другой k
     s = (x*r + k*H(m)) mod q; если s=0 — другой k
     Если H(m) mod q = 0, взять H(m) = 1
  3. Подпись: (r mod 2^256, s mod 2^256)

ПРОВЕРКА ПОДПИСИ (r, s):
  4. v  = H(m)^(q-2) mod q        [= H(m)^{-1} mod q]
     z1 = (s * v) mod q
     z2 = ((q - r) * v) mod q
     u  = ((a^z1 * y^z2) mod p) mod q
  5. Если u == r — подпись верна.
"""

import math
import random

# ---------------------------------------------------------------
# МАТЕМАТИКА
# ---------------------------------------------------------------

def is_prime(n):
    if n < 2:
        return False
    if n in (2, 3, 5, 7):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    for a in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


# ---------------------------------------------------------------
# ХЭШ: квадратичная свёртка mod q (методичка §16)
#   h0 = 0;  hi = (h_{i-1} + ord(M_i))^2 mod q
# Если H(m) mod q = 0, берём H(m) = 1 (по методичке §26).
# ---------------------------------------------------------------

def hash_msg(message, q):
    h = 0
    for ch in message:
        h = pow(h + ord(ch), 2, q)
    return h if h % q != 0 else 1


# ---------------------------------------------------------------
# ПРОВЕРКА ПАРАМЕТРОВ (критерии методички §26)
# ---------------------------------------------------------------

def validate_params(p, q, a):
    """Проверка p, q, a по условиям алгоритма. Raises ValueError."""
    if not is_prime(p):
        raise ValueError("p=%d не является простым числом." % p)
    if not is_prime(q):
        raise ValueError("q=%d не является простым числом." % q)
    if (p - 1) % q != 0:
        raise ValueError("q=%d не делит p-1=%d." % (q, p - 1))
    if not (1 < a < p - 1):
        raise ValueError("a=%d должно быть: 1 < a < p-1=%d." % (a, p - 1))
    if pow(a, q, p) != 1:
        raise ValueError("a^q mod p != 1. Некорректный генератор a=%d." % a)
    if pow(a, 1, p) == 1:
        raise ValueError("a=1 недопустимо (тривиальный генератор).")




def find_valid_a_values(p, q, limit=20):
    vals = []
    for a in range(2, p - 1):
        if pow(a, q, p) == 1:
            vals.append(a)
            if len(vals) >= limit:
                break
    return vals


def find_valid_q_values(p):
    vals = []
    for q in range(2, p):
        if is_prime(q) and (p - 1) % q == 0:
            vals.append(q)
    return vals

def validate_secret(x, q):
    """0 < x < q."""
    if not (0 < x < q):
        raise ValueError("x=%d должно быть: 0 < x < q=%d." % (x, q))


def validate_k(k, q):
    """0 < k < q."""
    if not (0 < k < q):
        raise ValueError("k=%d должно быть: 0 < k < q=%d." % (k, q))


# ---------------------------------------------------------------
# ВЫРАБОТКА И ПРОВЕРКА ПОДПИСИ
# ---------------------------------------------------------------

def sign(message, p, q, a, x):
    """
    Выработка подписи по ГОСТ Р 34.10-94.
    Возвращает (r, s, k, hm).
    """
    if not message:
        raise ValueError("Сообщение не должно быть пустым.")
    validate_secret(x, q)
    hm = hash_msg(message, q)

    for _ in range(10000):
        k = random.randint(1, q - 1)
        r = pow(a, k, p) % q
        if r == 0:
            continue
        s = (x * r + k * hm) % q
        if s == 0:
            continue
        return r, s, k, hm

    raise RuntimeError("Не удалось подобрать k за 10000 попыток.")


def verify(message, r, s, p, q, a, y):
    """
    Проверка подписи (r, s) по ГОСТ Р 34.10-94.
    Возвращает (valid, hm, v, z1, z2, u).
    """
    if not message:
        raise ValueError("Сообщение не должно быть пустым.")
    if not (0 < r < q):
        raise ValueError("r=%d должно быть: 0 < r < q=%d." % (r, q))
    if not (0 < s < q):
        raise ValueError("s=%d должно быть: 0 < s < q=%d." % (s, q))
    hm = hash_msg(message, q)
    v  = pow(hm, q - 2, q)          # H(m)^{-1} mod q (Ферма, q простое)
    z1 = (s * v) % q
    z2 = ((q - r) * v) % q
    u  = (pow(a, z1, p) * pow(y, z2, p)) % p % q
    return (u == r), hm, v, z1, z2, u


# ---------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЙ ВВОД
# ---------------------------------------------------------------

def input_int(prompt, lo=None, hi=None, inclusive_hi=False):
    while True:
        try:
            x = int(input(prompt).strip())
            if lo is not None and x <= lo:
                print("  ! Значение должно быть > %d." % lo)
                continue
            if hi is not None:
                if inclusive_hi and x > hi:
                    print("  ! Значение должно быть <= %d." % hi)
                    continue
                elif not inclusive_hi and x >= hi:
                    print("  ! Значение должно быть < %d." % hi)
                    continue
            return x
        except ValueError:
            print("  ! Введите целое число.")


def input_prime(prompt, lo=1):
    while True:
        x = input_int(prompt, lo=lo)
        if not is_prime(x):
            print("  ! %d не является простым числом." % x)
            continue
        return x


def ln(c="=", n=70):
    print(c * n)


# ---------------------------------------------------------------
# МЕНЮ: ВВОД ПАРАМЕТРОВ
# ---------------------------------------------------------------

# Демо-параметры для учебных примеров
DEMO = {
    "p": 607,
    "q": 101,
    "a": 64,
    "x": 57,
}


def menu_params(state):
    ln()
    print("  ПАРАМЕТРЫ ГОСТ Р 34.10-94  (методичка §26, блок J)")
    ln()
    print("  Условия:")
    print("    p — простое;  q — простое;  q | (p-1)")
    print("    1 < a < p-1;  a^q mod p = 1;  0 < x < q")
    print()
    print("  1 — Ввести вручную")
    print("  2 — Использовать демо-параметры (p=%d, q=%d, a=%d, x=%d)" % (
        DEMO["p"], DEMO["q"], DEMO["a"], DEMO["x"]))
    c = input("  Выбор [Enter=2]: ").strip()

    if c == "1":
        while True:
            p = input_prime("  p (простое): ", lo=4)

            valid_q = find_valid_q_values(p)
            print("  Подходящие q, для которых q | (p-1=%d): %s" % (
                p - 1, ", ".join(map(str, valid_q)) if valid_q else "нет"))
            if not valid_q:
                print("  ! Ошибка: для данного p нет подходящих простых q, делящих p-1.")
                print("  ! Ввод параметров будет начат заново.")
                continue

            q = input_prime("  q (простое, делитель p-1=%d): " % (p - 1), lo=1)
            if (p - 1) % q != 0:
                print("  ! q=%d не делит p-1=%d. Ввод параметров будет начат заново." % (q, p - 1))
                continue

            valid_a = find_valid_a_values(p, q)
            print("  Подходящие a, для которых a^q mod p = 1 (первые %d): %s" % (
                len(valid_a), ", ".join(map(str, valid_a)) if valid_a else "нет"))
            if not valid_a:
                print("  ! Ошибка: параметры p=%d и q=%d не позволяют закончить генерацию параметров" % (p, q))
                print("  ! для цифровой подписи, так как не найдено ни одного допустимого a.")
                print("  ! Ввод параметров будет начат заново.")
                continue

            while True:
                a = input_int("  a (1 < a < %d): " % (p - 1), lo=2, hi=p - 2)
                if pow(a, q, p) != 1:
                    print("  ! Для a=%d не выполняется условие a^q mod p = 1." % a)
                    print("  ! a^q mod p = %d. Введите a заново." % pow(a, q, p))
                    continue
                break

            print("  Подходящие x: все целые числа от 1 до %d" % (q - 1))
            x = input_int("  x — секретный ключ (0 < x < q=%d): " % q, lo=1, hi=q - 1)
            break
    else:
        p, q, a, x = DEMO["p"], DEMO["q"], DEMO["a"], DEMO["x"]
        validate_params(p, q, a)
        validate_secret(x, q)

    y = pow(a, x, p)
    state.update({"p": p, "q": q, "a": a, "x": x, "y": y,
                  "last_msg": None, "last_r": None, "last_s": None})
    print()
    ln("-")
    print("  p = %d  (простое)" % p)
    print("  q = %d  (простое, q|(p-1): %s)" % (q, (p - 1) % q == 0))
    print("  a = %d  (a^q mod p = %d)" % (a, pow(a, q, p)))
    print("  x = %d  (секретный ключ)" % x)
    print("  y = a^x mod p = %d^%d mod %d = %d  (открытый ключ)" % (a, x, p, y))
    ln("-")
    print("  Открытые параметры: (p=%d, q=%d, a=%d, y=%d)" % (p, q, a, y))
    print("  Секретный ключ: x=%d" % x)
    print("  [OK] Параметры сохранены.")


def menu_sign(state):
    ln()
    print("  ВЫРАБОТКА ПОДПИСИ  (шаги 1-3)")
    ln()
    if state["x"] is None:
        print("  [!] Сначала введите параметры (пункт 1).")
        return

    p, q, a, x = state["p"], state["q"], state["a"], state["x"]

    message = input("  Сообщение M: ").strip()
    if not message:
        print("  ! Пустое сообщение.")
        return

    hm = hash_msg(message, q)
    print()
    print("  ХЭШ (квадратичная свёртка mod q=%d):" % q)
    print("    h0 = 0")
    print("    hi = (h_{i-1} + ord(M_i))^2 mod q")
    print("    H(M) = %d" % hm)
    if hash_msg(message, q) == 1 and hm == 1:
        print("    (H(M) mod q = 0 => взяли H(M) = 1 по методичке)")

    try:
        r, s, k, hm = sign(message, p, q, a, x)
    except (ValueError, RuntimeError) as err:
        print("  ! %s" % err)
        return

    state["last_msg"] = message
    state["last_r"]   = r
    state["last_s"]   = s

    print()
    print("  Шаг 1: случайно выбран k = %d  (0 < k < q=%d)" % (k, q))
    print()
    print("  Шаг 2: вычисление r и s")
    print("    r = (a^k mod p) mod q")
    print("      = (%d^%d mod %d) mod %d" % (a, k, p, q))
    print("      = %d mod %d = %d" % (pow(a, k, p), q, r))
    print("    s = (x*r + k*H(M)) mod q")
    print("      = (%d*%d + %d*%d) mod %d" % (x, r, k, hm, q))
    print("      = (%d + %d) mod %d" % (x * r, k * hm, q))
    print("      = %d mod %d = %d" % (x * r + k * hm, q, s))
    print()
    print("  Шаг 3: ПОДПИСЬ = (r, s) = (%d, %d)" % (r, s))
    print("  [OK] Подпись сохранена.")


# ---------------------------------------------------------------
# МЕНЮ: ПРОВЕРКА ПОДПИСИ
# ---------------------------------------------------------------

def menu_verify(state):
    ln()
    print("  ПРОВЕРКА ПОДПИСИ  (шаги 4-5)")
    ln()
    if state["y"] is None:
        print("  [!] Сначала введите параметры (пункт 1).")
        return

    p, q, a, y = state["p"], state["q"], state["a"], state["y"]

    print("  Источник: 1 — из памяти  2 — ввести вручную")
    c = input("  Выбор [Enter=1]: ").strip()

    if c == "2":
        message = input("  Сообщение M: ").strip()
        try:
            r = int(input("  r (0 < r < q=%d): " % q).strip())
            s = int(input("  s (0 < s < q=%d): " % q).strip())
        except ValueError:
            print("  ! r и s должны быть целыми числами.")
            return
    else:
        if state["last_msg"] is None:
            print("  [!] Нет сохранённой подписи. Сначала подпишите (пункт 2).")
            return
        message = state["last_msg"]
        r, s    = state["last_r"], state["last_s"]
        print("  Сообщение : %s" % message)
        print("  Подпись   : r=%d, s=%d" % (r, s))

    try:
        valid, hm, v, z1, z2, u = verify(message, r, s, p, q, a, y)
    except ValueError as err:
        print("  ! %s" % err)
        return

    print()
    print("  Шаг 4: вычисление u")
    print("    H(M) = %d" % hm)
    print("    v  = H(M)^(q-2) mod q = %d^%d mod %d = %d  [= H(M)^{-1} mod q]" % (
        hm, q - 2, q, v))
    print("    z1 = s*v mod q = %d*%d mod %d = %d" % (s, v, q, z1))
    print("    z2 = (q-r)*v mod q = (%d-%d)*%d mod %d = %d" % (q, r, v, q, z2))
    print("    u  = (a^z1 * y^z2 mod p) mod q")
    print("       = (%d^%d * %d^%d mod %d) mod %d" % (a, z1, y, z2, p, q))
    print("       = (%d * %d mod %d) mod %d" % (
        pow(a, z1, p), pow(y, z2, p), p, q))
    print("       = %d" % u)
    print()
    result = "ДЕЙСТВИТЕЛЬНА" if valid else "НЕДЕЙСТВИТЕЛЬНА"
    mark   = "OK" if valid else "!!"
    print("  Шаг 5: r=%d,  u=%d  =>  [%s] Подпись %s" % (r, u, mark, result))
    if not valid:
        print("  Возможные причины: сообщение изменено или подпись подделана.")


# ---------------------------------------------------------------
# МЕНЮ: ДЕМОНСТРАЦИЯ АТАКИ
# ---------------------------------------------------------------

def main():
    ln()
    print("  ГОСТ Р 34.10-94 | Цифровая подпись | Методичка §26, блок J")
    ln()
    print("  Алгоритм хэша: квадратичная свёртка (методичка §16)")
    print("  Параметры:  p, q — простые;  q|(p-1);  1<a<p-1;  a^q mod p=1")
    print("  Подпись:    r=(a^k mod p) mod q;  s=(x*r + k*H(m)) mod q")
    print("  Проверка:   v=H(m)^{-1} mod q;  u=(a^z1 * y^z2 mod p) mod q;  u==r")

    state = {
        "p": None, "q": None, "a": None, "x": None, "y": None,
        "last_msg": None, "last_r": None, "last_s": None
    }

    while True:
        ln("-")
        print("  1 — Ввести параметры (p, q, a, x)")
        print("  2 — Подписать сообщение")
        print("  3 — Проверить подпись")
        print("  0 — Выход")
        ln("-")
        ch = input("  Выбор: ").strip()
        if ch == "1":
            menu_params(state)
        elif ch == "2":
            menu_sign(state)
        elif ch == "3":
            menu_verify(state)
        elif ch == "0":
            print("  Выход.")
            break
        else:
            print("  [!] Введите 0, 1, 2 или 3.")


if __name__ == "__main__":
    main()