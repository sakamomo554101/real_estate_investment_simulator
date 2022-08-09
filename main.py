import argparse
import pandas as pd
from executor import Executor
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
    # パラメーターの設定
    param_file_path = args.param_file_path
    result_folder = os.path.join(
        os.path.dirname(__file__),
        "simulation_result",
        datetime.now().strftime("%y%m%d%H%M%S"),
    )
    dfs = {}

    # シミュレーション処理の実施
    executor = Executor(
        parameter_file_path=param_file_path, result_folder=result_folder
    )
    dfs = executor.execute()

    # 処理結果を保存する
    executor.save_results(dfs=dfs)


if __name__ == "__main__":
    args = parse_args()
    main(args)
