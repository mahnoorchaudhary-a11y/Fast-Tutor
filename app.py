import streamlit as st
import re

st.set_page_config(
    page_title="OBE Alignment Checker",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
.main-title {
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 0;
}
.subtitle {
    color: #666;
    font-size: 17px;
    margin-bottom: 25px;
}
.card {
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #ddd;
    background-color: #fafafa;
    margin-bottom: 15px;
}
.score {
    font-size: 42px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title">🎯 OBE Alignment Checker</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">'
    'Check whether an assessment question is aligned with its CLO, PLO, '
    "Bloom's level, and marks."
    '</div>',
    unsafe_allow_html=True
)

BLOOM_VERBS = {
    "Remember": ["define", "list", "name", "identify", "recall", "state", "mention"],
    "Understand": ["explain", "summarize", "interpret", "classify", "discuss", "illustrate"],
    "Apply": ["apply", "calculate", "demonstrate", "use", "solve", "implement"],
    "Analyze": ["analyze", "analyse", "differentiate", "examine", "investigate", "compare", "contrast"],
    "Evaluate": ["evaluate", "assess", "justify", "critique", "judge", "defend", "argue", "recommend"],
    "Create": ["create", "design", "develop", "construct", "formulate", "propose", "produce", "generate"]
}

def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())

def get_words(text):
    return set(clean_text(text).split())

def detect_bloom(question):
    words = get_words(question)
    return {
        level: [verb for verb in verbs if verb in words]
        for level, verbs in BLOOM_VERBS.items()
        if any(verb in words for verb in verbs)
    }

def bloom_alignment(question, selected_bloom):
    detected = detect_bloom(question)

    if selected_bloom in detected:
        return 100, (
            f"The question contains a {selected_bloom.lower()}-level "
            f"action verb: {', '.join(detected[selected_bloom])}."
        )

    if detected:
        return 45, (
            f"The question appears to use verbs associated with "
            f"{', '.join(detected.keys())}, rather than clearly targeting "
            f"{selected_bloom}."
        )

    return 30, f"No clear {selected_bloom.lower()}-level action verb was detected."

def clo_alignment(question, clo):
    stopwords = {
        "the", "a", "an", "of", "to", "and", "in", "on", "for",
        "with", "students", "student", "will", "be", "able", "should", "can"
    }
    q = get_words(question) - stopwords
    c = get_words(clo) - stopwords

    if not c:
        return 50, "The CLO needs more information for alignment checking."

    overlap = q.intersection(c)
    ratio = len(overlap) / len(c)

    if ratio >= 0.5:
        return 100, "The assessment uses several concepts from the CLO."
    if ratio >= 0.25:
        return 70, "The assessment has partial conceptual overlap with the CLO."
    return 40, "The assessment may not directly measure the stated CLO."

def question_length_score(question, marks):
    words = len(question.split())

    if marks <= 2:
        return (
            (100, "Question length is appropriate for a short assessment.")
            if words <= 35 else
            (70, "Consider shortening the question.")
        )

    if marks <= 5:
        return (
            (100, "Question length is reasonable for the marks.")
            if 8 <= words <= 60 else
            (75, "Review the question length against the marks.")
        )

    return (
        (100, "Question provides sufficient scope for the allocated marks.")
        if words >= 15 else
        (70, "Consider providing more scope for a higher-mark question.")
    )

def rating(score):
    if score >= 85:
        return "🟢 Strong Alignment"
    if score >= 65:
        return "🟡 Moderate Alignment"
    return "🔴 Needs Improvement"

st.subheader("📝 Assessment Details")

col1, col2 = st.columns(2)

with col1:
    course = st.text_input(
        "📚 Course",
        placeholder="e.g., Introduction to Economics"
    )

    clo = st.text_area(
        "🎯 Course Learning Outcome (CLO)",
        placeholder="e.g., Analyze the causes and effects of inflation.",
        height=100
    )

    plo = st.text_input(
        "🔗 Program Learning Outcome (PLO)",
        placeholder="e.g., PLO 2 – Problem Analysis"
    )

with col2:
    bloom = st.selectbox("🧠 Target Bloom's Level", list(BLOOM_VERBS.keys()))

    marks = st.number_input(
        "📝 Marks",
        min_value=1,
        max_value=100,
        value=5
    )

    question_type = st.selectbox(
        "📋 Question Type",
        [
            "Short Answer", "MCQ", "Problem Solving", "Case Study",
            "Essay", "Scenario-Based", "Numerical", "Other"
        ]
    )

question = st.text_area(
    "🤖 Assessment Question",
    placeholder="Paste or type the assessment question here...",
    height=140
)

if st.button("🔍 CHECK OBE ALIGNMENT", type="primary", use_container_width=True):
    if not clo.strip() or not question.strip():
        st.error("Please enter both the CLO and assessment question.")
        st.stop()

    clo_score, clo_message = clo_alignment(question, clo)
    bloom_score, bloom_message = bloom_alignment(question, bloom)
    marks_score, marks_message = question_length_score(question, marks)
    plo_score = 100 if plo.strip() else 0

    overall = round((clo_score + bloom_score + marks_score + plo_score) / 4)

    st.divider()
    st.subheader("📊 OBE Alignment Report")

    result_col1, result_col2 = st.columns([1, 2])

    with result_col1:
        st.markdown(
            f'<div class="card" style="text-align:center;">'
            f'<div class="score">{overall}%</div>'
            f'<b>{rating(overall)}</b></div>',
            unsafe_allow_html=True
        )

    with result_col2:
        if overall >= 85:
            st.success("This assessment shows strong overall OBE alignment.")
        elif overall >= 65:
            st.warning("The assessment is partially aligned. Review the highlighted areas.")
        else:
            st.error("The assessment needs revision before approval.")

    st.subheader("🔎 Alignment Checks")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🎯 CLO Alignment")
        if clo_score >= 85:
            st.success(f"✅ {clo_score}% — {clo_message}")
        elif clo_score >= 65:
            st.warning(f"⚠️ {clo_score}% — {clo_message}")
        else:
            st.error(f"❌ {clo_score}% — {clo_message}")

        st.markdown("### 🔗 PLO Alignment")
        if plo.strip():
            st.success(f"✅ 100% — CLO is mapped to: **{plo}**")
        else:
            st.error("❌ No PLO selected. Please map the CLO to a PLO.")

    with c2:
        st.markdown("### 🧠 Bloom's Alignment")
        if bloom_score >= 85:
            st.success(f"✅ {bloom_score}% — {bloom_message}")
        elif bloom_score >= 65:
            st.warning(f"⚠️ {bloom_score}% — {bloom_message}")
        else:
            st.error(f"❌ {bloom_score}% — {bloom_message}")

        st.markdown("### ⚖️ Marks & Scope")
        if marks_score >= 85:
            st.success(f"✅ {marks_score}% — {marks_message}")
        else:
            st.warning(f"⚠️ {marks_score}% — {marks_message}")

    st.divider()
    st.subheader("💡 Recommended Improvements")

    suggestions = []

    if clo_score < 85:
        suggestions.append("🎯 Rewrite the question so that it directly measures the stated CLO.")

    if bloom_score < 85:
        suggestions.append(
            f"🧠 Use a clearer **{bloom}** action verb such as: "
            f"{', '.join(BLOOM_VERBS[bloom][:4])}."
        )

    if not plo.strip():
        suggestions.append("🔗 Select a PLO that the CLO contributes to.")

    if marks_score < 85:
        suggestions.append(
            "⚖️ Review whether the question provides enough scope for the allocated marks."
        )

    if not suggestions:
        st.success(
            "✨ No major alignment issues detected. "
            "The teacher should still make the final academic judgment."
        )
    else:
        for suggestion in suggestions:
            st.write(suggestion)

    st.divider()
    st.subheader("✏️ Tweak Your Assessment")
    st.write(
        "Change one element above and click CHECK again to see how the alignment changes."
    )

    t1, t2, t3 = st.columns(3)

    with t1:
        st.info("🧠 Change the Bloom's level above.")

    with t2:
        st.info("🎯 Change or refine the CLO above.")

    with t3:
        st.info("📝 Change the marks above.")

    st.divider()
    st.subheader("👩‍🏫 Faculty Decision")

    approve_col1, approve_col2 = st.columns(2)

    with approve_col1:
        if st.button("✅ APPROVE AS OBE ALIGNED", use_container_width=True):
            st.success("Assessment approved by faculty reviewer.")

    with approve_col2:
        if st.button("🔄 NEEDS REVISION", use_container_width=True):
            st.warning("Assessment marked for revision.")

st.divider()
st.caption(
    "🎓 OBE Assessment Checker | AI-assisted review with final validation by the faculty member."
)
