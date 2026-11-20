from dataclasses import dataclass
from Ascon.Models.AttackTarget import AttackTarget
from Configuration.Models.Attack.GenericAttackConfigModel import GenericAttackConfigModel
from Helpers.ParameterWrapper import ParameterWrapper


@dataclass
class AsconAttackConfigModel:
    attack_config: GenericAttackConfigModel
    initial_attack_target: AttackTarget
    data_parameters: ParameterWrapper
    use_prev_results: bool
    fix_key_x1: str = ''
    attack_bits_count: int = 1
    use_correct_key: bool = True
