from dataclasses import dataclass
from Configuration.Models.Traces.TraceCreatorConfigModel import TraceCreatorConfigModel
from MeasurementScripts.Models.MeasurementTarget import MeasurementTarget


@dataclass
class MeasurementScriptConfigModel:
    creator_config: TraceCreatorConfigModel
    applet_id: list[int]
    measurement_target: MeasurementTarget
    offset_mv: float
    channel_b_range: int
    threshold: int
    pre_trigger_samples: int
    pico_timebase: int
    fix_every_second_attack: bool = False
    fixed_key: int | None = None
    fixed_nonce: int | None = None
    fixed_pt: int | None = None
    save_graph: bool = False
