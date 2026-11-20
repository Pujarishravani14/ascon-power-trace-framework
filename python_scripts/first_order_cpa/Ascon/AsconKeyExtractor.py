import pandas as pd
import numpy as np
from typing import Tuple
from numpy.typing import NDArray
from Ascon.AsconAttacker import AsconAttacker
from Ascon.AsconMaps import attack_stages_map
from Ascon.Models.AttackTarget import AttackTarget
from Ascon.Models.AttackKey import AttackKey
from Common.Generics.GenericExtractor import GenericExtractor
from Common.Models.AttackResultWrapper import AttackResultWrapper
from Configuration.Constants import ASCON_KEY_WITH_CONFIDENCE_DTYPE, KEY_BIT_NAME, ASCON_ROUND_CONSTANT_BITS
from Configuration.Models.Extractors.AsconExtractorConfigModel import AsconExtractorConfigModel
from Helpers.NumpyHelper import convert_to_hex_string


class AsconKeyExtractor(GenericExtractor):

    def __init__(self, config: AsconExtractorConfigModel):
        self.attack_target: AttackTarget = config.attack_config.initial_attack_target
        self.attack_key: AttackKey = config.attack_key
        self.attack_bit_count: int = config.attack_config.attack_bits_count
        self.ascon_attacker: AsconAttacker = AsconAttacker(config.attack_config)
        super().__init__(self.ascon_attacker, config.extractor_config)

    def get_log_message(self, attack_stage: int, attack_sample_start: int, attack_sample_end: int,
                        correlation: float) -> str:
        return (f'Attack stage: {attack_stage}, sample: ({attack_sample_start} - {attack_sample_end}),'
                f' attacked bits: {self.attack_bit_count}, resampling: {self.get_current_resampling()},'
                f' attack_target = {self.attack_target.name}, correlation: {correlation}\n')

    def perform_result_operation(self, result: AttackResultWrapper, attack_sample_start: int,
                                 attack_sample_end: int, attack_stage: int) -> None:
        return # Ascon does not need to update key guess, it uses one from the attacker

    def _print_results(self) -> None:
        if self.attack_target == AttackTarget.Y1:
            extracted_key: ASCON_KEY_WITH_CONFIDENCE_DTYPE = self.ascon_attacker.extracted_key_x2
        else:
            extracted_key = self.ascon_attacker.extracted_key_x1
        pd.set_option('display.max_rows', None)
        print(pd.DataFrame(extracted_key))
        pd.reset_option('display.max_rows')
        key_bytes = np.packbits(extracted_key[KEY_BIT_NAME])
        print(f"Extracted key {self.attack_key.name} as byte array:", key_bytes)
        print(f"Extracted key {self.attack_key.name} as hex value:", convert_to_hex_string(key_bytes))

    def run_on_target(self) -> None:
        stage_count: int = attack_stages_map[self.attack_target]
        self.extract_key(stage_count, self.attack_bit_count)
        self._print_results()

    def remove_first_round_constant(self) -> None:
        for key_bit_index in ASCON_ROUND_CONSTANT_BITS:
            self.ascon_attacker.extracted_key_x2[key_bit_index][KEY_BIT_NAME] ^= 1

    def run(self) -> Tuple[NDArray | None, NDArray | None]:
        self.run_on_target()
        if self.attack_key == AttackKey.BOTH:
            self.attack_target = AttackTarget.Y1
            self.ascon_attacker.delete_cache()
            self.run_on_target()
            self.remove_first_round_constant()
            return self.ascon_attacker.extracted_key_x1, self.ascon_attacker.extracted_key_x2
        if self.attack_target == AttackTarget.Y1:
            self.remove_first_round_constant()
            return None, self.ascon_attacker.extracted_key_x2
        return self.ascon_attacker.extracted_key_x1 , None


if __name__ == '__main__':
    from Configuration.AsconConfiguration import ASCON_EXTRACTOR_CONFIG
    key_extractor: AsconKeyExtractor = AsconKeyExtractor(ASCON_EXTRACTOR_CONFIG)
    extracted_key_x1 , extracted_key_x2 = key_extractor.run()
