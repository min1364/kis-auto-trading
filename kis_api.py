import os
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv


load_dotenv()


class KisApi:
    def __init__(self):
        self.env = os.getenv("KIS_ENV", "mock")
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.account_no = os.getenv("KIS_ACCOUNT_NO")
        self.account_product_code = os.getenv("KIS_ACCOUNT_PRODUCT_CODE", "01")

        if not self.app_key or not self.app_secret:
            raise ValueError("KIS_APP_KEY 또는 KIS_APP_SECRET이 .env에 없습니다.")

        if not self.account_no:
            raise ValueError("KIS_ACCOUNT_NO가 .env에 없습니다.")

        if self.env == "mock":
            self.base_url = "https://openapivts.koreainvestment.com:29443"
        else:
            self.base_url = "https://openapi.koreainvestment.com:9443"

        self.access_token: Optional[str] = None

    def get_access_token(self) -> str:
        """
        접근 토큰 발급.
        KIS Developers REST 접근토큰발급(P) API 사용.
        """
        token_path = "logs/token.json"
        os.makedirs("logs", exist_ok=True)

         # 1. 저장된 토큰이 있으면 먼저 재사용
        if os.path.exists(token_path):
            try:
                with open(token_path, "r", encoding="utf-8") as f:
                    token_data = json.load(f)

                access_token = token_data.get("access_token")
                issued_at = token_data.get("issued_at")

                if access_token and issued_at:
                    issued_time = datetime.strptime(issued_at, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()

                    # 안전하게 23시간 이내 토큰만 재사용
                    if now - issued_time < timedelta(hours=23):
                        self.access_token = access_token
                        print("저장된 토큰 재사용")
                        return self.access_token

            except Exception:
                pass
            
         # 2. 저장된 토큰이 없거나 만료되었으면 새로 발급
        url = f"{self.base_url}/oauth2/tokenP"

        headers = {
            "content-type": "application/json"
        }

        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(body),
            timeout=10,
        )

        data = response.json()

        if response.status_code != 200 or "access_token" not in data:
            raise RuntimeError(f"토큰 발급 실패: {data}")

        self.access_token = data["access_token"]

        # 3. 토큰 저장
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "access_token": self.access_token,
                    "issued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print("새 토큰 발급 및 저장")
        return self.access_token

    def _headers(self, tr_id: str, hashkey: Optional[str] = None) -> Dict[str, str]:
        if not self.access_token:
            self.get_access_token()

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

        if hashkey:
            headers["hashkey"] = hashkey

        return headers

    def get_hashkey(self, body: Dict[str, Any]) -> str:
        """
        주문처럼 body가 있는 API에서 hashkey가 필요한 경우 사용.
        """
        url = f"{self.base_url}/uapi/hashkey"

        headers = {
            "content-type": "application/json",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
        data = response.json()

        if "HASH" not in data:
            raise RuntimeError(f"hashkey 발급 실패: {data}")

        return data["HASH"]

    def get_current_price(self, stock_code: str) -> int:
        """
        국내주식 현재가 조회.
        FID_COND_MRKT_DIV_CODE = J: 주식
        FID_INPUT_ISCD = 종목코드
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = self._headers("FHKST01010100")

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or data.get("rt_cd") != "0":
            raise RuntimeError(f"현재가 조회 실패: {data}")

        price = int(data["output"]["stck_prpr"])
        return price

    def get_balance(self) -> Dict[str, Any]:
        """
        국내주식 잔고 조회.
        모의투자 tr_id: VTTC8434R
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        tr_id = "VTTC8434R" if self.env == "mock" else "TTTC8434R"

        headers = self._headers(tr_id)

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_product_code,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or data.get("rt_cd") != "0":
            raise RuntimeError(f"잔고 조회 실패: {data}")

        return data

    def order_cash(self, stock_code: str, qty: int, side: str, price: int = 0) -> Dict[str, Any]:
        """
        국내주식 현금 주문.
        side = "buy" 또는 "sell"

        ORD_DVSN:
        00 = 지정가
        01 = 시장가

        과제 테스트용으로 시장가 주문 사용.
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        if side == "buy":
            tr_id = "VTTC0802U" if self.env == "mock" else "TTTC0802U"
        elif side == "sell":
            tr_id = "VTTC0801U" if self.env == "mock" else "TTTC0801U"
        else:
            raise ValueError("side는 buy 또는 sell만 가능합니다.")

        body = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_product_code,
            "PDNO": stock_code,
            "ORD_DVSN": "01",
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price),
        }

        hashkey = self.get_hashkey(body)
        headers = self._headers(tr_id, hashkey=hashkey)

        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
        data = response.json()

        return data

    def get_daily_orders(self) -> Dict[str, Any]:
        """
        국내주식 일별 주문 체결 조회.
        모의투자 tr_id: VTTC8001R
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"

        tr_id = "VTTC8001R" if self.env == "mock" else "TTTC8001R"
        headers = self._headers(tr_id)

        today = datetime.now().strftime("%Y%m%d")

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_product_code,
            "INQR_STRT_DT": today,
            "INQR_END_DT": today,
            "SLL_BUY_DVSN_CD": "00",
            "INQR_DVSN": "00",
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or data.get("rt_cd") != "0":
            raise RuntimeError(f"주문 체결 조회 실패: {data}")

        return data


def save_trade_log(
    stock_code: str,
    action: str,
    price: int,
    qty: int,
    result: Dict[str, Any],
    log_path: str = "logs/trade_log.csv",
):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    file_exists = os.path.exists(log_path)

    with open(log_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "datetime",
                "stock_code",
                "action",
                "price",
                "qty",
                "rt_cd",
                "msg_cd",
                "msg1",
                "raw_result",
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            stock_code,
            action,
            price,
            qty,
            result.get("rt_cd"),
            result.get("msg_cd"),
            result.get("msg1"),
            json.dumps(result, ensure_ascii=False),
        ])