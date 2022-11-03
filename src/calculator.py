import math

from params import Parameters
import pandas as pd
from abc import ABCMeta, abstractmethod
from util import (
    convert_positive_number_or_zero,
    calc_income_deduction,
    calc_income_tax,
    calc_resident_tax,
)
from typing import Dict


class AbstractCalculator(metaclass=ABCMeta):
    def __init__(self, parameters: Parameters, other_params: dict = None) -> None:
        self._parameters = parameters
        self._other_params = other_params

    @abstractmethod
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        pass


class BuildingDeprecationCalculator(AbstractCalculator):
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        # パラメーターの取得
        simulation_interval = self._parameters.get_simulation_interval()
        building_names = self._parameters.get_building_names()

        # DataFrameの列を設定
        columns = ["年", "物件名", "減価償却費用"]

        # 物件ごとに減価償却費用を算出
        datas = []
        for building_name in building_names:
            for year in range(1, 1 + simulation_interval):
                data = []
                # パラメーターの取得
                (
                    frame_interval,
                    equip_interval,
                ) = self._parameters.get_deprecation_interval(
                    building_name=building_name
                )
                frame_cost, equip_cost = self._parameters.get_deprecation_costs(
                    building_name=building_name
                )

                # 躯体の減価償却費用を設定
                deprecation_frame_cost = frame_cost if year <= frame_interval else 0

                # 設備の減価償却費用を設定
                deprecation_equip_cost = equip_cost if year <= equip_interval else 0

                # 減価償却費用の合計を設定
                data.extend(
                    [
                        year,
                        building_name,
                        deprecation_frame_cost + deprecation_equip_cost,
                    ]
                )

                datas.append(data)

        return pd.DataFrame(data=datas, columns=columns)


class LoanCalculator(AbstractCalculator):
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        # パラメーターの取得
        simulation_interval = self._parameters.get_simulation_interval()
        building_names = self._parameters.get_building_names()

        # 物件ごとに月ごとのローン利息を計算し、DataFrameを構築する
        columns_per_month = [
            "回数",
            "物件名",
            "毎月返済額",
            "利息返済額",
            "元金返済額",
            "ローン残高",
            "利息(建物分のみ)",
        ]
        datas = []
        for building_name in building_names:
            datas_per_building = []
            building_ratio = self._parameters.get_building_ratio(
                building_name=building_name
            )
            (
                payment_count,
                monthly_interest,
                total_loan_amount,
            ) = self._parameters.get_loan_info(building_name=building_name)
            monthly_interest = monthly_interest / 100
            monthly_payment_amount = int(
                (
                    total_loan_amount
                    * monthly_interest
                    * math.pow(1 + monthly_interest, payment_count)
                )
                / (math.pow(1 + monthly_interest, payment_count) - 1)
            )

            for index in range(1, simulation_interval * 12 + 1):
                # 利息返済額の計算
                if index == 1:
                    interest_payment_amount = int(total_loan_amount * monthly_interest)
                elif index > payment_count:
                    # ローン返済期間を超えたら、利息返済額を0に設定する
                    interest_payment_amount = 0
                else:
                    latest_data = datas_per_building[index - 2]
                    latest_loan_credit = latest_data[columns_per_month.index("ローン残高")]
                    interest_payment_amount = int(latest_loan_credit * monthly_interest)

                # 元金返済額の計算
                principal_payment_amount = convert_positive_number_or_zero(
                    monthly_payment_amount - interest_payment_amount
                )

                # ローン残高の計算
                if index == 1:
                    total_loan_amount = self._parameters.get_loan_info(
                        building_name=building_name
                    )[2]
                    loan_credit = convert_positive_number_or_zero(
                        total_loan_amount - principal_payment_amount
                    )
                elif index > payment_count:
                    # ローン返済期間を超えたら、ローン残高を0に設定する
                    loan_credit = 0
                else:
                    loan_credit = convert_positive_number_or_zero(
                        latest_data[5] - principal_payment_amount
                    )

                # 利息（建物分のみ）の計算
                interest_paymant_amount_of_building = int(
                    interest_payment_amount * building_ratio / 100
                )

                # データの追加
                datas_per_building.append(
                    [
                        index,
                        building_name,
                        monthly_payment_amount if index <= payment_count else 0,
                        interest_payment_amount,
                        principal_payment_amount,
                        loan_credit,
                        interest_paymant_amount_of_building,
                    ]
                )
            datas.extend(datas_per_building)
        df_per_month = pd.DataFrame(data=datas, columns=columns_per_month)

        # ローン利息や残高を年単位で計算しなおす
        columns_per_year = ["年", "毎年返済額", "利息返済額", "元金返済額", "ローン残高", "利息(建物分のみ)"]

        def calc_data_per_year(df: pd.DataFrame):
            datas = []
            for index in range(simulation_interval):
                year = index + 1
                target_df = df[
                    ((1 + 12 * index) <= df["回数"]) & (df["回数"] <= 12 * (index + 1))
                ]

                # 毎年返済額を算出
                yearly_paymant_amount = target_df["毎月返済額"].sum()

                # 利息返済額を算出
                interest_payment_amount = target_df["利息返済額"].sum()

                # 元金返済額を算出
                principal_payment_amount = target_df["元金返済額"].sum()

                # ローン残高を算出
                loan_credit = target_df["ローン残高"].min()

                # 利息返済額（建物分のみ）を算出
                interest_paymant_amount_of_building = target_df["利息(建物分のみ)"].sum()

                datas.append(
                    [
                        year,
                        yearly_paymant_amount,
                        interest_payment_amount,
                        principal_payment_amount,
                        loan_credit,
                        interest_paymant_amount_of_building,
                    ]
                )
            return pd.DataFrame(data=datas, columns=columns_per_year)

        df_per_year = df_per_month.groupby(["物件名"]).apply(calc_data_per_year)
        columns_per_year.insert(1, "物件名")
        df_per_year = df_per_year.reset_index().reindex(columns=columns_per_year)
        return df_per_year


# TODO : 家賃を年単位なりで減少させる対応を検討する（パラメーターで設定変更とする）
class RealEstateCashCalculator(AbstractCalculator):
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        # パラメーターの設定
        columns = [
            "年",
            "総収入",
            "物件経費",
            "減価償却費",
            "ローン利息（建物分）",
            "ローン支払い",
            "雑費",
            "帳簿上の支出",
            "帳簿上の収支",
            "リアル収支",
        ]
        simulation_interval = self._parameters.get_simulation_interval()
        simulation_start_year = self._parameters.get_simulation_start_year()
        building_names = self._parameters.get_building_names()

        # 必要なDataFrameがパラメーターに設定されているかを確認
        if "loan_data" not in dfs:
            raise CalculatorError(
                "please set the loan dataframe to calculate the real estate cache data!"
            )
        loan_df = dfs["loan_data"]
        if "building_deprecation_data" not in dfs:
            raise CalculatorError(
                "please set the building deprecation dataframe to calculate the real estate cache data!"
            )
        building_deprecation_df = dfs["building_deprecation_data"]

        # 年ごとの不動産収支を計算する
        datas = []
        for year in range(
            simulation_start_year, simulation_start_year + simulation_interval
        ):
            data = [year, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            for building_name in building_names:
                # 物件の保有期間でない場合は処理をスキップする
                if not self._parameters.is_ownership_period(
                    building_name=building_name, year=year
                ):
                    continue

                # 総収入の追加
                data_per_building = [year, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                data_per_building[1] = (
                    self._parameters.get_building_rent_income_per_month(
                        building_name=building_name
                    )
                    * 12
                )

                # 物件経費の追加
                data_per_building[2] = self._parameters.get_building_expenses(
                    building_name=building_name, year=year
                )

                # 減価償却費の追加
                year_index = (
                    year
                    - self._parameters.get_purchase_date(
                        building_name=building_name
                    ).year
                    + 1
                )
                target_df = building_deprecation_df[
                    (building_deprecation_df["物件名"] == building_name)
                    & (building_deprecation_df["年"] == year_index)
                ]
                if len(target_df) != 1:
                    raise CalculatorError(
                        f"target dataframe size of building deprecation data is not one! building_name is {building_name}, year is {year} and year_index is {year_index}. size is {len(target_df)}."
                    )
                deprecation_cost = target_df["減価償却費用"].values[0]
                data_per_building[3] = deprecation_cost

                # ローン利息（建物分）、ローン支払い分の設定
                target_df = loan_df[
                    (loan_df["物件名"] == building_name) & (loan_df["年"] == year_index)
                ]
                if len(target_df) != 1:
                    raise CalculatorError(
                        f"target dataframe size of loan is not one! building_name is {building_name}, year is {year} and year_index is {year_index}. size is {len(target_df)}"
                    )
                data_per_building[4] = target_df["利息(建物分のみ)"].values[0]
                data_per_building[5] = target_df["毎年返済額"].values[0]

                # 雑費の設定
                building_expenses = self._parameters.get_building_expenses(
                    building_name=building_name, year=year
                )
                petty_expenses_ratio = self._parameters.get_petty_expenses_ratio(
                    building_name=building_name
                )
                petty_expenses = int(
                    (building_expenses + deprecation_cost) * petty_expenses_ratio / 100
                )

                if petty_expenses > self._parameters.get_petty_expenses_upper(
                    building_name=building_name
                ):
                    petty_expenses = self._parameters.get_petty_expenses_upper(
                        building_name=building_name
                    )
                elif petty_expenses < self._parameters.get_petty_expenses_lower(
                    building_name=building_name
                ):
                    petty_expenses = self._parameters.get_petty_expenses_lower(
                        building_name=building_name
                    )
                data_per_building[6] = petty_expenses

                # 帳簿上の支出の設定(物件経費 + 減価償却費 + ローン利息)
                data_per_building[7] = sum(
                    [
                        data_per_building[2],
                        data_per_building[3],
                        data_per_building[4],
                        data_per_building[6],
                    ]
                )

                # 帳簿上の収支の設定（総収入 - 帳簿上の支出）
                data_per_building[8] = data_per_building[1] - data_per_building[7]

                # リアル収支の設定（総収入 - (物件経費 + ローン支払い)）
                # ただし、初期物件コストの一部が自己負担ではない場合は、負担でないコストを間引く
                data_per_building[9] = data_per_building[1] - sum(
                    [data_per_building[2], data_per_building[5]]
                )
                if self._parameters.is_cut_initial_cost() and self._parameters.is_purchase_year(
                    building_name=building_name, year=year
                ):
                    initial_expenses = self._parameters.get_initial_expenses(
                        building_name=building_name
                    )
                    data_per_building[9] += initial_expenses

                # 加算する
                for i in range(len(data_per_building)):
                    if i == 0:
                        continue
                    data[i] += data_per_building[i]

            datas.append(data)

        return pd.DataFrame(datas, columns=columns)


class TaxCalculator(AbstractCalculator):
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        if "real_estate_cash_data" in dfs:
            real_estate_cach_df = dfs["real_estate_cash_data"]
        else:
            real_estate_cach_df = None

        # パラメーターの取得
        income_df = self._parameters.get_income_df()

        # 課税所得, 税金の計算を実施
        def calc_tax(s: pd.Series) -> pd.Series:
            out_s = s.copy(deep=True)
            income = s["給与（万円）"] * 10000
            expenses = s["経費（万円）"] * 10000

            # 所得金額の計算
            out_s["給与所得控除"] = calc_income_deduction(income=income)
            if real_estate_cach_df is not None:
                # 不動産収支の情報がある場合は、不動産収支を考慮して、所得金額を計算する
                target_df = real_estate_cach_df[
                    (real_estate_cach_df["年"] == out_s.name)
                ]["帳簿上の収支"]
                if len(target_df) != 1:
                    raise CalculatorError(
                        f"target dataframe size of loan is not one! data is {out_s}. size is {len(target_df)}"
                    )
                out_s["所得金額"] = income - out_s["給与所得控除"] + int(target_df.values[0])
            else:
                out_s["所得金額"] = income - out_s["給与所得控除"]

            # 課税所得の計算
            out_s["基礎控除"] = 48 * 10000
            taxable_income = out_s["所得金額"] - (out_s["基礎控除"] + expenses)
            out_s["課税所得"] = taxable_income if taxable_income > 0 else 0

            # 所得税, 住民税の計算
            # TODO : 住民税は地域設定をして、計算を行うようにする
            out_s["所得税"] = calc_income_tax(taxable_income=out_s["課税所得"])
            out_s["住民税"] = calc_resident_tax(taxable_income=out_s["課税所得"], area=None)

            # 税金総額（所得税 + 住民税）の設定
            out_s["税額"] = out_s["所得税"] + out_s["住民税"]
            return out_s

        df = income_df.apply(calc_tax, axis=1)
        return df


class RealEstatePriceSimuationCalculator(AbstractCalculator):
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        # パラメーターの設定
        columns = ["年", "物件名", "想定評価額"]
        simulation_interval = self._parameters.get_simulation_interval()
        building_names = self._parameters.get_building_names()

        # 物件ごとの価格シミュレーションデータを作成
        # 現状は簡易的なシミュレーションとし、物件価格が年単位で（年ごとの価格に対して）1%ずつ減少するものとする
        datas = []
        for building_name in building_names:
            # 物件ごとのパラメーターの取得
            (
                building_price,
                decreace_rate,
                decreate_rate_in_1st_year,
            ) = self._parameters.get_real_estate_sale_info(building_name=building_name)
            datas_per_building = []
            for index in range(simulation_interval):
                data = []
                year = index + 1
                data.append(year)
                data.append(building_name)

                # 査定価格の計算
                if year == 1:
                    value = building_price * (
                        1 - float(decreate_rate_in_1st_year) / 100
                    )
                else:
                    value = datas_per_building[index - 1][2] * (
                        1 - float(decreace_rate) / 100
                    )
                data.append(int(value))

                datas_per_building.append(data)
            datas.extend(datas_per_building)

        return pd.DataFrame(data=datas, columns=columns)


class RealEstateSaleSimulationCalculator(AbstractCalculator):
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        # パラメーターの設定
        columns = ["年", "物件名", "想定評価額", "ローン残額", "累計減価償却費用", "売却経費", "譲渡所得税", "売却差額"]
        simulation_interval = self._parameters.get_simulation_interval()
        building_names = self._parameters.get_building_names()

        # 必要なDataFrameがパラメーターに設定されているかを確認
        if "loan_data" not in dfs:
            raise CalculatorError(
                "please set the loan dataframe to calculate the real estate sale simulation data!"
            )
        loan_df = dfs["loan_data"]
        if "building_deprecation_data" not in dfs:
            raise CalculatorError(
                "please set the building deprecation dataframe to calculate the real estate sale simulation data!"
            )
        building_deprecation_df = dfs["building_deprecation_data"]
        if "real_estate_price_data" not in dfs:
            raise CalculatorError(
                "please set the real estate price dataframe to calculate the real estate sale simulation data"
            )
        real_estate_price_df = dfs["real_estate_price_data"]

        # 物件ごとの売却シミュレーションデータを作成
        datas = []
        for building_name in building_names:
            # 物件ごとのパラメーターの取得
            (
                building_purchase_price,
                _,
                _,
            ) = self._parameters.get_real_estate_sale_info(building_name=building_name)
            building_sale_expenses = self._parameters.get_building_sale_expenses(
                building_name=building_name
            )
            datas_per_building = []
            for index in range(simulation_interval):
                data = []
                year = index + 1
                data.append(year)
                data.append(building_name)

                # 査定価格の取得
                values = real_estate_price_df[
                    (real_estate_price_df["物件名"] == building_name)
                    & (real_estate_price_df["年"] == year)
                ]["想定評価額"].values
                if len(values) != 1:
                    raise CalculatorError(
                        f"real estate price data is duprecated! value is {values}"
                    )
                building_price = values[0]
                data.append(building_price)

                # ローン残高情報を取得する
                values = loan_df[
                    (loan_df["物件名"] == building_name) & (loan_df["年"] == year)
                ]["ローン残高"].values
                if len(values) != 1:
                    raise CalculatorError(f"loan data is duprecated! value is {values}")
                loan_amount = values[0]
                data.append(loan_amount)

                # 累計減価償却費用の計算
                total_deprecation_cost = building_deprecation_df[
                    (building_deprecation_df["物件名"] == building_name)
                    & (building_deprecation_df["年"] <= year)
                ]["減価償却費用"].sum()
                data.append(total_deprecation_cost)

                # 売却経費の設定
                # TODO : 繰り上げ返済手数料の計算をしたようにしたほうが良いかも（現状はシンプルに多めに金額設定している）
                data.append(building_sale_expenses)

                # 譲渡所得税の計算
                sale_building_gain = building_price - (
                    building_purchase_price
                    - building_sale_expenses
                    - total_deprecation_cost
                )
                if year <= 5:
                    tax_of_sale_building = int(sale_building_gain * 0.3963)
                else:
                    tax_of_sale_building = int(sale_building_gain * 0.20315)
                data.append(tax_of_sale_building)

                # 売却差額の計算
                value = building_price - (
                    loan_amount + tax_of_sale_building + building_sale_expenses
                )
                data.append(value)
                datas_per_building.append(data)

            datas.extend(datas_per_building)

        return pd.DataFrame(datas, columns=columns)


class CashFlowCalculator(AbstractCalculator):
    def calculate(self, dfs: Dict[str, pd.DataFrame] = {}) -> pd.DataFrame:
        # パラメーターの設定
        columns = ["年", "リアル収支", "課税差額", "物件売却益", "収支差額", "差額累計"]
        simulation_interval = self._parameters.get_simulation_interval()
        simulation_start_year = self._parameters.get_simulation_start_year()
        building_names = self._parameters.get_building_names()

        # 必要なDataFrameがパラメーターに設定されているかを確認
        if "tax_data" not in dfs:
            raise CalculatorError(
                "please set the tax dataframe to calculate the cash flow!"
            )
        tax_df = dfs["tax_data"]
        if "tax_data_with_real_estate_cash" not in dfs:
            raise CalculatorError(
                "please set the tax with real estate cash dataframe to calculate the cash flow!"
            )
        tax_with_real_estate_df = dfs["tax_data_with_real_estate_cash"]
        if "real_estate_cash_data" not in dfs:
            raise CalculatorError(
                "please set the real estate cash dataframe to calculate the cash flow!"
            )
        real_estate_cash_df = dfs["real_estate_cash_data"]
        if "real_estate_sale_data" not in dfs:
            raise CalculatorError(
                "please set the real estate sale dataframe to calculate the cash flow!"
            )
        real_estate_sale_df = dfs["real_estate_sale_data"]

        # キャッシュフローの作成
        datas = []
        for year in range(
            simulation_start_year, simulation_start_year + simulation_interval
        ):
            data = []
            data.append(year)
            index = year - simulation_start_year

            # リアル収支の設定
            values = real_estate_cash_df[real_estate_cash_df["年"] == year][
                "リアル収支"
            ].values
            if len(values) != 1:
                raise CalculatorError(
                    f"real estate cash data is dupricated! value is {values}"
                )
            real_cash_per_year = values[0]
            data.append(real_cash_per_year)

            # 課税差額の設定（不動産あり税額 - 不動産なし税額）
            total_tax = tax_df.at[year, "税額"]
            total_tax_with_real_estate = tax_with_real_estate_df.at[year, "税額"]
            tax_diff = total_tax_with_real_estate - total_tax
            data.append(tax_diff)

            # 物件売却益の取得
            # 物件売却がある年のみ計上する
            total_profit_on_sale_of_real_estate = 0
            for building_name in building_names:
                sale_year = self._parameters.get_expected_sale_date(
                    building_name=building_name
                ).year
                if year == sale_year:
                    year_index = year - simulation_start_year + 1
                    values = real_estate_sale_df[
                        (real_estate_sale_df["年"] == year_index)
                        & (real_estate_sale_df["物件名"] == building_name)
                    ]["売却差額"].values
                    if len(values) != 1:
                        raise CalculatorError(
                            f"real estate sale data is dupricated! value is {values}"
                        )
                    total_profit_on_sale_of_real_estate += values[0]
            data.append(total_profit_on_sale_of_real_estate)

            # 収支差額の計算（リアル収支 - 課税差額）
            diff_cash = (
                real_cash_per_year - tax_diff + total_profit_on_sale_of_real_estate
            )
            data.append(diff_cash)

            # 差額累計の計算
            total_diff_cash = diff_cash
            if index != 0:
                total_diff_cash = datas[index - 1][5] + total_diff_cash
            data.append(total_diff_cash)

            datas.append(data)

        return pd.DataFrame(datas, columns=columns).set_index(keys="年", drop=True)


class CalculatorError(Exception):
    pass
