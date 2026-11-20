import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from typing import Tuple
from trsfile import Trace
from Common.Generics.GenericTraceLoader import GenericTraceLoader
from Common.Models.ParameterDefinition import ParameterDefinition
from Configuration.Constants import KEY_NAME, PLAIN_TEXT_NAME, NONCE_NAME
from Configuration.Models.Traces.TraceLoaderConfigModel import TraceLoaderConfigModel
from Helpers.GenericHelper import check_interval
from Helpers.NumpyHelper import convert_to_hex_string
from Helpers.ParameterWrapper import ParameterWrapper

# Visualizer Configuration

# IO
VISUALIZER_TARGET_PATH: str = '/data/JCVM/random_traces_ASCON_10000/large_traces.trs'
VISUALIZER_DATA_PATH: str = '' # Used only if input is npy

# Locality
VISUALIZER_SAMPLE_START: int = 0
VISUALIZER_SAMPLE_END: int = 64000 # -1 to show all samples
VISUALIZER_TRACE_START: int = 0
VISUALIZER_GRAPH_TRACE_COUNT: int = 1  # Number of traces shown in one graph
VISUALIZER_GRAPH_COUNT: int = 1

# Layout
VISUALIZER_TOGETHER: bool = False
VISUALIZER_SPACING: float = 0.05 # 0 to not use a tight layout

#Labels
VISUALIZER_X_LABEL: str = 'Time'
VISUALIZER_Y_LABEL: str = 'Values'
VISUALIZER_DISPLAY_LABELS: int = 5 # Number of labels to show
VISUALIZER_LABEL_LOCATION: str = 'upper left'
VISUALIZER_DISPLAY_DATA: bool = True # Include data inside labels
VISUALIZER_FONT_SIZE: int = 20

#Data
VISUALIZER_DATA_PARAMETERS: ParameterWrapper = ParameterWrapper([
    ParameterDefinition(KEY_NAME, 16),
    ParameterDefinition(PLAIN_TEXT_NAME, 16),
    ParameterDefinition(NONCE_NAME, 16),
])
VISUALIZER_DATA_NAME: str = NONCE_NAME
VISUALIZER_DATA_LENGTH: int = 0 # How much of data should be included in the label (0 - all)

class TraceVisualizer(GenericTraceLoader):

    def __init__(self):
        matplotlib.use('TkAgg') # Change backend for interactive visualization
        super().__init__(TraceLoaderConfigModel(VISUALIZER_TARGET_PATH, VISUALIZER_DATA_PATH))
        self._perform_basic_checks()

    def _perform_basic_checks(self) -> None:
        assert VISUALIZER_TRACE_START + VISUALIZER_GRAPH_TRACE_COUNT * VISUALIZER_GRAPH_COUNT <= self.trace_count, \
            'Insufficient amount of traces to show'
        assert VISUALIZER_TRACE_START >= 0 and VISUALIZER_GRAPH_TRACE_COUNT > 0 and VISUALIZER_GRAPH_COUNT > 0, \
            'Negative configuration values'

    def _get_samples_with_data(self, current_trace_index: int, start: int, end: int) -> Tuple[str, NDArray]:
        if self.is_input_numpy:
            raw_data: NDArray = VISUALIZER_DATA_PARAMETERS.get_parameter(self.data[current_trace_index],
                                                                         VISUALIZER_DATA_NAME)
            data: str = convert_to_hex_string(raw_data)
            samples: NDArray = self.traces[current_trace_index][start:end]
        else:
            trace: Trace | np.array = self.traceset[current_trace_index]
            data: str = str(trace.parameters[VISUALIZER_DATA_NAME])
            samples: NDArray = trace[start:end]
        print(f'Data {current_trace_index}:', data)
        print(f'Samples {current_trace_index}:', samples)
        return data, samples

    def visualize(self, start: int, end: int) -> None:
        if end == -1:
            end = self.trace_length
        check_interval(start, end, self.trace_length)
        if VISUALIZER_TOGETHER and VISUALIZER_GRAPH_COUNT > 1:
            fig, ax = plt.subplots(VISUALIZER_GRAPH_COUNT, sharex=True, sharey=True)
        else:
            fig, ax = plt.figure(), None
        for repeat_index in range(VISUALIZER_GRAPH_COUNT):
            trace_start: int = VISUALIZER_TRACE_START + (repeat_index * VISUALIZER_GRAPH_TRACE_COUNT)
            trace_end: int = trace_start + VISUALIZER_GRAPH_TRACE_COUNT
            title: str = f'Traces ({trace_start}-{trace_end - 1})' if VISUALIZER_GRAPH_TRACE_COUNT > 1 else f'Trace: {trace_start}'
            for iteration_index, current_trace_index in enumerate(range(trace_start, trace_end)):
                data, samples = self._get_samples_with_data(current_trace_index, start, end)
                label: str = ''
                if iteration_index < VISUALIZER_DISPLAY_LABELS:
                    label: str = f'Trace[{current_trace_index}]'
                    if VISUALIZER_DISPLAY_DATA:
                        if VISUALIZER_DATA_LENGTH == 0:
                            label += f': {data}'
                        else:
                            label += f': {data[:VISUALIZER_DATA_LENGTH]}...'
                if VISUALIZER_TOGETHER and VISUALIZER_GRAPH_COUNT > 1:
                    ax[repeat_index].plot(samples, label=label)
                else:
                    plt.plot(samples, label=label)
            if VISUALIZER_TOGETHER and VISUALIZER_GRAPH_COUNT > 1:
                ax[repeat_index].set_title(title, fontsize=VISUALIZER_FONT_SIZE)
                ax[repeat_index].set_xlabel(VISUALIZER_X_LABEL, fontsize=VISUALIZER_FONT_SIZE)
                ax[repeat_index].set_ylabel(VISUALIZER_Y_LABEL, fontsize=VISUALIZER_FONT_SIZE)
                if VISUALIZER_DISPLAY_LABELS != 0:
                    ax[repeat_index].legend(loc=VISUALIZER_LABEL_LOCATION, fontsize=VISUALIZER_FONT_SIZE)
            else:
                plt.title(title, fontsize=VISUALIZER_FONT_SIZE)
                plt.xlabel(VISUALIZER_X_LABEL, fontsize=VISUALIZER_FONT_SIZE)
                plt.ylabel(VISUALIZER_Y_LABEL, fontsize=VISUALIZER_FONT_SIZE)
                if VISUALIZER_DISPLAY_LABELS != 0:
                    plt.legend(loc=VISUALIZER_LABEL_LOCATION, fontsize=VISUALIZER_FONT_SIZE)
                plt.xticks(fontsize=VISUALIZER_FONT_SIZE)
                plt.yticks(fontsize=VISUALIZER_FONT_SIZE)
                plt.show()
        if VISUALIZER_TOGETHER:
            trace_end: int = VISUALIZER_TRACE_START + (VISUALIZER_GRAPH_TRACE_COUNT * VISUALIZER_GRAPH_COUNT) - 1
            fig.suptitle(f'Traces ({VISUALIZER_TRACE_START}-{trace_end})')
            if VISUALIZER_SPACING > 0:
                fig.subplots_adjust(top=(1 - VISUALIZER_SPACING), right=(1 - VISUALIZER_SPACING),
                                    left=VISUALIZER_SPACING, hspace=0.35)
            plt.xticks(fontsize=VISUALIZER_FONT_SIZE)
            plt.yticks(fontsize=VISUALIZER_FONT_SIZE)
            plt.show()


if __name__ == '__main__':
    visualizer = TraceVisualizer()
    visualizer.visualize(VISUALIZER_SAMPLE_START, VISUALIZER_SAMPLE_END)
