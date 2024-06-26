import io
from abc import ABC, abstractmethod

from braket.emulators.pytket_translator.qasm3_gen.qasm_context import Gate, QasmContext
from braket.emulators.pytket_translator.translations import MEASUREMENT_REGISTER_NAME


class QasmWriter(ABC):
    """Abstract class for OpenQASM program writing. It handles basic program writing flow,
    but methods can be overwritten by subclasses to modify output behavior.
    """

    def __init__(self, context: QasmContext):
        """
        Initialize a new QasmWriter from a context containing program information.
        The writer does not modify the context.
        """
        self.context = context

    def get_program(self) -> str:
        """
        Return the OpenQASM 3.0 program program string from the constructor argument
        ProgramContext.

        Returns:
            str: A complete OpenQASM 3.0 program string.
        """
        stream = io.StringIO()
        stream.write(self.get_program_header())
        stream.write(self.get_input_declarations())
        stream.write(self.get_classical_bit_declarations())
        # stream.write(self.get_verbatim_pragma())
        # stream.write(self.get_boxed_program_body())
        stream.write(self.get_body())
        stream.write(self.get_measurements())
        return stream.getvalue()

    def get_program_header(self) -> str:
        return "OPENQASM 3.0;\n"

    @abstractmethod
    def get_input_declarations(self) -> str:
        """Return input declaration statements.

        For example:
            "input float theta;\ninput float alpha;\n"
        """

    def get_classical_bit_declarations(self) -> str:
        return (
            f"bit[{self.context.num_bits}] {MEASUREMENT_REGISTER_NAME};\n"
            if self.context.num_bits
            else ""
        )

    def get_verbatim_pragma(self) -> str:
        return "#pragma braket verbatim\n"

    def get_boxed_program_body(self) -> str:
        return f"box {{\n{self.get_body()}}}\n"

    def get_body(self) -> str:
        """
        Creates an OpenQASM 3.0 program body from the program operations and
        returns a string containing the program body.

        Returns:
            str: the OpenQASM 3.0 program body.
        """
        stream = io.StringIO()
        for gate in self.context.gates:
            stream.write(self.get_gate(gate))
        return stream.getvalue()

    def get_gate(self, gate: Gate) -> str:
        return f"{gate.name}{self.get_gate_args(gate)} {self.get_gate_qubits(gate)};\n"

    @abstractmethod
    def get_gate_args(self, gate: Gate) -> str:
        """Return gate arguments.

        For example:
            "0.5,pi*theta"
        """

    def get_gate_qubits(self, gate: Gate) -> str:
        return ",".join(self.format_qubit(q) for q in gate.qubits)

    def get_measurements(self) -> str:
        return "\n".join(
            f"{meas.bit} = measure {self.format_qubit(meas.qubit)};"
            for meas in self.context.measurements
        )

    def format_qubit(self, qubit: int) -> str:
        return f"${qubit}"


class BasicQasmWriter(QasmWriter):
    """This writer returns human-readable, basic OpenQASM.

    For example:

        OPENQASM 3.0;
        input angle theta;
        bit[1] c;
        #pragma braket verbatim
        box {
        rx(pi*theta) $0;
        }
        c[0] = measure $0;

    """

    def get_input_declarations(self) -> str:
        """
        Creates parameter declarations for program inputs (e.g. theta, phi).
        Parameters are assumed to all be of type float.

        Returns:
            str: OpenQASM 3.0 lines with paramater variable declarations.
        """
        stream = io.StringIO()
        for param_name, param_type in self.context.input_parameters.items():
            stream.write(f"input {param_type} {param_name};\n")
        return stream.getvalue()

    def get_gate_args(self, gate: Gate) -> str:
        return f"({','.join(str(arg) for arg in gate.args)})" if gate.args else ""
