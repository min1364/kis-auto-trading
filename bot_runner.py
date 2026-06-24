import os
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv

from main import main


load_dotenv()


def run_bot():
    """
    main.py의 자동매매 로직을 일정 시간 동안 반복 실행한다.
    기본값:
    - 60초 간격
    - 60분 동안 실행
    """

    interval_seconds = int(os.getenv("RUN_INTERVAL_SECONDS", "60"))
    duration_minutes = int(os.getenv("RUN_DURATION_MINUTES", "60"))

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)

    print("=== KIS 자동매매 반복 실행 시작 ===")
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"종료 예정: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"실행 간격: {interval_seconds}초")
    print(f"총 실행 시간: {duration_minutes}분")
    print("중단하려면 Ctrl + C를 누르세요.")
    print("=" * 50)

    run_count = 0

    try:
        while datetime.now() < end_time:
            run_count += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[{run_count}회차 실행] {now}")
            print("-" * 50)

            try:
                main()

            except Exception as e:
                print(f"[오류 발생] {e}")
                print("오류가 발생했지만 다음 실행까지 대기합니다.")

            print("-" * 50)
            print(f"{interval_seconds}초 후 다음 실행")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n사용자가 Ctrl + C로 자동매매 반복 실행을 중단했습니다.")

    finally:
        finish_time = datetime.now()
        print("\n=== KIS 자동매매 반복 실행 종료 ===")
        print(f"종료 시간: {finish_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"총 실행 횟수: {run_count}회")


if __name__ == "__main__":
    run_bot()