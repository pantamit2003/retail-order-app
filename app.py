import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import threading
import pytz

st.title("📦 Retail Order Management")

# -----------------------------
# DATE
# -----------------------------
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
today = datetime.now().strftime("%d-%m-%Y")
st.subheader(f"📅 Date: {today}")
date_time = now_ist.strftime("%d-%m-%Y %H:%M:%S")

# -----------------------------
# GOOGLE SHEET (STOCK)
# -----------------------------
stock_url = "https://docs.google.com/spreadsheets/d/1c_B12xm6U9k9InwSNmu7_dwFRhiXe-r2wRCgbZd2hLA/export?format=csv"

@st.cache_data(ttl=60)
def load_stock():
    df = pd.read_csv(stock_url)
    df.columns = df.columns.str.strip().str.upper()
    return df

df = load_stock()

# -----------------------------
# GOOGLE SHEET (PARTY)
# -----------------------------
@st.cache_data(ttl=60)
def load_parties():
    party_url = "https://docs.google.com/spreadsheets/d/1c_B12xm6U9k9InwSNmu7_dwFRhiXe-r2wRCgbZd2hLA/export?format=csv&gid=1688755592"
    party_df = pd.read_csv(party_url)
    party_df.columns = party_df.columns.str.strip().str.upper()
    return party_df

party_df = load_parties()

# -----------------------------
# SESSION STATE INITIALISATION
# -----------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

if "last_sku" not in st.session_state:
    st.session_state.last_sku = None

if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# FIX: "submitted" flag lets us show balloons + toast AFTER the rerun,
# on the already-fresh form, instead of before it.
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "submitted_by" not in st.session_state:
    st.session_state.submitted_by = ""

# FIX: Read form_version into `v` ONCE here — it is now the correct,
# already-incremented value because the rerun has already happened.
v = st.session_state.form_version

# -----------------------------
# Show post-submit feedback on the fresh form
# -----------------------------
if st.session_state.submitted:
    st.balloons()
    st.success("Order Submitted Successfully 🚀")
    st.toast(f"Order placed by {st.session_state.submitted_by} ⚡")
    st.session_state.submitted = False      # reset flag so it shows only once
    st.session_state.submitted_by = ""

# -----------------------------
# USER NAME INPUT
# -----------------------------
user_name = st.text_input("👤 Your Name", key=f"user_name_{v}")

# -----------------------------
# PARTY INPUT (Dropdown)
# -----------------------------
party_list = party_df.iloc[:, 0].dropna().unique().tolist()
party_option = st.selectbox(
    "🏪 Select Party",
    ["-- Select --"] + party_list,
    key=f"party_{v}"
)
party = party_option if party_option != "-- Select --" else None

# -----------------------------
# INPUT SECTION
# -----------------------------
st.subheader("➕ Add Item")
col1, col2 = st.columns(2)

with col1:
    sku_list = ["-- Select SKU --"] + df["SKU"].tolist()
    sku = st.selectbox("Select SKU", sku_list, key=f"sku_{v}")

    if st.session_state.last_sku != sku:
        st.session_state[f"qty_{v}"] = 1
        st.session_state.last_sku = sku

with col2:
    qty = st.number_input(
        "Quantity",
        min_value=1,
        step=1,
        key=f"qty_{v}"
    )

# -----------------------------
# ADD TO CART
# -----------------------------
if st.button("➕ Add to Cart"):
    if sku == "-- Select SKU --":
        st.warning("Pehle ek valid SKU select karo ❌")
    else:
        found = False
        for item in st.session_state.cart:
            if item["SKU"] == sku:
                item["QTY"] += qty
                found = True
                break
        if not found:
            st.session_state.cart.append({"SKU": sku, "QTY": qty})
        st.success("Item Added ✅")

# -----------------------------
# CART DISPLAY
# -----------------------------
st.subheader("🧾 Your Order")

if st.session_state.cart:
    for i, item in enumerate(st.session_state.cart):
        st.markdown(f"""
        <div style="border:1px solid #ddd; padding:10px; border-radius:8px; margin-bottom:8px;">
            <div><b>SKU:</b> {item['SKU']}</div>
            <div><b>QTY:</b> {item['QTY']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("❌ Remove", key=f"remove_{i}_{v}"):
            st.session_state.cart.pop(i)
            st.rerun()

    total_qty = sum([item["QTY"] for item in st.session_state.cart])
    st.info(f"Total Quantity: {total_qty}")
else:
    st.warning("Abhi koi item add nahi hua ❌")

# -----------------------------
# CLEAR CART
# -----------------------------
if st.button("🗑 Clear Cart"):
    st.session_state.cart = []
    st.rerun()

# -----------------------------
# BACKGROUND FUNCTION (FAST)
# -----------------------------
def send_data(payload):
    try:
        url = "https://script.google.com/macros/s/AKfycbzoeuciiCqzwm6O_UHv-h_R8wkdeEX0TMTUSV64Ho1T-Ut3YoBw5rB3JtT0Sx8hkm4U/exec"
        requests.post(url, json=payload, timeout=3)
    except:
        pass

# -----------------------------
# SUBMIT ORDER 🚀
# -----------------------------
if st.button("✅ Submit Order"):
    if not user_name:
        st.warning("Apna naam daalo ❌")
    elif not party:
        st.warning("Party select karo ❌")
    elif not st.session_state.cart:
        st.warning("Cart khali hai ❌")
    else:
        invalid_skus = [
            item["SKU"] for item in st.session_state.cart
            if item["SKU"] == "-- Select SKU --"
        ]
        if invalid_skus:
            st.warning("Cart mein invalid SKU hai. Pehle remove karo ❌")
        else:
            payload = []
            for item in st.session_state.cart:
                payload.append({
                    "date": date_time,
                    "user": user_name,
                    "party": party,
                    "sku": str(item["SKU"]),
                    "qty": int(item["QTY"])
                })

            # 🔥 Background submit
            threading.Thread(target=send_data, args=(payload,)).start()

            # Clear cart & tracking state
            st.session_state.cart = []
            st.session_state.last_sku = None

            # FIX: Set flag + increment version BEFORE rerun.
            # On the next run, v will equal the new form_version,
            # so all widget keys are fresh and render at defaults.
            st.session_state.submitted = True
            st.session_state.submitted_by = user_name
            st.session_state.form_version += 1

            # FIX: rerun so the new form_version takes effect immediately.
            st.rerun()
