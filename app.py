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
# USER NAME INPUT
# -----------------------------
user_name = st.text_input("👤 Your Name")

# -----------------------------
# PARTY INPUT (Dropdown + Manual)
# -----------------------------
party_list = party_df.iloc[:, 0].dropna().unique().tolist()

party_option = st.selectbox("🏪 Select Party", ["-- Select --"] + party_list)
#new_party = st.text_input("➕ Or Enter New Party")

if party_option != "-- Select --":
    party = party_option
#elif new_party:
    #party = new_party
else:
    party = None

# -----------------------------
# SESSION STATE (CART)
# -----------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

# -----------------------------
# INPUT SECTION
# -----------------------------

if "qty" not in st.session_state:
    st.session_state.qty = 1

if "last_sku" not in st.session_state:
    st.session_state.last_sku = None

st.subheader("➕ Add Item")

col1, col2 = st.columns(2)

with col1:
    sku_list = ["-- Select SKU --"] + df["SKU"].tolist()
    sku = st.selectbox("Select SKU", sku_list, key="sku")

    if st.session_state.last_sku != sku:
        st.session_state.qty = 1
        st.session_state.last_sku = sku

#selected_stock = df[df["SKU"] == sku]["STOCK"].values


#if len(selected_stock) > 0:
    #available_stock = int(selected_stock[0])
#else:
    #available_stock = 0

# SHOW STOCK
#st.info(f"📦 Available Stock: {available_stock}")

with col2:
    qty = st.number_input(
        "Quantity",
        min_value=1,
        step=1,
        key="qty"
    )

# -----------------------------
# ADD TO CART
# -----------------------------
if st.button("➕ Add to Cart"):
    found = False

    for item in st.session_state.cart:
        if item["SKU"] == sku:
            item["QTY"] += qty
            found = True
            break

    if not found:
        st.session_state.cart.append({
            "SKU": sku,
            "QTY": qty
        })

    st.success("Item Added ✅")

# -----------------------------
# CART DISPLAY
# -----------------------------


st.subheader("🧾 Your Order")

if st.session_state.cart:

    for i, item in enumerate(st.session_state.cart):

        # 📱 Mobile friendly card layout
        st.markdown(f"""
        <div style="border:1px solid #ddd; padding:10px; border-radius:8px; margin-bottom:8px;">
            <div><b>SKU:</b> {item['SKU']}</div>
            <div><b>QTY:</b> {item['QTY']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("❌ Remove", key=f"remove_{i}"):
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
# SUBMIT ORDER (FAST 🚀)
# -----------------------------
if st.button("✅ Submit Order"):

    if not user_name:
        st.warning("Apna naam daalo ❌")

    elif not party:
        st.warning("Party select ya enter karo ❌")

    elif not st.session_state.cart:
        st.warning("Cart khali hai ❌")

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

        # 🔥 FAST BACKGROUND SUBMIT
        threading.Thread(target=send_data, args=(payload,)).start()

        st.session_state.cart = []

        st.success("Order Submitted 🚀")
        st.toast(f"Order placed by {user_name} ⚡")
