import { proxyActivities } from '@temporalio/workflow';
// Only import the activity types
import pythonActivities from '../activities/cartography';
import { CartographyResult } from '../activities/cartography/types'

const { cartographyRun } = proxyActivities<pythonActivities>({
  startToCloseTimeout: '1 hour',
  taskQueue: 'cartography-wf-activity'
});

export async function runCartographySync(): Promise<CartographyResult> {
  const results = await cartographyRun()
  return results
}