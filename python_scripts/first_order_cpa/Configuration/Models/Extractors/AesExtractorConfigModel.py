from dataclasses import dataclass
from Configuration.Models.Attack.AesAttackConfigModel import AesAttackConfigModel
from Configuration.Models.Extractors.GenericExtractorConfigModel import GenericExtractorConfigModel


@dataclass
class AesExtractorConfigModel:
    attack_config: AesAttackConfigModel
    extractor_config: GenericExtractorConfigModel

