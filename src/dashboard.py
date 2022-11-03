import streamlit as st
from executor import Executor
import os
from datetime import datetime
import shutil
import matplotlib.pyplot as plt


def dashboard():
    st.title("Real Estate Investment Simulator")

    # setup sidebar
    param_file = st.sidebar.file_uploader(
        "please upload the parameter file", type=["xlsx"]
    )

    # check whether prepare the parameter file
    if param_file is None:
        return
    start_btn = st.button("start simulation")
    if start_btn is False:
        return

    # start simulation when push button
    with st.spinner("simulation process is doing..."):
        now_date = datetime.now().strftime("%y%m%d%H%M%S")
        result_folder = os.path.join(
            os.path.dirname(__file__), "simulation_result", now_date,
        )
        executor = Executor(parameter_file_path=param_file, result_folder=result_folder)
        dfs = executor.execute()
        executor.save_results(dfs=dfs)

        # archive result folder
        result_file = shutil.make_archive(
            base_name=f"result_{now_date}", format="zip", root_dir=result_folder
        )

    # display result
    df = dfs["tax_data"][["税額"]]
    st.line_chart(data=df)

    if "cash_flow_data" in dfs:
        df = dfs["cash_flow_data"][["収支差額", "差額累計"]]
        fig, ax = plt.subplots()
        ax2 = ax.twinx()

        # 収支差額の設定
        ax.plot(df.index.values, df["収支差額"], marker="o", linestyle="--", color="r")
        ax.set_xlabel("year", fontname="MS Gothic")
        ax.set_ylabel("cash_diff", color="r", fontname="MS Gothic")
        ax.tick_params("y", colors="r")

        # 差額累計の設定
        ax2.plot(df.index.values, df["差額累計"], marker="x", linestyle="-", color="b")
        ax2.set_ylabel("cash_diff_sum", color="b", fontname="MS Gothic")
        ax2.tick_params("y", colors="b")

        # キャッシュフローのグラフをプロット
        st.pyplot(fig)

    # display download button
    with open(result_file, "rb") as f:
        st.download_button(
            "download the zip of result data", f, file_name="result_data.zip"
        )


if __name__ == "__main__":
    dashboard()
