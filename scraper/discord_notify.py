from __future__ import annotations

import os
from datetime import date

from scraper.diff import DiffResult


def send_discord_notification(diff: DiffResult, pages_url: str = "") -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[discord] DISCORD_WEBHOOK_URL not set, skipping notification")
        return

    from discord_webhook import DiscordWebhook, DiscordEmbed

    today = date.today().strftime("%Y-%m-%d")

    embed = DiscordEmbed(
        title=f"Weekly Robotics Job Update ({today})",
        color="3264d6",
    )

    if diff.new_jobs:
        new_lines = []
        for j in diff.new_jobs[:15]:
            line = f"[{j.company}] [{j.title}]({j.url})"
            if j.experience:
                line += f" — {j.experience}"
            new_lines.append(line)
        if len(diff.new_jobs) > 15:
            new_lines.append(f"... and {len(diff.new_jobs) - 15} more")
        embed.add_embed_field(
            name=f"NEW ({len(diff.new_jobs)})",
            value="\n".join(new_lines),
            inline=False,
        )

    if diff.closed_jobs:
        closed_lines = []
        for j in diff.closed_jobs[:10]:
            closed_lines.append(f"[{j.company}] {j.title}")
        if len(diff.closed_jobs) > 10:
            closed_lines.append(f"... and {len(diff.closed_jobs) - 10} more")
        embed.add_embed_field(
            name=f"CLOSED ({len(diff.closed_jobs)})",
            value="\n".join(closed_lines),
            inline=False,
        )

    if diff.reopened_jobs:
        reopen_lines = [f"[{j.company}] [{j.title}]({j.url})" for j in diff.reopened_jobs[:5]]
        embed.add_embed_field(
            name=f"REOPENED ({len(diff.reopened_jobs)})",
            value="\n".join(reopen_lines),
            inline=False,
        )

    summary = f"Total active: **{diff.total_active}** | New: +{len(diff.new_jobs)} | Closed: -{len(diff.closed_jobs)}"
    if pages_url:
        summary += f"\n[View full report]({pages_url})"
    embed.add_embed_field(name="Summary", value=summary, inline=False)

    embed.set_footer(text="Robotics Job Tracker | github.com")
    embed.set_timestamp()

    webhook = DiscordWebhook(url=webhook_url, rate_limit_retry=True)
    webhook.add_embed(embed)
    resp = webhook.execute()

    if resp and hasattr(resp, "status_code"):
        print(f"[discord] Sent notification (status {resp.status_code})")
    else:
        print("[discord] Notification sent")
