def convert_positive_number_or_zero(value: float) -> int:
    return int(value) if value >= 0 else 0


def calc_income_deduction(income: int) -> int:
    """給与から給与所得控除額を計算する

    Args:
        income (int): 給与金額（円）

    Returns:
        int: 給与所得控除額（円）
    """
    if income <= 1625000:
        return 550000
    elif 1625000 < income <= 1800000:
        return int(float(income) * 0.4 - 100000)
    elif 1800000 < income <= 3600000:
        return int(float(income) * 0.3 + 80000)
    elif 3600000 < income <= 6600000:
        return int(float(income) * 0.2 + 440000)
    elif 6600000 < income <= 8500000:
        return int(float(income) * 0.1 + 1100000)
    else:
        return 1950000


def calc_income_tax(taxable_income: int) -> int:
    if 1000 <= taxable_income <= 1949000:
        return int(taxable_income * 0.05)
    elif 1949000 < taxable_income <= 3299000:
        return int(taxable_income * 0.1 - 97500)
    elif 3299000 < taxable_income <= 6949000:
        return int(taxable_income * 0.2 - 427000)
    elif 6949000 < taxable_income <= 8999000:
        return int(taxable_income * 0.23 - 636000)
    elif 8999000 < taxable_income <= 17999000:
        return int(taxable_income * 0.33 - 1536000)
    elif 17999000 < taxable_income <= 39999000:
        return int(taxable_income * 0.4 - 2796000)
    elif taxable_income > 39999000:
        return int(taxable_income * 0.45 - 4796000)
    else:
        raise ValueError(f"{taxable_income} is invalid value!")


def calc_resident_tax(taxable_income: int, area: str) -> int:
    # TODO : 控除を全くみてないので、ちゃんと計算する
    # 特別区民税と都民税を計算している
    # 本来は区ごとに適切な計算式が必要（areaを見て、計算式を分岐させる）
    return int(taxable_income * 0.06 + taxable_income * 0.04)
