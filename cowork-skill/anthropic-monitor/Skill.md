---
name: "AI News Monitor"
description: "Checks Anthropic's news and research pages for new posts and summarizes them in chat."
---

# AI News Monitor Skill

You check Anthropic's public news and research pages for new posts, summarize what you find, and report directly in chat. No API keys or GitHub access needed — you fetch public web pages directly.

## When to Use This Skill

Use this skill when the user asks to:
- Check for new AI announcements
- Check for new posts from Anthropic
- What's new on Anthropic's blog
- Run the news monitor
- Any recent Anthropic research or news

## Steps to Execute

1. **Fetch the Anthropic news page** — GET request to:
   ```
   https://www.anthropic.com/news
   ```

2. **Fetch the Anthropic research page** — GET request to:
   ```
   https://www.anthropic.com/research
   ```

3. **Extract post links and titles** — Look for all links matching the pattern `/news/` or `/research/` in the page content. Each post has a title and URL.

4. **Fetch and summarize the top 3-5 most recent posts** that you haven't already summarized in this conversation:
   - GET each post URL
   - Write a 2-3 sentence summary: what was announced, why it matters, and any key details

5. **Report back** with:
   - A numbered list of new posts found (title + URL)
   - A brief summary for each one
   - The date checked (today's date)

## Format for Response

```
## Anthropic News Check — [DATE]

### New Posts Found

**1. [Post Title]**
[URL]
> [2-3 sentence summary]

**2. [Post Title]**
[URL]
> [2-3 sentence summary]

---
*Checked anthropic.com/news and anthropic.com/research*
```

## Notes

- If you can't fetch a page, say so clearly and suggest the user check manually.
- Focus on posts from the last 30 days if dates are visible.
- For email delivery of these updates, the full monitor at github.com/obizues/anthropic-monitor runs on a cron schedule and sends formatted emails to subscribers.
