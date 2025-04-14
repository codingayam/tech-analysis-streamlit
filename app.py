import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Set page configuration at the very top.
st.set_page_config(page_title="Dynamic Index Technical Indicators", layout="centered")

st.title("Dynamic Technical Indicators for Market Indices")
st.write("This app shows technical indicators for your chosen index along with brief analysis of whether the indicator is bullish or bearish. Select an index and time period below.")

# Allow the user to select which index to view
index_options = {
    "NASDAQ 100 (^NDX)": "^NDX",
    "S&P 500 (^GSPC)": "^GSPC"
}
selected_index = st.selectbox("Select Index", list(index_options.keys()))
ticker = index_options[selected_index]

st.write("Displaying historical data and indicators for:", selected_index)

# Caches data for 24 hours
@st.cache_data(ttl=86400)
def get_data(ticker, period):
    data = yf.download(ticker, period=period)
    # Flatten columns if they're a MultiIndex (common for index data)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

# Download full data ("max") for the selected ticker
full_period = "max"
data = get_data(ticker, full_period)

if data.empty:
    st.warning("No data found for the selected index. Check your internet connection or try again later.")
    st.stop()

# Dictionary for available time ranges, including from 1 day up to 20 years plus All Time
time_options = {
    "5d": pd.DateOffset(days=5),
    "1w": pd.DateOffset(weeks=1),
    "1 month": pd.DateOffset(months=1),
    "3 month": pd.DateOffset(months=3),
    "6 month": pd.DateOffset(months=6),
    "1 year": pd.DateOffset(years=1),
    "2 year": pd.DateOffset(years=2),
    "5 years": pd.DateOffset(years=5),
    "10 years": pd.DateOffset(years=10),
    "20 years": pd.DateOffset(years=20),
    "All Time": None
}

# Let the user select a time period
time_period_label = st.selectbox("Select Time Period", list(time_options.keys()))

# Filter the full dataset based on the selected time period.
if time_options[time_period_label] is None:
    filtered_data = data.copy()
else:
    offset = time_options[time_period_label]
    start_date = pd.Timestamp.today() - offset
    filtered_data = data.loc[start_date:]
filtered_data.index = pd.to_datetime(filtered_data.index)

# Recalculate technical indicators on the filtered data
# 1. 200-day SMA
filtered_data["SMA200"] = filtered_data["Close"].rolling(window=200).mean()
# 2. 50-day SMA
filtered_data["SMA50"] = filtered_data["Close"].rolling(window=50).mean()
# 3. MACD and its Signal line
ema_12 = filtered_data["Close"].ewm(span=12, adjust=False).mean()
ema_26 = filtered_data["Close"].ewm(span=26, adjust=False).mean()
filtered_data["MACD"] = ema_12 - ema_26
filtered_data["Signal"] = filtered_data["MACD"].ewm(span=9, adjust=False).mean()
# 4. Fibonacci Retracement Levels based on filtered data's high and low
high_price = filtered_data["High"].max()
low_price = filtered_data["Low"].min()
diff = high_price - low_price
fib_levels = {
    "0%": high_price,
    "23.6%": high_price - 0.236 * diff,
    "38.2%": high_price - 0.382 * diff,
    "50%": high_price - 0.5 * diff,
    "61.8%": high_price - 0.618 * diff,
    "100%": low_price,
}

# Get the latest row for analysis
latest_row = filtered_data.iloc[-1]
latest_close = latest_row["Close"]
latest_SMA200 = latest_row["SMA200"]
latest_SMA50 = latest_row["SMA50"]
latest_MACD = latest_row["MACD"]
latest_Signal = latest_row["Signal"]

# ---------------------------
# Chart 1: Price & 200-Day SMA
# ---------------------------
st.markdown("### Chart 1: Price & 200-Day SMA")
st.line_chart(filtered_data[["Close", "SMA200"]])

# Analysis for Chart 1: Compare latest close to 200-day SMA.
if pd.notna(latest_SMA200):
    if latest_close > latest_SMA200:
        analysis_chart1 = "The current closing price is above the 200-day SMA, suggesting a long-term bullish trend."
    else:
        analysis_chart1 = "The current closing price is below the 200-day SMA, which may indicate a long-term bearish trend."
    st.write("**Analysis (Chart 1):**", analysis_chart1)
else:
    st.write("**Analysis (Chart 1):** Not enough data to compute 200-day SMA for this time range.")

# ---------------------------
# Chart 2: MACD & Signal
# ---------------------------
st.markdown("### Chart 2: MACD & Signal")
st.line_chart(filtered_data[["MACD", "Signal"]])

# Analysis for Chart 2: Compare MACD vs Signal.
if latest_MACD > latest_Signal:
    analysis_chart2 = "MACD is above the Signal line, indicating potential bullish momentum."
else:
    analysis_chart2 = "MACD is below the Signal line, suggesting possible bearish momentum."
st.write("**Analysis (Chart 2):**", analysis_chart2)

# ---------------------------
# Chart 3: Fibonacci Retracement Levels
# ---------------------------
st.markdown("### Chart 3: Fibonacci Retracement Levels")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(filtered_data.index, filtered_data["Close"], label="Close Price")
for level_name, level_value in fib_levels.items():
    ax.axhline(y=level_value, linestyle="--", label=f"Fib {level_name}: {level_value:.2f}")
ax.set_title(f"{selected_index} Close Price with Fibonacci Levels ({time_period_label})")
ax.set_xlabel("Date")
ax.set_ylabel("Price")
ax.legend(loc="best")
st.pyplot(fig)

# Analysis for Chart 3: Fibonacci analysis based on current price.
if latest_close >= fib_levels["0%"]:
    analysis_chart3 = ("The current price is at or above the recent high. "
                      "This may indicate a potential new uptrend forming.")
elif latest_close >= fib_levels["23.6%"]:
    analysis_chart3 = ("The current price is between the 0% and 23.6% retracement levels. "
                      "This indicates a very weak bounce; bearish control is likely to continue.")
elif latest_close >= fib_levels["38.2%"]:
    analysis_chart3 = ("The current price is between the 23.6% and 38.2% retracement levels. "
                      "The 38.2% level often acts as common shallow resistance in a downtrend.")
elif latest_close >= fib_levels["50%"]:
    analysis_chart3 = ("The current price is between the 38.2% and 50% retracement levels. "
                      "The 50% mark represents a psychological midpoint that often acts as resistance.")
elif latest_close >= fib_levels["61.8%"]:
    analysis_chart3 = ("The current price is between the 50% and 61.8% retracement levels. "
                      "The 61.8% 'golden ratio' typically offers strong resistance; expect a major inflection here.")
elif latest_close >= fib_levels["100%"]:
    analysis_chart3 = ("The current price is between the 61.8% and 100% retracement levels. "
                      "A price above 78.6% (deep retracement) may signal a potential trend reversal.")
else:
    analysis_chart3 = ("The current price is below the 100% retracement level (the recent low). "
                      "This suggests a new low has been established and the downtrend is continuing.")
st.write("**Analysis (Chart 3):**", analysis_chart3)

# ---------------------------
# Chart 4: 50-Day MA vs 200-Day MA
# ---------------------------
st.markdown("### Chart 4: 50-Day MA vs 200-Day MA")
st.line_chart(filtered_data[["SMA50", "SMA200"]])

# Analysis for Chart 4: Comparing 50-day and 200-day SMAs.
if pd.notna(latest_SMA50) and pd.notna(latest_SMA200):
    if latest_SMA50 > latest_SMA200:
        analysis_chart4 = "The 50-day MA is above the 200-day MA, indicating a bullish 'golden cross' scenario."
    else:
        analysis_chart4 = "The 50-day MA is below the 200-day MA, which may indicate a bearish 'death cross' scenario."
    st.write("**Analysis (Chart 4):**", analysis_chart4)
else:
    st.write("**Analysis (Chart 4):** Not enough data to compute the 50-day and 200-day SMAs for this time range.")

st.write("**Disclaimer:** This app is for demonstration and educational purposes only. Not financial advice!")