#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import WorkflowEngine
async def main():
    print("Workflow Engine Demo")
    e = WorkflowEngine()
    wf = e.create_workflow("Test")
    e.add_step(wf.workflow_id, "s1", "Step 1", "noop")
    e.add_step(wf.workflow_id, "s2", "Step 2", "noop", ["s1"])
    r = await e.run(wf.workflow_id)
    print(f"Status: {r['status']}")
    print("Done!")
if __name__ == "__main__": import asyncio; asyncio.run(main())
