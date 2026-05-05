#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Протокол обмена ключами Диффи-Хеллмана  (методичка §28, блок К)

ПАРАМЕТРЫ СИСТЕМЫ (открытые, известны всем):
  n — большое простое число        (общий модуль)
  a — первообразный корень mod n   (1 < a < n)

ВЫРАБОТКА ОБЩЕГО СЕКРЕТНОГО КЛЮЧА K:
  1. Пользователи А и Б выбирают секретные ключи:
       KA, KB ∈ [2, n-1]  (случайные, не разглашаются)
  2. Вычисляют открытые ключи:
       YA = a^KA mod n
       YB = a^KB mod n
  3. Обмениваются YA и YB по открытому каналу.
  4. Независимо вычисляют общий секретный ключ:
       K_A = YB^KA mod n  = (a^KB)^KA mod n = a^(KB·KA) mod n
       K_B = YA^KB mod n  = (a^KA)^KB mod n = a^(KA·KB) mod n
       K_A = K_B = K  (доказательство: степени перемножаются)
"""

import random

# ═══════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════

def is_prime(n):
    """Тест простоты Миллера-Рабина."""
    if n < 2: return False
    if n in (2, 3, 5, 7): return True
    if n % 2 == 0 or n % 3 == 0: return False
    r, d = 0, n - 1
    while d % 2 == 0: r += 1; d //= 2
    for base in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        if base >= n: continue
        x = pow(base, d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1: break
        else: return False
    return True


def element_order(a, n):
    """Вычисляет порядок элемента a в мультипликативной группе Z*_n."""
    order, cur = 1, a % n
    while cur != 1:
        cur = cur * a % n
        order += 1
        if order > n:
            return None
    return order


def is_primitive_root(a, n):
    """Проверяет, является ли a первообразным корнем mod n."""
    if not is_prime(n): return False
    return element_order(a, n) == n - 1




def primitive_roots(n, limit=20):
    vals = []
    for a in range(2, n):
        if element_order(a, n) == n - 1:
            vals.append(a)
            if len(vals) >= limit:
                break
    return vals

def ln(c="=", width=70):
    print(c * width)


def input_int(prompt, lo=None, hi=None):
    """Ввод целого числа с проверкой диапазона."""
    while True:
        try:
            v = int(input(prompt).strip())
            if lo is not None and v < lo:
                print(f"  ! Значение должно быть ≥ {lo}.")
                continue
            if hi is not None and v > hi:
                print(f"  ! Значение должно быть ≤ {hi}.")
                continue
            return v
        except ValueError:
            print("  ! Введите целое число.")


# ═══════════════════════════════════════════════════════════════════
# ДЕМО-ПАРАМЕТРЫ (из методички §28)
# ═══════════════════════════════════════════════════════════════════
#   n = 23 (простое),  a = 5 (первообразный корень mod 23, порядок = 22)
#   KA = 6,  KA = 15
#   YA = 5^6  mod 23 = 8
#   YB = 5^15 mod 23 = 19
#   K  = 19^6 mod 23 = 8^15 mod 23 = 2

DEMO = {"n": 23, "a": 5, "KA": 6, "KB": 15}


# ═══════════════════════════════════════════════════════════════════
# ПУНКТЫ МЕНЮ
# ═══════════════════════════════════════════════════════════════════

def menu_params(state):
    ln()
    print("  ПАРАМЕТРЫ СИСТЕМЫ  (методичка §28, блок К)")
    ln()
    print("  Условия по методичке:")
    print("    n — простое число  (общий модуль)")
    print("    a — первообразный корень mod n,  1 < a < n")
    print()
    print(f"  1 — Ввести вручную")
    print(f"  2 — Демо: n={DEMO['n']}, a={DEMO['a']}  (5 — первообразный корень mod 23)")
    c = input("  Выбор [Enter=2]: ").strip()

    if c == "1":
        while True:
            n = input_int("  n (простое число): ", lo=5)
            if not is_prime(n):
                print(f"  ! {n} не является простым числом. Введите n заново.")
                continue
            break

        roots = primitive_roots(n, limit=20)
        print(f"  Подходящие a (первообразные корни mod {n}, первые {len(roots)}): " +
              (", ".join(map(str, roots)) if roots else "нет"))
        while True:
            a = input_int(f"  a (первообразный корень mod {n}, 1 < a < {n}): ", lo=2, hi=n - 1)
            ord_a = element_order(a, n)
            if ord_a != n - 1:
                print(f"  ! a={a} — НЕ первообразный корень mod {n}.")
                print(f"    Порядок a = {ord_a}, должно быть n-1 = {n-1}.")
                print("  ! Введите a заново.")
                continue
            break
    else:
        n, a = DEMO["n"], DEMO["a"]

    state.update({
        "n": n, "a": a,
        "KA": None, "KB": None,
        "YA": None, "YB": None,
        "K": None,
    })

    ord_a = element_order(a, n)
    print()
    ln("-")
    print(f"  n = {n}  (простое: {is_prime(n)})")
    print(f"  a = {a}  (первообразный корень: {is_primitive_root(a, n)},  порядок = {ord_a} = n-1)")
    ln("-")
    print("  [OK] Общие параметры сохранены.")


def menu_keys(state):
    ln()
    print("  СЕКРЕТНЫЕ КЛЮЧИ ПОЛЬЗОВАТЕЛЕЙ А и Б  (шаги 1–2)")
    ln()
    if state["n"] is None:
        print("  [!] Сначала введите параметры системы (пункт 1).")
        return

    n = state["n"]

    print(f"  Условие: KA, KB ∈ [2, {n-1}]")
    print(f"  Возможные KA и KB: все целые числа от 2 до {n-1}")
    print()
    print(f"  1 — Ввести вручную")
    print(f"  2 — Демо: KA={DEMO['KA']}, KB={DEMO['KB']}")
    c = input("  Выбор [Enter=2]: ").strip()

    if c == "1":
        KA = input_int(f"  Секретный ключ пользователя А  (KA ∈ [2, {n-1}]): ", lo=2, hi=n - 1)
        KB = input_int(f"  Секретный ключ пользователя Б  (KB ∈ [2, {n-1}]): ", lo=2, hi=n - 1)
    else:
        KA, KB = DEMO["KA"], DEMO["KB"]

    state["KA"] = KA
    state["KB"] = KB
    state["YA"] = None
    state["YB"] = None
    state["K"]  = None

    print()
    ln("-")
    print(f"  Пользователь А: KA = {KA}  (секретный, не передаётся)")
    print(f"  Пользователь Б: KB = {KB}  (секретный, не передаётся)")
    ln("-")
    print("  [OK] Секретные ключи сохранены.")


def menu_public(state):
    ln()
    print("  ОТКРЫТЫЕ КЛЮЧИ  (шаг 3: Y = a^K mod n)")
    ln()
    if state["KA"] is None:
        print("  [!] Сначала введите секретные ключи (пункт 2).")
        return

    n, a = state["n"], state["a"]
    KA, KB = state["KA"], state["KB"]

    YA = pow(a, KA, n)
    YB = pow(a, KB, n)

    state["YA"] = YA
    state["YB"] = YB

    print(f"  Пользователь А вычисляет:")
    print(f"    YA = a^KA mod n = {a}^{KA} mod {n} = {YA}")
    print()
    print(f"  Пользователь Б вычисляет:")
    print(f"    YB = a^KB mod n = {a}^{KB} mod {n} = {YB}")
    print()
    ln("-")
    print(f"  Пользователь А публикует: YA = {YA}")
    print(f"  Пользователь Б публикует: YB = {YB}")
    print()
    print("  Обмен открытыми ключами по открытому каналу связи...")
    ln("-")
    print("  [OK] Открытые ключи вычислены и обменяны.")


def menu_shared(state):
    ln()
    print("  ОБЩИЙ СЕКРЕТНЫЙ КЛЮЧ K  (шаги 4–5)")
    ln()
    if state["YA"] is None or state["YB"] is None:
        print("  [!] Сначала вычислите открытые ключи (пункт 3).")
        return

    n, a = state["n"], state["a"]
    KA, KB = state["KA"], state["KB"]
    YA, YB = state["YA"], state["YB"]

    K_A = pow(YB, KA, n)
    K_B = pow(YA, KB, n)

    state["K"] = K_A

    print(f"  Пользователь А (знает KA={KA}, получил YB={YB}):")
    print(f"    K_A = YB^KA mod n = {YB}^{KA} mod {n} = {K_A}")
    print(f"    Доказательство: (a^KB)^KA mod n = a^(KB·KA) mod n = {a}^({KB}·{KA}) mod {n}")
    print(f"                  = {a}^{KB*KA} mod {n} = {pow(a, KB*KA, n)}")
    print()
    print(f"  Пользователь Б (знает KB={KB}, получил YA={YA}):")
    print(f"    K_B = YA^KB mod n = {YA}^{KB} mod {n} = {K_B}")
    print(f"    Доказательство: (a^KA)^KB mod n = a^(KA·KB) mod n = {a}^({KA}·{KB}) mod {n}")
    print(f"                  = {a}^{KA*KB} mod {n} = {pow(a, KA*KB, n)}")
    print()
    ln("-")
    match = K_A == K_B
    mark  = "OK" if match else "!!"
    print(f"  Проверка: K_A = {K_A},  K_B = {K_B}  →  [{mark}] K_A {'=' if match else '≠'} K_B")
    if match:
        print(f"  Общий секретный ключ: K = {K_A}")
    else:
        print(f"  [!!] Ошибка: ключи не совпали.")
    ln("-")


def main():
    ln()
    print("  ДИФФИ-ХЕЛЛМАН | Обмен ключами | Методичка §28, блок К")
    ln()
    print("  Шаги по методичке:")
    print("    1. KA, KB ∈ [2, n-1]        (секретные ключи)")
    print("    2. Y = a^K mod n             (открытые ключи)")
    print("    3. Обмен YA, YB              (открытый канал)")
    print("    4. K = YB^KA = YA^KB mod n  (общий секрет)")

    state = {
        "n": None, "a": None,
        "KA": None, "KB": None,
        "YA": None, "YB": None,
        "K": None,
    }

    while True:
        ln("-")
        print("  1 — Ввести параметры системы (n, a)")
        print("  2 — Ввести секретные ключи (KA, KB)")
        print("  3 — Вычислить и обменять открытые ключи (YA, YB)")
        print("  4 — Вычислить общий секретный ключ K")
        print("  0 — Выход")
        ln("-")
        ch = input("  Выбор: ").strip()
        if   ch == "1": menu_params(state)
        elif ch == "2": menu_keys(state)
        elif ch == "3": menu_public(state)
        elif ch == "4": menu_shared(state)
        elif ch == "0": print("  Выход."); break
        else: print("  [!] Введите 0–4.")


if __name__ == "__main__":
    main()