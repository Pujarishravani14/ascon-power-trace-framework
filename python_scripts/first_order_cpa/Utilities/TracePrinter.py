from numpy.typing import NDArray
from Common.Generics.GenericTraceLoader import GenericTraceLoader
from Common.Models.ParameterDefinition import ParameterDefinition
from Configuration.Constants import KEY_NAME, PLAIN_TEXT_NAME, NONCE_NAME
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel
from trsfile import TraceSet
from Helpers.GenericHelper import check_interval
from Helpers.ParameterWrapper import ParameterWrapper


# IO
PRINTER_TARGET_PATH: str =  '/media/xmann/SSD/Traces/ascon_large_traces.npy'
PRINTER_DATA_PATH: str = ''

# Locality
PRINTER_TRACE_INDEX: int = 499
PRINTER_SHOW_SAMPLES: bool = True
PRINTER_SAMPLE_START: int = 0
PRINTER_SAMPLE_END: int = 200

# Numpy
PRINTER_SHOW_DATA_HEX: bool = True
PRINTER_DATA_PARAMETERS: ParameterWrapper = ParameterWrapper([
    ParameterDefinition(KEY_NAME, 16),
    ParameterDefinition(PLAIN_TEXT_NAME, 16),
    ParameterDefinition(NONCE_NAME, 16),
])


class TracePrinter(GenericTraceLoader):

    def __init__(self, loader_config: TraceLoaderConfigModel) -> None:
        super().__init__(loader_config)

    def _perform_basic_checks(self) -> None:
        check_interval(PRINTER_SAMPLE_START, PRINTER_SAMPLE_END, self.trace_length)
        assert PRINTER_TRACE_INDEX < self.trace_count, 'Trace index out of range'

    @staticmethod
    def print_headers_trs_file(trace_file: TraceSet) -> None:
        print("Headers:")
        for header, value in trace_file.get_headers().items():
            print(f'{header}: {value}')
        print("\nFirst trace parameters:")
        parameters: dict = trace_file[PRINTER_TRACE_INDEX].parameters
        for parameter_key, parameter_value in parameters.items():
            print(f'{parameter_key}: {parameter_value}')
        print()  # Add additional new line on the end of print

    @staticmethod
    def print_headers_np_file(data: NDArray, traces: NDArray) -> None:
        print(f'Data shape: {data.shape}, Traces shape: {traces.shape}')
        print(f'Data type: {data.dtype}, Traces type: {traces.dtype}')
        data = data[PRINTER_TRACE_INDEX]
        print(f'\nParameters from ({PRINTER_TRACE_INDEX}) trace:')
        PRINTER_DATA_PARAMETERS.print_parameters(data, PRINTER_SHOW_DATA_HEX)

    @staticmethod
    def generic_print(data: NDArray | None, traces: NDArray | None, traceset: TraceSet | None,  trace_length: int,
                      samples_trace_idx: int = 0, print_samples: bool = False, print_samples_from: int = 0,
                      print_samples_to: int = -1) -> None:
        if print_samples_to == -1:
            print_samples_to = trace_length
        if traceset is not None:
            TracePrinter.print_headers_trs_file(traceset)
        elif data is not None and traces is not None:
            TracePrinter.print_headers_np_file(data, traces)
        else:
            raise Exception('No data or traceset provided')
        if print_samples:
            print(f'Samples [{print_samples_from},{print_samples_to}] from (trace index - {samples_trace_idx}):')
            check_interval(print_samples_from, print_samples_to, trace_length)
            if traceset is not None:
                samples: NDArray = traceset[samples_trace_idx][print_samples_from:print_samples_to]
            else:
                samples: NDArray = traces[samples_trace_idx][print_samples_from:print_samples_to]
            print(samples)
        print()  # Add additional new line on the end of print

    def print_trace(self):
        self.generic_print(self.data, self.traces, self.traceset, self.trace_length, PRINTER_TRACE_INDEX,
                           PRINTER_SHOW_SAMPLES, PRINTER_SAMPLE_START, PRINTER_SAMPLE_END)


if __name__ == '__main__':
    printer = TracePrinter(TraceLoaderConfigModel(PRINTER_TARGET_PATH, PRINTER_DATA_PATH))
    printer.print_trace()
