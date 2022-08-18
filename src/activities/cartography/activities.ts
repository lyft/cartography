import { str } from '@temporalio/common';
import { CartographyResult } from './types'
import { promisify } from 'util'

let {PythonShell} = require('python-shell')
const pythonShellRun = promisify(PythonShell.run)

var options = {
  mode: 'text',
  args: ['--neo4j-uri', 'bolt://localhost:7687', '--neo4j-user', 'neo4j', '--neo4j-password-env-var', 'NEO4J_PASSWORD', '--permission-relationships-file', 'cartography/permissions_mapping_file.yaml', '--aws-best-effort-mode', '--aws-requested-syncs', 'dynamodb,s3_list_only']
};

export async function cartographyRun(): Promise<CartographyResult> {
  console.log("reached the execution stage")
  try {
    const result = await pythonShellRun('cartography/__main__.py', options)
    console.log("completed")
    return {"result": "0"}
  } catch (err) {
    console.log(err)
    return {"result": str(err)}
  }
}