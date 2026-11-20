from Common.Models.FileType import FileType
from Common.Models.PathType import PathType
from Configuration.Constants import ALIGNMENT_SHM_NAME_DATA, ALIGNMENT_SHM_NAME_TRACES
from Configuration.Models.Tools.AlignmentConfigModel import AlignmentConfigModel
from Configuration.Models.Traces.ParallelWriterConfigModel import ParallelWriterConfigModel
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel
from Configuration.Models.Traces.TraceWriterConfigModel import TraceWriterConfigModel
from Helpers.IntervalHelpers import calculate_config_length_interval

# Alignment Direct Start Configuration - Applied only if the alignment module is started directly

# IO
ALIGNMENT_TARGET_PATH: str = '/media/xmann/Disk/Traces/Test/all_traces2_conv_traces.npy'
# Used only if input is NPY v
ALIGNMENT_DATA_PATH : str = ''
ALIGNMENT_OUTPUT_FOLDER_PATH: str = '' # Empty to use the same input folder
ALIGNMENT_OUTPUT_TYPE: FileType = FileType.NPY
ALIGNMENT_INCLUDE_CUT_OUTPUT_NAME: bool = False # Show cut of traces in an output path
ALIGNMENT_OUTPUT_COMPRESSED: bool = False # Only used when an output type is NPZ
ALIGNMENT_DRY_RUN: bool = False  # If True, traces are not saved but only log alignment
ALIGNMENT_LOG_ENABLE: bool = True

# Alignment interval
ALIGNMENT_SAMPLE_START: int | None = 0 # None/0 to use the start of trace as a cut interval
ALIGNMENT_SAMPLE_END: int | None = 120000 # None to use the end of trace as a cut interval
ALIGNMENT_TRACE_COUNT: int | None = None # Trace count used in alignment, None to use all
ALIGNMENT_START: int = 10000  # Start of the segment to align from the reference trace
ALIGNMENT_END: int = 110000  # End of the segment to align from reference trace

# General
ALIGNMENT_REFERENCE_SAMPLE_INDEX: int = 0
ALIGNMENT_THRESHOLD: float = 0.7  # The minimum correlation to consider the alignment successful (other traces discarded)
ALIGNMENT_MAX_SHIFT: int = 10000  # The maximum shift allowed.
ADVANCED_ALIGNMENT_RESAMPLING_LENGTH: int = 0 # 0 to not use advanced alignment (Use non-resampled input)
# Use absolute value of samples during internal resampling, may help with alignment
ADVANCED_ALIGNMENT_USE_ABS: bool = True

# Graph
ALIGNMENT_SHOW_GRAPH: bool = False # Show alignment graph, can be used only outside DRY_RUN
ALIGNMENT_GRAPH_TRACE_COUNT: int = 2 # Number of traces to show in the graph not including reference trace
ALIGNMENT_GRAPH_LENGTH: int = 7000 # Number of samples to draw in the graph

# Multithreading
ALIGNMENT_PROCESS_COUNT: int = 32

def _generate_alignment_config() -> AlignmentConfigModel:
    loader_config = TraceLoaderConfigModel(ALIGNMENT_TARGET_PATH, ALIGNMENT_DATA_PATH)
    output_trace_length = calculate_config_length_interval(ALIGNMENT_SAMPLE_START, ALIGNMENT_SAMPLE_END)
    output_trace_count = calculate_config_length_interval(0, ALIGNMENT_TRACE_COUNT)
    writer_config = TraceWriterConfigModel(
        loader_config, PathType.Alignment, ALIGNMENT_OUTPUT_TYPE, ALIGNMENT_OUTPUT_FOLDER_PATH, output_trace_length,
        output_trace_count, output_compressed=ALIGNMENT_OUTPUT_COMPRESSED
    )
    parallel_config = ParallelWriterConfigModel(writer_config, ALIGNMENT_PROCESS_COUNT, ALIGNMENT_SHM_NAME_DATA,
                                                ALIGNMENT_SHM_NAME_TRACES)

    return AlignmentConfigModel(
        parallel_config, ALIGNMENT_MAX_SHIFT, ADVANCED_ALIGNMENT_RESAMPLING_LENGTH, ADVANCED_ALIGNMENT_USE_ABS,
        ALIGNMENT_THRESHOLD, ALIGNMENT_REFERENCE_SAMPLE_INDEX, ALIGNMENT_LOG_ENABLE, ALIGNMENT_SHOW_GRAPH,
        ALIGNMENT_GRAPH_TRACE_COUNT, ALIGNMENT_GRAPH_LENGTH, ALIGNMENT_DRY_RUN, ALIGNMENT_INCLUDE_CUT_OUTPUT_NAME
    )

ALIGNMENT_CONFIG: AlignmentConfigModel = _generate_alignment_config()
