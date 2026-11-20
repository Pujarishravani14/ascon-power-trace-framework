from dataclasses import dataclass
from Configuration.Models.Other.LoggerConfigModel import LoggerConfigModel


@dataclass
class GenericExtractorConfigModel:
    logger_config: LoggerConfigModel
    attack_start: int
    attack_length: int
    attack_step: int
    attack_end: int
    stop_on_first: bool
    attack_stage: int = -1
    warning_traces_below: int = 0
