# FUMIST Studio

A web video editor with a timeline, real FFmpeg MP4 exports, optional CPU speech transcription, a Telegram Mini App and a separate administrator bot. Uzbek, Russian and English interfaces; dark, light and system themes.

## Features implemented

- Upload videos, images and audio; per-account private media access.
- Trim, split, reorder (drag or buttons), duplicate and remove clips.
- Playback speed 0.25-4?, rotation, mirror, fit/crop, volume and mute.
- Brightness, contrast, saturation, seven color looks, fade in/out.
- Text overlays with timing, size, color and position.
- Subtitle editing, SRT import/export and burned-in subtitles.
- Up to three music/voiceover tracks with offset, source trim, volume and loop.
- Browser microphone voiceover recording (up to two minutes).
- 16:9, 9:16, 1:1 and 4:5 formats; 24/30 fps; 720p/1080p exports.
- Undo/redo, device drafts, account project saving and project JSON import/export.
- Six starting templates that set format, filter and title; add your own footage.
- Queued server renders and download history.
- Silence detection/removal and optional faster-whisper auto captions.
- Authenticated accounts, scrypt password hashes, opaque HttpOnly sessions, origin checks, quotas and server-enforced plan limits.
- Two Telegram bots: user bot / Mini App and administrator review bot.

## Subscription contract

| Plan | Price | Video limit | Exports / rolling 24h | Clips | Analyses / rolling 24h |
| --- | ---: | ---: | ---: | ---: | ---: |
| Free | 0 | 2 minutes, 720p | 3 | 10 | 1 |
| Plus | 15,000 UZS | 10 minutes, 1080p | 15 | 30 | 5 |
| Pro | 40,000 UZS | 20 minutes, 1080p | 40 | 60 | 15 |

Free exports include a FUMIST watermark. Plus and Pro remove it and unlock cinema/vintage looks. AI captions require the optional AI service to be enabled, regardless of quota.

**Uploading a receipt NEVER activates a subscription. Only an administrator whose numeric Telegram ID is in `ADMIN_IDS` can approve an order in the administrator bot.** The subscription starts at the approval instant and ends one calendar month later, at the same UTC time. Month-end dates clamp to the last day of the next month (January 31  February 28/29). Approval is atomic and cannot run twice. Expired access resolves to Free on every authenticated request, including export requests. A new approved purchase starts a new one-month period from its approval; unused time is not stacked.

### Payments

- Standalone website: show the configured card number and cardholder; user uploads JPG/PNG/PDF receipt; administrator reviews it against their bank statement and approves or rejects.
- Telegram bot / Mini App: digital subscriptions must use Telegram Stars. Set separate Stars prices. A successful Stars transaction goes to `paid_review`, **still without activation**, until administrator approval. Stars rejection does not itself refund the payment; use `/refund ORDER_ID` in the admin bot.
- `BILLING_ENABLED=false` by default. Payments remain unavailable until tokens, admin IDs, card details and prices are configured.
- Sources: [Telegram digital payments](https://core.telegram.org/bots/payments-stars), [Mini Apps](https://core.telegram.org/bots/webapps).

## Railway deployment

1. Deploy this repository as one Dockerfile service, **one replica**.
2. Attach a persistent volume at `/data` **before enabling accounts or billing**. SQLite, uploads, receipts, exports and downloaded AI models are kept there.
3. Set `DATA_DIR=/data` and `PUBLIC_URL` to the generated HTTPS domain.
4. Configure the variables below. Two separate bots are created using [@BotFather](https://t.me/BotFather); their polling loops run in this same service, so no extra Railway service is required.
5. In BotFather, set the user bot's Main Mini App / menu-button URL to `PUBLIC_URL`. The bot also provides an inline Mini App launch button on `/start`.
6. Start both bots once from your personal Telegram account. An administrator bot cannot deliver messages to an account that has never started it.
7. Enable billing only after testing with a real administrator account. Set prices in Stars before offering purchases inside Telegram.

| Variable | Purpose |
| --- | --- |
| `BOT_TOKEN` | User bot token. Secret; enter only in Railway Variables. |
| `BOT_USERNAME` | User bot username without @. |
| `ADMIN_BOT_TOKEN` | Separate administrator bot token. Secret. |
| `ADMIN_IDS` | Comma-separated numeric Telegram user IDs allowed to review. |
| `CARD_NUMBER` | Public receiving card number; never CVV, PIN or expiry. |
| `CARD_HOLDER` | Cardholder name as displayed for transfers. |
| `BILLING_ENABLED` | `true` when ready to accept payments. |
| `PUBLIC_URL` | Service HTTPS URL, no trailing slash. |
| `DATA_DIR` | `/data`, backed by the persistent volume. |
| `PLUS_PRICE_UZS` / `PRO_PRICE_UZS` | Defaults: `15000` / `40000`. |
| `PLUS_PRICE_STARS` / `PRO_PRICE_STARS` | Defaults: `0` (Stars sales disabled). |
| `ENABLE_AI_TRANSCRIPTION` | `true` to allow CPU auto captions; default false. |
| `WHISPER_MODEL` | Default `base`. Initial use downloads model files. |
| `SUPPORT_USERNAME` | Default `ferapmg`. |
| `MAX_UPLOAD_MB` | Default `200` per file. Receipts capped at 10 MB. |
| `STORAGE_QUOTA_MB` | Default `1000` uploaded media per account. |
| `RETENTION_DAYS` | Default `30` for media and exported video. |

Use at least 2 GB RAM for CPU auto captions; larger models and source videos may need more. Run only one replica: the durable SQLite queue and two bot polling consumers are deliberately single-instance. Render tasks run one at a time. This is a working initial product, not feature parity with CapCut or a horizontally scaled production architecture. Test representative phones, browsers and source codecs before broad release.

## Administrator bot

- `/stats`: user, active subscription, pending payment and job counts.
- `/pending`: pending orders and receipt documents with Approve / Reject buttons.
- `/block USER_ID` and `/unblock USER_ID`: account moderation.
- `/refund ORDER_ID`: refund a Stars transaction and revoke only that order's entitlement.
- Actions are restricted to `ADMIN_IDS` and logged in the audit table. There is no public HTTP approval endpoint.

## Development and tests

The core application runs on Python 3.12's standard library. FFmpeg and FFprobe must be on PATH for upload inspection, exports and silence analysis. Auto captions additionally require `pip install -r requirements.txt` and model downloads.

```sh
python server.py
python -m unittest discover -v
node --check static/app.js
```

Open `http://localhost:8080`. The Docker build installs FFmpeg, the speech package and fonts, then runs the tests including a real codec integration test (video + image + music + timed text + subtitles  vertical MP4).

Known limits: browser preview approximates some color/fade/audio settings; the exported FFmpeg result is authoritative. Auto transcription quality, especially Uzbek, must be checked manually. Render tasks interrupted by a deploy fail visibly and can be restarted. Media is private but uploaded to the service for processing; keep backups of important originals. Receipts and transaction records should be backed up with the volume. Forgotten-password recovery is via support in this initial release.

