from Ascon.Models.AttackKey import AttackKey
from Ascon.Models.AttackTarget import AttackTarget
from Common.Models.FileType import FileType
from Common.Models.ParameterDefinition import ParameterDefinition
from Common.Models.PathType import PathType
from Configuration.Constants import ALIGNMENT_SHM_NAME_DATA, ALIGNMENT_SHM_NAME_TRACES, ASCON_ATTACKED_BITS, \
    ASCON_NONCE_BITS, KEY_NAME, PLAIN_TEXT_NAME, NONCE_NAME
from Configuration.Models.Attack.AsconAttackConfigModel import AsconAttackConfigModel
from Configuration.Models.Attack.GenericAttackConfigModel import GenericAttackConfigModel
from Configuration.Models.Extractors.AsconExtractorConfigModel import AsconExtractorConfigModel
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

# Attacker configuration

# IO
ASCON_ATTACK_TARGET_PATH: str = '/home/shravani-s-p/Downloads/chipwhisperer/traces/ASCON_cw_ref_200000_20260523_153748.trs'
# Used only if input is npy
ASCON_ATTACK_DATA_PATH: str = ''

# ASCON Attack
ASCON_ATTACK_BITS_COUNT: int = 1 # How many bits of output to attack in one iteration
ASCON_USE_PREVIOUS_RESULTS: bool = False # Use hamming weight of previous bit results during the attack

# Attack features
ASCON_USE_AVERAGER: bool = False  # Average trace samples with identical input
ASCON_USE_INCREMENTAL_CORRELATION: bool = True
ASCON_USE_PREDICTION_CACHE: bool = True # Cache computed predictions (not recommended when attack_bits > 1)

# Attack locality
ASCON_TRACE_START_INDEX: int = 100000 # First fixed-key trace in the TRS file
ASCON_TRACE_COUNT: int | None = 15000 # Number of fixed-key traces to attack
ASCON_SAMPLE_START: int = 0
ASCON_SAMPLE_END: int = 896
ASCON_ATTACK_LENGTH: int = 896
ASCON_ATTACK_STEP: int = 896

# Attack success
ASCON_MIN_CORRELATION: float = 0 # Minimum correlation to accept the attack as successful
# Minimum correlation difference between the first two candidates to consider attack successful
ASCON_CORRELATION_DIFFERENCE: float = 0
ASCON_USE_CORRECT_KEY: bool = False # If you want to use the correct key in the attack

# Automatic alignment
ASCON_AUTOMATICALLY_UPDATE_ALIGNMENT_ON: int = 0 # Use 0 to disable automatic update, use already aligned traces in src
ASCON_ALIGNMENT_INTERVAL_LENGTH: int = 15000 # Length used during alignments
ASCON_ALIGNMENT_INTERMEDIATE_TYPE: FileType = FileType.NPY
ASCON_ALIGNMENT_PROCESS_COUNT: int = 64 # Process count to use during automatic alignment
ASCON_ALIGNMENT_MAX_SHIFT: int = 7500  # Maximum shift of trace samples allowed in automatic alignment
ASCON_ALIGNMENT_THRESHOLD: float = 0.55 # Filter traces with correlation lower than the threshold
ASCON_ALIGNMENT_REFERENCE_INDEX: int = 0 # Index of the trace to use as a reference for alignment

# Advanced alignment
ASCON_ADVANCED_ALIGNMENT_LENGTH: int = 0 # 0 to not use advanced alignment
# Use absolute value of samples during internal resampling, may help with alignment
ASCON_ADVANCED_ALIGNMENT_USE_ABS: bool = False

# Extractor
ASCON_ATTACK_KEY: AttackKey = AttackKey.X1 # Select if attack key X1 or X2 or BOTH
ATTACK_Y4: bool = True # Choose if to use Y4 or Y0 when attacking X1
ASCON_ATTACK_SPECIFIC_STAGE: int = -1 # Attack only stage on a specific index -1 to attack all
# To continue the attack on X2 where X1 have not run simultaneously (use prev key value as binary string)
ASCON_FIX_EXTRACTED_KEY_X1: str = ''
ASCON_STOP_ON_FIRST: bool = False # Stop on first find of a correct key

# Graph
ASCON_SHOW_GRAPH_EVERY_ATTACK: bool = False
ASCON_SHOW_GRAPH_ATTACK_SUCCESSFUL: bool = True
ASCON_SHOW_INTERACTIVE_GRAPH: bool = False
ASCON_EVOLUTION_STEP: int = 100 # How many steps between values in a graph

# Log
ASCON_LOG_FOLDER_PATH: str = '/home/shravani-s-p/Downloads/CPA-Framework/Ascon/Log/'
ASCON_LOG_RESAMPLER_USED: bool = True # Include in logs resampling information
ASCON_LOG_SUCCESS_ATTEMPTS: bool = True
ASCON_LOG_INCLUDE_GRAPHS: bool = True
ASCON_PRINT_LOG: bool = True
# When the trace count is lower than this number, log warning (too many discarded traces) - 0 to not warn the user
# Only functional when automatic alignment with a threshold used
ASCON_WARNING_TRACES_BELOW: int = 25000

ASCON_KEY_BITS_COUNT: int = ASCON_ATTACKED_BITS * ASCON_ATTACK_BITS_COUNT  # Number of key bits attacked in one stage
ASCON_DATA_BITS_COUNT: int = ASCON_NONCE_BITS * ASCON_ATTACK_BITS_COUNT + ASCON_KEY_BITS_COUNT # Number of nonce bits

# Data location
ASCON_DATA_PARAMETERS: ParameterWrapper = ParameterWrapper([
    ParameterDefinition(KEY_NAME, 16),
    ParameterDefinition(PLAIN_TEXT_NAME, 16),
    ParameterDefinition(NONCE_NAME, 16),
])

# Check configuration
if not ASCON_LOG_SUCCESS_ATTEMPTS:
    assert not ASCON_LOG_INCLUDE_GRAPHS, 'To enable graph logging, enable logging in general (LOG_SUCCESS_ATTEMPTS)'
if not ASCON_SHOW_GRAPH_ATTACK_SUCCESSFUL:
    assert not ASCON_LOG_INCLUDE_GRAPHS, 'To enable graph logging, enable graph rendering after successful attack'


def _generate_ascon_attack_config():
    loader_config = TraceLoaderConfigModel(ASCON_ATTACK_TARGET_PATH, ASCON_ATTACK_DATA_PATH)
    aa_config: AutomaticAlignmentConfigModel | None = None
    if ASCON_AUTOMATICALLY_UPDATE_ALIGNMENT_ON > 0:
        output_trace_length = ASCON_ATTACK_LENGTH + (ASCON_AUTOMATICALLY_UPDATE_ALIGNMENT_ON - 1) * ASCON_ATTACK_STEP
        output_trace_count = calculate_config_length_interval(0, ASCON_TRACE_COUNT)
        writer_config = TraceWriterConfigModel(loader_config, PathType.Alignment, ASCON_ALIGNMENT_INTERMEDIATE_TYPE,
                                               '', output_trace_length, output_trace_count)
        parallel_config = ParallelWriterConfigModel(writer_config, ASCON_ALIGNMENT_PROCESS_COUNT, ALIGNMENT_SHM_NAME_DATA,
                                                    ALIGNMENT_SHM_NAME_TRACES)
        alignment_config = AlignmentConfigModel(
            parallel_config, ASCON_ALIGNMENT_MAX_SHIFT, ASCON_ADVANCED_ALIGNMENT_LENGTH,
            ASCON_ADVANCED_ALIGNMENT_USE_ABS, ASCON_ALIGNMENT_THRESHOLD, ASCON_ALIGNMENT_REFERENCE_INDEX
        )
        intermediate_data_path, intermediate_traces_path = get_alignment_output_paths(
            ASCON_ATTACK_TARGET_PATH, ASCON_ALIGNMENT_INTERMEDIATE_TYPE
        )
        loader_config = TraceLoaderConfigModel(
            intermediate_traces_path, intermediate_data_path
        )
        aa_config = AutomaticAlignmentConfigModel(
            alignment_config, ASCON_SAMPLE_START, ASCON_ATTACK_LENGTH, ASCON_ATTACK_STEP, ASCON_SAMPLE_END,
            ASCON_AUTOMATICALLY_UPDATE_ALIGNMENT_ON, ASCON_ALIGNMENT_INTERVAL_LENGTH
        )
    if ASCON_ATTACK_KEY != AttackKey.X2:
        initial_attack_target: AttackTarget = AttackTarget.Y4 if ATTACK_Y4 else AttackTarget.Y0
    else:
        initial_attack_target: AttackTarget = AttackTarget.Y1
    generic_attack_config = GenericAttackConfigModel(
            loader_config, ASCON_EVOLUTION_STEP, ASCON_KEY_BITS_COUNT, ASCON_ATTACK_LENGTH,
            ASCON_MIN_CORRELATION, ASCON_CORRELATION_DIFFERENCE, ASCON_SHOW_GRAPH_EVERY_ATTACK,
            ASCON_SHOW_GRAPH_ATTACK_SUCCESSFUL, ASCON_TRACE_COUNT, ASCON_USE_AVERAGER, ASCON_USE_INCREMENTAL_CORRELATION,
            aa_config, ASCON_SHOW_INTERACTIVE_GRAPH, ASCON_USE_PREDICTION_CACHE, ASCON_DATA_BITS_COUNT,
            ASCON_TRACE_START_INDEX
        )
    return AsconAttackConfigModel(
        generic_attack_config, initial_attack_target, ASCON_DATA_PARAMETERS, ASCON_USE_PREVIOUS_RESULTS,
        ASCON_FIX_EXTRACTED_KEY_X1, ASCON_ATTACK_BITS_COUNT, ASCON_USE_CORRECT_KEY
    )


ASCON_ATTACK_CONFIGURATION: AsconAttackConfigModel = _generate_ascon_attack_config()


def _get_extractor_config():
    logger_config = LoggerConfigModel(
        ASCON_LOG_SUCCESS_ATTEMPTS, ASCON_LOG_FOLDER_PATH, ASCON_LOG_RESAMPLER_USED, ASCON_LOG_INCLUDE_GRAPHS,
        ASCON_PRINT_LOG
    )
    generic_extractor_config = GenericExtractorConfigModel(
        logger_config, ASCON_SAMPLE_START, ASCON_ATTACK_LENGTH, ASCON_ATTACK_STEP, ASCON_SAMPLE_END,
        ASCON_STOP_ON_FIRST, ASCON_ATTACK_SPECIFIC_STAGE, ASCON_WARNING_TRACES_BELOW
    )
    return AsconExtractorConfigModel(ASCON_ATTACK_CONFIGURATION, generic_extractor_config, ASCON_ATTACK_KEY)


ASCON_EXTRACTOR_CONFIG: AsconExtractorConfigModel = _get_extractor_config()
