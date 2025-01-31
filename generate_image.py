import mplfinance as mpf
import yfinance as yf

# ����
print("��ҹ���������ԡ�����ƫ�ñ��֣�")

# ���ɲ�����ͼƬ�ĺ���
def generate_and_save_plot(ticker, filename, period="1mo"):
    data = yf.Ticker(ticker).history(period=period)
    mpf.plot(data, type='candle', figscale=0.4, volume=True, savefig=filename)

# ����ͼƬ
generate_and_save_plot("^TNX", "tenbond.png")
generate_and_save_plot("^VIX", "vix.png", period="2mo")
generate_and_save_plot("^GSPC", "sp500.png")
generate_and_save_plot("^IXIC", "nasdaq.png")
generate_and_save_plot("^RUT", "rs2000.png")
generate_and_save_plot("VNQ", "vnq.png")
generate_and_save_plot("^N225", "nikkei225.png")
generate_and_save_plot("^HSI", "hsi.png")
generate_and_save_plot("CNY=X", "rmb.png", volume=False)

# ���㲢��ӡ����
tenbond = yf.Ticker("^TNX").history(period="1mo")['Close']
tenbond_change = tenbond.iloc[-1] - tenbond.iloc[-2]
print("10zhai data:\n", tenbond_change)

sp500 = yf.Ticker("^GSPC").history(period="1mo")['Close']
sp500_change = (sp500.iloc[-1] / sp500.iloc[-2] - 1) * 100
print("S&P 500 data:", sp500_change)

# �������ݼ�������
