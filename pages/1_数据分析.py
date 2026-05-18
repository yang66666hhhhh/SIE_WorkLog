import re
import streamlit as st
import pandas as pd
import numpy as np
from html import escape
from pathlib import Path
from io import BytesIO
from utils.config import Config
from utils.ai_chat_interface import render_natural_language_query
from utils.intelligent_cache import IntelligentCache
from utils.optimized_processor import OptimizedWorkRecordProcessor
from utils.charts import (
    get_chart_config, create_daily_bar_chart, create_task_pie_chart,
    create_device_bar_chart, create_stack_bar_chart, create_heatmap,
)
from utils.styles import (
    inject_global_css, render_kpi_card, render_section_title,
    render_empty_state, render_sidebar_nav, PRIMARY, SUCCESS, WARNING, DANGER, INFO, NEUTRAL,
)

MAX_UPLOAD_SIZE_MB = 10
ALLOWED_EXTENSIONS = {"xlsx"}


@st.cache_data(ttl=3600, show_spinner="📊 正在加载数据...")
def load_data(file_path, file_mtime_ns=0, file_size=0):
    try:
        cache = IntelligentCache()
        cache_key = cache.build_key("load_data", file_path, file_mtime_ns, file_size)
        df = cache.get(cache_key)
        if df is None:
            df = pd.read_excel(file_path)
            cache.set(cache_key, df)
        df["日期"] = pd.to_datetime(df["日期"])
        return df
    except Exception as e:
        st.error(f"❌ 数据加载失败: {e}")
        return pd.DataFrame()


@st.cache_resource
def get_config():
    return Config()


@st.cache_resource
def get_processor():
    return OptimizedWorkRecordProcessor()


st.set_page_config(page_title="Data Analysis", layout="wide", menu_items=None)
inject_global_css()

config = get_config()
processor = get_processor()

RAW_FILE = Path("工作记录.xlsx")
OUTPUT_FILE = Path("任务级数据.xlsx")


def load_output_data():
    if not OUTPUT_FILE.exists():
        return pd.DataFrame()
    stat = OUTPUT_FILE.stat()
    return load_data(str(OUTPUT_FILE), stat.st_mtime_ns, stat.st_size)


def process_file():
    processor.equipment_dict = config.load_equipment()
    processor.task_rules = {k: re.compile(v) for k, v in config.load_task_rules().items()}
    processor.process(str(RAW_FILE), str(OUTPUT_FILE))
    config.save_config_hash(config.config_hash())
    st.cache_data.clear()


def validate_upload(uploaded_file):
    if uploaded_file is None:
        return True, ""
    ext = Path(uploaded_file.name).suffix.lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式：.{ext}，仅支持 .xlsx"
    if len(uploaded_file.getvalue()) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        return False, f"文件超过 {MAX_UPLOAD_SIZE_MB}MB 限制"
    return True, ""


def render_filter_summary(start_date, end_date, source, device, task_type, rows):
    chips = [
        ("📅", f"{start_date} ~ {end_date}"),
        ("🏢", f"来源 {len(source)} 项"),
        ("⚙️", f"设备 {len(device)} 项"),
        ("📋", f"类型 {len(task_type)} 项"),
        ("🔎", f"{rows} 条任务"),
    ]
    html = "".join(
        f'<span class="filter-chip">{icon}<span>{escape(text)}</span></span>'
        for icon, text in chips
    )
    st.markdown(f'<div class="filter-summary">{html}</div>', unsafe_allow_html=True)


def render_rank_list(title, data, name_col, value_col="工时", max_rows=5, color=PRIMARY):
    st.markdown(f"**{title}**")
    if data.empty:
        st.caption("暂无数据")
        return

    top_data = data.sort_values(value_col, ascending=False).head(max_rows)
    max_value = top_data[value_col].max()
    rows_html = []
    for _, row in top_data.iterrows():
        value = float(row[value_col])
        percent = value / max_value * 100 if max_value else 0
        label = escape(str(row[name_col]))
        rows_html.append(
            '<div class="rank-row">'
            f'<div class="rank-head"><span>{label}</span><span>{value:.1f}h</span></div>'
            '<div class="rank-bar">'
            f'<div class="rank-fill" style="width:{percent:.0f}%;background:{color};"></div>'
            '</div>'
            f'<div class="rank-meta">占 Top 最大值 {percent:.0f}%</div>'
            '</div>'
        )
    st.markdown(f'<div class="rank-list">{"".join(rows_html)}</div>', unsafe_allow_html=True)


# =====================
# 侧边栏：导航 + 筛选 + 上传 + 操作
# =====================
with st.sidebar:
    render_sidebar_nav("数据分析")
    st.divider()

    st.markdown('<p class="sidebar-title">🔍 筛选条件</p>', unsafe_allow_html=True)

    if not RAW_FILE.exists() and not OUTPUT_FILE.exists():
        st.info("请先上传数据文件")
    else:
        if OUTPUT_FILE.exists():
            df_preview = load_output_data()
        else:
            df_preview = pd.DataFrame()

        if not df_preview.empty:
            with st.expander("📅 时间范围", expanded=True):
                date_min, date_max = df_preview["日期"].min().date(), df_preview["日期"].max().date()
                days_diff = (date_max - date_min).days

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("最近7天", use_container_width=True, key="btn_7d"):
                        st.session_state.date_filter = [date_max - pd.Timedelta(days=6), date_max]
                        st.rerun()
                with col_btn2:
                    if st.button("全范围", use_container_width=True, key="btn_all"):
                        st.session_state.date_filter = [date_min, date_max]
                        st.rerun()

                default_val = [date_min, date_max]
                if "date_filter" in st.session_state:
                    default_val = st.session_state.date_filter

                date_range = st.date_input("选择日期", value=default_val, key="date_filter")
                if len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date = end_date = date_range[0]
                st.caption(f"数据范围: {date_min} ~ {date_max} ({days_diff}天)")

            with st.expander("🏢 来源", expanded=False):
                source = st.multiselect("来源", df_preview["来源"].unique(), default=df_preview["来源"].unique(), key="source_filter")

            with st.expander("⚙️ 设备", expanded=False):
                device = st.multiselect("设备", df_preview["线体/设备"].unique(), default=df_preview["线体/设备"].unique(), key="device_filter")

            with st.expander("📋 任务类型", expanded=False):
                task_type = st.multiselect("任务类型", df_preview["任务类型"].unique(), default=df_preview["任务类型"].unique(), key="task_type_filter")

    st.divider()

    with st.expander("📤 上传数据", expanded=False):
        uploaded = st.file_uploader("上传工作记录", type=["xlsx"], key="upload_data", label_visibility="collapsed")
        if uploaded:
            is_valid, msg = validate_upload(uploaded)
            if not is_valid:
                st.error(f"❌ {msg}")
            else:
                RAW_FILE.write_bytes(uploaded.getvalue())
                st.success(f"✅ 已保存：{uploaded.name}")
                st.cache_data.clear()
                st.rerun()

    if st.button("🔄 重新处理数据", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        try:
            process_file()
            st.toast("✅ 数据重新处理完成")
            st.rerun()
        except Exception as e:
            st.error(f"处理失败: {e}")

# =====================
# 主区域：数据处理
# =====================
if not RAW_FILE.exists():
    render_empty_state("📭", "暂无数据", "请通过左侧「上传数据」上传工作记录.xlsx")
    st.stop()

current_hash = config.config_hash()
saved_hash = config.load_config_hash()
need_process = current_hash != saved_hash or not OUTPUT_FILE.exists()

if need_process:
    label = "⚙️ 配置变更检测中..." if current_hash != saved_hash else "📝 首次处理数据..."
    with st.status(label, expanded=True) as status:
        try:
            process_file()
            status.update(label="✅ 处理完成", state="complete")
        except Exception as e:
            status.update(label=f"❌ 处理失败: {e}", state="error")
            st.stop()

with st.spinner("📊 加载数据中..."):
    df = load_output_data()

if df.empty:
    render_empty_state("📭", "数据为空", "处理后的数据为空，请检查原始数据文件")
    st.stop()

# 应用筛选
if "source_filter" not in st.session_state:
    st.stop()

df = df[
    (df["日期"] >= pd.to_datetime(start_date))
    & (df["日期"] <= pd.to_datetime(end_date))
    & (df["来源"].isin(source))
    & (df["线体/设备"].isin(device))
    & (df["任务类型"].isin(task_type))
]

if df.empty:
    render_empty_state("🔍", "暂无匹配数据", "当前筛选范围内没有数据，请调整筛选条件")
    st.stop()

render_filter_summary(start_date, end_date, source, device, task_type, len(df))

# =====================
# KPI 指标
# =====================
total_hours = df["工时"].sum()
total_tasks = len(df)
avg = total_hours / total_tasks if total_tasks else 0
work_days = df["日期"].nunique()
daily_avg = total_hours / work_days if work_days else 0

all_dates = pd.date_range(start=pd.to_datetime(start_date), end=pd.to_datetime(end_date))
total_days = len(all_dates)
rest_days = total_days - work_days

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1: render_kpi_card(f"{total_hours:.0f}h", "总工时", "⏱️", PRIMARY, f"{total_tasks} 任务")
with kpi2: render_kpi_card(f"{daily_avg:.1f}h", "日均工时", "📅", INFO if 6 <= daily_avg <= 9 else DANGER, f"每任务 {avg:.1f}h")
with kpi3: render_kpi_card(f"{work_days}", "工作天数", "💼", SUCCESS, f"占比 {work_days/total_days*100:.0f}%" if total_days > 0 else None)
with kpi4: render_kpi_card(f"{rest_days}", "休息天数", "💤", NEUTRAL)
with kpi5:
    pct = daily_avg / 8 * 100 if daily_avg else 0
    color = SUCCESS if 90 <= pct <= 110 else WARNING if 75 <= pct <= 125 else DANGER
    render_kpi_card(f"{pct:.0f}%", "达标率", "🎯", color, "标准 8h/天")

# 来源分布
sources = df["来源"].unique()
if len(sources) > 1:
    with st.expander("📊 来源分布详情", expanded=False):
        src_cols = st.columns(len(sources))
        for i, src in enumerate(sources):
            src_hours = df[df["来源"] == src]["工时"].sum()
            src_pct = src_hours / total_hours * 100 if total_hours else 0
            src_cols[i].metric(f"{src}", f"{src_hours:.1f}h", f"{src_pct:.0f}%")

render_section_title("🏆", "重点排行")
rank_left, rank_right, rank_third = st.columns(3)
with rank_left:
    device_rank = df.groupby("线体/设备", as_index=False)["工时"].sum()
    render_rank_list("设备工时 Top 5", device_rank, "线体/设备", color=PRIMARY)
with rank_right:
    type_rank = df.groupby("任务类型", as_index=False)["工时"].sum()
    render_rank_list("任务类型 Top 5", type_rank, "任务类型", color=WARNING)
with rank_third:
    date_rank = df.assign(日期文本=df["日期"].dt.strftime("%Y-%m-%d")).groupby("日期文本", as_index=False)["工时"].sum()
    date_rank = date_rank.rename(columns={"日期文本": "日期"})
    render_rank_list("高工时日期 Top 5", date_rank, "日期", color=INFO)

# =====================
# 图表区
# =====================
render_section_title("📈", "工时分析")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("**工时趋势**")
    st.markdown('<div class="chart-note">按日期和来源对比每日投入，适合观察峰值和阶段性变化。</div>', unsafe_allow_html=True)
    fig = create_daily_bar_chart(df)
    st.plotly_chart(fig, use_container_width=True, config=get_chart_config())

with col_right:
    st.markdown("**任务类型分布**")
    st.markdown('<div class="chart-note">显示当前筛选范围内，各任务类型消耗的工时占比。</div>', unsafe_allow_html=True)
    fig_pie = create_task_pie_chart(df)
    st.plotly_chart(fig_pie, use_container_width=True, config=get_chart_config())

render_section_title("🔧", "设备与任务")

col_mid_left, col_mid_right = st.columns(2)
with col_mid_left:
    st.markdown("**设备工时分布**")
    st.markdown('<div class="chart-note">横向对比设备/线体投入，快速识别主要工作对象。</div>', unsafe_allow_html=True)
    fig_dev = create_device_bar_chart(df)
    st.plotly_chart(fig_dev, use_container_width=True, config=get_chart_config())

with col_mid_right:
    st.markdown("**每日任务构成**")
    st.markdown('<div class="chart-note">观察每天的任务类型组合，判断工作内容是否集中或分散。</div>', unsafe_allow_html=True)
    fig_stack = create_stack_bar_chart(df)
    st.plotly_chart(fig_stack, use_container_width=True, config=get_chart_config())

render_section_title("📅", "周工时热力图")
fig_heat = create_heatmap(df)
st.plotly_chart(fig_heat, use_container_width=True, config=get_chart_config())
st.caption("💤 灰色 = 休息日 | 颜色深浅 = 工时")

# =====================
# Drill Down
# =====================
render_section_title("🔍", "明细钻取")
tab1, tab2, tab3, tab4 = st.tabs(["📅 按日期", "🏢 按设备", "📋 按类型", "📂 按来源"])
drop_cols = [c for c in ["星期", "周数"] if c in df.columns]

df_show = df.drop(columns=drop_cols, errors="ignore")

col_config = {
    "工时": st.column_config.NumberColumn("工时", format="%.1f h"),
    "日总工时": st.column_config.NumberColumn("日总工时", format="%.1f h"),
    "任务占比": st.column_config.NumberColumn("占比", format="%.1f%%"),
    "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
}

with tab1:
    d = st.selectbox("选择日期", sorted(df["日期"].dt.date.unique()), key="date_select")
    st.dataframe(df_show[df_show["日期"].dt.date == d], use_container_width=True, hide_index=True, column_config=col_config)

with tab2:
    dev = st.selectbox("选择设备", df["线体/设备"].unique(), key="device_select")
    dev_df = df_show[df["线体/设备"] == dev]
    st.metric("设备总工时", f"{dev_df['工时'].sum():.1f}h")
    st.dataframe(dev_df, use_container_width=True, hide_index=True, column_config=col_config)

with tab3:
    task_type_sel = st.selectbox("选择任务类型", df["任务类型"].unique(), key="type_select")
    type_df = df_show[df["任务类型"] == task_type_sel]
    st.metric("类型总工时", f"{type_df['工时'].sum():.1f}h")
    st.dataframe(type_df, use_container_width=True, hide_index=True, column_config=col_config)

with tab4:
    src = st.selectbox("选择来源", df["来源"].unique(), key="source_select")
    src_df = df_show[df["来源"] == src]
    st.metric("来源总工时", f"{src_df['工时'].sum():.1f}h")
    st.dataframe(src_df, use_container_width=True, hide_index=True, column_config=col_config)

with st.expander("💬 自然语言查询", expanded=False):
    render_natural_language_query(df_show, key_prefix="worklog_nlq")

# =====================
# AI 分析
# =====================
render_section_title("🤖", "AI 智能分析")

ai_config = config.load_ai_config()
if ai_config.get("enabled") and ai_config.get("api_key"):
    with st.spinner("AI 分析中..."):
        from utils.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer(
            api_key=ai_config.get("api_key"),
            base_url=ai_config.get("base_url"),
            model=ai_config.get("model", "gpt-3.5-turbo")
        )
        ai_result = analyzer.generate_summary(df)
        st.markdown(ai_result)
else:
    from utils.analyzer import generate_insights
    insights_md = generate_insights(df)
    st.markdown(insights_md)

st.caption("💡 如需 AI 智能分析，请在系统配置中启用")

# =====================
# 数据明细
# =====================
render_section_title("📋", "数据明细")

show_cols = [c for c in df.columns if c not in drop_cols]
preferred_cols = ["日期", "来源", "线体/设备", "任务类型", "工时", "任务内容", "问题描述", "备注", "项目"]
show_cols = [c for c in preferred_cols if c in show_cols] + [c for c in show_cols if c not in preferred_cols]
if "问题描述" in show_cols:
    show_cols.remove("问题描述")
    task_idx = show_cols.index("任务内容") if "任务内容" in show_cols else 0
    show_cols.insert(task_idx + 1, "问题描述")

search = st.text_input("🔍 搜索任务内容", placeholder="输入关键词过滤...", key="data_search")
df_display = df[show_cols]
if search:
    mask = df_display.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
    df_display = df_display[mask]
    st.caption(f"当前关键词命中 {len(df_display)} / {len(df)} 条任务")
else:
    st.caption(f"当前筛选范围共 {len(df_display)} 条任务")

st.dataframe(df_display, use_container_width=True, hide_index=True, height=350, column_config=col_config)

col_csv, col_excel = st.columns(2)
with col_csv:
    csv = df[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button("📥 导出 CSV", csv, f"工作数据_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

with col_excel:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df[show_cols].to_excel(writer, sheet_name="工作数据", index=False)
    excel_data = output.getvalue()
    st.download_button("📥 导出 Excel", excel_data, f"工作数据_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
