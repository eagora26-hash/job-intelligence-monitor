"""Configuration page: toggle sources, tune scheduling/filters/notifications — no code edits.

Writes changes to the gitignored ``.env`` via the whitelisted writer (secrets are never
touched). Because :class:`Settings` is cached per process, changes apply on the next
run/restart — the page says so explicitly.
"""

from __future__ import annotations

import streamlit as st

from job_monitor.config.env_file import update_env_file
from job_monitor.config.keywords import DEFAULT_KEYWORDS
from job_monitor.dashboard.components import DashboardContext


def render(ctx: DashboardContext) -> None:
    st.subheader("⚙️ Configuration")
    s = ctx.settings

    st.caption(
        "Changes are saved to `.env` and take effect on the next scrape run / app restart. "
        "Secrets (Telegram token) are never editable here."
    )

    token_state = "✅ configured" if s.telegram_configured else "⚠️ not set"
    st.info(f"Telegram: **{token_state}** · notifications "
            f"**{'enabled' if s.notify_enabled else 'disabled'}**")

    with st.form("config"):
        st.markdown("#### Sources")
        cols = st.columns(5)
        toggles = {
            "ENABLE_REMOTEOK": cols[0].toggle("RemoteOK", value=s.enable_remoteok),
            "ENABLE_WWR": cols[1].toggle("WeWorkRemotely", value=s.enable_wwr),
            "ENABLE_FREELANCER": cols[2].toggle("Freelancer", value=s.enable_freelancer),
            "ENABLE_FIVERR": cols[3].toggle("Fiverr", value=s.enable_fiverr),
            "ENABLE_WELLFOUND": cols[4].toggle("Wellfound", value=s.enable_wellfound),
        }

        st.markdown("#### Scheduling & notifications")
        c1, c2, c3 = st.columns(3)
        polling = c1.number_input("Polling interval (s)", min_value=60, value=int(s.polling_interval), step=60)
        notify_enabled = c2.toggle("Notifications enabled", value=s.notify_enabled)
        notify_min = c3.number_input("Notify min score", min_value=0, value=int(s.notify_min_score))

        st.markdown("#### Keyword filters")
        include = st.text_area(
            "Include keywords (comma-separated; blank = default taxonomy)",
            value=", ".join(s.include_keywords),
            help="Defaults: " + ", ".join(DEFAULT_KEYWORDS[:8]) + ", …",
        )
        exclude = st.text_area("Exclude keywords (comma-separated)", value=", ".join(s.exclude_keywords))

        saved = st.form_submit_button("💾 Save to .env", width="stretch")

    if saved:
        updates = {key: ("true" if val else "false") for key, val in toggles.items()}
        updates["POLLING_INTERVAL"] = str(int(polling))
        updates["NOTIFY_ENABLED"] = "true" if notify_enabled else "false"
        updates["NOTIFY_MIN_SCORE"] = str(int(notify_min))
        updates["INCLUDE_KEYWORDS"] = ",".join(k.strip() for k in include.split(",") if k.strip())
        updates["EXCLUDE_KEYWORDS"] = ",".join(k.strip() for k in exclude.split(",") if k.strip())
        try:
            env_path = ctx.settings.project_root / ".env"
            update_env_file(env_path, updates)
            st.success("Saved to .env. Restart the app / next run picks up the changes.")
        except ValueError as exc:
            st.error(f"Could not save: {exc}")
