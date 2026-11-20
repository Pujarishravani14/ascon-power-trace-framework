import numpy as np
from numpy.typing import NDArray
from Common.Generics.GenericTraceCreator import GenericTraceCreator
from Common.Models.FileType import FileType
from Configuration.Constants import ASCON_IV, ASCON_NONCE_BYTE_SIZE, INT_LOW, INT_HIGH, NONCE_NAME, KEY_NAME
from Configuration.Models.Traces.TraceGenConfigModel import TraceGenConfigModel
from Helpers.GenericHelper import generate_random_number, hamming_weight, get_bits_on_interval
from AsconImplementation import Ascon
from trsfile.parametermap import TraceParameterMap
from trsfile.traceparameter import ByteArrayParameter
from secrets import token_bytes
from trsfile import Trace, SampleCoding


class AsconTraceGenerator(GenericTraceCreator):

    def __init__(self, trace_generation_config: TraceGenConfigModel):
        super().__init__(trace_generation_config.creator_config)
        self.random_distribution_mean: int = trace_generation_config.random_distribution_mean
        self.random_distribution_std: int = trace_generation_config.random_distribution_std
        self.variable_noise: int = trace_generation_config.variable_noise
        self.attack_position: int = trace_generation_config.leakage_position
        self.random_shift: int = trace_generation_config.random_shift
        self.attack_register: int = trace_generation_config.attack_register
        self.attack_register_from: int = trace_generation_config.attack_register_from
        self.attack_register_to: int = trace_generation_config.attack_register_to
        self.trace_gen_leakage_amplification: int = trace_generation_config.trace_gen_leakage_amplification
        self.key = trace_generation_config.key
        self._perform_gen_checks()
        if self.output_type == FileType.TRS:
            self.nonces: NDArray | None = np.empty((self.output_trace_count, ASCON_NONCE_BYTE_SIZE),
                                                   dtype=np.uint8)
        else:
            self.nonces = None

    def _perform_gen_checks(self) -> None:
        assert 0 <= self.attack_register < 5, 'Invalid attack register index'
        assert self.random_shift >= 0, 'Random shift must be greater than or equal to 0'
        assert self.trace_gen_leakage_amplification > 0, 'Leakage amplification must be greater than 0'
        assert self.variable_noise >= 0, 'Variable shift must be greater than or equal to 0'
        assert self.random_distribution_std >= 0, 'Random distribution must be greater than or equal to 0'

    def _generate_internal_state(self, trace_idx: int) -> NDArray[np.uint64]:
        nonce_x3 = generate_random_number()
        nonce_x4 = generate_random_number()
        internal_state = np.empty(5, dtype=np.uint64)
        internal_state[0] = ASCON_IV
        internal_state[1] = self.key[0]
        internal_state[2] = self.key[1]
        internal_state[3] = nonce_x3
        internal_state[4] = nonce_x4
        if self.is_output_numpy:
            nonce_bytes = np.array([nonce_x3, nonce_x4], dtype='>u8').view(np.uint8)
            self.output_parameters.write_parameter_to_array(self.output_data[trace_idx], NONCE_NAME, nonce_bytes)
            key_bytes = np.array([self.key[0], self.key[1]], dtype='>u8').view(np.uint8)
            self.output_parameters.write_parameter_to_array(self.output_data[trace_idx], KEY_NAME, key_bytes)
        else:
            self.nonces[trace_idx] = np.array([nonce_x3, nonce_x4], dtype='>u8').view(np.uint8)
        Ascon.add_round_key(internal_state, 0)
        Ascon.compute_substitution(internal_state)
        Ascon.compute_diffusion_layer(internal_state)
        return internal_state

    def _generate_shifted_random_traces(self, leakage: NDArray) -> None:
        traces: NDArray = np.random.normal(self.random_distribution_mean, self.random_distribution_std,
                                           (self.output_trace_count, self.output_trace_length + 2 * self.random_shift))
        if self.variable_noise > 0:
            trace_noise: NDArray = np.random.randint(0, self.variable_noise, size=(self.output_trace_count, 1))
            traces += trace_noise
        traces[:, self.attack_position] += leakage * self.trace_gen_leakage_amplification
        traces_rounded: NDArray = np.round(traces)
        traces_clipped: NDArray = np.clip(traces_rounded, INT_LOW, INT_HIGH).astype(np.int8)
        if self.random_shift > 0:
            random_shifts: NDArray = np.random.randint(0, self.random_shift, size=self.output_trace_count)
        else:
            random_shifts = np.zeros(self.output_trace_count, dtype=np.int8)
        for trace_idx in range(self.output_trace_count):
            random_shift: int = int(random_shifts[trace_idx])
            if random_shift > 0:
                traces_clipped[trace_idx] = np.roll(traces_clipped[trace_idx], random_shift)
                trace_samples: NDArray = traces_clipped[trace_idx][self.random_shift:-self.random_shift]
            else:
                trace_samples: NDArray = traces_clipped[trace_idx]
            if self.is_output_numpy:
                self.output_traces[trace_idx] = trace_samples
            else:
                key_bytes: bytes = np.array([self.key[0], self.key[1]], dtype='>u8').view(np.uint8).tobytes()
                nonce: bytes = self.nonces[trace_idx].tobytes()
                plaintext: bytes = token_bytes(16)  # Not used during the ascon attack
                trace_parameters = TraceParameterMap({
                    'KEY': ByteArrayParameter(key_bytes),
                    'PT': ByteArrayParameter(plaintext),
                    'NONCE': ByteArrayParameter(nonce)
                })
                self.output_traceset.append(Trace(SampleCoding.BYTE, trace_samples, trace_parameters))

    def create_simulated_traces(self) -> None:
        leakage: NDArray = np.empty(self.output_trace_count, dtype=np.uint8)
        print('Generating leakage...', end='', flush=True)
        for trace_idx in range(self.output_trace_count):
            state: NDArray = self._generate_internal_state(trace_idx)
            state_bits: int = get_bits_on_interval(int(state[self.attack_register]), self.attack_register_from,
                                              self.attack_register_to)
            leakage[trace_idx] = hamming_weight(state_bits)
        print('done', flush=True)
        print('Generating traces...', end='', flush=True)
        self._generate_shifted_random_traces(leakage)
        print('done', flush=True)
        self.save_output()


if __name__ == "__main__":
    from Configuration.AsconTraceGenConfiguration import TRACE_GEN_CONFIG
    trace_gen: AsconTraceGenerator = AsconTraceGenerator(TRACE_GEN_CONFIG)
    trace_gen.create_simulated_traces()
