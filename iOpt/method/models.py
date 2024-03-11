import enum
from typing import List

from sqlalchemy import Integer, Float, ForeignKey, String, Enum
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    DeclarativeBase,
    relationship,
)

from iOpt.trial import FunctionType


class Base(DeclarativeBase):
    pass


class FloatVariable(Base):
    __tablename__ = "float_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("points.id"))
    value: Mapped[float] = mapped_column(Float)


class DiscreteVariable(Base):
    __tablename__ = "discrete_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("points.id"))
    value: Mapped[str] = mapped_column(String)


class FunctionValue(Base):
    __tablename__ = "function_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("points.id"))
    type: Mapped[FunctionType] = mapped_column(Enum(FunctionType))
    function_id: Mapped[int] = mapped_column(Integer)
    value: Mapped[float] = mapped_column(Float)


class PointState(enum.IntEnum):
    WAITING = 0
    CALCULATING = 1
    CALCULATED = 2
    COMPLETE = 3


class Point(Base):
    __tablename__ = "points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    x: Mapped[float] = mapped_column(Float)
    index: Mapped[int] = mapped_column(Integer)
    z: Mapped[float] = mapped_column(Float)
    state: Mapped[PointState] = mapped_column(Enum(PointState))

    function_values: Mapped[List[FunctionValue]] = relationship(
        cascade="all, delete-orphan"
    )
    float_variables: Mapped[List[FloatVariable]] = relationship(
        cascade="all, delete-orphan"
    )
    discrete_variables: Mapped[List[DiscreteVariable]] = relationship(
        cascade="all, delete-orphan"
    )


class TaskState(enum.Enum):
    SOLVING = "solving"
    SOLVED = "solved"
    ERROR = "error"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[String] = mapped_column(String, unique=True)
    state: Mapped[TaskState] = mapped_column(Enum(TaskState))

    points: Mapped[List[Point]] = relationship(cascade="all, delete-orphan")
