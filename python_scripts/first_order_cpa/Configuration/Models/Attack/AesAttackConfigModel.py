from dataclasses import dataclass
from Configuration.Models.Attack.GenericAttackConfigModel import GenericAttackConfigModel
from Helpers.ParameterWrapper import ParameterWrapper


@dataclass
class AesAttackConfigModel:
    attack_config: GenericAttackConfigModel
    data_parameters: ParameterWrapper
    use_correct_key: bool = True
