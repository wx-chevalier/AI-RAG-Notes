import streamlit as st
import os
import time
from rag_engine import IndustrialRAG
from supabase_client import IndustrialAuth, TelemetryLogger

# --- Page Config ---
st.set_page_config(
    page_title="工业售后 Copilot (Pro)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    /* Card Style for Sources */
    .source-card {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid #007bff;
        font-size: 0.9em;
    }
    /* Login Form Centering */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialization ---

@st.cache_resource
def get_engine():
    return IndustrialRAG()

@st.cache_resource
def get_auth():
    return IndustrialAuth()

@st.cache_resource
def get_logger():
    return TelemetryLogger()

engine = get_engine()
auth = get_auth()
logger = get_logger()

# --- Session State Management ---
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "sources_cache" not in st.session_state:
    st.session_state.sources_cache = []

# --- Authentication Logic ---

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.header("🔐 工业知识库登录")
        st.info("请使用管理员分发的账号登录（初始密码：Welcome123）")
        
        with st.form("login_form"):
            email = st.text_input("邮箱", placeholder="your_name@company.com")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录系统", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("请输入邮箱和密码")
                else:
                    with st.spinner("正在验证身份..."):
                        user = auth.sign_in(email, password)
                        if user:
                            st.session_state.user = user
                            st.success("登录成功！跳转中...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("登录失败，请检查账号或密码")

# --- Main App Logic ---

def main_app():
    user = st.session_state.user
    user_id = user.id
    
    # Init Session if needed
    if not st.session_state.session_id:
        st.session_state.session_id = logger.create_session(user_id)
        
    # --- Sidebar: User Profile & Stats ---
    with st.sidebar:
        st.title("👤 个人中心")
        
        # Load Stats (Async fetch effectively)
        stats = auth.get_profile_stats(user_id)
        profile_stats = stats.get('stats', {})
        display_name = stats.get('display_name', user.email.split('@')[0])
        
        st.markdown(f"**欢迎回来, {display_name}**")
        st.caption(f"ID: {user.email}")
        
        # Stats Dashboard
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("总提问", profile_stats.get('total_queries', 0))
        col_s2.metric("贡献反馈", profile_stats.get('total_feedback_given', 0))
        
        st.divider()
        
        # Tools
        k_slider = st.slider("检索深度 (Top-K)", 1, 10, 3)
        
        with st.expander("🔒 修改密码"):
            new_pwd = st.text_input("新密码", type="password", key="new_pwd_input")
            if st.button("更新密码"):
                success, msg = auth.update_password(new_pwd)
                if success:
                    st.success("密码修改成功！")
                else:
                    st.error(f"失败: {msg}")
                    
        if st.button("退出登录", type="primary"):
            st.session_state.user = None
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

    # --- Chat Interface ---
    st.subheader("🤖 工业软件智能售后助手")
    
    # Render History
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
            
            # Additional UI for Assistant Messages
            if msg["role"] == "assistant":
                # 1. Sources
                if msg.get("sources"):
                     with st.expander(f"📚 参考来源 ({len(msg['sources'])})"):
                        for i, src in enumerate(msg['sources']):
                            c1, c2 = st.columns([0.85, 0.15])
                            c1.text(f"{i+1}. {src['title']}")
                            if c2.button("📂", key=f"hist_open_{idx}_{i}", help="打开本地文件"):
                                engine.open_local_file(src['path'])
                
                # 2. Feedback UI (Standalone Row)
                msg_id = msg.get("msg_id")
                if msg_id:
                    st.divider() # Visual separation
                    
                    # State Management Keys
                    fb_key_base = f"fb_{idx}"
                    show_comment_key = f"{fb_key_base}_comment_open"
                    
                    if show_comment_key not in st.session_state:
                        st.session_state[show_comment_key] = False
                    
                    # Layout: Text + Buttons
                    f_col1, f_col2, f_col3 = st.columns([0.3, 0.1, 0.6])
                    
                    with f_col1:
                        st.caption("此回答对您有帮助吗？")
                        
                    with f_col2:
                         # Use columns for compact buttons
                         b1, b2 = st.columns(2)
                         with b1:
                            if st.button("👍", key=f"{fb_key_base}_like"):
                                logger.log_feedback(msg_id, user_id, 1, "Helpful")
                                st.toast("✅ 已反馈：有帮助")
                         with b2:
                            if st.button("👎", key=f"{fb_key_base}_dislike"):
                                st.session_state[show_comment_key] = True # Open form
                                st.rerun()

                    # 3. Comment Form (Conditional)
                    if st.session_state[show_comment_key]:
                        with st.container(border=True):
                            st.text("请告知需要改进的地方：")
                            with st.form(key=f"{fb_key_base}_form"):
                                comment = st.text_area("反馈详情", height=100, label_visibility="collapsed", placeholder="例如：引用文档过时，步骤缺失...")
                                
                                s_col1, s_col2 = st.columns([0.2, 0.8])
                                with s_col1:
                                    if st.form_submit_button("提交反馈", type="primary"):
                                        logger.log_feedback(msg_id, user_id, -1, comment)
                                        st.toast("🙏 感谢您的纠错！")
                                        st.session_state[show_comment_key] = False
                                        st.rerun()
                                with s_col2:
                                    if st.form_submit_button("取消"):
                                        st.session_state[show_comment_key] = False
                                        st.rerun()

    # Input Area
    if prompt := st.chat_input("请输入技术问题..."):
        # 1. Show User Input
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # 2. Generate Answer
        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("正在检索知识库..."):
                
                # Retrieve History for Rewrite
                history = [m for m in st.session_state.messages if m['role'] != 'system'][:-1] # Exclude current
                rewritten_query = engine.rewrite_query(history, prompt)
                
                if rewritten_query != prompt:
                    st.caption(f"🔄 优化检索词: {rewritten_query}")

                # Retrieve
                docs = engine.retrieve(rewritten_query, top_k=k_slider)
                
                # Generate Answer & Log Telemetry
                # Pass user metrics for logging
                # Unpack tuple: response, msg_id
                response, msg_id = engine.generate_answer(
                    rewritten_query, 
                    docs, 
                    user_id=user_id, 
                    session_id=st.session_state.session_id,
                    rewritten_query=rewritten_query
                )
                
                # Image processing
                final_response = engine.process_markdown_images(response)
                
                placeholder.markdown(final_response, unsafe_allow_html=True)
                
                # Extract sources for UI
                sources_data = [{
                    "title": d.metadata.get('filename', 'Unknown'),
                    "path": d.metadata.get('clean_docx_path', '')
                } for d in docs]
                
                # Show Sources
                if sources_data:
                    with st.expander(f"📚 参考来源 ({len(sources_data)})", expanded=True):
                         for i, src in enumerate(sources_data):
                            c1, c2 = st.columns([0.85, 0.15])
                            c1.text(f"{i+1}. {src['title']}")
                            if c2.button("📂", key=f"fresh_open_{i}", help="打开本地文件"):
                                engine.open_local_file(src['path'])

                # Append to history with Msg ID
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_response,
                    "sources": sources_data,
                    "msg_id": msg_id
                })
                
                # Force rerun to render the new message via the main loop, adding Feedback Buttons
                st.rerun()
                
                # --- Immediate Feedback UI (For the just-generated message) ---
                # This ensures buttons appear instantly without needing st.rerun()
                # The feedback UI for the *current* message is now handled by the loop above
                # after st.session_state.messages is updated and st.rerun() is called.
                # This block is effectively removed as the new logic covers both historical and fresh messages.

# --- Routing ---
if st.session_state.user:
    main_app()
else:
    login_page()
