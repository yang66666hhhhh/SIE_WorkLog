import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from io import BytesIO
from utils.config import Config
from utils.processor import WorkRecordProcessor

@st.cache_data(ttl=3600, show_spinner="📊 正在加载数据...")
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df["日期"] = pd.to_datetime(df["日期"])
        return df
    except Exception as e:
        st.error(f"❌ 数据加载失败: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_processed_data(file_path):
    return load_data(file_path)

def get_chart_config():
    return {
        "displayModeBar": False,
        "toImageButtonOptions": {
            "format": "png",
            "filename": "chart",
            "height": 600,
            "width": 800,
            "scale": 2
        },
        "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d", "pan2d", "zoom2d"],
        "displaylogo": False,
        "responsive": True
    }

COLORS_MAP = {"MSAP": "#4C78A8", "HDI二处": "#F58518"}
TASK_COLORS = {"调试": "#4C78A8", "联调": "#4C78A8", "配置": "#F58518", "学习": "#E45756", "分析": "#72B7B2", "其他": "#54A24B"}
CHART_HEIGHT = 280
CHART_MARGIN = dict(t=15, b=20, l=30, r=30)

def create_bar_chart(data, x, y, color_col=None, orientation="v", title=""):
    fig = go.Figure()
    colors = COLORS_MAP if color_col == "来源" else TASK_COLORS
    for name, grp in data.groupby(color_col) if color_col else [(None, data)]:
        if color_col:
            grp_data = grp.sort_values(y, ascending=(orientation == "h"))
            fig.add_bar(
                x=grp_data[x] if orientation == "v" else grp_data[y],
                y=grp_data[y] if orientation == "v" else grp_data[x],
                orientation=orientation,
                name=name,
                marker_color=colors.get(name, "#999999"),
                text=grp_data[y].apply(lambda v: f"{v:.1f}h" if orientation == "v" else f"{v:.1f}h"),
                textposition="outside",
                hovertemplate=f"{name if name else title}: %{{text}}<extra></extra>"
            )
        else:
            fig.add_bar(
                x=data[x] if orientation == "v" else data[y],
                y=data[y] if orientation == "v" else data[x],
                orientation=orientation,
                marker_color=colors.get(name, "#999999") if name else "#4C78A8",
                hovertemplate=f"{title}: %{{y:.1f}}h<extra></extra>"
            )
    return fig

def create_pie_chart(labels, values, title=""):
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#9D7559"],
        textinfo="percent",
        hovertemplate="%{label}: %{percent}<extra></extra>"
    )])
    return fig

st.set_page_config(page_title="Data Analysis", layout="wide")

config = Config()
processor = WorkRecordProcessor()

RAW_FILE = Path("工作记录.xlsx")
OUTPUT_FILE = Path("任务级数据.xlsx")

# =====================
# 数据处理
# =====================
def process_file():
    processor.equipment_dict = config.load_equipment()
    processor.task_rules = {k: __import__("re").compile(v) for k, v in config.load_task_rules().items()}
    processor.process(str(RAW_FILE), str(OUTPUT_FILE))
    config.save_config_hash(config.config_hash())
    st.cache_data.clear()

uploaded = st.file_uploader("上传原始数据（可选，目录下已有工作记录.xlsx）", type=["xlsx"])

if uploaded:
    RAW_FILE.write_bytes(uploaded.getvalue())
    st.success(f"已保存：{uploaded.name}")

if not RAW_FILE.exists():
    st.warning("未找到工作记录.xlsx，请上传数据文件")
    st.stop()

# 配置变更检测
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

if st.button("🔄 重新处理", type="secondary"):
        st.cache_data.clear()
        try:
            process_file()
            st.success("重新处理完成")
            st.rerun()
        except Exception as e:
            st.error(f"处理失败: {e}")

# =====================
# 筛选器（侧边栏 - 可折叠）
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

    st.divider()

df = df[
    (df["日期"] >= pd.to_datetime(start_date))
    & (df["日期"] <= pd.to_datetime(end_date))
    & (df["来源"].isin(source))
    & (df["线体/设备"].isin(device))
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
    daily = df.groupby(["日期", "来源"])["工时"].sum().reset_index()
    fig = go.Figure()
    for src_name, grp in daily.groupby("来源"):
        fig.add_bar(
            x=grp["日期"], y=grp["工时"], name=src_name,
            marker_color=COLORS_MAP.get(src_name, "#999999"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>%{y:.1f}h<extra>" + src_name + "</extra>"
        )
    fig.update_layout(
        barmode="group", height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="工时 (h)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True, config=get_chart_config())

with col_right:
    st.subheader("任务类型分布")
    type_data = df.groupby("任务类型")["工时"].sum().reset_index().sort_values("工时", ascending=False)
    fig_pie = go.Figure(data=[go.Pie(
        labels=type_data["任务类型"], values=type_data["工时"], hole=0.4,
        marker_colors=["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#9D7559"],
        textinfo="percent",
        hovertemplate="%{label}<br>%{percent}<br>%{value:.1f}h<extra></extra>"
    )])
    fig_pie.update_layout(
        height=CHART_HEIGHT, margin=CHART_MARGIN,
        annotations=[dict(text=f"{type_data['工时'].sum():.0f}h", x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    st.plotly_chart(fig_pie, use_container_width=True, config=get_chart_config())

col_mid_left, col_mid_right = st.columns(2)

with col_mid_left:
    st.subheader("设备工时分布")
    dev_data = df.groupby(["线体/设备", "来源"])["工时"].sum().reset_index().sort_values("工时", ascending=True)
    fig_dev = go.Figure()
    for src_name, grp in dev_data.groupby("来源"):
        fig_dev.add_bar(
            y=grp["线体/设备"], x=grp["工时"], orientation="h", name=src_name,
            marker_color=COLORS_MAP.get(src_name, "#999999"),
            text=grp["工时"].apply(lambda x: f"{x:.1f}h"),
            textposition="outside",
            hovertemplate="%{y}<br>%{x:.1f}h<extra>{src_name}</extra>"
        )
    fig_dev.update_layout(
        barmode="group", height=CHART_HEIGHT,
        margin=dict(t=15, b=20, l=100, r=30), xaxis_title="工时 (h)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="closest"
    )
    st.plotly_chart(fig_dev, use_container_width=True, config=get_chart_config())

with col_mid_right:
    st.subheader("每日任务分布")
    stack_data = df.groupby(["日期", "任务类型"])["工时"].sum().reset_index()
    pivot = stack_data.pivot(index="日期", columns="任务类型", values="工时").fillna(0).reset_index()
    fig_stack = go.Figure()
    for col_name in pivot.columns:
        if col_name != "日期":
            fig_stack.add_bar(
                x=pivot["日期"], y=pivot[col_name], name=col_name,
                marker_color=TASK_COLORS.get(col_name, "#999999"),
                hovertemplate="%{x|%m-%d}<br>%{y:.1f}h<extra>{col_name}</extra>"
            )
    fig_stack.update_layout(
        barmode="stack", height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="日期", yaxis_title="工时 (h)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_stack, use_container_width=True, config=get_chart_config())

# ---- 热力图 ----
st.subheader("📅 周工时热力图")
df["星期"] = df["日期"].dt.day_name()
df["周数"] = df["日期"].dt.isocalendar().week.astype(int)
week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
week_cn = {"Monday": "周一", "Tuesday": "周二", "Wednesday": "周三", "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"}

heat_data = df.groupby(["周数", "星期"])["工时"].sum().reset_index()
heat_pivot = heat_data.pivot(index="星期", columns="周数", values="工时").reindex(week_order)

all_weeks = list(heat_pivot.columns)
all_days = week_order

z_values = []
text_values = []

for day in all_days:
    z_row = []
    text_row = []
    for week in all_weeks:
        if day in heat_pivot.index and week in heat_pivot.columns:
            val = heat_pivot.loc[day, week] if pd.notna(heat_pivot.loc[day, week]) else 0
        else:
            val = 0
        z_row.append(val if val > 0 else -1)
        text_row.append(f"{val:.1f}h" if val > 0 else "休")
    z_values.append(z_row)
    text_values.append(text_row)

fig_heat = go.Figure(data=go.Heatmap(
    z=z_values,
    x=[f"W{w}" for w in all_weeks],
    y=[week_cn.get(d, d) for d in all_days],
    colorscale=[[0, "#e0e0e0"], [0.01, "#fff7bc"], [0.3, "#fec44f"], [0.6, "#fe9929"], [1, "#d95f0e"]],
    showscale=True,
    text=text_values,
    texttemplate="%{text}",
    hovertemplate="<b>%{y}</b><br>W %{x}<br>%{text}<extra></extra>"
))
fig_heat.update_layout(
    height=250,
    margin=CHART_MARGIN,
    yaxis=dict(autorange="reversed"),
    coloraxis_colorbar=dict(title="工时", tickformat=".0f")
)
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
    task_type = st.selectbox("选择任务类型", df["任务类型"].unique(), key="type_select")
    type_df = df[df["任务类型"] == task_type]
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
# 问题统计
# =====================
st.markdown("---")
st.subheader("📝 问题统计")

if "问题描述" in df.columns:
    df_with_problems = df[df["问题描述"].astype(str).str.strip().str.len() > 0]

    if len(df_with_problems) > 0:
        dev_problem_counts = df_with_problems.groupby("线体/设备").size().sort_values(ascending=True)
        weekly_counts = df_with_problems.groupby(df_with_problems["日期"].dt.isocalendar().week).size()

        col_dev, col_trend = st.columns([1, 1])

        with col_dev:
            st.markdown("**📊 按设备统计**")
            if len(dev_problem_counts) > 0:
                fig_dev = go.Figure(go.Bar(
                    x=dev_problem_counts.values,
                    y=dev_problem_counts.index,
                    orientation="h",
                    marker_color="#4C78A8",
                    text=[f"{v} 个问题" for v in dev_problem_counts.values],
                    textposition="outside"
                ))
                fig_dev.update_layout(
                    height=max(200, 30 * len(dev_problem_counts)),
                    margin=dict(t=10, b=30, l=100, r=50),
                    xaxis_title="问题数量",
                    yaxis=dict(tickfont=dict(size=11))
                )
                st.plotly_chart(fig_dev, use_container_width=True, config=get_chart_config())
            else:
                st.markdown("<i style='color:#888;'>暂无问题记录</i>", unsafe_allow_html=True)

        with col_trend:
            st.markdown("**📈 周趋势**")
            if len(weekly_counts) > 0:
                fig_trend = go.Figure(go.Scatter(
                    x=[f"W{w.item()}" for w in weekly_counts.index],
                    y=weekly_counts.values,
                    mode="lines+markers",
                    marker=dict(size=8, color="#F58518"),
                    line=dict(width=2, color="#F58518"),
                    text=weekly_counts.values,
                    hovertemplate="W %{x}<br>%{y} 个问题<extra></extra>"
                ))
                fig_trend.update_layout(
                    height=max(200, 30 * len(weekly_counts)),
                    margin=dict(t=10, b=30, l=40, r=40),
                    xaxis_title="",
                    yaxis_title="问题数量"
                )
                st.plotly_chart(fig_trend, use_container_width=True, config=get_chart_config())
            else:
                st.markdown("<i style='color:#888;'>暂无趋势数据</i>", unsafe_allow_html=True)
    else:
        st.markdown("<i style='color:#888;'>当前筛选范围内没有问题描述记录</i>", unsafe_allow_html=True)
else:
    st.info("请重新处理数据以生成问题描述字段")

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
