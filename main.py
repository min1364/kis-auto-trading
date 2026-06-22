import os
from dotenv import load_dotenv

from kis_api import KisApi, save_trade_log


load_dotenv()


def main():
    stock_code = os.getenv("STOCK_CODE", "000660")
    order_qty = int(os.getenv("ORDER_QTY", "1"))
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    kis = KisApi()

    print("=== KIS 자동매매 프로그램 시작 ===")
    print(f"환경: {kis.env}")
    print(f"종목코드: {stock_code}")
    print(f"주문수량: {order_qty}")
    print(f"DRY_RUN: {dry_run}")

    print("\n[1] 접근 토큰 발급")
    kis.get_access_token()
    print("토큰 발급 성공")

    print("\n[2] 현재가 조회")
    current_price = kis.get_current_price(stock_code)
    print(f"현재가: {current_price:,}원")

    print("\n[3] 잔고 조회")
    balance = kis.get_balance()
    print("잔고 조회 성공")

    
    # 현재가 조회 후, DRY_RUN이면 주문 시뮬레이션만 기록
    # DRY_RUN=false이면 모의투자로 1주 시장가 매수
    action = "BUY"

    if dry_run:
        print("\n[4] DRY_RUN 모드: 실제 주문은 보내지 않음")
        fake_result = {
            "rt_cd": "0",
            "msg_cd": "DRY_RUN",
            "msg1": "실제 주문 없이 시뮬레이션으로 기록",
        }

        save_trade_log(
            stock_code=stock_code,
            action="DRY_RUN_BUY",
            price=current_price,
            qty=order_qty,
            result=fake_result,
        )

        print("시뮬레이션 거래 기록 저장 완료: logs/trade_log.csv")

    else:
        print("\n[4] 모의투자 시장가 매수 주문 실행")
        result = kis.order_cash(
            stock_code=stock_code,
            qty=order_qty,
            side="buy",
            price=0,
        )

        print("주문 결과:")
        print(result)

        save_trade_log(
            stock_code=stock_code,
            action=action,
            price=current_price,
            qty=order_qty,
            result=result,
        )

        print("거래 기록 저장 완료: logs/trade_log.csv")

        print("\n[5] 당일 주문/체결 내역 조회")
        orders = kis.get_daily_orders()
        print(orders)

    print("\n=== 프로그램 종료 ===")


if __name__ == "__main__":
    main()