import numpy as np
from Common.Models.FileType import FileType
from Common.Models.PathType import PathType
from Configuration.Constants import RESAMPLER_SHARE_MEMORY_NAME_DATA, RESAMPLER_SHARE_MEMORY_NAME_TRACES
from Configuration.Models.Traces.ParallelWriterConfigModel import ParallelWriterConfigModel
from Configuration.Models.Tools.ResamplerConfigModel import ResamplerConfigModel
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel
from Configuration.Models.Traces.TraceWriterConfigModel import TraceWriterConfigModel
from Helpers.IntervalHelpers import calculate_config_length_interval

# Resampler configuration

# Resampler IO
RESAMPLER_TARGET_PATH: str = '/data/backup/ascon_large_traces.npy'
RESAMPLER_DATA_PATH: str = '' # Used if input is NPY
RESAMPLER_OUTPUT_FOLDER_PATH: str = '' # Empty to use the same input folder
RESAMPLER_OUTPUT_TYPE: FileType = FileType.NPY
RESAMPLER_INCLUDE_CUT_OUTPUT_NAME: bool = True
RESAMPLER_OUTPUT_COMPRESSED: bool = False # Used only if output is NPZ

# Trace/sample selector
RESAMPLER_SAMPLE_START: int | None = 26000000 # Start of the resample window, None/0 to use samples from the beginning
RESAMPLER_SAMPLE_END: int | None = 31200000 # End of the resample window, None to use all remaining samples from the start
RESAMPLER_TRACE_START: int | None = 0  # Start of the traces, None/0 to use samples from the beginning
RESAMPLER_TRACE_END: int | None = None # End of the trace interval, None to use all remaining traces from the start

# Multithreading config
RESAMPLER_PROCESS_COUNT: int = 30 # Use 1 if the disk is HDD, otherwise Thread count

# Resampling config
RESAMPLER_WINDOW_SIZE: int = 10
RESAMPLER_OVERLAP: int = 5 # Number of samples to include in the following window from the previous one
RESAMPLER_ABS: bool = False
RESAMPLER_USE_FLOAT: bool = True


# Auto configuration
RESAMPLER_STEP: int = RESAMPLER_WINDOW_SIZE - RESAMPLER_OVERLAP

def _generate_resampler_config() -> ResamplerConfigModel:
    output_sample_coding: np.dtype = np.dtype(np.float32) if RESAMPLER_USE_FLOAT else None
    trace_length = calculate_config_length_interval(RESAMPLER_SAMPLE_START, RESAMPLER_SAMPLE_END)
    trace_count = calculate_config_length_interval(RESAMPLER_TRACE_START, RESAMPLER_TRACE_END)
    loader_config = TraceLoaderConfigModel(RESAMPLER_TARGET_PATH, RESAMPLER_DATA_PATH)
    writer_config = TraceWriterConfigModel(
        loader_config, PathType.Resampler, RESAMPLER_OUTPUT_TYPE, RESAMPLER_OUTPUT_FOLDER_PATH, trace_length,
        trace_count, output_sample_coding, RESAMPLER_OUTPUT_COMPRESSED, RESAMPLER_STEP
    )
    parallel_config: ParallelWriterConfigModel = ParallelWriterConfigModel(
        writer_config, RESAMPLER_PROCESS_COUNT, RESAMPLER_SHARE_MEMORY_NAME_DATA, RESAMPLER_SHARE_MEMORY_NAME_TRACES
    )

    return ResamplerConfigModel(
        parallel_config, RESAMPLER_WINDOW_SIZE, RESAMPLER_OVERLAP, RESAMPLER_STEP, RESAMPLER_ABS, RESAMPLER_USE_FLOAT,
        RESAMPLER_INCLUDE_CUT_OUTPUT_NAME
    )

RESAMPLER_CONFIG: ResamplerConfigModel = _generate_resampler_config()
