#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Цифровая подпись ГОСТ Р 34.10-2012  (ЭЦП на эллиптических кривых)
Методичка, блок J.

ПАРАМЕТРЫ СИСТЕМЫ (открытые):
  p     — простой модуль поля
  a, b  — коэффициенты кривой E: y² ≡ x³ + ax + b (mod p),  4a³+27b² ≢ 0
  G     — базовая точка (генератор подгруппы порядка q)
  q     — простой порядок точки G

КЛЮЧИ ПОЛЬЗОВАТЕЛЯ:
  xU    — секретный ключ:  0 < xU < q
  YU    — открытый ключ:   YU = [xU]G

ВЫРАБОТКА ПОДПИСИ (сообщение m):
  1. h = H(m);  если h = 0 (mod q) → h := 1
  2. Случайно k:  0 < k < q
  3. P = [k]G = (xP, y)
  4. r = xP mod q;  r = 0 → к шагу 2
  5. s = (k·h + r·xU) mod q;  s = 0 → к шагу 2
  6. Подпись: ξ = r‖s

ПРОВЕРКА ПОДПИСИ (m, r, s):
  1. h = H(m)
  2. 0 < r,s < q  →  иначе недействительна
  3. u1 = s·h⁻¹ mod q;   u2 = −r·h⁻¹ mod q
  4. P = [u1]G + [u2]YU = (xP, y);  P = O → недействительна
  5. xP mod q = r  →  действительна
"""

import random

INF = None   # Точка O (нейтральный элемент)

# ═══════════════════════════════════════════════════════════════════
# МАТЕМАТИКА — ЭЛЛИПТИЧЕСКАЯ КРИВАЯ
# ═══════════════════════════════════════════════════════════════════

def inv_mod(a, m):
    """Обратный элемент a⁻¹ mod m."""
    return pow(a, -1, m)


def point_add(P, Q, a, p):
    """Сложение двух точек P + Q на кривой y² = x³ + ax + b (mod p)."""
    if P is INF: return Q
    if Q is INF: return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return INF                          # P + (-P) = O
    if P != Q:
        lam = (y2 - y1) * inv_mod(x2 - x1, p) % p
    else:                                   # удвоение точки
        lam = (3 * x1 * x1 + a) * inv_mod(2 * y1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def scalar_mul(k, P, a, p):
    """Скалярное умножение [k]P методом double-and-add."""
    R, Q = INF, P
    while k:
        if k & 1:
            R = point_add(R, Q, a, p)
        Q = point_add(Q, Q, a, p)
        k >>= 1
    return R


def on_curve(P, a, b, p):
    """Проверяет, лежит ли точка P на кривой."""
    if P is INF:
        return True
    x, y = P
    return (y * y - (x * x * x + a * x + b)) % p == 0

# ═══════════════════════════════════════════════════════════════════
# КВАДРАТИЧНЫЙ ХЭШ (методичка §16)
#   h0 = 0;   hi = (h_{i-1} + ord(M_i))² mod q
#   Если H(m) ≡ 0 (mod q) → H(m) := 1  (условие стандарта)
# ═══════════════════════════════════════════════════════════════════

def hash_msg(message, q):
    h = 0
    for ch in message:
        h = pow(h + ord(ch), 2, q)
    return h if h % q != 0 else 1


# ═══════════════════════════════════════════════════════════════════
# ВЫРАБОТКА И ПРОВЕРКА ПОДПИСИ
# ═══════════════════════════════════════════════════════════════════

def sign(message, p, a, G, q, x_secret):
    """
    Выработка подписи ГОСТ Р 34.10-2012.
    Возвращает (r, s, k, h).
    """
    h = hash_msg(message, q)
    for _ in range(10000):
        k = random.randint(1, q - 1)
        P = scalar_mul(k, G, a, p)
        if P is INF:
            continue
        r = P[0] % q
        if r == 0:
            continue
        s = (k * h + r * x_secret) % q
        if s == 0:
            continue
        return r, s, k, h
    raise RuntimeError("Не удалось подобрать k за 10000 попыток.")


def verify(message, r, s, p, a, G, q, YU):
    """
    Проверка подписи ГОСТ Р 34.10-2012.
    Возвращает (valid, h, h_inv, u1, u2, P).
    """
    if not (0 < r < q and 0 < s < q):
        return False, None, None, None, None, None
    h = hash_msg(message, q)
    h_inv = pow(h, q - 2, q)               # h⁻¹ mod q (Ферма, q простое)
    u1 = (s * h_inv) % q
    u2 = ((-r) * h_inv) % q                # = (q - r) * h_inv % q
    P1 = scalar_mul(u1, G, a, p)
    P2 = scalar_mul(u2, YU, a, p)
    P  = point_add(P1, P2, a, p)
    if P is INF:
        return False, h, h_inv, u1, u2, INF
    valid = (P[0] % q == r)
    return valid, h, h_inv, u1, u2, P


# ═══════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЙ ВВОД
# ═══════════════════════════════════════════════════════════════════



def find_points_on_curve(a, b, p, limit=30):
    pts = []
    for x in range(p):
        rhs = (x * x * x + a * x + b) % p
        for y in range(p):
            if (y * y) % p == rhs:
                pts.append((x, y))
                if len(pts) >= limit:
                    return pts
    return pts


def point_order(P, a, p, limit=1000):
    Q = P
    for i in range(1, limit + 1):
        if Q is INF:
            return i
        Q = point_add(Q, P, a, p)
    return None


def find_prime_orders(points, a, p, limit=15):
    res = []
    for P in points:
        q = point_order(P, a, p)
        if q is not None and is_prime(q):
            res.append((P, q))
            if len(res) >= limit:
                break
    return res

def is_prime(n):
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


def input_int(prompt, lo=None, hi=None):
    while True:
        try:
            v = int(input(prompt).strip())
            if lo is not None and v <= lo:
                print(f"  ! Значение должно быть > {lo}.")
                continue
            if hi is not None and v >= hi:
                print(f"  ! Значение должно быть < {hi}.")
                continue
            return v
        except ValueError:
            print("  ! Введите целое число.")


def input_point(prompt, a, b, p):
    while True:
        raw = input(prompt).strip().replace("(", "").replace(")", "")
        try:
            xs, ys = raw.split(",")
            P = (int(xs.strip()), int(ys.strip()))
        except Exception:
            print("  ! Формат: x,y  или  (x,y)")
            continue
        if not on_curve(P, a, b, p):
            lhs = (P[1]**2) % p
            rhs = (P[0]**3 + a*P[0] + b) % p
            print(f"  ! Точка {P} не на кривой: y²={lhs} ≠ x³+ax+b={rhs} (mod {p}).")
            continue
        return P


def ln(c="=", n=70):
    print(c * n)


# ═══════════════════════════════════════════════════════════════════
# ДЕМО-ПАРАМЕТРЫ (проверены при разработке)
# ═══════════════════════════════════════════════════════════════════
#   Кривая y² ≡ x³ + x + 4 (mod 23)
#   G = (0, 2),  ord(G) = q = 29
#   x = 12  →  YU = [12]G = (17, 9)

DEMO = {
    "p": 23, "a": 1, "b": 4,
    "Gx": 0, "Gy": 2, "q": 29, "x": 12,
}


# ═══════════════════════════════════════════════════════════════════
# ПУНКТЫ МЕНЮ
# ═══════════════════════════════════════════════════════════════════

def menu_params(state):
    ln()
    print("  ПАРАМЕТРЫ КРИВОЙ И КЛЮЧИ  (ГОСТ Р 34.10-2012)")
    ln()
    print("  Условия:")
    print("    p — простое;  4a³+27b² ≢ 0 (mod p)")
    print("    G = (Gx, Gy) на кривой;  [q]G = O;  q — простое")
    print("    0 < x < q  (секретный ключ)")
    print()
    print(f"  1 — Ввести вручную")
    print(f"  2 — Демо: p={DEMO['p']}, a={DEMO['a']}, b={DEMO['b']}, "
          f"G=({DEMO['Gx']},{DEMO['Gy']}), q={DEMO['q']}, x={DEMO['x']}")
    c = input("  Выбор [Enter=2]: ").strip()

    if c == "1":
        while True:
            p = input_int("  p (простое): ", lo=5)
            if not is_prime(p):
                print(f"  ! {p} не простое. Введите p заново.")
                continue
            break

        while True:
            a = input_int("  a: ")
            b = input_int("  b: ")
            disc = (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p
            if disc == 0:
                print(f"  ! 4a³+27b² ≡ 0 (mod {p}) — кривая вырождена.")
                print("  ! Введите a и b заново.")
                continue
            print(f"  Дискриминант: 4a³+27b² mod {p} = {disc}  ✓")
            break

        pts = find_points_on_curve(a, b, p, limit=40)
        print("  Несколько точек на кривой:", ", ".join(map(str, pts)) if pts else "нет")
        prime_orders = find_prime_orders(pts, a, p, limit=10)
        if prime_orders:
            print("  Подходящие пары (G, q), где q — простой порядок точки G:")
            for P, qv in prime_orders:
                print(f"    G={P}, q={qv}")
        else:
            print("  Подходящих пар (G, q) среди первых найденных точек не найдено.")

        G = input_point(f"  G (x,y) на кривой y²=x³+{a}x+{b} mod {p}: ", a, b, p)

        ord_G = point_order(G, a, p)
        print(f"  Порядок введённой точки G = {ord_G}")
        while True:
            q = input_int(f"  Порядок q (простое): ", lo=2)
            if not is_prime(q):
                print(f"  ! q={q} не простое. Введите q заново.")
                continue
            chk = scalar_mul(q, G, a, p)
            if chk is not INF:
                print(f"  ! [q]G ≠ O. Для q={q} порядок точки G неверен.")
                if ord_G is not None:
                    print(f"  ! Подсказка: для этой точки подходит q = {ord_G}")
                continue
            break

        print(f"  Подходящие x: все целые числа от 1 до {q - 1}")
        x = input_int(f"  Секретный ключ x (0 < x < q={q}): ", lo=1, hi=q)
    else:
        p, a, b = DEMO["p"], DEMO["a"], DEMO["b"]
        G = (DEMO["Gx"], DEMO["Gy"])
        q, x = DEMO["q"], DEMO["x"]

    YU = scalar_mul(x, G, a, p)
    state.update({"p": p, "a": a, "b": b, "G": G, "q": q,
                  "x": x, "YU": YU,
                  "last_msg": None, "last_r": None, "last_s": None})

    print()
    ln("-")
    print(f"  Кривая:  y² ≡ x³ + {a}·x + {b}  (mod {p})")
    print(f"  4a³+27b² mod {p} = {(4*a**3+27*b**2)%p}  (≠ 0)")
    print(f"  G    = {G}")
    print(f"  q    = {q}  (порядок G,  [q]G = O: {scalar_mul(q,G,a,p) is INF})")
    print(f"  x    = {x}  (секретный ключ)")
    print(f"  YU   = [x]G = {YU}  (открытый ключ)")
    ln("-")
    print("  [OK] Параметры сохранены.")


def menu_sign(state):
    ln()
    print("  ВЫРАБОТКА ПОДПИСИ  (шаги 1–6)")
    ln()
    if state["x"] is None:
        print("  [!] Сначала введите параметры (пункт 1).")
        return

    p, a, G, q, x = state["p"], state["a"], state["G"], state["q"], state["x"]

    message = input("  Сообщение: ").strip()
    if not message:
        print("  ! Пустое сообщение.")
        return

    try:
        r, s, k, h = sign(message, p, a, G, q, x)
    except RuntimeError as err:
        print(f"  ! {err}")
        return

    P_k = scalar_mul(k, G, a, p)

    state["last_msg"] = message
    state["last_r"]   = r
    state["last_s"]   = s

    print()
    print(f"  Шаг 1. h = H('{message}') = {h}  (квадратичная свёртка mod q={q})")
    print()
    print(f"  Шаг 2. k = {k}  (случайное, 0 < k < q={q})")
    print()
    print(f"  Шаг 3. P = [k]G = [{k}]{G} = {P_k}")
    print()
    print(f"  Шаг 4. r = xP mod q = {P_k[0]} mod {q} = {r}")
    if r == 0:
        print("         r=0 — потребовался новый k (уже учтено)")
    print()
    print(f"  Шаг 5. s = (k·h + r·x) mod q")
    print(f"           = ({k}·{h} + {r}·{x}) mod {q}")
    print(f"           = ({k*h} + {r*x}) mod {q}")
    print(f"           = {k*h + r*x} mod {q} = {s}")
    print()
    print(f"  Шаг 6. Подпись ξ = r‖s = ({r}, {s})")
    print("  [OK] Подпись сохранена.")


def menu_verify(state):
    ln()
    print("  ПРОВЕРКА ПОДПИСИ  (шаги 1–5)")
    ln()
    if state["YU"] is None:
        print("  [!] Сначала введите параметры (пункт 1).")
        return

    p, a, G, q, YU = state["p"], state["a"], state["G"], state["q"], state["YU"]

    print("  1 — из памяти  2 — ввести вручную")
    c = input("  Выбор [Enter=1]: ").strip()

    if c == "2":
        message = input("  Сообщение: ").strip()
        try:
            r = int(input(f"  r (0 < r < q={q}): ").strip())
            s = int(input(f"  s (0 < s < q={q}): ").strip())
        except ValueError:
            print("  ! r и s должны быть целыми числами.")
            return
    else:
        if state["last_msg"] is None:
            print("  [!] Нет сохранённой подписи. Сначала подпишите (пункт 2).")
            return
        message = state["last_msg"]
        r, s    = state["last_r"], state["last_s"]
        print(f"  Сообщение: {message}")
        print(f"  Подпись: r={r}, s={s}")

    valid, h, h_inv, u1, u2, P = verify(message, r, s, p, a, G, q, YU)

    print()
    print(f"  Шаг 1. h = H('{message}') = {h}")
    print()
    if not (0 < r < q and 0 < s < q):
        print(f"  Шаг 2. ОШИБКА: r={r} или s={s} вне диапазона (0, q={q}).")
        print("  [!!] Подпись НЕДЕЙСТВИТЕЛЬНА.")
        return
    print(f"  Шаг 2. 0 < r={r} < q={q}  ✓  и  0 < s={s} < q={q}  ✓")
    print()
    print(f"  Шаг 3. h⁻¹ = h^(q-2) mod q = {h}^{q-2} mod {q} = {h_inv}")
    print(f"         u1 = s·h⁻¹ mod q = {s}·{h_inv} mod {q} = {u1}")
    u2_pos = u2 % q
    print(f"         u2 = −r·h⁻¹ mod q = −{r}·{h_inv} mod {q} = {u2_pos}")
    print()
    P1 = scalar_mul(u1, G, a, p)
    P2 = scalar_mul(u2, YU, a, p)
    print(f"  Шаг 4. [u1]G  = [{u1}]{G} = {P1}")
    print(f"         [u2]YU = [{u2_pos}]{YU} = {P2}")
    print(f"         P = [u1]G + [u2]YU = {P}")

    if P is INF:
        print("  P = O  →  [!!] Подпись НЕДЕЙСТВИТЕЛЬНА.")
        return

    xP_mod_q = P[0] % q
    result = "ДЕЙСТВИТЕЛЬНА" if valid else "НЕДЕЙСТВИТЕЛЬНА"
    mark   = "OK" if valid else "!!"
    print()
    print(f"  Шаг 5. xP mod q = {P[0]} mod {q} = {xP_mod_q},  r = {r}")
    print(f"         [{mark}] xP mod q {'=' if valid else '≠'} r  →  "
          f"Подпись {result}")


def main():
    ln()
    print("  ГОСТ Р 34.10-2012 | Цифровая подпись на ЭК | Методичка, блок J")
    ln()
    print("  Кривая:   y² ≡ x³ + ax + b  (mod p)")
    print("  Знак:     P=[k]G, r=xP mod q, s=(kh+r·xU) mod q")
    print("  Проверка: u1=s/h mod q, u2=-r/h mod q, P=[u1]G+[u2]YU, xP mod q=?=r")

    state = {
        "p": None, "a": None, "b": None, "G": None, "q": None,
        "x": None, "YU": None,
        "last_msg": None, "last_r": None, "last_s": None,
    }

    while True:
        ln("-")
        print("  1 — Ввести параметры (кривая, ключи)")
        print("  2 — Подписать сообщение")
        print("  3 — Проверить подпись")
        print("  0 — Выход")
        ln("-")
        ch = input("  Выбор: ").strip()
        if   ch == "1": menu_params(state)
        elif ch == "2": menu_sign(state)
        elif ch == "3": menu_verify(state)
        elif ch == "0": print("  Выход."); break
        else: print("  [!] Введите 0–3.")


if __name__ == "__main__":
    main()