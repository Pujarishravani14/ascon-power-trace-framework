from Ascon.Models.AttackTarget import AttackTarget
from numba import njit

attack_stages_map: dict[AttackTarget, int] = {
    AttackTarget.Y0: 28,
    AttackTarget.Y1: 30,
    AttackTarget.Y4: 33,
}

attack_indexes_map: dict[AttackTarget, list[int]] = {
    AttackTarget.Y0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21, 22, 23,
                     24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],
    AttackTarget.Y1: [0, 1, 2, 7 ,8, 9, 14, 15, 16,
                     20, 21, 22, 28, 29, 30, 35, 36, 37, 42, 43, 44, 45, 49, 50, 51, 52, 56, 57, 58, 63],
    AttackTarget.Y4: [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 15, 16, 17, 18, 20,
                     21, 22, 24, 26, 34, 37, 42, 46, 50, 51, 52, 53, 54, 55, 56, 58],
}

@njit
def attack_shift_1_map(target: AttackTarget) -> int:
    if target == AttackTarget.Y0:
        return 45
    elif target == AttackTarget.Y1:
        return 3
    elif target == AttackTarget.Y4:
        return 57
    else:
        raise Exception('Unknown attack target')


@njit
def attack_shift_2_map(target: AttackTarget) -> int:
    if target == AttackTarget.Y0:
        return 36
    elif target == AttackTarget.Y1:
        return 25
    elif target == AttackTarget.Y4:
        return 23
    else:
        raise Exception('Unknown attack target')


@njit(cache=True)
def get_part_y0(data: int, key_guess: int) -> int:
    x4_bit: int = data & 1
    data >>= 1
    x3_bit: int = data & 1
    return (key_guess & x4_bit) ^ x3_bit


@njit(cache=True)
def get_part_y1(data: int, key_guess: int) -> int:
    x4_bit: int = data & 1
    data >>= 1
    x3_bit: int = data & 1
    data >>= 1
    x1_bit: int = data & 1 # Key from previous extractions (only used in Y1)
    return (x3_bit & key_guess ^ x3_bit & x1_bit ^ x3_bit) ^ x4_bit


@njit(cache=True)
def get_part_y4(data: int, key_guess: int) -> int:
    x4_bit: int = data & 1
    data >>= 1
    x3_bit: int = data & 1
    return ((key_guess & x4_bit) ^ x4_bit) ^ x3_bit
