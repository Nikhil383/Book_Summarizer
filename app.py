import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage
from schema import BookSummary
import json

# Load environment variables
load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="Book Summarizer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling ---
st.markdown("""
<style>
    /* Import Premium Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    /* Global Reset */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Gradient Background */
    .stApp {
        background: radial-gradient(circle at top left, #1e1b4b, #0f172a, #020617);
        background-attachment: fixed;
    }

    /* Typography */
    h1 {
        background: linear-gradient(120deg, #60a5fa 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        font-size: 3rem !important;
    }
    
    h2, h3, h4 {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }

    /* Input Area - Glassmorphism */
    .stTextArea textarea {
        background-color: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 20px rgba(129, 140, 248, 0.2);
        background-color: rgba(30, 41, 59, 0.6) !important;
    }

    /* Primary Button */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }

    /* Custom Result Card */
    .result-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-top: 1rem;
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.3);
    }
    
    .result-title {
        color: #38bdf8;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .result-text {
        color: #e2e8f0;
        line-height: 1.6;
        white-space: pre-wrap;
    }

    /* Sidebar/Divider Styling */
    hr {
        border-color: rgba(148, 163, 184, 0.2);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
</style>
""", unsafe_allow_html=True)

# --- Logic Setup ---
SYSTEM_PROMPT = f"""
You are a professional book summarizer.

1. Read the input and extract keypoints.
2. Condense ideas in plain English.
3. Highlight themes, key events, or arguments.

Return JSON only in this format:

{json.dumps(BookSummary.model_json_schema(), indent=2).replace("{", "{{").replace("}", "}}")}
"""

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.4)
parser = PydanticOutputParser(pydantic_object=BookSummary)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{chat_history}"),
    ("human", "{query}"),
    ("placeholder", "{agent_scratchpad}")
]).partial(format_instructions=parser.get_format_instructions())

agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=[])
executor = AgentExecutor(agent=agent, tools=[], verbose=True)

# --- Layout Implementation ---
st.title("📚 Book Summarizer")
st.markdown("""
<p style='font-size: 1.1rem; color: #94a3b8; margin-bottom: 2rem;'>
    Transform long-form content into clear, structured summaries instantly using advanced AI.
</p>
""", unsafe_allow_html=True)

# Main Two-Column Layout
col1, col2 = st.columns([5, 4], gap="large")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_summary" not in st.session_state:
    st.session_state.last_summary = None

with col1:
    st.markdown("### 📥 Source Text")
    with st.form("book_summary_form", clear_on_submit=False):
        user_text = st.text_area(
            "Paste content", 
            height=450, 
            label_visibility="collapsed",
            placeholder="Paste your book text, article, or notes here..."
        )
        submit_btn = st.form_submit_button("✨ Generate Summary")

with col2:
    st.markdown("### 🧠 Analysis Result")
    
    if submit_btn and user_text.strip():
        # Add to history
        st.session_state.chat_history.append(HumanMessage(content=user_text))
        
        with st.spinner("Processing text & extracting insights..."):
            try:
                response = executor.invoke({
                    "query": user_text,
                    "chat_history": st.session_state.chat_history
                })
                
                result = parser.parse(response["output"])
                st.session_state.chat_history.append(AIMessage(content=result.summary))
                st.session_state.last_summary = result
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display Result
    if st.session_state.last_summary:
        res = st.session_state.last_summary
        
        # Custom HTML Card
        st.markdown(f"""
        <div class="result-card">
            <div class="result-title">📖 {res.title}</div>
            <div class="result-text">{res.summary}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Download Button
        json_output = {"title": res.title, "summary": res.summary}
        st.download_button(
            label="📥 Download JSON Report",
            data=json.dumps(json_output, indent=4),
            file_name=f"{res.title.replace(' ', '_')}_summary.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.info("👈 Enter text on the left to generate your first summary.")
        st.markdown(
            """
            <div style="text-align: center; opacity: 0.3; margin-top: 50px;">
                <h1 style="font-size: 5rem; margin: 0;">📚</h1>
                <p>Ready to summarize</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

# Optional History Section
if st.session_state.chat_history:
    st.markdown("---")
    with st.expander("� Conversation History"):
        for msg in st.session_state.chat_history:
            if isinstance(msg, HumanMessage):
                st.markdown(f"**Source:** *{msg.content[:80]}...*")
            elif isinstance(msg, AIMessage):
                st.markdown(f"**Summary:** {msg.content[:100]}...")
