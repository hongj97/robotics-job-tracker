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
        color=0x3264d6,
    )

    if diff.new_jobs:
        new_lines = []
        char_count = 0
        shown = 0
        for j in diff.new_jobs:
            line = f"**{j.company}** — {j.title}"
            if char_count + len(line) + 1 > 900:
                break
            new_lines.append(line)
            char_count += len(line) + 1
            shown += 1
        remaining = len(diff.new_jobs) - shown
        if remaining > 0:
            new_lines.append(f"*... and {remaining} more*")
        embed.add_embed_field(
            name=f"NEW +{len(diff.new_jobs)}",
            value="\n".join(new_lines) or "—",
            inline=False,
        )

    if diff.closed_jobs:
        closed_lines = []
        char_count = 0
        shown = 0
        for j in diff.closed_jobs:
            line = f"~~{j.company} — {j.title}~~"
            if char_count + len(line) + 1 > 900:
                break
            closed_lines.append(line)
            char_count += len(line) + 1
            shown += 1
        remaining = len(diff.closed_jobs) - shown
        if remaining > 0:
            closed_lines.append(f"*... and {remaining} more*")
        embed.add_embed_field(
            name=f"CLOSED -{len(diff.closed_jobs)}",
            value="\n".join(closed_lines) or "—",
            inline=False,
        )

    if diff.reopened_jobs:
        reopen_lines = [f"**{j.company}** — {j.title}" for j in diff.reopened_jobs[:5]]
        embed.add_embed_field(
            name=f"REOPENED {len(diff.reopened_jobs)}",
            value="\n".join(reopen_lines) or "—",
            inline=False,
        )

    summary = f"Total active: **{diff.total_active}** | New: +{len(diff.new_jobs)} | Closed: -{len(diff.closed_jobs)}"
    if pages_url:
        summary += f"\n[View full report]({pages_url})"
    embed.add_embed_field(name="Summary", value=summary, inline=False)

    embed.set_footer(text="Robotics Job Tracker")
    embed.set_timestamp()

    webhook = DiscordWebhook(url=webhook_url, rate_limit_retry=True)
    webhook.add_embed(embed)

    try:
        resp = webhook.execute()
        if resp and hasattr(resp, "status_code"):
            print(f"[discord] Sent notification (status {resp.status_code})")
            if resp.status_code >= 400:
                print(f"[discord] Error response: {resp.text}")
        else:
            print("[discord] Notification sent")
    except Exception as e:
        print(f"[discord] Failed to send: {e}")
