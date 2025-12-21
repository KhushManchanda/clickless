
# 🎧 Clickless — AI Headphone Buying Guide  

Clickless is an **agentic AI system** that transforms headphone shopping into a simple conversation. Instead of clicking through hundreds of products and reading thousands of reviews, just tell Clickless what you're looking for and get personalized recommendations backed by actual user reviews.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://khushmanchanda-clickless-uistreamlit-app-escdit.streamlit.app)

---

## 🚀 Features

### 🔹 Natural Language Shopping  
Just type what you want:
> *"Wireless headphones under $100 with good bass for the gym"*

No complex filters, no endless scrolling—Clickless understands your requirements and finds the right products.

### 🔹 Agentic Architecture  
**Planner → Retriever → Ranker → Explainer**  
- **Planner**: Extracts your budget, preferences, and use case
- **Retriever**: Filters from 12,000+ headphones with aggregated reviews
- **Ranker**: Scores products based on your specific needs
- **Explainer**: Generates natural language recommendations with reasoning

### 🔹 Smart Product Ranking  
Combines multiple signals:  
- Budget fit  
- Rating & review count  
- Feature matches (bass, comfort, ANC, wireless, etc.)  
- Use-case relevance (gym, commuting, gaming, etc.)  
- Hard & soft constraints from your query

### 🔹 Conversational Refinement  
Keep chatting to refine your search:
- *"Make it wireless"*
- *"Increase budget to $150"*
- *"Why did you pick #1?"*
- *"What do reviews say about comfort?"*

### 🔹 Interactive UI  
- Clean chat interface
- Product cards with images, prices, and ratings
- Direct Amazon links (ASIN-based)
- Side-by-side comparison tables
- Debug sidebar showing the AI's reasoning

---

## 📦 Project Structure

```
clickless/
│
├── data/
│   └── headphones_aggregated_index.jsonl   # 12K products with review summaries
│
├── src/
│   └── buying_guide/
│       ├── app/
│       │   ├── cli.py                       # Command-line interface
│       │   └── session.py                   # Session orchestration
│       ├── index/
│       │   ├── filters.py                   # Product filtering logic
│       │   ├── loader.py                    # Index loading
│       │   ├── retriever.py                 # Product retrieval
│       │   └── scoring.py                   # Ranking algorithms
│       ├── llm/
│       │   ├── client.py                    # OpenAI client
│       │   ├── planner.py                   # Query understanding
│       │   └── explainer.py                 # Response generation
│       ├── models/
│       │   ├── plan.py                      # BuyingGuidePlan schema
│       │   └── product.py                   # Product models
│       └── config.py                        # Configuration
│
├── ui/
│   └── streamlit_app.py                     # Streamlit web interface
│
├── scripts/
│   ├── build_headphone_indexes_large.py.py  # Step 1: Filter headphones
│   ├── build_headphones_aggregated_index.py # Step 2: Aggregate reviews
│   └── recommend_headphones.py              # CLI testing script
│
├── requirements.txt
├── .env                                     # Your OpenAI API key
└── README.md
```

---

## 🧠 How It Works

### 1. **Data Preprocessing** (Already Done)

The system is built on the **UCSD Amazon Product Dataset** (Electronics subset):

**Pass 1: Headphone Filter**  
- Streams through 1.6M product metadata entries
- Identifies headphone products using keyword heuristics
- Discards accessories, cables, and adapters
- Requires valid price data
- **Output**: 27,628 priced headphone products

**Pass 2: Review Filter**  
- Streams through 43.9M reviews
- Keeps only reviews for the filtered headphone products
- **Output**: 5.5M headphone reviews

**Pass 3: Aggregation**  
- Joins products with their reviews
- Computes rating statistics and histograms
- Extracts top pros/cons from highly-rated helpful reviews
- **Output**: `data/headphones_aggregated_index.jsonl` (12,339 products with ≥1 review)

### 2. **Conversational Shopping Flow**

```
User Query: "Gym headphones under $50 with strong bass"
         │
         ▼
    ┌─────────────────────────────────┐
    │  Planner (LLM)                  │
    │  Extracts:                      │
    │  - Budget: ≤ $50                │
    │  - Use-case: Gym                │
    │  - Priorities: Bass, sweat-proof│
    └─────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────┐
    │  Retriever + Ranker             │
    │  - Filters by budget            │
    │  - Scores by relevance          │
    │  - Returns top-k products       │
    └─────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────┐
    │  Explainer (LLM)                │
    │  - Generates summary            │
    │  - Explains reasoning           │
    │  - Cites review pros/cons       │
    └─────────────────────────────────┘
         │
         ▼
    Product Cards + Conversational Answer
```

---

## 🔧 Setup & Usage

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/KhushManchanda/clickless.git
cd clickless

# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" > .env
echo "PYTHONPATH=src" >> .env
```

### Running the Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Then open your browser to `http://localhost:8501` and start chatting!

### Using the CLI

```bash
python -m buying_guide.app.cli --query "headphones under 50 with bass"
```

The CLI will output:
- The extracted buying plan
- Top-ranked products with scores
- Natural language recommendation

---

## 🗄 Data Files

The repository includes only the **final aggregated index**:
```
data/headphones_aggregated_index.jsonl
```

This file contains 12,339 headphones with:
- Product metadata (title, price, features, images, ASIN)
- Aggregated review stats (avg rating, total reviews, rating histogram)
- Extracted pros/cons from helpful reviews

**Note**: Large raw data files (25-30GB) are excluded via `.gitignore` and not required to run the app.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.8+ |
| **LLM** | OpenAI GPT-4 |
| **Web UI** | Streamlit |
| **Data Processing** | Streaming JSONL (memory-efficient) |
| **Dataset** | UCSD Amazon Product Dataset |
| **Deployment** | Streamlit Community Cloud |

---

## 🎯 Key Features & Capabilities

### ✅ Explainable AI
Every recommendation includes:
- **Why** each product was chosen
- **Trade-offs** between options
- **Review quotes** supporting the recommendation

### ✅ Conversational Context
The system maintains context across turns:
- *"Make it wireless"* → Keeps budget and use-case from previous turn
- *"Cheaper options"* → Adjusts budget while keeping other preferences

### ✅ Multi-Constraint Handling
Handles complex queries with multiple constraints:
- Budget limits (hard constraint)
- Feature requirements (wireless, ANC, etc.)
- Use-case preferences (gym, commuting, gaming)
- Sound preferences (bass, balanced, audiophile)

### ✅ Review-Backed Recommendations
Uses actual customer reviews to:
- Extract common pros/cons
- Validate product claims
- Provide trust signals

---

## 🚀 Future Enhancements

- [ ] **Embedding-based semantic search** for better query understanding
- [ ] **Real-time price tracking** via Amazon Product Advertising API
- [ ] **User preference learning** from interaction history
- [ ] **Multi-category expansion** (laptops, cameras, smartwatches)
- [ ] **Comparison mode** for side-by-side detailed analysis
- [ ] **Price drop alerts** for saved products

---

## 📄 License

MIT License

This project uses the UCSD Amazon Product Dataset under its respective license terms.

---

## 👤 Author

**Khush Manchanda**  
GitHub: [@KhushManchanda](https://github.com/KhushManchanda)

---

**Built to make online shopping less painful, one conversation at a time.** 💬🎧
