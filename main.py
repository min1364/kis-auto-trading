import os
import time
from dotenv import load_dotenv

from kis_api import KisApi, save_trade_log


load_dotenv()


def find_holding(balance_data, stock_code):
    """
    잔고 조회 결과에서 특정 종목 보유 정보를 찾는다.
    KIS 잔고 조회 결과의 output1 안에서 종목코드가 같은 항목을 찾는다.
    """
    holdings = balance_data.get("output1", [])

    for item in holdings:
        pdno = item.get("pdno")  # 종목코드
        if pdno == stock_code:
            qty = int(item.get("hldg_qty", "0"))  # 보유수량

            # 평균매입가는 데이터가 비어있을 수도 있어서 예외 처리
            avg_price_raw = item.get("pchs_avg_pric", "0")
            try:
                avg_price = float(avg_price_raw)
            except ValueError:
                avg_price = 0.0

            return {
                "qty": qty,
                "avg_price": avg_price,
                "raw": item,
            }

    return {
        "qty": 0,
        "avg_price": 0.0,
        "raw": None,
    }


def decide_action(current_price, holding_qty, avg_price):
    """
    단순 자동매매 전략.

    1. 보유 수량이 없으면 매수
    2. 보유 중이고 수익률이 +1% 이상이면 매도
    3. 보유 중이고 수익률이 -1% 이하이면 매도
    4. 그 외에는 보유
    """
    take_profit_pct = float(os.getenv("TAKE_PROFIT_PCT", "1.0"))
    stop_loss_pct = float(os.getenv("STOP_LOSS_PCT", "-1.0"))

    if holding_qty <= 0:
        return "BUY", None

    if avg_price <= 0:
        return "HOLD", None

    profit_rate = ((current_price - avg_price) / avg_price) * 100

    if profit_rate >= take_profit_pct:
        return "SELL", profit_rate

    if profit_rate <= stop_loss_pct:
        return "SELL", profit_rate

    return "HOLD", profit_rate


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
    print("토큰 준비 완료")

    time.sleep(1.5)

    print("\n[2] 현재가 조회")
    current_price = kis.get_current_price(stock_code)
    print(f"현재가: {current_price:,}원")

    time.sleep(1.5)

    print("\n[3] 잔고 조회")
    balance = kis.get_balance()
    print("잔고 조회 성공")

    time.sleep(1.5)

    holding = find_holding(balance, stock_code)
    holding_qty = holding["qty"]
    avg_price = holding["avg_price"]

    print(f"\n[4] 보유 상태 확인")
    print(f"보유 수량: {holding_qty}주")
    print(f"평균 매입가: {avg_price:,.2f}원")

    action, profit_rate = decide_action(
        current_price=current_price,
        holding_qty=holding_qty,
        avg_price=avg_price,
    )

    print("\n[5] 매매 판단")
    print(f"판단 결과: {action}")

    if profit_rate is not None:
        print(f"현재 수익률: {profit_rate:.2f}%")

    if action == "HOLD":
        result = {
            "rt_cd": "0",
            "msg_cd": "HOLD",
            "msg1": "매수/매도 조건에 해당하지 않아 주문하지 않음",
        }

        save_trade_log(
            stock_code=stock_code,
            action="HOLD",
            price=current_price,
            qty=0,
            result=result,
        )

        print("HOLD 기록 저장 완료: logs/trade_log.csv")

    elif action == "BUY":
        if dry_run:
            result = {
                "rt_cd": "0",
                "msg_cd": "DRY_RUN_BUY",
                "msg1": "DRY_RUN 모드: 실제 매수 주문 없이 기록만 저장",
            }

            save_trade_log(
                stock_code=stock_code,
                action="DRY_RUN_BUY",
                price=current_price,
                qty=order_qty,
                result=result,
            )

            print("DRY_RUN 매수 기록 저장 완료: logs/trade_log.csv")

        else:
            print("\n[6] 모의투자 시장가 매수 주문 실행")
            time.sleep(1.5)

            result = kis.order_cash(
            stock_code=stock_code,
            qty=order_qty,
            side="buy",
            price=0,
)

            print("매수 주문 결과:")
            print(result)

            save_trade_log(
                stock_code=stock_code,
                action="BUY",
                price=current_price,
                qty=order_qty,
                result=result,
            )

            print("매수 거래 기록 저장 완료: logs/trade_log.csv")

    elif action == "SELL":
        sell_qty = min(order_qty, holding_qty)

        if sell_qty <= 0:
            result = {
                "rt_cd": "0",
                "msg_cd": "NO_SELL_QTY",
                "msg1": "매도 가능한 수량이 없어 주문하지 않음",
            }

            save_trade_log(
                stock_code=stock_code,
                action="NO_SELL_QTY",
                price=current_price,
                qty=0,
                result=result,
            )

            print("매도 가능 수량 없음")

        elif dry_run:
            result = {
                "rt_cd": "0",
                "msg_cd": "DRY_RUN_SELL",
                "msg1": "DRY_RUN 모드: 실제 매도 주문 없이 기록만 저장",
            }

            save_trade_log(
                stock_code=stock_code,
                action="DRY_RUN_SELL",
                price=current_price,
                qty=sell_qty,
                result=result,
            )

            print("DRY_RUN 매도 기록 저장 완료: logs/trade_log.csv")

        else:
            print("\n[6] 모의투자 시장가 매도 주문 실행")
            time.sleep(1.5)
            
            result = kis.order_cash(
                stock_code=stock_code,
                qty=sell_qty,
                side="sell",
                price=0,
            )

            print("매도 주문 결과:")
            print(result)

            save_trade_log(
                stock_code=stock_code,
                action="SELL",
                price=current_price,
                qty=sell_qty,
                result=result,
            )

            print("매도 거래 기록 저장 완료: logs/trade_log.csv")

    print("\n=== 프로그램 종료 ===")


if __name__ == "__main__":
    main()
