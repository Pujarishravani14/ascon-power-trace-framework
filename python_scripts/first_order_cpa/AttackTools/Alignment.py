import numpy as np
from os.path import splitext
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Queue
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from threading import Thread
from typing import TextIO, Tuple, Callable
from numpy.typing import NDArray
from trsfile import Trace
from tqdm import tqdm
from AttackTools.Resampler import Resampler
from Common.AlignmentShiftCalculator import compute_shift, compute_shift_cut
from Common.AlignmentVisualization import show_alignment_graph
from Common.Generics.GenericParallelWriter import GenericParallelWriter
from Common.Models.AlignmentInterval import AlignmentInterval
from Common.Models.FileType import FileType
from Configuration.Models.Tools.AlignmentConfigModel import AlignmentConfigModel
from Helpers.GenericHelper import check_interval
from Configuration.Constants import ALIGNMENT_SHM_NAME_REF, \
    ALIGNMENT_SHM_NAME_DATA, ALIGNMENT_SHM_NAME_TRACES, ADVANCED_ALIGNMENT_STEP


global alignment_traceset # Avoid the need for pickling, which is not allowed for memory-mapped objects
global log_queue # Avoid a need for pickling which makes the queue copied and separated between processes


def log_consumer(log: TextIO) -> None:
    min_corr: float = 1.0
    while True:
        trace_idx, shift_f, correlation = log_queue.get()
        if trace_idx is None:
            break
        if correlation < min_corr:
            min_corr = correlation
        if log is not None:
            log.write(f'trace {trace_idx}\t\t: shift:{shift_f}, corr:{correlation}\n')
    print('min_corr=', min_corr)


class Alignment(GenericParallelWriter):

    def __init__(self, config: AlignmentConfigModel):
        global alignment_traceset
        super().__init__(config.parallel_writer_config)
        print('Initializing alignment...', end='', flush=True)
        self.logging_enabled: bool = config.alignment_log_enable
        self.reference_index: int = config.reference_index
        self.max_shift: int = config.max_shift
        self.threshold: float = config.threshold
        self.dry_run: bool = config.dry_run
        self.show_graph: bool = config.show_graph
        self.graph_trace_count: int = config.graph_trace_count
        self.graph_trace_length: int = config.graph_trace_length
        self.include_cut: bool = config.include_cut
        self.alignment_resampling_length: int = config.alignment_resampling_length
        self.alignment_resampling_abs: bool = config.alignment_resampling_abs
        self.log_file, self.log_thread = None, None
        self._perform_alignment_checks()
        if self.is_input_numpy:
            alignment_traceset = self.traces # Make loaded traces global for multiprocessing
        else:
            alignment_traceset = self.traceset
        if self.is_input_numpy:
            self.reference_trace: NDArray = alignment_traceset[self.reference_index]  # Does not change between runs
        else:
            self.reference_trace: NDArray = alignment_traceset[self.reference_index].samples
        if self.alignment_resampling_length > 0:
            self.reference_trace = Resampler.process_trace(
                self.reference_trace, self.reference_trace.dtype, self.reference_trace.size, 1,
                self.alignment_resampling_length, self.alignment_resampling_abs
            )
        self._init_reference_trace()
        print('done', flush=True)

    def _perform_alignment_checks(self) -> None:
        assert self.trace_count > self.reference_index, 'Reference trace index out of range'
        assert not self.is_input_numpy or self.input_type != FileType.TRS, \
            'Unsupported conversion (NPY,NPZ -> TRS), use convertor instead or numpy as output!'
        assert self.max_shift >= 0, 'Max shift must be non-negative'
        assert self.threshold >= 0, 'Threshold must be non-negative'
        assert self.alignment_resampling_length >= 0, 'Alignment resampling length must be non-negative'
        assert self.graph_trace_count < self.trace_count, 'Graph trace count must be less than trace count'

    def _init_reference_trace(self) -> None:
        """
        Create shared memory for reference trace to avoid copying to each process
        """
        try:
            ref_shm: SharedMemory = SharedMemory(ALIGNMENT_SHM_NAME_REF)  # Check if memory not already created
        except FileNotFoundError:
            ref_shm = SharedMemory(ALIGNMENT_SHM_NAME_REF, True, self.trace_length * self.reference_trace.itemsize)
        shared_ref_array = np.ndarray(self.trace_length, dtype=self.sample_coding, buffer=ref_shm.buf)
        np.copyto(shared_ref_array, self.reference_trace)

    def cleanup(self) -> None:
        self.free_shared_memory(ALIGNMENT_SHM_NAME_REF)
        self.free_shared_memory(ALIGNMENT_SHM_NAME_DATA)
        self.free_shared_memory(ALIGNMENT_SHM_NAME_TRACES)
        if 'log_queue' in globals():
            log_queue.put((None, None, None)) # Exit loop
        if self.log_thread is not None:
            self.log_thread.join()
        if self.log_file is not None:
            self.log_file.close()
        super().cleanup()

    def _prepare_logging(self) -> Tuple[TextIO | None, Thread | None]:
        global log_queue
        log_file: TextIO | None = None
        if self.logging_enabled:
            log_file = open(splitext(self.target_path)[0] + '_align_log.txt', 'w')
        log_queue = Queue()
        # Logging thread to asynchronously write log
        log_thread = Thread(target=log_consumer, args=(log_file,), daemon=True)
        log_thread.start()
        return log_file, log_thread

    @staticmethod
    def _get_interval_samples(start: int, end: int, cut_start: int, cut_end: int, trace_length: int, max_shift: int,
                              is_input_numpy: bool, alignment_resampling_length: int, alignment_resampling_abs: bool,
                              trace_idx: int) -> AlignmentInterval:
        cut_start_index: int = max_shift # Where the cut is in the internal interval
        alignment_start_index_with_shift: int = 0 # Where the alignment with shift is in the internal interval
        pad_left: int = 0
        pad_right: int = 0
        # Use a larger interval (alignment or cut) and set start indexes accordingly
        if start < cut_start:
            cut_start_index += cut_start - start
            start_interval = start - max_shift
        else:
            alignment_start_index_with_shift = start - cut_start
            start_interval = cut_start - max_shift
        if end > cut_end:
            end_interval = end + max_shift
        else:
            end_interval = cut_end + max_shift
        # Pad out of bounds
        if start_interval < 0:
            pad_left = abs(start_interval)
            start_interval = 0
        if end_interval > trace_length:
            pad_right = end_interval - trace_length
            end_interval = trace_length
        trace: Trace | None = None  # Only used when input is trs
        if is_input_numpy:
            interval_samples: NDArray = alignment_traceset[trace_idx][start_interval:end_interval]
        else:
            trace = alignment_traceset[trace_idx]
            interval_samples = trace[start_interval:end_interval]
        interval_samples = np.pad(interval_samples, (pad_left, pad_right), 'constant', constant_values=0)
        original_samples: NDArray | None = None # Only used when advanced alignment is used
        if alignment_resampling_length > 0:
            original_samples = interval_samples
            interval_samples = Resampler.process_trace(
                interval_samples, interval_samples.dtype, interval_samples.size, ADVANCED_ALIGNMENT_STEP,
                alignment_resampling_length, alignment_resampling_abs
            )
        return AlignmentInterval(interval_samples, trace, cut_start_index, alignment_start_index_with_shift,
                                 original_samples)

    @staticmethod
    def _compute_shift(interval: AlignmentInterval, start: int, end: int, sample_coding: np.dtype,
                       max_shift: int, max_corr: float) -> Tuple[int, float]:
        ref_shm: SharedMemory = SharedMemory(name=ALIGNMENT_SHM_NAME_REF)
        ref_samples: NDArray = np.ndarray(end - start, dtype=sample_coding, buffer=ref_shm.buf,
                                   offset=start * sample_coding.itemsize)
        alignment_start: int = interval.alignment_start_index # Start including maximum shift
        alignment_length: int = end - start + 2 * max_shift # Length with maximum shift included
        alignment_samples: NDArray = interval.interval_samples[alignment_start:alignment_start + alignment_length]
        shift, corr = compute_shift_cut(ref_samples, alignment_samples, max_shift)
        correlation: float = corr / max_corr
        return shift, correlation

    #Multi-threading function
    @staticmethod
    def _run_alignment_trs_out(start: int, end: int, cut_start: int, cut_end: int, max_corr: float,
                               max_shift: int, threshold: float, dry_run: bool, sample_coding: np.dtype,
                               trace_length: int, alignment_resampling_length: int, alignment_resampling_abs: bool,
                               trace_idx: int) -> Trace | None:
        interval: AlignmentInterval = Alignment._get_interval_samples(
            start, end, cut_start, cut_end, trace_length, max_shift, False, alignment_resampling_length,
            alignment_resampling_abs, trace_idx
        )
        shift, correlation = Alignment._compute_shift(interval, start, end, sample_coding, max_shift, max_corr)
        log_queue.put((trace_idx, shift, correlation))
        if dry_run or correlation < threshold:
            return None
        cut_length: int = cut_end - cut_start
        if interval.original_samples is not None:
            output_traces: NDArray = interval.original_samples
        else:
            output_traces: NDArray = interval.interval_samples
        rolled_traces = np.roll(output_traces, shift)
        interval.trace.samples = rolled_traces[interval.cut_start_index:interval.cut_start_index+cut_length]
        return interval.trace

    #Multi-threading function
    @staticmethod
    def _run_alignment_np_out(start: int, end: int, cut_start: int, cut_end: int, max_corr: float, max_shift: int,
                              threshold: float, dry_run: bool, sample_coding: np.dtype, trace_length: int,
                              alignment_resampling_length: int, alignment_resampling_abs: bool, is_input_numpy: bool,
                              process_count: int, trace_idx: int) -> bool:
        interval: AlignmentInterval = Alignment._get_interval_samples(
            start, end, cut_start, cut_end, trace_length, max_shift, is_input_numpy, alignment_resampling_length,
            alignment_resampling_abs, trace_idx
        )
        shift, correlation = Alignment._compute_shift(interval, start, end, sample_coding, max_shift, max_corr)
        log_queue.put((trace_idx, shift, correlation))
        if dry_run or correlation < threshold:
            return False
        cut_length: int = cut_end - cut_start
        traces_shm: SharedMemory = SharedMemory(name=ALIGNMENT_SHM_NAME_TRACES)
        trace_samples_shm: NDArray = np.ndarray(cut_length, dtype=sample_coding, buffer=traces_shm.buf,
                                                offset=(trace_idx % process_count) * cut_length * sample_coding.itemsize)
        if not is_input_numpy:
            GenericParallelWriter.copy_data_from_trace(ALIGNMENT_SHM_NAME_DATA, process_count, interval.trace,
                                                       trace_idx)
        if interval.original_samples is not None:
            output_traces: NDArray = interval.original_samples
        else:
            output_traces: NDArray = interval.interval_samples
        rolled_traces = np.roll(output_traces, shift)
        trace_samples_shm[:] = rolled_traces[interval.cut_start_index:interval.cut_start_index+cut_length]
        return True # Trace not discarded

    def _get_alignment_function(self, start: int, end: int, cut_start: int, cut_end: int, max_corr: float) -> Callable:
        if self.output_type == FileType.TRS:
            return partial(
                self._run_alignment_trs_out, start, end, cut_start, cut_end, max_corr, self.max_shift,
                self.threshold, self.dry_run, self.sample_coding, self.trace_length, self.alignment_resampling_length,
                self.alignment_resampling_abs
            )
        else:
            return partial(
                self._run_alignment_np_out, start, end, cut_start, cut_end, max_corr, self.max_shift,
                self.threshold, self.dry_run, self.sample_coding, self.trace_length, self.alignment_resampling_length,
                self.alignment_resampling_abs, self.is_input_numpy, self.process_count
            )

    def _get_max_corr(self, start: int, end: int) -> float:
        """
        Compute max_corr by aligning ref trace with itself
        """
        ref_trace = self.reference_trace
        new_start = start - self.max_shift
        new_end = end + self.max_shift
        if new_start < 0:
            new_start_pad = abs(new_start)
            ref_trace = np.pad(ref_trace[:new_end], (new_start_pad, 0))
            start = start + new_start_pad
            end = end + new_start_pad
        elif new_end > len(ref_trace):
            new_end_pad = new_end - len(ref_trace)
            ref_trace = np.pad(ref_trace[new_start:], (0, new_end_pad))
            end = end - start + self.max_shift
            start = self.max_shift
        _, max_corr = compute_shift(ref_trace, ref_trace, start, end, self.max_shift)
        return max_corr

    def run_alignment(self, start: int, end: int, cut_from: int = 0, cut_to: int = None) -> Tuple[int, int]:
        cut_to = self.trace_length if cut_to is None else cut_to
        check_interval(start, end, self.trace_length)
        check_interval(cut_from, cut_to, self.trace_length)
        max_corr: float = self._get_max_corr(start, end)
        if not self.dry_run:
            self.create_output(cut_from, cut_to, self.include_cut)
        self.log_file, self.log_thread = self._prepare_logging()
        discarded_trace_count: int = 0
        run_alignment_with_constants = self._get_alignment_function(start, end, cut_from, cut_to, max_corr)
        with ProcessPoolExecutor() as executor:
            for current_batch in tqdm(range(0, self.output_trace_count, self.process_count)):
                current_process_count: int = self.check_process_bounds(current_batch)
                results: list = list(executor.map(run_alignment_with_constants,
                                                  range(current_batch, current_batch + current_process_count)))
                if self.dry_run:
                    continue # Avoid saving during a dry run
                elif self.output_type == FileType.TRS:
                    filtered_results: list[Trace] = [result for result in results if result is not None]
                    self.output_traceset.extend(filtered_results)
                else:
                    # Return indexes where trace was not discarded
                    indexes: NDArray[np.int32] = np.where(np.array(results))[0]
                    current_start_index: int = current_batch - discarded_trace_count
                    self.copy_from_shared_memory(current_start_index, current_process_count, current_batch, indexes)
                    discarded_trace_count += current_process_count - np.sum(results)
        log_queue.put((None, None, None)) # Exit loop
        if self.log_thread is not None:
            self.log_thread.join()
            self.log_thread = None
        new_trace_count: int = self.output_trace_count - discarded_trace_count
        if not self.dry_run:
            print(f'Trace count before alignment: {self.trace_count}, after alignment: {new_trace_count}')
            if self.show_graph:
                show_alignment_graph(self.output_traceset, self.output_traces, new_trace_count, self.reference_index,
                                     self.graph_trace_count, self.graph_trace_length, self.output_type)
            self.save_output(discarded_trace_count)
        return self.output_trace_count, new_trace_count


if __name__== '__main__':
    from Configuration.AlignmentConfiguration import (ALIGNMENT_CONFIG, ALIGNMENT_START, ALIGNMENT_END,
                                                      ALIGNMENT_SAMPLE_START, ALIGNMENT_SAMPLE_END)
    ascon_alignment = Alignment(ALIGNMENT_CONFIG)
    ascon_alignment.run_alignment(ALIGNMENT_START, ALIGNMENT_END, ALIGNMENT_SAMPLE_START, ALIGNMENT_SAMPLE_END)
