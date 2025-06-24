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

import numpy as np
from antlr4 import CommonTokenStream, InputStream

from braket.ir.jaqcd import (
    Amplitude,
    DensityMatrix,
    Expectation,
    Probability,
    Sample,
    StateVector,
    Variance,
)
from braket.ir.jaqcd.program_v1 import Results

from .generated.BraketPragmasLexer import BraketPragmasLexer
from .generated.BraketPragmasParser import BraketPragmasParser
from .generated.BraketPragmasParserVisitor import BraketPragmasParserVisitor
from .openqasm_parser import parse


class BraketPragmaNodeVisitor(BraketPragmasParserVisitor):
    """
    This is a visitor for the BraketPragmas grammar. Consumes a
    braketPragmas AST and converts to relevant python objects
    for use by the Interpreter
    """

    def __init__(self, qubit_table: "QubitTable"):  # noqa: F821
        self.qubit_table = qubit_table

    def visitNoArgResultType(self, ctx: BraketPragmasParser.NoArgResultTypeContext) -> Results:
        result_type = ctx.noArgResultTypeName().getText()
        no_arg_result_type_map = {
            "state_vector": StateVector,
        }
        return no_arg_result_type_map[result_type]()

    def visitOptionalMultiTargetResultType(
        self, ctx: BraketPragmasParser.OptionalMultiTargetResultTypeContext
    ) -> Results:
        result_type = ctx.optionalMultiTargetResultTypeName().getText()
        optional_multitarget_result_type_map = {
            "probability": Probability,
            "density_matrix": DensityMatrix,
        }
        targets = self.visit(ctx.multiTarget()) if ctx.multiTarget() is not None else None
        return optional_multitarget_result_type_map[result_type](targets=targets)

    def visitMultiTargetIdentifiers(self, ctx: BraketPragmasParser.MultiTargetIdentifiersContext):
        parsable = f"target {''.join(x.getText() for x in ctx.getChildren())};"
        parsed_statement = parse(parsable)
        target_identifiers = parsed_statement.statements[0].qubits
        target = sum(
            (self.qubit_table.get_by_identifier(identifier) for identifier in target_identifiers),
            (),
        )
        return target

    def visitMultiTargetAll(self, ctx: BraketPragmasParser.MultiTargetAllContext):
        return

    def visitMultiStateResultType(
        self, ctx: BraketPragmasParser.MultiStateResultTypeContext
    ) -> Results:
        result_type = ctx.multiStateResultTypeName().getText()
        multistate_result_type_map = {
            "amplitude": Amplitude,
        }
        states = self.visit(ctx.getChild(1))
        return multistate_result_type_map[result_type](states=states)

    def visitMultiState(self, ctx: BraketPragmasParser.MultiStateContext) -> list[str]:
        # unquote and skip commas
        states = [x.getText()[1:-1] for x in list(ctx.getChildren())[::2]]
        return states

    def visitObservableResultType(
        self, ctx: BraketPragmasParser.ObservableResultTypeContext
    ) -> Results:
        result_type = ctx.observableResultTypeName().getText()
        observable_result_type_map = {
            "expectation": Expectation,
            "sample": Sample,
            "variance": Variance,
        }
        observables, targets = self.visit(ctx.observable())
        obs = observable_result_type_map[result_type](targets=targets, observable=observables)
        return obs

    def visitStandardObservableIdentifier(
        self,
        ctx: BraketPragmasParser.StandardObservableIdentifierContext,
    ) -> tuple[tuple[str], int]:
        observable = ctx.standardObservableName().getText()
        target_tuple = self.visit(ctx.indexedIdentifier())
        if len(target_tuple) != 1:
            raise ValueError("Standard observable target must be exactly 1 qubit.")
        return (observable,), target_tuple

    def visitStandardObservableAll(
        self,
        ctx: BraketPragmasParser.StandardObservableAllContext,
    ) -> tuple[tuple[str], None]:
        observable = ctx.standardObservableName().getText()
        return (observable,), None

    def visitTensorProductObservable(
        self, ctx: BraketPragmasParser.TensorProductObservableContext
    ) -> tuple[tuple[str], tuple[int]]:
        observables, targets = zip(
            *(self.visit(ctx.getChild(i)) for i in range(0, ctx.getChildCount(), 2))
        )
        observables = sum(observables, ())
        targets = sum(targets, ())
        return observables, targets

    def visitHermitianObservable(
        self, ctx: BraketPragmasParser.HermitianObservableContext
    ) -> tuple[tuple[list[list[float]]], int]:
        matrix = self.visit(ctx.twoDimMatrix())
        matrix = np.expand_dims(matrix, axis=-1)
        converted = np.append(matrix.real, matrix.imag, axis=-1).tolist()
        target = self.visit(ctx.multiTarget())
        return (converted,), target

    def visitIndexedIdentifier(
        self, ctx: BraketPragmasParser.IndexedIdentifierContext
    ) -> tuple[int]:
        parsable = f"target {''.join(x.getText() for x in ctx.getChildren())};"
        parsed_statement = parse(parsable)
        identifier = parsed_statement.statements[0].qubits[0]
        target = self.qubit_table.get_by_identifier(identifier)
        return target

    def visitComplexOneValue(self, ctx: BraketPragmasParser.ComplexOneValueContext) -> list[float]:
        sign = -1 if ctx.neg else 1
        value = ctx.value.text
        imag = False
        if value.endswith("im"):
            value = value[:-2]
            imag = True
        complex_array = [0, 0]
        complex_array[imag] = sign * float(value)
        return complex_array

    def visitComplexTwoValues(
        self, ctx: BraketPragmasParser.ComplexTwoValuesContext
    ) -> list[float]:
        real = float(ctx.real.text)
        imag = float(ctx.imag.text[:-2])  # exclude "im"
        if ctx.neg:
            real *= -1
        if ctx.imagNeg:
            imag *= -1
        if ctx.sign.text == "-":
            imag *= -1
        return [real, imag]

    def visitBraketUnitaryPragma(
        self, ctx: BraketPragmasParser.BraketUnitaryPragmaContext
    ) -> tuple[np.ndarray, tuple[int]]:
        target = self.visit(ctx.multiTarget())
        matrix = self.visit(ctx.twoDimMatrix())
        return matrix, target

    def visitRow(self, ctx: BraketPragmasParser.RowContext) -> list[complex]:
        numbers = ctx.children[1::2]
        return [x[0] + x[1] * 1j for x in [self.visit(number) for number in numbers]]

    def visitTwoDimMatrix(self, ctx: BraketPragmasParser.TwoDimMatrixContext) -> np.ndarray:
        rows = [self.visit(row) for row in ctx.children[1::2]]
        if not all(len(r) == len(rows) for r in rows):
            raise TypeError("Not a valid square matrix")
        matrix = np.array(rows)
        return matrix

    def visitNoise(self, ctx: BraketPragmasParser.NoiseContext):
        target = self.visit(ctx.target)
        probabilities = self.visit(ctx.probabilities())
        noise_instruction = ctx.noiseInstructionName().getText()
        return noise_instruction, target, probabilities

    def visitKraus(self, ctx: BraketPragmasParser.KrausContext):
        target = self.visit(ctx.target)
        matrices = [self.visit(m) for m in ctx.matrices().children[::2]]
        return matrices, target

    def visitProbabilities(self, ctx: BraketPragmasParser.ProbabilitiesContext):
        return [float(prob.symbol.text) for prob in ctx.children[::2]]


def parse_braket_pragma(pragma_body: str, qubit_table: "QubitTable"):  # noqa: F821
    """Parse braket pragma and return relevant information.

    Pragma types include:
      - result types
      - custom unitary operations
    """
    data = InputStream(pragma_body)
    lexer = BraketPragmasLexer(data)
    stream = CommonTokenStream(lexer)
    parser = BraketPragmasParser(stream)
    tree = parser.braketPragma()
    visited = BraketPragmaNodeVisitor(qubit_table).visit(tree)
    return visited
