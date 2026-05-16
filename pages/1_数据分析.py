import re
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from io import BytesIO
from utils.config import Config
from utils.processor import WorkRecordProcessor
from utils.charts import (
    get_chart_config, create_daily_bar_chart, create_task_pie_chart,
    create_device_bar_chart, create_stack_bar_chart, create_heatmap,
    COLORS_MAP, TASK_COLORS, CHART_HEIGHT, CHART_MARGIN
)

MAX_UPLOAD_SIZE_MB = 10
ALLOWED_EXTENSIONS = {"xlsx"}


@st.cache_data(ttl=3600, show_spinner="📊 正在加载数据...")
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
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
    return WorkRecordProcessor()


st.set_page_config(page_title="Data Analysis", layout="wide")

config = get_config()
processor = get_processor()

RAW_FILE = Path("工作记录.xlsx")
OUTPUT_FILE = Path("任务级数据.xlsx")


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


uploaded = st.file_uploader("上传原始数据（可选，目录下已有工作记录.xlsx）", type=["xlsx"])

if uploaded:
    is_valid, msg = validate_upload(uploaded)
    if not is_valid:
        st.error(f"❌ {msg}")
        st.stop()
    RAW_FILE.write_bytes(uploaded.getvalue())
    st.success(f"已保存：{uploaded.name}")

if not RAW_FILE.exists():
    st.warning("未找到工作记录.xlsx，请上传数据文件")
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
    df = load_data(str(OUTPUT_FILE))

# =====================
# 筛选器（侧边栏）
# =====================
st.sidebar.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e8ecf0 100%);
    }
    .sidebar-title {
        font-size: 16px;
        font-weight: 600;
        color: #4C78A8;
        padding: 8px 0 4px 0;
    }
    [data-testid="stSidebar"] h3 {
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<p class="sidebar-title">🔍 筛选条件</p>', unsafe_allow_html=True)

    with st.expander("📅 时间范围", expanded=True):
        date_min, date_max = df["日期"].min().date(), df["日期"].max().date()
        days_diff = (date_max - date_min).days

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("最近7天", use_container_width=True):
                st.session_state.date_filter = [date_max - pd.Timedelta(days=6), date_max]
                st.rerun()
        with col_btn2:
            if st.button("全范围", use_container_width=True):
                st.session_state.date_filter = [date_min, date_max]
                st.rerun()

        default_val = [date_max - pd.Timedelta(days=6), date_max]
        if "date_filter" in st.session_state:
            default_val = st.session_state.date_filter

        date_range = st.date_input(
            "选择日期",
            value=default_val,
            key="date_filter"
        )
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range[0]

        st.caption(f"数据范围: {date_min} ~ {date_max} (共{days_diff}天)")

    with st.expander("🏢 来源", expanded=True):
        source = st.multiselect(
            "选择来源",
            df["来源"].unique(),
            default=df["来源"].unique(),
            key="source_filter"
        )

    with st.expander("⚙️ 设备", expanded=True):
        device = st.multiselect(
            "选择设备",
            df["线体/设备"].unique(),
            default=df["线体/设备"].unique(),
            key="device_filter"
        )

    with st.expander("📋 任务类型", expanded=True):
        task_type = st.multiselect(
            "选择任务类型",
            df["任务类型"].unique(),
            default=df["任务类型"].unique(),
            key="task_type_filter"
        )

    st.divider()

    if st.button("🔄 重新处理数据", type="secondary", use_container_width=True):
        st.cache_data.clear()
        try:
            process_file()
            st.success("重新处理完成")
            st.rerun()
        except Exception as e:
            st.error(f"处理失败: {e}")

df = df[
    (df["日期"] >= pd.to_datetime(start_date))
    & (df["日期"] <= pd.to_datetime(end_date))
    & (df["来源"].isin(source))
    & (df["线体/设备"].isin(device))
    & (df["任务类型"].isin(task_type))
]

if len(df) == 0:
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px;">
        <h3>🔍 暂无数据</h3>
        <p style="color: #666;">当前筛选范围内没有数据</p>
        <p style="color: #999;">请调整筛选条件或检查数据文件</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# =====================
# KPI
# =====================
total_hours = df["工时"].sum()
total_tasks = len(df)
avg = total_hours / total_tasks if total_tasks else 0
work_days = df["日期"].nunique()
daily_avg = total_hours / work_days if work_days else 0

all_dates = pd.date_range(start=pd.to_datetime(start_date), end=pd.to_datetime(end_date))
total_days = len(all_dates)
rest_days = total_days - work_days

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("总工时", f"{total_hours:.1f}h", f"{total_tasks}任务")
col2.metric("日均工时", f"{daily_avg:.1f}h", f"每任务{avg:.1f}h")
col3.metric("工作天数", f"{work_days}天", f"占比{work_days/total_days*100:.0f}%" if total_days > 0 else None)
col4.metric("休息天数", f"{rest_days}天", f"💤" if rest_days > 0 else "✅")
col5.metric("日标准工时", "8.0h", f"{daily_avg/8*100:.0f}%" if daily_avg > 0 else None)

sources = df["来源"].unique()
if len(sources) > 1:
    with st.expander("📊 来源分布详情", expanded=False):
        src_cols = st.columns(len(sources))
        for i, src in enumerate(sources):
            src_hours = df[df["来源"] == src]["工时"].sum()
            src_pct = src_hours / total_hours * 100 if total_hours else 0
            src_cols[i].metric(f"{src}", f"{src_hours:.1f}h", f"{src_pct:.0f}%")

st.markdown("---")

# =====================
# 图表区
# =====================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("工时趋势")
    fig = create_daily_bar_chart(df)
    st.plotly_chart(fig, use_container_width=True, config=get_chart_config())

with col_right:
    st.subheader("任务类型分布")
    fig_pie = create_task_pie_chart(df)
    st.plotly_chart(fig_pie, use_container_width=True, config=get_chart_config())

col_mid_left, col_mid_right = st.columns(2)

with col_mid_left:
    st.subheader("设备工时分布")
    fig_dev = create_device_bar_chart(df)
    st.plotly_chart(fig_dev, use_container_width=True, config=get_chart_config())

with col_mid_right:
    st.subheader("每日任务分布")
    fig_stack = create_stack_bar_chart(df)
    st.plotly_chart(fig_stack, use_container_width=True, config=get_chart_config())

st.subheader("📅 周工时热力图")
fig_heat = create_heatmap(df)
st.plotly_chart(fig_heat, use_container_width=True, config=get_chart_config())
st.caption("💤 灰=休息日 | 颜色=工时")

# =====================
# Drill Down
# =====================
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["按日期", "按设备", "按类型", "按来源"])
drop_cols = [c for c in ["星期", "周数"] if c in df.columns]

with tab1:
    d = st.selectbox("选择日期", sorted(df["日期"].dt.date.unique()), key="date_select")
    st.dataframe(df[df["日期"].dt.date == d].drop(columns=drop_cols), use_container_width=True)

with tab2:
    dev = st.selectbox("选择设备", df["线体/设备"].unique(), key="device_select")
    dev_df = df[df["线体/设备"] == dev]
    st.metric("设备总工时", f"{dev_df['工时'].sum():.1f}h")
    st.dataframe(dev_df.drop(columns=drop_cols), use_container_width=True)

with tab3:
    task_type_sel = st.selectbox("选择任务类型", df["任务类型"].unique(), key="type_select")
    type_df = df[df["任务类型"] == task_type_sel]
    st.metric("类型总工时", f"{type_df['工时'].sum():.1f}h")
    st.dataframe(type_df.drop(columns=drop_cols), use_container_width=True)

with tab4:
    src = st.selectbox("选择来源", df["来源"].unique(), key="source_select")
    src_df = df[df["来源"] == src]
    st.metric("来源总工时", f"{src_df['工时'].sum():.1f}h")
    st.dataframe(src_df.drop(columns=drop_cols), use_container_width=True)

# =====================
# AI分析
# =====================
st.markdown("---")
st.subheader("🤖 AI 智能分析")

with st.expander("查看分析报告", expanded=True):
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
st.markdown("---")
st.subheader("📋 数据明细")

show_cols = [c for c in df.columns if c not in drop_cols]
has_problem_desc = "问题描述" in df.columns
if has_problem_desc and "问题描述" in show_cols:
    show_cols.remove("问题描述")
    task_idx = show_cols.index("任务内容") if "任务内容" in show_cols else 0
    show_cols.insert(task_idx + 1, "问题描述")

st.dataframe(df[show_cols], use_container_width=True)

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
