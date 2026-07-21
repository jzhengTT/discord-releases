# discord-releases

Posts new releases from the [Planet Tenstorrent releases feed](https://docs.tenstorrent.com/tt-awesome/planet/) to a Discord channel, on a schedule, via GitHub Actions.

- Feed: `https://docs.tenstorrent.com/tt-awesome/feeds/releases.xml`
- Each release becomes one embed (title, link, summary, timestamp)
- Already-posted releases are tracked in `state/seen.json`, which the workflow commits back to the repo — no duplicates
- On the very first run the state file is empty, so the entire feed backlog is posted (oldest first, rate-limited)

## Setup

### 1. Create the Discord webhook

In your Discord server: **#releases channel → Edit Channel → Integrations → Webhooks → New Webhook**, then copy the webhook URL.

### 2. Test locally (optional)

```sh
pip install -r requirements.txt
cp .env.example .env   # paste your webhook URL into .env
export $(cat .env) && python post_releases.py
```

The first run posts every release currently in the feed. Running it again immediately should print `posted 0 new release(s)`.

### 3. Set up GitHub Actions

```sh
git init && git add -A && git commit -m "Initial commit"
gh repo create discord-releases --private --source . --push
gh secret set DISCORD_WEBHOOK_URL   # paste the webhook URL when prompted
```

Then trigger the first run manually:

```sh
gh workflow run post-releases.yml
```

After that it runs automatically every 30 minutes. When new releases are posted, the workflow commits the updated `state/seen.json` back to the repo.

## Notes

- To skip the initial backlog instead of posting it, seed `state/seen.json` with all current entry IDs before the first run.
- Discord webhooks are rate-limited (~30 messages/min); the script paces itself and honors `Retry-After` on 429s.
