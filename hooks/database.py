import shutil
from os.path import join, isfile, isdir
from subprocess import check_output, CalledProcessError
from syncloudlib import logger

from hooks.installer import DB_USER


class Database:

    def __init__(self, app_dir, data_dir, psql, user, database_path, port):
        self.app_dir = app_dir
        self.data_dir = data_dir
        self.psql = psql
        self.user = user
        self.database_dir = database_path
        self.port = port
        self.log = logger.get_logger('postgres')
        self.old_major_version_file = join(self.data_dir, 'db.major.version')
        self.new_major_version_file = join(self.app_dir, 'db.major.version')
        self.backup_file = join(self.data_dir, 'database.dump')

    def execute(self, database, sql):
        self.log.info("executing: {0}".format(sql))
        command_line = '{0} -U {1} -d {2} -c "{3}" -h {4} -p {5}'.format(self.psql, self.user, database, sql,
                                                                         self.database_dir, self.port)
        self.log.info(check_output(command_line, shell=True))

    def init(self):
        if not isdir(self.database_dir):
            psql_initdb = join(self.app_dir, 'postgresql/bin/initdb.sh')
            self.log.info(check_output(['sudo', '-H', '-u', DB_USER, psql_initdb, self.database_dir]))
            postgresql_conf_to = join(self.database_dir, 'postgresql.conf')
            postgresql_conf_from = join(self.data_dir, 'config', 'postgresql.conf')
            shutil.copy(postgresql_conf_from, postgresql_conf_to)
        else:
            self.log.info('Database path "{0}" already exists'.format(self.database_dir))
        return self.database_dir

    def remove(self):
        if not isfile(self.backup_file):
            raise Exception("Backup file does not exist: {0}".format(self.backup_file))

        if isdir(self.database_dir):
            shutil.rmtree(self.database_dir)

    def restore(self):
        self.run('snap run gogs.psql -f {0} postgres'.format(self.backup_file))

    def backup(self):
        self.run('snap run gogs.pgdumpall -f {0}'.format(self.backup_file))
        shutil.copy(self.new_major_version_file, self.old_major_version_file)

    def requires_upgrade(self):
        if not isfile(self.old_major_version_file):
            return True
        old_version = open(self.old_major_version_file).read().strip()
        new_version = open(self.new_major_version_file).read().strip()
        return old_version != new_version

    def run(self, cmd):
        try:
            self.log.info("postgres executing: {0}".format(cmd))
            output = check_output(cmd, shell=True).decode()
            self.log.info(output)
        except CalledProcessError as e:
            self.log.error("postgres error: " + e.output.decode())
            raise e
