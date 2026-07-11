-- 在管理员连接下执行。请先替换密码，并按实际部署网段收紧 host。
CREATE USER IF NOT EXISTS 'aiquery_readonly'@'127.0.0.1' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT SELECT ON `ai_query`.* TO 'aiquery_readonly'@'127.0.0.1';
FLUSH PRIVILEGES;
