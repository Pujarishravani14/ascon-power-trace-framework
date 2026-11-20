from Configuration.Models.Attack.TvlaConfigModel import TvlaConfigModel
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel

# IO Configuration
TVLA_RANDOM_FILE_PATH: str = '/media/xmann/SSD/Traces/tvla_alt_var_align_traces.npy'
TVLA_RANDOM_DATA_PATH: str = ''
TVLA_FIXED_FILE_PATH: str = '/media/xmann/SSD/Traces/tvla_alt_var_align_traces.npy'
TVLA_FIXED_DATA_PATH: str = ''

# Sample configuration
TVLA_SAMPLE_START: int = 0
TVLA_SAMPLE_END: int = -1 # End of the attack, -1 to use maximum amount
TVLA_TRACE_COUNT: int = -1 # -1 to use all traces
TVLA_ATTACK_ORDER: int = 1
TVLA_STEP_SIZE: int = 1000000

# Tvla configuration
TVLA_EQUAL_VARIANCE: bool = False # Establish if both datasets have equal variance

# Graph configuration
TVLA_SHOW_GRAPH_P_VALUE: bool = False
TVLA_SHOW_GRAPH_T_VALUE: bool = True
TVLA_INTERACTIVE_GRAPH: bool = False
TVLA_P_VALUE_THRESHOLD: float = 0.0001 # Threshold of p-value to highlight values lower/higher(complement) than it


def get_tvla_config() -> TvlaConfigModel:
    fixed_traces_config: TraceLoaderConfigModel = TraceLoaderConfigModel(TVLA_FIXED_FILE_PATH, TVLA_FIXED_DATA_PATH)
    random_traces_config: TraceLoaderConfigModel = TraceLoaderConfigModel(TVLA_RANDOM_FILE_PATH, TVLA_RANDOM_DATA_PATH)
    return TvlaConfigModel(fixed_traces_config, random_traces_config, TVLA_ATTACK_ORDER, TVLA_STEP_SIZE,
                           TVLA_SHOW_GRAPH_P_VALUE, TVLA_SHOW_GRAPH_T_VALUE, TVLA_P_VALUE_THRESHOLD,
                           TVLA_EQUAL_VARIANCE, TVLA_INTERACTIVE_GRAPH)


TVLA_CONFIG_MODEL: TvlaConfigModel = get_tvla_config()
