#
# Assumption drift detection based on baseline and intel service graph data
#
# Author: Sacha Faust (sfaust@lyft.com)
#
from enum import IntEnum


class DriftDetectorType(IntEnum):
    EXPOSURE = 1
