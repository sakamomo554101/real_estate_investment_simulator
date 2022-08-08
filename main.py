import argparse
import pandas as pd
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
from typing import Dict
import os
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("param_file_path", help="set parameters file path")
    return parser.parse_args()


def save_results(folder_path: str, dfs: Dict[str, pd.DataFrame]):
    os.makedirs(folder_path, exist_ok=True)
    for name, df in dfs.items():
        file_path = os.path.join(folder_path, f"{name}.csv")
        df.to_csv(file_path)


def main(args):
    param_file_path = args.param_file_path
    dfs = {}

    # パラメーターファイルの読み込みを行う
    reader = ParametersReader(params_file_path=param_file_path)
    parameters = reader.read_params()

    # 減価償却のデータを作成
    bdc = BuildingDeprecationCalculator(parameters=parameters)
    df = bdc.calculate()
    dfs["building_deprecation_data"] = df.copy(deep=True)

    # ローン利息のデータを作成
    lc = LoanCalculator(parameters=parameters)
    df = lc.calculate()
    dfs["loan_data"] = df.copy(deep=True)

    # 不動産所得を考慮しない税金のデータを作成
    tc = TaxCalculator(parameters=parameters)
    df = tc.calculate()
    dfs["tax_data"] = df.copy(deep=True)

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

    # 処理結果を保存する
    save_results(
        folder_path=os.path.join(
            os.path.dirname(__file__),
            "simulation_result",
            datetime.now().strftime("%y%m%d%H%M%S"),
        ),
        dfs=dfs,
    )


if __name__ == "__main__":
    args = parse_args()
    main(args)
