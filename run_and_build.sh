#!/bin/sh

echo "build simulator image"
docker build -t real_estate_investment_simulator:0.0.1 .

echo "run simulator"
docker run --name real_estate_investment_simulator -p 8501:8501 -d -it real_estate_investment_simulator:0.0.1
