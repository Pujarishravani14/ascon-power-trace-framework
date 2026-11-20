import concurrent.futures
import numpy as np
from typing import Callable
from tqdm import tqdm
from numpy.typing import NDArray
from trsfile import Trace
from functools import partial
from multiprocessing.shared_memory import SharedMemory
from Common.Generics.GenericParallelWriter import GenericParallelWriter
from Common.Models.FileType import FileType
from Configuration.Constants import RESAMPLER_SHARE_MEMORY_NAME_TRACES, RESAMPLER_SHARE_MEMORY_NAME_DATA
from Configuration.Models.Tools.ResamplerConfigModel import ResamplerConfigModel
from Helpers.GenericHelper import check_interval
from numba import njit

global resampler_traceset # Avoid the need for pickling, which is not allowed for memory-mapped objects


class Resampler(GenericParallelWriter):

    def __init__(self, resampler_config: ResamplerConfigModel) -> None:
        global resampler_traceset
        super().__init__(resampler_config.parallel_config)
        self.window_size: int = resampler_config.window_size
        self.resampler_step: int = resampler_config.resampler_step
        self.resampler_abs: bool = resampler_config.use_absolute_value
        self.resampler_float: bool = resampler_config.use_float
        self.include_cut_in_output_name: bool = resampler_config.include_cut_in_output_name
        if self.is_input_numpy:
            resampler_traceset = self.traces
        elif self.input_type == FileType.TRS:
            resampler_traceset = self.traceset
        else:
            raise Exception('Invalid input type for resampler')
        self.perform_resampler_checks()

    def cleanup(self):
        super().cleanup()

    def perform_resampler_checks(self):
        assert self.window_size > 0, 'Window size must be positive'
        assert self.resampler_step > 0, 'Resampling step must be positive'
        assert self.window_size > self.resampler_step, 'Window size must be greater than resampling step'

    @staticmethod
    @njit
    def process_trace(samples: NDArray, sample_coding: np.dtype, output_trace_length: int, resampler_step: int,
                      window_size: int, use_abs: bool) -> NDArray:
        processed = np.empty(output_trace_length, dtype=sample_coding)
        for step in range(output_trace_length):
            start: int = step * resampler_step
            chunk: NDArray = samples[start:start + window_size]
            if use_abs:
                chunk = np.abs(chunk)
            average: np.floating = np.average(chunk)
            if sample_coding.kind == 'f': # Check if it is a float type
                processed[step] = average
            else:
                processed[step] = np.round(average)
        return processed

    @staticmethod
    def _resampler_numpy_to_numpy(sample_start: int, sample_end: int, output_trace_length: int,
                                  output_sample_coding: np.dtype, resampler_step: int,  window_size: int,
                                  use_abs: bool, process_count: int, trace_idx: int) -> None:
        samples: NDArray = resampler_traceset[trace_idx][sample_start:sample_end]
        processed: NDArray = Resampler.process_trace(
            samples, output_sample_coding, output_trace_length, resampler_step, window_size, use_abs
        )
        traces_shm: SharedMemory = SharedMemory(name=RESAMPLER_SHARE_MEMORY_NAME_TRACES)
        trace_samples_shm: NDArray = np.ndarray(output_trace_length, dtype=output_sample_coding, buffer=traces_shm.buf,
                                                offset=(trace_idx % process_count) * output_trace_length
                                                       * output_sample_coding.itemsize)
        trace_samples_shm[:] = processed

    @staticmethod
    def _resample_trs_to_numpy(sample_start: int, sample_end: int, output_trace_length: int,
                               output_sample_coding: np.dtype,  resampler_step: int, window_size: int,
                               use_abs: bool, process_count: int, trace_idx: int) -> None:
        trace: Trace = resampler_traceset[trace_idx]
        trace_array = trace[sample_start:sample_end]
        processed: np.array = Resampler.process_trace(
            trace_array, output_sample_coding, output_trace_length, resampler_step, window_size, use_abs
        )
        GenericParallelWriter.copy_data_from_trace(RESAMPLER_SHARE_MEMORY_NAME_DATA, process_count, trace,
                                                   trace_idx)
        traces_shm: SharedMemory = SharedMemory(name=RESAMPLER_SHARE_MEMORY_NAME_TRACES)
        trace_samples_shm: NDArray = np.ndarray(output_trace_length, dtype=output_sample_coding, buffer=traces_shm.buf,
                                                offset=(trace_idx % process_count) * output_trace_length
                                                       * output_sample_coding.itemsize)
        trace_samples_shm[:] = processed

    @staticmethod
    def _resample_trs_to_trs(sample_start: int, sample_end: int, trace_length: int, output_sample_coding: np.dtype,
                             resampler_step: int, window_size: int, use_abs: bool, trace_idx: int) -> Trace:
        """
        Function to process each trace in parallel
        """
        trace: Trace = resampler_traceset[trace_idx]
        trace_array = trace.samples[sample_start:sample_end]
        processed: np.array = Resampler.process_trace(
            trace_array, output_sample_coding, trace_length, resampler_step, window_size, use_abs
        )
        trace.samples = processed
        return trace

    def _get_resampler_function(self, cut_start: int = 0, cut_end: int = None) -> Callable:
        if self.output_type == FileType.TRS:
            if self.is_input_numpy:
                raise Exception(f'Unsupported conversion {self.input_type} -> {self.output_type} during resampling')
            return partial(
                self._resample_trs_to_trs, cut_start, cut_end, self.output_trace_length, self.output_sample_coding,
                self.resampler_step,self.window_size, self.resampler_abs
            )
        elif self.is_output_numpy:
            if self.is_input_numpy:
                resampler_function: Callable = self._resampler_numpy_to_numpy
            else:
                resampler_function = self._resample_trs_to_numpy
            return partial(
                resampler_function, cut_start, cut_end, self.output_trace_length, self.output_sample_coding,
                self.resampler_step, self.window_size, self.resampler_abs, self.process_count
            )
        else:
            raise Exception('Invalid output type for resampler')

    def _perform_run_checks(self, start: int, end: int, traces_start: int, traces_end: int) -> None:
        check_interval(start, end, self.trace_length)
        check_interval(traces_start, traces_end, self.trace_count)
        assert traces_end - traces_start == self.output_trace_count,\
            'Trace count must be consistent across different calls'

    def run_resampler(self, traces_start: int = 0, traces_end: int = None,
                      cut_start: int = 0, cut_end: int = None) -> None:
        cut_end = self.trace_length if cut_end is None else cut_end
        traces_end = self.trace_count if traces_end is None else traces_end
        self._perform_run_checks(cut_start, cut_end, traces_start, traces_end)
        self.create_output(cut_start, cut_end, self.include_cut_in_output_name)
        resample_with_constants = self._get_resampler_function(cut_start, cut_end)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for current in tqdm(range(traces_start, traces_end, self.process_count)):
                current_process_count: int = self.check_process_bounds(current)
                results = list(executor.map(resample_with_constants,
                                            range(current, current + current_process_count)))
                if self.output_type == FileType.TRS:
                    self.output_traceset.extend(results)
                else:
                    self.copy_from_shared_memory(current, current_process_count)
        self.save_output()


if __name__ == '__main__':
    from Configuration.ResamplerConfiguration import RESAMPLER_SAMPLE_START, \
        RESAMPLER_SAMPLE_END, RESAMPLER_TRACE_END, RESAMPLER_TRACE_START, RESAMPLER_CONFIG
    resampler = Resampler(RESAMPLER_CONFIG)
    resampler.run_resampler(RESAMPLER_TRACE_START, RESAMPLER_TRACE_END, RESAMPLER_SAMPLE_START, RESAMPLER_SAMPLE_END)
