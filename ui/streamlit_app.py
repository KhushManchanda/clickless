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

from buying_guide.app.session import (  # noqa: E402
    run_agentic_session,
    continue_agentic_session,
)


st.set_page_config(page_title="Headphone Buying Guide", page_icon="🎧", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5 {
        font-weight: 600;
    }
    
    /* Cleaner spacing */
    .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎧 Headphone Buying Guide")


# Ensure API key exists
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set OPENAI_API_KEY in a .env file at the project root.")
    st.stop()


# ---------- SESSION STATE SETUP ----------

if "messages" not in st.session_state:
    # Chat history for UI and planner/explainer context
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hi! Tell me what kind of headphones you're looking for "
                "(budget, use-case like gym/commute/audiophile, etc.)."
            ),
        }
    ]

if "last_result" not in st.session_state:
    # Stores the last agentic result (plan + products + explainer_products + answer)
    st.session_state["last_result"] = None


# ---------- HELPERS FOR UI RENDERING ----------

def render_product_cards(products):
    """
    Render compact product cards showing only image, name, and price.
    Click to expand for full details (rating, reviews, pros/cons, ASIN).
    """
    if not products:
        st.info("No products to display.")
        return

    st.subheader("Recommendations")

    for idx, p in enumerate(products, 1):
        asin = p.get("asin")
        amazon_url = f"https://www.amazon.com/dp/{asin}" if asin else None
        
        # Compact card with just image, name, price - expandable for full details
        with st.expander(f"**#{idx}** · {p['title'][:60]}{'...' if len(p['title']) > 60 else ''}", expanded=False):
            cols = st.columns([1, 2])
            
            # Image
            with cols[0]:
                if p.get("image_url"):
                    st.image(p["image_url"], width="stretch")
                else:
                    st.write("No image")
            
            # Details
            with cols[1]:
                # Price (always visible in title, but repeated here for clarity)
                price = p.get("price")
                if price is not None:
                    st.markdown(f"### ${price:.2f}")
                else:
                    st.markdown("### Price: N/A")
                
                # Rating
                avg_rating = p.get("avg_rating")
                if avg_rating is not None:
                    st.markdown(f"**Rating:** {avg_rating:.2f} / 5.0 ({p.get('review_count', 0)} reviews)")
                else:
                    st.markdown(f"**Rating:** N/A ({p.get('review_count', 0)} reviews)")
                
                # Amazon link
                if asin and amazon_url:
                    st.markdown(f"[View on Amazon]({amazon_url})")
                
                st.markdown("---")
                
            # Pros/Cons
            pros = p.get("sample_pros") or []
            cons = p.get("sample_cons") or []
            
            if pros:
                st.markdown("**Top Pros from Reviews:**")
                for i, pro in enumerate(pros[:3], 1):
                    st.markdown(f"{i}. {pro}")
                st.markdown("")
            
            if cons:
                st.markdown("**Top Cons from Reviews:**")
                for i, con in enumerate(cons[:3], 1):
                    st.markdown(f"{i}. {con}")
                st.markdown("")
            
            # ASIN for reference
            if asin:
                st.caption(f"ASIN: {asin}")
        
        st.markdown("")  # spacing between products


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

    # Build chat history for planner/explainer (excluding the latest user message)
    history_for_llm = st.session_state["messages"][:-1]

    # Decide whether this is the first turn (new search)
    # or a follow-up (explanations / reviews / scoring).
    with st.chat_message("assistant"):
        # Better loading animation with context
        loading_messages = [
            "Analyzing your preferences...",
            "Scoring hundreds of products...",
            "Finding the best matches...",
            "Preparing recommendations..."
        ]
        
        with st.spinner(loading_messages[0]):
            if st.session_state["last_result"] is None:
                # First turn → full agentic pipeline (plan + retrieve + explain)
                result = run_agentic_session(
                    user_input,
                    top_k=3,
                    chat_history=history_for_llm,
                )
            else:
                # Follow-up turn → reuse existing plan/products, only re-explain.
                result = continue_agentic_session(
                    user_input,
                    last_result=st.session_state["last_result"],
                    chat_history=history_for_llm,
                )

        # Save last result for further turns
        st.session_state["last_result"] = result

        answer = result["answer"]
        st.markdown(answer)

        # Only render product cards if the result indicates we should
        # (initial searches = True, follow-up questions about existing products = False)
        if result.get("show_products", True):
            products = result.get("products") or []
            render_product_cards(products)

    # Persist assistant answer as a chat message (text only – UI cards are extra)
    st.session_state["messages"].append({"role": "assistant", "content": answer})


# ---------- SMART SUGGESTIONS (fixed button logic) ----------

# Show buttons when we have products (always show them, don't hide on input)
if st.session_state.get("last_result") and st.session_state["last_result"].get("products"):
    st.markdown("")
    st.markdown("")
    st.markdown("##### Quick Actions")
    cols = st.columns(3)
    
    with cols[0]:
        if st.button("📊 Compare Top 2", use_container_width=True, type="secondary", key="btn_compare"):
            st.session_state["pending_query"] = "Compare #1 and #2"
            st.rerun()
    
    with cols[1]:
        if st.button("💬 Reviews for #1", use_container_width=True, type="secondary", key="btn_reviews"):
            st.session_state["pending_query"] = "Give me reviews for the first product"
            st.rerun()
    
    with cols[2]:
        # Smart cheaper options - reduce current budget by 20%
        if st.button("💵 Cheaper Options", use_container_width=True, type="secondary", key="btn_cheaper"):
            current_plan = st.session_state["last_result"].get("plan", {})
            current_budget = current_plan.get("budget")
            
            if current_budget and current_budget > 0:
                # Reduce by 20%
                new_budget = round(current_budget * 0.8, 2)
                st.session_state["pending_query"] = f"Show me headphones under ${new_budget:.0f}"
                st.session_state["trigger_new_search"] = True  # Flag to trigger new search
            else:
                # No budget was set, use generic cheaper query
                st.session_state["pending_query"] = "Show me cheaper alternatives"
                st.session_state["trigger_new_search"] = True
            st.rerun()

# Process pending query from button click
if "pending_query" in st.session_state:
    pending = st.session_state["pending_query"]
    trigger_new_search = st.session_state.get("trigger_new_search", False)
    
    del st.session_state["pending_query"]
    if "trigger_new_search" in st.session_state:
        del st.session_state["trigger_new_search"]
    
    # Add as user message
    st.session_state["messages"].append({"role": "user", "content": pending})
    
    # Process the query
    history_for_llm = st.session_state["messages"][:-1]
    
    with st.chat_message("user"):
        st.markdown(pending)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            # If cheaper options, trigger a NEW search instead of continuing
            if trigger_new_search:
                result = run_agentic_session(
                    pending,
                    top_k=3,
                    chat_history=history_for_llm,
                )
            else:
                result = continue_agentic_session(
                    pending,
                    last_result=st.session_state["last_result"],
                    chat_history=history_for_llm,
                )
    
        st.session_state["last_result"] = result
        answer = result["answer"]
        st.markdown(answer)
        
        if result.get("show_products", True):
            products = result.get("products") or []
            render_product_cards(products)
    
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    st.rerun()


# ---------- SIDEBAR ----------

with st.sidebar:
    st.header("Settings")
    
    if st.button("🔄 New Search", use_container_width=True, type="primary"):
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hi! Tell me what kind of headphones you're looking for (budget, use-case like gym/commute/audiophile, etc.).",
            }
        ]
        st.session_state["last_result"] = None
        st.rerun()
    
    st.markdown("---")
    
    # Debug section (collapsible)
    if st.session_state.get("last_result"):
        with st.expander("Debug Data"):
            st.write("**Plan:**")
            st.json(st.session_state["last_result"]["plan"])
            st.write("**Products:**")
            st.json(st.session_state["last_result"]["products"])
