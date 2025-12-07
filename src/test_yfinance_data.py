# -*- coding: utf-8 -*-
import pandas as pd
import yfinance as yf
from utils import validate_data
from config import OUTPUT_DIR
import os

# 测试yfinance返回的数据结构
def test_yfinance_data():
    print("=== 测试yfinance数据返回结构 ===")
    
    # 测试几个ticker
    tickers = ["^TNX", "^VIX", "^GSPC", "^IXIC"]
    
    for ticker in tickers:
        print(f"\n测试ticker: {ticker}")
        try:
            data = yf.Ticker(ticker).history(period="1mo")
            print(f"- 数据类型: {type(data)}")
            print(f"- 是否为空: {data.empty}")
            print(f"- 数据行数: {len(data)}")
            print(f"- 列名: {list(data.columns)}")
            print(f"- 前几行数据:")
            print(data.head())
            print(f"- validate_data(data, 5)结果: {validate_data(data, 5)}")
            print(f"- validate_data(data, 10)结果: {validate_data(data, 10)}")
            
            # 检查是否包含有效数据
            if not data.empty:
                has_valid_close = not data['Close'].isna().all()
                print(f"- 是否包含有效Close数据: {has_valid_close}")
                
        except Exception as e:
            print(f"- 错误: {e}")

if __name__ == "__main__":
    test_yfinance_data()