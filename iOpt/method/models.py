from typing import List

from sqlalchemy import Integer, Float, ForeignKey, String, Enum
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship

from iOpt.trial import FunctionType


class BaseModel(DeclarativeBase):
    pass


class FloatVariableModel(BaseModel):
    __tablename__ = "float_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_data_id: Mapped[int] = mapped_column(ForeignKey("search_data.id"))
    value: Mapped[float] = mapped_column(Float)


class DiscreteVariableModel(BaseModel):
    __tablename__ = "discrete_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_data_id: Mapped[int] = mapped_column(ForeignKey("search_data.id"))
    value: Mapped[str] = mapped_column(String)


class FunctionValueModel(BaseModel):
    __tablename__ = "function_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_data_id: Mapped[int] = mapped_column(ForeignKey("search_data.id"))
    type: Mapped[FunctionType] = mapped_column(Enum(FunctionType))
    function_id: Mapped[int] = mapped_column(Integer)
    value: Mapped[float] = mapped_column(Float)


class SearchDataModel(BaseModel):
    __tablename__ = "search_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    x: Mapped[float] = mapped_column(Float)

    function_values: Mapped[List[FunctionValueModel]] = relationship()
    float_variables: Mapped[List[FloatVariableModel]] = relationship()
    discrete_variables: Mapped[List[DiscreteVariableModel]] = relationship()
