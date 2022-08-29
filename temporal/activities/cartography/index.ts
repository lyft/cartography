import { CartographyResult } from './types'

// Interfaces for activities implemented by Python workers
type activities = {
  cartographyRun: () => Promise<CartographyResult>
}

export default activities;