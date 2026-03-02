import streamlit as st
from openai import OpenAI

# -------------------------- 【讯飞GLM大模型配置】 --------------------------
# 部署时请替换为 st.secrets["XUNFEI_API_KEY"]
client = OpenAI(
    api_key =st.secrets["XUNFEI_API_KEY"],
    base_url ="https://maas-api.cn-huabei-1.xf-yun.com/v2"
)
# ----------------------------------------------------------------------

# ✅ 页面配置
st.set_page_config(
    page_title="大模型应用开发求职助手",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ 大模型应用开发求职助手")
st.caption("专注应用落地 | 一键搞定简历优化与个性化面试题")

# -------------------------- 关键修复：初始化+清空逻辑 --------------------------
# 1. 初始化会话状态（确保所有状态都有默认值）
def init_session_state():
    default_states = {
        "resume_content": "",
        "optimized_resume": "",
        "interview_questions": "",
        "question_source": "",
        "clear_trigger": False  # 新增清空触发标记
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

# 2. 清空所有内容的函数（修复核心：强制刷新+重置所有状态）
def clear_all_content():
    """清空所有内容（兼容旧版 Streamlit）"""
    # 重置所有会话状态为初始值
    st.session_state.resume_content = ""
    st.session_state.optimized_resume = ""
    st.session_state.interview_questions = ""
    st.session_state.question_source = ""
    st.session_state.clear_trigger = False
    # 移除 st.experimental_rerun()，依靠状态重置后页面自动重渲染

# 初始化状态
init_session_state()

# -------------------------- 核心提示词 --------------------------
# 1. 简历优化提示词（纯应用开发）
def get_app_dev_resume_prompt(resume_text):
    prompt = f"""
    你是资深的「大模型应用开发」技术面试官，专注招聘**应用型**开发人才，而非算法研究员。
    请严格按照以下**应用开发导向**规则优化简历，**完全回避**模型训练、微调、算法原理等需要高学历的内容。

    ### 核心优化规则（纯应用开发专属）
    1. **突出工程化落地能力（核心）**：
       - 重点放大：大模型API调用（如讯飞/OpenAI）、Prompt工程（提示词设计/优化）、Function Calling（工具调用）；
       - 强化：业务流程对接、数据处理、前端交互、部署上线等生产级应用开发细节；
    2. **突出开发框架与工具**：
       - 必须细化：使用的框架（LangChain）、后端（FastAPI/Flask）、前端（Streamlit）、部署工具（Docker）；
    3. **量化业务价值**：
       - 将“做了一个聊天机器人”改为“开发智能对话系统，实现上下文记忆，接口响应速度≤500ms”；
    4. **弱化/删除无关内容**：
       - **完全删除**：LeetCode刷题、机器学习算法原理、模型微调/训练等内容；
       - 精简：非技术类校园经历；
    5. **格式要求**：
       - 语言聚焦“开发、集成、部署、交付”，保持简历结构，控制在1200字内。

    ### 需要优化的原始简历
    {resume_text}

    ### 输出要求
    直接输出优化后的完整简历，无需额外解释。
    """
    return prompt

# 2. 面试题生成通用函数（支持传入不同简历）
def get_interview_prompt(resume_text, source_desc):
    prompt = f"""
    你是资深的大模型应用开发面试官，现在要根据候选人的{source_desc}简历，生成**100%贴合内容**的个性化面试题。
    所有题目必须从这份简历里找细节，**禁止出简历里没有提到的技术或项目**，不考任何算法原理。

    ### 面试题设计规则
    1. **题目必须来自简历**：
       - 针对简历里的**每一个项目**，追问技术选型、遇到的问题、优化方案；
       - 针对简历里的**每一项技能**，考察实际使用场景和细节；
    2. **题型分类**：
       - **项目深挖题（4道）**：针对项目的实现细节和问题排查；
       - **技能实操题（3道）**：针对工具使用的具体场景；
       - **场景应用题（3道）**：结合项目业务的拓展需求；
    3. **难度要求**：
       - 贴合校招/应用开发岗，只考**做过的事**；
    4. **输出格式**：
       - 按「项目深挖题」「技能实操题」「场景应用题」分类；
       - 每题标注难度（简单/中等），语言像真实面试官提问。

    ### 候选人简历
    {resume_text}

    ### 输出要求
    直接输出面试题，无需额外解释。
    """
    return prompt

# -------------------------- 核心业务逻辑 --------------------------
def only_optimize():
    """仅优化简历"""
    # 增加非空校验（修复清空后误触问题）
    if not st.session_state.resume_content.strip():
        st.warning("⚠️ 请先粘贴简历内容！")
        return
    with st.spinner("⚙️ 正在优化简历..."):
        try:
            prompt = get_app_dev_resume_prompt(st.session_state.resume_content)
            response = client.chat.completions.create(
                model="xopglmv47flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=2800
            )
            st.session_state.optimized_resume = response.choices[0].message.content
            st.session_state.interview_questions = ""
            st.session_state.question_source = ""
            st.success("✅ 简历优化完成！")
        except Exception as e:
            st.error(f"❌ 优化失败：{str(e)}")

def only_question_origin():
    """仅对原始简历出面试题"""
    if not st.session_state.resume_content.strip():
        st.warning("⚠️ 请先粘贴简历内容！")
        return
    with st.spinner("🧠 基于原始简历生成题目..."):
        try:
            prompt = get_interview_prompt(st.session_state.resume_content, "原始")
            response = client.chat.completions.create(
                model="xopglmv47flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3500
            )
            st.session_state.interview_questions = response.choices[0].message.content
            st.session_state.question_source = "原始"
            st.success("✅ 基于原始简历的面试题生成完成！")
        except Exception as e:
            st.error(f"❌ 生成失败：{str(e)}")

def optimize_and_question():
    """优化简历 + 对优化后的简历出面试题"""
    if not st.session_state.resume_content.strip():
        st.warning("⚠️ 请先粘贴简历内容！")
        return
    # 第一步：优化简历
    with st.spinner("⚙️ 先优化简历..."):
        try:
            prompt = get_app_dev_resume_prompt(st.session_state.resume_content)
            response = client.chat.completions.create(
                model="xopglmv47flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=2800
            )
            st.session_state.optimized_resume = response.choices[0].message.content
        except Exception as e:
            st.error(f"❌ 简历优化失败：{str(e)}")
            return
    # 第二步：基于优化后的简历出题
    with st.spinner("🧠 再生成面试题..."):
        try:
            prompt = get_interview_prompt(st.session_state.optimized_resume, "优化后")
            response = client.chat.completions.create(
                model="xopglmv47flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3500
            )
            st.session_state.interview_questions = response.choices[0].message.content
            st.session_state.question_source = "优化后"
            st.success("✅ 简历优化+面试题生成双完成！")
        except Exception as e:
            st.error(f"❌ 面试题生成失败：{str(e)}")

# -------------------------- 界面布局（修复清空后显示问题） --------------------------
# 1. 简历输入区域（顶部固定）
st.subheader("📝 原始简历输入")
st.info("💡 提示：请填写API调用、Streamlit开发、项目部署经历，系统会自动弱化算法相关内容。")

# 关键：输入框值直接绑定会话状态，清空后立即同步
resume_input = st.text_area(
    label="简历内容",
    height=400,
    max_chars=3500,
    placeholder="请粘贴你的原始简历...",
    value=st.session_state.resume_content,  # 绑定状态，清空后立即为空
    label_visibility="collapsed"
)
# 实时更新会话状态（避免输入框内容不同步）
st.session_state.resume_content = resume_input

# 2. 核心功能按钮区（精简文字，三按钮并列）
st.subheader("⚡ 功能选择")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("仅优化简历", type="primary", on_click=only_optimize, use_container_width=True)
with col2:
    st.button("仅原始简历出题", on_click=only_question_origin, use_container_width=True)
with col3:
    st.button("优化+优化后出题", on_click=optimize_and_question, use_container_width=True)

# 清空按钮（无刷新函数，兼容所有版本）
if st.button("🗑️ 单击清空结果，再次单机清空结果", type="secondary"):
    clear_all_content()

# 3. 结果展示区域（分两栏，清空后自动隐藏内容）
st.subheader("📊 结果展示")
tab1, tab2 = st.tabs(["优化后简历", "专属面试题"])

with tab1:
    if st.session_state.optimized_resume:
        st.text_area(
            label="优化结果（可直接复制）",
            height=450,
            value=st.session_state.optimized_resume,
            disabled=False,
            label_visibility="collapsed"
        )
    else:
        st.info("ℹ️ 点击「仅优化简历」或「优化+优化后出题」，结果将显示在这里。")

with tab2:
    if st.session_state.interview_questions:
        st.markdown(f"### 🎯 基于{st.session_state.question_source}简历的面试题")
        st.markdown(st.session_state.interview_questions)
    else:
        st.info("ℹ️ 点击对应功能按钮，面试题将显示在这里。")

# 侧边栏
with st.sidebar:
    st.markdown("### 📌 功能说明")
    st.markdown("1. **仅优化简历**：专注应用开发方向，弱化算法内容")
    st.markdown("2. **仅原始简历出题**：针对未优化的简历生成问题")
    st.markdown("3. **优化+优化后出题**：先优化再针对优化版生成问题")
    st.divider()
    st.markdown("### ⚙️ 技术栈")
    st.markdown("- 前端：Streamlit（单页自适应）")
    st.markdown("- 大模型：讯飞GLM API")