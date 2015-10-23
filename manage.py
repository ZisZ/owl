#!/usr/bin/env python
import os
import sys
import ctypes

if __name__ == "__main__":
  os.environ["DJANGO_SETTINGS_MODULE"] = "owl.settings"

  owl_root_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
  sys.path.append(owl_root_path)
  owl_conf_path = os.path.join(owl_root_path, 'config')
  sys.path.append(owl_conf_path)
  owl_lib_path = os.path.join(owl_root_path, 'libs')
  sys.path.append(owl_lib_path)

  from django.core.management import execute_from_command_line
#  import pdb
#  pdb.set_trace()
  execute_from_command_line(sys.argv)
