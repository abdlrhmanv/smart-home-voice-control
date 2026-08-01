import streamlit as st


def device_card(icon, title, status, color):

    st.markdown(
        f"""
        <div style="
            background:#1E293B;
            padding:25px;
            border-radius:20px;
            border-left:8px solid {color};
            text-align:center;
            box-shadow:0px 0px 18px rgba(0,0,0,.35);
        ">

            <div style="font-size:50px;">
                {icon}
            </div>

            <div style="
                color:white;
                font-size:24px;
                font-weight:bold;
                margin-top:10px;
            ">
                {title}
            </div>

            <div style="
                color:{color};
                font-size:28px;
                font-weight:bold;
                margin-top:15px;
            ">
                {status}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )