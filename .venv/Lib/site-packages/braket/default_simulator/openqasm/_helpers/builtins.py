import math
from enum import Enum
from typing import Optional, Union

import numpy as np
import sympy

from braket.default_simulator.openqasm._helpers.casting import cast_to
from braket.default_simulator.openqasm.parser.openqasm_ast import (
    ArrayLiteral,
    BitstringLiteral,
    FloatLiteral,
    IntegerLiteral,
    SymbolLiteral,
    UintType,
)


class BuiltinConstants(Enum):
    PI = SymbolLiteral(sympy.pi)
    TAU = SymbolLiteral(2 * sympy.pi)
    E = SymbolLiteral(sympy.E)


class BuiltinFunctions:
    @staticmethod
    def sizeof(array: ArrayLiteral, dim: Optional[IntegerLiteral] = None) -> IntegerLiteral:
        return (
            IntegerLiteral(len(array.values))
            if dim is None or dim.value == 0
            else BuiltinFunctions.sizeof(array.values[0], IntegerLiteral(dim.value - 1))
        )

    @staticmethod
    def arccos(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.acos(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.arccos(x.value))
        )

    @staticmethod
    def arcsin(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.asin(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.arcsin(x.value))
        )

    @staticmethod
    def arctan(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.atan(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.arctan(x.value))
        )

    @staticmethod
    def ceiling(x: Union[FloatLiteral, SymbolLiteral]) -> Union[IntegerLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.ceiling(x.value))
            if isinstance(x, SymbolLiteral)
            else IntegerLiteral(math.ceil(x.value))
        )

    @staticmethod
    def cos(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.cos(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.cos(x.value))
        )

    @staticmethod
    def exp(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.exp(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.exp(x.value))
        )

    @staticmethod
    def floor(x: Union[FloatLiteral, SymbolLiteral]) -> Union[IntegerLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.floor(x.value))
            if isinstance(x, SymbolLiteral)
            else IntegerLiteral(np.floor(x.value))
        )

    @staticmethod
    def log(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.log(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.log(x.value))
        )

    @staticmethod
    def mod(
        x: Union[IntegerLiteral, FloatLiteral, SymbolLiteral],
        y: Union[IntegerLiteral, FloatLiteral, SymbolLiteral],
    ) -> Union[IntegerLiteral, FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(x.value % y.value)
            if isinstance(x, SymbolLiteral) or isinstance(y, SymbolLiteral)
            else (
                IntegerLiteral(x.value % y.value)
                if isinstance(x, IntegerLiteral) and isinstance(y, IntegerLiteral)
                else FloatLiteral(x.value % y.value)
            )
        )

    @staticmethod
    def popcount(x: Union[IntegerLiteral, BitstringLiteral, ArrayLiteral]) -> IntegerLiteral:
        # does not support symbols or expressions
        return IntegerLiteral(np.binary_repr(cast_to(UintType(), x).value).count("1"))

    @staticmethod
    def pow(
        x: Union[IntegerLiteral, FloatLiteral, SymbolLiteral],
        y: Union[IntegerLiteral, FloatLiteral, SymbolLiteral],
    ) -> Union[IntegerLiteral, FloatLiteral, SymbolLiteral]:
        # parser gets confused by pow, mistaking for quantum modifier
        return (
            SymbolLiteral(x.value**y.value)
            if isinstance(x, SymbolLiteral) or isinstance(y, SymbolLiteral)
            else (
                IntegerLiteral(x.value**y.value)
                if isinstance(x, IntegerLiteral) and isinstance(y, IntegerLiteral)
                else FloatLiteral(x.value**y.value)
            )
        )

    @staticmethod
    def rotl(x, y):
        raise NotImplementedError

    @staticmethod
    def rotr(x, y):
        raise NotImplementedError

    @staticmethod
    def sin(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.sin(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.sin(x.value))
        )

    @staticmethod
    def sqrt(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.sqrt(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.sqrt(x.value))
        )

    @staticmethod
    def tan(x: Union[FloatLiteral, SymbolLiteral]) -> Union[FloatLiteral, SymbolLiteral]:
        return (
            SymbolLiteral(sympy.tan(x.value))
            if isinstance(x, SymbolLiteral)
            else FloatLiteral(np.tan(x.value))
        )
