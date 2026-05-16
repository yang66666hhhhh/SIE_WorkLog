import pandas as pd
import plotly.graph_objects as go

COLORS_MAP = {"MSAP": "#4C78A8", "HDI二处": "#F58518"}
TASK_COLORS = {
    "调试": "#4C78A8", "联调": "#4C78A8", "配置": "#F58518",
    "学习": "#E45756", "分析": "#72B7B2", "其他": "#54A24B",
    "协助": "#9D7559", "培训": "#B279A2",
}
CHART_HEIGHT = 280
CHART_MARGIN = dict(t=15, b=20, l=30, r=30)


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


def create_daily_bar_chart(df, colors_map=None):
    colors = colors_map or COLORS_MAP
    daily = df.groupby(["日期", "来源"])["工时"].sum().reset_index()
    fig = go.Figure()
    for src_name, grp in daily.groupby("来源"):
        fig.add_bar(
            x=grp["日期"], y=grp["工时"], name=src_name,
            marker_color=colors.get(src_name, "#999999"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>%{y:.1f}h<extra>" + src_name + "</extra>"
        )
    fig.update_layout(
        barmode="group", height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="工时 (h)",
        hovermode="x unified"
    )
    return fig


def create_task_pie_chart(df, task_colors=None):
    colors = task_colors or TASK_COLORS
    type_data = df.groupby("任务类型")["工时"].sum().reset_index().sort_values("工时", ascending=False)
    pie_colors = ["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#9D7559", "#B279A2"]
    fig = go.Figure(data=[go.Pie(
        labels=type_data["任务类型"], values=type_data["工时"], hole=0.4,
        marker_colors=pie_colors,
        textinfo="percent",
        hovertemplate="%{label}<br>%{percent}<br>%{value:.1f}h<extra></extra>"
    )])
    fig.update_layout(
        height=CHART_HEIGHT, margin=CHART_MARGIN,
        annotations=[dict(text=f"{type_data['工时'].sum():.0f}h", x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    return fig


def create_device_bar_chart(df, colors_map=None):
    colors = colors_map or COLORS_MAP
    dev_data = df.groupby(["线体/设备", "来源"])["工时"].sum().reset_index().sort_values("工时", ascending=True)
    fig = go.Figure()
    for src_name, grp in dev_data.groupby("来源"):
        fig.add_bar(
            y=grp["线体/设备"], x=grp["工时"], orientation="h", name=src_name,
            marker_color=colors.get(src_name, "#999999"),
            text=grp["工时"].apply(lambda x: f"{x:.1f}h"),
            textposition="outside",
            hovertemplate="%{y}<br>%{x:.1f}h<extra>" + src_name + "</extra>"
        )
    fig.update_layout(
        barmode="group", height=CHART_HEIGHT,
        margin=dict(t=15, b=20, l=100, r=30), xaxis_title="工时 (h)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="closest"
    )
    return fig


def create_stack_bar_chart(df, task_colors=None):
    colors = task_colors or TASK_COLORS
    stack_data = df.groupby(["日期", "任务类型"])["工时"].sum().reset_index()
    pivot = stack_data.pivot(index="日期", columns="任务类型", values="工时").fillna(0).reset_index()
    fig = go.Figure()
    for col_name in pivot.columns:
        if col_name != "日期":
            fig.add_bar(
                x=pivot["日期"], y=pivot[col_name], name=col_name,
                marker_color=colors.get(col_name, "#999999"),
                hovertemplate="%{x|%m-%d}<br>%{y:.1f}h<extra>" + col_name + "</extra>"
            )
    fig.update_layout(
        barmode="stack", height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="日期", yaxis_title="工时 (h)",
        hovermode="x unified"
    )
    return fig


def create_heatmap(df):
    week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    week_cn = {
        "Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
        "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"
    }

    df_heat = df.copy()
    df_heat["星期"] = df_heat["日期"].dt.day_name()
    df_heat["周数"] = df_heat["日期"].dt.isocalendar().week.astype(int)

    heat_data = df_heat.groupby(["周数", "星期"])["工时"].sum().reset_index()
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

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=[f"W{w}" for w in all_weeks],
        y=[week_cn.get(d, d) for d in all_days],
        colorscale=[[0, "#e0e0e0"], [0.01, "#fff7bc"], [0.3, "#fec44f"], [0.6, "#fe9929"], [1, "#d95f0e"]],
        showscale=True,
        text=text_values,
        texttemplate="%{text}",
        hovertemplate="<b>%{y}</b><br>W %{x}<br>%{text}<extra></extra>"
    ))
    fig.update_layout(
        height=250,
        margin=CHART_MARGIN,
        yaxis=dict(autorange="reversed"),
        coloraxis_colorbar=dict(title="工时", tickformat=".0f")
    )
    return fig
