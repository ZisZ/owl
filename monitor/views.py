# -*- coding: utf-8 -*-
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, Context, loader
from django.utils import timezone
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction

import datetime
import dbutil
import json
import metric_helper
import time

class Namespace:
  def __init__(self, **kwargs):
    for name, value in kwargs.iteritems():
      setattr(self, name, value)


def index(request):
  # show all cluster
  clusters = dbutil.get_clusters_by_service()
  service = Namespace(name="all services")
  params = {
    'service': service,
    'clusters': clusters,
  }
  return respond(request, 'monitor/service.html', params)


#url: /service/$id/
def show_service(request, id):
  service = dbutil.get_service(id)
  clusters = dbutil.get_clusters_by_service(id)
  params = {
    'service': service,
    'clusters': clusters,
  }
  if service.name == 'hbase':

    tsdb_read_query = []
    tsdb_write_query = []
    for cluster in clusters:
      tsdb_read_query.append(metric_helper.make_metric_query(cluster.name, 'Cluster', 'readRequestsCountPerSec'))
      tsdb_write_query.append(metric_helper.make_metric_query(cluster.name, 'Cluster', 'writeRequestsCountPerSec'))

    params.update({
      'tsdb_read_query': tsdb_read_query,
      'tsdb_write_query': tsdb_write_query,
    })

    return respond(request, 'monitor/hbase_service.html', params)
  else:
    return respond(request, 'monitor/service.html', params)

#url: /cluster/$id/
def show_cluster(request, id):
  # return task board by default
  return redirect('/monitor/cluster/%s/task/' % id)

#url: /cluster/$id/task/
def show_cluster_task_board(request, id):
  cluster = dbutil.get_cluster(id)
  tasks = dbutil.get_tasks_by_cluster(id)
  params = {'cluster': cluster,
            'tasks': tasks}
  if cluster.service.name == 'hdfs':
    return respond(request, 'monitor/hdfs_task_board.html', params)
  elif cluster.service.name == 'hbase':
    return respond(request, 'monitor/hbase_task_board.html', params)
  else:
    return respond(request, 'monitor/cluster.html', params)

#url: /cluster/$id/table/
def show_cluster_table_board(request, id):
  cluster = dbutil.get_cluster(id)
  if cluster.service.name != 'hbase':
    # return empty paget for unsupported service
    return HttpResponse('')
  read_requests_dist_by_table, write_requests_dist_by_table = dbutil.get_requests_distribution_groupby(cluster, 'table');
  params = {
    'chart_id': 'read_requests_on_table',
    'chart_title': 'read requests on table',
    'request_dist': read_requests_dist_by_table,
    'base_url': '/monitor/table/',
  }

  read_requests_dist_by_table_chart = loader.get_template('monitor/requests_dist_pie_chart.tpl').render(Context(params))

  params = {
    'chart_id': 'write_requests_on_table',
    'chart_title': 'write requests on table',
    'request_dist': write_requests_dist_by_table,
    'base_url': '/monitor/table/',
  }
  write_requests_dist_by_table_chart = loader.get_template('monitor/requests_dist_pie_chart.tpl').render(
    Context(params))

  tables = dbutil.get_items_on_cluster(cluster, 'table', order_by='-qps')
  system_tables = [table for table in tables if is_system_table(table)]
  user_tables = [table for table in tables if not is_system_table(table)]

  table_read_item_keys = '|'.join(['%s-readRequestsCountPerSec' % (table.name) for table in user_tables])
  table_write_item_keys ='|'.join(['%s-writeRequestsCountPerSec' % (table.name) for table in user_tables])

  tsdb_read_query = []
  tsdb_write_query = []
  for table in user_tables:
    tsdb_read_query.append(metric_helper.make_metric_query(cluster.name, table.name, 'readRequestsCountPerSec'))
    tsdb_write_query.append(metric_helper.make_metric_query(cluster.name, table.name, 'writeRequestsCountPerSec'))

  params = {
    'cluster': cluster,
    'read_requests_dist_by_table_chart': read_requests_dist_by_table_chart,
    'write_requests_dist_by_table_chart': write_requests_dist_by_table_chart,
    'system_tables': system_tables,
    'user_tables': user_tables,
    'table_read_item_keys': table_read_item_keys,
    'table_write_item_keys': table_write_item_keys,
    'tsdb_read_query': tsdb_read_query,
    'tsdb_write_query': tsdb_write_query,
  }
  return respond(request, 'monitor/hbase_table_board.html', params)

def is_system_table(table):
  system_table_names = ('-ROOT-', '.META.', '_acl_')
  return table.name in system_table_names

#url: /cluster/$id/basic/
def show_cluster_basic_board(request, id):
  cluster = dbutil.get_cluster(id)
  if cluster.service.name != 'hbase':
    # return empty paget for unsupported service
    return HttpResponse('')

  basic_info = dbutil.get_hbase_basic_info(cluster)

  group = 'Cluster'
  tsdb_read_query = [metric_helper.make_metric_query(cluster.name, group, 'readRequestsCountPerSec')]
  tsdb_write_query = [metric_helper.make_metric_query(cluster.name, group, 'writeRequestsCountPerSec')]

  params = {
    'cluster': cluster,
    'basic_info': basic_info,
    'tsdb_read_query': tsdb_read_query,
    'tsdb_write_query': tsdb_write_query,
  }
  return respond(request, 'monitor/hbase_basic_board.html', params)

#url: /cluster/$id/regionserver/
def show_cluster_regionserver_board(request, id):
  cluster = dbutil.get_cluster(id)
  if cluster.service.name != 'hbase':
    # return empty paget for unsupported service
    return HttpResponse('')

  read_requests_dist_by_rs, write_requests_dist_by_rs = dbutil.get_requests_distribution_groupby(cluster, 'regionserver');
  params = {
    'chart_id': 'read_requests_on_rs',
    'chart_title': 'read requests on region server',
    'request_dist': read_requests_dist_by_rs,
    'base_url': '/monitor/regionserver/',
  }

  read_requests_dist_by_rs_chart = loader.get_template('monitor/requests_dist_pie_chart.tpl').render(Context(params))

  params = {
    'chart_id': 'write_requests_on_rs',
    'chart_title': 'write requests on region server',
    'request_dist': write_requests_dist_by_rs,
    'base_url': '/monitor/regionserver/',
  }
  write_requests_dist_by_rs_chart = loader.get_template('monitor/requests_dist_pie_chart.tpl').render(Context(params))

  regionservers = dbutil.get_items_on_cluster(cluster, 'regionserver', order_by='name')
  params = {
    'cluster': cluster,
    'read_requests_dist_by_rs_chart': read_requests_dist_by_rs_chart,
    'write_requests_dist_by_rs_chart': write_requests_dist_by_rs_chart,
    'regionservers': regionservers,
  }
  return respond(request, 'monitor/hbase_regionserver_board.html', params)

#url: /cluster/$id/replication/
def show_cluster_replication(request, id):
  cluster = dbutil.get_cluster(id)
  region_servers = dbutil.get_regionservers_with_active_replication_metrics_by_cluster(cluster) 
  peer_id_endpoint_map = metric_helper.get_peer_id_endpoint_map(region_servers)
  params = {
    'cluster' : cluster,
    'replication_metrics' : metric_helper.make_metrics_query_for_replication(peer_id_endpoint_map),
  }
  return respond(request, 'monitor/hbase_replication.html', params)

#url: /table/$table_id/
def show_table(request, id):
  table = dbutil.get_table(id)
  cluster = table.cluster

  read_requests_dist_by_rs, write_requests_dist_by_rs = dbutil.get_requests_distribution(table)
  params = {
    'chart_id': 'read_requests_on_rs',
    'chart_title': 'read requests on region',
    'request_dist': read_requests_dist_by_rs,
  }

  read_requests_dist_by_rs_chart = loader.get_template('monitor/requests_dist_column_chart.tpl').render(Context(params))

  params = {
    'chart_id': 'write_requests_on_rs',
    'chart_title': 'write requests on region',
    'request_dist': write_requests_dist_by_rs,
  }
  write_requests_dist_by_rs_chart = loader.get_template('monitor/requests_dist_column_chart.tpl').render(
    Context(params))

  group = str(table)
  tsdb_read_query = [metric_helper.make_metric_query(cluster.name, group, 'readRequestsCountPerSec')]
  tsdb_write_query = [metric_helper.make_metric_query(cluster.name, group, 'writeRequestsCountPerSec')]

  params = {
    'cluster': cluster,
    'table': table,
    'read_requests_dist_by_rs_chart': read_requests_dist_by_rs_chart,
    'write_requests_dist_by_rs_chart': write_requests_dist_by_rs_chart,
    'tsdb_read_query': tsdb_read_query,
    'tsdb_write_query': tsdb_write_query,
  }

  return respond(request, 'monitor/hbase_table.html', params)

#url: /table/operation/$table_id
def show_table_operation(request, id):
  table = dbutil.get_table(id)
  cluster = table.cluster
  endpoint = dbutil.map_cluster_to_endpoint(cluster.name)
  group = str(table)
  params = {
    'cluster' : cluster,
    'table' : table,
    'tsdb_metrics' : metric_helper.make_operation_metrics(endpoint, table, group),
    'endpoint' : endpoint
  }
  return respond(request, 'monitor/hbase_table_operation.html', params)

#url: /regionserver/operation/$rs_id
def show_regionserver_operation(request, id):
  regionserver = dbutil.get_regionserver(id)
  cluster = regionserver.cluster
  endpoint = dbutil.map_cluster_to_endpoint(cluster.name)
  params = {
    'cluster' : cluster,
    'regionserver' : regionserver,
    'tsdb_metrics' : metric_helper.generate_operation_metric_for_regionserver(regionserver),
    'endpoint' : endpoint
  }
  return respond(request, 'monitor/hbase_regionserver_operation.html', params)

#url: /cluster/operation/$cluster_id
def show_cluster_operation(request, id):
  cluster = dbutil.get_cluster(id)
  endpoint = dbutil.map_cluster_to_endpoint(cluster.name)
  group = 'Cluster'
  params = {
    'cluster' : cluster,
    'tsdb_metrics' : metric_helper.make_operation_metrics(endpoint, cluster.hbasecluster, group),
    'endpoint' : endpoint
  }

  return respond(request, 'monitor/hbase_cluster_operation.html', params)

#url: /cluster/operation/tablecomparsion
def show_cluster_operation_table_comparison(request, id):
  cluster = dbutil.get_cluster(id)
  endpoint = dbutil.map_cluster_to_endpoint(cluster.name)
  params = {
    'cluster' : cluster,
    'tsdb_metrics' : metric_helper.make_operation_metrics_for_tables_in_cluster(cluster),
    'endpoint' : endpoint
  }
  print params['tsdb_metrics']
  return respond(request, 'monitor/hbase_cluster_operation_table_comparsion.html', params)

#url: /regionserver/$rs_id/
def show_regionserver(request, id):
  rs = dbutil.get_regionserver(id)
  cluster = rs.cluster

  read_requests_dist_by_rs, write_requests_dist_by_rs = dbutil.get_requests_distribution(rs);
  params = {
    'chart_id': 'read_requests_on_rs',
    'chart_title': 'read requests on region',
    'request_dist': read_requests_dist_by_rs,
  }

  read_requests_dist_by_rs_chart = loader.get_template('monitor/requests_dist_column_chart.tpl').render(Context(params))

  params = {
    'chart_id': 'write_requests_on_rs',
    'chart_title': 'write requests on region',
    'request_dist': write_requests_dist_by_rs,
  }
  write_requests_dist_by_rs_chart = loader.get_template('monitor/requests_dist_column_chart.tpl').render(
    Context(params))

  group = str(rs)
  tsdb_read_query = [metric_helper.make_metric_query(cluster.name, group, 'readRequestsCountPerSec')]
  tsdb_write_query = [metric_helper.make_metric_query(cluster.name, group, 'writeRequestsCountPerSec')]

  params = {
    'cluster': cluster,
    'regionserver': rs,
    'read_requests_dist_by_rs_chart': read_requests_dist_by_rs_chart,
    'write_requests_dist_by_rs_chart': write_requests_dist_by_rs_chart,
    'tsdb_read_query': tsdb_read_query,
    'tsdb_write_query': tsdb_write_query,
  }
  return respond(request, 'monitor/hbase_regionserver.html', params)

#url: /job/$id/
def show_job(request, id):
  tasks = dbutil.get_healthy_tasks_by_job(id)
  job = dbutil.get_job(id)

  endpoints = [metric_helper.form_perf_counter_endpoint_name(task) for task in tasks]
  tsdb_metrics = metric_helper.make_metrics_query_for_job(endpoints, job, tasks)
  print tsdb_metrics
  params = {
    'job': job,
    'tasks': tasks,
    'tsdb_metrics': tsdb_metrics,
  }

  return respond(request, 'monitor/job.html', params)

#url: /task/$id/
def show_task(request, id):
  task = dbutil.get_task(id)
  job = task.job
  tasks = dbutil.get_tasks_by_job(job)

  tsdb_metrics = metric_helper.make_metrics_query_for_task(
    metric_helper.form_perf_counter_endpoint_name(task),
    task)

  params = {
    'job': job,
    'task': task,
    'tasks': tasks,
    'tsdb_metrics': tsdb_metrics,
  }
  return respond(request, 'monitor/task.html', params)


def show_all_metrics(request):
  result = {}
  metrics = dbutil.get_all_metrics()
  if not metrics:
    return HttpResponse('', content_type='application/json; charset=utf8')

  result['timestamp'] = int(time.time())
  result['data'] = metrics
  # defaultly not format output
  indent = None
  if 'indent' in request.GET:
    # when indent is set, format json output with indent = 1
    indent = 1
  return HttpResponse(json.dumps(result, indent=indent),
                      content_type='application/json; charset=utf8')

def show_all_metrics_config(request):
  metrics_config = metric_helper.get_all_metrics_config()

  # defaultly not format output
  indent = None
  if 'indent' in request.GET:
    # when indent is set, format json output with indent = 1
    indent = 1
  return HttpResponse(json.dumps(metrics_config, indent=indent),
                      content_type='application/json; charset=utf8')

def get_time_range(request):
  start_time = datetime.datetime.today() + datetime.timedelta(hours=-1)
  end_time = datetime.datetime.today()
  if 'start_time' in request.COOKIES:
    start_time = datetime.datetime.strptime(request.COOKIES['start_time'], '%Y-%m-%d-%H-%M')

  if 'start_time' in request.GET:
    start_time = datetime.datetime.strptime(request.GET['start_time'], '%Y-%m-%d-%H-%M')

  if 'end_time' in request.COOKIES:
    end_time = datetime.datetime.strptime(request.COOKIES['end_time'], '%Y-%m-%d-%H-%M')

  if 'end_time' in request.GET:
    end_time = datetime.datetime.strptime(request.GET['end_time'], '%Y-%m-%d-%H-%M')
  return start_time, end_time


@transaction.commit_on_success
@csrf_exempt
@require_http_methods(["POST"])
def add_counter(request):
  counters = json.loads(request.body)
  remote_ip = request.META['REMOTE_ADDR']
  update_time = datetime.datetime.utcfromtimestamp(time.time()).replace(tzinfo=timezone.utc)
  for dict in counters:
    group = dict['group']
    endpoint = remote_ip
    if 'endpoint' in dict:
      endpoint = dict['endpoint']
    label = ''
    if 'label' in dict:
      label = dict['label']
    name = dict['name']
    counter, create = dbutil.get_or_create_counter(group, name)

    counter.host = endpoint
    counter.value = (float)(dict['value'])
    counter.unit = dict['unit']
    counter.last_update_time = update_time
    counter.label = label
    counter.save()
  return HttpResponse("ok")


def show_all_counters(request):
  result = {}
  metrics = dbutil.get_all_counters()
  if not metrics:
    return HttpResponse('', content_type='application/json; charset=utf8')

  result['timestamp'] = time.time()
  result['data'] = metrics
  # defaultly not format output
  indent = None
  if 'indent' in request.GET:
  # when indent is set, format json output with indent = 1
    indent = 1
  return HttpResponse(json.dumps(result, indent=indent),
                      content_type='application/json; charset=utf8')


def respond(request, template, params=None):
  """Helper to render a response, passing standard stuff to the response.
  Args:
  request: The request object.
  template: The template name; '.html' is appended automatically.
  params: A dict giving the template parameters; modified in-place.
  Returns:
  Whatever render_to_response(template, params) returns.
  Raises:
  Whatever render_to_response(template, params) raises.
  """
  params['request'] = request
  params['user'] = request.user
  params['tsdb_url_prefix'] = settings.TSDB_ADDR
  params['start_date'] = (datetime.datetime.now() - datetime.timedelta(minutes=15)).strftime('%Y/%m/%d-%H:%M:%S')
  params.update(request.GET)
  response = render_to_response(template, params,
                                context_instance=RequestContext(request))
  return response
