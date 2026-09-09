import streamlit as st
import pandas as pd
import os
import time
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Page config
st.set_page_config(
    page_title="Real or AI?",
    page_icon="media/page_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants & colours
RESULT_FILE = "data/responses_final.csv"
MEDIA_BASE = Path("media")

PURPLE = "#6C2E8B"
LIGHT_PURPLE = "#F3EDF7"
SOFT_PURPLE = "#DCC8E8"
GREEN = "#248A57"
RED = "#B33A3A"

# Supabase connection (if secrets are available)
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
    st.warning("Supabase package not installed. pip install supabase-py")

# Custom CSS
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


# Media list (9 rounds)
ROUNDS: List[Dict[str, Any]] = [
    {
        "id": "video1",
        "type": "single_video",
        "file": "media/single/video1.mp4",
        "ground_truth": "No",
        "notes": "authentic"
    },
    {
        "id": "video2",
        "type": "single_video",
        "file": "media/single/video2.mp4",
        "ground_truth": "Yes (AI-generated)",
        "notes": "ai_generated"
    },
    {
        "id": "video3",
        "type": "single_video",
        "file": "media/single/video3.mp4",
        "ground_truth": "No",
        "notes": "authentic"
    },
    {
        "id": "video4",
        "type": "single_video",
        "file": "media/single/video4.mp4",
        "ground_truth": "No",
        "notes": "authentic"
    },
    {
        "id": "video5",
        "type": "single_video",
        "file": "media/single/video5.mp4",
        "ground_truth": "Yes (AI-generated)",
        "notes": "ai_generated"
    },
    {
        "id": "video6",
        "type": "single_video",
        "file": "media/single/video6.mp4",
        "ground_truth": "No",
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

# Session state initialisation
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
        "should_scroll_to_top": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Helper functions
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
    if supabase is None:
        return
    try:
        row_copy = row.copy()
        if isinstance(row_copy["correct"], bool):
            row_copy["correct"] = str(row_copy["correct"])
        supabase.table("responses").insert(row_copy).execute()
    except Exception as e:
        st.warning(f"Supabase insert error: {e}")

def save_results():
    os.makedirs("data", exist_ok=True)
    columns = [
        "participant_name", "participant_id", "timestamp",
        "round", "stimulus_id", "stimulus_type", "stimulus_notes",
        "ground_truth", "answer", "correct", "confidence",
        "response_time_seconds"
    ]
    df = pd.DataFrame(st.session_state.responses, columns=columns)
    if os.path.exists(RESULT_FILE):
        df.to_csv(RESULT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(RESULT_FILE, index=False)
    for _, row in df.iterrows():
        insert_response_to_supabase(row.to_dict())

def save_post_quiz():
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
    df = pd.DataFrame([row])
    if os.path.exists(RESULT_FILE):
        df.to_csv(RESULT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(RESULT_FILE, index=False)
    insert_response_to_supabase(row)

def get_all_responses() -> pd.DataFrame:
    if supabase is not None:
        try:
            res = supabase.table("responses").select("*").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            st.warning(f"Supabase fetch error: {e}")
    if os.path.exists(RESULT_FILE):
        return pd.read_csv(RESULT_FILE)
    return pd.DataFrame()

def get_detector_results():
    json_path = Path("media/detector_results.json")
    if not json_path.exists():
        alt_path = Path("media/mediadetector_results.json")
        if alt_path.exists():
            json_path = alt_path
        else:
            return {}
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except:
        return {}

def restart_quiz():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def request_scroll_to_top():
    st.session_state["should_scroll_to_top"] = True

def handle_scroll_to_top():
    if not st.session_state.get("should_scroll_to_top", False):
        return
    st.session_state["should_scroll_to_top"] = False
    st.components.v1.html(
        """
        <script>
            window.parent.scrollTo({
                top: 0,
                left: 0,
                behavior: "instant"
            });
        </script>
        """,
        height=0,
    )


# Page components
def render_hero():
    st.html(
        """
        <div class="hero">
            <div class="hero-badge">AI DeMoS Lab - TU Delft</div>
            <div class="hero-title">Real or AI?</div>
            <div class="purple-line"></div>
            <div class="hero-subtitle">
                A short study about how accurately people can judge whether media is AI‑generated,
                and why it matters in the era of everyday synthetic content.
            </div>
        </div>
        """
    )

def render_start_screen():
    handle_scroll_to_top()
    render_hero()

    # Updated Purpose and motivation
    with st.container(border=True):
        st.markdown(
            """
### Purpose

To investigate how people judge AI-generated, authentic, and traditionally edited media, while also raising awareness that AI-generated content is becoming part of everyday social media environments and may not always be easy to recognize.

**A short background:**  
Early discussions around synthetic media often focused on political deepfakes and deliberate deception. More recently, AI-generated images and videos have become part of everyday social media feeds, where they appear alongside authentic and conventionally edited content.

Following a discussion with **Jordi Viader Guerrero** at the DeMoS Lab, I shifted the focus of the project toward this everyday media environment. The study was designed to explore how people judge the authenticity of mixed online media and how confident they are in those judgments.

The data from this study will help explore where people struggle to distinguish synthetic from authentic media, how confidence relates to these judgments, and how participants reflect on trust in the content they encounter online.
            """
        )

    st.write("")

    # Image (TU Delft logo etc.)
    col_left, col_center, col_right = st.columns([0.55, 2.2, 0.55])
    with col_center:
        st.image("media/demos_lab.png", use_container_width=True)

    st.write("")

    # How it works
    with st.container(border=True):
        st.html(f"""
            <div style="color:{PURPLE}; font-weight:800; font-size:1.4rem; margin-bottom:0.7rem;">
                How it works
            </div>
        """)
        st.markdown(
            """
You will see **9 pieces of media** (videos and images).

For each one, decide whether you think the content is AI‑generated and tell us how confident you are.

Some rounds show two items side by side – go with your first impression.

**Estimated time:** 4‑6 minutes.
            """
        )

        # Machine baseline note
        st.markdown(
            """
**Also:** I tested these media with UniversalFakeDetect as a machine baseline.  
You can compare your answers with the detector at the end.
            """
        )

        # Data use & consent
        st.markdown(
            """
---
**Data use & privacy**

Your answers, confidence ratings, response times and final feedback will be recorded for this research project.  
You can use a nickname. Your nickname and score may appear on the leaderboard.  
By starting, you agree to these responses being used for the analysis.
            """
        )

        # Start form
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
                    request_scroll_to_top()
                    st.rerun()


# Render functions for single video, video pair, image pair
def render_single_video(round_data: Dict[str, Any]):
    with st.container(border=True):
        missing = validate_round_media(round_data)
        if missing:
            st.warning(f"⚠️ Media file not found: {missing[0]}. Please check your assets.")
            return None
        _, center, _ = st.columns([1, 1.65, 1])
        with center:
            st.video(round_data["file"])
        st.html("""
            <div class="question-heading">Is this video AI‑generated?</div>
            <div class="question-subheading">Go with your first impression.</div>
        """)
        return st.radio(
            "Answer",
            ["Yes (AI-generated)", "No", "Not sure"],
            index=None,
            horizontal=True,
            label_visibility="collapsed",
            key=f"answer_{st.session_state.current_round}"
        )

def render_pair_video(round_data: Dict[str, Any]):
    missing = validate_round_media(round_data)
    if missing:
        st.warning(f"⚠️ Media file(s) missing: {', '.join(missing)}")
        return None
    st.html(f"""
        <div style="text-align:center; color:{PURPLE}; font-size:1.4rem; font-weight:800;">
            Which video is AI‑generated?
        </div>
        <div style="text-align:center; opacity:0.65; margin-bottom:1rem;">
            One of these videos is AI‑generated.
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
            "Which video is AI‑generated?",
            ["Left", "Right", "Not sure"],
            index=None,
            horizontal=True,
            key=f"answer_{st.session_state.current_round}"
        )

def render_pair_image(round_data: Dict[str, Any]):
    missing = validate_round_media(round_data)
    if missing:
        st.warning(f"⚠️ Image file(s) missing: {', '.join(missing)}")
        return None
    st.html(f"""
        <div style="text-align:center; color:{PURPLE}; font-size:1.4rem; font-weight:800;">
            TU Delft image comparison
        </div>
        <div style="text-align:center; opacity:0.65; margin-bottom:1rem;">
            One image is authentic. The other is AI‑generated.
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
            "Which image is AI‑generated?",
            ["Left", "Right", "Not sure"],
            index=None,
            horizontal=True,
            key=f"answer_{st.session_state.current_round}"
        )


# Round screen (question + confidence scale + submit inside a form)
def render_round():
    round_num = st.session_state.current_round
    round_data = ROUNDS[round_num]

    st.html(f'<div class="round-label">ROUND {round_num + 1} OF {len(ROUNDS)}</div>')
    st.progress((round_num + 1) / len(ROUNDS))
    st.write("")

    with st.form(key=f"quiz_form_{round_num}"):
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
            submitted = st.form_submit_button(
                "Submit",
                type="primary",
                use_container_width=True
            )

    if submitted:
        if answer is None:
            st.warning("Please choose an answer before continuing.")
            st.rerun()
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


# Post‑quiz questions
def render_post_quiz():
    if not st.session_state.saved:
        save_results()
        st.session_state.saved = True

    handle_scroll_to_top()

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
            "Frequent exposure to AI‑generated content makes it harder to trust real content.",
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
            request_scroll_to_top()
            st.rerun()


# Leaderboard
def render_leaderboard():
    df = get_all_responses()
    if df.empty:
        st.info("No data yet.")
        return

    df["round"] = pd.to_numeric(df["round"], errors="coerce")
    df_rounds = df[(df["round"] >= 1) & (df["round"] <= len(ROUNDS))].copy()
    if df_rounds.empty:
        st.info("No quiz data found yet.")
        return

    def correct_to_int(value):
        if pd.isna(value):
            return 0
        if isinstance(value, bool):
            return int(value)
        text = str(value).strip().lower()
        if text in ["true", "1", "yes"]:
            return 1
        return 0

    df_rounds["correct_num"] = df_rounds["correct"].apply(correct_to_int).astype(int)

    grouped = df_rounds.groupby("participant_id").agg(
        participant_name=("participant_name", "first"),
        total_rounds=("round", "nunique"),
        correct=("correct_num", "sum")
    ).reset_index()

    grouped = grouped[grouped["total_rounds"] == len(ROUNDS)].copy()
    if grouped.empty:
        st.info("No complete quiz records yet.")
        return

    grouped["correct"] = pd.to_numeric(grouped["correct"], errors="coerce").fillna(0).astype(int)
    grouped["accuracy"] = (grouped["correct"] / len(ROUNDS) * 100).round(1)
    grouped = grouped.sort_values(["correct", "participant_name"], ascending=[False, True]).reset_index(drop=True)
    grouped["rank"] = grouped["correct"].rank(method="dense", ascending=False).astype(int)

    st.html(
        """
        <div style="margin-top:2.5rem; text-align:center;">
            <span style="font-size:1.5rem; font-weight:800; color:#6C2E8B;">🏆 Leaderboard</span>
            <div style="font-size:0.85rem; opacity:0.6; margin-top:0.3rem;">
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
            <td class="leaderboard-rank">{rank_display}</td>
            <td>{name}</td>
            <td>{correct}/{len(ROUNDS)}</td>
            <td>{acc:.1f}%</td>
        </tr>
        """
    table_html += "</tbody></table>"
    st.html(table_html)

    # Total participant count
    total_participants = grouped.shape[0]
    st.caption(f"📊 **{total_participants}** people have completed the quiz so far.")


# Results page – now includes "What you may have noticed" section
def render_results():
    handle_scroll_to_top()

    if not st.session_state.saved:
        save_results()
        st.session_state.saved = True

    detector_data = get_detector_results()
    if not detector_data:
        st.warning(
            "⚠️ Detector results not found. "
            "Please add `media/detector_results.json` to see AI detector comparisons."
        )

    responses = st.session_state.responses
    total = len(responses)
    correct_count = sum(1 for r in responses if r["correct"])
    avg_confidence = round(sum(r["confidence"] for r in responses) / total, 1) if total else 0

    # Score display
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

    # Metric cards
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
        single_responses = [
            r for r in responses
            if r["ground_truth"] in ("Yes (AI-generated)", "No")
        ]
        non_ai_correct = sum(
            1 for r in single_responses
            if r["ground_truth"] == "No" and r["correct"]
        )
        non_ai_total = sum(
            1 for r in single_responses
            if r["ground_truth"] == "No"
        )
        ai_correct = sum(
            1 for r in single_responses
            if r["ground_truth"] == "Yes (AI-generated)" and r["correct"]
        )
        ai_total = sum(
            1 for r in single_responses
            if r["ground_truth"] == "Yes (AI-generated)"
        )
        non_ai_pct = round((non_ai_correct/non_ai_total)*100) if non_ai_total else 0
        ai_pct = round((ai_correct/ai_total)*100) if ai_total else 0
        st.html(f"""
            <div class="metric-card">
                <div class="metric-value">Not AI: {non_ai_pct}% / AI: {ai_pct}%</div>
                <div class="metric-label">Single‑video accuracy</div>
            </div>
        """)

    # Machine baseline
    st.html(f"""
        <div style="
            text-align:center;
            font-size:0.95rem;
            opacity:0.7;
            margin: 1.5rem 0 1rem 0;
            padding: 0.8rem;
            background: {LIGHT_PURPLE};
            border-radius: 12px;
            border: 1px solid {SOFT_PURPLE};
        ">
            <strong>Machine baseline:</strong> 
            I also tested UniversalFakeDetect on the same media. 
            It achieved <strong>6/9 (66.7%)</strong> overall accuracy.
        </div>
    """)

    # Thanks
    st.html("""
        <div style="text-align:center; font-size:1.05rem; opacity:0.7; margin: 1rem 0 2rem 0;">
            Thanks for taking part.
        </div>
    """)

    # ----- What you may have noticed (Updated) -----
    st.html("""
        <div class="review-title" style="margin-top:1rem;">What you may have noticed</div>
    """)

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.image("media/Video2.png", use_container_width=True)
        st.markdown(
            """
            **Video 2** - look closely at the face.  
            There are small distortions around the eyes and mouth, a common sign of generative models struggling with fine details.
            """
        )
    with col_b:
        st.image("media/Video5.png", use_container_width=True)
        st.markdown(
            """
            **Video 5** - check the emblem on the shoulder.  
            The logo is unnaturally warped, which often happens when an AI tries to generate text or structured symbols.
            """
        )

    # Third image for Delft comparison
    st.image("media/delft.png", use_container_width=True)
    st.markdown(
        """
        **Delft comparison** - look at the person in the yellow suit.  
        The AI-generated version often produces strange artifacts or unnatural details in complex clothing or body proportions.
        """
    )

    st.markdown(
        """
        If you'd like to learn more, I recommend this short article:

        > [**"AI slop" – how fake photos and videos are shaping our feeds**](https://techxplore.com/news/2025-05-ai-slop-fake-photos-videos.html)

        It explains the broader context behind this study and why synthetic content is becoming part of our everyday digital lives.
        """
    )

    # Answer review
    st.html("""
        <div class="review-title">Review your answers</div>
        <div class="review-subtitle">
            Open a round to see the media again and compare your answer with the correct one.
            You can also see what the AI detector predicted for each piece of media.
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
                st.info("ℹ️ This video is edited/manipulated using traditional visual effects, but it is **not** AI‑generated.")

            # AI Detector prediction
            det_key = round_data["id"]
            if detector_data and det_key in detector_data:
                det = detector_data[det_key]
                det_icon = "✅" if det.get("correct", False) else "❌"
                if "score" in det:
                    st.caption(
                        f"**AI Detector predicted:** {det['prediction']} "
                        f"(score: {det['score']:.5f}) {det_icon}"
                    )
                else:
                    st.caption(
                        f"**AI Detector predicted:** {det['prediction']} "
                        f"(Left: {det['left_score']:.5f}, Right: {det['right_score']:.5f}) {det_icon}"
                    )

    # Leaderboard
    render_leaderboard()

    # Restart
    st.write("")
    _, restart_col, _ = st.columns([1.4, 1, 1.4])
    with restart_col:
        if st.button("Restart Quiz", use_container_width=True):
            restart_quiz()


# Main flow
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
