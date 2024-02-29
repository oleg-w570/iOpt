from typing import Tuple

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

import iOpt.method.models as m
from iOpt.method.search_data import SearchData, SearchDataItem
from iOpt.problem import Problem
from iOpt.trial import FunctionValue, Point


class SearchDB(SearchData):
    def __init__(self, url: str, problem: Problem, maxlen: int = None):
        super().__init__(problem, maxlen)
        self.engine = create_engine(url)
        self.session_maker = sessionmaker(bind=self.engine)
        m.Base.metadata.drop_all(self.engine)  # temp
        m.Base.metadata.create_all(self.engine)

    def count_not_calculated_points(self) -> int:
        with self.session_maker() as session:
            return (
                session.query(func.count(m.SearchDataItem.id))
                .filter(m.SearchDataItem.state < m.SearchDataItem.State.CALCULATED)
                .scalar()
            )

    def set_point_to_calculate(self, point: SearchDataItem) -> None:
        with self.session_maker() as session:
            db_point = m.SearchDataItem(
                state=m.SearchDataItem.State.WAITING,
                x=point.get_x(),
                index=point.get_index(),
                z=point.get_z(),
            )
            session.add(db_point)
            session.flush()

            float_variables = [
                m.FloatVariable(point_id=db_point.id, value=var)
                for var in point.point.float_variables
            ]
            session.add_all(float_variables)

            discrete_variables = [
                m.DiscreteVariable(point_id=db_point.id, value=var)
                for var in point.point.discrete_variables
            ]
            session.add_all(discrete_variables)

            session.commit()

    def get_point_to_calculate(self, n_func: int) -> Tuple[SearchDataItem, int]:
        with self.session_maker() as session:
            db_point = (
                session.query(m.SearchDataItem)
                .filter(m.SearchDataItem.state == m.SearchDataItem.State.WAITING)
                .first()
            )
            db_point.state = m.SearchDataItem.State.CALCULATING
            session.commit()

            point = SearchDataItem(
                Point(
                    [var.value for var in db_point.float_variables],
                    [var.value for var in db_point.discrete_variables],
                ),
                db_point.x,
                [FunctionValue()] * n_func,
            )
            point.set_index(db_point.index)
            point.set_z(db_point.z)
            return point, db_point.id

    def set_calculated_point(self, point: SearchDataItem, db_point_id: int) -> None:
        with self.session_maker() as session:
            db_point = session.query(m.SearchDataItem).get(db_point_id)
            db_point.index = point.get_index()
            db_point.z = point.get_z()
            db_point.state = m.SearchDataItem.State.CALCULATED
            function_values = [
                m.FunctionValue(
                    point_id=db_point_id,
                    type=fv.type,
                    function_id=fv.functionID,
                    value=fv.value,
                )
                for fv in point.function_values
            ]
            session.add_all(function_values)
            session.commit()

    def get_calculated_point(self) -> SearchDataItem:
        with self.session_maker() as session:
            db_point = (
                session.query(m.SearchDataItem)
                .filter(m.SearchDataItem.state == m.SearchDataItem.State.CALCULATED)
                .first()
            )
            db_point.state = m.SearchDataItem.State.COMPLETE
            session.commit()

            point = SearchDataItem(
                Point(
                    [var.value for var in db_point.float_variables],
                    [var.value for var in db_point.discrete_variables],
                ),
                db_point.x,
                [
                    FunctionValue(fv.type, fv.function_id, fv.value)
                    for fv in db_point.function_values
                ],
            )
            point.set_index(db_point.index)
            point.set_z(db_point.z)
            return point
