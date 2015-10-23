import Queue
import datetime
import json
import logging
import os
import socket
import time
import traceback

from opentsdb_sender import TSDBSender
from django.conf import settings

from collect_utils import METRIC_TSDB_TASK_TYPE
from collect_utils import QueueTask

sender = TSDBSender(settings.TSDB_ADDR)
logger = logging.getLogger(__name__)

def send_metrics_to_tsdb(output_queue, data):
  global sender
  try:
    start_time = time.time()
    if data:
      metrics = json.loads(data)
      timestamp = metrics['timestamp']
      for endpoint, group_metrics in metrics['data'].iteritems():
        for group, key_metrics in group_metrics.iteritems():
          for key, metric in key_metrics.iteritems():
            value = metric['value']
            message = "%s %s %s host=%s group=%s\n" % (key, timestamp, value, endpoint, group) 
            #print 'send data: %s' % message
            sender.SendData(message)

    logger.info("spent %f seconds for sending metrics to tsdb",
      time.time() - start_time)
  except Exception, e:
    logger.warning("failed to send metrics: %r", e)
    traceback.print_exc()
  finally:
    # just put the corresponding metric_source id back to the output queue
    output_queue.put(QueueTask(METRIC_TSDB_TASK_TYPE, None))
