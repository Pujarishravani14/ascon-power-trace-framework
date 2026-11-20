from dataclasses import dataclass
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel


@dataclass
class TvlaConfigModel:
    fixed_traces_config: TraceLoaderConfigModel
    random_traces_config: TraceLoaderConfigModel
    attack_order: int
    step_size: int
    show_graph_p_value: bool
    show_graph_t_value: bool
    p_threshold: float
    equal_variance: bool
    interactive_graph: bool
