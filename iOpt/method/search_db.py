from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from iOpt.method.models import (
    BaseModel,
    SearchDataModel,
    FloatVariableModel,
    DiscreteVariableModel,
    FunctionValueModel,
)
from iOpt.method.search_data import SearchData, SearchDataItem
from iOpt.problem import Problem


def item_to_model(data_item: SearchDataItem) -> SearchDataModel:
    data_model = SearchDataModel(x=data_item.get_x(), z=data_item.get_z())
    return data_model


class SearchDB(SearchData):
    def __init__(self, url: str, problem: Problem, maxlen: int = None):
        super().__init__(problem, maxlen)
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)
        BaseModel.metadata.drop_all(self.engine)  # temp
        BaseModel.metadata.create_all(self.engine)

    @staticmethod
    def add_to_db(data_item: SearchDataItem, session: Session) -> None:
        search_data = SearchDataModel(x=data_item.get_x())
        session.add(search_data)
        session.flush()

        function_values = [
            FunctionValueModel(
                search_data_id=search_data.id,
                type=fv.type,
                function_id=fv.functionID,
                value=fv.value,
            )
            for fv in data_item.function_values
        ]
        session.add_all(function_values)

        float_variables = [
            FloatVariableModel(search_data_id=search_data.id, value=var)
            for var in data_item.point.float_variables
        ]
        session.add_all(float_variables)

        if data_item.point.discrete_variables is not None:
            discrete_variables = [
                DiscreteVariableModel(search_data_id=search_data.id, value=var)
                for var in data_item.point.discrete_variables
            ]
            session.add_all(discrete_variables)

    def insert_data_item(
        self, new_data_item: SearchDataItem, right_data_item: SearchDataItem = None
    ):
        with self.Session() as session:
            self.add_to_db(new_data_item, session)
            session.commit()
        super().insert_data_item(new_data_item, right_data_item)

    def insert_first_data_item(
        self, left_data_item: SearchDataItem, right_data_item: SearchDataItem
    ):
        with self.Session() as session:
            self.add_to_db(left_data_item, session)
            self.add_to_db(right_data_item, session)
            session.commit()
        super().insert_first_data_item(left_data_item, right_data_item)
