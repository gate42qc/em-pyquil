import numpy as np
import matplotlib.pyplot as plt
import random

from pyquil.api import get_qc
from pyquil.quil import Program
from pyquil.gates import RX, RZ, CZ

from em_pyquil import apply_em, apply_noise


def get_dagger_of_native_gate(gate):
    if gate.name == "RZ":
        return RZ(-gate.params[0], gate.qubits[0])
    if gate.name == "RX":
        return RX(-gate.params[0], gate.qubits[0])
    if gate.name == "CZ":
        return CZ(*gate.qubits)

    raise ValueError("Unsupported gate: " + str(gate))


def get_random_circuit(qubits, length, two_qubit_gate_portion=0.3):
    p = Program()

    for i in range(int(length / 2)):
        if (len(qubits) > 1) and (random.random() < two_qubit_gate_portion):
            random_gate = CZ(*(random.sample(qubits, 2)))
        else:
            theta = 2 * np.pi * random.random()
            qubit = random.choice(qubits)
            random_gate = random.choice([
                RZ(theta, qubit),
                RX(np.pi / 2, qubit),
                RX(- np.pi / 2, qubit)
            ])

        p.inst(random_gate)

    for gate in reversed(Program(p.out()).instructions):
        p.inst(get_dagger_of_native_gate(gate))

    return Program('PRAGMA PRESERVE_BLOCK') + p + Program('PRAGMA END_PRESERVE_BLOCK')


def run_with_qc(qc, lengths):
    data = []

    for i in lengths:
        p = get_random_circuit(qc.qubits(), i)
        res = qc.run_and_measure(p, 1000)
        fidelity = 1 - np.mean(res[0])
        data.append(fidelity)

    return data


def main():
    noisy_qc = apply_noise(get_qc("3q-qvm"))
    em_qc = apply_em(get_qc("3q-qvm"))

    lengths = np.arange(2, 100, 5)

    em_data = run_with_qc(em_qc, lengths)
    noisy_data = run_with_qc(noisy_qc, lengths)

    plt.xlabel('Circuit depth')
    plt.ylabel('Fidelity')
    plt.plot(lengths, noisy_data, 'o-', label="Only Noise")
    plt.plot(lengths, em_data, 'o-', label="Noise + EM")
    plt.legend()
    plt.show()


main()
