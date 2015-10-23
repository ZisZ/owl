
METRIC_TASK_TYPE = "Metric"
METRIC_TSDB_TASK_TYPE = "Metric-Tsdb"
STATUS_TASK_TYPE = "Status"
AGGREGATE_TASK_TYPE = "Aggregate"

class QueueTask:
  def __init__(self, task_type, task_data):
    self.task_type = task_type
    self.task_data = task_data



