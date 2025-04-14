import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Set page configuration at the very top.
st.set_page_config(page_title="Dynamic Index Technical Indicators", layout="centered")

st.title("Dynamic Technical Indicators for Market Indices")
st.write("This app shows technical indicators for your chosen index. Select an index and time period below.")

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

# Create a dictionary for the various time period options.
# For each option (except "All Time"), we map it to a corresponding Pandas DateOffset.
time_options = {
    "1d": pd.DateOffset(days=1),
    "3d": pd.DateOffset(days=3),
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

# Let the user select the time period from the available options.
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

# 1. 200-day Simple Moving Average (SMA)
filtered_data["SMA200"] = filtered_data["Close"].rolling(window=200).mean()

# 2. 50-day Simple Moving Average (SMA)
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

# ---------------------------
# Chart Rendering
# ---------------------------

st.markdown("### Chart 1: Price & 200-Day SMA")
st.line_chart(filtered_data[["Close", "SMA200"]])

st.markdown("### Chart 2: MACD & Signal")
st.line_chart(filtered_data[["MACD", "Signal"]])

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

st.markdown("### Chart 4: 50-Day MA vs 200-Day MA")
st.line_chart(filtered_data[["SMA50", "SMA200"]])

st.write("**Disclaimer:** This app is for demonstration and educational purposes only. Not financial advice!")