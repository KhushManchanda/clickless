
# 🎧 Clickless — Agentic Headphone Buying Guide  

Clickless is an **agentic AI system** that lets users shop for headphones using natural language.  
It processes **millions of Amazon metadata & reviews**, filters headphone products, aggregates review statistics, and uses an LLM-driven multi-agent workflow to generate accurate, personalized buying guides.

---

## 🚀 Features

### 🔹 Agentic Architecture  
Planner → Retriever → Ranker → Explainer  
Supports conversational refinements (“make it wireless”, “increase budget to 100”, etc.)

### 🔹 Product Ranking  
Combines:  
- Budget fit  
- Rating & review count  
- Aspect matches (bass, comfort, ANC…)  
- Popularity  
- Soft & hard constraints from user prompt  

### 🔹 Streamlit UI  
- Chat interface  
- Image cards for products  
- Side‑by‑side comparison tables  
- Debug sidebar (plan + ranked product data)

---

## 📦 Project Structure

```
clickless/
│
├── data/
│   ├── headphones_aggregated_index.jsonl   # final index used by app
│   └── (all massive source datasets ignored)
│
├── src/
│   └── buying_guide/
│       ├── app/
│       ├── index/
│       ├── llm/
│       ├── models/
│       └── config.py
│
├── ui/
│   └── streamlit_app.py
│
├── scripts/
│   ├── build_headphone_indexes_large.py
│   ├── build_headphones_aggregated_index.py
│   └── recommend_headphones.py
│
└── README.md
```

---

## 🧠 How It Works

1. **Headphone Filter (Pass 1)**  
   - Streams through metadata JSONL  
   - Detects headphone-like items  
   - Discards accessories/adapters  
   - Requires valid price  

2. **Review Filter (Pass 2)**  
   - Streams review JSONL  
   - Keeps only reviews for priced headphone products  

3. **Aggregator**  
   - Builds rating histograms  
   - Computes avg. rating  
   - Extracts top pros/cons  
   - Produces `headphones_aggregated_index.jsonl`

4. **Agentic Loop**  
   - Planner builds BuyingGuidePlan  
   - Retriever filters candidates  
   - Ranker scores them  
   - Explainer generates a natural-language recommendation  

---

## 🔧 Setup

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Create `.env`
```
OPENAI_API_KEY=your-key-here
PYTHONPATH=src
```

### 3. Run the Streamlit UI
```
streamlit run ui/streamlit_app.py
```

### 4. CLI usage
```
python -m buying_guide.app.cli --query "headphones under 50 with bass"
```

---

## 🗄 Data

Only this file is committed:

```
data/headphones_aggregated_index.jsonl
```

All large raw data files (25–30GB) are ignored via `.gitignore`.

---

## 🛠 Future Enhancements

- Embedding-based semantic retrieval  
- Real-time web search / Amazon API integration  
- User preference learning  
- Multi-category expansion  

---

## 📄 License

MIT License.
