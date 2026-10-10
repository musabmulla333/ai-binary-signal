import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

st.set_page_config(page_title="Binary Signal Prototype", page_icon="📈", layout="centered")

st.title("📈 Forex / OTC Signal Prototype")
st.caption("Educational prototype • 1-minute candles • No automatic trading")

st.warning(
    "এটি শিক্ষামূলক প্রোটোটাইপ, নিশ্চিত ট্রেডিং সিগন্যাল নয়। "
    "Forex ও OTC-এর ডেটা এক নয়। OTC ডেটা সংযুক্ত না থাকলে কোনো OTC signal তৈরি হবে না।"
)

market = st.radio("মার্কেট নির্বাচন করুন", ["Forex", "OTC"], horizontal=True)
pair = st.selectbox("Forex pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"])
api_key = st.text_input(
    "Alpha Vantage API key (এখানে লিখুন; কাউকে শেয়ার করবেন না)",
    type="password",
    help="Key-টি GitHub কোডে লিখবেন না। চাইলে Streamlit Cloud Secrets-এ রাখুন।"
)

st.caption("টাইমফ্রেম: 1 মিনিট")

if market == "OTC":
    st.info(
        "OTC signal বন্ধ রাখা হয়েছে: এই প্রোটোটাইপে আপনার broker-এর অনুমোদিত OTC feed নেই। "
        "সাধারণ Forex ডেটা দিয়ে OTC signal বানানো নিরাপদ বা নির্ভরযোগ্য নয়।"
    )
    st.stop()

if st.button("লাইভ Forex ডেটা আনুন ও বিশ্লেষণ করুন", type="primary", use_container_width=True):
    if not api_key.strip():
        st.error("আগে Alpha Vantage API key দিন।")
        st.stop()

    from_symbol, to_symbol = pair.split("/")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "interval": "1min",
        "outputsize": "compact",
        "apikey": api_key.strip(),
    }

    try:
        with st.spinner("ডেটা আনা হচ্ছে..."):
            response = requests.get(url, params=params, timeout=25)
            response.raise_for_status()
            payload = response.json()

        series_key = next(
            (k for k in payload.keys() if "Time Series FX" in k),
            None
        )
        if not series_key:
            msg = payload.get("Note") or payload.get("Information") or payload.get("Error Message")
            st.error(
                "API থেকে ক্যান্ডেল ডেটা পাওয়া যায়নি। "
                + (str(msg) if msg else "API key, API access বা provider-এর সীমা পরীক্ষা করুন।")
            )
            st.stop()

        df = pd.DataFrame.from_dict(payload[series_key], orient="index")
        df.index = pd.to_datetime(df.index, errors="coerce")
        df = df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
        })
        df = df[["Open", "High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce")
        df = df.dropna().sort_index()

        if len(df) < 10:
            st.error("বিশ্লেষণের জন্য অন্তত ১০টি বৈধ candle দরকার।")
            st.stop()

        latest_time = df.index[-1]
        age_minutes = (datetime.now(timezone.utc).replace(tzinfo=None) - latest_time.to_pydatetime()).total_seconds() / 60

        st.subheader(f"{pair} • সর্বশেষ 1-minute candles")
        st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True)

        # Avoid implying stale data is live. If latest candle is over 3 minutes old, show WAIT.
        close = df["Close"]
        sma5 = close.tail(5).mean()
        sma10 = close.tail(10).mean()
        momentum = close.iloc[-1] - close.iloc[-4]

        st.metric("SMA 5", f"{sma5:.6f}")
        st.metric("SMA 10", f"{sma10:.6f}")
        st.metric("3-candle momentum", f"{momentum:+.6f}")
        st.caption(f"সর্বশেষ candle: {latest_time} • ডেটার আনুমানিক বয়স: {age_minutes:.1f} মিনিট")

        if age_minutes > 3:
            signal = "WAIT"
            reason = "সর্বশেষ candle পুরোনো; লাইভ বলে ধরে নেওয়া যাবে না।"
        elif sma5 > sma10 and momentum > 0:
            signal = "BUY (demo)"
            reason = "SMA 5, SMA 10-এর ওপরে এবং momentum positive।"
        elif sma5 < sma10 and momentum < 0:
            signal = "SELL (demo)"
            reason = "SMA 5, SMA 10-এর নিচে এবং momentum negative।"
        else:
            signal = "WAIT"
            reason = "ট্রেন্ড ও momentum একমত নয়।"

        if signal.startswith("BUY"):
            st.success(signal)
        elif signal.startswith("SELL"):
            st.error(signal)
        else:
            st.info(signal)

        st.write(reason)
        st.caption(
            "এটি নিয়মভিত্তিক demo signal, প্রশিক্ষিত AI মডেল নয়। "
            "সিগন্যালের accuracy যাচাই করা হয়নি; আসল টাকায় ট্রেড করার জন্য ব্যবহার করবেন না।"
        )
    except requests.RequestException:
        st.error("ডেটা সার্ভিসে সংযোগ করা যায়নি। ইন্টারনেট বা provider-এর অবস্থা পরে আবার পরীক্ষা করুন।")
    except (ValueError, KeyError, TypeError) as exc:
        st.error(f"ডেটা পড়তে সমস্যা হয়েছে: {exc}")

with st.expander("OTC কেন বন্ধ আছে?"):
    st.write(
        "OTC দাম আপনার নির্দিষ্ট broker/platform-এর নিজস্ব feed হতে পারে। "
        "অনুমোদিত ও নির্ভরযোগ্য feed ছাড়া Forex-এর দামকে OTC হিসেবে দেখানো হবে না।"
    )

with st.expander("নিরাপত্তা ও পরবর্তী ধাপ"):
    st.markdown(
        "- API key GitHub-এ প্রকাশ করবেন না।\n"
        "- Streamlit Cloud-এর Secrets ব্যবহার করতে পারেন।\n"
        "- পরে historical data দিয়ে backtest করতে হবে।\n"
        "- এই অ্যাপ স্বয়ংক্রিয় ট্রেড করে না।"
    )
