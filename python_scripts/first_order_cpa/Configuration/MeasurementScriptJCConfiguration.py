from Common.Models.FileType import FileType
from Common.Models.ParameterDefinition import ParameterDefinition
from Configuration.Constants import KEY_NAME, PLAIN_TEXT_NAME, NONCE_NAME
from Configuration.Models.Other.MeasurementScriptConfigModel import MeasurementScriptConfigModel
from Configuration.Models.Traces.TraceCreatorConfigModel import TraceCreatorConfigModel
from Helpers.ParameterWrapper import ParameterWrapper
from Configuration.MeasurementScriptConstants import PICO_MAGIC_VALUE
from MeasurementScripts.Models.MeasurementTarget import MeasurementTarget

# Measured traces
MS_TRACE_COUNT: int = 1000  # Number of traces to capture
MS_SAMPLE_START: int = 0 # Captured location start
MS_SAMPLE_END: int = 64200000 # Captured location end (Needs to be always specified)

# Output
MS_OUTPUT_FOLDER_PATH: str = '/media/xmann/SSD/Traces' # Time folder is added automatically to the folder path
MS_OUTPUT_FILE_NAME: str = 'tvla_alt'
MS_OUTPUT_TYPE: FileType = FileType.NPY
MS_OUTPUT_PARAMETERS: ParameterWrapper = ParameterWrapper([
    ParameterDefinition(KEY_NAME, 16),
    ParameterDefinition(PLAIN_TEXT_NAME, 16),
    ParameterDefinition(NONCE_NAME, 16),
])

# Target
MS_MEASUREMENT_TARGET: MeasurementTarget = MeasurementTarget.ASCON
MS_FIXED_KEY: int | None = 0x8D7BC7569361894DF1DAE2A18C0E3498
MS_FIXED_NONCE: int | None = 0x828486fea10c2e4d10745691c375aa90 # Used for TVLA (ASCON)
MS_FIXED_PT: int | None = 0x0db0865a4d243bd18dda5a0267abba8a # Used for TVLA (AES)
MS_FIX_EVERY_SECOND_ATTACK: bool = True # If fixed nonce or plaintext used, fix it only every second attack (TVLA)
MS_APPLET_ID: list[int] = [0x55, 0x6E, 0x69, 0x74, 0x54, 0x65, 0x73, 0x74]

# Picoscope
MS_OFFSET_MV: float = -0.2 # Set up channel B with -180 mV offset
MS_CHANNEL_B_RANGE: int = 5
MS_THRESHOLD : int = int(3 / 10 * PICO_MAGIC_VALUE) # Set up a single trigger on AUX IN
MS_PRE_TRIGGER_SAMPLES: int = 10
MS_PICO_TIMEBASE: int = 2

# Graph
MS_SAVE_GRAPH: bool = False


def get_measurement_script_config() -> MeasurementScriptConfigModel:
    creator_config: TraceCreatorConfigModel = TraceCreatorConfigModel(
        MS_OUTPUT_FILE_NAME, MS_OUTPUT_FOLDER_PATH, MS_OUTPUT_TYPE, MS_OUTPUT_PARAMETERS, MS_TRACE_COUNT,
        MS_SAMPLE_START, MS_SAMPLE_END
    )
    return MeasurementScriptConfigModel(
        creator_config, MS_APPLET_ID, MS_MEASUREMENT_TARGET, MS_OFFSET_MV, MS_CHANNEL_B_RANGE, MS_THRESHOLD,
        MS_PRE_TRIGGER_SAMPLES, MS_PICO_TIMEBASE, MS_FIX_EVERY_SECOND_ATTACK, MS_FIXED_KEY, MS_FIXED_NONCE,
        MS_FIXED_PT, MS_SAVE_GRAPH
    )

MEASUREMENT_SCRIPT_JC_CONFIG: MeasurementScriptConfigModel = get_measurement_script_config()
