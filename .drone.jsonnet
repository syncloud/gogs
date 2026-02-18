local name = "gogs";
local browser = "firefox";
local gogs_ver = "0.14.1";
local nginx = "1.24.0";
local python = '3.12-slim-bookworm';
local debian = 'bookworm-slim';
local distro = "bookworm";
local platform = '25.09';
local selenium_ver = '4.35.0-20250828';
local dind = '20.10.21-dind';

local build(arch, test_ui) = [{
    kind: "pipeline",
    type: "docker",
    name: arch,
    platform: {
        os: "linux",
        arch: arch
    },
    steps: [
        {
            name: "version",
            image: "debian:" + debian,
            commands: [
                "echo $DRONE_BUILD_NUMBER > version"
            ]
        },
        {
            name: "gogs",
            image: "gogs/gogs:" + gogs_ver,
            commands: [
                "./gogs/build.sh"
            ]
        },
        {
            name: "gogs test",
            image: "syncloud/platform-" + distro + "-" + arch + ":" + platform,
            commands: [
                "./gogs/test.sh"
            ]
        },
        {
            name: "nginx",
            image: "nginx:" + nginx,
            commands: [
                "./nginx/build.sh"
            ]
        },
        {
            name: "nginx test",
            image: "syncloud/platform-" + distro + "-" + arch + ":" + platform,
            commands: [
                "./nginx/test.sh"
            ]
        },
        {
            name: "package postgresql",
            image: "docker:" + dind,
            commands: [
                "./postgresql/build.sh"
            ],
            volumes: [
                {
                    name: "dockersock",
                    path: "/var/run"
                }
            ]
        },
        {
            name: "test postgresql",
            image: "debian:" + debian,
            commands: [
                "./postgresql/test.sh"
            ]
        },
      {
            name: "package git",
            image: "docker:" + dind,
            commands: [
                "./git/build.sh"
            ],
            volumes: [
                {
                    name: "dockersock",
                    path: "/var/run"
                }
            ]
        },
        {
            name: "package python",
            image: "docker:" + dind,
            commands: [
                "./python/build.sh"
            ],
            volumes: [
                {
                    name: "dockersock",
                    path: "/var/run"
                }
            ]
        },
        {
            name: "package",
            image: "debian:" + debian,
            commands: [
                "VERSION=$(cat version)",
                "./package.sh " + name + " $VERSION "
            ]
        },
        {
            name: "test-integration-bookworm",
            image: "python:" + python,
            commands: [
              "APP_ARCHIVE_PATH=$(realpath $(cat package.name))",
              "cd test",
              "./deps.sh",
              "py.test -x -s test.py --distro=" + distro + " --domain=" + distro + ".com --app-archive-path=$APP_ARCHIVE_PATH --device-host=" + name + "." + distro + ".com --app="  + name + " --device-user=gogs --arch=" + arch
            ]
        }] +
        ( if test_ui then ([
        {
            name: "selenium-video",
            image: "selenium/video:ffmpeg-4.3.1-20220208",
            detach: true,
            environment: {
                DISPLAY_CONTAINER_NAME: "selenium",
                FILE_NAME: "video.mkv"
            },
            volumes: [
            {
                name: "shm",
                path: "/dev/shm"
            },
            {
                name: "videos",
                path: "/videos"
            }
        ]
       }] +
        [{
            name: "test-ui-" + mode,
            image: "python:" + python,
            commands: [
              "cd test",
              "./deps.sh",
              "pip install -r requirements.txt",
              "py.test -x -s ui.py --distro=" + distro + " --ui-mode=" + mode + " --domain=" + distro + ".com --device-host=" + name + "." + distro + ".com --app=" + name + " --device-user=gogs --browser=" + browser,
            ]
        } for mode in ["desktop", "mobile"]
       ]
        +
       [
        {
            name: "test-upgrade",
            image: "python:" + python,
            commands: [
              "APP_ARCHIVE_PATH=$(realpath $(cat package.name))",
              "cd test",
              "./deps.sh",
              "py.test -x -s upgrade.py --distro=" + distro + " --ui-mode=desktop --domain=" + distro + ".com --app-archive-path=$APP_ARCHIVE_PATH --device-host=" + name + "." + distro + ".com --app=" + name + " --device-user=gogs --browser=" + browser,
            ],
            privileged: true,
            volumes: [{
                name: "videos",
                path: "/videos"
            }]
        } ] +
        [{
            name: "test-ui-upgrade",
            image: "python:" + python,
            commands: [
              "cd test",
              "./deps.sh",
              "pip install -r requirements.txt",
              "py.test -x -s ui.py --distro=" + distro + " --ui-mode=" + mode + " --domain=" + distro + ".com --device-host=" + name + "." + distro + ".com --app=" + name + " --device-user=gogs --browser=" + browser,
            ]
        } for mode in ["desktop"]
       ]) else [] ) + [
        {
            name: "upload",
            image: "debian:" + debian,
            environment: {
                AWS_ACCESS_KEY_ID: {
                    from_secret: "AWS_ACCESS_KEY_ID"
                },
                AWS_SECRET_ACCESS_KEY: {
                    from_secret: "AWS_SECRET_ACCESS_KEY"
                }
            },
            commands: [
                "PACKAGE=$(cat package.name)",
                "apt update && apt install -y wget",
                "wget https://github.com/syncloud/snapd/releases/download/1/syncloud-release-" + arch + " -O release --progress=dot:giga",
                "chmod +x release",
                "./release publish -f $PACKAGE -b $DRONE_BRANCH"
            ],
            when: {
                branch: ["stable", "master"]
            }
        },
        {
            name: "artifact",
            image: "appleboy/drone-scp:1.6.4",
            settings: {
                host: {
                    from_secret: "artifact_host"
                },
                username: "artifact",
                key: {
                    from_secret: "artifact_key"
                },
                timeout: "2m",
                command_timeout: "2m",
                target: "/home/artifact/repo/" + name + "/${DRONE_BUILD_NUMBER}-" + arch ,
                source: "artifact/*",
                strip_components: 1
            },
            when: {
              status: [ "failure", "success" ]
            }
        }
        ],
        trigger: {
          event: [
            "push",
            "pull_request"
          ]
        },
        services: [
            {
                name: "docker",
                image: "docker:" + dind,
                privileged: true,
                volumes: [
                    {
                        name: "dockersock",
                        path: "/var/run"
                    }
                ]
            },
            {
                name: name + "." + distro + ".com",
                image: "syncloud/platform-" + distro + "-" + arch + ":" + platform,
                privileged: true,
                volumes: [
                    {
                        name: "dbus",
                        path: "/var/run/dbus"
                    },
                    {
                        name: "dev",
                        path: "/dev"
                    }
                ]
            }
        ] + ( if test_ui then [
            {
                name: "selenium",
                image: "selenium/standalone-" + browser + ":" + selenium_ver,
                environment: {
                    SE_NODE_SESSION_TIMEOUT: "999999"
                },
                volumes: [{
                    name: "shm",
                    path: "/dev/shm"
                }]
            }
        ] else [] ),
        volumes: [
            {
                name: "dockersock",
                temp: {}
            },
            {
                name: "dbus",
                host: {
                    path: "/var/run/dbus"
                }
            },
            {
                name: "dev",
                host: {
                    path: "/dev"
                }
            },
            {
                name: "shm",
                temp: {}
            },
            {
                name: "videos",
                temp: {}
            }
        ]
    },
    {
         kind: "pipeline",
         type: "docker",
         name: "promote-" + arch,
         platform: {
             os: "linux",
             arch: arch
         },
         steps: [
         {
                 name: "promote",
                 image: "debian:" + debian,
                 environment: {
                     AWS_ACCESS_KEY_ID: {
                         from_secret: "AWS_ACCESS_KEY_ID"
                     },
                     AWS_SECRET_ACCESS_KEY: {
                         from_secret: "AWS_SECRET_ACCESS_KEY"
                     }
                 },
                 commands: [
                   "apt update && apt install -y wget",
                   "wget https://github.com/syncloud/snapd/releases/download/1/syncloud-release-" + arch + " -O release --progress=dot:giga",
                   "chmod +x release",
                   "./release promote -n " + name + " -a $(dpkg --print-architecture)"
                 ]
           }
          ],
          trigger: {
           event: [
             "promote"
           ]
         }
     }
];

build("amd64", true) +
build("arm64", false) +
build("arm", false)
