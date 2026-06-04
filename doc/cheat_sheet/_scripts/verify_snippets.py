#!/usr/bin/env python3
# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Verify the Amazon Braket cheat sheet against the installed SDK.

The cheat sheet lives in ``doc/cheat_sheet/_includes/en/`` as small Markdown
tables of ``| description | `code` |`` rows. This script keeps those snippets
honest in two complementary ways:

1. **Imports** -- every ``import`` statement found in the English sections is
   executed against the installed ``braket`` package, so a renamed or removed
   symbol fails loudly (the exact class of bug that makes a cheat sheet stale).

2. **Behaviour** -- the snippets that run without AWS (circuits, free
   parameters, noise, the local simulator, program sets, the local emulator,
   analog Hamiltonian simulation and experimental capabilities) are executed
   end-to-end. Cloud-only entry points (``AwsDevice.run``, ``DirectReservation``,
   ``AwsQuantumJob``/``@hybrid_job``) are verified by inspecting their public
   signatures, which needs no credentials.

Run it with::

    python doc/cheat_sheet/_scripts/verify_snippets.py

It exits non-zero if anything is out of sync with the SDK.
"""

from __future__ import annotations

import inspect
import re
import sys
import traceback
from pathlib import Path

EN_DIR = Path(__file__).resolve().parents[1] / "_includes" / "en"
CODE_SPAN = re.compile(r"`([^`]+)`")


def _iter_code_spans() -> list[tuple[str, str]]:
    """Yield ``(section, code)`` for every inline-code span in the English sections."""
    spans: list[tuple[str, str]] = []
    for md in sorted(EN_DIR.glob("*.md")):
        for raw in md.read_text(encoding="utf-8").splitlines():
            for match in CODE_SPAN.findall(raw):
                spans.append((md.stem, match.strip()))
    return spans


def check_imports() -> list[str]:
    """Execute every import statement appearing in the cheat sheet.

    Imports of optional third-party packages that are not installed (e.g. the
    Qiskit provider) are skipped rather than failed -- only ``braket`` symbols
    are treated as load-bearing here.
    """
    failures: list[str] = []
    seen: set[str] = set()
    for section, code in _iter_code_spans():
        stripped = code.lstrip()
        if not (stripped.startswith("import ") or stripped.startswith("from ")):
            continue
        if code in seen:
            continue
        seen.add(code)
        try:
            exec(compile(code, f"<{section}:imports>", "exec"), {})  # noqa: S102
        except ModuleNotFoundError as exc:
            missing = (exc.name or "").split(".")[0]
            if missing != "braket":
                continue  # optional external dependency, not part of the SDK
            failures.append(f"[{section}] import failed: {code!r} -> {exc}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"[{section}] import failed: {code!r} -> {exc}")
    return failures


def check_behaviour() -> list[str]:
    """Run the local snippets and signature-check the cloud-only ones."""
    failures: list[str] = []

    def case(name: str, fn) -> None:
        try:
            fn()
        except Exception:  # noqa: BLE001
            failures.append(f"[{name}] {traceback.format_exc(limit=2).strip()}")

    # --- Circuits -------------------------------------------------------------
    def circuits() -> None:
        import numpy as np
        from braket.circuits import Circuit, Gate, Instruction
        from braket.circuits.observables import X

        circuit = Circuit().x(0).rx(1, 1.23).cnot(0, 1)
        circuit.probability(0)
        circuit.expectation(0.5 * X() @ X(), target=[0, 1])
        circuit.unitary([0], np.eye(2))
        assert circuit.to_unitary().shape[0] >= 2
        circuit.add(Instruction(Gate.CPhaseShift(1.23), target=[0, 1]))
        # Round-trip a plain circuit (result types do not parse back through from_ir).
        qasm = Circuit().h(0).cnot(0, 1).to_ir("OPENQASM").source
        assert "OPENQASM" in qasm
        assert Circuit.from_ir(source=qasm) is not None

    # --- Free parameters ------------------------------------------------------
    def free_parameters() -> None:
        from braket.circuits import Circuit, FreeParameter

        alpha = FreeParameter("alpha")
        circuit = Circuit().rx(0, alpha)
        _ = 2 * alpha + 1
        assert circuit.parameters == {alpha}
        bound = circuit.make_bound_circuit({"alpha": 0.1})
        assert not bound.parameters

    # --- Program sets ---------------------------------------------------------
    def program_sets() -> None:
        from braket.circuits import Circuit, FreeParameter
        from braket.circuits.observables import X, Z
        from braket.program_sets import CircuitBinding, ProgramSet

        c1, c2 = Circuit().h(0), Circuit().x(0)
        ps = ProgramSet([c1, c2], shots_per_executable=100)
        assert ps.total_executables == 2
        circuit = Circuit().rx(0, FreeParameter("theta")).cnot(0, 1)
        CircuitBinding(circuit, input_sets=[{"theta": 0.1}, {"theta": 0.2}])
        CircuitBinding(circuit, {"theta": [0.1, 0.2]}, 2.1 * X(0) @ Z(1) - 4.5 * Z(0) @ Z(1))
        ProgramSet.zip([c1, c2], observables=[X(0), Z(0)])
        ProgramSet.product([c1], [X(0), Z(0)])

    # --- Noise simulation -----------------------------------------------------
    def noise() -> None:
        import numpy as np
        from braket.circuits import Circuit, Gate, Noise

        pauli_x = np.array([[0, 1], [1, 0]])
        e0 = np.sqrt(0.9) * np.eye(4)
        e1 = np.sqrt(0.1) * np.kron(pauli_x, pauli_x)
        circuit = Circuit().x(0).x(1).x(2)
        circuit.depolarizing(0, 0.1)
        circuit.kraus([0, 2], [e0, e1])
        noise_channel = Noise.PhaseDamping(0.1)
        circuit.apply_gate_noise(noise_channel, Gate.X)

    # --- Local simulator + results -------------------------------------------
    def simulator_results() -> None:
        from braket.circuits import Circuit
        from braket.devices import LocalSimulator

        bell = Circuit().h(0).cnot(0, 1)
        result = LocalSimulator().run(bell, shots=100).result()
        assert sum(result.measurement_counts.values()) == 100
        assert result.measured_qubits == [0, 1]

    # --- Local emulator -------------------------------------------------------
    def emulator() -> None:
        from braket.circuits import Circuit
        from braket.devices import LocalSimulator
        from braket.emulation import Emulator

        emu = Emulator(backend=LocalSimulator("braket_dm"))
        circuit = Circuit().h(0).cnot(0, 1)
        emu.validate(circuit)
        emu.transform(circuit)
        assert sum(emu.run(circuit, shots=10).result().measurement_counts.values()) == 10

    # --- Experimental capabilities -------------------------------------------
    def experimental() -> None:
        import math

        from braket.circuits import Circuit
        from braket.experimental_capabilities import EnableExperimentalCapability
        from braket.experimental_capabilities.iqm.classical_control import CCPRx, MeasureFF

        with EnableExperimentalCapability():
            circuit = Circuit()
            circuit.measure_ff(0, feedback_key=0)
            circuit.cc_prx(1, math.pi / 2, math.pi / 4, feedback_key=0)
        assert any(isinstance(i.operator, (CCPRx, MeasureFF)) for i in circuit.instructions)

    # --- Analog Hamiltonian Simulation ---------------------------------------
    def ahs() -> None:
        from braket.ahs import AnalogHamiltonianSimulation, AtomArrangement, DrivingField
        from braket.timings.time_series import TimeSeries

        register = AtomArrangement()
        register.add((5.7e-6, 5.7e-6))
        assert register.coordinate_list(0)
        amplitude = TimeSeries().put(0, 0).put(1e-7, 0)
        phase = TimeSeries().put(0, 0).put(1e-7, 0)
        detuning = TimeSeries().put(0, 0).put(1e-7, 0)
        drive = DrivingField(amplitude=amplitude, phase=phase, detuning=detuning)
        AnalogHamiltonianSimulation(register=register, hamiltonian=drive)

    # --- Cost tracking --------------------------------------------------------
    def tracking() -> None:
        from braket.tracking import Tracker

        with Tracker() as tracker:
            tracker.qpu_tasks_cost()
            tracker.simulator_tasks_cost()
            tracker.quantum_tasks_statistics()

    # --- Cloud-only: verify by signature (no network) -------------------------
    def cloud_signatures() -> None:
        from braket.aws import AwsDevice, AwsQuantumJob, DirectReservation
        from braket.jobs import hybrid_job, save_job_result
        from braket.jobs.metrics import log_metric

        run_params = inspect.signature(AwsDevice.run).parameters
        assert "reservation_arn" in run_params
        job_params = inspect.signature(hybrid_job).parameters
        for expected in ("device", "local", "dependencies", "include_modules",
                         "input_data", "reservation_arn"):
            assert expected in job_params, expected
        assert "reservation_arn" in inspect.signature(AwsQuantumJob.create).parameters
        res_params = inspect.signature(DirectReservation.__init__).parameters
        assert "reservation_arn" in res_params
        assert callable(save_job_result)
        metric_params = inspect.signature(log_metric).parameters
        for expected in ("metric_name", "value", "iteration_number"):
            assert expected in metric_params, expected

    case("Circuits", circuits)
    case("FreeParameters", free_parameters)
    case("ProgramSets", program_sets)
    case("NoiseSimulation", noise)
    case("Simulators/Results", simulator_results)
    case("Emulators", emulator)
    case("ExperimentalCapabilities", experimental)
    case("AHS", ahs)
    case("Pricing", tracking)
    case("Cloud (signatures)", cloud_signatures)
    return failures


def main() -> int:
    import_failures = check_imports()
    behaviour_failures = check_behaviour()
    failures = import_failures + behaviour_failures

    if failures:
        print("CHEAT SHEET VERIFICATION FAILED\n")
        for failure in failures:
            print(f"  - {failure}\n")
        return 1

    print("Cheat sheet verified: all imports resolve and all local snippets run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
