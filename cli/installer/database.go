package installer

import (
	"errors"
	"fmt"
	"io"
	"os"
	"path"
	"strconv"

	"go.uber.org/zap"
)

type Database struct {
	appDir      string
	dataDir     string
	configDir   string
	user        string
	databaseDir string
	port        int
	backupFile  string
	executor    *Executor
	logger      *zap.Logger
}

func NewDatabase(appDir, commonDir, dataDir, configDir, user string, port int, executor *Executor, logger *zap.Logger) *Database {
	return &Database{
		appDir:      appDir,
		dataDir:     dataDir,
		configDir:   configDir,
		user:        user,
		databaseDir: path.Join(commonDir, "database"),
		port:        port,
		backupFile:  path.Join(commonDir, "database.dump"),
		executor:    executor,
		logger:      logger,
	}
}

func (d *Database) DatabaseDir() string {
	return d.databaseDir
}

func (d *Database) Execute(database, sql string) error {
	return d.executor.Run(
		path.Join(d.appDir, "postgresql/bin/psql.sh"),
		"-U", d.user,
		"-d", database,
		"-c", sql,
		"-h", d.databaseDir,
		"-p", strconv.Itoa(d.port),
	)
}

func (d *Database) Init() error {
	return d.executor.Run(path.Join(d.appDir, "bin/initdb.sh"), d.databaseDir)
}

func (d *Database) InitConfig() error {
	src := path.Join(d.configDir, "postgresql.conf")
	dst := path.Join(d.databaseDir, "postgresql.conf")
	return copyFile(src, dst)
}

func (d *Database) Remove() error {
	if _, err := os.Stat(d.backupFile); errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("backup file does not exist: %s", d.backupFile)
	}
	return os.RemoveAll(d.databaseDir)
}

func (d *Database) Restore() error {
	return d.executor.Run("snap", "run", "gogs.psql", "-f", d.backupFile, "postgres")
}

func (d *Database) Backup() error {
	return d.executor.Run("snap", "run", "gogs.pgdumpall", "-f", d.backupFile)
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}
