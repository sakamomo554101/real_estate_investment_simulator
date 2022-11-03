from params import ParametersReader
from calculator import (
    BuildingDeprecationCalculator,
    LoanCalculator,
    TaxCalculator,
    RealEstateCashCalculator,
    RealEstatePriceSimuationCalculator,
    RealEstateSaleSimulationCalculator,
    CashFlowCalculator,
)
import pandas as pd
from typing import Dict
import os


class Executor:
    def __init__(self, parameter_file_path: str, result_folder: str) -> None:
        self.__parameter_file_path = parameter_file_path
        self.__result_folder = result_folder

    def execute(self) -> Dict[str, pd.DataFrame]:
        dfs = {}

        # パラメーターファイルの読み込みを行う
        reader = ParametersReader(params_file_path=self.__parameter_file_path)
        parameters = reader.read_params()

        # 不動産所得を考慮しない税金のデータを作成
        tc = TaxCalculator(parameters=parameters)
        df = tc.calculate()
        dfs["tax_data"] = df.copy(deep=True)

        # 税金計算のみの場合は、ここで処理が終了
        if parameters.is_only_tax_calculation():
            return dfs

        # 減価償却のデータを作成
        bdc = BuildingDeprecationCalculator(parameters=parameters)
        df = bdc.calculate()
        dfs["building_deprecation_data"] = df.copy(deep=True)

        # ローン利息のデータを作成
        lc = LoanCalculator(parameters=parameters)
        df = lc.calculate()
        dfs["loan_data"] = df.copy(deep=True)

        # 不動産収支の計算
        recc = RealEstateCashCalculator(parameters=parameters)
        df = recc.calculate(dfs=dfs)
        dfs["real_estate_cash_data"] = df.copy(deep=True)

        # 不動産収支込みの税金のデータを作成
        df = tc.calculate(dfs=dfs)
        dfs["tax_data_with_real_estate_cash"] = df.copy(deep=True)

        # 物件の価格シミュレーションのデータを作成
        repc = RealEstatePriceSimuationCalculator(parameters=parameters)
        df = repc.calculate()
        dfs["real_estate_price_data"] = df.copy(deep=True)

        # 物件の売却シミュレーションのデータを作成
        resc = RealEstateSaleSimulationCalculator(parameters=parameters)
        df = resc.calculate(dfs=dfs)
        dfs["real_estate_sale_data"] = df.copy(deep=True)

        # キャッシュフローのデータを作成
        cfc = CashFlowCalculator(parameters=parameters)
        df = cfc.calculate(dfs=dfs)
        dfs["cash_flow_data"] = df.copy(deep=True)

        return dfs

    def save_results(self, dfs: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        os.makedirs(self.__result_folder, exist_ok=True)
        file_paths = {}
        for name, df in dfs.items():
            file_path = os.path.join(self.__result_folder, f"{name}.csv")
            df.to_csv(file_path)
            file_paths[name] = file_path
        return file_paths
