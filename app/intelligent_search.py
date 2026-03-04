"""
Healthcare AI Search - Enterprise Demo
Semantic patient search powered by Couchbase Vector Search + OpenAI
Modern UI with Shadcn components + AI Copilot
"""

import streamlit as st
import streamlit_shadcn_ui as ui
import os
import pandas as pd
from datetime import timedelta
from dotenv import load_dotenv
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
import openai

load_dotenv()

# Config
COUCHBASE_CONNECTION_STRING = os.getenv("COUCHBASE_CONNECTION_STRING")
COUCHBASE_USERNAME = os.getenv("COUCHBASE_USERNAME")
COUCHBASE_PASSWORD = os.getenv("COUCHBASE_PASSWORD")
COUCHBASE_BUCKET = os.getenv("COUCHBASE_BUCKET", "pharma_knowledge")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Page config
st.set_page_config(
    page_title="Healthcare AI Platform",
    page_icon="https://cdn-icons-png.flaticon.com/512/2966/2966327.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern CSS with glassmorphism and dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main > div { padding: 1rem 2rem; }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* App header */
    .app-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98));
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    .app-title {
        font-size: 2.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #6366f1, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .app-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    .filter-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    /* Result cards */
    .result-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .result-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
    }
    
    .result-rank {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        color: white;
        margin-right: 0.75rem;
    }
    
    .result-condition {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e2e8f0;
    }
    
    .result-summary {
        color: #cbd5e1;
        font-size: 0.9rem;
        font-style: italic;
        margin: 0.75rem 0;
        padding-left: 1rem;
        border-left: 2px solid rgba(99, 102, 241, 0.4);
    }
    
    .result-details {
        display: flex;
        gap: 1.5rem;
        margin-top: 0.75rem;
        flex-wrap: wrap;
    }
    
    .detail-item {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        color: #94a3b8;
        font-size: 0.85rem;
    }
    
    .score-badge {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(22, 163, 74, 0.3));
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #4ade80;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .billing-badge {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(79, 70, 229, 0.3));
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #a5b4fc;
        padding: 0.35rem 0.85rem;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    /* Query display */
    .query-box {
        background: rgba(6, 78, 59, 0.3);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 12px;
        padding: 1rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.8rem;
        color: #4ade80;
        white-space: pre-wrap;
        overflow-x: auto;
    }
    
    /* Breakdown section */
    .breakdown-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-radius: 10px;
        padding: 1rem;
    }
    
    .breakdown-title {
        font-size: 0.75rem;
        color: #818cf8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }
    
    .breakdown-item {
        display: flex;
        justify-content: space-between;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(99, 102, 241, 0.08);
        font-size: 0.85rem;
    }
    
    .breakdown-item:last-child { border-bottom: none; }
    .breakdown-name { color: #94a3b8; }
    .breakdown-count { color: #e2e8f0; font-weight: 600; }
    
    /* Chat styles */
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(79, 70, 229, 0.3));
        border: 1px solid rgba(99, 102, 241, 0.3);
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(99, 102, 241, 0.15);
        margin-right: 2rem;
    }
    
    .source-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
    }
    
    /* Streamlit overrides */
    .stTextInput > div > div > input {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 10px;
        color: #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
    
    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 8px;
    }
    
    div[data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.8);
        border-color: rgba(99, 102, 241, 0.2);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #818cf8, #6366f1);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    .stExpander {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Cache connection
@st.cache_resource
def get_cluster():
    auth = PasswordAuthenticator(COUCHBASE_USERNAME, COUCHBASE_PASSWORD)
    options = ClusterOptions(auth)
    options.apply_profile("wan_development")
    cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)
    cluster.wait_until_ready(timedelta(seconds=10))
    return cluster

# Cache filter options
@st.cache_data(ttl=3600)
def load_filter_options():
    return {
        "age_groups": ["All", "Child", "Young Adult", "Middle-Aged", "Adult", "Elderly"],
        "billing_categories": ["All", "Low", "Medium", "High"],
        "conditions": ["All", "Diabetes", "Hypertension", "Asthma", "Cancer", "Obesity", "Arthritis"],
        "medications": ["All", "Paracetamol", "Aspirin", "Ibuprofen", "Penicillin", "Lipitor", "Metformin"]
    }

# Get stats from pre-computed document (KV lookup = instant)
def get_stats_from_kv(_cluster):
    """Read pre-computed stats from stats collection - instant lookup"""
    try:
        bucket = _cluster.bucket(COUCHBASE_BUCKET)
        collection = bucket.scope("_default").collection("stats")
        result = collection.get("dashboard_stats")
        return result.content_as[dict]
    except Exception as e:
        # Fallback to None if stats doc doesn't exist
        return None

# Cache basic statistics (fallback if KV doc doesn't exist)
@st.cache_data(ttl=3600)
def load_basic_stats(_cluster):
    try:
        query = f"""
            SELECT 
                COUNT(*) AS total_patients,
                COUNT(*) FILTER (WHERE vector IS NOT MISSING) AS with_embeddings,
                COUNT(DISTINCT medical.condition) AS conditions,
                COUNT(DISTINCT medical.medication) AS medications
            FROM {COUCHBASE_BUCKET}._default.processed_documents
            WHERE type = "processed_patient_record"
        """
        result = list(_cluster.query(query))
        return result[0] if result else None
    except:
        return None

# Cache breakdown stats
@st.cache_data(ttl=3600)
def load_breakdown_stats(_cluster):
    stats = {}
    try:
        combined_query = f"""
            SELECT 'age' AS type, metrics.age_group AS category, COUNT(*) AS count
            FROM {COUCHBASE_BUCKET}._default.processed_documents
            WHERE type = "processed_patient_record" AND metrics.age_group IS NOT MISSING
            GROUP BY metrics.age_group
            UNION ALL
            SELECT 'billing' AS type, metrics.billing_category AS category, COUNT(*) AS count
            FROM {COUCHBASE_BUCKET}._default.processed_documents
            WHERE type = "processed_patient_record" AND metrics.billing_category IS NOT MISSING
            GROUP BY metrics.billing_category
            UNION ALL
            SELECT 'condition' AS type, medical.condition AS category, COUNT(*) AS count
            FROM {COUCHBASE_BUCKET}._default.processed_documents
            WHERE type = "processed_patient_record" AND medical.condition IS NOT MISSING
            GROUP BY medical.condition
            UNION ALL
            SELECT 'medication' AS type, medical.medication AS category, COUNT(*) AS count
            FROM {COUCHBASE_BUCKET}._default.processed_documents
            WHERE type = "processed_patient_record" AND medical.medication IS NOT MISSING AND medical.medication != "None"
            GROUP BY medical.medication
        """
        results = list(_cluster.query(combined_query))
        
        stats['by_age'] = {}
        stats['by_billing'] = {}
        stats['by_condition'] = {}
        stats['by_medication'] = {}
        
        for r in results:
            t = r.get('type')
            if t == 'age':
                stats['by_age'][r['category']] = r['count']
            elif t == 'billing':
                stats['by_billing'][r['category']] = r['count']
            elif t == 'condition':
                stats['by_condition'][r['category']] = r['count']
            elif t == 'medication':
                stats['by_medication'][r['category']] = r['count']
        
        return stats
    except:
        return None

def generate_embedding(text: str) -> list:
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def search_patients(cluster, query_text: str, age_group: str, billing: str, condition: str, medication: str, limit: int):
    embedding = generate_embedding(query_text)
    
    conditions = ["d.vector IS NOT MISSING", "d.type = 'processed_patient_record'"]
    if age_group != "All":
        conditions.append(f'd.metrics.age_group = "{age_group}"')
    if billing != "All":
        conditions.append(f'd.metrics.billing_category = "{billing}"')
    if condition != "All":
        conditions.append(f'd.medical.condition = "{condition}"')
    if medication != "All":
        conditions.append(f'd.medical.medication = "{medication}"')
    
    where_clause = " AND ".join(conditions)
    
    display_query = f"""SELECT META(d).id, d.medical_summary, d.patient.gender,
       d.medical.condition, d.medical.medication, d.medical.hospital,
       d.metrics.age_group, d.metrics.billing_category, d.billing.amount,
       APPROX_VECTOR_DISTANCE(d.vector, $embedding, "DOT") AS score
FROM {COUCHBASE_BUCKET}._default.processed_documents d
WHERE {where_clause}
ORDER BY APPROX_VECTOR_DISTANCE(d.vector, $embedding, "DOT")
LIMIT {limit};

-- $embedding = OpenAI text-embedding-3-small (1536 dims)
-- Query: "{query_text[:60]}..." """
    
    embedding_str = str(embedding)
    query = f"""
        SELECT META(d).id AS id,
               d.medical_summary,
               d.patient.gender,
               d.medical.condition,
               d.medical.medication,
               d.medical.hospital,
               d.medical.admission_type,
               d.metrics.age_group,
               d.metrics.billing_category,
               d.billing.amount,
               APPROX_VECTOR_DISTANCE(d.vector, {embedding_str}, "DOT") AS score
        FROM {COUCHBASE_BUCKET}._default.processed_documents d
        WHERE {where_clause}
        ORDER BY APPROX_VECTOR_DISTANCE(d.vector, {embedding_str}, "DOT")
        LIMIT {limit}
    """
    
    try:
        results = list(cluster.query(query))
        return results, display_query
    except Exception as e:
        st.error(f"Search failed: {e}")
        return [], display_query

def retrieve_context(cluster, question: str, limit: int = 8):
    """Retrieve relevant patient records for RAG context. Returns (results, display_query)."""
    embedding = generate_embedding(question)
    embedding_str = str(embedding)
    
    # Display-friendly query
    display_query = f"""SELECT META(d).id, d.medical_summary, d.patient.gender,
       d.medical.condition, d.medical.medication, d.medical.hospital,
       d.medical.admission_type, d.metrics.age_group, d.metrics.billing_category,
       d.billing.amount
FROM {COUCHBASE_BUCKET}._default.processed_documents d
WHERE d.vector IS NOT MISSING AND d.type = 'processed_patient_record'
ORDER BY APPROX_VECTOR_DISTANCE(d.vector, $embedding, "DOT")
LIMIT {limit};

-- $embedding = OpenAI text-embedding-3-small (1536 dims)
-- Question: "{question[:80]}..." """
    
    query = f"""
        SELECT META(d).id AS id,
               d.medical_summary,
               d.patient.gender,
               d.medical.condition,
               d.medical.medication,
               d.medical.hospital,
               d.medical.admission_type,
               d.metrics.age_group,
               d.metrics.billing_category,
               d.billing.amount
        FROM {COUCHBASE_BUCKET}._default.processed_documents d
        WHERE d.vector IS NOT MISSING AND d.type = 'processed_patient_record'
        ORDER BY APPROX_VECTOR_DISTANCE(d.vector, {embedding_str}, "DOT")
        LIMIT {limit}
    """
    
    try:
        return list(cluster.query(query)), display_query
    except:
        return [], display_query

def generate_copilot_response(question: str, context: list) -> tuple:
    """Generate AI response using retrieved context. Returns (response, context_text)."""
    
    # Format context for the prompt
    context_text = "\n\n".join([
        f"Patient {i+1}:\n"
        f"- Condition: {p.get('condition', 'N/A')}\n"
        f"- Age Group: {p.get('age_group', 'N/A')}\n"
        f"- Gender: {p.get('gender', 'N/A')}\n"
        f"- Medication: {p.get('medication', 'N/A')}\n"
        f"- Admission: {p.get('admission_type', 'N/A')}\n"
        f"- Hospital: {p.get('hospital', 'N/A')}\n"
        f"- Billing: ${p.get('amount', 0):,.0f} ({p.get('billing_category', 'N/A')})\n"
        f"- Summary: {p.get('medical_summary', 'N/A')}"
        for i, p in enumerate(context)
    ])
    
    system_prompt = """You are an AI healthcare assistant helping pharmaceutical researchers analyze patient data. 
You have access to a database of patient records with conditions, medications, billing, and demographics.

Based on the retrieved patient records below, answer the user's question with specific insights.
Always cite which patients support your analysis. Be concise but thorough.
If the data doesn't support a definitive answer, say so.

Retrieved Patient Records:
""" + context_text

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    return response.choices[0].message.content, context_text

# Session state initialization
if "results" not in st.session_state:
    st.session_state.results = None
if "searched" not in st.session_state:
    st.session_state.searched = False
if "executed_query" not in st.session_state:
    st.session_state.executed_query = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "copilot_sources" not in st.session_state:
    st.session_state.copilot_sources = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

def render_search_tab(cluster, filters):
    """Render the patient search interface."""
    
    # Get stats from KV document (instant) or fallback to query
    stats_doc = get_stats_from_kv(cluster)
    
    if stats_doc:
        # Stats from pre-computed KV document (instant)
        cols = st.columns(4)
        with cols[0]:
            ui.card(title="Total Patients", content=f"{stats_doc.get('total_patients', 0):,}", key="card_total").render()
        with cols[1]:
            ui.card(title="With Embeddings", content=f"{stats_doc.get('with_embeddings', 0):,}", key="card_embed").render()
        with cols[2]:
            ui.card(title="Conditions", content=str(stats_doc.get('unique_conditions', 0)), key="card_cond").render()
        with cols[3]:
            ui.card(title="Medications", content=str(stats_doc.get('unique_medications', 0)), key="card_med").render()
        
        # Breakdown expander
        with st.expander("View Patient Distribution by Category", expanded=False):
            bc1, bc2, bc3, bc4 = st.columns(4)
            
            with bc1:
                st.markdown('<div class="breakdown-card"><div class="breakdown-title">By Age Group</div>', unsafe_allow_html=True)
                for cat, count in sorted(stats_doc.get('by_age_group', {}).items(), key=lambda x: -x[1]):
                    st.markdown(f'<div class="breakdown-item"><span class="breakdown-name">{cat}</span><span class="breakdown-count">{count:,}</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with bc2:
                st.markdown('<div class="breakdown-card"><div class="breakdown-title">By Billing</div>', unsafe_allow_html=True)
                for cat, count in sorted(stats_doc.get('by_billing', {}).items(), key=lambda x: -x[1]):
                    st.markdown(f'<div class="breakdown-item"><span class="breakdown-name">{cat}</span><span class="breakdown-count">{count:,}</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with bc3:
                st.markdown('<div class="breakdown-card"><div class="breakdown-title">By Condition</div>', unsafe_allow_html=True)
                for cat, count in sorted(stats_doc.get('by_condition', {}).items(), key=lambda x: -x[1]):
                    st.markdown(f'<div class="breakdown-item"><span class="breakdown-name">{cat}</span><span class="breakdown-count">{count:,}</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with bc4:
                st.markdown('<div class="breakdown-card"><div class="breakdown-title">By Medication</div>', unsafe_allow_html=True)
                for cat, count in sorted(stats_doc.get('by_medication', {}).items(), key=lambda x: -x[1]):
                    st.markdown(f'<div class="breakdown-item"><span class="breakdown-name">{cat}</span><span class="breakdown-count">{count:,}</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Stats document not found. Deploy the stats eventing function to enable real-time stats.")
    
    # Search section
    search_col, btn_col = st.columns([5, 1])
    
    with search_col:
        query = st.text_input(
            "Search Query",
            placeholder="Describe the patient profile (e.g., diabetic patient with emergency admission)",
            label_visibility="collapsed",
            key="search_query"
        )
    
    with btn_col:
        search_clicked = st.button("Search", type="primary", use_container_width=True, key="search_btn")
    
    # Filters
    f1, f2, f3, f4, f5 = st.columns(5)
    
    with f1:
        st.markdown('<div class="filter-label">Age Group</div>', unsafe_allow_html=True)
        age = st.selectbox("Age", filters["age_groups"], label_visibility="collapsed", key="filter_age")
    with f2:
        st.markdown('<div class="filter-label">Billing</div>', unsafe_allow_html=True)
        billing = st.selectbox("Billing", filters["billing_categories"], label_visibility="collapsed", key="filter_billing")
    with f3:
        st.markdown('<div class="filter-label">Condition</div>', unsafe_allow_html=True)
        condition = st.selectbox("Condition", filters["conditions"], label_visibility="collapsed", key="filter_condition")
    with f4:
        st.markdown('<div class="filter-label">Medication</div>', unsafe_allow_html=True)
        medication = st.selectbox("Medication", filters["medications"], label_visibility="collapsed", key="filter_medication")
    with f5:
        st.markdown('<div class="filter-label">Results</div>', unsafe_allow_html=True)
        limit = st.selectbox("Limit", [5, 10, 20, 50], index=1, label_visibility="collapsed", key="filter_limit")
    
    # Search execution
    if search_clicked:
        if not query:
            st.warning("Please enter a search query")
        else:
            with st.spinner("Searching similar patients..."):
                results, executed_query = search_patients(cluster, query, age, billing, condition, medication, limit)
                st.session_state.results = results
                st.session_state.executed_query = executed_query
                st.session_state.searched = True
    
    # Results display
    if st.session_state.searched and st.session_state.results:
        results = st.session_state.results
        
        st.markdown("---")
        
        badge_list = [("Results", "default"), (str(len(results)), "secondary")]
        if age != "All":
            badge_list.append((age, "outline"))
        if billing != "All":
            badge_list.append((billing, "outline"))
        if condition != "All":
            badge_list.append((condition, "outline"))
        if medication != "All":
            badge_list.append((medication, "outline"))
        
        ui.badges(badge_list=badge_list, class_name="flex gap-2", key="result_badges")
        
        # Query expander
        if st.session_state.executed_query:
            with st.expander("View Couchbase Query", expanded=False):
                st.markdown(f'<div class="query-box">{st.session_state.executed_query}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### Composite Vector Index Breakdown")
                
                st.markdown("""
                **Index Type:** This query uses a **Composite Vector Index** on GSI (Global Secondary Index).
                
                | Index Type | Best For | Our Use Case |
                |------------|----------|--------------|
                | **Composite Vector** | Vector + scalar filters (<20% exclusion) | Patient search with age/billing filters |
                | Hyperscale Vector | Pure vector search, billions of docs | Large-scale similarity only |
                | FTS Hybrid | Vector + full-text + geospatial | Text search + vectors |
                """)
                
                st.markdown("#### How the Query Works:")
                
                st.markdown("""
                ```
                1. SCALAR PRE-FILTER (WHERE clause)
                   d.metrics.age_group = "Elderly"
                   - First, Couchbase filters to ONLY matching patients
                   - This dramatically reduces the search space
                
                2. VECTOR SIMILARITY (APPROX_VECTOR_DISTANCE)
                   APPROX_VECTOR_DISTANCE(d.vector, $query_embedding, "DOT")
                   - Compares your query embedding against filtered documents
                   - Uses DOT product similarity (higher = more similar)
                   - "APPROX" = Approximate Nearest Neighbor (ANN) for speed
                
                3. RANKING (ORDER BY)
                   ORDER BY APPROX_VECTOR_DISTANCE(...) 
                   - Results sorted by similarity score
                   - Most similar patients appear first
                
                4. LIMIT
                   - Returns top N most similar matches
                ```
                """)
                
                st.markdown("""
                #### Why Composite Vector Index?
                
                - **Pre-filtering**: Scalar conditions (age, billing) are applied **before** vector search
                - **Efficiency**: Searches only within filtered subset (e.g., only elderly patients)
                - **Native SQL++**: Uses standard Couchbase query language
                - **Single Query**: Combines filtering + similarity in one database call
                
                > **Key Insight**: Unlike post-filtering approaches that search all vectors then filter, 
                > Couchbase's Composite Vector Index filters first, then performs ANN search on the reduced dataset.
                """)
        
        # Results
        st.markdown("")
        
        for i, p in enumerate(results, 1):
            score = abs(p.get('score', 0))
            amount = p.get('amount') or 0
            
            st.markdown(f"""
            <div class="result-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span class="result-rank">{i}</span>
                            <span class="result-condition">{p.get('condition', 'N/A')}</span>
                            <span style="margin-left: 0.75rem;" class="score-badge">Score: {score:.4f}</span>
                        </div>
                        <div class="result-summary">{p.get('medical_summary', 'No summary available')}</div>
                        <div class="result-details">
                            <span class="detail-item">👤 {p.get('age_group', 'N/A')} · {p.get('gender', 'N/A')}</span>
                            <span class="detail-item">🏥 {p.get('hospital', 'N/A')}</span>
                            <span class="detail-item">💊 {p.get('medication', 'N/A')}</span>
                            <span class="detail-item">🚑 {p.get('admission_type', 'N/A')}</span>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div class="billing-badge">${amount:,.0f}</div>
                        <div style="color: #64748b; font-size: 0.75rem; margin-top: 0.25rem;">{p.get('billing_category', '')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    elif st.session_state.searched:
        st.info("No patients found matching your criteria. Try adjusting your search or filters.")
    
    else:
        st.markdown("---")
        st.markdown("""
        ### How to Use
        
        1. **Enter a natural language query** describing the patient profile you're looking for
        2. **Apply filters** to narrow results by age group, billing category, condition, or medication
        3. **Click Search** to find semantically similar patients using vector similarity
        
        ---
        
        #### Example Queries
        - `diabetic patient with emergency admission and high medical costs`
        - `elderly cancer patient prescribed Lipitor`
        - `young adult with asthma requiring urgent care`
        """)

def render_copilot_tab(cluster):
    """Render the AI Copilot chat interface."""
    
    st.markdown("### Ask questions about your patient data")
    st.markdown("The AI Copilot retrieves relevant patient records and generates insights based on your questions.")
    
    # Example questions
    st.markdown("**Try asking:**")
    example_cols = st.columns(3)
    with example_cols[0]:
        if st.button("What medications are common for diabetic patients?", key="ex1"):
            st.session_state.pending_question = "What medications are commonly prescribed for diabetic patients?"
            st.rerun()
    with example_cols[1]:
        if st.button("Compare costs: emergency vs elective", key="ex2"):
            st.session_state.pending_question = "How do billing costs compare between emergency and elective admissions?"
            st.rerun()
    with example_cols[2]:
        if st.button("Elderly patient patterns", key="ex3"):
            st.session_state.pending_question = "What patterns do you see in elderly patient conditions and treatments?"
            st.rerun()
    
    st.markdown("---")
    
    # Process pending question from example buttons
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
        
        with st.spinner("Retrieving relevant patients and generating response..."):
            context, couchbase_query = retrieve_context(cluster, question, limit=8)
            response, context_text = generate_copilot_response(question, context)
            
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": response, 
                "sources": context,
                "couchbase_query": couchbase_query,
                "context_text": context_text
            })
        st.rerun()
    
    # Chat input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask a question",
            placeholder="Ask anything about patient demographics, conditions, medications, or costs...",
            label_visibility="collapsed",
            key="copilot_input"
        )
    
    with col2:
        ask_clicked = st.button("Ask", type="primary", use_container_width=True, key="copilot_ask")
    
    # Process typed question
    if ask_clicked and user_input:
        with st.spinner("Retrieving relevant patients and generating response..."):
            context, couchbase_query = retrieve_context(cluster, user_input, limit=8)
            response, context_text = generate_copilot_response(user_input, context)
            
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": response, 
                "sources": context,
                "couchbase_query": couchbase_query,
                "context_text": context_text
            })
        st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        
        for idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>AI Copilot:</strong><br>{msg["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                # Show Couchbase Query and RAG flow
                if msg.get("couchbase_query"):
                    with st.expander("View Couchbase Query & RAG Flow", expanded=False):
                        st.markdown("#### Step 1: Vector Search Query")
                        st.markdown(f'<div class="query-box">{msg["couchbase_query"]}</div>', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.markdown("#### Step 2: Context Injected to LLM")
                        st.markdown("The retrieved patient records are formatted and sent to GPT-4:")
                        
                        # Show truncated context
                        context_preview = msg.get("context_text", "")[:1500]
                        if len(msg.get("context_text", "")) > 1500:
                            context_preview += "\n\n... (truncated)"
                        
                        st.code(context_preview, language=None)
                        
                        st.markdown("---")
                        st.markdown("#### RAG Flow Breakdown")
                        st.markdown("""
                        ```
                        1. USER QUESTION
                           "What medications are common for diabetic patients?"
                                    │
                                    ▼
                        2. EMBED QUESTION (OpenAI)
                           text-embedding-3-small → 1536-dim vector
                                    │
                                    ▼
                        3. VECTOR SEARCH (Couchbase)
                           APPROX_VECTOR_DISTANCE finds top 8 similar patients
                           Uses Composite Vector Index for fast retrieval
                                    │
                                    ▼
                        4. FORMAT CONTEXT
                           Patient records → structured text for LLM
                                    │
                                    ▼
                        5. LLM COMPLETION (OpenAI GPT-4)
                           System prompt + patient context + user question
                           → Natural language answer with citations
                        ```
                        """)
                
                # Show sources
                if msg.get("sources"):
                    with st.expander(f"View {len(msg['sources'])} source patients", expanded=False):
                        for i, p in enumerate(msg["sources"], 1):
                            st.markdown(f"""
                            <div class="source-card">
                                <strong>Patient {i}:</strong> {p.get('condition', 'N/A')} | 
                                {p.get('age_group', 'N/A')} {p.get('gender', 'N/A')} | 
                                {p.get('medication', 'N/A')} | 
                                ${p.get('amount', 0):,.0f}
                            </div>
                            """, unsafe_allow_html=True)
        
        # Clear chat button
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.copilot_sources = []
            st.rerun()
    
    else:
        st.markdown("""
        ---
        ### How it works
        
        1. **You ask a question** about patient data, demographics, treatments, or costs
        2. **Vector search retrieves** the most relevant patient records from the database
        3. **GPT-4 analyzes** the retrieved patients and generates insights
        4. **Sources are cited** so you can verify the analysis
        
        This is **Retrieval Augmented Generation (RAG)** - combining your enterprise data with AI reasoning.
        """)

def main():
    cluster = get_cluster()
    filters = load_filter_options()
    
    # Header with refresh button
    header_col, refresh_col = st.columns([6, 1])
    
    with header_col:
        st.markdown("""
        <div class="app-header">
            <h1 class="app-title">Healthcare AI Platform</h1>
            <p class="app-subtitle">Semantic search and AI-powered insights on patient data</p>
        </div>
        """, unsafe_allow_html=True)
    
    with refresh_col:
        st.markdown("<div style='padding-top: 2rem;'>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="refresh_data", help="Clear cache and reload data from database"):
            st.cache_data.clear()
            st.session_state.results = None
            st.session_state.searched = False
            st.session_state.executed_query = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Tabs using shadcn
    selected_tab = ui.tabs(
        options=['Patient Search', 'AI Copilot'],
        default_value='Patient Search',
        key="main_tabs"
    )
    
    st.markdown("")
    
    if selected_tab == 'Patient Search':
        render_search_tab(cluster, filters)
    else:
        render_copilot_tab(cluster)

if __name__ == "__main__":
    main()
