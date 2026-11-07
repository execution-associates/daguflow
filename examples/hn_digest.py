from daguflow import ITEM, Cron, SubDAG, dag, task


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
    return {"title": s["title"], "score": s["score"], "comments": s.get("descendants", 0)}


@task
def digest(stories: list, min_score: int) -> str:
    hot = sorted((s for s in stories if s["score"] >= min_score), key=lambda s: -s["score"])
    return "\n".join(f"{s['score']:>5}  {s['title']}" for s in hot)


@dag(schedule=Cron("0 8 * * *"))
def hn_digest(limit: int = 30, min_score: int = 100, api: str = "https://hacker-news.firebaseio.com/v0"):
    """This morning's Hacker News, best first."""
    ids = top_ids(api, limit)
    with SubDAG("fetch", items=ids.output, max_concurrent=8,
                params={"story_id": ITEM, "api": api}) as fetch:
        story(fetch.params.api, fetch.params.story_id)
    digest(fetch.results, min_score)
