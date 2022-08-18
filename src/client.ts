import { Connection, WorkflowClient } from '@temporalio/client';
import { nanoid } from 'nanoid'
import { runSync } from './workflows/workflows';

async function run() {
  const connection = await Connection.connect();
  const client = new WorkflowClient({ connection });

  const handle = await client.start(runSync, {
    taskQueue: 'cartography-wf',
    workflowId: `cartography-wf-${ nanoid() }`
  });
  console.log(`Started workflow ${handle.workflowId}`);

  const result = await handle.result()
  console.log('Result:', result);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});