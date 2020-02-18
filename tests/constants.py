import json

__all__ = [
    "PLUGIN_CONFIG",
    "UUID",
    "BAD_UUID",
    "UUID_URL",
    "STATUSES_URL",
    "MISSING_UUID_RESPONSE_BODY",
    "UUID_RESPONSE_BODY",
    "STATUSES_RESPONSE_BODY",
    "NO_ANSIBLE_STATUSES_RESPONSE_BODY",
    "NO_CAPSULES_STATUSES_RESPONSE_BODY",
    "DOWN_CAPSULE_STATUSES_RESPONSE_BODY",
]

PLUGIN_CONFIG = dict(
    username="username", password="password", url="http://localhost", ca_file=None
)
UUID = "dd77f17a-2fe1-4f7a-b220-58f4140a1f9e"
BAD_UUID = "1"
UUID_URL = f"{PLUGIN_CONFIG['url']}/api/settings?search=name%20%3D%20instance_id"
STATUSES_URL = f"{PLUGIN_CONFIG['url']}/api/statuses"
MISSING_UUID_RESPONSE_BODY = json.dumps(
    {
        "total": 230,
        "subtotal": 0,
        "page": 1,
        "per_page": 20,
        "search": "name = instance_id",
        "sort": {"by": None, "order": None},
        "results": [],
    }
)
UUID_RESPONSE_BODY = json.dumps(
    {
        "total": 230,
        "subtotal": 1,
        "page": 1,
        "per_page": 20,
        "search": "name = instance_id",
        "sort": {"by": None, "order": None},
        "results": [
            {
                "value": UUID,
                "description": "Foreman instance ID, uniquely identifies this Foreman instance.",
                "category": "Setting::General",
                "settings_type": "string",
                "default": "uuid",
                "created_at": "2019-11-18 11:51:49 UTC",
                "updated_at": "2019-11-18 11:51:49 UTC",
                "id": 128,
                "name": "instance_id",
                "full_name": "Foreman UUID",
                "category_name": "General",
            }
        ],
    }
)
STATUSES_RESPONSE_BODY = json.dumps(
    {
        "results": {
            "foreman": {
                "version": "1.24.0",
                "api": {"version": "v2"},
                "plugins": [
                    "Foreman plugin: foreman-tasks, 0.17.5, Ivan Ne\u010das, The goal of this plugin is to unify the way of showing task statuses across the Foreman instance.\nIt defines Task model for keeping the information about the tasks and Lock for assigning the tasks\nto resources. The locking allows dealing with preventing multiple colliding tasks to be run on the\nsame resource. It also optionally provides Dynflow infrastructure for using it for managing the tasks.\n",
                    "Foreman plugin: foreman_ansible, 4.0.3, Daniel Lobato Garcia, Ansible integration with Foreman",
                    "Foreman plugin: foreman_bootdisk, 16.0.0, Dominic Cleal, Plugin for Foreman that creates iPXE-based boot disks to provision hosts without the need for PXE infrastructure.",
                    "Foreman plugin: foreman_discovery, 16.0.1, Aditi Puntambekar, alongoldboim, Alon Goldboim, amirfefer, Amit Karsale, Amos Benari, Avi Sharvit, Bryan Kearney, bshuster, Daniel Lobato, Daniel Lobato Garcia, Daniel Lobato Garc\u00eda, Danny Smit, David Davis, Djebran Lezzoum, Dominic Cleal, Eric D. Helms, Ewoud Kohl van Wijngaarden, Frank Wall, Greg Sutcliffe, ChairmanTubeAmp, Ido Kanner, imriz, Imri Zvik, Ivan Ne\u010das, Joseph Mitchell Magen, June Zhang, kgaikwad, Lars Berntzon, ldjebran, Lukas Zapletal, Luk\u00e1\u0161 Zapletal, Marek Hulan, Marek Hul\u00e1n, Martin Ba\u010dovsk\u00fd, Matt Jarvis, Michael Moll, Nick, odovzhenko, Ohad Levy, Ondrej Prazak, Ond\u0159ej Ezr, Ori Rabin, orrabin, Partha Aji, Petr Chalupa, Phirince Philip, Rahul Bajaj, Robert Antoni Buj Gelonch, Scubafloyd, Sean O\\'Keeffe, Sebastian Gra\u0308\u00dfl, Shimon Shtein, Shlomi Zadok, Stephen Benjamin, Swapnil Abnave, Thomas Gelf, Timo Goebel, Tomas Strych, Tom Caspy, Tomer Brisker, and Yann C\u00e9zard, MaaS Discovery Plugin engine for Foreman",
                    "Foreman plugin: foreman_hooks, 0.3.15, Dominic Cleal, Plugin engine for Foreman that enables running custom hook scripts on Foreman events",
                    "Foreman plugin: foreman_inventory_upload, 1.0.2, Inventory upload team, Foreman plugin that process & upload data to cloud based host inventory",
                    "Foreman plugin: foreman_openscap, 2.0.2, slukasik@redhat.com, Foreman plug-in for managing security compliance reports",
                    "Foreman plugin: foreman_remote_execution, 2.0.6, Foreman Remote Execution team, A plugin bringing remote execution to the Foreman, completing the config management functionality with remote management functionality.",
                    "Foreman plugin: foreman_templates, 7.0.5, Greg Sutcliffe, Engine to synchronise provisioning templates from GitHub",
                    "Foreman plugin: foreman_theme_satellite, 5.0.1.5, Alon Goldboim, Shimon Stein, Theme changes for Satellite 6.",
                    "Foreman plugin: foreman_virt_who_configure, 0.5.0, Foreman virt-who-configure team, A plugin to make virt-who configuration easy",
                    "Foreman plugin: katello, 3.14.0.1, N/A, Katello adds Content and Subscription Management to Foreman. For this it relies on Candlepin and Pulp.",
                    "Foreman plugin: redhat_access, 2.2.8, Lindani Phiri, This plugin adds Red Hat Access knowledge base search, case management and diagnostics to Foreman",
                ],
                "smart_proxies": [
                    {
                        "name": "foreman-nuc1.usersys.redhat.com",
                        "status": "ok",
                        "duration_ms": "138",
                        "version": "1.24.0",
                        "features": {
                            "pulp": "1.5.0",
                            "dynflow": "0.2.4",
                            "ansible": "3.0.1",
                            "discovery": "1.0.5",
                            "openscap": "0.7.2",
                            "ssh": "0.2.1",
                            "dns": "1.24.0",
                            "templates": "1.24.0",
                            "tftp": "1.24.0",
                            "dhcp": "1.24.0",
                            "puppetca": "1.24.0",
                            "puppet": "1.24.0",
                            "logs": "1.24.0",
                            "httpboot": "1.24.0",
                        },
                        "failed_features": {},
                    }
                ],
                "compute_resources": [
                    {
                        "name": "libvirt",
                        "status": "ok",
                        "duration_ms": "85",
                        "errors": [],
                    }
                ],
                "database": {"active": True, "duration_ms": "0"},
            },
            "katello": {
                "version": "3.14.0.1",
                "timeUTC": "2020-02-18 19:52:16 UTC",
                "services": {
                    "pulp": {"status": "ok", "duration_ms": "31"},
                    "pulp_auth": {"status": "ok", "duration_ms": "16"},
                    "candlepin": {"status": "ok", "duration_ms": "10"},
                    "candlepin_auth": {"status": "ok", "duration_ms": "12"},
                    "foreman_tasks": {"status": "ok", "duration_ms": "3"},
                    "katello_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                    "candlepin_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                },
                "status": "ok",
            },
        }
    }
)
NO_CAPSULES_STATUSES_RESPONSE_BODY = json.dumps(
    {
        "results": {
            "foreman": {
                "version": "1.24.0",
                "api": {"version": "v2"},
                "plugins": [
                    "Foreman plugin: foreman-tasks, 0.17.5, Ivan Ne\u010das, The goal of this plugin is to unify the way of showing task statuses across the Foreman instance.\nIt defines Task model for keeping the information about the tasks and Lock for assigning the tasks\nto resources. The locking allows dealing with preventing multiple colliding tasks to be run on the\nsame resource. It also optionally provides Dynflow infrastructure for using it for managing the tasks.\n",
                    "Foreman plugin: foreman_ansible, 4.0.3, Daniel Lobato Garcia, Ansible integration with Foreman",
                    "Foreman plugin: foreman_bootdisk, 16.0.0, Dominic Cleal, Plugin for Foreman that creates iPXE-based boot disks to provision hosts without the need for PXE infrastructure.",
                    "Foreman plugin: foreman_discovery, 16.0.1, Aditi Puntambekar, alongoldboim, Alon Goldboim, amirfefer, Amit Karsale, Amos Benari, Avi Sharvit, Bryan Kearney, bshuster, Daniel Lobato, Daniel Lobato Garcia, Daniel Lobato Garc\u00eda, Danny Smit, David Davis, Djebran Lezzoum, Dominic Cleal, Eric D. Helms, Ewoud Kohl van Wijngaarden, Frank Wall, Greg Sutcliffe, ChairmanTubeAmp, Ido Kanner, imriz, Imri Zvik, Ivan Ne\u010das, Joseph Mitchell Magen, June Zhang, kgaikwad, Lars Berntzon, ldjebran, Lukas Zapletal, Luk\u00e1\u0161 Zapletal, Marek Hulan, Marek Hul\u00e1n, Martin Ba\u010dovsk\u00fd, Matt Jarvis, Michael Moll, Nick, odovzhenko, Ohad Levy, Ondrej Prazak, Ond\u0159ej Ezr, Ori Rabin, orrabin, Partha Aji, Petr Chalupa, Phirince Philip, Rahul Bajaj, Robert Antoni Buj Gelonch, Scubafloyd, Sean O\\'Keeffe, Sebastian Gra\u0308\u00dfl, Shimon Shtein, Shlomi Zadok, Stephen Benjamin, Swapnil Abnave, Thomas Gelf, Timo Goebel, Tomas Strych, Tom Caspy, Tomer Brisker, and Yann C\u00e9zard, MaaS Discovery Plugin engine for Foreman",
                    "Foreman plugin: foreman_hooks, 0.3.15, Dominic Cleal, Plugin engine for Foreman that enables running custom hook scripts on Foreman events",
                    "Foreman plugin: foreman_inventory_upload, 1.0.2, Inventory upload team, Foreman plugin that process & upload data to cloud based host inventory",
                    "Foreman plugin: foreman_openscap, 2.0.2, slukasik@redhat.com, Foreman plug-in for managing security compliance reports",
                    "Foreman plugin: foreman_remote_execution, 2.0.6, Foreman Remote Execution team, A plugin bringing remote execution to the Foreman, completing the config management functionality with remote management functionality.",
                    "Foreman plugin: foreman_templates, 7.0.5, Greg Sutcliffe, Engine to synchronise provisioning templates from GitHub",
                    "Foreman plugin: foreman_theme_satellite, 5.0.1.5, Alon Goldboim, Shimon Stein, Theme changes for Satellite 6.",
                    "Foreman plugin: foreman_virt_who_configure, 0.5.0, Foreman virt-who-configure team, A plugin to make virt-who configuration easy",
                    "Foreman plugin: katello, 3.14.0.1, N/A, Katello adds Content and Subscription Management to Foreman. For this it relies on Candlepin and Pulp.",
                    "Foreman plugin: redhat_access, 2.2.8, Lindani Phiri, This plugin adds Red Hat Access knowledge base search, case management and diagnostics to Foreman",
                ],
                "compute_resources": [
                    {
                        "name": "libvirt",
                        "status": "ok",
                        "duration_ms": "85",
                        "errors": [],
                    }
                ],
                "database": {"active": True, "duration_ms": "0"},
            },
            "katello": {
                "version": "3.14.0.1",
                "timeUTC": "2020-02-18 19:52:16 UTC",
                "services": {
                    "pulp": {"status": "ok", "duration_ms": "31"},
                    "pulp_auth": {"status": "ok", "duration_ms": "16"},
                    "candlepin": {"status": "ok", "duration_ms": "10"},
                    "candlepin_auth": {"status": "ok", "duration_ms": "12"},
                    "foreman_tasks": {"status": "ok", "duration_ms": "3"},
                    "katello_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                    "candlepin_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                },
                "status": "ok",
            },
        }
    }
)

NO_ANSIBLE_STATUSES_RESPONSE_BODY = json.dumps(
    {
        "results": {
            "foreman": {
                "version": "1.24.0",
                "api": {"version": "v2"},
                "plugins": [
                    "Foreman plugin: foreman-tasks, 0.17.5, Ivan Ne\u010das, The goal of this plugin is to unify the way of showing task statuses across the Foreman instance.\nIt defines Task model for keeping the information about the tasks and Lock for assigning the tasks\nto resources. The locking allows dealing with preventing multiple colliding tasks to be run on the\nsame resource. It also optionally provides Dynflow infrastructure for using it for managing the tasks.\n",
                    "Foreman plugin: foreman_ansible, 4.0.3, Daniel Lobato Garcia, Ansible integration with Foreman",
                    "Foreman plugin: foreman_bootdisk, 16.0.0, Dominic Cleal, Plugin for Foreman that creates iPXE-based boot disks to provision hosts without the need for PXE infrastructure.",
                    "Foreman plugin: foreman_discovery, 16.0.1, Aditi Puntambekar, alongoldboim, Alon Goldboim, amirfefer, Amit Karsale, Amos Benari, Avi Sharvit, Bryan Kearney, bshuster, Daniel Lobato, Daniel Lobato Garcia, Daniel Lobato Garc\u00eda, Danny Smit, David Davis, Djebran Lezzoum, Dominic Cleal, Eric D. Helms, Ewoud Kohl van Wijngaarden, Frank Wall, Greg Sutcliffe, ChairmanTubeAmp, Ido Kanner, imriz, Imri Zvik, Ivan Ne\u010das, Joseph Mitchell Magen, June Zhang, kgaikwad, Lars Berntzon, ldjebran, Lukas Zapletal, Luk\u00e1\u0161 Zapletal, Marek Hulan, Marek Hul\u00e1n, Martin Ba\u010dovsk\u00fd, Matt Jarvis, Michael Moll, Nick, odovzhenko, Ohad Levy, Ondrej Prazak, Ond\u0159ej Ezr, Ori Rabin, orrabin, Partha Aji, Petr Chalupa, Phirince Philip, Rahul Bajaj, Robert Antoni Buj Gelonch, Scubafloyd, Sean O\\'Keeffe, Sebastian Gra\u0308\u00dfl, Shimon Shtein, Shlomi Zadok, Stephen Benjamin, Swapnil Abnave, Thomas Gelf, Timo Goebel, Tomas Strych, Tom Caspy, Tomer Brisker, and Yann C\u00e9zard, MaaS Discovery Plugin engine for Foreman",
                    "Foreman plugin: foreman_hooks, 0.3.15, Dominic Cleal, Plugin engine for Foreman that enables running custom hook scripts on Foreman events",
                    "Foreman plugin: foreman_inventory_upload, 1.0.2, Inventory upload team, Foreman plugin that process & upload data to cloud based host inventory",
                    "Foreman plugin: foreman_openscap, 2.0.2, slukasik@redhat.com, Foreman plug-in for managing security compliance reports",
                    "Foreman plugin: foreman_remote_execution, 2.0.6, Foreman Remote Execution team, A plugin bringing remote execution to the Foreman, completing the config management functionality with remote management functionality.",
                    "Foreman plugin: foreman_templates, 7.0.5, Greg Sutcliffe, Engine to synchronise provisioning templates from GitHub",
                    "Foreman plugin: foreman_theme_satellite, 5.0.1.5, Alon Goldboim, Shimon Stein, Theme changes for Satellite 6.",
                    "Foreman plugin: foreman_virt_who_configure, 0.5.0, Foreman virt-who-configure team, A plugin to make virt-who configuration easy",
                    "Foreman plugin: katello, 3.14.0.1, N/A, Katello adds Content and Subscription Management to Foreman. For this it relies on Candlepin and Pulp.",
                    "Foreman plugin: redhat_access, 2.2.8, Lindani Phiri, This plugin adds Red Hat Access knowledge base search, case management and diagnostics to Foreman",
                ],
                "smart_proxies": [
                    {
                        "name": "foreman-nuc1.usersys.redhat.com",
                        "status": "ok",
                        "duration_ms": "138",
                        "version": "1.24.0",
                        "features": {
                            "pulp": "1.5.0",
                            "dynflow": "0.2.4",
                            "discovery": "1.0.5",
                            "openscap": "0.7.2",
                            "ssh": "0.2.1",
                            "dns": "1.24.0",
                            "templates": "1.24.0",
                            "tftp": "1.24.0",
                            "dhcp": "1.24.0",
                            "puppetca": "1.24.0",
                            "puppet": "1.24.0",
                            "logs": "1.24.0",
                            "httpboot": "1.24.0",
                        },
                        "failed_features": {},
                    }
                ],
                "compute_resources": [
                    {
                        "name": "libvirt",
                        "status": "ok",
                        "duration_ms": "85",
                        "errors": [],
                    }
                ],
                "database": {"active": True, "duration_ms": "0"},
            },
            "katello": {
                "version": "3.14.0.1",
                "timeUTC": "2020-02-18 19:52:16 UTC",
                "services": {
                    "pulp": {"status": "ok", "duration_ms": "31"},
                    "pulp_auth": {"status": "ok", "duration_ms": "16"},
                    "candlepin": {"status": "ok", "duration_ms": "10"},
                    "candlepin_auth": {"status": "ok", "duration_ms": "12"},
                    "foreman_tasks": {"status": "ok", "duration_ms": "3"},
                    "katello_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                    "candlepin_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                },
                "status": "ok",
            },
        }
    }
)
DOWN_CAPSULE_STATUSES_RESPONSE_BODY = json.dumps(
    {
        "results": {
            "foreman": {
                "version": "1.24.0",
                "api": {"version": "v2"},
                "plugins": [
                    "Foreman plugin: foreman-tasks, 0.17.5, Ivan Ne\u010das, The goal of this plugin is to unify the way of showing task statuses across the Foreman instance.\nIt defines Task model for keeping the information about the tasks and Lock for assigning the tasks\nto resources. The locking allows dealing with preventing multiple colliding tasks to be run on the\nsame resource. It also optionally provides Dynflow infrastructure for using it for managing the tasks.\n",
                    "Foreman plugin: foreman_ansible, 4.0.3, Daniel Lobato Garcia, Ansible integration with Foreman",
                    "Foreman plugin: foreman_bootdisk, 16.0.0, Dominic Cleal, Plugin for Foreman that creates iPXE-based boot disks to provision hosts without the need for PXE infrastructure.",
                    "Foreman plugin: foreman_discovery, 16.0.1, Aditi Puntambekar, alongoldboim, Alon Goldboim, amirfefer, Amit Karsale, Amos Benari, Avi Sharvit, Bryan Kearney, bshuster, Daniel Lobato, Daniel Lobato Garcia, Daniel Lobato Garc\u00eda, Danny Smit, David Davis, Djebran Lezzoum, Dominic Cleal, Eric D. Helms, Ewoud Kohl van Wijngaarden, Frank Wall, Greg Sutcliffe, ChairmanTubeAmp, Ido Kanner, imriz, Imri Zvik, Ivan Ne\u010das, Joseph Mitchell Magen, June Zhang, kgaikwad, Lars Berntzon, ldjebran, Lukas Zapletal, Luk\u00e1\u0161 Zapletal, Marek Hulan, Marek Hul\u00e1n, Martin Ba\u010dovsk\u00fd, Matt Jarvis, Michael Moll, Nick, odovzhenko, Ohad Levy, Ondrej Prazak, Ond\u0159ej Ezr, Ori Rabin, orrabin, Partha Aji, Petr Chalupa, Phirince Philip, Rahul Bajaj, Robert Antoni Buj Gelonch, Scubafloyd, Sean O\\'Keeffe, Sebastian Gra\u0308\u00dfl, Shimon Shtein, Shlomi Zadok, Stephen Benjamin, Swapnil Abnave, Thomas Gelf, Timo Goebel, Tomas Strych, Tom Caspy, Tomer Brisker, and Yann C\u00e9zard, MaaS Discovery Plugin engine for Foreman",
                    "Foreman plugin: foreman_hooks, 0.3.15, Dominic Cleal, Plugin engine for Foreman that enables running custom hook scripts on Foreman events",
                    "Foreman plugin: foreman_inventory_upload, 1.0.2, Inventory upload team, Foreman plugin that process & upload data to cloud based host inventory",
                    "Foreman plugin: foreman_openscap, 2.0.2, slukasik@redhat.com, Foreman plug-in for managing security compliance reports",
                    "Foreman plugin: foreman_remote_execution, 2.0.6, Foreman Remote Execution team, A plugin bringing remote execution to the Foreman, completing the config management functionality with remote management functionality.",
                    "Foreman plugin: foreman_templates, 7.0.5, Greg Sutcliffe, Engine to synchronise provisioning templates from GitHub",
                    "Foreman plugin: foreman_theme_satellite, 5.0.1.5, Alon Goldboim, Shimon Stein, Theme changes for Satellite 6.",
                    "Foreman plugin: foreman_virt_who_configure, 0.5.0, Foreman virt-who-configure team, A plugin to make virt-who configuration easy",
                    "Foreman plugin: katello, 3.14.0.1, N/A, Katello adds Content and Subscription Management to Foreman. For this it relies on Candlepin and Pulp.",
                    "Foreman plugin: redhat_access, 2.2.8, Lindani Phiri, This plugin adds Red Hat Access knowledge base search, case management and diagnostics to Foreman",
                ],
                "smart_proxies": [
                    {
                        "name": "foreman-nuc1.usersys.redhat.com",
                        "status": "error",
                        "duration_ms": "138",
                        "version": "1.24.0",
                        "features": {
                            "pulp": "1.5.0",
                            "dynflow": "0.2.4",
                            "ansible": "3.0.1",
                            "discovery": "1.0.5",
                            "openscap": "0.7.2",
                            "ssh": "0.2.1",
                            "dns": "1.24.0",
                            "templates": "1.24.0",
                            "tftp": "1.24.0",
                            "dhcp": "1.24.0",
                            "puppetca": "1.24.0",
                            "puppet": "1.24.0",
                            "logs": "1.24.0",
                            "httpboot": "1.24.0",
                        },
                        "failed_features": {},
                    }
                ],
                "compute_resources": [
                    {
                        "name": "libvirt",
                        "status": "ok",
                        "duration_ms": "85",
                        "errors": [],
                    }
                ],
                "database": {"active": True, "duration_ms": "0"},
            },
            "katello": {
                "version": "3.14.0.1",
                "timeUTC": "2020-02-18 19:52:16 UTC",
                "services": {
                    "pulp": {"status": "ok", "duration_ms": "31"},
                    "pulp_auth": {"status": "ok", "duration_ms": "16"},
                    "candlepin": {"status": "ok", "duration_ms": "10"},
                    "candlepin_auth": {"status": "ok", "duration_ms": "12"},
                    "foreman_tasks": {"status": "ok", "duration_ms": "3"},
                    "katello_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                    "candlepin_events": {
                        "status": "ok",
                        "message": "0 Processed, 0 Failed",
                        "duration_ms": "0",
                    },
                },
                "status": "ok",
            },
        }
    }
)
