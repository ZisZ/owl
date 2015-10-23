# Owl
Owl is a monitor system for Hadoop cluster. It collects data from servers through JMX interface. And it organizes pages in cluster, job and task corresponding to the definition in cluster configuration.

# Requirements
mysql-server

python 2.6

python lib:

django 1.4.x <https://www.djangoproject.com/>

twisted <http://twistedmatrix.com/>

mysql-python <http://sourceforge.net/projects/mysql-python/>

dbutils <https://pypi.python.org/pypi/DBUtils/>

If you use pip(<http://www.pip-installer.org/>), you can install python libs like:

    pip install django

# Installation
Initialize Mysql

    mysql -uroot -ppassword
    >create database owl
    >use mysql;
    >GRANT ALL ON owl.* TO 'owl'@'localhost' identified by 'owl';
    >flush privileges;

Initialize Django
  
    python manage.py syncdb

# Configuration
Collector configuration

Modify collector.cfg in config to change configuration for monitor

    [collector]
    # service name(space seperated)
    service = hdfs hbase
    
    [hdfs] 
    # cluster name(space seperated)
    clusters=cluster-example
    # job name(space seperated)
    jobs=journalnode namenode datanode
    # url for collecotr, usually JMX url
    metric_url=/jmx?qry=Hadoop:*

Modify owl/settings.py to change configuration for owl

    # Opentsdb base url, for displaying metrics in owl
    TSDB_ADDR = 'http://127.0.0.1:9888'

# Run
###Start collector
    ./collector.sh

###Start server
    ./runserver.sh 0.0.0.0:8000 
