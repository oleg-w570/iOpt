import logging
from time import sleep
from typing import Tuple, List

from sqlalchemy import func, create_engine, update, select, delete
from sqlalchemy.orm import sessionmaker

import iOpt.method.models as models
from iOpt.method.search_data import SearchDataItem
from iOpt.solver_parametrs import SolverParameters
from iOpt.trial import FunctionValue, Point

WAIT_TIME = 1
MAX_ATTEMPTS = 3


class DBManager:
    def __init__(self, parameters: SolverParameters):
        self.engine = create_engine(parameters.url_db)
        self.session_maker = sessionmaker(bind=self.engine)
        if not parameters.is_worker:
            models.Base.metadata.create_all(self.engine)
            self.task_id = self.create_task(parameters.task_name)
        else:
            self.task_id = self.load_task(parameters.task_name)

    def create_task(self, name: str) -> int:
        with self.session_maker() as session:
            task = models.Task(name=name, state=models.TaskState.SOLVING)
            session.add(task)
            session.commit()
            return task.id

    def find_task_by_name(self, name: str) -> int:
        with self.session_maker() as session:
            task = session.execute(
                select(models.Task).where(models.Task.name == name)
            ).scalar_one()
            return task.id

    def load_task(self, name: str) -> int:
        for attempt in range(MAX_ATTEMPTS):
            try:
                return self.find_task_by_name(name)
            except Exception:
                logging.info(f"Attempt {attempt+1} failed with error")
                if attempt < MAX_ATTEMPTS - 1:
                    sleep(WAIT_TIME)
        else:
            raise Exception(f"Failed to find record after {MAX_ATTEMPTS} attempts")

    def set_task_solved(self) -> None:
        with self.session_maker() as session:
            session.execute(
                update(models.Task)
                .where(models.Task.id == self.task_id)
                .values(state=models.TaskState.SOLVED)
            )
            session.commit()

    def set_task_error(self) -> None:
        with self.session_maker() as session:
            session.execute(
                update(models.Task)
                .where(models.Task.id == self.task_id)
                .values(state=models.TaskState.ERROR)
            )
            session.commit()

    def is_task_solving(self) -> bool:
        with self.session_maker() as session:
            state = session.scalar(
                select(models.Task.state).where(models.Task.id == self.task_id)
            )
            return state == models.TaskState.SOLVING

    def delete_task(self) -> None:
        with self.session_maker() as session:
            session.execute(delete(models.Task).where(models.Task.id == self.task_id))
            session.commit()

    def count_not_calculated_points(self) -> int:
        with self.session_maker() as session:
            return session.scalar(
                select(func.count())
                .select_from(models.Point)
                .where(models.Point.state < models.PointState.CALCULATED)
            )

    def set_point_to_calculate(self, point: SearchDataItem) -> int:
        with self.session_maker() as session:
            db_point = models.Point(
                task_id=self.task_id,
                state=models.PointState.WAITING,
                x=point.get_x(),
                index=point.get_index(),
                z=point.get_z(),
                float_variables=[
                    models.FloatVariable(value=var)
                    for var in point.point.float_variables
                ],
                discrete_variables=[
                    models.DiscreteVariable(value=var)
                    for var in point.point.discrete_variables
                ],
            )
            session.add(db_point)
            session.commit()
            return db_point.id

    def get_point_to_calculate(
        self, n_func: int
    ) -> Tuple[SearchDataItem, int] | Tuple[None, None]:
        with self.session_maker() as session:
            db_point = session.scalars(
                select(models.Point)
                .where(models.Point.task_id == self.task_id)
                .where(models.Point.state == models.PointState.WAITING)
                .with_for_update(skip_locked=True)
                .limit(1)
            ).first()
            if db_point is None:
                return None, None
            db_point.state = models.PointState.CALCULATING
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
            session.add_all(
                [
                    models.FunctionValue(
                        point_id=db_point_id,
                        type=fv.type,
                        function_id=fv.functionID,
                        value=fv.value,
                    )
                    for fv in point.function_values
                ]
            )
            session.execute(
                update(models.Point)
                .where(models.Point.id == db_point_id)
                .values(
                    index=point.get_index(),
                    z=point.get_z(),
                    state=models.PointState.CALCULATED,
                )
            )
            session.commit()

    def get_calculated_point(self) -> Tuple[SearchDataItem, int]:
        with self.session_maker() as session:
            db_point = session.scalars(
                select(models.Point)
                .where(models.Point.task_id == self.task_id)
                .where(models.Point.state == models.PointState.CALCULATED)
                .limit(1)
            ).first()
            db_point.state = models.PointState.COMPLETE
            session.commit()
            return self._convert_db_point(db_point)

    def get_all_calculated_points(self) -> List[Tuple[SearchDataItem, int]]:
        with self.session_maker() as session:
            list_db_points = session.scalars(
                select(models.Point)
                .where(models.Point.task_id == self.task_id)
                .where(models.Point.state == models.PointState.CALCULATED)
            ).all()
            for db_point in list_db_points:
                db_point.state = models.PointState.COMPLETE
            session.commit()
            return list(map(self._convert_db_point, list_db_points))

    @staticmethod
    def _convert_db_point(db_point: models.Point) -> Tuple[SearchDataItem, int]:
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
        return point, db_point.id

    def calculate_functionals_for_items(
        self, points: List[SearchDataItem]
    ) -> List[SearchDataItem]:
        t = {}
        for point in points:
            point_id = self.set_point_to_calculate(point)
            t[point_id] = point
        while self.count_not_calculated_points() > 0:
            ...
        points_res = self.get_all_calculated_points()
        for point_r, point_id in points_res:
            point = t[point_id]
            point.function_values = point_r.function_values
            point.set_z(point_r.get_z())
            point.set_index(point_r.get_index())
        return points
