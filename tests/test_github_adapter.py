#!/usr/bin/env python3
"""Tests for adapters/github/adapter, driven through a stub `gh` on PATH.

No network, no live repo: the stub records every argv it is handed and
replays canned responses, so a test can assert exactly which calls the
adapter makes and in what order. That is the property that matters here —
worklog #235 was not a wrong output, it was a call that happened at the
wrong moment.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADAPTER = os.path.join(ROOT, "adapters", "github", "adapter")

# A stub `gh`. Appends its argv to $GH_CALLS as one JSON line per call, then
# looks up a response in $GH_RESPONSES keyed by the first two argv words:
# {"<key>": {"out": "...", "rc": 0}}. Unmatched calls succeed with empty
# stdout, which is what the best-effort label/milestone calls expect.
STUB = r"""#!/usr/bin/env python3
import json, os, sys
argv = sys.argv[1:]
with open(os.environ["GH_CALLS"], "a") as fh:
    fh.write(json.dumps(argv) + "\n")
table = json.load(open(os.environ["GH_RESPONSES"]))
for n in (2, 1):
    r = table.get(" ".join(argv[:n]))
    if r:
        sys.stdout.write(r.get("out", ""))
        sys.stderr.write(r.get("err", ""))
        sys.exit(r.get("rc", 0))
sys.exit(0)
"""

CREATED = {"number": 412, "html_url": "https://github.com/o/r/issues/412",
           "updated_at": "2026-07-28T12:00:00Z"}


class AdapterSandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="worklog-ghadapter-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        binp = os.path.join(self.dir, "bin")
        os.makedirs(binp)
        stub = os.path.join(binp, "gh")
        with open(stub, "w", encoding="utf-8") as fh:
            fh.write(STUB)
        os.chmod(stub, 0o755)
        self.calls = os.path.join(self.dir, "calls.jsonl")
        self.responses = os.path.join(self.dir, "responses.json")
        self.env = dict(os.environ,
                        PATH=binp + os.pathsep + os.environ["PATH"],
                        GH_CALLS=self.calls, GH_RESPONSES=self.responses,
                        WORKLOG_TICKET_PROJECT="o/r")

    def set_responses(self, table):
        with open(self.responses, "w", encoding="utf-8") as fh:
            json.dump(table, fh)

    def push(self, req):
        return subprocess.run([sys.executable, ADAPTER, "push"],
                              input=json.dumps(req), capture_output=True,
                              text=True, env=self.env)

    def gh_calls(self):
        if not os.path.exists(self.calls):
            return []
        with open(self.calls, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def mutations(self):
        """Calls that create an issue — the ones that must happen exactly once."""
        return [c for c in self.gh_calls()
                if (c[:1] == ["api"] and c[1:2] == ["repos/o/r/issues"])
                or c[:2] == ["issue", "create"]]


def create_req(**over):
    req = {"op": "create", "key": None, "marker": "<!-- worklog:01A -->",
           "item": {"id": "01A", "title": "File me", "status": "todo",
                    "level": "task", "kind": "bug", "priority": "P1"}}
    req.update(over)
    return req


class TestCreateIsASingleCall(AdapterSandbox):
    """worklog #235: the rev was read by a SECOND call, after the issue
    already existed. A rate limit there exits 4, the dispatcher retries the
    whole push with op still 'create', and each retry files another issue."""

    def test_create_reads_no_issue_afterwards(self):
        self.set_responses({"api repos/o/r/issues": {"out": json.dumps(CREATED)}})
        p = self.push(create_req())
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        resp = json.loads(p.stdout)
        self.assertEqual(resp["key"], "412")
        self.assertEqual(resp["url"], CREATED["html_url"])
        self.assertEqual(resp["rev"], CREATED["updated_at"])
        # The regression: no read-back of any kind after the write.
        self.assertEqual([c for c in self.gh_calls() if c[:2] == ["issue", "view"]],
                         [], "create still reads the issue back after making it")
        self.assertEqual(len(self.mutations()), 1)

    def test_a_rate_limited_read_cannot_duplicate_the_issue(self):
        # Every `issue view` is rate limited. Before the fix this exited 4
        # with the issue already filed, which is what made the dispatcher
        # retry the create.
        self.set_responses({
            "api repos/o/r/issues": {"out": json.dumps(CREATED)},
            "issue view": {"rc": 1, "err": "API rate limit exceeded"},
        })
        p = self.push(create_req())
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(json.loads(p.stdout)["rev"], CREATED["updated_at"])

    def test_create_carries_title_body_and_labels(self):
        self.set_responses({"api repos/o/r/issues": {"out": json.dumps(CREATED)}})
        self.assertEqual(self.push(create_req()).returncode, 0)
        (call,) = self.mutations()
        self.assertIn("title=File me", call)
        body = next(a for a in call if a.startswith("body="))
        self.assertIn("<!-- worklog:01A -->", body)   # the idempotency marker
        labels = {a[len("labels[]="):] for a in call if a.startswith("labels[]=")}
        self.assertEqual(labels, {"worklog", "level:task", "kind:bug", "bug", "P1"})

    def test_a_failed_create_reports_the_transient_code_and_files_nothing(self):
        # Failing BEFORE the mutation is the case where a retry is correct.
        self.set_responses({"api repos/o/r/issues":
                            {"rc": 1, "err": "API rate limit exceeded"}})
        p = self.push(create_req())
        self.assertEqual(p.returncode, 4, p.stdout + p.stderr)  # contract §3.6
        self.assertEqual(p.stdout, "")


class TestUpdateStillReadsTheRev(AdapterSandbox):
    def test_update_edits_then_reads_and_a_retry_is_idempotent(self):
        """The update path keeps the second read on purpose: re-editing the
        same issue costs a call, not a duplicate."""
        self.set_responses({
            "issue edit": {"out": ""},
            "issue view": {"out": json.dumps({"updatedAt": "2026-07-28T13:00:00Z"})},
        })
        p = self.push(create_req(op="update", key="412"))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        resp = json.loads(p.stdout)
        self.assertEqual(resp["key"], "412")
        self.assertEqual(resp["rev"], "2026-07-28T13:00:00Z")
        self.assertEqual(self.mutations(), [], "update filed a new issue")


class TestResponseMatchesTheContract(AdapterSandbox):
    def test_push_response_validates_against_the_schema(self):
        with open(os.path.join(ROOT, "schema", "adapter-io.schema.json"),
                  encoding="utf-8") as fh:
            spec = json.load(fh)["properties"]["push_response"]
        self.set_responses({"api repos/o/r/issues": {"out": json.dumps(CREATED)}})
        resp = json.loads(self.push(create_req()).stdout)
        for field in spec["required"]:
            self.assertIn(field, resp)
        # `rev` is a required STRING -- which is why #235 could not be fixed
        # by simply reporting a null rev when the read-back failed.
        self.assertIsInstance(resp["rev"], str)
        self.assertIsInstance(resp["key"], str)
        self.assertIsInstance(resp["url"], str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
