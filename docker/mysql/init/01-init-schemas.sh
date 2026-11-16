#!/bin/bash
set -euo pipefail

create_db() {
  local db="$1" user="$2" pass="$3"
  mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${db}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS '${user}'@'%' IDENTIFIED BY '${pass}';
GRANT ALL PRIVILEGES ON \`${db}\`.* TO '${user}'@'%';
SQL
}

create_db auth_db auth_user "${DB_AUTH_PASSWORD}"
create_db shop_db shop_user "${DB_SHOP_PASSWORD}"
create_db cart_db cart_user "${DB_CART_PASSWORD}"
create_db order_db order_user "${DB_ORDER_PASSWORD}"
create_db audit_db audit_user "${DB_AUDIT_PASSWORD}"
create_db payment_db payment_user "${DB_PAYMENT_PASSWORD}"
create_db notification_db notification_user "${DB_NOTIFICATION_PASSWORD}"
