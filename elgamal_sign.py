#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Цифровая подпись Эль-Гамаля — алгоритм 25, блок I, методичка.

ГЕНЕРАЦИЯ КЛЮЧЕЙ:
  1. P — простое, G: 1 < G < P
  2. X — секретный ключ: 1 < X <= P-1
  3. Y = G^X mod P — открытый ключ

ПОДПИСАНИЕ:
  4. m = h(M) — квадратичная свёртка mod (P-1), 1 < m < P-1
  5. K: 1 < K < P-1, gcd(K, P-1) = 1  — случайный
  6. a = G^K mod P;  a != 0
  7. b = K^{-1} * (m - X*a) mod (P-1);  b != 0
  8. S = (a, b)

ПРОВЕРКА:
  9. m = h(M)
 10. A1 = Y^a * a^b mod P
     A2 = G^m mod P
 11. A1 == A2 => подпись верна

ПРОВЕРКИ по методичке:
  P простое; P > 33; 1 < G < P; 1 < X <= P-1; Y != 0
  1 < K < P-1; gcd(K, P-1) = 1
  a != 0; b != 0; 0 < a < P; 0 < b < P-1; 1 < m < P-1
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


def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_inverse(a, m):
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        raise ValueError("НОД(%d, %d) = %d != 1 — обратного элемента не существует" % (a, m, g))
    return x % m


# ---------------------------------------------------------------
# ХЭШ: квадратичная свёртка (методичка §16)
#   h0 = 0
#   hi = (h(i-1) + ord(Mi))^2 mod (P-1)
# ---------------------------------------------------------------

def hash_quadratic(message, modulus):
    h = 0
    for ch in message:
        h = pow(h + ord(ch), 2, modulus)
    return h if h != 0 else 1


# ---------------------------------------------------------------
# ПРОВЕРКА ПАРАМЕТРОВ (все условия методички §25)
# ---------------------------------------------------------------

def validate_params(P, G, X):
    """Возвращает Y = G^X mod P при успехе; иначе ValueError."""
    if not is_prime(P):
        raise ValueError("P=%d не является простым числом." % P)
    if P <= 33:
        raise ValueError(
            "P=%d <= 33. Модуль P должен быть > 33 "
            "(коды символов могут превышать 33). "
            "Выберите большее простое: 37, 41, 53, 59, 61, 67, ..." % P
        )
    if not (1 < G < P):
        raise ValueError("G=%d должно удовлетворять 1 < G < P=%d." % (G, P))
    if not (1 < X <= P - 1):
        raise ValueError("X=%d должно удовлетворять 1 < X <= P-1=%d." % (X, P - 1))
    Y = pow(G, X, P)
    if Y == 0:
        raise ValueError("Y = G^X mod P = 0 — недопустимо. Выберите другие G и X.")
    return Y


def validate_k(K, P):
    """Проверка: 1 < K < P-1, gcd(K, P-1) = 1."""
    phi = P - 1
    if not (1 < K < phi):
        raise ValueError("K=%d должно удовлетворять 1 < K < P-1=%d." % (K, phi))
    g = math.gcd(K, phi)
    if g != 1:
        raise ValueError("НОД(K=%d, P-1=%d) = %d != 1. Выберите другой K." % (K, phi, g))


# ---------------------------------------------------------------
# СЛУЧАЙНЫЙ K
# ---------------------------------------------------------------

def random_k(P):
    """Случайный K: 1 < K < P-1, gcd(K, P-1) = 1."""
    phi = P - 1
    while True:
        K = random.randint(2, phi - 1)
        if math.gcd(K, phi) == 1:
            return K


# ---------------------------------------------------------------
# ПОДПИСАНИЕ И ПРОВЕРКА
# ---------------------------------------------------------------

def sign(message, P, G, X, K):
    """Подписание по алгоритму §25. Возвращает (a, b, m)."""
    if not message:
        raise ValueError("Сообщение не должно быть пустым.")
    validate_params(P, G, X)
    validate_k(K, P)

    phi = P - 1
    m = hash_quadratic(message, phi)

    if not (1 < m < phi):
        raise ValueError(
            "Хэш m=%d не в диапазоне 1 < m < P-1=%d. "
            "Попробуйте другое сообщение или P." % (m, phi)
        )

    a = pow(G, K, P)
    if a == 0:
        raise ValueError("a = G^K mod P = 0 — выберите другой K.")

    k_inv = mod_inverse(K, phi)
    b = (k_inv * ((m - X * a) % phi)) % phi

    if b == 0:
        raise ValueError("b = 0 — подпись недействительна. Выберите другой K.")
    if not (0 < a < P):
        raise ValueError("a=%d вне диапазона 0 < a < P=%d." % (a, P))
    if not (0 < b < phi):
        raise ValueError("b=%d вне диапазона 0 < b < P-1=%d." % (b, phi))

    return a, b, m


def verify_sig(message, a, b, P, G, Y):
    """Проверка подписи по алгоритму §25. Возвращает (valid, m, A1, A2)."""
    if not message:
        raise ValueError("Сообщение не должно быть пустым.")
    phi = P - 1
    if not (0 < a < P):
        raise ValueError("a=%d должно удовлетворять 0 < a < P=%d." % (a, P))
    if not (0 < b < phi):
        raise ValueError("b=%d должно удовлетворять 0 < b < P-1=%d." % (b, phi))
    m = hash_quadratic(message, phi)
    A1 = (pow(Y, a, P) * pow(a, b, P)) % P
    A2 = pow(G, m, P)
    return (A1 == A2), m, A1, A2


# ---------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЙ ВВОД
# ---------------------------------------------------------------

def input_int(prompt, lo=None, hi=None, inclusive_hi=False):
    while True:
        try:
            x = int(input(prompt).strip())
            if lo is not None and x <= lo:
                print(" ! Значение должно быть > %d." % lo)
                continue
            if hi is not None:
                if inclusive_hi and x > hi:
                    print(" ! Значение должно быть <= %d." % hi)
                    continue
                elif not inclusive_hi and x >= hi:
                    print(" ! Значение должно быть < %d." % hi)
                    continue
            return x
        except ValueError:
            print(" ! Введите целое число.")


def input_prime(prompt):
    """Ввод простого P строго > 33 (по методичке)."""
    while True:
        try:
            x = int(input(prompt).strip())
            if x <= 33:
                print(" ! P должно быть > 33.")
                continue
            if not is_prime(x):
                print(" ! %d не является простым числом." % x)
                continue
            return x
        except ValueError:
            print(" ! Введите целое число.")


def suggest_k(P, count=15):
    phi = P - 1
    result = []
    for k in range(2, phi):
        if math.gcd(k, phi) == 1:
            result.append(k)
        if len(result) >= count:
            break
    return result


# ---------------------------------------------------------------
# МЕНЮ
# ---------------------------------------------------------------

def ln(c="=", n=70):
    print(c * n)


def menu_keys(state):
    ln()
    print(" ГЕНЕРАЦИЯ КЛЮЧЕЙ (методичка §25)")
    ln()
    print(" Проверки: P простое, P > 33; 1 < G < P; 1 < X <= P-1; Y != 0")
    while True:
        P = input_prime(" P (простое, > 33): ")
        phi = P - 1
        G = input_int(" G (1 < G < %d): " % P, lo=1, hi=P)
        X = input_int(
            " X — секретный ключ (1 < X <= %d): " % phi,
            lo=1, hi=phi, inclusive_hi=True
        )
        try:
            Y = validate_params(P, G, X)
            break
        except ValueError as err:
            print(" ! %s" % err)
            print(" Повторите ввод.")

    state.update({"P": P, "G": G, "X": X, "Y": Y,
                  "last_msg": None, "last_a": None, "last_b": None})
    print()
    print(" P = %d  (простое, > 33: OK)" % P)
    print(" G = %d  (1 < G < P: OK)" % G)
    print(" X = %d  (секретный ключ)" % X)
    print(" Y = G^X mod P = %d^%d mod %d = %d  (открытый ключ)" % (G, X, P, Y))
    print()
    print(" Открытый ключ  : (P=%d, G=%d, Y=%d)" % (P, G, Y))
    print(" Секретный ключ : X=%d" % X)
    print(" [OK] Ключи сохранены.")


def menu_sign(state):
    ln()
    print(" ПОДПИСАНИЕ СООБЩЕНИЯ (методичка §25)")
    ln()
    if state["X"] is None:
        print(" [!] Сначала введите ключи (пункт 1).")
        return

    P, G, X = state["P"], state["G"], state["X"]
    phi = P - 1

    message = input(" Сообщение M: ").strip()
    if not message:
        print(" ! Пустое сообщение.")
        return

    m_show = hash_quadratic(message, phi)
    print()
    print(" Алгоритм хэша (квадратичная свёртка, методичка §16):")
    print("   h0 = 0")
    print("   hi = (h(i-1) + ord(Mi))^2 mod (P-1=%d)" % phi)
    print("   h(M) = %d" % m_show)
    print("   1 < h(M) < P-1 : %s" % (1 < m_show < phi))

    K = random_k(P)
    k_list = suggest_k(P)
    print()
    print(" Условие K: 1 < K < %d, НОД(K, %d) = 1" % (phi, phi))
    print(" Примеры допустимых K: %s" % k_list)
    print(" Случайно выбранный K = %d" % K)
    print(" Проверка: 1 < K < P-1: %s, НОД(K,P-1)=1: %s" % (
        1 < K < phi, math.gcd(K, phi) == 1))

    try:
        a, b, m = sign(message, P, G, X, K)
    except ValueError as err:
        print(" ! %s" % err)
        return

    state["last_msg"] = message
    state["last_a"] = a
    state["last_b"] = b

    k_inv = mod_inverse(K, phi)
    print()
    print(" Шаги вычисления подписи:")
    print("   Шаг 6: a = G^K mod P = %d^%d mod %d = %d" % (G, K, P, a))
    print("   a != 0      : %s" % (a != 0))
    print("   0 < a < P   : %s" % (0 < a < P))
    print("   Шаг 7: K^(-1) mod (P-1) = %d" % k_inv)
    print("   b = K^(-1) * (m - X*a) mod (P-1)")
    print("     = %d * (%d - %d*%d) mod %d" % (k_inv, m, X, a, phi))
    print("     = %d * (%d) mod %d" % (k_inv, m - X * a, phi))
    print("     = %d" % b)
    print("   b != 0      : %s" % (b != 0))
    print("   0 < b < P-1 : %s" % (0 < b < phi))
    print()
    print(" Подпись S = (a, b) = (%d, %d)" % (a, b))
    print(" Передаётся: (M, a=%d, b=%d)" % (a, b))
    print(" [OK] Подпись сохранена.")


def menu_verify(state):
    ln()
    print(" ПРОВЕРКА ПОДПИСИ (методичка §25)")
    ln()
    if state["Y"] is None:
        print(" [!] Сначала введите ключи (пункт 1).")
        return

    P, G, Y = state["P"], state["G"], state["Y"]
    phi = P - 1

    print(" Источник: 1 - из памяти  2 - ввести вручную")
    c = input(" Выбор [Enter=1]: ").strip()

    if c == "2":
        message = input(" Сообщение M: ").strip()
        try:
            a = int(input(" a (0 < a < P=%d): " % P).strip())
            b = int(input(" b (0 < b < P-1=%d): " % phi).strip())
        except ValueError:
            print(" ! a и b должны быть целыми числами.")
            return
    else:
        if state["last_msg"] is None:
            print(" [!] Нет сохранённой подписи. Сначала подпишите (пункт 2).")
            return
        message = state["last_msg"]
        a, b = state["last_a"], state["last_b"]
        print(" Сообщение : %s" % message)
        print(" Подпись   : a=%d, b=%d" % (a, b))

    try:
        valid, m, A1, A2 = verify_sig(message, a, b, P, G, Y)
    except ValueError as err:
        print(" ! %s" % err)
        return

    print()
    print(" Хэш h(M) = %d  (квадратичная свёртка mod P-1=%d)" % (m, phi))
    print(" 1 < h(M) < P-1 : %s" % (1 < m < phi))
    print(" 0 < a < P      : %s" % (0 < a < P))
    print(" 0 < b < P-1    : %s" % (0 < b < phi))
    print()
    print(" A1 = Y^a * a^b mod P = %d^%d * %d^%d mod %d = %d" % (Y, a, a, b, P, A1))
    print(" A2 = G^m mod P        = %d^%d mod %d = %d" % (G, m, P, A2))
    result = "ДЕЙСТВИТЕЛЬНА" if valid else "НЕДЕЙСТВИТЕЛЬНА"
    mark   = "OK" if valid else "!!"
    print()
    print(" [%s] A1 %s A2  =>  Подпись %s" % (mark, "==" if valid else "!=", result))
    if not valid:
        print(" Возможные причины: сообщение изменено, неверная подпись или ключ.")


def menu_demo(state):
    ln()
    print(" ДЕМОНСТРАЦИЯ: подпись + проверка + атака изменением сообщения")
    ln()
    if state["X"] is None or state["Y"] is None:
        print(" [!] Сначала введите ключи (пункт 1).")
        return

    P, G, X, Y = state["P"], state["G"], state["X"], state["Y"]

    message = input(" Сообщение: ").strip()
    if not message:
        print(" ! Пустое сообщение.")
        return

    K = random_k(P)
    print(" Случайно выбранный K = %d" % K)

    try:
        a, b, m = sign(message, P, G, X, K)
    except ValueError as err:
        print(" ! %s" % err)
        return

    print()
    print(" [1] ИСХОДНОЕ: '%s'" % message)
    print("     h(M) = %d,  a = %d,  b = %d" % (m, a, b))
    v, _, A10, A20 = verify_sig(message, a, b, P, G, Y)
    print("     A1=%d, A2=%d  =>  %s" % (A10, A20, "OK — подпись верна" if v else "FAIL"))

    fake = message + " (изменено)"
    print()
    print(" [2] ИЗМЕНЁННОЕ: '%s'" % fake)
    v2, m2, A12, A22 = verify_sig(fake, a, b, P, G, Y)
    print("     h(M') = %d,  A1=%d,  A2=%d" % (m2, A12, A22))
    print("     => %s" % ("OK" if v2 else "ПОДПИСЬ НЕВЕРНА (ожидаемо)"))


def main():
    ln()
    print("  Цифровая подпись Эль-Гамаля  |  Методичка §25, блок I")
    print("  Хэш: квадратичная свёртка (методичка §16)")
    ln()
    print(" Алгоритм хэша:")
    print("   h0 = 0")
    print("   hi = (h(i-1) + ord(Mi))^2 mod (P-1)")
    print()
    print(" Проверки по методичке:")
    print("   P простое; P > 33; 1 < G < P; 1 < X <= P-1; Y != 0")
    print("   K — случайный: 1 < K < P-1, gcd(K,P-1)=1")
    print("   a != 0; b != 0; 0 < a < P; 0 < b < P-1; 1 < h(M) < P-1")

    state = {
        "P": None, "G": None, "X": None, "Y": None,
        "last_msg": None, "last_a": None, "last_b": None
    }

    while True:
        ln("-")
        print(" 1 - Ввести ключи (P, G, X)")
        print(" 2 - Подписать сообщение")
        print(" 3 - Проверить подпись")
        print(" 0 - Выход")
        ln("-")
        choice = input(" Выбор: ").strip()
        if choice == "1":
            menu_keys(state)
        elif choice == "2":
            menu_sign(state)
        elif choice == "3":
            menu_verify(state)
        elif choice == "0":
            print(" Выход.")
            break
        else:
            print(" [!] Введите 0, 1, 2, 3.")


if __name__ == "__main__":
    main()
