import numpy as np
from enum import Enum


class FunctionType(Enum):
    OBJECTIV = 1
    CONSTRAINT = 2


class Point:
    def __init__(self,
                 float_variables: np.ndarray(shape=(1), dtype=np.double),
                 discrete_variables: np.ndarray(shape=(1), dtype=str) = [],
                 ):
        self.float_variables = float_variables
        self.discrete_variables = discrete_variables


class FunctionValue:
    def __init__(self,
                 type: FunctionType = FunctionType.OBJECTIV,
                 functionID: int = 0,
                 value: float = 0
                 ):
        self.type = type
        self.functionID = functionID
        self.value = value


class Trial:
    def __init__(self,
                 point: Point,
                 function_values: np.ndarray(shape=(1), dtype=FunctionValue)
                 ):
        self.point = point
        self.function_values = function_values
