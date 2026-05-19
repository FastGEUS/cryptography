# -*- coding: utf-8 -*-

from typing import Dict, Any, List

PI = [
    [12, 4, 6, 2, 10, 5, 11, 9, 14, 8, 13, 7, 0, 3, 15, 1],
    [6, 8, 2, 3, 9, 10, 5, 12, 1, 14, 4, 7, 11, 13, 0, 15],
    [11, 3, 5, 8, 2, 15, 10, 13, 14, 1, 7, 4, 12, 9, 6, 0],
    [12, 8, 2, 1, 13, 4, 15, 6, 7, 0, 10, 5, 3, 14, 9, 11],
    [7, 15, 5, 10, 8, 1, 6, 13, 0, 9, 3, 14, 11, 4, 2, 12],
    [5, 13, 15, 6, 9, 2, 12, 10, 11, 7, 8, 1, 4, 3, 14, 0],
    [8, 14, 2, 5, 6, 9, 1, 12, 15, 4, 11, 0, 13, 10, 3, 7],
    [1, 7, 14, 13, 0, 5, 8, 3, 4, 15, 10, 6, 9, 12, 11, 2]
]


def is_valid_hex(text: str, expected_length: int) -> bool:
    if len(text) != expected_length:
        return False
    try:
        int(text, 16)
        return True
    except ValueError:
        return False


def normalize_hex(text: str, expected_length: int, field_name: str) -> str:
    text = text.strip().lower()
    if text.startswith("0x"):
        text = text[2:]

    if not is_valid_hex(text, expected_length):
        raise ValueError(
            f"{field_name} должен быть HEX-строкой длиной {expected_length} символов."
        )
    return text


def t_transform(a: int) -> int:
    result = 0
    for i in range(8):
        nibble = (a >> (4 * i)) & 0x0F
        substituted = PI[i][nibble]
        result |= (substituted << (4 * i))
    return result


def rotate_left_11(value: int) -> int:
    value &= 0xFFFFFFFF
    return ((value << 11) | (value >> 21)) & 0xFFFFFFFF


def g_transform_details(k: int, a: int) -> Dict[str, int]:
    added = (a + k) & 0xFFFFFFFF
    t_value = t_transform(added)
    rotated = rotate_left_11(t_value)

    return {
        "input_a": a & 0xFFFFFFFF,
        "round_key": k & 0xFFFFFFFF,
        "after_add_mod32": added,
        "after_t": t_value,
        "after_rot11": rotated
    }


def g_transform(k: int, a: int) -> int:
    return g_transform_details(k, a)["after_rot11"]


def G_transform(k: int, a1: int, a0: int):
    new_a1 = a0
    new_a0 = g_transform(k, a0) ^ a1
    return new_a1, new_a0


def G_star_transform(k: int, a1: int, a0: int):
    result_high = g_transform(k, a0) ^ a1
    result_low = a0
    return result_high, result_low


def generate_round_keys(key_hex: str) -> List[int]:
    key_hex = normalize_hex(key_hex, 64, "Ключ")
    key_bytes = bytes.fromhex(key_hex)

    K = []
    for i in range(8):
        k_bytes = key_bytes[i * 4:(i + 1) * 4]
        K.append(int.from_bytes(k_bytes, byteorder='big'))

    round_keys = []
    round_keys.extend(K)
    round_keys.extend(K)
    round_keys.extend(K)
    round_keys.extend(K[::-1])

    return round_keys


def magma_encrypt_block(block_hex: str, key_hex: str, return_rounds: bool = False) -> Dict[str, Any]:
    try:
        block_hex = normalize_hex(block_hex, 16, "Открытый текст")
        key_hex = normalize_hex(key_hex, 64, "Ключ")

        round_keys = generate_round_keys(key_hex)
        block = int(block_hex, 16)

        a1 = (block >> 32) & 0xFFFFFFFF
        a0 = block & 0xFFFFFFFF

        rounds = []

        for i in range(31):
            g_info = g_transform_details(round_keys[i], a0)
            new_a1 = a0
            new_a0 = g_info["after_rot11"] ^ a1

            if return_rounds:
                rounds.append({
                    "round": i + 1,
                    "type": "G",
                    "key": f"{round_keys[i]:08x}",
                    "in_a1": f"{a1:08x}",
                    "in_a0": f"{a0:08x}",
                    "a0_plus_k": f"{g_info['after_add_mod32']:08x}",
                    "after_t": f"{g_info['after_t']:08x}",
                    "after_rot11": f"{g_info['after_rot11']:08x}",
                    "out_a1": f"{new_a1:08x}",
                    "out_a0": f"{new_a0:08x}"
                })

            a1, a0 = new_a1, new_a0

        g_info = g_transform_details(round_keys[31], a0)
        b1 = g_info["after_rot11"] ^ a1
        b0 = a0

        if return_rounds:
            rounds.append({
                "round": 32,
                "type": "G*",
                "key": f"{round_keys[31]:08x}",
                "in_a1": f"{a1:08x}",
                "in_a0": f"{a0:08x}",
                "a0_plus_k": f"{g_info['after_add_mod32']:08x}",
                "after_t": f"{g_info['after_t']:08x}",
                "after_rot11": f"{g_info['after_rot11']:08x}",
                "out_a1": f"{b1:08x}",
                "out_a0": f"{b0:08x}"
            })

        result = (b1 << 32) | b0

        return {
            "success": True,
            "algorithm": "magma",
            "mode": "encrypt",
            "input_block": block_hex,
            "key": key_hex,
            "round_keys": [f"{k:08x}" for k in round_keys],
            "rounds": rounds,
            "result_block": f"{result:016x}"
        }

    except Exception as e:
        return {
            "success": False,
            "algorithm": "magma",
            "mode": "encrypt",
            "error": str(e),
            "input_block": block_hex,
            "key": key_hex
        }


def magma_decrypt_block(block_hex: str, key_hex: str, return_rounds: bool = False) -> Dict[str, Any]:
    try:
        block_hex = normalize_hex(block_hex, 16, "Зашифрованный текст")
        key_hex = normalize_hex(key_hex, 64, "Ключ")

        round_keys = generate_round_keys(key_hex)
        block = int(block_hex, 16)

        b1 = (block >> 32) & 0xFFFFFFFF
        b0 = block & 0xFFFFFFFF

        rounds = []

        for i in range(31, 0, -1):
            g_info = g_transform_details(round_keys[i], b0)
            new_b1 = b0
            new_b0 = g_info["after_rot11"] ^ b1

            if return_rounds:
                rounds.append({
                    "round": 32 - i,
                    "type": "G",
                    "key": f"{round_keys[i]:08x}",
                    "in_a1": f"{b1:08x}",
                    "in_a0": f"{b0:08x}",
                    "a0_plus_k": f"{g_info['after_add_mod32']:08x}",
                    "after_t": f"{g_info['after_t']:08x}",
                    "after_rot11": f"{g_info['after_rot11']:08x}",
                    "out_a1": f"{new_b1:08x}",
                    "out_a0": f"{new_b0:08x}"
                })

            b1, b0 = new_b1, new_b0

        g_info = g_transform_details(round_keys[0], b0)
        a1 = g_info["after_rot11"] ^ b1
        a0 = b0

        if return_rounds:
            rounds.append({
                "round": 32,
                "type": "G*",
                "key": f"{round_keys[0]:08x}",
                "in_a1": f"{b1:08x}",
                "in_a0": f"{b0:08x}",
                "a0_plus_k": f"{g_info['after_add_mod32']:08x}",
                "after_t": f"{g_info['after_t']:08x}",
                "after_rot11": f"{g_info['after_rot11']:08x}",
                "out_a1": f"{a1:08x}",
                "out_a0": f"{a0:08x}"
            })

        result = (a1 << 32) | a0

        return {
            "success": True,
            "algorithm": "magma",
            "mode": "decrypt",
            "input_block": block_hex,
            "key": key_hex,
            "round_keys": [f"{k:08x}" for k in round_keys],
            "rounds": rounds,
            "result_block": f"{result:016x}"
        }

    except Exception as e:
        return {
            "success": False,
            "algorithm": "magma",
            "mode": "decrypt",
            "error": str(e),
            "input_block": block_hex,
            "key": key_hex
        }


def run_magma(
    mode: str,
    block_hex: str,
    key_hex: str,
    return_rounds: bool = False
) -> Dict[str, Any]:
    if mode == "encrypt":
        return magma_encrypt_block(block_hex, key_hex, return_rounds=return_rounds)
    elif mode == "decrypt":
        return magma_decrypt_block(block_hex, key_hex, return_rounds=return_rounds)
    else:
        return {
            "success": False,
            "algorithm": "magma",
            "mode": mode,
            "error": "mode должен быть 'encrypt' или 'decrypt'."
        }


def format_feistel_table(rounds: List[Dict[str, Any]]) -> str:
    if not rounds:
        return "Таблица раундов отсутствует."

    lines = []
    lines.append(
        "Rnd | T  | Key      | InA1     | InA0     | A0+K     | S(A0+K)  | Rot11    | OutA1    | OutA0"
    )
    lines.append("-" * 110)

    for r in rounds:
        lines.append(
            f"{r['round']:>3} | "
            f"{r['type']:<2} | "
            f"{r['key']} | "
            f"{r['in_a1']} | "
            f"{r['in_a0']} | "
            f"{r['a0_plus_k']} | "
            f"{r['after_t']} | "
            f"{r['after_rot11']} | "
            f"{r['out_a1']} | "
            f"{r['out_a0']}"
        )

    return "\n".join(lines)


def test_gost_example() -> Dict[str, Any]:
    key = "ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    plaintext = "fedcba9876543210"
    expected_cipher = "4ee901e5c2d8ca3d"

    enc = magma_encrypt_block(plaintext, key, return_rounds=True)
    if not enc["success"]:
        return enc

    dec = magma_decrypt_block(enc["result_block"], key, return_rounds=False)
    if not dec["success"]:
        return dec

    return {
        "success": True,
        "algorithm": "magma",
        "test_name": "ГОСТ Р 34.12-2015 A.2",
        "key": key,
        "plaintext": plaintext,
        "expected_cipher": expected_cipher,
        "actual_cipher": enc["result_block"],
        "decrypted": dec["result_block"],
        "test_passed": enc["result_block"] == expected_cipher and dec["result_block"] == plaintext,
        "rounds": enc["rounds"],
        "round_keys": enc["round_keys"]
    }


def main():
    print("=" * 80)
    print("ШИФР МАГМА (ГОСТ Р 34.12-2015)")
    print("СЕТЬ ФЕЙСТЕЛЯ / ТАБЛИЦА РАУНДОВ")
    print("=" * 80)

    while True:
        print("\n" + "=" * 80)
        print("Выберите действие:")
        print("1 - Зашифровать 64-битный блок")
        print("2 - Расшифровать 64-битный блок")
        print("3 - Тест ГОСТ (A.2)")
        print("0 - Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == '0':
            print("\nДо свидания!")
            break

        elif choice == '1':
            block = input("Введите открытый текст (16 HEX): ").strip()
            key = input("Введите ключ (64 HEX): ").strip()
            show_rounds = input("Показать таблицу Фейстеля? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')

            result = magma_encrypt_block(block, key, return_rounds=show_rounds)

            if not result["success"]:
                print(f"\nОшибка: {result['error']}")
                continue

            print("\n" + "=" * 80)
            print("РЕЗУЛЬТАТ ШИФРОВАНИЯ")
            print("=" * 80)
            print(f"Открытый текст:      {result['input_block']}")
            print(f"Ключ:                {result['key']}")
            print(f"Зашифрованный текст: {result['result_block']}")
            print("=" * 80)

            if show_rounds:
                print("\nТАБЛИЦА ФЕЙСТЕЛЯ:")
                print(format_feistel_table(result["rounds"]))

        elif choice == '2':
            block = input("Введите шифртекст (16 HEX): ").strip()
            key = input("Введите ключ (64 HEX): ").strip()
            show_rounds = input("Показать таблицу Фейстеля? (y/n): ").strip().lower() in ('y', 'yes', 'д', 'да')

            result = magma_decrypt_block(block, key, return_rounds=show_rounds)

            if not result["success"]:
                print(f"\nОшибка: {result['error']}")
                continue

            print("\n" + "=" * 80)
            print("РЕЗУЛЬТАТ РАСШИФРОВАНИЯ")
            print("=" * 80)
            print(f"Шифртекст:           {result['input_block']}")
            print(f"Ключ:                {result['key']}")
            print(f"Расшифрованный текст:{result['result_block']}")
            print("=" * 80)

            if show_rounds:
                print("\nТАБЛИЦА ФЕЙСТЕЛЯ:")
                print(format_feistel_table(result["rounds"]))

        elif choice == '3':
            test = test_gost_example()

            if not test["success"]:
                print(f"\nОшибка теста: {test.get('error', 'неизвестная ошибка')}")
                continue

            print("\n" + "=" * 80)
            print("ТЕСТ ГОСТ Р 34.12-2015 A.2")
            print("=" * 80)
            print(f"Ключ:              {test['key']}")
            print(f"Открытый текст:    {test['plaintext']}")
            print(f"Ожидаемый шифртекст: {test['expected_cipher']}")
            print(f"Фактический шифртекст:{test['actual_cipher']}")
            print(f"Расшифровка:       {test['decrypted']}")
            print(f"Статус:            {'УСПЕХ' if test['test_passed'] else 'ОШИБКА'}")
            print("=" * 80)

        else:
            print("\nНеверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()