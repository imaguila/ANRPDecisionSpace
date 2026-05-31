import plotly.express as px
import plotly.graph_objects as go


def scatter_plot(df, x, y, color=None, show_ids=False):

    fig = px.scatter(df, x=x, y=y, color=color)

    if show_ids and "id" in df.columns:
        fig.update_traces(text=df["id"], textposition="top center")

    return fig


def radar_plot(df, metrics):

    fig = go.Figure()

    for _, row in df.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row[m] for m in metrics],
            theta=metrics,
            fill='toself',
            name=f"ID {int(row['id'])}" if "id" in row else "solution"
        ))

    return fig