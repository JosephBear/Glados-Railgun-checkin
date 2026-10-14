"""Check workflow safety without executing a workflow or reading secrets."""

from pathlib import Path
import unittest

import yaml


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


class WorkflowTests(unittest.TestCase):
    def read_workflow(self, name):
        return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)

    def test_every_workflow_is_a_mapping_with_triggers_and_jobs(self):
        for path in WORKFLOWS.glob("*.yml"):
            with self.subTest(path=path.name):
                workflow = self.read_workflow(path.name)
                self.assertIsInstance(workflow, dict)
                self.assertIn("on", workflow)
                self.assertIn("jobs", workflow)

    def test_live_checkin_only_runs_on_schedule_or_explicit_dispatch(self):
        workflow = self.read_workflow("gladosCheck.yml")
        self.assertEqual(set(workflow["on"]), {"schedule", "workflow_dispatch"})

    def test_push_to_master_runs_only_offline_tests(self):
        workflow = self.read_workflow("main.yml")
        self.assertIsInstance(workflow, dict)
        self.assertEqual(workflow["on"]["push"]["branches"], ["master"])
        contents = (WORKFLOWS / "main.yml").read_text()
        self.assertNotIn("secrets.", contents)
        self.assertNotIn("python checkin.py", contents)
        self.assertIn("python -m unittest discover -s tests -v", contents)

    def test_exchange_defaults_to_false_in_workflow(self):
        workflow = self.read_workflow("gladosCheck.yml")
        steps = workflow["jobs"]["build"]["steps"]
        run_step = next(step for step in steps if step.get("name") == "Running checkin")
        self.assertEqual(run_step["env"].get("GLADOS_AUTO_EXCHANGE"), "${{ vars.GLADOS_AUTO_EXCHANGE || 'false' }}")

    def test_keepalive_runs_even_when_checkin_fails(self):
        workflow = self.read_workflow("gladosCheck.yml")
        steps = workflow["jobs"]["build"]["steps"]
        keepalive = next(step for step in steps if step.get("name") == "Keep alive")
        self.assertEqual(keepalive.get("if"), "${{ always() }}")


if __name__ == "__main__":
    unittest.main()
