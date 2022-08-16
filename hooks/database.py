from subprocess import check_output
from syncloudlib import logger


class Database:

    def __init__(self, psql, user, database_path, port):
        self.psql = psql
        self.user = user
        self.database_path = database_path
        self.port = port
        self.log = logger.get_logger('postgres')

    def execute(self, database, sql):
        self.log.info("executing: {0}".format(sql))
        command_line = '{0} -U {1} -d {2} -c "{3}" -h {4} -p {5}'.format(self.psql, self.user, database, sql,
                                                                         self.database_path, self.port)
        self.log.info(check_output(command_line, shell=True))
