import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Real or AI?",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==================================================
# SETTINGS
# ==================================================

RESULT_FILE = "data/responses_final.csv"
SHOW_RESEARCHER_RESULTS = False

PURPLE = "#5F247E"
LIGHT_PURPLE = "#F4EEF8"
SOFT_PURPLE = "#E9DDF0"


# ==================================================
# CSS
# ==================================================

st.html(
    f"""
    <style>

    .block-container {{
        max-width: 1120px;
        padding-top: 1.4rem;
        padding-bottom: 4rem;
    }}

    .hero {{
        text-align: center;
        padding: 0.2rem 0 1.2rem 0;
    }}

    .hero-badge {{
        display: inline-block;
        color: {PURPLE};
        background: {LIGHT_PURPLE};
        border: 1px solid {SOFT_PURPLE};
        padding: 0.38rem 0.8rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
    }}

    .hero-title {{
        font-size: clamp(2.6rem, 6vw, 4.2rem);
        font-weight: 850;
        line-height: 1;
        margin: 0;
    }}

    .hero-subtitle {{
        max-width: 700px;
        margin: 1rem auto 0 auto;
        opacity: 0.72;
        font-size: 1.05rem;
        line-height: 1.55;
    }}

    .purple-line {{
        height: 4px;
        width: 58px;
        border-radius: 100px;
        background: {PURPLE};
        margin: 0.8rem auto 1.3rem auto;
    }}

    .round-label {{
        width: fit-content;
        margin: auto;
        margin-bottom: 0.75rem;
        color: {PURPLE};
        background: {LIGHT_PURPLE};
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.05em;
    }}

    .question-heading {{
        font-size: 1.22rem;
        font-weight: 780;
        margin-bottom: 0.25rem;
    }}

    .question-subheading {{
        opacity: 0.65;
        font-size: 0.92rem;
        margin-bottom: 0.8rem;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 18px;
        border-color: {SOFT_PURPLE};
    }}

    .stButton > button,
    .stFormSubmitButton > button {{
        border-radius: 12px;
        min-height: 48px;
        font-weight: 750;
        font-size: 1rem;
    }}

    button[kind="primary"] {{
        background-color: {PURPLE} !important;
        border-color: {PURPLE} !important;
        color: white !important;
    }}

    div[data-testid="stTextInput"] input {{
        border-radius: 12px;
        min-height: 48px;
        font-size: 1rem;
    }}

    div[data-testid="stRadio"] label p {{
        font-weight: 650;
        font-size: 1rem;
    }}

    div[data-testid="stProgress"] > div > div > div > div {{
        background-color: {PURPLE};
    }}

    .final-score {{
        text-align: center;
        padding: 1rem 0 1.5rem 0;
    }}

    .score-number {{
        font-size: 4rem;
        font-weight: 900;
        color: {PURPLE};
        line-height: 1;
        margin: 0.5rem 0;
    }}

    .score-caption {{
        font-size: 1.05rem;
        opacity: 0.7;
    }}

    </style>
    """
)


# ==================================================
# QUIZ ROUNDS
# ==================================================

rounds = [

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
# SESSION STATE
# ==================================================

if "started" not in st.session_state:
    st.session_state.started = False

if "participant_name" not in st.session_state:
    st.session_state.participant_name = ""

if "participant_id" not in st.session_state:
    st.session_state.participant_id = None

if "current_round" not in st.session_state:
    st.session_state.current_round = 0

if "responses" not in st.session_state:
    st.session_state.responses = []

if "round_start_time" not in st.session_state:
    st.session_state.round_start_time = None

if "saved" not in st.session_state:
    st.session_state.saved = False


# ==================================================
# FUNCTIONS
# ==================================================

def save_results():

    os.makedirs("data", exist_ok=True)

    columns = [
        "participant_name",
        "participant_id",
        "timestamp",
        "round",
        "stimulus_id",
        "stimulus_type",
        "stimulus_notes",
        "ground_truth",
        "answer",
        "correct",
        "confidence",
        "response_time_seconds"
    ]

    df = pd.DataFrame(
        st.session_state.responses,
        columns=columns
    )

    if os.path.exists(RESULT_FILE):

        df.to_csv(
            RESULT_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        df.to_csv(
            RESULT_FILE,
            index=False
        )


def restart_quiz():
    st.session_state.clear()
    st.rerun()


# ==================================================
# HERO
# ==================================================

st.html(
    """
    <div class="hero">
        <div class="hero-badge">
            AI DeMoS Lab • TU Delft
        </div>

        <div class="hero-title">
            🤖 Real or AI?
        </div>

        <div class="purple-line"></div>

        <div class="hero-subtitle">
            Can you tell the difference between authentic,
            traditionally edited and AI-generated media?
        </div>
    </div>
    """
)


# ==================================================
# START SCREEN
# ==================================================

if not st.session_state.started:

    image_left, image_center, image_right = st.columns(
        [0.55, 2, 0.55]
    )

    with image_center:

        st.image(
            "media/demos_lab.png",
            use_container_width=True
        )


    st.write("")


    left_space, center, right_space = st.columns(
        [0.9, 2, 0.9]
    )


    with center:

        with st.container(border=True):

            st.html(
                f"""
                <div style="
                    color:{PURPLE};
                    font-weight:800;
                    font-size:1.3rem;
                    margin-bottom:0.7rem;
                ">
                    Ready to play?
                </div>
                """
            )

            st.markdown(
                """
You will see **9 pieces of media**.

Your task is simple:

**Decide whether the content is real or AI-generated.**

For some rounds, you will compare two pieces of media.

After each answer, tell us how confident you are.

**Estimated time: 4–6 minutes.**
                """
            )


            with st.form("start_form"):

                participant_name = st.text_input(
                    "Enter your name or nickname",
                    placeholder="e.g. Umut"
                )

                start_button = st.form_submit_button(
                    "Start Quiz →",
                    type="primary",
                    use_container_width=True
                )

                if start_button:

                    cleaned_name = " ".join(
                        participant_name.split()
                    )

                    if not cleaned_name:

                        st.warning(
                            "Please enter your name or nickname."
                        )

                    else:

                        st.session_state.participant_name = cleaned_name

                        st.session_state.participant_id = (
                            str(uuid.uuid4())[:8]
                        )

                        st.session_state.current_round = 0
                        st.session_state.responses = []
                        st.session_state.saved = False
                        st.session_state.round_start_time = time.time()
                        st.session_state.started = True

                        st.rerun()

    st.stop()


# ==================================================
# FINISHED
# ==================================================

if st.session_state.current_round >= len(rounds):

    if not st.session_state.saved:

        save_results()
        st.session_state.saved = True


    correct_answers = sum(
        1
        for response in st.session_state.responses
        if response["correct"]
    )

    total_questions = len(rounds)

    score_percentage = round(
        (correct_answers / total_questions) * 100
    )


    st.html(
        f"""
        <div style="
            text-align:center;
            color:{PURPLE};
            font-weight:800;
            font-size:1.4rem;
            margin-bottom:0.5rem;
        ">
            Quiz complete 🎉
        </div>
        """
    )


    st.html(
        f"""
        <div class="final-score">

            <div class="score-caption">
                {st.session_state.participant_name}, your score is
            </div>

            <div class="score-number">
                {correct_answers}/{total_questions}
            </div>

            <div class="score-caption">
                You correctly identified
                <strong>{score_percentage}%</strong>
                of the media.
            </div>

        </div>
        """
    )


    final_left, final_center, final_right = st.columns(
        [0.45, 2.2, 0.45]
    )

    with final_center:

        st.image(
            "media/ai_demos.png",
            use_container_width=True
        )


    st.write("")


    st.html(
        """
        <div style="
            text-align:center;
            font-size:1.05rem;
            opacity:0.72;
        ">
            Thank you for participating in this synthetic media study.
        </div>
        """
    )


    if SHOW_RESEARCHER_RESULTS:

        with st.expander(
            "Researcher view — full responses"
        ):

            results_df = pd.DataFrame(
                st.session_state.responses
            )

            st.dataframe(
                results_df,
                use_container_width=True,
                hide_index=True
            )


    st.write("")


    _, restart_col, _ = st.columns(
        [1.4, 1, 1.4]
    )

    with restart_col:

        if st.button(
            "Restart Quiz",
            use_container_width=True
        ):

            restart_quiz()


    st.stop()


# ==================================================
# CURRENT ROUND
# ==================================================

round_number = st.session_state.current_round
current = rounds[round_number]


st.html(
    f"""
    <div class="round-label">
        ROUND {round_number + 1} OF {len(rounds)}
    </div>
    """
)


st.progress(
    (round_number + 1) / len(rounds)
)


st.write("")


# ==================================================
# SINGLE VIDEO
# ==================================================

if current["type"] == "single_video":

    # Biraz daha küçük video
    video_left, video_center, video_right = st.columns(
        [1, 1.65, 1]
    )

    with video_center:

        st.video(
            current["file"]
        )


    st.write("")


    with st.container(border=True):

        st.html(
            """
            <div class="question-heading">
                Is this video AI-generated?
            </div>

            <div class="question-subheading">
                Trust your first impression.
            </div>
            """
        )


        answer = st.radio(
            "Answer",
            [
                "Real",
                "AI-generated",
                "Not sure"
            ],
            index=None,
            horizontal=True,
            label_visibility="collapsed",
            key=f"answer_{round_number}"
        )


# ==================================================
# VIDEO PAIR
# ==================================================

elif current["type"] == "pair_video":

    st.html(
        f"""
        <div style="
            text-align:center;
            color:{PURPLE};
            font-size:1.35rem;
            font-weight:800;
        ">
            Which video is AI-generated?
        </div>

        <div style="
            text-align:center;
            opacity:0.65;
            margin-bottom:1rem;
        ">
            One of these videos is AI-generated.
        </div>
        """
    )


    # Biraz daha küçük pair videolar
    outer_left, left_col, right_col, outer_right = st.columns(
        [0.28, 1, 1, 0.28],
        gap="large"
    )


    with left_col:

        st.html(
            f"""
            <div style="
                text-align:center;
                color:{PURPLE};
                font-weight:800;
                margin-bottom:0.4rem;
            ">
                ← LEFT
            </div>
            """
        )

        st.video(
            current["left"]
        )


    with right_col:

        st.html(
            f"""
            <div style="
                text-align:center;
                color:{PURPLE};
                font-weight:800;
                margin-bottom:0.4rem;
            ">
                RIGHT →
            </div>
            """
        )

        st.video(
            current["right"]
        )


    st.write("")


    with st.container(border=True):

        answer = st.radio(
            "Which video is AI-generated?",
            [
                "Left",
                "Right",
                "Not sure"
            ],
            index=None,
            horizontal=True,
            key=f"answer_{round_number}"
        )


# ==================================================
# DELFT IMAGE PAIR
# ==================================================

elif current["type"] == "pair_image":

    st.html(
        f"""
        <div style="
            text-align:center;
            color:{PURPLE};
            font-size:1.35rem;
            font-weight:800;
        ">
            Final challenge: TU Delft
        </div>

        <div style="
            text-align:center;
            opacity:0.65;
            margin-bottom:1rem;
        ">
            One image is authentic.
            The other is AI-generated.
        </div>
        """
    )


    outer_left, left_col, right_col, outer_right = st.columns(
        [0.18, 1, 1, 0.18],
        gap="large"
    )


    with left_col:

        st.html(
            f"""
            <div style="
                text-align:center;
                color:{PURPLE};
                font-weight:800;
                margin-bottom:0.4rem;
            ">
                ← LEFT
            </div>
            """
        )

        st.image(
            current["left"],
            use_container_width=True
        )


    with right_col:

        st.html(
            f"""
            <div style="
                text-align:center;
                color:{PURPLE};
                font-weight:800;
                margin-bottom:0.4rem;
            ">
                RIGHT →
            </div>
            """
        )

        st.image(
            current["right"],
            use_container_width=True
        )


    st.write("")


    with st.container(border=True):

        answer = st.radio(
            "Which image is AI-generated?",
            [
                "Left",
                "Right",
                "Not sure"
            ],
            index=None,
            horizontal=True,
            key=f"answer_{round_number}"
        )


# ==================================================
# CONFIDENCE
# ==================================================

st.write("")


with st.container(border=True):

    st.html(
        """
        <div class="question-heading">
            How confident are you?
        </div>

        <div class="question-subheading">
            1 = pure guess
            &nbsp;&nbsp; • &nbsp;&nbsp;
            5 = very confident
        </div>
        """
    )


    slider_left, slider_center, slider_right = st.columns(
        [0.3, 3, 0.3]
    )

    with slider_center:

        confidence = st.slider(
            "Confidence",
            min_value=1,
            max_value=5,
            value=3,
            label_visibility="collapsed",
            key=f"confidence_{round_number}"
        )


# ==================================================
# NEXT BUTTON
# ==================================================

st.write("")


button_left, button_center, button_right = st.columns(
    [1.2, 1, 1.2]
)


with button_center:

    next_clicked = st.button(
        "Lock answer →",
        type="primary",
        use_container_width=True
    )


if next_clicked:

    if answer is None:

        st.warning(
            "Please choose an answer before continuing."
        )

    else:

        response_time = round(
            time.time()
            - st.session_state.round_start_time,
            2
        )


        correct = (
            answer == current["ground_truth"]
        )


        response = {

            "participant_name":
                st.session_state.participant_name,

            "participant_id":
                st.session_state.participant_id,

            "timestamp":
                datetime.now()
                .astimezone()
                .isoformat(
                    timespec="seconds"
                ),

            "round":
                round_number + 1,

            "stimulus_id":
                current["id"],

            "stimulus_type":
                current["type"],

            "stimulus_notes":
                current["notes"],

            "ground_truth":
                current["ground_truth"],

            "answer":
                answer,

            "correct":
                correct,

            "confidence":
                confidence,

            "response_time_seconds":
                response_time
        }


        st.session_state.responses.append(
            response
        )


        st.session_state.current_round += 1

        st.session_state.round_start_time = time.time()

        st.rerun()