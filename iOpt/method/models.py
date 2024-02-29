import enum
from typing import List

from sqlalchemy import Integer, Float, ForeignKey, String, Enum
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship

from iOpt.trial import FunctionType


class Base(DeclarativeBase):
    pass


class FloatVariable(Base):
    __tablename__ = "float_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("search_data.id"))
    value: Mapped[float] = mapped_column(Float)


class DiscreteVariable(Base):
    __tablename__ = "discrete_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("search_data.id"))
    value: Mapped[str] = mapped_column(String)


class FunctionValue(Base):
    __tablename__ = "function_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("search_data.id"))
    type: Mapped[FunctionType] = mapped_column(Enum(FunctionType))
    function_id: Mapped[int] = mapped_column(Integer)
    value: Mapped[float] = mapped_column(Float)


class SearchDataItem(Base):
    __tablename__ = "search_data"

    class State(enum.IntEnum):
        WAITING = 0
        CALCULATING = 1
        CALCULATED = 2
        COMPLETE = 3

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    x: Mapped[float] = mapped_column(Float)
    index: Mapped[int] = mapped_column(Integer)
    z: Mapped[float] = mapped_column(Float)
    state: Mapped[State] = mapped_column(Enum(State))

    function_values: Mapped[List[FunctionValue]] = relationship()
    float_variables: Mapped[List[FloatVariable]] = relationship()
    discrete_variables: Mapped[List[DiscreteVariable]] = relationship()
