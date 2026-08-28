import streamlit as st
import pandas as pd
import os
import time
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Real or AI?",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================================================
# CONSTANTS
# ==================================================

RESULT_FILE = "data/responses_final.csv"
MEDIA_BASE = Path("media")

# Colours
PURPLE = "#6C2E8B"
LIGHT_PURPLE = "#F3EDF7"
SOFT_PURPLE = "#DCC8E8"
GREEN = "#248A57"
RED = "#B33A3A"

# ==================================================
# SUPABASE CLIENT (if secrets available)
# ==================================================

try:
    from supabase import create_client, Client
    supabase: Optional[Client] = None
    if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        supabase = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
except ImportError:
    supabase = None
    st.warning("Supabase paketi yüklü değil. pip install supabase")

# ==================================================
# CSS - Enhanced Design
# ==================================================

def inject_custom_css():
    st.html(
        f"""
        <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,600;14..32,700;14..32,800;14..32,900&display=swap" rel="stylesheet">
        <style>
            * {{
                font-family: 'Inter', sans-serif;
            }}

            .block-container {{
                max-width: 1200px;
                padding-top: 2.2rem;
                padding-bottom: 4rem;
            }}

            .hero {{
                text-align: center;
                padding: 0.4rem 0 1.4rem 0;
                margin-top: 0.2rem;
            }}

            .hero-badge {{
                display: inline-block;
                color: {PURPLE};
                background: {LIGHT_PURPLE};
                border: 1px solid {SOFT_PURPLE};
                padding: 0.4rem 1rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 0.9rem;
            }}

            .hero-title {{
                font-size: clamp(2.8rem, 7vw, 4.6rem);
                font-weight: 900;
                line-height: 1.1;
                margin: 0;
                background: linear-gradient(135deg, {PURPLE}, #A855F7);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}

            .hero-subtitle {{
                max-width: 700px;
                margin: 1rem auto 0 auto;
                opacity: 0.75;
                font-size: 1.1rem;
                line-height: 1.6;
            }}

            .purple-line {{
                height: 4px;
                width: 60px;
                border-radius: 100px;
                background: {PURPLE};
                margin: 1rem auto 1.5rem auto;
            }}

            .round-label {{
                width: fit-content;
                margin: 0 auto 0.8rem auto;
                color: {PURPLE};
                background: {LIGHT_PURPLE};
                padding: 0.4rem 1rem;
                border-radius: 999px;
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.05em;
            }}

            .question-heading {{
                font-size: 1.3rem;
                font-weight: 800;
                margin-bottom: 0.2rem;
            }}

            .question-subheading {{
                opacity: 0.65;
                font-size: 0.95rem;
                margin-bottom: 0.8rem;
            }}

            div[data-testid="stVerticalBlockBorderWrapper"] {{
                border-radius: 20px;
                border-color: {SOFT_PURPLE};
                box-shadow: 0 8px 24px rgba(108, 46, 139, 0.06);
                transition: box-shadow 0.2s ease;
            }}

            div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
                box-shadow: 0 12px 32px rgba(108, 46, 139, 0.10);
            }}

            .stButton > button,
            .stFormSubmitButton > button {{
                border-radius: 14px;
                min-height: 52px;
                font-weight: 700;
                font-size: 1rem;
                transition: all 0.2s ease;
                border: none;
            }}

            .stButton > button:hover,
            .stFormSubmitButton > button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(108, 46, 139, 0.25);
            }}

            button[kind="primary"] {{
                background: {PURPLE} !important;
                color: white !important;
            }}

            button[kind="primary"]:hover {{
                background: #7C3E9E !important;
            }}

            div[data-testid="stTextInput"] input {{
                border-radius: 14px;
                min-height: 52px;
                font-size: 1rem;
                border: 1.5px solid {SOFT_PURPLE};
                transition: border-color 0.2s;
            }}

            div[data-testid="stTextInput"] input:focus {{
                border-color: {PURPLE};
                box-shadow: 0 0 0 3px rgba(108, 46, 139, 0.15);
            }}

            div[data-testid="stRadio"] label p {{
                font-weight: 600;
                font-size: 1rem;
            }}

            div[data-testid="stRadio"] label {{
                padding: 0.5rem 0.8rem;
                border-radius: 12px;
                transition: background 0.15s;
            }}

            div[data-testid="stRadio"] label:hover {{
                background: {LIGHT_PURPLE};
            }}

            div[data-testid="stProgress"] > div > div > div > div {{
                background: linear-gradient(90deg, {PURPLE}, #A855F7);
                border-radius: 100px;
            }}

            .final-score {{
                text-align: center;
                padding: 1.5rem 0 2rem 0;
            }}

            .score-number {{
                font-size: 4.8rem;
                font-weight: 900;
                background: linear-gradient(135deg, {PURPLE}, #A855F7);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                line-height: 1.2;
                margin: 0.5rem 0;
            }}

            .score-caption {{
                font-size: 1.1rem;
                opacity: 0.7;
            }}

            .review-title {{
                text-align: center;
                color: {PURPLE};
                font-size: 1.7rem;
                font-weight: 850;
                margin-top: 2.5rem;
                margin-bottom: 0.3rem;
            }}

            .review-subtitle {{
                text-align: center;
                opacity: 0.65;
                margin-bottom: 1.5rem;
            }}

            .correct-box {{
                background: rgba(36, 138, 87, 0.08);
                border-left: 5px solid {GREEN};
                padding: 1rem 1.2rem;
                border-radius: 12px;
                margin-bottom: 0.8rem;
            }}

            .incorrect-box {{
                background: rgba(179, 58, 58, 0.08);
                border-left: 5px solid {RED};
                padding: 1rem 1.2rem;
                border-radius: 12px;
                margin-bottom: 0.8rem;
            }}

            .metric-card {{
                background: {LIGHT_PURPLE};
                border-radius: 16px;
                padding: 1.2rem 1rem;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.02);
            }}

            .metric-value {{
                font-size: 2rem;
                font-weight: 800;
                color: {PURPLE};
            }}

            .metric-label {{
                font-size: 0.9rem;
                opacity: 0.7;
                margin-top: 0.2rem;
            }}

            .leaderboard-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
            }}
            .leaderboard-table th {{
                background: {LIGHT_PURPLE};
                color: {PURPLE};
                font-weight: 700;
                padding: 0.8rem 0.5rem;
                text-align: center;
            }}
            .leaderboard-table td {{
                padding: 0.6rem 0.5rem;
                text-align: center;
                border-bottom: 1px solid {SOFT_PURPLE};
            }}
            .leaderboard-table tr:hover {{
                background: {LIGHT_PURPLE};
            }}
            .leaderboard-rank {{
                font-weight: 800;
                color: {PURPLE};
            }}

            @media (max-width: 640px) {{
                .block-container {{
                    padding-left: 1rem;
                    padding-right: 1rem;
                }}
                .metric-value {{
                    font-size: 1.6rem;
                }}
            }}
        </style>
        """
    )


# ==================================================
# ROUND DEFINITIONS
# ==================================================

ROUNDS: List[Dict[str, Any]] = [
    {
        "id": "video1",
        "type": "single_video",
        "file": "media/single/video1.mp4",
        "ground_truth": "Real",
        "notes": "authentic"
    },
    {
        "id": "video2",
        "type": "single_video",
        "file": "media/single/video2.mp4",
        "ground_truth": "AI-generated",
        "notes": "ai_generated"
    },
    {
        "id": "video3",
        "type": "single_video",
        "file": "media/single/video3.mp4",
        "ground_truth": "Real",
        "notes": "authentic"
    },
    {
        "id": "video4",
        "type": "single_video",
        "file": "media/single/video4.mp4",
        "ground_truth": "Real",
        "notes": "authentic"
    },
    {
        "id": "video5",
        "type": "single_video",
        "file": "media/single/video5.mp4",
        "ground_truth": "AI-generated",
        "notes": "ai_generated"
    },
    {
        "id": "video6",
        "type": "single_video",
        "file": "media/single/video6.mp4",
        "ground_truth": "Real",
        "notes": "edited_non_ai"
    },
    {
        "id": "pair1",
        "type": "pair_video",
        "left": "media/pairs/pair1_left.mp4",
        "right": "media/pairs/pair1_right.mp4",
        "ground_truth": "Left",
        "notes": "left_ai_right_real"
    },
    {
        "id": "pair2",
        "type": "pair_video",
        "left": "media/pairs/pair2_left.mp4",
        "right": "media/pairs/pair2_right.mp4",
        "ground_truth": "Right",
        "notes": "left_real_right_ai"
    },
    {
        "id": "delft",
        "type": "pair_image",
        "left": "media/delft/real.jpg",
        "right": "media/delft/ai.jpg",
        "ground_truth": "Right",
        "notes": "left_real_right_ai"
    }
]

# ==================================================
# SESSION STATE INITIALISATION
# ==================================================

def init_session_state():
    defaults = {
        "started": False,
        "participant_name": "",
        "participant_id": None,
        "current_round": 0,
        "responses": [],
        "round_start_time": None,
        "saved": False,
        "post_quiz_answered": False,
        "post_quiz_responses": {},
        "last_scroll_key": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def media_file_exists(path: str) -> bool:
    p = Path(path)
    return p.exists() and p.stat().st_size > 0


def validate_round_media(round_data: Dict[str, Any]) -> List[str]:
    missing = []
    if round_data["type"] == "single_video":
        if not media_file_exists(round_data["file"]):
            missing.append(round_data["file"])
    elif round_data["type"] in ("pair_video", "pair_image"):
        for key in ("left", "right"):
            if not media_file_exists(round_data[key]):
                missing.append(round_data[key])
    return missing


def insert_response_to_supabase(row: Dict[str, Any]):
    """Insert a single response row into Supabase."""
    if supabase is None:
        return
    try:
        # Convert boolean to string for 'correct' field
        row_copy = row.copy()
        if isinstance(row_copy["correct"], bool):
            row_copy["correct"] = str(row_copy["correct"])
        # Post-quiz entries have empty ground_truth etc.
        supabase.table("responses").insert(row_copy).execute()
    except Exception as e:
        st.warning(f"Supabase insert error: {e}")


def save_results():
    """Append current session responses to CSV and Supabase."""
    os.makedirs("data", exist_ok=True)
    columns = [
        "participant_name", "participant_id", "timestamp",
        "round", "stimulus_id", "stimulus_type", "stimulus_notes",
        "ground_truth", "answer", "correct", "confidence",
        "response_time_seconds"
    ]
    df = pd.DataFrame(st.session_state.responses, columns=columns)
    
    # Write to CSV (fallback)
    if os.path.exists(RESULT_FILE):
        df.to_csv(RESULT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(RESULT_FILE, index=False)
    
    # Insert each row to Supabase
    for _, row in df.iterrows():
        insert_response_to_supabase(row.to_dict())


def save_post_quiz():
    """Save post-quiz answers to CSV and Supabase."""
    if not st.session_state.post_quiz_responses:
        return
    os.makedirs("data", exist_ok=True)
    row = {
        "participant_name": st.session_state.participant_name,
        "participant_id": st.session_state.participant_id,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "round": 0,
        "stimulus_id": "post_quiz",
        "stimulus_type": "post_quiz",
        "stimulus_notes": "",
        "ground_truth": "",
        "answer": json.dumps(st.session_state.post_quiz_responses),
        "correct": "",
        "confidence": 0,
        "response_time_seconds": 0
    }
    # Write to CSV
    df = pd.DataFrame([row])
    if os.path.exists(RESULT_FILE):
        df.to_csv(RESULT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(RESULT_FILE, index=False)
    # Insert to Supabase
    insert_response_to_supabase(row)


def get_all_responses() -> pd.DataFrame:
    """Fetch all responses from CSV (fallback) or Supabase if available."""
    if supabase is not None:
        try:
            res = supabase.table("responses").select("*").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            st.warning(f"Supabase fetch error: {e}")
    # Fallback to CSV
    if os.path.exists(RESULT_FILE):
        return pd.read_csv(RESULT_FILE)
    return pd.DataFrame()


def restart_quiz():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def scroll_to_top_once(page_key: str):
    """Scroll to the top once when the user moves to a new page or round."""
    if st.session_state.get("last_scroll_key") == page_key:
        return

    st.session_state["last_scroll_key"] = page_key

    st.components.v1.html(
        """
        <script>
            window.parent.scrollTo(0, 0);
        </script>
        """,
        height=0,
    )


# ==================================================
# UI COMPONENTS
# ==================================================

def render_hero():
    st.html(
        """
        <div class="hero">
            <div class="hero-badge">AI DeMoS Lab - TU Delft</div>
            <div class="hero-title">Real or AI?</div>
            <div class="purple-line"></div>
            <div class="hero-subtitle">
                A short study about how we judge real, edited and AI-generated media online.
            </div>
        </div>
        """
    )


def render_start_screen():
    scroll_to_top_once("start")
    render_hero()

    # Short introduction
    with st.container(border=True):
        st.markdown(
            """
### Why this study?

A lot of the early discussion around AI-generated media focused on political deepfakes and the idea that they could strongly manipulate public opinion. That did not always play out as dramatically as expected.

At the same time, AI-generated content became much more common in everyday social media feeds. After talking about this with Jordi at the DeMoS Lab, I became more interested in this everyday kind of exposure - people scrolling past real, edited and AI-generated content mixed together.

This short study looks at how people judge those different kinds of media.
            """
        )

    st.write("")

    col_left, col_center, col_right = st.columns([0.55, 2.2, 0.55])
    with col_center:
        st.image("media/demos_lab.png", use_container_width=True)

    st.write("")

    with st.container(border=True):
        st.html(f"""
            <div style="color:{PURPLE}; font-weight:800; font-size:1.4rem; margin-bottom:0.7rem;">
                How it works
            </div>
        """)

        st.markdown(
            """
You will see **9 pieces of media**.

For each one, choose whether you think it is real or AI-generated and tell us how confident you are.

Some rounds show two items side by side. Go with your own judgement.

**Estimated time: 4-6 minutes.**
            """
        )

        with st.form("start_form"):
            name = st.text_input(
                "Enter your name or nickname",
                placeholder="e.g. Umut"
            )

            submitted = st.form_submit_button(
                "Start",
                type="primary",
                use_container_width=True
            )

            if submitted:
                cleaned = " ".join(name.split())

                if not cleaned:
                    st.warning("Please enter your name or nickname.")
                else:
                    st.session_state.participant_name = cleaned
                    st.session_state.participant_id = str(uuid.uuid4())[:8]
                    st.session_state.current_round = 0
                    st.session_state.responses = []
                    st.session_state.saved = False
                    st.session_state.round_start_time = time.time()
                    st.session_state.started = True
                    st.session_state.post_quiz_answered = False
                    st.session_state.post_quiz_responses = {}
                    st.rerun()

def render_single_video(round_data: Dict[str, Any]):
    with st.container(border=True):
        missing = validate_round_media(round_data)
        if missing:
            st.warning(f"⚠️ Media file not found: {missing[0]}. Please check your assets.")
            return
        _, center, _ = st.columns([1, 1.65, 1])
        with center:
            st.video(round_data["file"])
        st.html("""
            <div class="question-heading">Is this video AI-generated?</div>
            <div class="question-subheading">Go with your first impression.</div>
        """)
        return st.radio(
            "Answer",
            ["Real", "AI-generated", "Not sure"],
            index=None,
            horizontal=True,
            label_visibility="collapsed",
            key=f"answer_{st.session_state.current_round}"
        )


def render_pair_video(round_data: Dict[str, Any]):
    missing = validate_round_media(round_data)
    if missing:
        st.warning(f"⚠️ Media file(s) missing: {', '.join(missing)}")
        return
    st.html(f"""
        <div style="text-align:center; color:{PURPLE}; font-size:1.4rem; font-weight:800;">
            Which video is AI-generated?
        </div>
        <div style="text-align:center; opacity:0.65; margin-bottom:1rem;">
            One of these videos is AI-generated.
        </div>
    """)
    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800; margin-bottom:0.4rem;'>← LEFT</div>")
        st.video(round_data["left"])
    with right_col:
        st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800; margin-bottom:0.4rem;'>RIGHT →</div>")
        st.video(round_data["right"])
    st.write("")
    with st.container(border=True):
        return st.radio(
            "Which video is AI-generated?",
            ["Left", "Right", "Not sure"],
            index=None,
            horizontal=True,
            key=f"answer_{st.session_state.current_round}"
        )


def render_pair_image(round_data: Dict[str, Any]):
    missing = validate_round_media(round_data)
    if missing:
        st.warning(f"⚠️ Image file(s) missing: {', '.join(missing)}")
        return
    st.html(f"""
        <div style="text-align:center; color:{PURPLE}; font-size:1.4rem; font-weight:800;">
            TU Delft image comparison
        </div>
        <div style="text-align:center; opacity:0.65; margin-bottom:1rem;">
            One image is authentic. The other is AI-generated.
        </div>
    """)
    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800; margin-bottom:0.4rem;'>← LEFT</div>")
        st.image(round_data["left"], use_container_width=True)
    with right_col:
        st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800; margin-bottom:0.4rem;'>RIGHT →</div>")
        st.image(round_data["right"], use_container_width=True)
    st.write("")
    with st.container(border=True):
        return st.radio(
            "Which image is AI-generated?",
            ["Left", "Right", "Not sure"],
            index=None,
            horizontal=True,
            key=f"answer_{st.session_state.current_round}"
        )


def render_round():
    round_num = st.session_state.current_round
    round_data = ROUNDS[round_num]

    scroll_to_top_once(f"round_{round_num}")

    st.html(f'<div class="round-label">ROUND {round_num + 1} OF {len(ROUNDS)}</div>')
    st.progress((round_num + 1) / len(ROUNDS))
    st.write("")

    if round_data["type"] == "single_video":
        answer = render_single_video(round_data)
    elif round_data["type"] == "pair_video":
        answer = render_pair_video(round_data)
    elif round_data["type"] == "pair_image":
        answer = render_pair_image(round_data)
    else:
        st.error("Unknown round type.")
        return

    st.write("")
    with st.container(border=True):
        st.html("""
            <div class="question-heading">How confident are you?</div>
            <div class="question-subheading">
                1 = pure guess &nbsp;&nbsp;|&nbsp;&nbsp; 5 = very confident
            </div>
        """)
        _, slider_col, _ = st.columns([0.3, 3, 0.3])
        with slider_col:
            confidence = st.slider(
                "Confidence",
                min_value=1, max_value=5, value=3,
                label_visibility="collapsed",
                key=f"confidence_{round_num}"
            )

    st.write("")
    _, btn_col, _ = st.columns([1.2, 1, 1.2])
    with btn_col:
        next_clicked = st.button("Lock answer →", type="primary", use_container_width=True)

    if next_clicked:
        if answer is None:
            st.warning("Please choose an answer before continuing.")
            return

        response_time = round(time.time() - st.session_state.round_start_time, 2)
        correct = (answer == round_data["ground_truth"])

        response = {
            "participant_name": st.session_state.participant_name,
            "participant_id": st.session_state.participant_id,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "round": round_num + 1,
            "stimulus_id": round_data["id"],
            "stimulus_type": round_data["type"],
            "stimulus_notes": round_data["notes"],
            "ground_truth": round_data["ground_truth"],
            "answer": answer,
            "correct": correct,
            "confidence": confidence,
            "response_time_seconds": response_time
        }

        st.session_state.responses.append(response)
        st.session_state.current_round += 1
        st.session_state.round_start_time = time.time()
        st.rerun()


def render_post_quiz():
    """Show two extra questions as a separate page."""

    # Save the 9 quiz responses before asking the final questions.
    # This way the main study data is not lost if someone closes the page here.
    if not st.session_state.saved:
        save_results()
        st.session_state.saved = True

    scroll_to_top_once("post_quiz")

    st.html(f"""
        <div style="text-align:center; color:{PURPLE}; font-weight:800; font-size:1.5rem; margin-bottom:0.5rem;">
            Two quick questions
        </div>
        <div style="text-align:center; opacity:0.7; margin-bottom:1.5rem;">
            Answer these before you see your results.
        </div>
    """)

    scale_options = [
        "Strongly disagree",
        "Disagree",
        "In between",
        "Agree",
        "Strongly agree"
    ]

    scale_to_number = {
        "Strongly disagree": 1,
        "Disagree": 2,
        "In between": 3,
        "Agree": 4,
        "Strongly agree": 5
    }

    with st.container(border=True):
        q1 = st.radio(
            "After this quiz, I feel more skeptical about content I see online.",
            options=scale_options,
            index=None,
            horizontal=True,
            key="post_q1"
        )

        st.write("")

        q2 = st.radio(
            "Frequent exposure to AI-generated content makes it harder to trust real content.",
            options=scale_options,
            index=None,
            horizontal=True,
            key="post_q2"
        )

        if st.button(
            "See my results",
            type="primary",
            use_container_width=True
        ):
            if q1 is None or q2 is None:
                st.warning("Please answer both questions before continuing.")
                return

            st.session_state.post_quiz_responses = {
                "skepticism": scale_to_number[q1],
                "skepticism_label": q1,
                "trust_harder": scale_to_number[q2],
                "trust_harder_label": q2
            }

            save_post_quiz()
            st.session_state.post_quiz_answered = True
            st.rerun()

def render_leaderboard():
    """Display leaderboard safely for CSV and Supabase data."""

    df = get_all_responses()

    if df.empty:
        st.info("No data yet.")
        return

    # Make sure round is numeric
    df["round"] = pd.to_numeric(
        df["round"],
        errors="coerce"
    )

    # Only actual quiz rounds
    df_rounds = df[
        (df["round"] >= 1) &
        (df["round"] <= len(ROUNDS))
    ].copy()

    if df_rounds.empty:
        st.info("No quiz data found yet.")
        return

    # ----------------------------------------------
    # NORMALIZE CORRECT COLUMN
    # Handles:
    # True / False
    # "True" / "False"
    # "true" / "false"
    # 1 / 0
    # Arrow string dtype
    # ----------------------------------------------

    def correct_to_int(value):

        if pd.isna(value):
            return 0

        if isinstance(value, bool):
            return int(value)

        text = str(value).strip().lower()

        if text in ["true", "1", "yes"]:
            return 1

        return 0

    df_rounds["correct_num"] = (
        df_rounds["correct"]
        .apply(correct_to_int)
        .astype(int)
    )

    # ----------------------------------------------
    # GROUP PARTICIPANTS
    # ----------------------------------------------

    grouped = (
        df_rounds
        .groupby("participant_id")
        .agg(
            participant_name=(
                "participant_name",
                "first"
            ),

            # nunique is safer than count
            total_rounds=(
                "round",
                "nunique"
            ),

            correct=(
                "correct_num",
                "sum"
            )
        )
        .reset_index()
    )

    # Only people who completed all 9 rounds
    grouped = grouped[
        grouped["total_rounds"] == len(ROUNDS)
    ].copy()

    if grouped.empty:
        st.info("No complete quiz records yet.")
        return

    # Explicit numeric conversion
    grouped["correct"] = pd.to_numeric(
        grouped["correct"],
        errors="coerce"
    ).fillna(0).astype(int)

    grouped["accuracy"] = (
        grouped["correct"]
        / len(ROUNDS)
        * 100
    ).round(1)

    # Highest score first
    grouped = grouped.sort_values(
        ["correct", "participant_name"],
        ascending=[False, True]
    ).reset_index(drop=True)

    # Same score = same rank
    grouped["rank"] = (
        grouped["correct"]
        .rank(
            method="dense",
            ascending=False
        )
        .astype(int)
    )

    # ----------------------------------------------
    # DISPLAY
    # ----------------------------------------------

    st.html(
        """
        <div style="
            margin-top:2.5rem;
            text-align:center;
        ">
            <span style="
                font-size:1.5rem;
                font-weight:800;
                color:#6C2E8B;
            ">
                🏆 Leaderboard
            </span>

            <div style="
                font-size:0.85rem;
                opacity:0.6;
                margin-top:0.3rem;
            ">
                Just for fun - not used in the research analysis.
            </div>
        </div>
        """
    )

    table_html = """
    <table class="leaderboard-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Name</th>
                <th>Correct</th>
                <th>Accuracy</th>
            </tr>
        </thead>
        <tbody>
    """

    for _, row in grouped.iterrows():

        rank = int(row["rank"])
        name = str(row["participant_name"])
        correct = int(row["correct"])
        acc = float(row["accuracy"])

        # Medal for top 3
        if rank == 1:
            rank_display = "🥇 #1"
        elif rank == 2:
            rank_display = "🥈 #2"
        elif rank == 3:
            rank_display = "🥉 #3"
        else:
            rank_display = f"#{rank}"

        table_html += f"""
        <tr>
            <td class="leaderboard-rank">
                {rank_display}
            </td>
            <td>
                {name}
            </td>
            <td>
                {correct}/{len(ROUNDS)}
            </td>
            <td>
                {acc:.1f}%
            </td>
        </tr>
        """

    table_html += """
        </tbody>
    </table>
    """

    st.html(table_html)


def render_results():
    scroll_to_top_once("results")

    if not st.session_state.saved:
        save_results()
        st.session_state.saved = True

    responses = st.session_state.responses
    total = len(responses)
    correct_count = sum(1 for r in responses if r["correct"])
    avg_confidence = round(sum(r["confidence"] for r in responses) / total, 1) if total else 0

    st.html(f"""
        <div style="text-align:center; color:{PURPLE}; font-weight:800; font-size:1.5rem; margin-bottom:0.5rem;">
            Quiz complete
        </div>
        <div class="final-score">
            <div class="score-caption">{st.session_state.participant_name}, your score is</div>
            <div class="score-number">{correct_count}/{total}</div>
            <div class="score-caption">
                You correctly identified <strong>{round((correct_count/total)*100)}%</strong> of the media.
            </div>
        </div>
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.html(f"""
            <div class="metric-card">
                <div class="metric-value">{correct_count}/{total}</div>
                <div class="metric-label">Correct</div>
            </div>
        """)
    with col2:
        st.html(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_confidence}/5</div>
                <div class="metric-label">Avg. Confidence</div>
            </div>
        """)
    with col3:
        # Only single-video rounds have ground_truth "Real" or "AI-generated"
        single_responses = [r for r in responses if r["ground_truth"] in ("Real", "AI-generated")]
        real_correct = sum(1 for r in single_responses if r["ground_truth"] == "Real" and r["correct"])
        real_total = sum(1 for r in single_responses if r["ground_truth"] == "Real")
        ai_correct = sum(1 for r in single_responses if r["ground_truth"] == "AI-generated" and r["correct"])
        ai_total = sum(1 for r in single_responses if r["ground_truth"] == "AI-generated")
        real_pct = round((real_correct/real_total)*100) if real_total else 0
        ai_pct = round((ai_correct/ai_total)*100) if ai_total else 0
        st.html(f"""
            <div class="metric-card">
                <div class="metric-value">R:{real_pct}% / A:{ai_pct}%</div>
                <div class="metric-label">Single-video accuracy - Real / AI</div>
            </div>
        """)

    _, center, _ = st.columns([0.45, 2.2, 0.45])
    with center:
        st.image("media/ai_demos.png", use_container_width=True)

    st.html("""
        <div style="text-align:center; font-size:1.05rem; opacity:0.7; margin: 1rem 0 2rem 0;">
            Thanks for taking part.
        </div>
    """)

    st.html("""
        <div class="review-title">Review your answers</div>
        <div class="review-subtitle">
            Open a round to see the media again and compare your answer with the correct one.
        </div>
    """)

    for response in responses:
        round_idx = response["round"] - 1
        round_data = ROUNDS[round_idx]
        icon = "✅" if response["correct"] else "❌"
        result_text = "Correct" if response["correct"] else "Incorrect"
        expander_title = f"{icon} Round {response['round']} - {result_text}"

        with st.expander(expander_title):
            if round_data["type"] == "single_video":
                _, col, _ = st.columns([1.2, 1.4, 1.2])
                with col:
                    if media_file_exists(round_data["file"]):
                        st.video(round_data["file"])
                    else:
                        st.warning("Media file not found.")
            elif round_data["type"] == "pair_video":
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800;'>LEFT</div>")
                    if media_file_exists(round_data["left"]):
                        st.video(round_data["left"])
                    else:
                        st.warning("File missing")
                with c2:
                    st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800;'>RIGHT</div>")
                    if media_file_exists(round_data["right"]):
                        st.video(round_data["right"])
                    else:
                        st.warning("File missing")
            elif round_data["type"] == "pair_image":
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800;'>LEFT</div>")
                    if media_file_exists(round_data["left"]):
                        st.image(round_data["left"], use_container_width=True)
                    else:
                        st.warning("File missing")
                with c2:
                    st.html(f"<div style='text-align:center; color:{PURPLE}; font-weight:800;'>RIGHT</div>")
                    if media_file_exists(round_data["right"]):
                        st.image(round_data["right"], use_container_width=True)
                    else:
                        st.warning("File missing")

            st.write("")
            if response["correct"]:
                st.html(f"""
                    <div class="correct-box">
                        <strong>✅ Correct</strong><br><br>
                        Your answer: <strong>{response["answer"]}</strong><br>
                        Correct answer: <strong>{response["ground_truth"]}</strong><br>
                        Confidence: <strong>{response["confidence"]}/5</strong>
                    </div>
                """)
            else:
                st.html(f"""
                    <div class="incorrect-box">
                        <strong>❌ Incorrect</strong><br><br>
                        Your answer: <strong>{response["answer"]}</strong><br>
                        Correct answer: <strong>{response["ground_truth"]}</strong><br>
                        Confidence: <strong>{response["confidence"]}/5</strong>
                    </div>
                """)
            if round_data["notes"] == "edited_non_ai":
                st.info("ℹ️ This video is edited/manipulated using traditional visual effects, but it is **not** AI-generated.")

    render_leaderboard()

    st.write("")
    _, restart_col, _ = st.columns([1.4, 1, 1.4])
    with restart_col:
        if st.button("Restart Quiz", use_container_width=True):
            restart_quiz()


# ==================================================
# MAIN APP
# ==================================================

def main():
    inject_custom_css()
    init_session_state()

    if not st.session_state.started:
        render_start_screen()
    elif st.session_state.current_round < len(ROUNDS):
        render_round()
    elif not st.session_state.post_quiz_answered:
        render_post_quiz()
    else:
        render_results()


if __name__ == "__main__":
    main()
