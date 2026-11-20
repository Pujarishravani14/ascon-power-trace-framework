from dataclasses import dataclass

from Ascon.Models.AttackKey import AttackKey
from Configuration.Models.Attack.AsconAttackConfigModel import AsconAttackConfigModel
from Configuration.Models.Extractors.GenericExtractorConfigModel import GenericExtractorConfigModel


@dataclass
class AsconExtractorConfigModel:
    attack_config: AsconAttackConfigModel
    extractor_config: GenericExtractorConfigModel
    attack_key: AttackKey
