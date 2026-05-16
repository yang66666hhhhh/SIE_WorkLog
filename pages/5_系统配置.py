import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
from utils.config import Config

st.set_page_config(page_title="System Config", layout="wide", page_icon="⚙️")

config = Config()

if "config_msg" not in st.session_state:
    st.session_state.config_msg = None

if st.session_state.config_msg:
    st.session_state.config_msg[0](st.session_state.config_msg[1])
    st.session_state.config_msg = None

with st.sidebar:
    st.header("⚙️ 系统")
    st.caption("主题: 右上角 ⋮ 菜单")

    with st.expander("💾 配置备份", expanded=True):
        equipment = config.load_equipment()
        task_rules = config.load_task_rules()
        backup_data = {
            "equipment": equipment,
            "task_rules": task_rules,
            "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)

        st.download_button(
            "📥 导出",
            backup_json,
            f"config_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

        uploaded = st.file_uploader("📤 导入", type=["json"], key="restore_config")
        if uploaded:
            try:
                restore_data = json.load(uploaded)
                if "equipment" in restore_data and "task_rules" in restore_data:
                    config.save_equipment(restore_data["equipment"])
                    config.save_task_rules(restore_data["task_rules"])
                    st.success("✅ 成功")
                    st.rerun()
                else:
                    st.error("❌ 格式错误")
            except Exception as e:
                st.error(f"❌ 失败: {e}")

# =====================
# 项目名称配置
# =====================
st.header("📌 项目配置")

project_name = config.load_project_name()
new_project_name = st.text_input("项目名称", value=project_name, key="project_name_input")
if st.button("💾 保存项目名称", key="btn_project_save"):
    if new_project_name.strip():
        config.save_project_name(new_project_name.strip())
        st.session_state.config_msg = (st.success, f"✅ 项目名称已更新")
        st.rerun()
    else:
        st.warning("项目名称不能为空")

st.markdown("---")

# =====================
# AI 配置
# =====================
st.header("🤖 AI 分析配置")

ai_config = config.load_ai_config()

col1, col2 = st.columns([3, 1])
with col1:
    provider = st.selectbox(
        "📡 提供商",
        ["openai", "azure", "自定义"],
        index=["openai", "azure", "自定义"].index(ai_config.get("provider", "openai")) if ai_config.get("provider") in ["openai", "azure", "自定义"] else 0,
        key="ai_provider"
    )

with col2:
    enabled = st.toggle("✅ 启用", value=ai_config.get("enabled", False), key="ai_enabled")

api_key = st.text_input(
    "🔑 API Key",
    value=ai_config.get("api_key", ""),
    type="password",
    placeholder="sk-...",
    key="ai_api_key"
)

if provider == "openai":
    base_url = st.text_input(
        "🌐 API Base URL",
        value=ai_config.get("base_url", "https://api.openai.com/v1"),
        placeholder="https://api.openai.com/v1",
        key="ai_base_url"
    )
    model = st.text_input(
        "🤖 模型",
        value=ai_config.get("model", "gpt-3.5-turbo"),
        key="ai_model"
    )
elif provider == "azure":
    base_url = st.text_input(
        "🌐 Azure Endpoint",
        value=ai_config.get("base_url", ""),
        placeholder="https://xxx.openai.azure.com",
        key="ai_base_url"
    )
    model = st.text_input(
        "📦 Deployment Name",
        value=ai_config.get("model", ""),
        key="ai_model"
    )
else:
    base_url = st.text_input("🌐 API Base URL", value=ai_config.get("base_url", ""), key="ai_base_url")
    model = st.text_input("🤖 模型名称", value=ai_config.get("model", ""), key="ai_model")

if st.button("💾 保存配置", type="primary", key="btn_ai_save"):
    new_config = {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "enabled": enabled
    }
    config.save_ai_config(new_config)
    st.session_state.config_msg = (st.success, "✅ AI 配置已保存")
    st.rerun()

st.markdown("---")

# =====================
# 设备线体配置
# =====================
st.subheader("🏢 设备线体")

equipment = config.load_equipment()

c1, c2, c3 = st.columns(3)
c1.metric("📊 线体", f"{len(equipment)} 个")
c2.metric("🔑 关键词", f"{sum(len(v) for v in equipment.values())} 个")
c3.metric("📈 平均", f"{sum(len(v) for v in equipment.values()) / len(equipment):.1f} 个" if equipment else "0 个")

st.dataframe(
    pd.DataFrame([{"线体": k, "关键词": ", ".join(v), "数量": len(v)} for k, v in equipment.items()]),
    use_container_width=True, hide_index=True,
)

tab_eq1, tab_eq2, tab_eq3 = st.tabs(["➕ 新增", "✏️ 编辑", "🗑️ 删除"])

with tab_eq1:
    st.markdown("**添加新线体**")
    eq_name = st.text_input("线体名称", placeholder="例如：LDD棕化线（HDI）", label_visibility="collapsed")
    eq_kw = st.text_input("关键词（逗号分隔）", placeholder="例如：ldd棕化线（hdi）, hdi", label_visibility="collapsed")
    if st.button("✅ 添加", type="primary", use_container_width=True, key="btn_eq_add"):
        if eq_name and eq_kw:
            equipment[eq_name] = [k.strip() for k in eq_kw.split(",") if k.strip()]
            config.save_equipment(equipment)
            st.session_state.config_msg = (st.success, f"已添加：{eq_name}")
            st.rerun()
        else:
            st.session_state.config_msg = (st.warning, "请填写完整")
            st.rerun()

with tab_eq2:
    st.markdown("**编辑关键词**")
    eq_keys = list(equipment.keys())
    edit_name = st.selectbox("选择线体", eq_keys, key="eq_edit_select")

    if "eq_current_kw" not in st.session_state:
        st.session_state.eq_current_kw = ", ".join(equipment[edit_name]) if edit_name else ""

    if edit_name:
        new_kw = st.text_input("关键词", value=st.session_state.eq_current_kw, key="eq_kw_edit")
        if st.button("💾 保存", type="primary", use_container_width=True, key="btn_eq_save"):
            if new_kw.strip():
                equipment[edit_name] = [k.strip() for k in new_kw.split(",") if k.strip()]
                config.save_equipment(equipment)
                st.session_state.eq_current_kw = new_kw
                st.session_state.config_msg = (st.success, f"已更新：{edit_name}")
                st.rerun()
            else:
                st.session_state.config_msg = (st.warning, "关键词不能为空")
                st.rerun()

with tab_eq3:
    st.markdown("**删除线体**")
    del_name = st.selectbox("选择线体", list(equipment.keys()), key="eq_del_select")
    if del_name:
        st.warning(f"将删除：**{del_name}**")
        if st.button("🗑️ 确认删除", type="primary", use_container_width=True, key="btn_eq_del"):
            equipment.pop(del_name, None)
            config.save_equipment(equipment)
            st.session_state.config_msg = (st.success, f"已删除：{del_name}")
            st.rerun()

st.markdown("---")

# =====================
# 任务类型配置
# =====================
st.subheader("📋 任务类型")

task_rules = config.load_task_rules()

c4, c5 = st.columns(2)
c4.metric("📊 类型", f"{len(task_rules)} 个")
c5.metric("📝 规则", f"{sum(len(v) for v in task_rules.values())} 字符")

st.dataframe(
    pd.DataFrame([{"类型": k, "匹配规则": v} for k, v in task_rules.items()]),
    use_container_width=True, hide_index=True,
)

tab_tr1, tab_tr2, tab_tr3 = st.tabs(["➕ 新增", "✏️ 编辑", "🗑️ 删除"])

with tab_tr1:
    st.markdown("**添加新类型**")
    tr_name = st.text_input("类型名称", placeholder="例如：部署", label_visibility="collapsed")
    tr_pattern = st.text_input("匹配规则（正则，用|分隔）", placeholder="例如：部署|上线|发布", label_visibility="collapsed")
    if st.button("✅ 添加", type="primary", use_container_width=True, key="btn_tr_add"):
        if tr_name and tr_pattern:
            is_valid, err_msg = config.validate_regex(tr_pattern)
            if not is_valid:
                st.error(f"❌ 正则表达式无效: {err_msg}")
            else:
                task_rules[tr_name] = tr_pattern
                config.save_task_rules(task_rules)
                st.session_state.config_msg = (st.success, f"已添加：{tr_name}")
                st.rerun()
        else:
            st.session_state.config_msg = (st.warning, "请填写完整")
            st.rerun()

with tab_tr2:
    st.markdown("**编辑规则**")
    tr_keys = list(task_rules.keys())
    tr_edit_name = st.selectbox("选择类型", tr_keys, key="tr_edit_select")

    if "tr_current_pat" not in st.session_state:
        st.session_state.tr_current_pat = task_rules[tr_edit_name] if tr_edit_name else ""

    if tr_edit_name:
        new_pattern = st.text_input("匹配规则", value=st.session_state.tr_current_pat, key="tr_pattern_edit")
        if st.button("💾 保存", type="primary", use_container_width=True, key="btn_tr_save"):
            if new_pattern.strip():
                is_valid, err_msg = config.validate_regex(new_pattern)
                if not is_valid:
                    st.error(f"❌ 正则表达式无效: {err_msg}")
                else:
                    task_rules[tr_edit_name] = new_pattern
                    config.save_task_rules(task_rules)
                    st.session_state.tr_current_pat = new_pattern
                    st.session_state.config_msg = (st.success, f"已更新：{tr_edit_name}")
                    st.rerun()
            else:
                st.session_state.config_msg = (st.warning, "规则不能为空")
                st.rerun()

with tab_tr3:
    st.markdown("**删除类型**")
    tr_del_name = st.selectbox("选择类型", list(task_rules.keys()), key="tr_del_select")
    if tr_del_name:
        st.warning(f"将删除：**{tr_del_name}**")
        if st.button("🗑️ 确认删除", type="primary", use_container_width=True, key="btn_tr_del"):
            task_rules.pop(tr_del_name, None)
            config.save_task_rules(task_rules)
            st.session_state.config_msg = (st.success, f"已删除：{tr_del_name}")
            st.rerun()
