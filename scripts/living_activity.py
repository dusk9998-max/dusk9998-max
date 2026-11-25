"""Read-only repository metadata and owner-authored commit collection.

Nothing in this module writes raw repository metadata or commit identities.
"""
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


class AccessError(ValueError):
    pass


class CommitLedger:
    def __init__(self, login: str, now: datetime):
        self.login, self.now = login.lower(), now
        self.commits = {}
        self.by_repository = Counter()

    def add(self, item: dict, repository: str):
        if (item.get("author") or {}).get("login", "").lower() != self.login:
            return
        sha = item.get("sha", "")
        try:
            when = datetime.fromisoformat(item["commit"]["author"]["date"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            raise AccessError("Invalid commit timestamp.") from None
        if not re.fullmatch(r"[a-f0-9]{40,64}", sha) or when.tzinfo is None or when > self.now:
            raise AccessError("Invalid commit metadata.")
        if sha not in self.commits:
            self.commits[sha] = when
            self.by_repository[repository] += 1

    @property
    def daily(self):
        return dict(Counter(when.date() for when in self.commits.values()))

    @property
    def recent_count(self):
        return sum(self.now - timedelta(days=7) <= when <= self.now for when in self.commits.values())


class GitHubRead:
    def __init__(self, token: str):
        if not isinstance(token, str) or not token.strip():
            raise AccessError("Repository activity credentials are missing.")
        self.token, self.requests = token, 0

    def request(self, path: str, payload=None):
        if not path.startswith("/") or path.startswith("//"):
            raise AccessError("Invalid API path.")
        self.requests += 1
        if self.requests > 4000:
            raise AccessError("Collection exceeds the API budget; previous artwork retained.")
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request("https://api.github.com" + path, data=body, headers={
            "Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
            "Content-Type": "application/json", "User-Agent": "living-paper-dragon",
            "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urlopen(request, timeout=45) as response:
                result = json.load(response)
        except HTTPError as error:
            raise AccessError(f"GitHub repository API returned HTTP {error.code}.") from None
        except (OSError, ValueError):
            # Do not echo response bodies, request URLs or authorization headers.
            raise AccessError("Repository metadata could not be read; verify access and API limits.") from None
        if isinstance(result, dict) and result.get("errors"):
            raise AccessError("Partial GitHub response; previous artwork retained.")
        return result

    def pages(self, path: str, params=None):
        for page in range(1, 4001):
            query = dict(params or {}, per_page=100, page=page)
            rows = self.request(path + "?" + urlencode(query))
            if not isinstance(rows, list):
                raise AccessError("Invalid paginated response.")
            yield from rows
            if len(rows) < 100:
                return
        raise AccessError("Incomplete pagination.")

    def languages(self, full_name: str):
        owner, name = full_name.split("/")
        query = """query($owner:String!,$name:String!,$after:String) {
          repository(owner:$owner,name:$name) { languages(first:100,after:$after) {
            edges { size node { name color } } pageInfo { hasNextPage endCursor }
          } }
        }"""
        after, languages = None, {}
        while True:
            result = self.request("/graphql", {"query": query, "variables": {
                "owner": owner, "name": name, "after": after}})
            connection = result["data"]["repository"]["languages"]
            for edge in connection["edges"]:
                language, size = edge["node"], edge["size"]
                color = language["color"] or "#888888"
                if (not isinstance(language["name"], str) or len(language["name"]) > 100
                        or not re.fullmatch(r"#[a-fA-F0-9]{6}", color)
                        or type(size) is not int or size < 0):
                    raise AccessError("Invalid language metadata.")
                languages[language["name"]] = (size, color)
            if not connection["pageInfo"]["hasNextPage"]:
                return languages
            cursor = connection["pageInfo"]["endCursor"]
            if not cursor or cursor == after:
                raise AccessError("Incomplete language pagination.")
            after = cursor


def collect_repositories(login: str, credentials: str, now: datetime):
    try:
        tokens = json.loads(credentials)
    except (ValueError, TypeError):
        raise AccessError("Set DRAGON_REPO_TOKENS to a JSON array of read-only tokens.") from None
    if not isinstance(tokens, list) or not tokens or len(tokens) > 20:
        raise AccessError("Repository credentials must contain 1–20 owner tokens.")
    repositories = {}
    for token in tokens:
        client = GitHubRead(token)
        if client.request("/user").get("login", "").lower() != login.lower():
            raise AccessError("Every repository token must belong to the profile owner.")
        for repo in client.pages("/user/repos", {"affiliation": "owner,collaborator,organization_member"}):
            full_name = repo.get("full_name", "")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", full_name):
                raise AccessError("Invalid repository metadata.")
            repositories.setdefault(full_name.lower(), (repo, client))
    ledger, weights, colors = CommitLedger(login, now), Counter(), {}
    private_verified = False
    # Prefer original repositories when the same authored commit also exists in forks.
    for full_name, (repo, client) in sorted(repositories.items(), key=lambda row: (row[1][0].get("fork", False), row[0])):
        if repo.get("size") == 0:
            continue
        path = "/repos/" + full_name
        for branch in client.pages(path + "/branches"):
            name = branch.get("name")
            if not isinstance(name, str) or not name:
                raise AccessError("Invalid branch metadata.")
            for commit in client.pages(path + "/commits", {
                    "sha": name, "author": login, "until": now.isoformat()}):
                ledger.add(commit, full_name)
            if repo.get("private"):
                private_verified = True
        authored = ledger.by_repository[full_name]
        if authored:
            languages = client.languages(full_name)
            total = sum(size for size, _ in languages.values())
            for name, (size, color) in languages.items():
                weights[name] += authored * size / max(1, total)
                colors[name] = color
    if not private_verified:
        raise AccessError("No nonempty private repository was verified; refusing public-only collection.")
    palette = [{"name": name, "color": colors[name], "weight": weight}
               for name, weight in weights.most_common(4) if weight > 0]
    # Only aggregate values cross into the model; commit SHAs and repository names
    # remain ephemeral within this collector.
    return {"daily": ledger.daily, "total": len(ledger.commits),
            "recent": ledger.recent_count, "palette": palette}
