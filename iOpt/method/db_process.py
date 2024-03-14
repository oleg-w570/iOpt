import traceback
from datetime import datetime
from typing import List

from iOpt.evolvent.evolvent import Evolvent
from iOpt.method.db_manager import DBManager
from iOpt.method.listener import Listener
from iOpt.method.method import Method
from iOpt.method.optim_task import OptimizationTask
from iOpt.method.process import Process
from iOpt.method.search_data import SearchData, SearchDataItem
from iOpt.solution import Solution
from iOpt.solver_parametrs import SolverParameters


class DBProcess(Process):
    def __init__(
        self,
        parameters: SolverParameters,
        task: OptimizationTask,
        evolvent: Evolvent,
        search_data: SearchData,
        method: Method,
        listeners: List[Listener],
        db_manager: DBManager,
    ):
        super().__init__(parameters, task, evolvent, search_data, method, listeners)
        self.db = db_manager
        self.waiting_oldpoints = {}

    def save_oldpoint(self, oldpoint: SearchDataItem, db_newpoint_id: int):
        self.waiting_oldpoints[db_newpoint_id] = oldpoint
        oldpoint.blocked = True

    def find_oldpoint(self, db_newpoint_id: int) -> SearchDataItem:
        oldpoint = self.waiting_oldpoints.pop(db_newpoint_id)
        oldpoint.blocked = False
        return oldpoint

    def do_global_iteration(self, number: int = 1):
        done_trials = []
        if self._first_iteration is True:
            for listener in self._listeners:
                listener.before_method_start(self.method)
            done_trials = self.method.first_iteration(self.db)
            self._first_iteration = False
        else:
            for _ in range(
                self.parameters.number_of_parallel_points
                - len(self.waiting_oldpoints)
            ):
                newpoint, oldpoint = self.method.calculate_iteration_point()
                db_newpoint_id = self.db.set_point_to_calculate(newpoint)
                self.save_oldpoint(oldpoint, db_newpoint_id)

            for newpoint, db_newpoint_id in self.db.get_all_calculated_points():
                oldpoint = self.find_oldpoint(db_newpoint_id)
                self.method.update_optimum(newpoint)
                self.method.renew_search_data(newpoint, oldpoint)
                self.method.finalize_iteration()
                done_trials.append(newpoint)

        for listener in self._listeners:
            listener.on_end_iteration(done_trials, self.get_results())

    def solve(self) -> Solution:
        start_time = datetime.now()

        try:
            while not self.method.check_stop_condition():
                self.do_global_iteration()
            self.db.set_task_solved()
        except Exception:
            self.db.set_task_error()
            print("Exception was thrown")
            print(traceback.format_exc())

        if self.parameters.refine_solution:
            self.do_local_refinement(self.parameters.local_method_iteration_count)

        result = self.get_results()
        result.solving_time += (datetime.now() - start_time).total_seconds()

        for listener in self._listeners:
            status = self.method.check_stop_condition()
            listener.on_method_stop(self.search_data, self.get_results(), status)

        return result


class DBProcessWorker(Process):
    def __init__(
        self,
        parameters: SolverParameters,
        task: OptimizationTask,
        evolvent: Evolvent,
        search_data: SearchData,
        method: Method,
        listeners: List[Listener],
        db_manager: DBManager
    ):
        super().__init__(parameters, task, evolvent, search_data, method, listeners)
        self.db = db_manager

    def do_global_iteration(self, number: int = 1):
        point, db_point_id = self.db.get_point_to_calculate(
            self.method.numberOfAllFunctions
        )
        if point and db_point_id:
            self.method.calculate_functionals(point)
            self.db.set_calculated_point(point, db_point_id)

    def solve(self) -> Solution:
        while self.db.is_task_solving():
            self.do_global_iteration()
        return self.get_results()
