import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Insights Chat", layout="wide")


if "chat" not in st.session_state:
    st.session_state.chat = []

if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None



st.markdown("""
<h1 style="text-align:center;">💬 Data Insights Chat</h1>
<p style="text-align:center; font-size:18px;">
AI-агент, который отвечает на вопросы и достаёт данные из базы
</p>
""", unsafe_allow_html=True)

st.divider()



user_msg = st.chat_input("Введите ваш вопрос о продажах...")

if user_msg:
    st.session_state.pending_user_message = user_msg


if st.session_state.pending_user_message:

    msg = st.session_state.pending_user_message
    st.session_state.pending_user_message = None
    st.session_state.chat.append({"role": "user", "content": msg})
    try:
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"message": msg},
            timeout=30
        )
        result = response.json()
    except Exception as e:
        result = {"error": str(e)}

    st.session_state.chat.append({"role": "assistant", "content": result})



def safe_metric(label, value):
    """metric only for numbers and strings, else json"""
    if isinstance(value, (int, float, str)):
        st.metric(label, value)
    else:
        st.write(f"**{label}:**")
        st.json(value)



for msg_index, msg in enumerate(st.session_state.chat):

    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])

    else:
        with st.chat_message("assistant"):
            data = msg["content"]

            if isinstance(data, str):
                st.write(data)

            elif isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)

                    if "amount" in df.columns:
                        non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

                        if "method" in df.columns:
                            x = "method"
                        elif "full_name" in df.columns:
                            x = "full_name"
                        elif "category" in df.columns:
                            x = "category"
                        elif len(non_numeric_cols) > 0:
                            x = non_numeric_cols[0]
                        else:
                            x = None

                        fig = px.bar(
                            df.sort_values("amount", ascending=False).head(10),
                            x=x,
                            y="amount",
                            title="TOP by amount" + (f" by {x}" if x else "")
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            key=f"chart-list-{msg_index}"
                        )
                else:
                    st.json(data)

            elif isinstance(data, dict):

                if "rows" in data and isinstance(data["rows"], list):
                    rows = data["rows"]
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)

                    if "amount" in df.columns:
                        non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

                        if "method" in df.columns:
                            x = "method"
                        elif "full_name" in df.columns:
                            x = "full_name"
                        elif "category" in df.columns:
                            x = "category"
                        elif len(non_numeric_cols) > 0:
                            x = non_numeric_cols[0]
                        else:
                            x = None

                        fig = px.bar(
                            df.sort_values("amount", ascending=False).head(10),
                            x=x,
                            y="amount",
                            title="TOP by amount" + (f" by {x}" if x else "")
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            key=f"chart-dict-{msg_index}"
                        )

                    st.write("### ℹ Информация:")
                    for k, v in data.items():
                        if k != "rows":
                            safe_metric(k, v)

                else:
                    for k, v in data.items():
                        safe_metric(k, v)

            else:
                st.json(data)
