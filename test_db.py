import xml.etree.ElementTree as ET

import numpy as np

from examples.Genetic_algorithm.TSP._2D.Problems.ga_tsp_2d import GA_TSP_2D
from iOpt.solver import Solver
from iOpt.solver_parametrs import SolverParameters


URL_DB = 'postgresql://postgres:12345@localhost:5432/iopt_db'


def load_tsp_matrix(file_name):
    root = ET.parse(file_name).getroot()
    columns = root.findall('graph/vertex')
    num_cols = len(columns)
    trans_matrix = np.zeros((num_cols, num_cols))
    for i, v in enumerate(columns):
        for e in v:
            j = int(e.text)
            trans_matrix[i, j] = float(e.get('cost'))
    return trans_matrix


if __name__ == "__main__":
    tsp_matrix = load_tsp_matrix('examples/Genetic_algorithm/TSP/TSPs_matrices/a280.xml')
    num_iteration = 200
    mutation_probability_bound = {'low': 0.0, 'up': 1.0}
    population_size_bound = {'low': 10.0, 'up': 100.0}
    problem = GA_TSP_2D(tsp_matrix, num_iteration, mutation_probability_bound, population_size_bound)
    params = SolverParameters(
        r=np.double(4.0),
        iters_limit=200,
        number_of_parallel_points=4,
        url_db=URL_DB,
        task_name='tsp',
    )
    solver = Solver(problem, params)
    solution = solver.solve()
    print(solution)
