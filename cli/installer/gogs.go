package installer

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"regexp"
	"time"

	"go.uber.org/zap"
)

type GogsSession struct {
	client  *http.Client
	baseURL string
	logger  *zap.Logger
}

func newGogsSession(socketPath string, logger *zap.Logger) *GogsSession {
	transport := &http.Transport{
		DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			return (&net.Dialer{}).DialContext(ctx, "unix", socketPath)
		},
	}
	jar, _ := cookiejar.New(nil)
	return &GogsSession{
		client: &http.Client{
			Transport: transport,
			Jar:       jar,
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				return http.ErrUseLastResponse
			},
		},
		baseURL: "http://localhost",
		logger:  logger,
	}
}

func (g *GogsSession) WaitURL(timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		resp, err := g.client.Get(g.baseURL + "/")
		if err == nil {
			_ = resp.Body.Close()
			if resp.StatusCode == 200 || resp.StatusCode == 302 {
				return nil
			}
			g.logger.Info("waiting for gogs", zap.Int("status", resp.StatusCode))
		} else {
			g.logger.Info("waiting for gogs", zap.Error(err))
		}
		time.Sleep(3 * time.Second)
	}
	return fmt.Errorf("timeout waiting for gogs")
}

func (g *GogsSession) extractCSRF(urlPath string) (string, error) {
	g.logger.Info("extract csrf", zap.String("path", urlPath))
	resp, err := g.client.Get(g.baseURL + urlPath)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("extract csrf: unexpected status %d for %s", resp.StatusCode, urlPath)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	re := regexp.MustCompile(`<meta[^>]+name="_csrf"[^>]+content="([^"]+)"`)
	matches := re.FindSubmatch(body)
	if len(matches) < 2 {
		return "", fmt.Errorf("csrf token not found in %s", urlPath)
	}
	return string(matches[1]), nil
}

func (g *GogsSession) SignUp(email, login, password string) error {
	g.logger.Info("sign up", zap.String("login", login), zap.String("email", email))
	data := url.Values{
		"user_name": {login},
		"password":  {password},
		"retype":    {password},
		"email":     {email},
	}
	resp, err := g.client.PostForm(g.baseURL+"/user/sign_up", data)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 302 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("sign up failed with status %d: %s", resp.StatusCode, string(body))
	}
	return nil
}

func (g *GogsSession) Login(username, password string) error {
	g.logger.Info("login", zap.String("username", username))
	csrf, err := g.extractCSRF("/user/login")
	if err != nil {
		return fmt.Errorf("login: %w", err)
	}
	data := url.Values{
		"user_name": {username},
		"password":  {password},
		"_csrf":     {csrf},
	}
	resp, err := g.client.PostForm(g.baseURL+"/user/login", data)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 302 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("login failed with status %d: %s", resp.StatusCode, string(body))
	}
	return nil
}

func (g *GogsSession) ActivateLDAP() error {
	g.logger.Info("activating ldap")
	csrf, err := g.extractCSRF("/admin/auths/new")
	if err != nil {
		return fmt.Errorf("activate ldap: %w", err)
	}
	data := url.Values{
		"_csrf":              {csrf},
		"type":              {"5"},
		"name":              {"syncloud"},
		"security_protocol": {""},
		"host":              {"localhost"},
		"port":              {"389"},
		"bind_dn":           {""},
		"bind_password":     {""},
		"user_base":         {""},
		"user_dn":           {"cn=%s,ou=users,dc=syncloud,dc=org"},
		"filter":            {"(&(objectclass=inetOrgPerson)(cn=%s))"},
		"admin_filter":      {"(objectClass=inetOrgPerson)"},
		"attribute_username": {"cn"},
		"attribute_name":    {"cn"},
		"attribute_surname": {""},
		"attribute_mail":    {"mail"},
		"group_dn":          {""},
		"group_filter":      {""},
		"group_member_uid":  {""},
		"user_uid":          {""},
		"smtp_auth":         {"PLAIN"},
		"smtp_host":         {""},
		"smtp_port":         {""},
		"allowed_domains":   {""},
		"pam_service_name":  {""},
		"is_default":        {"on"},
		"is_active":         {"on"},
	}
	resp, err := g.client.PostForm(g.baseURL+"/admin/auths/new", data)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 302 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("activate ldap failed with status %d: %s", resp.StatusCode, string(body))
	}
	return nil
}

func (g *GogsSession) DeleteUser(id int) error {
	g.logger.Info("delete install user", zap.Int("id", id))
	csrf, err := g.extractCSRF(fmt.Sprintf("/admin/users/%d", id))
	if err != nil {
		return fmt.Errorf("delete user: %w", err)
	}
	data := url.Values{
		"id":    {fmt.Sprintf("%d", id)},
		"_csrf": {csrf},
	}
	resp, err := g.client.PostForm(fmt.Sprintf("%s/admin/users/%d/delete", g.baseURL, id), data)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("delete user failed with status %d: %s", resp.StatusCode, string(body))
	}
	return nil
}
