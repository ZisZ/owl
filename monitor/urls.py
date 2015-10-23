# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
import views

urlpatterns = patterns(
  '',
  url(r'^$', views.index),

  url(r'^metrics/', views.show_all_metrics),
  url(r'^metrics_config/', views.show_all_metrics_config),

  url(r'^counters/', views.show_all_counters),
  url(r'^addCounter/$', views.add_counter),


  url(r'^service/(?P<id>\d+)/$', views.show_service),
  url(r'^cluster/(?P<id>\d+)/$', views.show_cluster),
  url(r'^cluster/(?P<id>\d+)/task/$', views.show_cluster_task_board),
  url(r'^cluster/(?P<id>\d+)/basic/$', views.show_cluster_basic_board),
  url(r'^cluster/(?P<id>\d+)/table/$', views.show_cluster_table_board),
  url(r'^cluster/(?P<id>\d+)/regionserver/$', views.show_cluster_regionserver_board),
  url(r'^cluster/(?P<id>\d+)/replication/$', views.show_cluster_replication),

  url(r'^job/(?P<id>[^/]+)/$', views.show_job),
  url(r'^task/(?P<id>[^/]+)/$', views.show_task),


  url(r'^table/(?P<id>\d+)/$', views.show_table),
  url(r'^table/operation/(?P<id>\d+)/$', views.show_table_operation),
  url(r'^cluster/operation/(?P<id>\d+)/$', views.show_cluster_operation),
  url(r'^cluster/operation/tablecomparsion/(?P<id>\d+)/$', views.show_cluster_operation_table_comparison),
  url(r'^regionserver/(?P<id>\d+)/$', views.show_regionserver),
  url(r'^regionserver/operation/(?P<id>\d+)/$', views.show_regionserver_operation),
)
