#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Цифровая подпись RSA (методичка, блок I §24).

Хэш-функция квадратичной свёртки (методичка §16):
  h0 = 0
  hi = (h(i-1) + ord(Mi))^2 mod N
  m  = h_last; если m==0 -> m=1

Проверки из методички:
  P, Q простые; P != Q; N = P*Q > 32
  1 < E < phi; gcd(E,phi)=1; D != E
  1 < h(M) < N; 0 <= S < N
"""

import random
import math

# ───────────────────────────────────────────────────────────────
# МАТЕМАТИКА
# ───────────────────────────────────────────────────────────────

def miller_rabin(n: int, k: int = 20) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
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


def generate_prime(bits: int) -> int:
    while True:
        n = random.getrandbits(bits)
        n |= (1 << (bits - 1))
        n |= 1
        if miller_rabin(n):
            return n


def extended_gcd(a: int, b: int):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_inverse(e: int, phi: int) -> int:
    g, x, _ = extended_gcd(e, phi)
    if g != 1:
        raise ValueError(f"NOD({e}, {phi}) != 1")
    return x % phi


# ───────────────────────────────────────────────────────────────
# ХЭШ-ФУНКЦИЯ: квадратичная свёртка (методичка формула 16)
# ───────────────────────────────────────────────────────────────

def hash_quadratic(message: str, p: int) -> int:
    """hi = (h(i-1) + ord(Mi))^2 mod p"""
    h = 0
    for ch in message:
        h = pow(h + ord(ch), 2, p)
    return h if h != 0 else 1


# ───────────────────────────────────────────────────────────────
# ПОЛНАЯ ПРОВЕРКА ПАРАМЕТРОВ (все условия методички)
# ───────────────────────────────────────────────────────────────

def validate_params(P: int, Q: int, E: int) -> tuple:
    if not miller_rabin(P):
        raise ValueError(f"P={P} не является простым числом.")
    if not miller_rabin(Q):
        raise ValueError(f"Q={Q} не является простым числом.")
    if P == Q:
        raise ValueError("P и Q должны быть различными.")

    N = P * Q
    phi = (P - 1) * (Q - 1)

    # N > 32 по условию методички (коды букв <= 127, нужен запас)
    if N <= 32:
        raise ValueError(
            f"N = P*Q = {N} <= 32. Выберите большие P и Q (например P=5, Q=11 -> N=55)."
        )

    if phi <= 2:
        raise ValueError(f"phi(N)={phi} слишком мало.")

    if not (1 < E < phi):
        raise ValueError(f"E={E} должно быть в диапазоне 1 < E < phi(N)={phi}.")

    if math.gcd(E, phi) != 1:
        raise ValueError(f"NOD(E={E}, phi(N)={phi}) != 1. Выберите другой E.")

    D = mod_inverse(E, phi)

    if D == E:
        raise ValueError(
            f"D = E = {E}. Закрытый ключ совпадает с открытым. Выберите другой E."
        )

    if D < 1:
        raise ValueError(f"Вычислено некорректное D={D}.")

    return N, phi, D


# ───────────────────────────────────────────────────────────────
# ВВОД
# ───────────────────────────────────────────────────────────────

def input_int(prompt: str, lo=None, hi=None) -> int:
    while True:
        try:
            x = int(input(prompt).strip())
            if lo is not None and x < lo:
                print(f" ! Значение должно быть >= {lo}.")
                continue
            if hi is not None and x > hi:
                print(f" ! Значение должно быть <= {hi}.")
                continue
            return x
        except ValueError:
            print(" ! Введите целое число.")


def input_prime(prompt: str) -> int:
    while True:
        x = input_int(prompt, lo=2)
        if not miller_rabin(x):
            print(f" ! {x} не является простым числом.")
            continue
        return x


def suggest_e(phi: int, count: int = 10) -> list:
    result = []
    for cand in [65537, 257, 17, 13, 11, 7, 5, 3]:
        if 1 < cand < phi and math.gcd(cand, phi) == 1:
            try:
                if mod_inverse(cand, phi) != cand:
                    result.append(cand)
            except ValueError:
                pass
    v = 3
    while len(result) < count and v < phi:
        if v not in result and math.gcd(v, phi) == 1:
            try:
                if mod_inverse(v, phi) != v:
                    result.append(v)
            except ValueError:
                pass
        v += 2
    return sorted(result[:count])


# ───────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ / РУЧНОЙ ВВОД
# ───────────────────────────────────────────────────────────────

def generate_keys(bits: int = 512):
    half = bits // 2
    print(f" Генерация простых чисел ({half} бит)...", end=" ", flush=True)
    P = generate_prime(half)
    Q = generate_prime(half)
    while Q == P or P * Q <= 32:
        Q = generate_prime(half)
    print("готово.")
    E = 65537
    N = P * Q
    phi = (P - 1) * (Q - 1)
    if not (1 < E < phi) or math.gcd(E, phi) != 1:
        for cand in (17, 13, 11, 7, 5, 3):
            if 1 < cand < phi and math.gcd(cand, phi) == 1:
                E = cand
                break
    N, phi, D = validate_params(P, Q, E)
    return (E, N), (D, N), {"P": P, "Q": Q, "phi": phi}


def manual_keys():
    print("\n--- РУЧНОЙ ВВОД ПАРАМЕТРОВ RSA ---")
    print(" Требования: P,Q простые; P!=Q; N>32; 1<E<phi; gcd(E,phi)=1; D!=E")

    while True:
        P = input_prime("\n P (простое): ")
        Q = input_prime(" Q (простое, != P): ")
        if Q == P:
            print(" ! Q должно отличаться от P.")
            continue

        N = P * Q
        phi = (P - 1) * (Q - 1)
        print(f"\n N = {P} x {Q} = {N}")
        print(f" phi(N) = {P-1} x {Q-1} = {phi}")

        if N <= 32:
            print(f" ! N={N} <= 32. Выберите большие P и Q (например P=5, Q=11).")
            continue

        options = suggest_e(phi)
        if not options:
            print(" ! Нет допустимых E для этих P, Q.")
            continue

        print(f"\n Допустимые E: {options}")
        print(f" Enter — выбрать E={options[0]}")

        raw = input(" E: ").strip()
        if raw == "":
            E = options[0]
            print(f" Выбрано E = {E}")
        else:
            try:
                E = int(raw)
            except ValueError:
                print(" ! Введите целое число.")
                continue

        try:
            N, phi, D = validate_params(P, Q, E)
            return (E, N), (D, N), {"P": P, "Q": Q, "phi": phi}
        except ValueError as err:
            print(f" ! {err}\n Повторите ввод.\n")


# ───────────────────────────────────────────────────────────────
# ПОДПИСЬ И ПРОВЕРКА
# ───────────────────────────────────────────────────────────────

def sign(message: str, private_key: tuple) -> tuple:
    if not message:
        raise ValueError("Сообщение не должно быть пустым.")
    D, N = private_key
    if N <= 32:
        raise ValueError(f"N={N} <= 32.")

    m = hash_quadratic(message, N)

    if not (1 < m < N):
        raise ValueError(f"Хэш m={m} не в диапазоне 1 < m < N={N}.")

    S = pow(m, D, N)

    if not (0 <= S < N):
        raise ValueError(f"Подпись S={S} вне диапазона [0, N).")

    return S, m


def verify_sig(message: str, S: int, public_key: tuple) -> tuple:
    if not message:
        raise ValueError("Сообщение не должно быть пустым.")
    E, N = public_key
    if N <= 32:
        raise ValueError(f"N={N} <= 32.")
    if not (1 < E < N):
        raise ValueError(f"E={E} должно быть 1 < E < N={N}.")
    if not (0 <= S < N):
        raise ValueError(f"Подпись S={S} вне диапазона [0, N).")

    m_original = hash_quadratic(message, N)
    m_restored  = pow(S, E, N)
    return (m_restored == m_original), m_original, m_restored


# ───────────────────────────────────────────────────────────────
# МЕНЮ
# ───────────────────────────────────────────────────────────────

def ln(c="=", n=70):
    print(c * n)


def menu_keys(state: dict):
    ln()
    print(" ГЕНЕРАЦИЯ / ВВОД КЛЮЧЕЙ RSA")
    ln()
    print(" 1 - Автогенерация")
    print(" 2 - Ввести P, Q, E вручную")
    c = input(" Выбор [Enter=1]: ").strip()

    if c == "2":
        pub, priv, params = manual_keys()
    else:
        print(" Битовая длина N: 1-512 бит  2-1024 бит")
        b = input(" Выбор [Enter=1]: ").strip()
        bits = 1024 if b == "2" else 512
        pub, priv, params = generate_keys(bits)

    state.update({"pub": pub, "priv": priv, "last_msg": None, "last_sig": None})
    E, N = pub
    D, _ = priv
    n_ok = "OK (> 32)" if N > 32 else "!!! <= 32"
    print(f"\n P       = {params['P']}")
    print(f" Q       = {params['Q']}")
    print(f" N       = {N}  [{n_ok}]")
    print(f" phi(N)  = {params['phi']}")
    print(f" E       = {E}  (открытый ключ)")
    print(f" D       = {D}  (закрытый ключ)")
    print(f" D != E  : {D != E}")
    print(" [OK] Ключи сохранены.")


def menu_sign(state: dict):
    ln()
    print(" СОЗДАНИЕ ПОДПИСИ")
    ln()
    if state["priv"] is None:
        print(" [!] Сначала сгенерируйте ключи (пункт 1).")
        return
    message = input(" Сообщение: ").strip()
    try:
        S, m = sign(message, state["priv"])
    except ValueError as err:
        print(f" [!] {err}")
        return

    state["last_msg"] = message
    state["last_sig"] = S
    _, N = state["priv"]
    print(f"\n Сообщение      : {message}")
    print(f" Алгоритм хэша  : hi = (h(i-1) + ord(Mi))^2 mod N")
    print(f" Хэш h(M)       = {m}")
    print(f" 1 < h(M) < N   : {1 < m < N}")
    print(f" Подпись S      = {m}^D mod {N} = {S}")
    print(f" 0 <= S < N     : {0 <= S < N}")
    print(" [OK] Подпись сохранена.")


def menu_verify(state: dict):
    ln()
    print(" ПРОВЕРКА ПОДПИСИ")
    ln()
    if state["pub"] is None:
        print(" [!] Сначала сгенерируйте ключи (пункт 1).")
        return

    print(" Источник: 1 - из памяти  2 - ввести вручную")
    c = input(" Выбор [Enter=1]: ").strip()

    if c == "2":
        message = input(" Сообщение: ").strip()
        try:
            S = int(input(" Подпись S: ").strip())
        except ValueError:
            print(" [!] Подпись должна быть целым числом.")
            return
    else:
        if state["last_msg"] is None or state["last_sig"] is None:
            print(" [!] Нет сохранённой подписи. Сначала подпишите сообщение.")
            return
        message = state["last_msg"]
        S = state["last_sig"]
        print(f" Сообщение : {message}")
        print(f" Подпись S = {S}")

    try:
        valid, m_orig, m_rest = verify_sig(message, S, state["pub"])
    except ValueError as err:
        print(f" [!] {err}")
        return

    print(f"\n h(M)         = {m_orig}")
    print(f" S^E mod N    = {m_rest}")
    result = "ДЕЙСТВИТЕЛЬНА" if valid else "НЕДЕЙСТВИТЕЛЬНА"
    mark   = "OK" if valid else "!!"
    print(f"\n [{mark}] Подпись {result}")
    if not valid:
        print(" Сообщение изменено, неверная подпись или ключ.")


def menu_demo(state: dict):
    ln()
    print(" ДЕМОНСТРАЦИЯ: подпись + проверка + атака изменением")
    ln()
    if state["priv"] is None or state["pub"] is None:
        print(" [!] Сначала сгенерируйте ключи (пункт 1).")
        return

    message = input(" Сообщение: ").strip()
    try:
        S, m = sign(message, state["priv"])
    except ValueError as err:
        print(f" [!] {err}")
        return

    print(f"\n [1] ИСХОДНОЕ: '{message}'")
    print(f"     h(M) = {m}  |  S = {S}")
    valid, mo, mr = verify_sig(message, S, state["pub"])
    print(f"     h(M)={mo}  S^E mod N={mr}  => {'OK' if valid else 'FAIL'}")

    fake = message + " (изменено)"
    print(f"\n [2] ИЗМЕНЁННОЕ: '{fake}'")
    valid2, mo2, mr2 = verify_sig(fake, S, state["pub"])
    print(f"     h(M)={mo2}  S^E mod N={mr2}")
    print(f"     Результат: {'OK' if valid2 else 'ПОДПИСЬ НЕВЕРНА (ожидаемо)'}")


def main():
    ln()
    print("  Цифровая подпись RSA  |  Методичка §24")
    print("  Хэш: квадратичная свёртка (методичка §16)")
    ln()
    print(" Алгоритм хэша:")
    print("   h0 = 0")
    print("   hi = (h(i-1) + ord(Mi))^2 mod N")
    print()
    print(" Проверки:")
    print("   P,Q простые; P!=Q; N=P*Q > 32")
    print("   1 < E < phi; gcd(E,phi)=1; D!=E")
    print("   1 < h(M) < N; 0 <= S < N")

    state = {"pub": None, "priv": None, "last_msg": None, "last_sig": None}

    while True:
        ln("-")
        print(" 1 - Сгенерировать / ввести ключи")
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
