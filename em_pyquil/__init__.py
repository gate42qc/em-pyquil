from pyquil import Program
from pyquil.api import QuantumComputer
from pyquil.api._quantum_computer import Executable
from pyquil.noise import add_decoherence_noise
import numpy as np
import types

from typing import Iterator

from pyquil.quilbase import Gate

__all__ = ['apply_em', 'apply_noise']


def preserved(p: Program) -> Program:
    return Program('PRAGMA PRESERVE_BLOCK') + p + Program('PRAGMA END_PRESERVE_BLOCK')


def get_expectations(measurements: np.ndarray) -> np.ndarray:
    trials, qubits = measurements.shape

    expectations = np.zeros((1 << qubits))
    powers = 1 << np.arange(qubits)

    trial_values = np.dot(measurements, powers)

    for value in trial_values:
        expectations[value] += 1

    expectations = expectations / trials

    return expectations


def get_extrapolated_with_richardson(noise_param_multiply_coefficients: np.ndarray, data: np.ndarray) -> np.ndarray:
    measurements, = noise_param_multiply_coefficients.shape

    matrix = \
        noise_param_multiply_coefficients ** np.arange(0, measurements)[:, np.newaxis]
    b = np.zeros((measurements,))
    b[0] = 1
    coefficients = np.linalg.solve(matrix, b)

    mitigated_result = np.dot(coefficients, data).T
    mitigated_result = np.maximum(mitigated_result, np.full(mitigated_result.shape, 0))
    mitigated_result = np.minimum(mitigated_result, np.full(mitigated_result.shape, 1))
    return mitigated_result


def get_binary(n: int, length) -> Iterator[int]:
    return list(reversed([((n >> i) & 1) for i in range(length)]))


def get_bitstrings_from_expectations(expectations: np.ndarray, shape: tuple) -> np.ndarray:
    qubits, trials = shape

    bitstrings = np.zeros((trials, qubits), dtype=int)
    index = 0
    for i, v in enumerate(expectations):
        bits = np.array(get_binary(i, qubits), dtype=int)
        number_of_occurrences = int(v * trials)
        bitstrings[index: index + number_of_occurrences] = bits
        index += number_of_occurrences

    return bitstrings


def get_noisy_executable(qc: QuantumComputer, original_executable: Executable, noise_param: float):
    original_program = Program(original_executable.program)
    native_program = original_program.copy_everything_except_instructions()

    # we
    for g in original_program:
        if isinstance(g, Gate):
            native_gates = [i for i in
                            qc.compiler.quil_to_native_quil(Program([g])).instructions
                            if isinstance(i, Gate)]
            native_program.inst(native_gates)
        else:
            native_program.inst(g)

    noisy = add_decoherence_noise(native_program, gate_time_1q=noise_param, gate_time_2q=3 * noise_param)
    return qc.compiler.native_quil_to_executable(noisy)


def apply_em(qc: QuantumComputer,
             base_gate_time: float = 50e-9,
             order: int = 3) -> QuantumComputer:
    """
    Get new QuantumComputer which will run programs with EM technique applied.
    :param qc: QuantumComputer instance to patch
    :param base_gate_time: base noise parameter
    :param order: coefficients to be used for stretching base noise parameter
    :return: the new patched QuantumComputer instance
    """

    if not isinstance(qc, QuantumComputer):
        raise ValueError(f"Invalid parameter {qc} for apply_em(). You should provide a QuantumComputer instance.")

    if hasattr(qc.qam, "noise_model") and qc.qam.noise_model is not None:
        raise ValueError(f"QuantumComputer {qc} instance should not have noise model.")

    original_run = qc.run

    noise_param_multiply_coefficients = np.arange(1, order + 2)

    def new_run(self, executable, *args, **kwargs):
        noise_params = noise_param_multiply_coefficients * base_gate_time
        original_results = []
        trials, qubits = None, None

        for noise_param in noise_params:
            original_exec = executable.copy()
            new_exec = get_noisy_executable(qc, original_exec, noise_param)
            original_exec.program = new_exec.program

            bitstring = original_run(executable=original_exec, *args, **kwargs)
            trials, qubits = bitstring.shape
            original_results.append(get_expectations(bitstring))

        original_results = np.array(original_results)

        mitigated_result = get_extrapolated_with_richardson(noise_param_multiply_coefficients, original_results)
        result_bitstring = get_bitstrings_from_expectations(mitigated_result, (qubits, trials))

        return result_bitstring

    qc.run = types.MethodType(new_run, qc)

    return qc


def apply_noise(qc: QuantumComputer, gate_time=50e-9):
    """
    Get new QuantumComputer with noise model applied
    :param qc: QuantumComputer instance to patch
    :param gate_time: gate time for using in noise model
    :return: patched QuantumComputer instance
    """
    if not isinstance(qc, QuantumComputer):
        raise ValueError(f"Invalid parameter {qc} for apply_em(). You should provide a QuantumComputer instance.")

    if hasattr(qc.qam, "noise_model") and qc.qam.noise_model is not None:
        raise ValueError(f"QuantumComputer {qc} instance should not have noise model.")

    original_run = qc.run

    def new_run(self, executable, *args, **kwargs):
        original_exec = executable.copy()
        new_exec = get_noisy_executable(qc, original_exec, noise_param=gate_time)
        original_exec.program = new_exec.program

        return original_run(executable=original_exec, *args, **kwargs)

    qc.run = types.MethodType(new_run, qc)

    return qc
