import streamlit as st
import pandas as pd
import json
import re
from html import escape
from datetime import datetime
from utils.config import Config
from utils import report_db
from utils.styles import inject_global_css, render_section_title, render_top_nav
from utils.test_report_format import get_available_version_options, load_active_report_format
from utils.report_form import generate_report_content

st.set_page_config(page_title="System Config", layout="wide", page_icon="⚙️", menu_items=None)
inject_global_css()
render_top_nav("系统配置")

config = Config()


def split_keywords(text):
    return [item.strip() for item in re.split(r"[,，]", text or "") if item.strip()]


def render_config_overview(project_name, equipment, task_rules, ai_config):
    enabled_text = "已启用" if ai_config.get("enabled") else "未启用"
    key_text = "已配置 Key" if ai_config.get("api_key") else "未配置 Key"
    cards = [
        ("项目", project_name, "当前工作记录归属项目"),
        ("设备线体", f"{len(equipment)} 个", f"{sum(len(v) for v in equipment.values())} 个关键词"),
        ("任务类型", f"{len(task_rules)} 个", f"{sum(len(v) for v in task_rules.values())} 字符规则"),
        ("AI 分析", enabled_text, f"{ai_config.get('provider', 'openai')} · {key_text}"),
    ]
    html = "".join(
        '<div class="config-overview-card">'
        f'<div class="config-overview-label">{escape(label)}</div>'
        f'<div class="config-overview-value">{escape(str(value))}</div>'
        f'<div class="config-overview-note">{escape(note)}</div>'
        '</div>'
        for label, value, note in cards
    )
    st.markdown(f'<div class="config-overview">{html}</div>', unsafe_allow_html=True)


def render_keyword_tags(keywords):
    if not keywords:
        st.caption("暂无关键词")
        return
    html = "".join(f'<span class="config-tag">{escape(str(item))}</span>' for item in keywords)
    st.markdown(f'<div class="config-tag-list">{html}</div>', unsafe_allow_html=True)

if "config_msg" not in st.session_state:
    st.session_state.config_msg = None

if st.session_state.config_msg:
    msg_type, msg_text = st.session_state.config_msg
    st.toast(msg_text, icon="✅" if msg_type == st.success else "⚠️")
    st.session_state.config_msg = None

with st.expander("💾 配置备份", expanded=False):
    equipment = config.load_equipment()
    task_rules = config.load_task_rules()
    report_format = config.load_report_format_config()
    backup_data = {
        "equipment": equipment,
        "task_rules": task_rules,
        "report_format": report_format,
        "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)

    st.download_button(
        "📥 导出配置",
        backup_json,
        f"config_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        width='stretch'
    )

    uploaded = st.file_uploader("📤 导入配置", type=["json"], key="restore_config")
    if uploaded:
        try:
            restore_data = json.load(uploaded)
            if "equipment" in restore_data and "task_rules" in restore_data:
                config.save_equipment(restore_data["equipment"])
                config.save_task_rules(restore_data["task_rules"])
                if "report_format" in restore_data:
                    config.save_report_format_config(restore_data["report_format"])
                st.toast("✅ 配置已导入", icon="✅")
                st.rerun()
            else:
                st.error("❌ 格式错误：缺少 equipment 或 task_rules 字段")
        except Exception as e:
            st.error(f"❌ 导入失败: {e}")

# =====================
# 主区域：Tab 分区
# =====================
st.title("⚙️ 系统配置")

project_name = config.load_project_name()
equipment = config.load_equipment()
task_rules = config.load_task_rules()
ai_config = config.load_ai_config()

render_config_overview(project_name, equipment, task_rules, ai_config)

tab_proj, tab_format, tab_ai, tab_eq, tab_tr, tab_data = st.tabs(["📌 项目", "📝 报告格式", "🤖 AI 配置", "🏢 设备线体", "📋 任务类型", "💾 数据管理"])

# =====================
# 项目配置
# =====================
with tab_proj:
    render_section_title("📌", "项目配置")
    new_project_name = st.text_input("项目名称", value=project_name, key="project_name_input")
    if st.button("💾 保存项目名称", key="btn_project_save", type="primary"):
        if new_project_name.strip():
            config.save_project_name(new_project_name.strip())
            st.toast("✅ 项目名称已更新", icon="✅")
            st.rerun()
        else:
            st.warning("项目名称不能为空")

# =====================
# 报告格式配置
# =====================
with tab_format:
    render_section_title("📝", "测试报告格式配置")

    report_format_config = config.load_report_format_config()
    current_version = report_format_config.get("version", "v1")
    available_versions = get_available_version_options()
    parsed_cats = report_format_config.get("custom_categories", [])
    custom_labels_edit = {}

    col_fv1, col_fv2 = st.columns([1, 2])
    with col_fv1:
        selected_version = st.selectbox(
            "格式版本",
            options=available_versions,
            index=available_versions.index(current_version) if current_version in available_versions else 0,
            key="report_format_version"
        )

    preview_config = {
        "version": selected_version,
        "custom_categories": parsed_cats,
        "custom_field_labels": custom_labels_edit,
    }
    fmt = load_active_report_format(version=selected_version, custom_config=preview_config)
    with col_fv2:
        st.markdown(f"**当前版本：** `{fmt.get('version', 'v1')}`")
        st.markdown(f"**问题分类数：** {len(fmt.get('categories', []))}")
        st.markdown(f"**字段数：** {len(fmt.get('field_labels', {}))}")

    if selected_version == "custom":
        with st.expander("🔧 自定义分类", expanded=False):
            custom_cats = report_format_config.get("custom_categories", [])
            custom_cats_str = st.text_area(
                "自定义问题分类（每行一个）",
                value="\n".join(custom_cats) if custom_cats else "",
                height=150,
                key="custom_categories_input"
            )
            parsed_cats = [c.strip() for c in custom_cats_str.split("\n") if c.strip()]

            custom_labels = report_format_config.get("custom_field_labels", {})
            st.markdown("**自定义字段标签**")
            custom_labels_edit = {}
            for fkey, flabel in fmt.get("field_labels", {}).items():
                default_label = custom_labels.get(fkey, flabel)
                new_label = st.text_input(f"字段 {fkey}", value=default_label, key=f"custom_label_{fkey}")
                if new_label != flabel:
                    custom_labels_edit[fkey] = new_label

            preview_config = {
                "version": selected_version,
                "custom_categories": parsed_cats,
                "custom_field_labels": custom_labels_edit,
            }
            fmt = load_active_report_format(version=selected_version, custom_config=preview_config)

    preview_categories = fmt.get("categories", [])
    preview_problems = {cat: "示例问题 1\n示例问题 2" if i == 0 else "无" for i, cat in enumerate(preview_categories)}
    preview_content = generate_report_content(
        date_str="2026-05-19",
        lines=["VCP1", "VCP2"],
        time_periods=[{"start": "09:30", "end": "12:00"}, {"start": "14:30", "end": "18:00"}],
        work_order="M126041900006，共3528 PCS",
        today_plans=["垂直电镀VCP1自动化测试（放板机）"],
        actual_scenes=["自动化测试：VCP1（测试环境）"],
        processes=["叫料→AGV送料→安全交互→配方下发→TrackIn"],
        problems=preview_problems,
        todo_item="待确认现场网络稳定性",
        test_results=["放板流程已跑通"],
        completions=["自动化测试：已完成 ✅"],
        next_plan_scene="VCP1/VCP2线放板机全流程（测试环境）",
        next_plan_processes=["放板机：叫料→AGV送料→安全交互→配方下发"],
        coordination="需要IT协助处理网络白名单",
        format_version=selected_version,
        format_config=preview_config,
    )

    with st.expander("👁️ 格式预览", expanded=True):
        st.caption("下方展示当前所选格式版本生成出的测试报告文本。")
        st.text_area("预览内容", value=preview_content, height=420, disabled=True, label_visibility="collapsed")

    if st.button("💾 保存格式配置", type="primary", key="btn_format_save"):
        save_data = {"version": selected_version}
        if selected_version == "custom":
            save_data["custom_categories"] = parsed_cats
            save_data["custom_field_labels"] = custom_labels_edit
        else:
            save_data["custom_categories"] = []
            save_data["custom_field_labels"] = {}
        config.save_report_format_config(save_data)
        st.toast("✅ 报告格式配置已保存", icon="✅")
        st.rerun()

    st.info("💡 切换格式版本后，新建/编辑报告将使用对应版本的字段和分类规则。")

# =====================
# AI 配置
# =====================
with tab_ai:
    render_section_title("🤖", "AI 分析配置")
    st.info("AI 配置会影响数据分析页的智能总结；未启用时使用本地规则生成洞察。")

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
        "🔑 API Key", value=ai_config.get("api_key", ""),
        type="password", placeholder="sk-...", key="ai_api_key"
    )

    if provider == "openai":
        base_url = st.text_input("🌐 API Base URL", value=ai_config.get("base_url", "https://api.openai.com/v1"), placeholder="https://api.openai.com/v1", key="ai_base_url")
        model = st.text_input("🤖 模型", value=ai_config.get("model", "gpt-3.5-turbo"), key="ai_model")
    elif provider == "azure":
        base_url = st.text_input("🌐 Azure Endpoint", value=ai_config.get("base_url", ""), placeholder="https://xxx.openai.azure.com", key="ai_base_url")
        model = st.text_input("📦 Deployment Name", value=ai_config.get("model", ""), key="ai_model")
    else:
        base_url = st.text_input("🌐 API Base URL", value=ai_config.get("base_url", ""), key="ai_base_url")
        model = st.text_input("🤖 模型名称", value=ai_config.get("model", ""), key="ai_model")

    if enabled and not api_key.strip():
        st.warning("启用 AI 前请先填写 API Key")

    if st.button("💾 保存配置", type="primary", key="btn_ai_save"):
        if enabled and not api_key.strip():
            st.error("启用 AI 时 API Key 不能为空")
            st.stop()
        new_config = {"provider": provider, "api_key": api_key, "base_url": base_url, "model": model, "enabled": enabled}
        config.save_ai_config(new_config)
        st.toast("✅ AI 配置已保存", icon="✅")
        st.rerun()

# =====================
# 设备线体
# =====================
with tab_eq:
    render_section_title("🏢", "设备线体")

    c1, c2, c3 = st.columns(3)
    c1.metric("线体", f"{len(equipment)} 个")
    c2.metric("关键词", f"{sum(len(v) for v in equipment.values())} 个")
    c3.metric("平均", f"{sum(len(v) for v in equipment.values()) / len(equipment):.1f} 个" if equipment else "0 个")

    eq_search = st.text_input("🔍 搜索线体或关键词", placeholder="输入线体名、关键词过滤...", key="eq_search")
    equipment_rows = [{"线体": k, "关键词": ", ".join(v), "数量": len(v)} for k, v in equipment.items()]
    equipment_df = pd.DataFrame(equipment_rows)
    if eq_search and not equipment_df.empty:
        mask = equipment_df.astype(str).apply(lambda x: x.str.contains(eq_search, case=False, na=False)).any(axis=1)
        equipment_df = equipment_df[mask]
    st.caption(f"当前显示 {len(equipment_df)} / {len(equipment)} 个线体")

    st.dataframe(
        equipment_df,
        width='stretch', hide_index=True,
    )

    eq_tab1, eq_tab2, eq_tab3 = st.tabs(["➕ 新增", "✏️ 编辑", "🗑️ 删除"])

    with eq_tab1:
        st.markdown("**添加新线体**")
        eq_name = st.text_input("线体名称", placeholder="例如：LDD棕化线（HDI）", key="eq_add_name")
        eq_kw = st.text_input("关键词（逗号分隔）", placeholder="例如：ldd棕化线（hdi）, hdi", key="eq_add_kw")
        render_keyword_tags(split_keywords(eq_kw))
        if st.button("✅ 添加", type="primary", width='stretch', key="btn_eq_add"):
            keywords = split_keywords(eq_kw)
            if eq_name.strip() and keywords:
                if eq_name.strip() in equipment:
                    st.error("线体已存在，请使用编辑功能更新关键词")
                    st.stop()
                equipment[eq_name.strip()] = keywords
                config.save_equipment(equipment)
                st.toast(f"✅ 已添加：{eq_name}", icon="✅")
                st.rerun()
            else:
                st.warning("请填写完整")

    with eq_tab2:
        st.markdown("**编辑关键词**")
        eq_keys = list(equipment.keys())
        if eq_keys:
            edit_name = st.selectbox("选择线体", eq_keys, key="eq_edit_select")
            default_kw = ", ".join(equipment.get(edit_name, []))
            new_kw = st.text_input("关键词", value=default_kw, key="eq_kw_edit")
            render_keyword_tags(split_keywords(new_kw))
            if st.button("💾 保存", type="primary", width='stretch', key="btn_eq_save"):
                keywords = split_keywords(new_kw)
                if keywords:
                    equipment[edit_name] = keywords
                    config.save_equipment(equipment)
                    st.toast(f"✅ 已更新：{edit_name}", icon="✅")
                    st.rerun()
                else:
                    st.warning("关键词不能为空")

    with eq_tab3:
        st.markdown("**删除线体**")
        del_name = st.selectbox("选择线体", list(equipment.keys()), key="eq_del_select")
        if del_name:
            st.warning(f"将删除：**{del_name}**")
            confirm_del = st.checkbox("我确认要删除", key="eq_del_confirm")
            if confirm_del and st.button("🗑️ 确认删除", type="primary", width='stretch', key="btn_eq_del"):
                equipment.pop(del_name, None)
                config.save_equipment(equipment)
                st.toast(f"✅ 已删除：{del_name}", icon="✅")
                st.rerun()

# =====================
# 任务类型
# =====================
with tab_tr:
    render_section_title("📋", "任务类型")

    c4, c5 = st.columns(2)
    c4.metric("类型", f"{len(task_rules)} 个")
    c5.metric("规则", f"{sum(len(v) for v in task_rules.values())} 字符")

    tr_search = st.text_input("🔍 搜索任务类型或规则", placeholder="输入类型名、正则关键词过滤...", key="tr_search")
    task_rule_df = pd.DataFrame([{"类型": k, "匹配规则": v} for k, v in task_rules.items()])
    if tr_search and not task_rule_df.empty:
        mask = task_rule_df.astype(str).apply(lambda x: x.str.contains(tr_search, case=False, na=False)).any(axis=1)
        task_rule_df = task_rule_df[mask]
    st.caption(f"当前显示 {len(task_rule_df)} / {len(task_rules)} 个任务类型")

    st.dataframe(
        task_rule_df,
        width='stretch', hide_index=True,
    )

    tr_tab1, tr_tab2, tr_tab3 = st.tabs(["➕ 新增", "✏️ 编辑", "🗑️ 删除"])

    with tr_tab1:
        st.markdown("**添加新类型**")
        tr_name = st.text_input("类型名称", placeholder="例如：部署", key="tr_add_name")
        tr_pattern = st.text_input("匹配规则（正则，用|分隔）", placeholder="例如：部署|上线|发布", key="tr_add_pattern")
        if tr_pattern:
            is_valid, err_msg = config.validate_regex(tr_pattern)
            if not is_valid:
                st.error(f"❌ 正则表达式无效: {err_msg}")
            else:
                st.success("✅ 正则表达式有效")
        if st.button("✅ 添加", type="primary", width='stretch', key="btn_tr_add"):
            if tr_name.strip() and tr_pattern.strip():
                if tr_name.strip() in task_rules:
                    st.error("任务类型已存在，请使用编辑功能更新规则")
                    st.stop()
                is_valid, err_msg = config.validate_regex(tr_pattern)
                if not is_valid:
                    st.error(f"❌ 正则表达式无效: {err_msg}")
                else:
                    task_rules[tr_name.strip()] = tr_pattern.strip()
                    config.save_task_rules(task_rules)
                    st.toast(f"✅ 已添加：{tr_name}", icon="✅")
                    st.rerun()
            else:
                st.warning("请填写完整")

    with tr_tab2:
        st.markdown("**编辑规则**")
        tr_keys = list(task_rules.keys())
        if tr_keys:
            tr_edit_name = st.selectbox("选择类型", tr_keys, key="tr_edit_select")
            default_pat = task_rules.get(tr_edit_name, "")
            new_pattern = st.text_input("匹配规则", value=default_pat, key="tr_pattern_edit")
            if new_pattern:
                is_valid, err_msg = config.validate_regex(new_pattern)
                if not is_valid:
                    st.error(f"❌ 正则表达式无效: {err_msg}")
                else:
                    st.success("✅ 正则表达式有效")
            if st.button("💾 保存", type="primary", width='stretch', key="btn_tr_save"):
                if new_pattern.strip():
                    is_valid, err_msg = config.validate_regex(new_pattern)
                    if not is_valid:
                        st.error(f"❌ 正则表达式无效: {err_msg}")
                    else:
                        task_rules[tr_edit_name] = new_pattern.strip()
                        config.save_task_rules(task_rules)
                        st.toast(f"✅ 已更新：{tr_edit_name}", icon="✅")
                        st.rerun()
                else:
                    st.warning("规则不能为空")

    with tr_tab3:
        st.markdown("**删除类型**")
        tr_del_name = st.selectbox("选择类型", list(task_rules.keys()), key="tr_del_select")
        if tr_del_name:
            st.warning(f"将删除：**{tr_del_name}**")
            confirm_del_tr = st.checkbox("我确认要删除", key="tr_del_confirm")
            if confirm_del_tr and st.button("🗑️ 确认删除", type="primary", width='stretch', key="btn_tr_del"):
                task_rules.pop(tr_del_name, None)
                config.save_task_rules(task_rules)
                st.toast(f"✅ 已删除：{tr_del_name}", icon="✅")
                st.rerun()

# =====================
# 数据管理
# =====================
with tab_data:
    render_section_title("💾", "数据管理")

    col_stat1, col_stat2 = st.columns(2)
    try:
        db_reports = report_db.get_all_reports()
        db_count = len(db_reports)
    except Exception:
        db_count = 0
    col_stat1.metric("数据库报告数", db_count)
    col_stat2.metric("数据库文件", "reports.db")

    st.markdown("---")
    st.markdown("**🔄 迁移 txt 到数据库**")
    st.caption("将 report/ 目录下的 txt 报告文件迁移到 SQLite 数据库")
    if st.button("🚀 执行迁移", width='stretch'):
        result = report_db.migrate_from_txt()
        if result["errors"]:
            for err in result["errors"]:
                st.error(f"❌ {err}")
        st.success(f"✅ 成功迁移 {result['migrated']} 份报告")
        st.rerun()

    st.markdown("---")
    st.markdown("**📤 导出数据**")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        if st.button("📋 导出 JSON", width='stretch'):
            export_path = report_db.export_db_json()
            st.success(f"✅ 已导出：{export_path.name}")
            with open(export_path, "rb") as f:
                st.download_button(
                    "📥 下载 JSON 文件", f,
                    file_name=export_path.name,
                    mime="application/json",
                    width='stretch'
                )
    with col_exp2:
        if st.button("💾 备份数据库", width='stretch'):
            backup_path = report_db.backup_db()
            if backup_path:
                st.success(f"✅ 备份已保存")
                with open(backup_path, "rb") as f:
                    st.download_button(
                        "📥 下载备份文件", f,
                        file_name=backup_path.name,
                        mime="application/octet-stream",
                        width='stretch'
                    )
            else:
                st.warning("数据库文件不存在")

    st.markdown("---")
    st.markdown("**📥 导入数据**")
    uploaded = st.file_uploader("选择 JSON 备份文件", type=["json"], key="import_json")
    if uploaded:
        import json as json_lib
        try:
            data = json_lib.load(uploaded)
            st.success(f"检测到 {len(data.get('reports', []))} 份报告，{len(data.get('problems', []))} 条问题")
            if st.button("✅ 确认导入", width='stretch'):
                result = report_db.import_db_json(uploaded)
                st.success(f"✅ 导入完成：{result['reports']} 份报告，{result['problems']} 条问题")
                st.rerun()
        except Exception as e:
            st.error(f"❌ 文件格式错误：{e}")
