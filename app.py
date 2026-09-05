import sys
from pathlib import Path
import importlib

import streamlit as st


# ==========================================================
# PROJECT PATH
# ==========================================================

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent),
)


# ==========================================================
# DATABASE
# ==========================================================

import database.db as db

db = importlib.reload(db)


# ==========================================================
# FRONTEND
# ==========================================================

from frontend import (
    upload_page,
    chat_page,
    dashboard,
)

from frontend.sidebar import render_sidebar


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="MemoryVault AI",
    page_icon="🧠",
    layout="wide",
)


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

db.initialize_database()


# ==========================================================
# FIXED MEMORYVAULT AI HEADER
# ==========================================================

st.markdown(
    """
    <style>

    /* ======================================================
       FIXED APPLICATION HEADER
       ====================================================== */

    .stApp::before {
        content: "🧠  MemoryVault AI";

        position: fixed;

        top: 0;
        left: 50px;
        right: 0;

        height: 68px;

        background: #0e1117;

        border-bottom: 1px solid #30333d;

        z-index: 999999;

        display: flex;
        align-items: center;

        padding-left: 260px;

        box-sizing: border-box;

        color: white;

        font-size: 25px;

        font-weight: 700;

        letter-spacing: -0.5px;

    }


    /* ======================================================
       KEEP PAGE CONTENT BELOW HEADER
       ====================================================== */

    .block-container {
        padding-top: 105px !important;
    }


    /* ======================================================
       KEEP STREAMLIT TOP BAR TRANSPARENT
       ====================================================== */

    header[data-testid="stHeader"] {
        background: transparent;
    }


    /* ======================================================
       SIDEBAR ABOVE / BELOW HEADER CLEANLY
       ====================================================== */

    section[data-testid="stSidebar"] {
        z-index: 1000000;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# SIDEBAR
# ==========================================================

page = render_sidebar()


# ==========================================================
# APPLICATION PAGES
# ==========================================================

PAGES = {
    "Upload": upload_page.render_upload_page,
    "Chat": chat_page.render_chat_page,
    "Dashboard": dashboard.render_dashboard,
    "Timeline": dashboard.render_timeline,
    "Recall": dashboard.render_recall,
}


# ==========================================================
# RENDER CURRENT PAGE
# ==========================================================

PAGES[page]()