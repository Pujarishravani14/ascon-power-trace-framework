import numpy as np
from Common.Models.FileType import FileType
from Common.Models.ParameterDefinition import ParameterDefinition
from Configuration.Constants import KEY_NAME, PLAIN_TEXT_NAME, NONCE_NAME
from Configuration.Models.Traces.TraceGenConfigModel import TraceGenConfigModel
from Configuration.Models.Traces.TraceCreatorConfigModel import TraceCreatorConfigModel
from Helpers.ParameterWrapper import ParameterWrapper

# Leakage extraction difficulty
TRACE_GEN_RANDOM_DISTRIBUTION_MEAN: int = 0
TRACE_GEN_RANDOM_DISTRIBUTION_STD: int = 20
TRACE_GEN_LEAKAGE_AMPLIFICATION: int = 4
TRACE_GEN_RANDOM_SHIFT: int = 0
TRACE_GEN_VARIABLE_NOISE: int = 3

# Traces parameters
TRACE_GEN_KEY: list[int] = [0x80400C0600110000, 0x80400C0600220000]
TRACE_GEN_TRACE_GEN_COUNT: int = 2000 # Trace count that should be generated
TRACE_GEN_SAMPLE_COUNT: int = 10000 # Number of samples in the generated trace
TRACE_SAMPLE_CODING: np.dtype = np.dtype(np.int8)

# Leakage location
TRACE_GEN_LEAKAGE_POSITION: int = 5600 # Register which leakage should be simulated
TRACE_GEN_ATTACK_REGISTER: int = 4
TRACE_GEN_ATTACK_REGISTER_FROM: int = 58
TRACE_GEN_ATTACK_REGISTER_TO: int = 59

#IO
TRACE_GEN_OUTPUT_FOLDER: str = '/media/xmann/Disk/Traces/'
TRACE_GEN_OUTPUT_NAME: str = 'gen'
TRACE_GEN_OUTPUT_TYPE: FileType = FileType.TRS
TRACE_GEN_OUTPUT_COMPRESSED: bool = False

# Parameter Definition
TRACE_GEN_OUTPUT_PARAMETERS: ParameterWrapper = ParameterWrapper([
    ParameterDefinition(KEY_NAME, 16),
    ParameterDefinition(PLAIN_TEXT_NAME, 16),
    ParameterDefinition(NONCE_NAME, 16),
])


def get_trace_gen_config() -> TraceGenConfigModel:
    trace_creator_config = TraceCreatorConfigModel(
        TRACE_GEN_OUTPUT_NAME, TRACE_GEN_OUTPUT_FOLDER, TRACE_GEN_OUTPUT_TYPE, TRACE_GEN_OUTPUT_PARAMETERS,
        TRACE_GEN_TRACE_GEN_COUNT, 0, TRACE_GEN_SAMPLE_COUNT, TRACE_SAMPLE_CODING, TRACE_GEN_OUTPUT_COMPRESSED
    )
    return TraceGenConfigModel(
        trace_creator_config, TRACE_GEN_RANDOM_DISTRIBUTION_MEAN, TRACE_GEN_RANDOM_DISTRIBUTION_STD,
        TRACE_GEN_VARIABLE_NOISE, TRACE_GEN_LEAKAGE_POSITION, TRACE_GEN_RANDOM_SHIFT, TRACE_GEN_ATTACK_REGISTER,
        TRACE_GEN_ATTACK_REGISTER_FROM, TRACE_GEN_ATTACK_REGISTER_TO, TRACE_GEN_KEY, TRACE_GEN_LEAKAGE_AMPLIFICATION
    )

TRACE_GEN_CONFIG: TraceGenConfigModel = get_trace_gen_config()
