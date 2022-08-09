FROM python:3.10

WORKDIR /workspace
ENV PYTHONPATH $PYTHONPATH:/workspace

# install python packages
ADD requirements.txt .
RUN pip install -r requirements.txt

# copy sources
COPY src/ /workspace/src/

# setup port
EXPOSE 8501

# set up the execution command
CMD streamlit run src/dashboard.py
