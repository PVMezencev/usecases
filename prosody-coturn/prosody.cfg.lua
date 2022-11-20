-- Prosody Example Configuration File
--
-- Information on configuring Prosody can be found on our
-- website at https://prosody.im/doc/configure
--
-- Tip: You can check that the syntax of this file is correct
-- when you have finished by running this command:
--     prosodyctl check config
-- If there are any errors, it will let you know what and where
-- they are, otherwise it will keep quiet.
--
-- The only thing left to do is rename this file to remove the .dist ending, and fill in the
-- blanks. Good luck, and happy Jabbering!


---------- Server-wide settings ----------
-- Settings in this section apply to the whole server and are the default settings
-- for any virtual hosts

-- This is a (by default, empty) list of accounts that are admins
-- for the server. Note that you must create the accounts separately
-- (see https://prosody.im/doc/creating_accounts for info)
-- Example: admins = { "user1@example.com", "user2@example.net" }
admins = { "user1@example.com" }

-- Enable use of libevent for better performance under high load
-- For more information see: https://prosody.im/doc/libevent
--use_libevent = true

-- Prosody will always look in its source directory for modules, but
-- this option allows you to specify additional locations where Prosody
-- will look for modules first. For community modules, see https://modules.prosody.im/
-- For a local administrator it's common to place local modifications
-- under /usr/local/ hierarchy:
-- plugin_paths = { "/usr/local/lib/prosody/modules" }
plugin_paths = { "/opt/prosody-modules/" }

-- This is the list of modules Prosody will load on startup.
-- It looks for mod_modulename.lua in the plugins folder, so make sure that exists too.
-- Documentation for bundled modules can be found at: https://prosody.im/doc/modules
modules_enabled = {
                -- Wichtige Module
                        "roster";
                        "saslauth";
                        "tls";
                        "dialback";
                        "disco";

                -- Empfohlene Module
                        "private";
                        "profile";
                        "offline";
                        "admin_adhoc";
                        "admin_telnet";
                        "http_files";
                        "legacyauth";
                        "version";
                        "uptime";
                        "time";
                        "ping";
                        "register";
                        "posix";
                        "bosh";
                        "announce";
--                        "proxy65";
                        "pep";
                        "smacks";
                        "carbons";
                        "blocklist";
                        "csi";
                        "csi_battery_saver";
                        "mam";
                        "lastlog";
                        "list_inactive";
                        "cloud_notify";
                        "compat_dialback";
                        "throttle_presence";
                        "log_auth";
                        "server_contact_info";
                        "websocket";
                        "bookmarks";
                        "privacy_lists";
--                        "pubsub";
                        "filter_chatstates";
                        "vcard_legacy"; 
                        "pinger";
--                        "turncredentials";
			"http_upload_external";
			"register_web";
			"http_altconnect";
			"conversejs";
			"turn_external";
			"external_services";
			"extdisco";
}

-- These modules are auto-loaded, but should you want
-- to disable them then uncomment them here:
modules_disabled = {
	-- "offline"; -- Store offline messages
	-- "c2s"; -- Handle client connections
	-- "s2s"; -- Handle server-to-server connections
}

-- Disable account creation by default, for security
-- For more information see https://prosody.im/doc/creating_accounts
allow_registration = false

-- Debian:
--   Do not send the server to background, either systemd or start-stop-daemon take care of that.
--
daemonize = false;

-- Debian:
--   Please, don't change this option since /run/prosody/
--   is one of the few directories Prosody is allowed to write to
--
pidfile = "/run/prosody/prosody.pid";

-- Force clients to use encrypted connections? This option will
-- prevent clients from authenticating unless they are using encryption.

c2s_require_encryption = true

-- Force servers to use encrypted connections? This option will
-- prevent servers from authenticating unless they are using encryption.

s2s_require_encryption = true

-- Force certificate authentication for server-to-server connections?

s2s_secure_auth = true

-- Some servers have invalid or self-signed certificates. You can list
-- remote domains here that will not be required to authenticate using
-- certificates. They will be authenticated using DNS instead, even
-- when s2s_secure_auth is enabled.

--s2s_insecure_domains = { "insecure.example" }

-- Even if you disable s2s_secure_auth, you can still require valid
-- certificates for some domains by specifying a list here.

--s2s_secure_domains = { "jabber.org" }

-- Enable rate limits for incoming client and server connections

limits = {
  c2s = {
    rate = "10kb/s";
  };
  s2sin = {
    rate = "30kb/s";
  };
}

-- Select the authentication backend to use. The 'internal' providers
-- use Prosody's configured data storage to store the authentication data.

-- Select the storage backend to use. By default Prosody uses flat files
-- in its configured data directory, but it also supports more backends
-- through modules. An "sql" backend is included by default, but requires
-- additional dependencies. See https://prosody.im/doc/storage for more info.

--storage = "sql" -- Default is "internal" (Debian: "sql" requires one of the
-- lua-dbi-sqlite3, lua-dbi-mysql or lua-dbi-postgresql packages to work)

-- For the "sql" backend, you can uncomment *one* of the below to configure:
--sql = { driver = "SQLite3", database = "prosody.sqlite" } -- Default. 'database' is the filename.
--sql = { driver = "MySQL", database = "prosody", username = "prosody", password = "secret", host = "localhost" }
--sql = { driver = "PostgreSQL", database = "prosody", username = "prosody", password = "secret", host = "localhost" }


-- Archiving configuration
-- If mod_mam is enabled, Prosody will store a copy of every message. This
-- is used to synchronize conversations between multiple clients, even if
-- they are offline. This setting controls how long Prosody will keep
-- messages in the archive before removing them.

default_archive_policy = true;
archive_expires_after = "1d" -- Remove archived messages after 1 week

-- You can also configure messages to be stored in-memory only. For more
-- archiving options, see https://prosody.im/doc/modules/mod_mam

-- Logging configuration
-- For advanced logging see https://prosody.im/doc/logging
--
-- Debian:
--  Logs info and higher to /var/log
--  Logs errors to syslog also
log = {
	-- Log files (change 'info' to 'debug' for debug logs):
	-- info = "/var/log/prosody/prosody.log";
	-- error = "/var/log/prosody/prosody.err";
    debug = "/var/log/prosody/debug.log";
    info = "/var/log/prosody/info.log";
    warn = "/var/log/prosody/warn.log";
    error = "/var/log/prosody/error.log";
	-- Syslog:
--	{ levels = { "debug" }; to = "syslog";  };
}

-- Uncomment to enable statistics
-- For more info see https://prosody.im/doc/statistics
-- statistics = "internal"

-- Certificates
-- Every virtual host and component needs a certificate so that clients and
-- servers can securely verify its identity. Prosody will automatically load
-- certificates/keys from the directory specified here.
-- For more information, including how to use 'prosodyctl' to auto-import certificates
-- (from e.g. Let's Encrypt) see https://prosody.im/doc/certificates

-- Location of directory to find certificates in (relative to main config file):
certificates = "certs"

-- HTTPS currently only supports a single certificate, specify it here:
--https_certificate = "/etc/prosody/certs/localhost.crt"

----------- Virtual hosts -----------
-- You need to add a VirtualHost entry for each domain you wish Prosody to serve.
-- Settings under each VirtualHost entry apply *only* to that host.
-- It's customary to maintain VirtualHost entries in separate config files
-- under /etc/prosody/conf.d/ directory. Examples of such config files can
-- be found in /etc/prosody/conf.avail/ directory.

------ Additional config files ------
-- For organizational purposes you may prefer to add VirtualHost and
-- Component definitions in their own config files. This line includes
-- all config files in /etc/prosody/conf.d/

--VirtualHost "example.com"
--	certificate = "/path/to/example.crt"

------ Components ------
-- You can specify components to add hosts that provide special services,
-- like multi-user conferences, and transports.
-- For more information on components, see https://prosody.im/doc/components

---Set up a MUC (multi-user chat) room server on conference.example.com:
--Component "conference.example.com" "muc"
--- Store MUC messages in an archive and allow users to access it
--modules_enabled = { "muc_mam" }

---Set up an external component (default component port is 5347)
--
-- External components allow adding various services, such as gateways/
-- transports to other networks like ICQ, MSN and Yahoo. For more info
-- see: https://prosody.im/doc/components#adding_an_external_component
--
--Component "gateway.example.com"
--	component_secret = "password"

---Хранить всё в БД---
default_storage = "sql"
sql = {
    driver = "PostgreSQL";
    database = "prosodyuser";
    host = "127.0.0.1";
    port = 5432;
    username = "prosodyuser";
    password = "password";
}


sql_manage_tables = true

---http
http_host = "127.0.0.1"
http_ports = { 5280 }
https_ports = { }
http_interfaces = { "127.0.0.1" }
trusted_proxies = { "127.0.0.1" }


---Методы шифрования---

ssl = {
	--key = "/etc/prosody/certs/chat.example-domain.me.key";
        --certificate = "/etc/prosody/certs/chat.example-domain.me.crt";
        
options = { "no_sslv3", "no_sslv2", "no_ticket", "no_compression", "cipher_server_preference", "single_dh_use", "single_ecdh_use" };
ciphers="EECDH+ECDSA+AESGCM:EECDH+aRSA+AESGCM:EECDH+ECDSA+SHA384:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA384:EECDH+aRSA+SHA256:EECDH+aRSA+RC4:EECDH:EDH+aRSA:!aNULL:!eNULL:!LOW:!3DES:!MD5:!EXP:!PSK:!SRP:!DSS:!RC4:AES256-GCM-SHA384";
protocol = "tlsv1_1+";
dhparam = "/etc/prosody/certs/dh-2048.pem";
}


---EXTERNAL HTTP UPLOAD---
http_upload_external_base_url = "https://upload.example-domain.me/"
http_upload_external_secret = "password"
http_upload_external_file_size_limit = 536870912 --4Gb

---шаблон для веб регистрации---
--register_web_template = "/etc/prosody/register-templates/Prosody-Web-Registration-Theme"
---Websocket---
consider_websocket_secure = true;
cross_domain_websocket = true;
---настройки веб клиента---
conversejs_options = {
    debug = false;
    view_mode = "fullscreen";
}
conversejs_tags = {
        -- Load libsignal-protocol.js for OMEMO support (GPLv3; be aware of licence implications)
        [[<script src="https://cdn.conversejs.org/3rdparty/libsignal-protocol.min.js"></script>]];
}

---cross_domain_bosh = true;
consider_bosh_secure = true;
---TURN STUN для звонков---
turn_external_host = "turn.example-domain.me"
turn_external_port = 3478
turn_external_secret = "ext_password"

-- Turn & Stun credential config
--turncredentials_secret = "ext_password"
--turncredentials_host = "turn.example-domain.me"
--turncredentials_port = "3478"
--turncredentials_ttl = "86400"

external_service_secret = "ext_password"
external_services = {
    {
        type = "stun",
	transport = "udp",
        host = "turn.example-domain.me",        
	port = "3478",
    },
    {
        type = "turn",
        transport = "udp",
        host = "turn.example-domain.me",
        port = "3478",
	secret = true,
	ttl = 86400,
	algorithm = "turn",
    },
    {
        type = "turns",
        transport = "tcp",
        host = "turn.example-domain.me",
        port = "5349",
	secret = true,
	ttl = 86400,
	algorithm = "turn",
    }
}
contact_info = {
  abuse         = { "mailto:username@yandex.ru", "xmpp:username@yandex.ru" };
  admin         = { "mailto:username@yandex.ru", "xmpp:username@yandex.ru" };
  feedback      = { "mailto:username@yandex.ru", "xmpp:username@yandex.ru" };
  sales         = { "mailto:username@yandex.ru", "xmpp:username@yandex.ru" };
  security      = { "mailto:username@yandex.ru", "xmpp:username@yandex.ru" };
  support       = { "mailto:username@yandex.ru", "xmpp:username@yandex.ru" };
};

--legacy_ssl_ports = { 5223 }
c2s_direct_tls_ports = { 5223 }
c2s_direct_tls_ssl = {
  certificate = "/etc/prosody/certs/chat.example-domain.me.crt";
  key = "/etc/prosody/certs/chat.example-domain.me.key";
}

---domain---
VirtualHost "chat.example-domain.me"
	disco_items = {
	    { "conference.example-domain.me", "chat.example-domain.me MUC" };
	}

http_host = "chat.example-domain.me"
http_external_url = "https://chat.example-domain.me/"
authentication = "internal_hashed"


Component "conference.example-domain.me" "muc"
        name = "chat.example-domain.me chatrooms"
--        restrict_room_creation = "local"
        restrict_room_creation = false
        muc_room_default_public = false
        muc_room_default_members_only = true
        muc_room_default_language = "ru"
        max_history_messages = 500
                modules_enabled = {
                        "muc_mam";
                        "vcard_muc";
                        "muc_cloud_notify";
                        "omemo_all_access";
                }
                 muc_log_by_default = true
	ssl = {
	  certificate = "/etc/prosody/certs/conference.example-domain.me.crt";
	  key = "/etc/prosody/certs/conference.example-domain.me.key";
	}


Component "pubsub.example-domain.me" "pubsub"

Component "proxy.example-domain.me" "proxy65"
	proxy65_address = "upload.example-domain.me"
	proxy65_acl = { "chat.example-domain.me" }

--Include "conf.d/*.cfg.lua"
