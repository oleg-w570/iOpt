from iOpt.method.process import Process


class DBProcess(Process):
    def do_global_iteration(self, number: int = 1):
        if self._first_iteration is True:
            for listener in self._listeners:
                listener.before_method_start(self.method)
            done_trials = self.method.first_iteration()
            self._first_iteration = False
        else:
            # вычисляем следующие точки и сохраняем в БД, чтобы рабочий процесс вычислил значения их функций
            # нужно будет добавить связь между newpoint и oldpoint
            for _ in range(
                self.parameters.number_of_parallel_points
                - self.search_data.count_not_calculated_points()
            ):
                newpoint, oldpoint = self.method.calculate_iteration_point()
                self.search_data.set_point_to_calculate(newpoint)

            # эта часть будет выполняться на рабочем процессе
            point, db_point_id = self.search_data.get_point_to_calculate(
                self.method.numberOfAllFunctions
            )
            self.method.calculate_functionals(point)
            self.search_data.set_calculated_point(point, db_point_id)

            # после основной процесс собирает посчитанные точки
            newpoint = self.search_data.get_calculated_point()
            self.method.update_optimum(newpoint)
            self.method.renew_search_data(newpoint, oldpoint)
            self.method.finalize_iteration()
            done_trials = self.search_data.get_last_items()

        for listener in self._listeners:
            listener.on_end_iteration(done_trials, self.get_results())
