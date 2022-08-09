import pandas as pd
from datetime import datetime
from typing import List, Tuple
from datetime import datetime
import math


class Parameters:
    def __init__(
        self, income_df: pd.DataFrame, building_df: pd.DataFrame, other_dict: dict
    ) -> None:
        self.__income_df = income_df
        self.__building_df = building_df
        self.__other_dict = other_dict

    def get_simulation_interval(self) -> int:
        return self.get_simulation_end_year() - self.get_simulation_start_year() + 1

    def get_building_names(self) -> List[str]:
        return self.__building_df.columns.values.tolist()

    def get_simulation_start_year(self) -> int:
        return self.__income_df.index.min()

    def get_simulation_end_year(self) -> int:
        return self.__income_df.index.max()

    def get_purchase_date(self, building_name: str) -> datetime:
        return self.__building_df.at["契約日", building_name]

    def get_expected_sale_date(self, building_name: str) -> datetime:
        return self.__building_df.at["売却予定日", building_name]

    def get_building_ratio(self, building_name: str) -> float:
        return self.__building_df.at["建物割合（%）", building_name]

    def get_building_rent_income_per_month(self, building_name: str) -> int:
        return self.__building_df.at["家賃収入（円/月）", building_name]

    def get_petty_expenses_ratio(self, building_name: str) -> int:
        return self.__building_df.at["雑費割合（%）", building_name]

    def get_petty_expenses_upper(self, building_name: str) -> int:
        return self.__building_df.at["雑費上限", building_name]

    def get_petty_expenses_lower(self, building_name: str) -> int:
        return self.__building_df.at["雑費下限", building_name]

    def get_deprecation_interval(self, building_name: str) -> Tuple:
        """指定した物件名の躯体及び設備の減価償却期間を返す

        Args:
            building_name (str): 物件名

        Returns:
            Tuple: 躯体の減価償却期間, 設備の償却期間
        """
        return (
            self.__building_df.at["減価償却期間（躯体部分）", building_name],
            self.__building_df.at["減価償却期間（設備部分）", building_name],
        )

    def get_deprecation_costs(self, building_name: str) -> Tuple:
        """指定した物件名の躯体及び設備の減価償却費用（円/年）を返す

        Args:
            building_name (str): 物件名

        Returns:
            Tuple: 躯体の減価償却費用（円/年）, 設備の減価償却費用（円/年）
        """
        return (
            self.__building_df.at["減価償却費用（躯体）（円/年）", building_name],
            self.__building_df.at["減価償却費用（設備）（円/年）", building_name],
        )

    def get_loan_info(self, building_name: str) -> Tuple:
        """指定した物件名の返済回数, 月利（%）及び借入金額を返す

        Args:
            building_name (str): 物件名

        Returns:
            Tuple: 返済回数, 月利, 借入金額
        """
        return (
            self.__building_df.at["ローン期間（年）", building_name] * 12,
            self.__building_df.at["月利（%）", building_name],
            self.__building_df.at["借入金額", building_name],
        )

    def is_ownership_period(self, building_name: str, year: int) -> bool:
        own_start_date = self.get_purchase_date(building_name=building_name)
        own_end_date = self.get_expected_sale_date(building_name=building_name)
        return own_start_date.year <= year <= own_end_date.year

    def is_cut_initial_cost(self) -> bool:
        return self.__other_dict["other_parameters"].at["初期費用カット", "value"]

    def is_purchase_year(self, building_name: str, year: int) -> bool:
        purchase_year = self.get_purchase_date(building_name=building_name).year
        return purchase_year == year

    def get_building_expenses(self, building_name: str, year: int) -> int:
        total_expenses = (
            sum(
                [
                    self.__building_df.at["管理費（円/月）", building_name],
                    self.__building_df.at["修繕積立金（円/月）", building_name],
                ]
            )
            * 12
            + self.__building_df.at["その他経費（固定資産税）（円/年）", building_name]
        )
        if self.is_purchase_year(building_name=building_name, year=year):
            total_expenses = sum(
                [
                    total_expenses,
                    self.get_initial_expenses(building_name=building_name),
                    self.__building_df.at["不動産取得税", building_name],
                ]
            )
        return total_expenses

    def get_initial_expenses(self, building_name) -> int:
        return self.__building_df.at[
            "初期費用（不動産取得税、事務手数料、登記費用、印紙代、火災保険料、金融機関手数料、など）", building_name
        ]

    def get_real_estate_sale_info(self, building_name: str) -> Tuple:
        """指定した物件の価格, 価格減少率(%/年), 物件価格初年度減少率(%/年)を返す

        Args:
            building_name (str): 物件名

        Returns:
            Tuple: 物件価格（円）, 物件の価格減少率(%/年), 物件価格初年度減少率(%/年)
        """
        return (
            self.__building_df.at["物件価格", building_name],
            self.__building_df.at["物件価格減少率(%/年)", building_name],
            self.__building_df.at["物件価格初年度減少率(%/年)", building_name],
        )

    def get_building_sale_expenses(self, building_name) -> int:
        return self.__building_df.at["譲渡費用（円）", building_name]

    def get_income_df(self) -> pd.DataFrame:
        return self.__income_df.copy(deep=True)

    def get_buidling_df(self) -> pd.DataFrame:
        return self.__building_df.copy(deep=True)


class ParametersReader:
    def __init__(self, params_file_path: str) -> None:
        self.params_file_path = params_file_path

    def read_params(self) -> Parameters:
        # excelのシート名が想定通りかを検証する
        input_data = pd.ExcelFile(self.params_file_path)
        input_sheet_names = [
            "income_simulation",
            "building_information",
            "basic_exemption",
            "exemption_from_income",
            "building_durable_life",
            "other_parameters",
        ]
        actual_sheet_names = input_data.sheet_names
        for sheet_name in input_sheet_names:
            if sheet_name not in actual_sheet_names:
                raise ParametersReaderException(
                    "parameter format is invalid! {} sheet is not exist in parameter excel file.".format(
                        sheet_name
                    )
                )

        # 入力パラメーターの読み込み
        income_df = input_data.parse(input_sheet_names[0], index_col=0, header=0)
        building_df = input_data.parse(input_sheet_names[1], index_col=0, header=0)
        other_dict = {
            "basic_exemption": input_data.parse(input_sheet_names[2], index_col=0),
            "exemption_from_income": input_data.parse(
                input_sheet_names[3], index_col=0
            ),
            "building_durable_life": input_data.parse(
                input_sheet_names[4], index_col=0
            ),
            "other_parameters": input_data.parse(input_sheet_names[5], index_col=0),
        }

        # 築年数の計算（購入日を0年としてカウントする）
        def calc_building_age(s: pd.Series) -> pd.Series:
            init_date = s["築年"]
            purchase_date = s["契約日"]
            difftime = purchase_date - init_date
            out_s = s.copy(deep=True)
            out_s["築年数"] = math.ceil(float(difftime.days) / 365)
            return out_s

        building_df = building_df.apply(calc_building_age)

        # 減価償却費の計算
        def calc_deprecation_cost(s: pd.Series) -> pd.Series:
            building_age = s["築年数"]
            building_structure = s["構造"]
            building_durable_life_df = other_dict["building_durable_life"]
            building_limit_of_frame = building_durable_life_df.at[
                building_structure, "耐用年数"
            ]
            building_limit_of_equipment = 15  # 設備の減価償却上限期間は15年で固定とする
            out_s = s.copy(deep=True)

            def calc_deprecation_interval(
                building_limit: int, building_age: int
            ) -> int:
                return (
                    (building_limit - building_age) + 0.2 * float(building_age)
                    if building_age <= building_limit
                    else 0.2 * float(building_age)
                )

            out_s["減価償却期間（躯体部分）"] = calc_deprecation_interval(
                building_limit_of_frame, building_age
            )
            out_s["減価償却期間（設備部分）"] = calc_deprecation_interval(
                building_limit_of_equipment, building_age
            )

            building_cost = s["物件価格"]
            building_ratio = float(s["建物割合（%）"]) / 100
            building_frame_ratio = float(s["躯体割合（建物の内）"]) / 100
            building_equip_ratio = float(s["設備割合（建物の内）"]) / 100
            out_s["減価償却費用合計（躯体）"] = int(
                building_cost * building_ratio * building_frame_ratio
            )
            out_s["減価償却費用合計（設備）"] = int(
                building_cost * building_ratio * building_equip_ratio
            )
            out_s["減価償却費用（躯体）（円/年）"] = int(
                out_s["減価償却費用合計（躯体）"] / out_s["減価償却期間（躯体部分）"]
            )
            out_s["減価償却費用（設備）（円/年）"] = int(
                out_s["減価償却費用合計（設備）"] / out_s["減価償却期間（設備部分）"]
            )
            return out_s

        building_df = building_df.apply(calc_deprecation_cost)

        # ローン関連の計算
        def calc_loan_data(s: pd.Series):
            out_s = s.copy(deep=True)
            out_s["月利（%）"] = s["金利（%）"] / 12
            out_s["借入金額"] = s["物件価格"] - s["初期投資金額"]
            return out_s

        building_df = building_df.apply(calc_loan_data)

        return Parameters(
            income_df=income_df, building_df=building_df, other_dict=other_dict
        )


class ParametersReaderException(Exception):
    pass
