import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from living_activity import CommitLedger, AccessError, GitHubRead, collect_repositories
from unittest.mock import patch


class LedgerTests(unittest.TestCase):
    def commit(self, sha="a" * 40, login="dusk9998-max", when="2026-11-16T12:00:00Z"):
        return {"sha": sha, "author": {"login": login},
                "commit": {"author": {"date": when}}}

    def test_private_working_branch_and_fork_duplicates_count_once(self):
        ledger = CommitLedger("dusk9998-max", datetime(2026, 11, 16, 14, tzinfo=timezone.utc))
        ledger.add(self.commit(), "repo-one")
        ledger.add(self.commit(), "fork")
        self.assertEqual(len(ledger.commits), 1)
        self.assertEqual(ledger.recent_count, 1)

    def test_today_is_included_and_other_authors_are_excluded(self):
        ledger = CommitLedger("dusk9998-max", datetime(2026, 11, 16, 14, tzinfo=timezone.utc))
        ledger.add(self.commit(), "repo")
        ledger.add(self.commit("b" * 40, "someone-else"), "repo")
        self.assertEqual(sum(ledger.daily.values()), 1)

    def test_future_and_malformed_commits_fail(self):
        ledger = CommitLedger("dusk9998-max", datetime(2026, 11, 16, 14, tzinfo=timezone.utc))
        for item in (self.commit("bad"), self.commit(when="2026-11-17T00:00:00Z")):
            with self.assertRaises(AccessError):
                ledger.add(item, "repo")

    def test_pagination_reads_beyond_first_hundred(self):
        client = GitHubRead("fixture-only")
        with patch.object(client, "request", side_effect=[[{}] * 100, [{}]]) as request:
            self.assertEqual(len(list(client.pages("/user/repos"))), 101)
            self.assertIn("page=2", request.call_args.args[0])

    def test_private_branch_collection_and_language_weighting(self):
        now = datetime(2026, 11, 16, 14, tzinfo=timezone.utc)
        def pages(client, path, params=None):
            if path == "/user/repos":
                return iter([{"full_name": "org/private", "private": True, "size": 1}])
            if path.endswith("/branches"):
                return iter([{"name": "main"}, {"name": "working"}])
            return iter([] if params["sha"] == "main" else [self.commit()])
        with patch.object(GitHubRead, "request", return_value={"login": "dusk9998-max"}), \
             patch.object(GitHubRead, "pages", pages), \
             patch.object(GitHubRead, "languages", return_value={"Python": (100, "#3572A5")}):
            result = collect_repositories("dusk9998-max", '["fixture-only"]', now)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["recent"], 1)
        self.assertEqual(result["palette"][0]["name"], "Python")
        self.assertNotIn("org/private", repr(result))

    def test_api_failure_does_not_return_partial_activity(self):
        now = datetime(2026, 11, 16, 14, tzinfo=timezone.utc)
        with patch.object(GitHubRead, "request", return_value={"login": "dusk9998-max"}), \
             patch.object(GitHubRead, "pages", side_effect=AccessError("fixture failure")):
            with self.assertRaises(AccessError):
                collect_repositories("dusk9998-max", '["fixture-only"]', now)

    def test_wrong_owner_and_public_only_coverage_fail(self):
        now = datetime(2026, 11, 16, 14, tzinfo=timezone.utc)
        with patch.object(GitHubRead, "request", return_value={"login": "other"}):
            with self.assertRaises(AccessError):
                collect_repositories("dusk9998-max", '["fixture-only"]', now)
        with patch.object(GitHubRead, "request", return_value={"login": "dusk9998-max"}):
            with patch.object(GitHubRead, "pages", return_value=iter([])):
                with self.assertRaises(AccessError):
                    collect_repositories("dusk9998-max", '["fixture-only"]', now)


if __name__ == "__main__":
    unittest.main()
