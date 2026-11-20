import numpy as np
from numpy.typing import NDArray

class Ascon:

    @staticmethod
    def add_round_key(internal_state: NDArray[np.uint64], current_round: int) -> None:
        internal_state[2] ^= (0xf0 - current_round * 0x10 + current_round * 0x1)

    @staticmethod
    def reverse_round_key(current_round: int, key: int) -> int:
        key ^= (0xf0 - current_round * 0x10 + current_round * 0x1)
        return key

    @staticmethod
    def compute_substitution(internal_state: NDArray[np.uint64]) -> None:
        internal_state[0] ^= internal_state[4]
        internal_state[4] ^= internal_state[3]
        internal_state[2] ^= internal_state[1]
        temp = [(internal_state[i] ^ 0xFFFFFFFFFFFFFFFF) & internal_state[(i + 1) % 5] for i in range(5)]
        for i in range(5):
            internal_state[i] ^= temp[(i + 1) % 5]
        internal_state[1] ^= internal_state[0]
        internal_state[0] ^= internal_state[4]
        internal_state[3] ^= internal_state[2]
        internal_state[2] ^= 0XFFFFFFFFFFFFFFFF

    @staticmethod
    def compute_diffusion_layer(internal_state: NDArray[np.uint64]) -> None:
        internal_state[0] ^= (Ascon.right_rotation(int(internal_state[0]), 19)
                              ^ Ascon.right_rotation(int(internal_state[0]), 28))
        internal_state[1] ^= (Ascon.right_rotation(int(internal_state[1]), 61)
                              ^ Ascon.right_rotation(int(internal_state[1]), 39))
        internal_state[2] ^= (Ascon.right_rotation(int(internal_state[2]), 1)
                              ^ Ascon.right_rotation(int(internal_state[2]), 6))
        internal_state[3] ^= (Ascon.right_rotation(int(internal_state[3]), 10)
                              ^ Ascon.right_rotation(int(internal_state[3]), 17))
        internal_state[4] ^= (Ascon.right_rotation(int(internal_state[4]), 7)
                              ^ Ascon.right_rotation(int(internal_state[4]), 41))

    @staticmethod
    def right_rotation(value: int, rotate_by: int, bit_size: int = 64) -> int:
        bit_size_mask =  ((1 << bit_size) - 1) # 0xFFFF...
        return (value >> rotate_by) | (value  << (bit_size - rotate_by)) & bit_size_mask
