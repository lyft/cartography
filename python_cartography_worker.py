import asyncio
from datetime import datetime, timedelta
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker
import argparse
from cartography import cli

@activity.defn(name="cartographyRun")
async def cartography_python():
  # default result
  results = {}
  result = cli.main()
  if result == 0:
    results['result'] = "Sync completed successfully"
  else:
    results['result'] = "Error while sync"
  return results

async def main():
  # Create client connected to server at the given address
  client = await Client.connect("http://localhost:7233")

  # Run the worker
  worker = Worker(client, task_queue="cartography-wf-activity", activities=[cartography_python])
  await worker.run()

if __name__ == "__main__":
  asyncio.run(main())