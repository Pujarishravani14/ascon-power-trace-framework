import numpy as np
from dataclasses import dataclass
from Configuration.Models.Tools.AutomaticAlignmentConfigModel import AutomaticAlignmentConfigModel
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel


@dataclass
class GenericAttackConfigModel:
    loader_config: TraceLoaderConfigModel
    evolution_step: int
    attacked_key_bits: int
    attack_length: int
    min_correlation: float = 0
    min_correlation_difference: float = 0
    always_show_graph: bool = False
    show_graph_attack_successful: bool = True
    attack_trace_count: int | None = None
    use_averager: bool = False
    use_incremental_correlation: bool = False
    aa_config: AutomaticAlignmentConfigModel = None
    show_interactive_graph: bool = False
    use_prediction_cache: bool = True
    data_bit_length: int = 8
    prediction_dtype = np.dtype(np.uint8)
    trace_start_index: int = 0
