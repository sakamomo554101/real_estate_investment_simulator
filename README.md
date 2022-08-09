# Real Estate Investment Simulator

不動産投資を行う際のキャッシュフロー（物件売却含む）を簡易シミュレーションするツールとなります.

## Usage

### create parameter file

TBD

### build dashboard image

```
docker build -t real_estate_investment_simulator:0.0.1 .
```

### run dashboard

```
docker run --name real_estate_investment_simulator -p 8501:8501 -d -it real_estate_investment_simulator:0.0.1
```

### open the dashboard

* 下記のURLにアクセスし、ダッシュボードをブラウザ上で表示させる.
  * http://localhost:8501
* parameter fileをダッシュボード経由でアップロードし、シミュレーション処理を実行する

## License

MIT
