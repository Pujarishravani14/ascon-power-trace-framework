from Common.Models.FileType import FileType
from Common.Models.ParameterDefinition import ParameterDefinition
from Common.Models.PathType import PathType
from Configuration.Constants import ALIGNMENT_SHM_NAME_DATA, ALIGNMENT_SHM_NAME_TRACES, KEY_NAME, PLAIN_TEXT_NAME
from Configuration.Models.Attack.AesAttackConfigModel import AesAttackConfigModel
from Configuration.Models.Attack.GenericAttackConfigModel import GenericAttackConfigModel
from Configuration.Models.Extractors.AesExtractorConfigModel import AesExtractorConfigModel
from Configuration.Models.Extractors.GenericExtractorConfigModel import GenericExtractorConfigModel
from Configuration.Models.Other.LoggerConfigModel import LoggerConfigModel
from Configuration.Models.Tools.AlignmentConfigModel import AlignmentConfigModel
from Configuration.Models.Tools.AutomaticAlignmentConfigModel import AutomaticAlignmentConfigModel
from Configuration.Models.Traces.ParallelWriterConfigModel import ParallelWriterConfigModel
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel
from Configuration.Models.Traces.TraceWriterConfigModel import TraceWriterConfigModel
from Helpers.FileNamingHelper import get_alignment_output_paths
from Helpers.IntervalHelpers import calculate_config_length_interval
from Helpers.ParameterWrapper import ParameterWrapper

#IO
AES_ATTACK_TARGET_PATH: str = '/media/xmann/Disk/Traces_AES/all_traces_2_traces.npy'
# Used only if input is npy (if empty, automatically replace _traces with _data and use as a data path)
AES_ATTACK_DATA_PATH: str = ''

# AES attack
AES_ATTACKED_BITS_COUNT: int = 8 # Number of key bits attacked in one stage

# Attack features
AES_USE_AVERAGER: bool = False # Average trace samples with identical input
AES_USE_INCREMENTAL_CORRELATION: bool = True
AES_USE_PREDICTION_CACHE: bool = True # Cache computed predictions (Always recommended in AES)

# Attack locality
AES_SAMPLE_START: int = 19630000
AES_SAMPLE_END: int = -1 # End of the attack, -1 (negative) to use maximum amount
AES_TRACE_COUNT: int | None = None  # Number of traces to attack, None to use all
AES_ATTACK_LENGTH: int = 10000 # Sample length of one attack iteration (must be larger than 0)
AES_ATTACK_STEP: int = 5000 # Attack step length (>attack_length - overlap attacks; <attack_length - skip interval)

# Attack success
AES_MIN_CORRELATION: float = 0.2 # Minimum correlation to accept the attack as successful
# Minimum correlation difference between the first two candidates to consider attack successful
AES_CORRELATION_DIFFERENCE: float = 0.05
AES_USE_CORRECT_KEY: bool = True # If you want to use the correct key in the attack

# Automatic Alignment
AES_AUTOMATICALLY_UPDATE_ALIGNMENT_ON: int = 1  # Use 0 to disable automatic update, use already aligned traces in src
AES_ALIGNMENT_INTERVAL_LENGTH: int = 50000 # Length used during alignments
AES_ALIGNMENT_INTERMEDIATE_TYPE: FileType = FileType.NPY
AES_ALIGNMENT_PROCESS_COUNT: int = 64 # Process count to use during automatic alignment
AES_ALIGNMENT_MAX_SHIFT: int = 30000 # Maximum shift of trace samples allowed in automatic alignment
AES_ALIGNMENT_THRESHOLD: float = 0.4 # Filter traces with correlation lower than the threshold
AES_ALIGNMENT_REFERENCE_INDEX: int = 0 # Index of the trace to use as a reference for alignment

# Advanced alignment
AES_ADVANCED_ALIGNMENT_LENGTH: int = 100 # 0 to not use advanced alignment (Use non-resampled input)
# Use absolute value of samples during internal resampling, may help with alignment
AES_ADVANCED_ALIGNMENT_USE_ABS: bool = False

# Extractor
AES_ATTACK_STAGE: int = 7 # Attack byte on a specific index (-1) to attack all bytes
AES_STOP_ON_FIRST: bool = False

# Graph generation
AES_SHOW_GRAPH_EVERY_ATTACK: bool = True
AES_SHOW_INTERACTIVE_GRAPH: bool = True
AES_SHOW_GRAPH_ATTACK_SUCCESSFUL : bool = True
AES_EVOLUTION_STEP: int = 50  # How many steps between values in a graph

# Log
AES_LOG_FOLDER_PATH: str = '/home/xmann/CPA-Framework/Aes/Log/'
AES_LOG_RESAMPLER_USED: bool = True # Include in logs current resampling information
AES_LOG_SUCCESS_ATTEMPTS: bool = True
AES_LOG_INCLUDE_GRAPHS: bool = True
AES_PRINT_LOG: bool = True
# When the trace count is lower than this number, log warning (too many discarded traces) - 0 to not warn the user
# Only functional when automatic alignment with a threshold used
AES_WARNING_TRACES_BELOW: int = 600

# Data location
AES_DATA_PARAMETERS: ParameterWrapper = ParameterWrapper([
    ParameterDefinition(KEY_NAME, 16),
    ParameterDefinition(PLAIN_TEXT_NAME, 16)
])

# Prepare config objects

def _generate_aes_attack_config():
    loader_config = TraceLoaderConfigModel(AES_ATTACK_TARGET_PATH, AES_ATTACK_DATA_PATH)
    aa_config: AutomaticAlignmentConfigModel | None = None
    if AES_AUTOMATICALLY_UPDATE_ALIGNMENT_ON > 0:
        output_trace_length = AES_ATTACK_LENGTH + (AES_AUTOMATICALLY_UPDATE_ALIGNMENT_ON - 1) * AES_ATTACK_STEP
        output_trace_count = calculate_config_length_interval(0, AES_TRACE_COUNT)
        writer_config = TraceWriterConfigModel(
            loader_config, PathType.Alignment, AES_ALIGNMENT_INTERMEDIATE_TYPE, '', output_trace_length,
            output_trace_count
        )
        parallel_config = ParallelWriterConfigModel(
            writer_config, AES_ALIGNMENT_PROCESS_COUNT, ALIGNMENT_SHM_NAME_DATA, ALIGNMENT_SHM_NAME_TRACES
        )
        alignment_config = AlignmentConfigModel(
            parallel_config, AES_ALIGNMENT_MAX_SHIFT, AES_ADVANCED_ALIGNMENT_LENGTH,
            AES_ADVANCED_ALIGNMENT_USE_ABS, AES_ALIGNMENT_THRESHOLD, AES_ALIGNMENT_REFERENCE_INDEX
        )
        intermediate_data_path, intermediate_traces_path = get_alignment_output_paths(
            AES_ATTACK_TARGET_PATH, AES_ALIGNMENT_INTERMEDIATE_TYPE
        )
        loader_config = TraceLoaderConfigModel(
            intermediate_traces_path, intermediate_data_path
        )
        aa_config = AutomaticAlignmentConfigModel(
            alignment_config, AES_SAMPLE_START, AES_ATTACK_LENGTH, AES_ATTACK_STEP, AES_SAMPLE_END,
            AES_AUTOMATICALLY_UPDATE_ALIGNMENT_ON, AES_ALIGNMENT_INTERVAL_LENGTH
        )
    generic_attack_model = GenericAttackConfigModel(
            loader_config, AES_EVOLUTION_STEP, AES_ATTACKED_BITS_COUNT, AES_ATTACK_LENGTH, AES_MIN_CORRELATION,
            AES_CORRELATION_DIFFERENCE, AES_SHOW_GRAPH_EVERY_ATTACK, AES_SHOW_GRAPH_ATTACK_SUCCESSFUL, AES_TRACE_COUNT,
            AES_USE_AVERAGER, AES_USE_INCREMENTAL_CORRELATION, aa_config, AES_SHOW_INTERACTIVE_GRAPH,
            AES_USE_PREDICTION_CACHE, AES_ATTACKED_BITS_COUNT
        )
    return AesAttackConfigModel(
        generic_attack_model, AES_DATA_PARAMETERS, AES_USE_CORRECT_KEY
    )

AES_ATTACK_CONFIGURATION: AesAttackConfigModel = _generate_aes_attack_config()

def _get_extractor_config():
    logger_config = LoggerConfigModel(
        AES_LOG_SUCCESS_ATTEMPTS, AES_LOG_FOLDER_PATH, AES_LOG_RESAMPLER_USED, AES_LOG_INCLUDE_GRAPHS, AES_PRINT_LOG
    )
    generic_extractor_config = GenericExtractorConfigModel(
        logger_config, AES_SAMPLE_START, AES_ATTACK_LENGTH, AES_ATTACK_STEP, AES_SAMPLE_END, AES_STOP_ON_FIRST,
        AES_ATTACK_STAGE, AES_WARNING_TRACES_BELOW
    )
    return AesExtractorConfigModel(AES_ATTACK_CONFIGURATION, generic_extractor_config)


AES_EXTRACTOR_CONFIG: AesExtractorConfigModel = _get_extractor_config()
