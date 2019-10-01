import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

from pyquil.api import get_qc
from pyquil.quil import Program
from pyquil.gates import RX
from pyquil.paulis import sZ
from grove.pyvqe.vqe import VQE

from em_pyquil import apply_em, apply_noise

# Important: Please use Grove's latest version from github to work with is example
# to install grove from github use this command:
# pip install -e git+https://github.com/rigetti/grove.git#egg=quantum-grove


def run_with_qc(qc, angle_range):
    def small_ansatz(params):
        return Program(RX(params[0], 0))

    hamiltonian = sZ(0)

    vqe_inst = VQE(minimizer=minimize,
                   minimizer_kwargs={'method': 'nelder-mead'})

    # Do not run with samples=None otherwise VQE will use WaveFunctionSimulator and will bypass our patch version of qc
    data = [vqe_inst.expectation(small_ansatz([angle]), hamiltonian, qc=qc, samples=10000)
            for angle in angle_range]

    return data


def main():
    noisy_qc = apply_noise(get_qc("3q-qvm"))
    em_qc = apply_em(get_qc("3q-qvm"))

    angle_range = np.linspace(0.0, 2 * np.pi, 20)

    noisy_data = run_with_qc(noisy_qc, angle_range)
    em_data = run_with_qc(em_qc, angle_range)

    plt.xlabel('Angle [radians]')
    plt.ylabel('Expectation value')
    plt.plot(angle_range, noisy_data, label="Only Noise")
    plt.plot(angle_range, em_data, label="EM + Noise")
    plt.legend()
    plt.show()


main()
