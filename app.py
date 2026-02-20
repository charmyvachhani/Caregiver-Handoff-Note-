import re
from datetime import datetime
import streamlit as st
import pandas as pd

# ----------------------------
# Safety + rule-based analyzer
# ----------------------------

DISCLAIMER = """
### Important safety note (demo-only)
This app provides **general caregiver-support suggestions** using **simple rule-based text matching** (keywords + regex).
It is **not medical advice**, **not a diagnostic tool**, and **does not recommend medication changes**.

- If you think someone may be in **immediate danger**, call your local emergency number (e.g., **911 in the U.S.**) right now.
- For urgent or worsening concerns, contact a licensed clinician or local urgent care.
"""

EMERGENCY_PATTERNS = [
    (r"\b(chest pain|pressure in chest|heart attack)\b", "Possible chest-pain emergency"),
    (r"\b(trouble breathing|can't breathe|cannot breathe|shortness of breath|turning blue)\b", "Breathing emergency"),
    (r"\b(stroke|face droop|slurred speech|arm weakness|FAST)\b", "Possible stroke signs"),
    (r"\b(unconscious|unresponsive|won't wake|not waking)\b", "Unresponsive person"),
    (r"\b(seizure|convulsion)\b", "Seizure/convulsion"),
    (r"\b(heavy bleeding|won't stop bleeding|bleeding a lot)\b", "Severe bleeding"),
    (r"\b(suicidal|kill myself|end my life|self harm)\b", "Self-harm risk"),
    (r"\b(overdose|took too many pills|poisoned)\b", "Possible overdose/poisoning"),
]

URGENT_PATTERNS = [
    (r"\b(fever\s*(over|above)\s*103|fever\s*103)\b", "High fever"),
    (r"\b(new confusion|sudden confusion|delirium|not making sense)\b", "Sudden confusion"),
    (r"\b(fall|fell|hit (their|her|his) head|head injury)\b", "Fall or head impact"),
    (r"\b(severe pain|worst pain)\b", "Severe pain"),
    (r"\b(dehydrated|no urine|not peeing|dry mouth)\b", "Possible dehydration"),
]

MEDICATION_MENTION = r"\b(med|meds|medicine|medication|pill|dose|dosage|prescription|refill)\b"

TOPIC_KEYWORDS = {
    "agitation_or_anxiety": [r"\b(agitated|agitation|anxious|panic|restless|irritable)\b"],
    "sleep": [r"\b(can't sleep|insomnia|sleeping all day|sleepy)\b"],
    "pain": [r"\b(pain|hurts|ache|aching)\b"],
    "memory_or_confusion": [r"\b(forgetful|memory|confused|confusion|dementia|delirium)\b"],
    "eating_drinking": [r"\b(not eating|not drinking|won't eat|won't drink|loss of appetite)\b"],
    "caregiver_stress": [r"\b(burnout|overwhelmed|exhausted|can't do this|no support)\b"],
    "safety": [r"\b(wandering|left the stove on|unsafe|falls risk|choking)\b"],
    "mood": [r"\b(depressed|hopeless|crying|sad)\b"],
}

GENERAL_STEPS = [
    "Make sure the person is **safe right now** (remove hazards, ensure supervision if needed).",
    "Gather **facts**: when it started, what changed, triggers, what helped/worsened it.",
    "If symptoms are **new, severe, or worsening**, contact a licensed clinician for guidance.",
    "If there’s any **immediate danger**, call your local emergency number.",
]

CARE_LOG_FIELDS = ["timestamp", "what_happened", "triggers_context", "what_helped", "notes"]


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def find_matches(patterns, text):
    hits = []
    for pat, label in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            hits.append(label)
    return hits


def detect_topics(text):
    topics = []
    for topic, pats in TOPIC_KEYWORDS.items():
        for pat in pats:
            if re.search(pat, text, flags=re.IGNORECASE):
                topics.append(topic)
                break
    return sorted(set(topics))


def build_response(user_text: str):
    t = normalize(user_text)

    emergency_hits = find_matches(EMERGENCY_PATTERNS, t)
    urgent_hits = find_matches(URGENT_PATTERNS, t)
    topics = detect_topics(t)
    mentions_meds = bool(re.search(MEDICATION_MENTION, t, flags=re.IGNORECASE))

    # Determine urgency (rule-based)
    if emergency_hits:
        urgency = "EMERGENCY — act now"
        urgency_color = "red"
    elif urgent_hits:
        urgency = "URGENT — contact a clinician soon"
        urgency_color = "orange"
    else:
        urgency = "NON-URGENT — supportive steps & monitoring"
        urgency_color = "green"

    # Topic-specific suggestions (non-diagnostic, supportive)
    suggestions = []

    if emergency_hits:
        suggestions.append("**Call your local emergency number now** (e.g., 911 in the U.S.).")
        suggestions.append("If it’s safe, stay with the person and keep them comfortable until help arrives.")
        suggestions.append("If you can, note **when symptoms started** and any key history to share with responders.")

    if urgent_hits and not emergency_hits:
        suggestions.append("Consider calling a licensed clinician/nurse line **today** for guidance, especially if symptoms are new or worsening.")
        suggestions.append("If there was a **fall/head impact**, monitor closely and seek professional guidance—especially for new symptoms.")

    # Medication guardrail
    if mentions_meds:
        suggestions.append("**Medication note:** This app cannot advise on medicines. **Do not start/stop/change doses** based on this tool. Contact a **pharmacist or prescriber** for medication questions or side effects.")

    # Add topic guidance
    if "agitation_or_anxiety" in topics:
        suggestions += [
            "**Agitation/anxiety support (general):**",
            "- Reduce stimulation (lower noise/light), offer calm reassurance, and keep your voice steady.",
            "- Check basic needs: hunger, thirst, toileting, temperature comfort.",
            "- Try a simple grounding activity: slow breathing together, familiar music, short walk if safe.",
        ]
    if "sleep" in topics:
        suggestions += [
            "**Sleep support (general):**",
            "- Keep a consistent routine (wake time, light exposure in the morning).",
            "- Limit caffeine late in the day and reduce screen/light at night.",
            "- If sudden major sleep changes occur, consider discussing with a clinician.",
        ]
    if "pain" in topics:
        suggestions += [
            "**Pain support (general):**",
            "- Ask where it hurts and what makes it better/worse; note severity and timing.",
            "- Use comfort measures (rest, positioning, gentle heat/cold if appropriate and safe).",
            "- New or severe pain warrants professional guidance.",
        ]
    if "memory_or_confusion" in topics:
        suggestions += [
            "**Confusion/memory changes (general):**",
            "- Use simple, reassuring cues; avoid arguing; offer one step at a time.",
            "- Note if confusion is **new/sudden**—that can be urgent and worth clinician input.",
        ]
    if "eating_drinking" in topics:
        suggestions += [
            "**Eating/drinking support (general):**",
            "- Offer small sips/snacks more frequently and make food easy to chew/swallow.",
            "- Watch for dehydration signs (very dark urine, dizziness, very dry mouth) and seek guidance if concerned.",
        ]
    if "safety" in topics:
        suggestions += [
            "**Safety support (general):**",
            "- Reduce fall risks (clear pathways, good lighting, assistive devices if already used).",
            "- If wandering risk: consider supervision, door alarms, ID bracelet, and a plan for if they leave.",
        ]
    if "mood" in topics:
        suggestions += [
            "**Mood support (general):**",
            "- Listen and validate feelings; try gentle structure and social connection if welcome.",
            "- If you notice any self-harm language or intent, treat it as urgent and seek immediate help.",
        ]
    if "caregiver_stress" in topics:
        suggestions += [
            "**Caregiver support (you matter too):**",
            "- If possible, take a short break (even 5–10 minutes) and hydrate/eat.",
            "- Ask someone specific for help (e.g., “Can you sit with them for 30 minutes today?”).",
            "- Consider local respite, caregiver groups, or talking with a clinician/therapist for support.",
        ]

    # Always include general steps
    suggestions += ["---", "**Helpful next steps (general):**"] + [f"- {x}" for x in GENERAL_STEPS]

    # Structured “what to track”
    tracking = [
        "- When it started / how it changed over time",
        "- Triggers (time of day, meals, new stressors, activity)",
        "- What helped (calm environment, hydration, rest, distraction)",
        "- Sleep, food, fluids, toileting changes",
        "- Any new safety risks (falls, wandering, choking)",
    ]

    # Draft message template to a clinician (safe + non-diagnostic)
    clinician_msg = f"""Hello, I’m caring for someone and I’m concerned about the following:

- What happened: {user_text.strip()[:400]}
- When it started / timeline:
- Severity (mild/moderate/severe) and what has changed:
- What we tried and what helped:
- Any safety concerns (falls, breathing, confusion, etc.):

Could you advise on next steps and whether we should be seen urgently?
"""

    return {
        "urgency": urgency,
        "urgency_color": urgency_color,
        "emergency_hits": emergency_hits,
        "urgent_hits": urgent_hits,
        "topics": topics,
        "mentions_meds": mentions_meds,
        "suggestions": suggestions,
        "tracking": tracking,
        "clinician_msg": clinician_msg,
    }


# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title="Caregiver Support (Rule-Based Demo)", page_icon="🧩", layout="centered")

st.title("🧩 Caregiver Support (Rule-Based Demo)")
st.markdown(DISCLAIMER)

with st.sidebar:
    st.header("About")
    st.write(
        "This is a **demo-only** caregiver-support assistant built for workshops. "
        "It uses **regex + keywords**—no AI, no external APIs."
    )
    st.write("**Non-diagnostic** • **No medication changes** • **Safety-forward**")
    st.divider()
    st.caption("Tip: Keep descriptions short and factual (what/when/how changed).")

tab1, tab2 = st.tabs(["Support suggestions", "Care notes (log)"])

with tab1:
    user_text = st.text_area(
        "Describe the situation (plain language):",
        height=160,
        placeholder="Example: Mom fell yesterday and seems more confused today. She won’t eat much and is agitated in the evening.",
    )

    colA, colB = st.columns([1, 1])
    with colA:
        run = st.button("Generate suggestions", type="primary")
    with colB:
        st.button("Clear", on_click=lambda: st.session_state.update({"_clear": True}))

    if st.session_state.get("_clear"):
        st.session_state["_clear"] = False
        st.rerun()

    if run:
        if not user_text.strip():
            st.warning("Please enter a brief description first.")
        else:
            result = build_response(user_text)

            # Urgency banner
            if result["urgency_color"] == "red":
                st.error(result["urgency"])
            elif result["urgency_color"] == "orange":
                st.warning(result["urgency"])
            else:
                st.success(result["urgency"])

            # Matched flags
            if result["emergency_hits"]:
                st.markdown("**Matched emergency flags:**")
                st.write("• " + "\n• ".join(result["emergency_hits"]))
            if result["urgent_hits"]:
                st.markdown("**Matched urgent flags:**")
                st.write("• " + "\n• ".join(result["urgent_hits"]))
            if result["topics"]:
                st.markdown("**Detected topics (keyword-based):**")
                st.write(", ".join(result["topics"]))

            st.subheader("Suggested next steps (non-diagnostic)")
            for item in result["suggestions"]:
                if item == "---":
                    st.divider()
                else:
                    st.markdown(f"- {item}" if not item.startswith("**") else item)

            with st.expander("What to track for a clinician or caregiver team"):
                st.markdown("\n".join(result["tracking"]))

            with st.expander("Draft message you can copy to a clinician (editable)"):
                st.code(result["clinician_msg"], language="text")

            # Prepare export
            export_text = []
            export_text.append("Caregiver Support (Rule-Based Demo) — Export")
            export_text.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
            export_text.append("")
            export_text.append("USER INPUT:")
            export_text.append(user_text.strip())
            export_text.append("")
            export_text.append(f"URGENCY: {result['urgency']}")
            if result["emergency_hits"]:
                export_text.append("EMERGENCY FLAGS: " + ", ".join(result["emergency_hits"]))
            if result["urgent_hits"]:
                export_text.append("URGENT FLAGS: " + ", ".join(result["urgent_hits"]))
            if result["topics"]:
                export_text.append("TOPICS: " + ", ".join(result["topics"]))
            export_text.append("")
            export_text.append("SUGGESTIONS:")
            for item in result["suggestions"]:
                if item != "---":
                    export_text.append(f"- {item}")
            export_text.append("")
            export_text.append("TRACKING CHECKLIST:")
            export_text.extend(result["tracking"])
            export_text.append("")
            export_text.append("CLINICIAN MESSAGE TEMPLATE:")
            export_text.append(result["clinician_msg"])

            st.download_button(
                label="Download these suggestions as a text file",
                data="\n".join(export_text),
                file_name="caregiver_support_export.txt",
                mime="text/plain",
            )

with tab2:
    st.subheader("Care notes (simple log)")
    st.caption("For demo purposes only. Do not include highly sensitive personal data.")

    if "care_log" not in st.session_state:
        st.session_state["care_log"] = []

    with st.form("log_form", clear_on_submit=True):
        what = st.text_input("What happened (brief):", placeholder="e.g., Increased agitation after dinner")
        triggers = st.text_input("Triggers/context:", placeholder="e.g., Loud TV, visitors, missed nap")
        helped = st.text_input("What helped:", placeholder="e.g., Quiet room, short walk, water")
        notes = st.text_area("Notes:", height=80, placeholder="Anything else you want to remember")
        submitted = st.form_submit_button("Add log entry")

    if submitted:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "what_happened": what.strip(),
            "triggers_context": triggers.strip(),
            "what_helped": helped.strip(),
            "notes": notes.strip(),
        }
        st.session_state["care_log"].append(entry)
        st.success("Added.")

    if st.session_state["care_log"]:
        df = pd.DataFrame(st.session_state["care_log"], columns=CARE_LOG_FIELDS)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export log
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download log as CSV",
            data=csv,
            file_name="care_log.csv",
            mime="text/csv",
        )

        if st.button("Clear all log entries"):
            st.session_state["care_log"] = []
            st.rerun()
    else:
        st.info("No log entries yet.")
