import numpy as np
from tqdm import tqdm
from trsfile import Trace
from numpy.typing import NDArray
from Ascon.AsconMaps import attack_indexes_map, attack_shift_1_map, attack_shift_2_map, get_part_y0, get_part_y1, \
    get_part_y4
from Ascon.Models.AttackTarget import AttackTarget
from Common.Generics.GenericAttacker import GenericAttacker
from Common.Models.AttackResultWrapper import AttackResultWrapper
from Common.Models.FileType import FileType
from Configuration.Constants import ASCON_SECTION_BIT_SIZE, NONCE_NAME, KEY_BIT_NAME, CONFIDENCE_NAME, KEY_NAME, \
    ASCON_KEY_WITH_CONFIDENCE_DTYPE, START_NAME, END_NAME, ASCON_KEY_SIZE_BITS, NONCE_SECTION_LEN, \
    ASCON_FIRST_ROUND_CONSTANT, ASCON_ATTACKED_BITS
from Configuration.Models.Attack.AsconAttackConfigModel import AsconAttackConfigModel
from Helpers.GenericHelper import get_bit_on_index_jit
from numba import njit
from Helpers.NumpyHelper import convert_big_endian_bytes_to_numpy
from Helpers.ParameterWrapper import ParameterWrapper


class AsconAttacker(GenericAttacker):

    def __init__(self, config: AsconAttackConfigModel):
        # Init config
        self.attack_target: AttackTarget = config.initial_attack_target
        self.data_parameters: ParameterWrapper = config.data_parameters
        self.attack_bits_count: int = config.attack_bits_count
        self.use_prev_results: bool = config.use_prev_results
        self.use_correct_key: bool = config.use_correct_key
        super().__init__(config.attack_config)
        self.key: NDArray = self._initialize_key()
        if config.fix_key_x1 == '':
            if self.attack_target == AttackTarget.Y1:
                raise Exception('When attacking only the second key part, you must define the first key.')
            self.extracted_key_x1: NDArray = np.zeros(ASCON_SECTION_BIT_SIZE, dtype=ASCON_KEY_WITH_CONFIDENCE_DTYPE)
        else:
            self.extracted_key_x1: NDArray = np.array([(bool(int(bit)), 0, 0, 0) for bit in config.fix_key_x1],
                dtype=ASCON_KEY_WITH_CONFIDENCE_DTYPE)
        self.extracted_key_x2: NDArray = np.zeros(ASCON_SECTION_BIT_SIZE, dtype=ASCON_KEY_WITH_CONFIDENCE_DTYPE)
        self.attack_indexes: list[int] = []
        self.current_trace_index: int = 0

    @staticmethod
    def _get_trace_parameter(trace: Trace, parameter_name: str):
        try:
            return trace.parameters[parameter_name]
        except KeyError:
            return trace.parameters[parameter_name.lower()]

    def _initialize_key(self) -> NDArray:
        if not self.use_correct_key:
            return np.empty(0)
        elif self.input_type == FileType.TRS:
            trace = self.traceset[self.trace_start_index]
            key_bytes: bytes = bytes(self._get_trace_parameter(trace, KEY_NAME).value)
        else:
            key_bytes = bytes(self.data_parameters.get_parameter(self.data[0], KEY_NAME))
        key: NDArray = convert_big_endian_bytes_to_numpy(key_bytes)
        key[1] ^= ASCON_FIRST_ROUND_CONSTANT # Add the first round constant to the key
        return key

    def attack(self, attack_stage: int, sample_start: int, sample_end: int,
               graph_path: str = '') -> AttackResultWrapper:
        self.should_update_alignment(sample_start) # Performs automatic alignment if necessary
        attack_indexes: list[int] = attack_indexes_map.get(self.attack_target)
        assert attack_stage + self.attack_bits_count <= len(attack_indexes), 'Invalid attack stage'
        print(f'\nRunning analysis on {attack_stage} with interval {sample_start}-{sample_end}')
        self.attack_indexes = attack_indexes[attack_stage:attack_stage + self.attack_bits_count]
        correlation_results: NDArray = np.empty(0)
        for local_trace_index in tqdm(range(self.attack_trace_count)):
            self.current_trace_index = self.trace_start_index + local_trace_index
            nonce: int = self._calculate_nonce_number()
            predictions: NDArray = self._get_predictions_for_nonce(nonce)
            self.add_trace(nonce, local_trace_index, sample_start, sample_end, predictions)
            if self.is_index_graph_point(local_trace_index):
                correlation_results = self.update_evolution(local_trace_index)
        correct_key: int = self._get_correct_key()
        attack_result: AttackResultWrapper = self.evaluate_attack_stage(correlation_results, graph_path, correct_key)
        if attack_result.success:
            self._update_key_guess(attack_result.key, attack_result.correlation, sample_start, sample_end)
        return attack_result

    def _update_key_guess(self, current_key: int, correlation: float, sample_start: int, sample_end: int) -> None:
        key_mask: int = 1
        shift_1: int = attack_shift_1_map(self.attack_target)
        shift_2: int = attack_shift_2_map(self.attack_target)
        target_array: NDArray = self.extracted_key_x2 if self.attack_target == AttackTarget.Y1 else self.extracted_key_x1
        for attack_index in self.attack_indexes[::-1]: # Reverse order
            for shift in [0, shift_1, shift_2]:
                index: int = (attack_index + shift) % target_array.size
                if target_array[index][CONFIDENCE_NAME] < correlation:
                    target_array[index][KEY_BIT_NAME] = current_key & key_mask
                    target_array[index][CONFIDENCE_NAME] = correlation
                    target_array[index][START_NAME] = sample_start
                    target_array[index][END_NAME] = sample_end
                key_mask <<= 1

    def _get_correct_key(self) -> int:
        if not self.use_correct_key:
            return -1
        correct_key_part: int = 0
        shift_1: int = attack_shift_1_map(self.attack_target)
        shift_2: int = attack_shift_2_map(self.attack_target)
        key_part: int = int(self.key[1]) if self.attack_target == AttackTarget.Y1 else int(self.key[0])
        for index, attack_index in enumerate(self.attack_indexes):
            for shift in [shift_2, shift_1, 0]:
                correct_key_part += get_bit_on_index_jit(key_part, attack_index + shift, ASCON_KEY_SIZE_BITS)
                if shift != 0 or index + 1 != len(self.attack_indexes):
                    correct_key_part <<= 1
        return correct_key_part

    def _get_predictions_for_nonce(self, nonce_number: int) -> NDArray:
        if self.use_prediction_cache and nonce_number in self.observed_values:
            predictions: NDArray = self.predictions[nonce_number]
        else:
            predictions: NDArray = self._compute_predictions_for_nonce(
                nonce_number, self.attacked_key_max, self.attack_bits_count, self.attack_target)
        if not self.use_prev_results:
            hw: int = 0 # Do not add previous results
        elif self.attack_target != AttackTarget.Y1:
            hw = np.sum(self.extracted_key_x1[KEY_BIT_NAME])
        else:
            hw = np.sum(self.extracted_key_x2[KEY_BIT_NAME])
        return predictions + hw

    @staticmethod
    @njit
    def _compute_predictions_for_nonce(nonce_number: int, attack_key_max: int, attack_bits_count: int,
                                       attack_target: AttackTarget) -> NDArray:
        predictions: NDArray = np.zeros(attack_key_max, dtype='uint8')
        for key_guess in range(attack_key_max):
            result: int = 0
            current_key: int = key_guess
            current_data: int = nonce_number
            for current_attack_bit in range(attack_bits_count):
                if attack_target == AttackTarget.Y0:
                    bit: int = (get_part_y0(current_data, current_key & 1) ^
                                get_part_y0(current_data >> 3, (current_key >> 1) & 1) ^
                                get_part_y0(current_data >> 6, (current_key >> 2) & 1))
                elif attack_target == AttackTarget.Y1:
                    bit: int = (get_part_y1(current_data, current_key & 1) ^
                                get_part_y1(current_data >> 3, (current_key >> 1) & 1) ^
                                get_part_y1(current_data >> 6, (current_key >> 2) & 1))
                elif attack_target == AttackTarget.Y4:
                    bit: int = (get_part_y4(current_data, current_key & 1) ^
                                get_part_y4(current_data >> 3, (current_key >> 1) & 1) ^
                                get_part_y4(current_data >> 6, (current_key >> 2) & 1))
                else:
                    raise Exception('Unknown attack target')
                result += bit
                current_data >>= NONCE_SECTION_LEN
                current_key >>= ASCON_ATTACKED_BITS
            predictions[key_guess] = result
        return predictions

    def _get_current_nonces(self) -> NDArray[np.uint64]:
        if self.input_type == FileType.TRS:
            trace: Trace = self.traceset[self.current_trace_index]
            nonce_bytes: bytes = bytes(self._get_trace_parameter(trace, NONCE_NAME).value)
        else:
            nonce_bytes = bytes(self.data_parameters.get_parameter(self.data[self.current_trace_index], NONCE_NAME))
        return convert_big_endian_bytes_to_numpy(nonce_bytes)


    def _calculate_nonce_number(self) -> int:
        nonces: NDArray[np.uint64] = self._get_current_nonces()
        return self._calculate_nonce_number_jit(nonces, self.attack_indexes, self.extracted_key_x1[KEY_BIT_NAME],
                                                self.attack_target)

    @staticmethod
    @njit
    def _calculate_nonce_number_jit(nonces: NDArray[np.uint64], attack_indexes: list[int], key_x1: NDArray,
                                    attack_target: AttackTarget) -> int:
        nonce_number: int = 0
        nonce_x3 = int(nonces[0])
        nonce_x4 = int(nonces[1])
        shift_1: int = attack_shift_1_map(attack_target)
        shift_2: int = attack_shift_2_map(attack_target)
        for index, attack_index in enumerate(attack_indexes):
            for shift in [shift_2, shift_1, 0]:
                if attack_target == AttackTarget.Y1:
                    nonce_number += key_x1[(attack_index + shift) % key_x1.size]
                nonce_number <<= 1
                nonce_number += get_bit_on_index_jit(nonce_x3, attack_index + shift)
                nonce_number <<= 1
                nonce_number += get_bit_on_index_jit(nonce_x4, attack_index + shift)
                if shift != 0 or index + 1 != len(attack_indexes):
                    nonce_number <<= 1 # Move only if it is not last position in nonce number
        return nonce_number
