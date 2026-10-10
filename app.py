import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Binary Signal", layout="centered")

st.title("Forex Signal Analysis (Free)")

st.warning("এটি শিক্ষামূলক প্রোটোটাইপ, নিশ্চিত ট্রেডিং সংকেত নয়।")

# কারেন্সি পেয়ার সিলেকশন
pair = st.selectbox(
    "Forex pair নির্বাচন করুন",
    ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"]
)

# টাইমফ্রেম সিলেকশন
interval = st.selectbox(
    "টাইমফ্রেম নির্বাচন করুন",
    ["1m", "5m", "15m"],
    index=0
)

if st.button("লাইভ Forex ডেটা আনুন ও বিশ্লেষণ করুন", type="primary"):
    with st.spinner("ডেটা আনা হচ্ছে..."):
        try:
            # yfinance থেকে ১ মিনিটের ডেটা ফেচ করা
            data = yf.download(tickers=pair, period="1d", interval=interval)
            
            if not data.empty:
                st.success("সফলভাবে লাইভ ডেটা পাওয়া গেছে!")
                
                # ক্যান্ডেল ডেটা দেখানো
                st.subheader("সাম্প্রতিক ক্যান্ডেল ডেটা")
                st.dataframe(data.tail(10))
                
                # সাধারণ সিগন্যাল লজিক (উদাহরণস্বরূপ)
                last_close = data['Close'].iloc[-1].item()
                prev_close = data['Close'].iloc[-2].item()
                
                st.subheader("বিশ্লেষণ ফলাফল")
                if last_close > prev_close:
                    st.success(f"সংকেত: **CALL (BUY)** 📈 (বর্তমান মূল্য: {last_close:.5f})")
                else:
                    st.error(f"সংকেত: **PUT (SELL)** 📉 (বর্তমান মূল্য: {last_close:.5f})")
            else:
                st.error("ডেটা পাওয়া যায়নি। কিছুক্ষণ পর আবার চেষ্টা করুন (মার্কেট বন্ধ থাকতে পারে)।")
        except Exception as e:
            st.error(f"ত্রুটি ঘটেছে: {e}")
