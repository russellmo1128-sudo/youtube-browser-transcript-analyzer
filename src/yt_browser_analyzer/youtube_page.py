from __future__ import annotations

from typing import Any

from playwright.sync_api import Page

from .numbers import parse_count_text


def _to_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_page_payload(page: Page) -> dict[str, Any]:
    payload = page.evaluate(
        """
        () => {
          const playerResponse = window.ytInitialPlayerResponse
            || (window.ytplayer?.config?.args?.raw_player_response
              ? JSON.parse(window.ytplayer.config.args.raw_player_response)
              : null)
            || null;
          const initialData = window.ytInitialData || {};
          const videoDetails = playerResponse?.videoDetails || {};
          const microformat = playerResponse?.microformat?.playerMicroformatRenderer || {};
          const tracklist = playerResponse?.captions?.playerCaptionsTracklistRenderer || null;
          const tracks = (tracklist?.captionTracks || []).map(track => ({
            baseUrl: track.baseUrl || null,
            name: track.name?.simpleText || (track.name?.runs || []).map(run => run.text).join(''),
            languageCode: track.languageCode || '',
            kind: track.kind || null,
            isTranslatable: !!track.isTranslatable
          }));

          const textOf = (value) => {
            if (!value) return null;
            if (typeof value === 'string') return value;
            if (value.simpleText) return value.simpleText;
            if (Array.isArray(value.runs)) return value.runs.map(run => run.text || '').join('');
            return null;
          };

          let showEndpoint = null;
          let continuationEndpoint = null;
          const queue = [initialData];
          const seen = new Set();
          while (queue.length) {
            const current = queue.pop();
            if (!current || typeof current !== 'object') continue;
            if (seen.has(current)) continue;
            seen.add(current);

            const transcriptRenderer = current.videoDescriptionTranscriptSectionRenderer;
            const candidateShow = transcriptRenderer?.primaryButton?.buttonRenderer
              ?.command?.commandExecutorCommand?.commands?.[0]?.showEngagementPanelEndpoint;
            if (!showEndpoint && candidateShow) showEndpoint = candidateShow;

            if (!continuationEndpoint
                && current.getTranscriptEndpoint
                && current.commandMetadata?.webCommandMetadata?.apiUrl === '/youtubei/v1/get_transcript') {
              continuationEndpoint = current;
            }

            for (const value of Object.values(current)) {
              if (value && typeof value === 'object') queue.push(value);
            }
          }

          return {
            pageUrl: location.href,
            documentTitle: document.title,
            videoId: videoDetails.videoId || null,
            title: videoDetails.title || microformat.title?.simpleText || document.title,
            channel: videoDetails.author || microformat.ownerChannelName || null,
            channelId: videoDetails.channelId || microformat.externalChannelId || null,
            channelUrl: microformat.ownerProfileUrl || null,
            durationSeconds: videoDetails.lengthSeconds ? Number(videoDetails.lengthSeconds) : null,
            shortDescription: videoDetails.shortDescription || microformat.description?.simpleText || null,
            keywords: videoDetails.keywords || [],
            isLiveContent: !!videoDetails.isLiveContent,
            publishDate: microformat.publishDate || null,
            uploadDate: microformat.uploadDate || null,
            category: microformat.category || null,
            viewCount: videoDetails.viewCount || microformat.viewCount || null,
            tracks,
            showEndpoint,
            continuationEndpoint,
          };
        }
        """
    )
    if not payload.get("videoId"):
        raise RuntimeError("The YouTube watch page did not expose a usable videoId.")
    return payload


def collect_public_metrics(page: Page, page_payload: dict[str, Any], settle_ms: int) -> dict[str, Any]:
    # Comments are lazy-loaded. A short scroll gives YouTube a chance to render the header.
    page.wait_for_timeout(settle_ms)
    for _ in range(6):
        if page.locator("ytd-comments-header-renderer").count() > 0:
            break
        page.evaluate("() => window.scrollBy(0, Math.max(window.innerHeight, 900))")
        page.wait_for_timeout(settle_ms)

    visible = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim() || null;
          const textOf = (value) => {
            if (!value) return null;
            if (typeof value === 'string') return clean(value);
            if (value.simpleText) return clean(value.simpleText);
            if (Array.isArray(value.runs)) return clean(value.runs.map(run => run.text || '').join(''));
            if (value.content) return textOf(value.content);
            if (value.text) return textOf(value.text);
            if (value.title) return textOf(value.title);
            return null;
          };
          const pickText = (selectors) => {
            for (const selector of selectors) {
              const node = document.querySelector(selector);
              const text = clean(node?.textContent);
              if (text) return text;
            }
            return null;
          };
          const pickAttr = (selectors, attr) => {
            for (const selector of selectors) {
              const node = document.querySelector(selector);
              const text = clean(node?.getAttribute(attr));
              if (text) return text;
            }
            return null;
          };

          const likeCandidates = [
            pickAttr(['like-button-view-model button', '#segmented-like-button button'], 'aria-label'),
            pickText(['like-button-view-model button', '#segmented-like-button button'])
          ].filter(Boolean);

          const structured = {
            subscriberTexts: [],
            commentTexts: [],
            likeTexts: [],
            viewTexts: []
          };
          const queue = [window.ytInitialData || {}];
          const seen = new Set();
          while (queue.length) {
            const current = queue.pop();
            if (!current || typeof current !== 'object') continue;
            if (seen.has(current)) continue;
            seen.add(current);
            for (const [key, value] of Object.entries(current)) {
              const lower = key.toLowerCase();
              const text = textOf(value);
              if (text) {
                if (lower.includes('subscriber')) structured.subscriberTexts.push(text);
                if (lower.includes('commentcount') || lower === 'commentcount') structured.commentTexts.push(text);
                if (lower.includes('likecount')) structured.likeTexts.push(text);
                if (lower.includes('viewcount')) structured.viewTexts.push(text);
              }
              if (value && typeof value === 'object') queue.push(value);
            }
          }

          return {
            channelNameText: pickText([
              'ytd-watch-metadata #owner ytd-channel-name a',
              'ytd-video-owner-renderer ytd-channel-name a'
            ]),
            subscriberCountText: pickText([
              '#owner-sub-count',
              'yt-formatted-string#owner-sub-count',
              'ytd-video-owner-renderer #owner-sub-count'
            ]),
            commentCountText: pickText([
              'ytd-comments-header-renderer #count',
              'ytd-comments-header-renderer h2',
              '#comments #count'
            ]) || structured.commentTexts[0] || null,
            likeText: likeCandidates[0] || null,
            visibleViewText: pickText([
              'ytd-watch-info-text #info span',
              'ytd-video-view-count-renderer span',
              '#info-text span'
            ]) || structured.viewTexts[0] || null,
            structuredSubscriberText: structured.subscriberTexts[0] || null,
            structuredLikeText: structured.likeTexts[0] || null
          };
        }
        """
    )

    view_count_raw = page_payload.get("viewCount")
    view_count_value = _to_int(view_count_raw)
    if view_count_value is None:
        view_count_value = parse_count_text(visible.get("visibleViewText"))

    return {
        "schema_version": "1.0",
        "source": "youtube_watch_page_public_data",
        "page_url": page_payload.get("pageUrl"),
        "video": {
            "video_id": page_payload.get("videoId"),
            "title": page_payload.get("title"),
            "duration_seconds": page_payload.get("durationSeconds"),
            "publish_date": page_payload.get("publishDate"),
            "upload_date": page_payload.get("uploadDate"),
            "category": page_payload.get("category"),
            "is_live_content": page_payload.get("isLiveContent"),
            "keywords": page_payload.get("keywords") or [],
            "view_count": {
                "raw": view_count_raw or visible.get("visibleViewText"),
                "value": view_count_value,
                "source": "player_response.videoDetails.viewCount"
                if view_count_raw
                else "visible_page_text",
            },
        },
        "channel": {
            "name": page_payload.get("channel") or visible.get("channelNameText"),
            "channel_id": page_payload.get("channelId"),
            "url": page_payload.get("channelUrl"),
            "subscriber_count": {
                "raw": visible.get("subscriberCountText") or visible.get("structuredSubscriberText"),
                "approx_value": parse_count_text(
                    visible.get("subscriberCountText") or visible.get("structuredSubscriberText")
                ),
                "source": "visible_page_text",
            },
        },
        "engagement": {
            "comment_count": {
                "raw": visible.get("commentCountText"),
                "approx_value": parse_count_text(visible.get("commentCountText")),
                "source": "visible_page_text",
            },
            "like_count": {
                "raw": visible.get("likeText") or visible.get("structuredLikeText"),
                "approx_value": parse_count_text(
                    visible.get("likeText") or visible.get("structuredLikeText")
                ),
                "source": "visible_page_text",
            },
        },
        "caption_tracks": page_payload.get("tracks") or [],
        "notes": [
            "View count from player response is usually more stable than visible page text.",
            "Subscriber, like, and comment counts are locale-dependent visible text and may be approximate.",
            "Comment count can be missing if YouTube does not render comments in the browser session.",
        ],
    }


def build_metadata(input_url: str, requested_video_id: str, page_payload: dict[str, Any]) -> dict[str, Any]:
    tracks = page_payload.get("tracks") or []
    return {
        "schema_version": "1.0",
        "status": "ready",
        "input_url": input_url,
        "requested_video_id": requested_video_id,
        "page_url": page_payload["pageUrl"],
        "video_id": page_payload["videoId"],
        "title": page_payload["title"],
        "channel": page_payload.get("channel"),
        "channel_id": page_payload.get("channelId"),
        "channel_url": page_payload.get("channelUrl"),
        "duration_seconds": page_payload.get("durationSeconds"),
        "language": tracks[0]["languageCode"] if tracks else None,
        "description": page_payload.get("shortDescription"),
        "publish_date": page_payload.get("publishDate"),
        "upload_date": page_payload.get("uploadDate"),
        "category": page_payload.get("category"),
        "keywords": page_payload.get("keywords") or [],
        "notes": [],
    }
