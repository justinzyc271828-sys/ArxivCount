"""Streamlit dashboard for ArxivCount."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from .config import load_milestones, load_settings
    from .paths import ROOT, resolve
except ImportError:  # pragma: no cover - streamlit direct path
    from src.config import load_milestones, load_settings
    from src.paths import ROOT, resolve


st.set_page_config(
    page_title="ArxivCount · AI Math Proofs",
    page_icon="∫",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_stats(stats_dir: str) -> dict:
    d = Path(stats_dir)
    out: dict = {}
    monthly = d / "monthly_counts.csv"
    yearly = d / "yearly_counts.csv"
    cats = d / "category_counts.csv"
    growth = d / "monthly_growth.csv"
    summary = d / "summary.json"
    top = d / "top_papers.csv"
    milestones = d / "milestones.json"

    out["monthly"] = pd.read_csv(monthly) if monthly.exists() else pd.DataFrame()
    out["yearly"] = pd.read_csv(yearly) if yearly.exists() else pd.DataFrame()
    out["categories"] = pd.read_csv(cats) if cats.exists() else pd.DataFrame()
    out["growth"] = pd.read_csv(growth) if growth.exists() else pd.DataFrame()
    out["top"] = pd.read_csv(top) if top.exists() else pd.DataFrame()

    if summary.exists():
        out["summary"] = json.loads(summary.read_text(encoding="utf-8"))
    else:
        out["summary"] = {}

    if milestones.exists():
        out["milestones"] = json.loads(milestones.read_text(encoding="utf-8"))
    else:
        out["milestones"] = load_milestones()
    return out


def add_milestones(fig: go.Figure, milestones: list[dict], y_max: float) -> go.Figure:
    for m in milestones:
        date = m.get("date")
        if not date:
            continue
        fig.add_vline(
            x=date,
            line_width=1,
            line_dash="dot",
            line_color="rgba(180,80,80,0.7)",
        )
        fig.add_annotation(
            x=date,
            y=y_max,
            text=m.get("label", m.get("id", "")),
            showarrow=False,
            textangle=-90,
            yanchor="top",
            font=dict(size=10, color="rgba(120,40,40,0.9)"),
            xanchor="right",
        )
    return fig


def main() -> None:
    settings = load_settings()
    project = settings.get("project", {})
    stats_dir = resolve(settings["paths"]["stats_dir"])

    st.title(project.get("title", "ArxivCount"))
    st.caption(
        f"Proxy dashboard for AI-related mathematical work on arXiv · "
        f"[{project.get('github', '')}]({project.get('github', '')}) · "
        f"[{project.get('website', '')}]({project.get('website', '')})"
    )

    data = load_stats(str(stats_dir))
    summary = data["summary"]
    monthly: pd.DataFrame = data["monthly"]
    yearly: pd.DataFrame = data["yearly"]
    cats: pd.DataFrame = data["categories"]
    top: pd.DataFrame = data["top"]
    milestones = data["milestones"]

    if not summary or summary.get("total_candidates", 0) == 0:
        st.warning(
            "还没有统计数据。请先运行：\n\n"
            "```bash\n"
            "python -m src.collect --max-per-query 50\n"
            "python -m src.aggregate\n"
            "python -m src.curate\n"
            "```"
        )
        st.info(f"数据目录: `{stats_dir}`（相对于 `{ROOT}`）")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Candidates", summary.get("total_candidates", 0))
    by_level = summary.get("by_level") or {}
    c2.metric("L1+", sum(by_level.get(k, 0) for k in ("L1", "L2", "L3")))
    c3.metric("L2/L3 formal-ish", by_level.get("L2", 0) + by_level.get("L3", 0))
    c4.metric("Writing-only demoted", summary.get("writing_only", 0))

    st.subheader("Monthly trend (loose + scored)")
    if not monthly.empty:
        y_max = float(monthly["count"].max() or 1)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=monthly["year_month"],
                y=monthly["count"],
                mode="lines+markers",
                name="All candidates",
                line=dict(width=2),
            )
        )
        for level, color in [
            ("L0", "#a0a0a0"),
            ("L1", "#4c78a8"),
            ("L2", "#f58518"),
            ("L3", "#e45756"),
        ]:
            if level in monthly.columns:
                fig.add_trace(
                    go.Bar(
                        x=monthly["year_month"],
                        y=monthly[level],
                        name=level,
                        marker_color=color,
                        opacity=0.55,
                    )
                )
        fig.update_layout(
            barmode="stack",
            xaxis_title="Month",
            yaxis_title="Papers",
            legend_title="Series",
            height=480,
            margin=dict(l=40, r=20, t=30, b=40),
        )
        # milestone lines need datetime-ish x; year_month strings still work as categories
        for m in milestones:
            fig.add_vline(
                x=m["date"][:7] if len(m.get("date", "")) >= 7 else m.get("date"),
                line_width=1,
                line_dash="dot",
                line_color="rgba(120,40,40,0.55)",
                annotation_text=m.get("label", ""),
                annotation_position="top",
                annotation_textangle=-90,
                annotation_font_size=9,
            )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No monthly data.")

    left, right = st.columns(2)
    with left:
        st.subheader("Yearly totals")
        if not yearly.empty:
            fig_y = px.bar(yearly, x="year", y="count", title=None)
            fig_y.update_layout(height=360, margin=dict(l=20, r=20, t=10, b=20))
            st.plotly_chart(fig_y, use_container_width=True)
        by = summary.get("by_level") or {}
        if by:
            st.write("Level mix:", by)

    with right:
        st.subheader("Top primary categories")
        if not cats.empty:
            fig_c = px.bar(
                cats.head(15),
                x="count",
                y="primary_category",
                orientation="h",
            )
            fig_c.update_layout(
                height=360,
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=20, r=20, t=10, b=20),
            )
            st.plotly_chart(fig_c, use_container_width=True)

    st.subheader("Milestones")
    for m in milestones:
        st.markdown(
            f"- **{m.get('date')}** — {m.get('label')}  \n"
            f"  <span style='color:#666'>{m.get('note','')}</span>",
            unsafe_allow_html=True,
        )

    st.subheader("Top papers (local cache)")
    if not top.empty:
        show = top.copy()
        if "arxiv_id" in show.columns:
            show["link"] = show["arxiv_id"].map(lambda x: f"https://arxiv.org/abs/{x}")
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.write("No top papers file yet.")

    deep_summary_path = resolve(settings["paths"]["curated_dir"]) / "deep_audit_summary.json"
    deep_yearly_role = resolve(settings["paths"]["stats_dir"]) / "deep_yearly_role.csv"
    deep_yearly_sub = resolve(settings["paths"]["stats_dir"]) / "deep_yearly_subfield.csv"
    if deep_summary_path.exists():
        st.subheader("Deep audit (DeepSeek second pass)")
        deep = json.loads(deep_summary_path.read_text(encoding="utf-8"))
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Deep confirmed", deep.get("confirmed", 0))
        d2.metric("Demoted on re-check", deep.get("demoted", 0))
        d3.metric("Open-problem linked", deep.get("open_problem_count", 0))
        d4.metric("Mean audit conf.", f"{float(deep.get('mean_audit_confidence') or 0):.2f}")

        c_left, c_right = st.columns(2)
        with c_left:
            roles = deep.get("by_primary_ai_role") or {}
            if roles:
                rdf = pd.DataFrame(
                    {"role": list(roles.keys()), "count": list(roles.values())}
                ).sort_values("count", ascending=True)
                fig_r = px.bar(rdf, x="count", y="role", orientation="h", title="Primary AI role")
                fig_r.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_r, use_container_width=True)
        with c_right:
            subs = deep.get("by_subfield") or {}
            if subs:
                sdf = (
                    pd.DataFrame({"subfield": list(subs.keys()), "count": list(subs.values())})
                    .sort_values("count", ascending=True)
                    .tail(12)
                )
                fig_s = px.bar(sdf, x="count", y="subfield", orientation="h", title="Math subfields")
                fig_s.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_s, use_container_width=True)

        if deep_yearly_role.exists():
            yrole = pd.read_csv(deep_yearly_role)
            if not yrole.empty:
                fig_yr = px.bar(
                    yrole,
                    x="year",
                    y="count",
                    color="primary_ai_role",
                    title="Year × AI role",
                    barmode="stack",
                )
                fig_yr.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_yr, use_container_width=True)

        if deep_yearly_sub.exists():
            ysub = pd.read_csv(deep_yearly_sub)
            if not ysub.empty:
                top_subs = (
                    ysub.groupby("primary_subfield")["count"].sum().nlargest(8).index.tolist()
                )
                ysub2 = ysub[ysub["primary_subfield"].isin(top_subs)]
                fig_ys = px.bar(
                    ysub2,
                    x="year",
                    y="count",
                    color="primary_subfield",
                    title="Year × subfield (top 8)",
                    barmode="stack",
                )
                fig_ys.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_ys, use_container_width=True)

        ops = deep.get("open_problems") or []
        if ops:
            st.markdown("**Open-problem linked (sample)**")
            st.dataframe(pd.DataFrame(ops).head(30), use_container_width=True, hide_index=True)
        st.caption("Full narrative: docs/deep_audit_report.md")

    # Contribution tiers (strict impact)
    contrib_summary = resolve(settings["paths"]["curated_dir"]) / "contribution_summary.json"
    contrib_yearly = resolve(settings["paths"]["stats_dir"]) / "contribution_yearly_tier.csv"
    dual_yearly = resolve(settings["paths"]["stats_dir"]) / "contribution_wide_vs_strict_yearly.csv"
    if contrib_summary.exists():
        st.subheader("Contribution tiers (C0–C4)")
        cs = json.loads(contrib_summary.read_text(encoding="utf-8"))
        a, b, c, d = st.columns(4)
        a.metric("Graded", cs.get("n", 0))
        b.metric("Wide (C2+)", cs.get("wide_n", 0))
        c.metric("Strict (C3+)", cs.get("strict_n", 0))
        d.metric("C4 / milestone-ish", cs.get("c4_or_milestone_n", 0))
        by_tier = cs.get("by_tier") or {}
        if by_tier:
            tdf = pd.DataFrame({"tier": list(by_tier.keys()), "count": list(by_tier.values())})
            tdf = tdf.sort_values("tier")
            fig_t = px.bar(tdf, x="tier", y="count", title="Tier mix (fulltext-graded)")
            fig_t.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_t, use_container_width=True)
        if dual_yearly.exists():
            dual = pd.read_csv(dual_yearly)
            if not dual.empty:
                melt = dual.melt(id_vars=["year"], value_vars=[c for c in ("wide", "strict") if c in dual.columns],
                                 var_name="set", value_name="count")
                fig_d = px.line(melt, x="year", y="count", color="set", markers=True,
                                title="Wide vs strict impact sets by year")
                fig_d.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_d, use_container_width=True)
        if contrib_yearly.exists():
            cy = pd.read_csv(contrib_yearly)
            if not cy.empty:
                fig_cy = px.bar(cy, x="year", y="count", color="contribution_tier",
                                title="Year × contribution tier", barmode="stack")
                fig_cy.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_cy, use_container_width=True)
        st.caption("C0 noise · C1 writing · C2 assistive · C3 material · C4 decisive/open-problem")

    # Penetration
    pen_csv = resolve(settings["paths"]["stats_dir"]) / "penetration_yearly.csv"
    if pen_csv.exists():
        st.subheader("Penetration vs math.* totals")
        pen = pd.read_csv(pen_csv)
        st.dataframe(pen, use_container_width=True, hide_index=True)
        if not pen.empty and "strict_per_10k" in pen.columns:
            fig_p = px.line(
                pen,
                x="year",
                y=["wide_per_10k", "strict_per_10k"],
                markers=True,
                title="Per 10,000 math.* papers (API totals)",
            )
            fig_p.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_p, use_container_width=True)
        st.caption(
            "Denominator: arXiv API cat:math* by calendar year. "
            "2026 is partial-year. Rates are disclosed-proxy lower bounds."
        )

    # Timeline
    timeline_path = resolve(settings["paths"]["stats_dir"]) / "timeline.json"
    highlights_path = resolve(settings["paths"]["stats_dir"]) / "timeline_highlights.json"
    if timeline_path.exists():
        st.subheader("Timeline & milestone works")
        tl = json.loads(timeline_path.read_text(encoding="utf-8"))
        st.markdown(
            f"Events: **{tl.get('counts', {}).get('paper_events', 0)}** papers · "
            f"**{tl.get('counts', {}).get('canon_milestones', 0)}** canon milestones · "
            f"**{tl.get('counts', {}).get('highlights', 0)}** highlights"
        )
        for ph in tl.get("phases") or []:
            with st.expander(
                f"{ph.get('label')} ({ph.get('start')} → {ph.get('end')}) · "
                f"papers={ph.get('paper_events')} strict~{ph.get('strict_like')}"
            ):
                st.write(ph.get("note") if "note" in ph else "")
                highs = ph.get("highlights") or []
                if highs:
                    st.dataframe(pd.DataFrame(highs)[
                        [c for c in ["date", "label", "contribution_tier", "arxiv_id", "url"] if c in pd.DataFrame(highs).columns]
                    ], use_container_width=True, hide_index=True)
        if highlights_path.exists():
            highs = json.loads(highlights_path.read_text(encoding="utf-8"))
            if highs:
                st.markdown("**Highlight cards (canon + C4 / milestone candidates)**")
                hdf = pd.DataFrame(highs)
                cols = [c for c in ["date", "type", "label", "contribution_tier", "arxiv_id", "url", "note"] if c in hdf.columns]
                st.dataframe(hdf[cols].head(40), use_container_width=True, hide_index=True)
        st.caption("Narrative timeline: docs/timeline.md")

    with st.expander("Method notes / limitations"):
        st.markdown(
            """
            - **Pipeline**: loose collect → refine → fulltext audit → **C0–C4 contribution grading**.
            - **Wide set** = C2+ (ecosystem); **Strict set** = C3+ (material math impact claims).
            - Full text is head+tail extract; not a human gold standard.
            - Seed queries ≠ all of math.*; treat as observable disclosed AI-for-math proxy.
            - Canon milestones are curated anchors; paper highlights are model-graded.
            """
        )


if __name__ == "__main__":
    main()
