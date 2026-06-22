# KIS Open API Mock Auto Trading System

## 1. 프로젝트 개요

본 프로젝트는 한국투자증권 KIS Developers Open API를 사용하여 국내주식 모의투자 환경에서 자동매매 시스템을 구현한 프로젝트이다.

자동매매 대상 종목은 SK하이닉스(000660)이며, REST API를 사용하여 현재가 조회, 계좌 잔고 조회, 모의투자 주문, 거래 기록 저장 기능을 구현하였다.

본 프로젝트는 실전투자 환경이 아닌 모의투자 환경에서만 실행되도록 구성하였다.

---

## 2. 사용 기술

* Python
* requests
* python-dotenv
* pandas
* 한국투자증권 KIS Developers Open API
* 국내주식 모의투자 API
* REST API

---

## 3. 주요 기능

### 3.1 접근 토큰 발급

KIS Developers에서 발급받은 모의투자용 APP Key와 APP Secret을 사용하여 access token을 발급받는다.
토큰 발급 제한을 고려하여 발급된 토큰은 `logs/token.json`에 저장하고 재사용하도록 구현하였다.

### 3.2 현재가 조회

국내주식 현재가 조회 API를 사용하여 SK하이닉스(000660)의 현재가를 조회한다.

### 3.3 잔고 조회

모의투자 계좌의 국내주식 잔고를 조회한다.

### 3.4 자동 주문

`DRY_RUN=false`일 때 모의투자 계좌에서 SK하이닉스 1주 시장가 매수 주문을 실행하도록 구현하였다.

### 3.5 거래 기록 저장

자동매매 실행 결과는 `logs/trade_log.csv`에 저장되도록 구현하였다.
GitHub 제출 시에는 보안상 민감정보가 포함될 수 있는 원본 로그 파일은 제외하였다.

---

## 4. 프로젝트 구조

```text
kis-auto-trading/
│
├── main.py
├── kis_api.py
├── requirements.txt
├── README.md
├── .gitignore
└── logs/
```

---

## 5. 환경변수 설정

보안상 APP Key, APP Secret, 계좌번호는 코드에 직접 작성하지 않고 `.env` 파일에서 불러오도록 구현하였다.

`.env` 예시는 다음과 같다.

```env
KIS_ENV=mock

KIS_APP_KEY=your_mock_app_key
KIS_APP_SECRET=your_mock_app_secret

KIS_ACCOUNT_NO=your_mock_account_number
KIS_ACCOUNT_PRODUCT_CODE=01

STOCK_CODE=000660
ORDER_QTY=1

DRY_RUN=true
```

실제 `.env` 파일은 보안상 GitHub에 업로드하지 않는다.

---

## 6. 실행 방법

필요한 패키지를 설치한다.

```bash
pip install -r requirements.txt
```

자동매매 프로그램을 실행한다.

```bash
python main.py
```

처음에는 안전을 위해 `DRY_RUN=true`로 실행하여 현재가 조회와 잔고 조회가 정상적으로 되는지 확인한다.

실제 모의투자 주문을 실행하려면 `.env`에서 다음과 같이 변경한다.

```env
DRY_RUN=false
```

---

## 7. 실행 결과

`DRY_RUN=true` 상태에서 접근 토큰 발급, 현재가 조회, 잔고 조회가 정상적으로 실행되는 것을 확인하였다.

이후 `DRY_RUN=false` 상태에서 모의투자 주문 실행을 시도하였으나, 실행 시점이 장 종료 이후였기 때문에 주문 가능 시간이 아니라는 응답을 확인하였다.

따라서 본 프로젝트는 다음 사항을 확인하였다.

* 한국투자증권 Open API 인증 연결
* 모의투자용 access token 발급
* 국내주식 현재가 조회
* 모의투자 계좌 잔고 조회
* 모의투자 주문 API 호출 구조 구현
* 주문 가능 시간 외 실행 시 오류 응답 확인
* 거래 기록 저장 기능 구현

장중 시간에 재실행하면 실제 모의투자 주문 및 체결 기록을 추가로 확인할 수 있다.

---

## 8. 보안 주의사항

본 프로젝트에서는 다음 정보를 GitHub에 업로드하지 않는다.

* APP Key
* APP Secret
* access token
* 계좌번호
* `.env`
* `logs/token.json`

모든 인증 정보는 환경변수로 관리한다.

---

## 9. 한계 및 개선 방향

현재 버전은 기말 프로젝트 제출을 위한 최소 기능 자동매매 시스템이다.
추후 다음 기능을 개선할 수 있다.

* 이동평균선 기반 매매 전략
* RSI 기반 매매 전략
* 주문 체결 여부 반복 확인
* 매도 조건 추가
* 장중 자동 실행 스케줄링
* 거래 결과 시각화
