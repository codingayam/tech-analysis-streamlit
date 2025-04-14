import streamlit as st
# Ensure page config is the first Streamlit command.
st.set_page_config(page_title="NASDAQ 100 Indicators", layout="centered")

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("NASDAQ 100 Indicators")
st.write("Displaying historical data for the NASDAQ 100 Index (^NDX) with technical indicators, updated daily.")

# Hard-coded ticker for NASDAQ 100 with default period "max"
ticker = "^NDX"
period = "max"  # Get the maximum available historical data

st.write(f"Fetching data for {ticker} (Period: {period})...")
data = yf.download(ticker, period=period)

# If data.columns is a MultiIndex (e.g., ('Close', '^NDX')), flatten it.
if isinstance(data.columns, pd.MultiIndex):
    # This will drop the secondary level, leaving just the primary column names.
    data.columns = data.columns.get_level_values(0)

if data.empty:
    st.warning("No data found for the given ticker. Check your internet connection or try again later.")
    st.stop()

# Calculate the 200-day Simple Moving Average (SMA)
data["SMA200"] = data["Close"].rolling(window=200).mean()

# Calculate MACD and Signal line
ema_12 = data["Close"].ewm(span=12, adjust=False).mean()
ema_26 = data["Close"].ewm(span=26, adjust=False).mean()
data["MACD"] = ema_12 - ema_26
data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

# Compute Fibonacci Retracement Levels based on the overall high and low in the data
high_price = data["High"].max()
low_price = data["Low"].min()
diff = high_price - low_price
levels = {
    "0%": high_price,
    "23.6%": high_price - 0.236 * diff,
    "38.2%": high_price - 0.382 * diff,
    "50%": high_price - 0.5 * diff,
    "61.8%": high_price - 0.618 * diff,
    "100%": low_price,
}

# Display the Price Chart and 200-day SMA
st.subheader("Price & 200-day SMA")
st.line_chart(data[["Close", "SMA200"]])

# Display the MACD chart
st.subheader("MACD")
st.line_chart(data[["MACD", "Signal"]])

# Plot Fibonacci Retracement Levels using Matplotlib
st.subheader("Fibonacci Retracement Levels")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(data.index, data["Close"], label="Close Price")

for level_name, level_value in levels.items():
    ax.axhline(y=level_value, linestyle="--", label=f"Fib {level_name}: {level_value:.2f}")

ax.set_title(f"{ticker} Price with Fibonacci Retracements")
ax.set_xlabel("Date")
ax.set_ylabel("Price")
ax.legend(loc="best")
st.pyplot(fig)

st.write("**Disclaimer:** This app is for demonstration and educational purposes only. Not financial advice!")