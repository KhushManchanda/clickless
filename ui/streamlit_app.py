import os
import sys

from dotenv import load_dotenv
import streamlit as st

# Load .env (for OPENAI_API_KEY, etc.)
load_dotenv()

# Make sure src/ is on sys.path when running via `streamlit run ui/streamlit_app.py`
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from buying_guide.app.session import run_agentic_session  # noqa: E402


st.set_page_config(page_title="Headphone Buying Guide", page_icon="🎧")
st.title("🎧 Headphone Buying Guide (Agentic Chatbot)")


# Ensure API key exists
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set OPENAI_API_KEY in a .env file at the project root.")
    st.stop()


# ---------- SESSION STATE SETUP ----------

if "messages" not in st.session_state:
    # Chat history for UI and planner context
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "Hi! Tell me what kind of headphones you're looking for "
                       "(budget, use-case like gym/commute/audiophile, etc.).",
        }
    ]

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None  # store last agentic result (plan + products + answer)


# ---------- HELPERS FOR UI RENDERING ----------

def render_product_cards(products):
    """
    Render a list of product dicts as UI cards with optional thumbnail image.
    Each product is expected to have:
      - title, price, avg_rating, review_count, asin, score, image_url
    """
    if not products:
        st.info("No products to display.")
        return

    st.subheader("Recommended Products")

    for p in products:
        with st.container():
            cols = st.columns([1, 3])

            # Image
            with cols[0]:
                if p.get("image_url"):
                    st.image(p["image_url"])
                else:
                    st.write("No image")

            # Textual info
            with cols[1]:
                st.markdown(f"**{p['title']}**")
                price = p.get("price")
                if price is not None:
                    st.markdown(f"**Price:** ${price:.2f}")
                else:
                    st.markdown("**Price:** N/A")

                avg_rating = p.get("avg_rating")
                if avg_rating is not None:
                    st.markdown(
                        f"**Rating:** {avg_rating:.2f} ⭐  "
                        f"({p.get('review_count', 0)} reviews)"
                    )
                else:
                    st.markdown(
                        f"**Rating:** N/A  "
                        f"({p.get('review_count', 0)} reviews)"
                    )

                st.markdown(
                    f"**Score:** {p.get('score', 0):.3f} "
                    f"(base: {p.get('base_score', 0):.3f}, "
                    f"aspects: {p.get('aspect_score', 0):.3f})"
                )
                st.markdown(f"**ASIN:** `{p.get('asin')}`")

            st.markdown("---")


def render_comparison_table(products):
    """
    Render a side-by-side comparison table for the current recommendations.
    """
    if not products:
        return

    import pandas as pd

    rows = []
    for p in products:
        rows.append(
            {
                "Title": p["title"],
                "Price ($)": p["price"],
                "Avg Rating": p["avg_rating"],
                "Reviews": p["review_count"],
                "Score": p["score"],
                "Base Score": p["base_score"],
                "Aspect Score": p["aspect_score"],
                "ASIN": p["asin"],
            }
        )

    df = pd.DataFrame(rows)
    st.subheader("Side-by-Side Comparison")
    st.dataframe(df, width="stretch")


# ---------- RENDER CHAT HISTORY ----------

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------- HANDLE NEW USER INPUT ----------

user_input = st.chat_input("Ask me for headphone recommendations...")
if user_input:
    # Show user message in chat
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build chat history for planner (excluding the latest user message)
    history_for_planner = st.session_state["messages"][:-1]

    # Agentic turn
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = run_agentic_session(
                user_input,
                top_k=5,
                chat_history=history_for_planner,
            )

        # Save last result for further UI (cards + comparison)
        st.session_state["last_result"] = result

        answer = result["answer"]
        st.markdown(answer)

        products = result.get("products") or []

        # Render product cards with thumbnails
        render_product_cards(products)

        # Comparison table inside an expander
        with st.expander("Compare these options side by side"):
            render_comparison_table(products)

    # Persist assistant answer as a chat message
    st.session_state["messages"].append({"role": "assistant", "content": answer})


# ---------- OPTIONAL: SHOW RAW PLAN & DATA ----------

if st.session_state["last_result"]:
    with st.sidebar:
        st.header("Debug / Inspector")
        st.write("Planner output (current plan):")
        st.json(st.session_state["last_result"]["plan"])
        st.write("Top products (raw):")
        st.json(st.session_state["last_result"]["products"])
