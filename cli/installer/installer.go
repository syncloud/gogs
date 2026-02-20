package installer

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

const (
	App      = "gogs"
	UserName = "git"
	PsqlPort = 5433
	DbUser   = "git"
	DbPass   = "git"
	DbName   = "gogs"
)

type Variables struct {
	AppDir              string
	AppDataDir          string
	DatabaseDir         string
	DbPsqlPort          int
	DbName              string
	DbUser              string
	DbPassword          string
	GogsReposPath       string
	LogPath             string
	AppUrl              string
	AppDomain           string
	WebSecret           string
	DisableRegistration bool
	DataDir             string
}

type Installer struct {
	appDir         string
	commonDir      string
	dataDir        string
	configDir      string
	installFile    string
	platformClient *platform.Client
	database       *Database
	executor       *Executor
	logger         *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	commonDir := fmt.Sprintf("/var/snap/%s/common", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	configDir := path.Join(dataDir, "config")
	executor := NewExecutor(logger)
	return &Installer{
		appDir:         appDir,
		commonDir:      commonDir,
		dataDir:        dataDir,
		configDir:      configDir,
		installFile:    path.Join(commonDir, "installed"),
		platformClient: platform.New(),
		database:       NewDatabase(appDir, commonDir, dataDir, configDir, DbUser, PsqlPort, executor, logger),
		executor:       executor,
		logger:         logger,
	}
}

func (i *Installer) UpdateConfigs() error {
	homeFolder := path.Join("/home", UserName)
	if err := createGitUser(UserName, homeFolder); err != nil {
		return err
	}
	if err := copyFile(path.Join(i.appDir, "config", ".bashrc"), path.Join(homeFolder, ".bashrc")); err != nil {
		return err
	}
	logPath := path.Join(i.commonDir, "log")
	if err := os.MkdirAll(logPath, 0755); err != nil {
		return err
	}
	reposPath, err := i.platformClient.InitStorage(App, UserName)
	if err != nil {
		return err
	}
	appUrl, err := i.platformClient.GetAppUrl(App)
	if err != nil {
		return err
	}
	appDomain, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return err
	}
	variables := Variables{
		AppDir:              i.appDir,
		AppDataDir:          i.commonDir,
		DatabaseDir:         i.database.DatabaseDir(),
		DbPsqlPort:          PsqlPort,
		DbName:              DbName,
		DbUser:              DbUser,
		DbPassword:          DbPass,
		GogsReposPath:       reposPath,
		LogPath:             logPath,
		AppUrl:              appUrl,
		AppDomain:           appDomain,
		WebSecret:           uuid.New().String(),
		DisableRegistration: false,
		DataDir:             i.dataDir,
	}
	err = config.Generate(
		path.Join(i.appDir, "config"),
		i.configDir,
		variables,
	)
	if err != nil {
		return err
	}
	if err := linux.Chown(i.commonDir, UserName); err != nil {
		return err
	}
	return linux.Chown(i.dataDir, UserName)
}

func (i *Installer) Install() error {
	if err := i.UpdateConfigs(); err != nil {
		return err
	}
	if err := i.database.Init(); err != nil {
		return err
	}
	return i.database.InitConfig()
}

func (i *Installer) Configure() error {
	if i.IsInstalled() {
		return i.Upgrade()
	}
	return i.Initialize()
}

func (i *Installer) IsInstalled() bool {
	_, err := os.Stat(i.installFile)
	return err == nil
}

func (i *Installer) Initialize() error {
	i.logger.Info("initialize")
	adminPassword := uuid.New().String()

	if err := i.database.Execute("postgres", fmt.Sprintf("ALTER USER %s WITH PASSWORD '%s';", DbUser, DbPass)); err != nil {
		return err
	}
	if err := i.database.Execute("postgres", fmt.Sprintf("CREATE DATABASE %s WITH OWNER=%s;", DbName, DbUser)); err != nil {
		return err
	}

	email, err := getUserEmail()
	if err != nil {
		return err
	}

	socketPath := path.Join(i.commonDir, "web.socket")

	signupSession := newGogsSession(socketPath, i.logger)
	if err := signupSession.WaitURL(60 * time.Second); err != nil {
		return err
	}
	if err := signupSession.SignUp(email, "gogs", adminPassword); err != nil {
		return err
	}

	ldapSession := newGogsSession(socketPath, i.logger)
	if err := ldapSession.Login("gogs", adminPassword); err != nil {
		return err
	}
	if err := ldapSession.ActivateLDAP(); err != nil {
		return err
	}

	deleteSession := newGogsSession(socketPath, i.logger)
	if err := deleteSession.Login("gogs", adminPassword); err != nil {
		return err
	}
	if err := deleteSession.DeleteUser(1); err != nil {
		return err
	}

	if err := i.database.Execute(DbName, "select * from login_source;"); err != nil {
		return err
	}
	if err := i.disableRegistration(); err != nil {
		return err
	}
	return os.WriteFile(i.installFile, []byte("installed\n"), 0644)
}

func (i *Installer) Upgrade() error {
	i.logger.Info("upgrade")
	return i.database.Restore()
}

func (i *Installer) PreRefresh() error {
	return i.database.Backup()
}

func (i *Installer) PostRefresh() error {
	i.logger.Info("post refresh")
	if err := i.UpdateConfigs(); err != nil {
		return err
	}
	if err := i.database.Remove(); err != nil {
		return err
	}
	if err := i.database.Init(); err != nil {
		return err
	}
	return i.database.InitConfig()
}

func (i *Installer) StorageChange() error {
	_, err := i.platformClient.InitStorage(App, UserName)
	return err
}

func (i *Installer) AccessChange() error {
	return i.UpdateConfigs()
}

func (i *Installer) BackupPreStop() error {
	return i.PreRefresh()
}

func (i *Installer) RestorePreStart() error {
	return i.PostRefresh()
}

func (i *Installer) RestorePostStart() error {
	return i.Configure()
}

func (i *Installer) disableRegistration() error {
	configPath := path.Join(i.configDir, "gogs.ini")
	content, err := os.ReadFile(configPath)
	if err != nil {
		return err
	}
	newContent := strings.Replace(string(content), "DISABLE_REGISTRATION = false", "DISABLE_REGISTRATION = true", 1)
	return os.WriteFile(configPath, []byte(newContent), 0644)
}

func createGitUser(username, homeFolder string) error {
	if err := exec.Command("id", username).Run(); err == nil {
		return nil
	}
	cmd := exec.Command("/usr/sbin/useradd",
		"-m",
		"-d", homeFolder,
		"-s", "/bin/bash",
		username,
	)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("useradd %s: %w: %s", username, err, string(out))
	}
	return nil
}

func getUserEmail() (string, error) {
	transport := &http.Transport{
		DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			return (&net.Dialer{}).DialContext(ctx, "unix", "/var/snap/platform/common/api.socket")
		},
	}
	client := &http.Client{Transport: transport}
	resp, err := client.Get("http://localhost/user/email")
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	var result struct {
		Data string `json:"data"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return "", err
	}
	return result.Data, nil
}
