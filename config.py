#!/usr/bin/env python

import ConfigParser
import os
import re

from configobj import ConfigObj

def get_config_dir(args=None, cluster=None, jobs=None):
  '''
  Get the service config file's root directory.
  '''
  return "%s/config" % os.path.dirname(__file__)

def get_service_config_path(args):
  return "%s/service-conf/%s/%s-%s.cfg" % (get_config_dir(),
    args.service, args.service, args.cluster)


class ConfigUtils:
  @staticmethod
  def get_config_dir():
    '''
    Get the service config directory.
    '''
    return get_config_dir()

  @staticmethod
  def get_service_config(args):
    '''
    Get service config, without any dependencies.
  
    @param  args       the command line arguments object parsed by argparse
    '''
    if not getattr(args, args.service + "_config", None):
      setattr(args, args.service+"_config", ServiceConfig(args))
    return getattr(args, args.service+"_config")


HOST_RULE_REGEX = re.compile(r'host\.(?P<id>\d+)')
HOST_REGEX = re.compile(r'(?P<host>(.+))$')

COMMON_JOB_SCHEMA = {
    # "param_name": (type, default_value)
    # type must be in {bool, int, float, str}
    # if default_value is None, it means it's NOT an optional parameter.
    "http_port": (int, None),
}

CLUSTER_SCHEMA = {
  "name": (str, None),
  "version": (str, None),
  "jobs": (str, None),
  "revision": (str, ""),
  "timestamp": (str, ""),
  "hdfs_cluster": (str, ""),
}

class ServiceConfig:
  '''
  The class represents the configuration of a service.
  '''
  def __init__(self, args):
    self.config_dict_full = self.get_config_dict_full(
      get_service_config_path(args))

    self.cluster_dict = self.config_dict_full["cluster"]

    self.cluster = ServiceConfig.Cluster(self.cluster_dict, args.cluster)
    self.jobs = {}
    for job_name in self.cluster.jobs:
      self.jobs[job_name] = ServiceConfig.Jobs(
        self.config_dict_full[job_name], job_name)

  class Cluster:
    '''
    The class represents a service cluster
    '''
    def __init__(self, cluster_dict, cluster_name):
      ServiceConfig.parse_params(self, "cluster", cluster_dict, CLUSTER_SCHEMA)

      self.jobs = self.jobs.split()
      if self.name != cluster_name:
        Log.print_critical(
          "Cluster name in config doesn't match the config file name: "
          "%s vs. %s" % (self.name, cluster_name))

  class Jobs:
    '''
    The class represents all the jobs of a service
    '''
    def __init__(self, job_dict, job_name):
      self.name = job_name
      ServiceConfig.parse_params(self, job_name, job_dict, COMMON_JOB_SCHEMA)
      self.hosts = {}
      self.hostnames = {}
      for name, value in job_dict.iteritems():
        reg_expr = HOST_RULE_REGEX.match(name)
        if not reg_expr:
          continue
        host_id = int(reg_expr.group("id"))
        reg_expr = HOST_REGEX.match(value)
        if not reg_expr:
          Log.print_critical("Host/IP address expected on rule: %s = %s" %
                            (name, value))
        ip = reg_expr.group("host")
        self.hosts[host_id] = ip
        try:
          self.hostnames[host_id] = socket.gethostbyaddr(ip)[0]
        except:
          self.hostnames[host_id] = ip

  def get_config_dict_full(self, config_path):
    '''
    Get the whole configuration dict: reading the base common-config and
    using the child_config_dict to update the base_config_dict

    @param   config_path      The path for configuration file
    @return  dict             The whole configuration dict
    '''
    base_config_dict = {}
    child_config_dict = ConfigObj(config_path, file_error=True)

    return child_config_dict


  @staticmethod
  def parse_params(namespace, section_name, section_dict, schema):
    '''
    Parse the parameters specified by the schema dict from the specific section dict
    '''
    for param_name, param_def in schema.iteritems():
      if param_name in section_dict:
        if param_def[0] is bool:
          param_value = section_dict.as_bool(param_name)
        elif param_def[0] is int:
          param_value = section_dict.as_int(param_name)
        elif param_def[0] is float:
          param_value = section_dict.as_float(param_name)
        else:
          param_value = section_dict[param_name]
      else:
        # option not found, use the default value if there is.
        if param_def[1] is None:
          Log.print_critical("required option %s missed in section %s!" %
            (param_name, section_name))
        else:
          param_value = param_def[1]
      setattr(namespace, param_name, param_value)
