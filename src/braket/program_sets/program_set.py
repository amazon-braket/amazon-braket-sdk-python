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

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from braket.ir.openqasm import ProgramSet as OpenQASMProgramSet

from braket.circuits import Circuit, Gate, Observable
from braket.circuits.observables import Sum
from braket.circuits.serialization import IRType
from braket.program_sets.circuit_binding import CircuitBinding
from braket.pulse import PulseSequence
from braket.registers import QubitSet


class ProgramSet:
    def __init__(
        self,
        programs: list[CircuitBinding | Circuit] | CircuitBinding,
        shots_per_executable: int | None = None,
    ):
        """
        A set of programs to be run together on a device.

        Args:
            programs (list[CircuitBinding | Circuit] | CircuitBinding): A list of circuit bindings
                or circuits to execute. It is also possible to provide a single circuit binding.
                Note: circuits cannot have result types.
            shots_per_executable (int | None): The number of shots to run each executable;
                this will be used to enforce the total shots on task creation. If not provided,
                the only validation at task creation will be divisibility by number of executables.
        """
        self._programs = [programs] if isinstance(programs, CircuitBinding) else programs
        if any(isinstance(circuit, Circuit) and circuit.result_types for circuit in self._programs):
            raise ValueError("Circuit cannot have result types")
        self._shots_per_executable = shots_per_executable

    def to_ir(
        self,
        *,
        gate_definitions: Mapping[tuple[Gate, QubitSet], PulseSequence] | None = None,
    ) -> OpenQASMProgramSet:
        """Serializes the program set into a form that can run on a Braket device.

        Args:
            gate_definitions (dict[tuple[Gate, QubitSet], PulseSequence] | None): The
                calibration data for the device. default: None.

        Returns:
            braket.ir.openqasm.ProgramSet: The serialized program set.
        """
        return OpenQASMProgramSet(
            programs=[
                (
                    circuit_binding.to_ir(IRType.OPENQASM, gate_definitions=gate_definitions)
                    if isinstance(circuit_binding, Circuit)
                    else circuit_binding.to_ir(gate_definitions=gate_definitions)
                )
                for circuit_binding in self._programs
            ]
        )

    @property
    def entries(self) -> list[CircuitBinding | Circuit]:
        """list[CircuitBinding | Circuit]: The circuit bindings or circuits in this program set"""
        return self._programs

    @property
    def total_executables(self) -> int:
        """int: The total number of executables in this program set"""
        return sum(len(prog) if isinstance(prog, CircuitBinding) else 1 for prog in self._programs)

    @property
    def shots_per_executable(self) -> int | None:
        """int: The number of shots to run each executable in this program set"""
        return self._shots_per_executable

    @property
    def total_shots(self) -> int:
        """
        int: The total number of shots across all executables in this program set,
        if shots_per_executable was provided.
        """
        if not self._shots_per_executable:
            raise ValueError("No per-executable shots defined")
        return self._shots_per_executable * self.total_executables

    def enumerate_executables(self) -> Iterator[tuple[int, int, int]]:
        """Yield ``(binding_index, parameter_set_index, observable_index)`` tuples in order,
        one per executable.

        The iteration order is: iterate over ``self.entries``; within each entry,
        iterate over parameter set indices; within each parameter set index,
        iterate over observable indices. The total number of yields is ``self.total_executables``.

        For ``Circuit``s and ``CircuitBinding``s with no input sets, ``parameter_set_index`` is 0.
        For entries with no observables, ``observable_index`` is 0. For ``CircuitBinding``s with a
        ``Sum`` Hamiltonian, ``observable_index`` ranges over the summands.

        This ordering is used by ``split`` to build its index map and by
        ``ProgramSetQuantumTaskResult.merge`` to merge results back into the original shape.

        Yields:
            tuple[int, int, int]: ``(binding_index, parameter_set_index, observable_index)``.
        """
        for binding_idx, prog in enumerate(self._programs):
            if isinstance(prog, Circuit):
                yield binding_idx, 0, 0
                continue
            num_obs = len(prog.observables) if prog.observables is not None else 1
            for ps_idx in range(len(prog.input_sets) if prog.input_sets is not None else 1):
                for obs_idx in range(num_obs):
                    yield binding_idx, ps_idx, obs_idx

    def split(self, max_executables: int) -> tuple[list[ProgramSet], list[list[int]]]:
        """Split this program set into program sets of at most ``max_executables`` executables,
        alongside a map that records the position in the original program set of each executable
        in each of the generated program sets.

        When a single parameter set index of a ``CircuitBinding`` would by itself exceed
        ``max_executables`` due to its observable list or ``Sum`` Hamiltonian being larger than
        the budget, the observable list is split into chunks of at most ``max_executables`` entries
        (``Sum`` summands are sliced with coefficients preserved). Observable splitting is only
        performed when necessary; otherwise the full observable list or ``Sum`` is kept intact.

        The indices in the list of positions take values in the range [0, total_executables - 1].

        Args:
            max_executables (int): The maximum number of executables per program
                set. Must be positive.

        Returns:
            tuple[list[ProgramSet], list[list[int]]]: ``(program_sets, index_map)``.
            ``index_map[k][j]`` is the index of the executable that the j-th executable of
            ``program_sets[k]`` represents.
            If this program set already fits within ``max_executables``, the returned
            program-set list is ``[self]`` and the index_map is ``[[0, 1, ...,
            total_executables - 1]]``.

        Raises:
            ValueError: If ``max_executables`` is not positive.

        Examples:
            >>> ps = ProgramSet([
            ...     CircuitBinding(c1, inputs1, obs1),  # 100 param sets, 4 observables
            ...     CircuitBinding(c2, inputs2, obs2),  # 50 param sets, 2 observables
            ... ])
            >>> subs, index_map = ps.split(120)
            >>> [s.total_executables for s in subs]
            [120, 120, 120, 120, 20]
            >>> sum(len(m) for m in index_map) == ps.total_executables
            True
        """
        if max_executables <= 0:
            raise ValueError(f"max_executables must be positive, got {max_executables}")

        if self.total_executables <= max_executables:
            return [self], [list(range(self.total_executables))]

        program_sets = []
        index_map = []
        current = []
        current_size = 0
        for block in self._executable_blocks(max_executables):
            if current and current_size + block.size > max_executables:
                sub, sub_map = self._build_program_set(current)
                program_sets.append(sub)
                index_map.append(sub_map)
                current = []
                current_size = 0
            current.append(block)
            current_size += block.size
        sub, sub_map = self._build_program_set(current)
        program_sets.append(sub)
        index_map.append(sub_map)

        return program_sets, index_map

    def _executable_blocks(self, max_executables: int) -> list[_ExecutableBlock]:
        """Enumerate this program set's executables as a list of ``_ExecutableBlock``s in the order
        of ``enumerate_executables``

        Each block is a contiguous run of executables that share the same
        ``(circuit, observable list/Sum Hamiltonian, single parameter assignment)`` and can thus be
        kept together when packing program sets in ``split``. A ``Circuit`` entry and a
        ``CircuitBinding`` with no input sets each yield a single block; a ``CircuitBinding`` with
        input sets yields one block per parameter set index. Within a parameter set index,
        the observables are chunked into slices of at most ``max_executables``, so an observable
        list or ``Sum`` Hamiltonian larger than the ``max_executables`` is split across multiple
        blocks with a slice recorded on each.

        Args:
            max_executables (int): The maximum number of executables per program
                set. Must be positive.

        Returns:
            list[_ExecutableBlock]: The blocks in order.
        """
        blocks = []
        orig_idx = 0
        for prog_idx, prog in enumerate(self._programs):
            if isinstance(prog, Circuit):
                blocks.append(
                    _ExecutableBlock(
                        prog_idx=prog_idx,
                        param_set_index=None,
                        obs_slice=None,
                        size=1,
                        original_indices=[orig_idx],
                    )
                )
                orig_idx += 1
                continue

            num_ps = len(prog.input_sets) if prog.input_sets is not None else 1
            obs_windows = _observable_windows(
                len(prog.observables) if prog.observables is not None else 1, max_executables
            )
            split_observables = len(obs_windows) > 1
            for ps_idx in range(num_ps) if prog.input_sets is not None else [None]:
                for start, stop in obs_windows:
                    size = stop - start
                    blocks.append(
                        _ExecutableBlock(
                            prog_idx=prog_idx,
                            param_set_index=ps_idx,
                            obs_slice=slice(start, stop) if split_observables else None,
                            size=size,
                            original_indices=list(range(orig_idx, orig_idx + size)),
                        )
                    )
                    orig_idx += size
        return blocks

    def _build_program_set(self, blocks: list[_ExecutableBlock]) -> tuple[ProgramSet, list[int]]:
        entries = []
        sub_map = []
        i = 0
        while i < len(blocks):
            head = blocks[i]
            prog = self._programs[head.prog_idx]
            if head.param_set_index is None:
                entries.append(_apply_obs_slice(prog, head.obs_slice))
                sub_map.extend(head.original_indices)
                i += 1
                continue

            j = i
            while (
                j + 1 < len(blocks)
                and blocks[j + 1].prog_idx == head.prog_idx
                and blocks[j + 1].obs_slice == blocks[j].obs_slice
                and blocks[j + 1].param_set_index == blocks[j].param_set_index + 1
            ):
                j += 1
            start = head.param_set_index
            stop = blocks[j].param_set_index + 1
            entries.append(
                CircuitBinding(
                    prog.circuit,
                    input_sets=prog.input_sets.as_list()[start:stop],
                    observables=_slice_observables(prog.observables, head.obs_slice),
                )
            )
            for k in range(i, j + 1):
                sub_map.extend(blocks[k].original_indices)
            i = j + 1
        return ProgramSet(entries, self._shots_per_executable), sub_map

    @staticmethod
    def zip(
        circuits: Sequence[Circuit] | CircuitBinding,
        *,
        input_sets: Sequence[Mapping[str, float]] | None = None,
        observables: Sequence[Observable | None] | None = None,
        shots_per_executable: int | None = None,
    ) -> ProgramSet:
        """
        Constructs a batch of circuits from a list of circuits and optionally an input set and/or
        observable for each; alternatively, a single CircuitBinding can be provided and paired
        with corresponding observables.

        Args:
            circuits (Sequence[Circuit] | CircuitBinding): The parametrized circuit with parameters
                or set of fixed circuits to run with multiple observables.
            input_sets (Sequence[Mapping[str, float]] | None): The inputs to the circuit;
                must match number of circuits if provided.
                Must be empty if circuits is a CircuitBinding.
            observables (Sequence[Observable | None]| None): A set of observables to measure
                with the circuits; must match number of circuits if provided.
            shots_per_executable (int | None): The number of shots to run each executable;
                this will be used to enforce the total shots on task creation. If not provided,
                the only validation at task creation will be divisibility by number of executables.

        Returns:
            ProgramSet: a program set consisting of matching sets of
            circuits, inputs and observables.
        """
        if isinstance(circuits, CircuitBinding):
            return _zip_circuit_bindings(circuits, input_sets, observables, shots_per_executable)
        return _zip_circuits(circuits, input_sets, observables, shots_per_executable)

    @staticmethod
    def product(
        circuits: Sequence[Circuit | CircuitBinding],
        observables: Sum | Sequence[Observable],
        shots_per_executable: int | None = None,
    ) -> ProgramSet:
        """
        Constructs a program set from the Cartesian product of the given observables with the given
        circuits or bindings.

        If an entry of the list is a single circuit, then the resulting program will consist of that
        circuit and all the observables; if an entry is a circuit binding, then the result program
        will be the Cartesian product of the binding's input values and observables.

        Args:
            circuits (Sequence[Circuit] | CircuitBinding): The parametrized circuit with parameters
                or set of fixed circuits to run with multiple observables.
            observables (Sum | Sequence[Observable]): A set of observables to measure
                with the circuits.
            shots_per_executable (int | None): The number of shots to run each executable;
                this will be used to enforce the total shots on task creation. If not provided,
                the only validation at task creation will be divisibility by number of executables.

        Returns:
            ProgramSet: a program set consisting of Cartesian products of the given observables
            with the given circuits or bindings.
        """
        if not observables:
            raise ValueError("Observables must be specified")
        programs = []
        for circuit in circuits:
            if isinstance(circuit, CircuitBinding):
                if circuit.observables:
                    raise ValueError(
                        "Cannot specify observables in both circuit bindings and product"
                    )
                programs.append(CircuitBinding(circuit.circuit, circuit.input_sets, observables))
            else:
                programs.append(CircuitBinding(circuit, input_sets=None, observables=observables))
        return ProgramSet(programs, shots_per_executable)

    def __len__(self):
        return len(self._programs)

    def __getitem__(self, item: int):
        return self._programs[item]

    def __add__(self, other: ProgramSet | list):
        if isinstance(other, ProgramSet):
            if (
                self._shots_per_executable == other._shots_per_executable
                or other._shots_per_executable is None
            ):
                return ProgramSet(self._programs + other._programs, self._shots_per_executable)
            if self._shots_per_executable is None:
                return ProgramSet(self._programs + other._programs, other._shots_per_executable)
            raise ValueError("Mismatched shots per executable")
        if isinstance(other, list):
            return ProgramSet(self._programs + other, self._shots_per_executable)
        raise TypeError(f"Cannot add type {type(other)} to ProgramSet")

    def __eq__(self, other: ProgramSet):
        if not isinstance(other, ProgramSet):
            return False
        return (
            self._programs == other._programs
            and self._shots_per_executable == other._shots_per_executable
        )

    def __repr__(self):
        return (
            f"ProgramSet(programs={self._programs}, "
            f"shots_per_executable={self._shots_per_executable})"
        )


@dataclass
class _ExecutableBlock:
    """Multi-index range for an equivalence class of executables sharing the same combination of
    ``(circuit, observable list/Sum Hamiltonian, single parameter assignment)``.

    Attributes:
        prog_idx: Index of the originating program in ``ProgramSet.entries``.
        param_set_index: Index into the originating ``CircuitBinding``'s ``input_sets``, or ``None``
            for ``Circuit`` entries and ``CircuitBinding``s with no input sets.
        obs_slice: Slice into the originating observable list or ``Sum`` summands when observables
            were split to fit the budget; ``None`` means the full original observable list
            (or no observables).
        size: Number of executables this block represents (== ``len(original_indices)``).
        original_indices: The indices of this block's executables
            in the order of the original program set.
    """

    prog_idx: int
    param_set_index: int | None
    obs_slice: slice | None
    size: int
    original_indices: list[int]


def _observable_windows(num_observables: int, max_executables: int) -> list[tuple[int, int]]:
    if num_observables <= max_executables:
        return [(0, num_observables)]
    windows = []
    start = 0
    while start < num_observables:
        stop = min(start + max_executables, num_observables)
        windows.append((start, stop))
        start = stop
    return windows


def _slice_observables(
    observables: Sum | Sequence[Observable] | None, obs_slice: slice | None
) -> Sum | Sequence[Observable] | None:
    if obs_slice is None or observables is None:
        return observables
    if isinstance(observables, Sum):
        return Sum(list(observables.summands)[obs_slice])
    return list(observables)[obs_slice]


def _apply_obs_slice(
    prog: CircuitBinding | Circuit, obs_slice: slice | None
) -> CircuitBinding | Circuit:
    if obs_slice is None or isinstance(prog, Circuit) or prog.observables is None:
        return prog
    return CircuitBinding(
        prog.circuit,
        input_sets=prog.input_sets,
        observables=_slice_observables(prog.observables, obs_slice),
    )


def _zip_circuit_bindings(
    circuit_binding: CircuitBinding,
    input_sets: Sequence[Mapping[str, float]] | None,
    observables: Sequence[Observable | None] | None,
    shots_per_executable: int | None,
) -> ProgramSet:
    circuit = circuit_binding.circuit
    if circuit_binding.observables:
        if isinstance(circuit_binding.observables, Sum):
            raise TypeError("Cannot zip with Sum observable")
        if observables:
            raise ValueError("Cannot specify observables in both circuit bindings and zip")
        if not input_sets:
            raise ValueError("Must specify input sets")
        if len(circuit_binding.observables) != len(input_sets):
            raise ValueError("Number of observables must match number of input sets")
        return ProgramSet(
            [
                CircuitBinding(circuit, [input_set], [observable])
                for input_set, observable in zip(
                    input_sets, circuit_binding.observables, strict=True
                )
            ],
            shots_per_executable,
        )
    if input_sets:
        raise ValueError("Cannot specify input sets in both circuit bindings and zip")
    if not observables:
        raise ValueError("Must specify observables")
    if any(isinstance(obs, Sum) for obs in observables):
        raise TypeError("Cannot have Sum Hamiltonian in list of observables")
    if len(circuit_binding.input_sets) != len(observables):
        raise ValueError("Number of observables must match number of input sets")
    inputs_list = circuit_binding.input_sets.as_list()
    return ProgramSet(
        [
            CircuitBinding(circuit, [input_set], [observable])
            for input_set, observable in zip(inputs_list, observables, strict=True)
        ],
        shots_per_executable,
    )


def _zip_circuits(
    circuits: Sequence[Circuit],
    input_sets: Sequence[Mapping[str, float]] | None,
    observables: Sequence[Observable | None] | None,
    shots_per_executable: int | None,
) -> ProgramSet:
    if input_sets and observables:
        if len(circuits) != len(observables):
            raise ValueError("Number of circuits must match number of observables")
        if len(circuits) != len(input_sets):
            raise ValueError("Number of circuits must match number of input sets")
        return ProgramSet(
            [
                CircuitBinding(circuit, [input_set], [observable])
                for circuit, input_set, observable in zip(
                    circuits, input_sets, observables, strict=True
                )
            ],
            shots_per_executable,
        )
    if input_sets:
        if len(circuits) != len(input_sets):
            raise ValueError("Number of circuits must match number of input sets")
        return ProgramSet(
            [
                CircuitBinding(circuit, [input_set], None)
                for circuit, input_set in zip(circuits, input_sets, strict=True)
            ],
            shots_per_executable,
        )
    if observables:
        if len(circuits) != len(observables):
            raise ValueError("Number of circuits must match number of observables")
        return ProgramSet(
            [
                CircuitBinding(circuit, None, [observable])
                for circuit, observable in zip(circuits, observables, strict=True)
            ],
            shots_per_executable,
        )
    raise ValueError("Must specify either input sets or observables")
