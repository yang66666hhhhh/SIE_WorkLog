import streamlit as st

from utils.natural_language_query import NaturalLanguageQuery


def render_natural_language_query(df, key_prefix="nlq"):
    """在数据页渲染轻量自然语言查询面板。"""
    query_engine = NaturalLanguageQuery(df)
    suggestions = query_engine.suggestions()
    input_key = f"{key_prefix}_input"
    selected_key = f"{key_prefix}_selected"

    selected = st.session_state.pop(selected_key, None)
    if selected:
        st.session_state[input_key] = selected

    st.markdown("**自然语言查询**")
    st.caption("可输入类似“最近7天调试任务”“VCP1问题有哪些”“工时最高的设备”。")
    query = st.text_input(
        "查询内容",
        placeholder=suggestions[0],
        key=input_key,
        label_visibility="collapsed",
    )

    cols = st.columns(len(suggestions[:3]))
    for idx, suggestion in enumerate(suggestions[:3]):
        if cols[idx].button(suggestion, key=f"{key_prefix}_suggest_{idx}", width='stretch'):
            st.session_state[selected_key] = suggestion
            st.rerun()

    if not query:
        return

    result, summary = query_engine.query(query)
    st.caption(summary)
    if result.empty:
        st.info("没有匹配结果")
    else:
        st.dataframe(result.head(100), width='stretch', hide_index=True)
