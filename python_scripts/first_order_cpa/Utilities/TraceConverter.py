import concurrent
import numpy as np
from multiprocessing.shared_memory import SharedMemory
from numpy.typing import NDArray
from typing import Callable
from functools import partial
from trsfile import Trace
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from Common.Generics.GenericParallelWriter import GenericParallelWriter
from Common.Models.FileType import FileType
from Common.Models.PathType import PathType
from Configuration.Constants import CONVERTER_SHARE_MEMORY_NAME_DATA, CONVERTER_SHARE_MEMORY_NAME_TRACES
from Helpers.IntervalHelpers import calculate_config_length_interval, calculate_config_length_discard_set
from Configuration.Models.Traces.ParallelWriterConfigModel import ParallelWriterConfigModel


global converter_traces

# IO
CONVERTER_TARGET_PATH: str = '/media/xmann/Disk/Traces/all_traces2.trs'
# Ignored if input not npy
CONVERTER_DATA_PATH: str = ''
CONVERTER_OUTPUT_FOLDER_PATH: str = '/media/xmann/Disk/Traces/Test' # Empty to use the same input folder
CONVERTER_OUTPUT_TYPE: FileType = FileType.NPY
CONVERTER_OUTPUT_COMPRESSED: bool = False # Used only if output is NPZ

# Locality
CONVERTER_SAMPLE_START: int | None = 0
CONVERTER_SAMPLE_END: int | None = None
CONVERTER_TRACES_TO_SKIP: set[int] = set()

# Multithreading
CONVERTER_PROCESS_COUNT: int = 16


class TraceConverter(GenericParallelWriter):

    def __init__(self, parallel_config: ParallelWriterConfigModel, traces_to_skip: set[int]):
        global converter_traces
        super().__init__(parallel_config)
        if self.is_input_numpy:
            converter_traces = self.traces
        else:
            converter_traces = self.traceset
        self.traces_to_skip: set[int] = traces_to_skip
        self._perform_basic_checks()

    def _perform_basic_checks(self) -> None:
        assert self.trace_count > len(self.traces_to_skip), 'Invalid number of Traces to skip'
        if len(self.traces_to_skip) > 0:
            assert min(self.traces_to_skip) >= 0, 'Trace index to skip cannot be negative'
            assert self.trace_count > max(self.traces_to_skip), 'Invalid maximum index of Traces to skip'

    @staticmethod
    def _convert_numpy_to_trs(start: int, end: int, index: int) -> Trace:
        raise NotImplementedError() # This conversion is unnecessary

    @staticmethod
    def _convert_numpy_to_numpy(start: int, end: int, process_count: int, sample_coding: np.dtype,
                                trace_index: int) -> None:
        cut_sample_length: int = end - start
        samples: NDArray = converter_traces[trace_index][start:end]
        traces_shm: SharedMemory = SharedMemory(name=CONVERTER_SHARE_MEMORY_NAME_TRACES)
        trace_samples_shm: NDArray = np.ndarray(cut_sample_length, dtype=sample_coding, buffer=traces_shm.buf,
                                                offset=(trace_index % process_count) * cut_sample_length
                                                       * sample_coding.itemsize)
        trace_samples_shm[:] = samples

    @staticmethod
    def _convert_trs_to_numpy(start: int, end: int, process_count: int, sample_coding: np.dtype,
                              trace_index: int) -> None:
        cut_sample_length: int = end - start
        traces_shm: SharedMemory = SharedMemory(name=CONVERTER_SHARE_MEMORY_NAME_TRACES)
        trace_samples_shm: NDArray = np.ndarray(cut_sample_length, dtype=sample_coding, buffer=traces_shm.buf,
                                                offset=(trace_index % process_count) * cut_sample_length
                                                       * sample_coding.itemsize)
        trace: Trace = converter_traces[trace_index]
        GenericParallelWriter.copy_data_from_trace(CONVERTER_SHARE_MEMORY_NAME_DATA, process_count, trace, trace_index)
        trace_samples_shm[:] = trace[start:end]

    @staticmethod
    def _convert_trs_to_trs(start: int, end: int, trace_index: int) -> Trace:
        trace: Trace = converter_traces[trace_index]
        trace.samples = trace[start:end]
        return trace

    def _get_converter_function(self, cut_from: int, cut_to: int) -> Callable:
        if self.input_type == FileType.TRS:
            if self.output_type == FileType.TRS:
                return partial(self._convert_trs_to_trs, cut_from, cut_to)
            elif self.is_output_numpy:
                return partial(self._convert_trs_to_numpy, cut_from, cut_to, self.process_count,
                               self.output_sample_coding)
        elif self.is_input_numpy:
            if self.is_output_numpy:
                return partial(self._convert_numpy_to_numpy, cut_from, cut_to, self.process_count,
                               self.output_sample_coding)
            elif self.output_type == FileType.TRS:
                return partial(self._convert_trs_to_numpy, cut_from, cut_to)
        raise Exception(f'Invalid combination od input and output type {self.input_type} -> {self.output_type}')


    def convert_and_cut(self, cut_from: int | None = 0, cut_to: int = None) -> None:
        cut_from = 0 if cut_from is None else cut_from
        cut_to = self.trace_length if cut_to is None else cut_to
        print(f'Converting to {self.output_type.name}, samples ({cut_from} - {cut_to})...')
        print(f'Traces to skip: {self.traces_to_skip}')
        self.create_output(cut_from, cut_to, True)
        convert_function: Callable = self._get_converter_function(cut_from, cut_to)
        discarded_traces_count: int = 0
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for current_batch in tqdm(range(0, self.trace_count, self.process_count)):
                current_process_count: int = self.check_process_bounds(current_batch, True)
                current_indexes: set[int] = set(range(current_batch, current_batch + current_process_count)
                                              ).difference(self.traces_to_skip)
                cut_traces: list = list(executor.map(convert_function, current_indexes))
                if self.output_type == FileType.TRS:
                    self.output_traceset.extend(cut_traces)
                elif self.is_output_numpy:
                    current_trace_index: int = current_batch - discarded_traces_count
                    current_process_indexes: NDArray[np.int32] = np.array(list(current_indexes), dtype=np.int32
                                                                          ) % self.process_count
                    self.copy_from_shared_memory(current_trace_index, current_process_count, current_batch,
                                                 current_process_indexes)
                    discarded_traces_count += current_process_count - len(current_process_indexes)
        self.save_output(0) # Convertor already subtracts skipped traces during config initialization


if __name__ == '__main__':
    from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel
    from Configuration.Models.Traces.TraceWriterConfigModel import TraceWriterConfigModel
    loader_config = TraceLoaderConfigModel(CONVERTER_TARGET_PATH, CONVERTER_DATA_PATH)
    trace_length = calculate_config_length_interval(CONVERTER_SAMPLE_START, CONVERTER_SAMPLE_END)
    trace_count = calculate_config_length_discard_set(CONVERTER_TRACES_TO_SKIP)
    writer_config = TraceWriterConfigModel(
        loader_config, PathType.Converter, CONVERTER_OUTPUT_TYPE, CONVERTER_OUTPUT_FOLDER_PATH, trace_length,
        trace_count, output_compressed=CONVERTER_OUTPUT_COMPRESSED
    )
    config = ParallelWriterConfigModel(writer_config, CONVERTER_PROCESS_COUNT,
                                       CONVERTER_SHARE_MEMORY_NAME_DATA, CONVERTER_SHARE_MEMORY_NAME_TRACES)
    converter: TraceConverter = TraceConverter(config, CONVERTER_TRACES_TO_SKIP)
    converter.convert_and_cut(CONVERTER_SAMPLE_START, CONVERTER_SAMPLE_END)
