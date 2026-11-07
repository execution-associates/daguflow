from daguflow import SubDAG, dag, task


@task
def top_ids(api: str, limit: int) -> list:
    import json, urllib.request
    with urllib.request.urlopen(f"{api}/topstories.json", timeout=10) as r:
        return json.load(r)[:limit]


@task(retries=3)
def story(api: str, story_id: int) -> dict:
    import json, urllib.request
    with urllib.request.urlopen(f"{api}/item/{story_id}.json", timeout=10) as r:
        s = json.load(r)
    return {"title": s["title"], "score": s["score"], "kids": s.get("kids", [])}


@task(retries=3)
def first_comment(api: str, story: dict) -> dict:
    import html, json, re, urllib.request
    text = ""
    for kid in story["kids"][:1]:
        with urllib.request.urlopen(f"{api}/item/{kid}.json", timeout=10) as r:
            text = html.unescape(re.sub(r"<[^>]+>", " ", json.load(r).get("text", "")))
    return {"title": story["title"], "score": story["score"], "comment": " ".join(text.split())[:200]}


@task
def threads(stories: list) -> str:
    best = sorted(stories, key=lambda s: -s["score"])
    return "\n\n".join(f"{s['title']} ({s['score']})\n  > {s['comment'] or 'no comments yet'}" for s in best)


@dag
def hn_threads(limit: int = 10, api: str = "https://hacker-news.firebaseio.com/v0"):
    """Each top story with its first comment: two steps per story, four stories at a time."""
    ids = top_ids(api, limit)
    with SubDAG("thread", items=ids, as_="story_id", params={"api": api}, max_concurrent=4) as thread:
        s = story(thread.params.api, thread.params.story_id)
        first_comment(thread.params.api, s)
    threads(thread.results)
