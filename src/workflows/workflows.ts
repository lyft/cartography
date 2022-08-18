import { proxyActivities } from '@temporalio/workflow';
// Only import the activity types
import type * as activities from '../activities/cartography';
import { CartographyResult } from '../activities/cartography/types'

const { cartographyRun } = proxyActivities<typeof activities>({
  startToCloseTimeout: '1 hour',
  taskQueue: 'cartography-wf-activity'
});

export async function runSync(): Promise<CartographyResult> {
  const results = await cartographyRun()
  return results
}