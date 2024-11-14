import streamlit as st
from copilot import Copilot
import os
import pandas as pd
from datetime import datetime, timedelta
from polygon.rest import RESTClient
import numpy as np

# page set
st.set_page_config(layout="wide", page_icon="🚗")

# Custom CSS for dark theme and metric colors
st.markdown("""
    <style>
        /*  */
        .stApp {
            background-color: #0E1117;
        }
        
        /*  */
        .market-card, .reference-card, .chart-container, .chat-container {
            background-color: #262B3D;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #363C4F;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }
        
        /*  */
        .big-title {
            color: #FFFFFF;
            font-size: 2.5rem;
            font-weight: 600;
            background: linear-gradient(90deg, #262B3D, #1E2330);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /*  */
        [data-testid="stMetricValue"] {
            color: white !important;
        }
        
        /*  */
        [data-testid="stMetricLabel"] {
            color: white !important;
        }
        
        /* */
        .positive {
            color: rgb(0, 200, 0) !important;
        }
        
        /*  */
        .negative {
            color: rgb(255, 75, 75) !important;
        }
        
        /*  */
        p, span, label, h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
        }
        
        /* Reference Card */
        .reference-card h3 {
            color: #FFFFFF !important;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .reference-card li {
            color: #FFFFFF !important;
            margin: 8px 0;
            line-height: 1.6;
        }
        
        .reference-card strong {
            color: #FFFFFF !important;
        }
        
        /* link style */
        .reference-card a {
            color: #7CB9FF !important;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        .reference-card a:hover {
            color: #99CCFF !important;
            text-decoration: underline;
        }
        
        /* tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #262B3D;
            border-radius: 10px;
            padding: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #363C4F;
            border-radius: 5px;
            color: #FFFFFF !important;
            padding: 10px 20px;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            background-color: #262B3D;
            border-radius: 10px;
            padding: 20px;
            margin-top: 10px;
        }
        
        /* text input */
        .stTextInput > div > div {
            background-color: #262B3D;
            color: #FFFFFF;
            border: 1px solid #363C4F;
        }

        /* chart label */
        text {
            fill: #FFFFFF !important;
        }
        
        /* time set */
        em {
            color: #FFFFFF !important;
        }/* message color */
        .stChatMessage {
            background-color: #262B3D !important;
        }
        
        /* message color */
        .stChatMessage p,
        .stChatMessage span,
        .stMarkdown p,
        .stMarkdown span,
        div[data-testid="stChatMessageContent"] {
            color: #FFFFFF !important;
        }
        
        /* message */
        .stChatMessageContent {
            background-color: #363C4F !important;
            color: #FFFFFF !important;
        }
        
        /* color */
        .stChatMessageContent * {
            color: #FFFFFF !important;
        }
        
        /* text color */
        .stTextInput input {
            color: #FFFFFF !important;
        }
    </style>
""", unsafe_allow_html=True)

# Polygon API
POLYGON_API_KEY = "k7hmTlM7ZTaRp8Ku2M7XSk3VJEr5IDSg"
client = RESTClient(api_key=POLYGON_API_KEY)

@st.cache_data(ttl=300)
def get_stock_data():
    try:
        ticker = "LI"
        aggs = list(client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            to=datetime.now().strftime('%Y-%m-%d')
        ))
        
        if not aggs:
            st.warning("No recent data available. Using last known data point.")
            return None
            
        current_price = aggs[-1].close
        prev_close = aggs[-2].close if len(aggs) > 1 else current_price
        price_change = ((current_price - prev_close) / prev_close) * 100
        
        year_aggs = list(client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            to=datetime.now().strftime('%Y-%m-%d')
        ))
        
        fifty_two_week_high = max(agg.high for agg in year_aggs)
        current_volume = aggs[-1].volume
        avg_volume = sum(agg.volume for agg in aggs[:-1]) / len(aggs[:-1]) if len(aggs) > 1 else current_volume
        volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        shares_outstanding = 924700000
        market_cap = current_price * shares_outstanding
        
        return {
            "current_price": current_price,
            "price_change": price_change,
            "market_cap": market_cap,
            "fifty_two_week_high": fifty_two_week_high,
            "volume": current_volume,
            "volume_change": volume_change,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_historical_data():
    try:
        aggs = list(client.get_aggs(
            ticker="LI",
            multiplier=1,
            timespan="day",
            from_=(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
            to=datetime.now().strftime('%Y-%m-%d')
        ))
        
        return pd.DataFrame({
            'Date': [datetime.fromtimestamp(agg.timestamp/1000) for agg in aggs],
            'Price': [agg.close for agg in aggs],
            'Volume': [agg.volume for agg in aggs]
        })
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return None

# Logo&title
header_col1, header_col2 = st.columns([3, 2])
with header_col1:
    st.markdown('<div class="big-title">Chat with Li Auto (NASDAQ: LI) Copilot</div>', unsafe_allow_html=True)
with header_col2:
    st.image("https://logowik.com/content/uploads/images/li-auto5478.jpg", width=300)

# get data
stock_data = get_stock_data()
historical_data = get_historical_data()

# market overview
st.markdown('<div class="market-card">', unsafe_allow_html=True)
st.markdown("### Market Overview")
if stock_data:
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric(
            label="Stock Price",
            value=f"${stock_data['current_price']:.2f}",
            delta=f"{stock_data['price_change']:.1f}%"
        )

    with metric_col2:
        st.metric(
            label="Market Cap",
            value=f"${stock_data['market_cap']/1e9:.1f}B",
            delta=f"{stock_data['price_change']:.1f}%"
        )

    with metric_col3:
        st.metric(
            label="52W High",
            value=f"${stock_data['fifty_two_week_high']:.2f}",
            delta=f"Current: {((stock_data['current_price']/stock_data['fifty_two_week_high'])-1)*100:.1f}%",
            delta_color="inverse"
        )

    with metric_col4:
        st.metric(
            label="Trading Volume",
            value=f"{stock_data['volume']/1e6:.1f}M",
            delta=f"{stock_data['volume_change']:.1f}% avg",
            delta_color="inverse" if stock_data['volume_change'] < 0 else "normal"
        )
st.markdown('</div>', unsafe_allow_html=True)

# chart
if historical_data is not None:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    chart_tab1, chart_tab2 = st.tabs(["Stock Price", "Trading Volume"])

    with chart_tab1:
        st.line_chart(historical_data.set_index('Date')['Price'])

    with chart_tab2:
        st.bar_chart(historical_data.set_index('Date')['Volume'])
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# API Key
st.write(
    "To use this chat feature, please provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
)


chat_col, ref_col = st.columns([2, 1])

# chat
with chat_col:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = st.text_input("Please enter your OpenAI API Key", type="password")

    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.", icon="🗝️")
    else:
        if "messages" not in st.session_state.keys():
            st.session_state.messages = [
                {"role": "assistant", "content": "I am Li Auto Copilot, your AI financial assistant. You can ask me about Li Auto's business, financial metrics, and market performance."}
            ]

        @st.cache_resource
        def load_copilot():
            return Copilot(key=openai_api_key)

        if "chat_copilot" not in st.session_state.keys():
            st.session_state.chat_copilot = load_copilot()

        if prompt := st.chat_input("Ask about Li Auto"):
            st.session_state.messages.append({"role": "user", "content": prompt})

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                retrived_info, answer = st.session_state.chat_copilot.ask(prompt, messages=st.session_state.messages[:-1])
                
                if isinstance(answer, str):
                    st.write(answer)
                else:
                    def generate():
                        for chunk in answer:
                            content = chunk.choices[0].delta.content
                            if content:
                                yield content
                    answer = st.write_stream(generate())

                st.session_state.messages.append({"role": "assistant", "content": answer})
    st.markdown('</div>', unsafe_allow_html=True)

with ref_col:
    st.markdown('<div class="reference-card">', unsafe_allow_html=True)
    st.markdown("### Quick References")
    st.markdown("""
    - **Latest Quarter Results** [[IR Link]](https://ir.lixiang.com/)
        - Revenue: $20.1B
        - Gross Margin: 32.1%
        - Deliveries: 30,000 [[Press Release]](https://ir.lixiang.com/news-releases)
    
    - **Key Products**
        - [Li L9](https://en.wikipedia.org/wiki/Li_L9)
        - [Li L8](https://en.wikipedia.org/wiki/Li_L8)
        - [Li L7](https://en.wikipedia.org/wiki/Li_L7)
    
    - **Useful Links:**
        - [Investor Relations](https://ir.lixiang.com/)
        - [Official Website](https://li-auto.cn/)
        - [SEC Filings](https://ir.lixiang.com/sec-filings)
        - [Corporate Governance](https://ir.lixiang.com/corporate-governance)
    """)
    st.markdown('</div>', unsafe_allow_html=True)


st.markdown("---")
st.markdown(f"*Data updated as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
