CREATE DATABASE IF NOT EXISTS `ai_query` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ai_query`;

CREATE TABLE IF NOT EXISTS `aiquery_schema_version` (
  `component` VARCHAR(80) PRIMARY KEY,
  `version` INT NOT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `category` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `category_name` VARCHAR(100) NOT NULL,
  `parent_id` BIGINT NULL,
  `level` INT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `product` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `product_name` VARCHAR(160) NOT NULL,
  `category_id` BIGINT NULL,
  `brand` VARCHAR(100) NULL,
  `price` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `stock` INT NOT NULL DEFAULT 0,
  `cost` DECIMAL(12,2) NOT NULL DEFAULT 0,
  KEY `idx_product_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_name` VARCHAR(100) NOT NULL,
  `province` VARCHAR(60) NULL,
  `city` VARCHAR(60) NULL,
  `member_level` VARCHAR(40) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `orders` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `order_no` VARCHAR(64) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `total_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `discount_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `channel` VARCHAR(60) NULL,
  `region` VARCHAR(60) NULL,
  `province` VARCHAR(60) NULL,
  `order_status` VARCHAR(40) NOT NULL DEFAULT 'paid',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_orders_order_no` (`order_no`),
  KEY `idx_orders_user` (`user_id`),
  KEY `idx_orders_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `order_item` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `order_id` BIGINT NOT NULL,
  `product_id` BIGINT NOT NULL,
  `quantity` INT NOT NULL DEFAULT 1,
  `unit_price` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `line_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  KEY `idx_order_item_order` (`order_id`),
  KEY `idx_order_item_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `purchase_record` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `product_id` BIGINT NOT NULL,
  `purchase_quantity` INT NOT NULL DEFAULT 0,
  `purchase_amount` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `supplier` VARCHAR(120) NULL,
  `purchased_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_purchase_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `chat_record` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `session_id` VARCHAR(80) NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `content` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_chat_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `query_example` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `question` VARCHAR(300) NOT NULL,
  `is_active` TINYINT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `schema_metadata` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `table_name` VARCHAR(80) NOT NULL,
  `column_name` VARCHAR(80) NOT NULL,
  `business_name` VARCHAR(120) NULL,
  `description` VARCHAR(300) NULL,
  `is_metric` TINYINT NOT NULL DEFAULT 0,
  `sort_order` INT NOT NULL DEFAULT 0,
  UNIQUE KEY `uk_schema_metadata` (`table_name`, `column_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `category` (`id`, `category_name`, `parent_id`, `level`) VALUES
  (1, '手机数码', NULL, 1),
  (2, '家用电器', NULL, 1),
  (3, '办公用品', NULL, 1)
ON DUPLICATE KEY UPDATE `category_name` = VALUES(`category_name`);

INSERT INTO `product` (`id`, `product_name`, `category_id`, `brand`, `price`, `stock`, `cost`) VALUES
  (1, '智能手机 A1', 1, 'Nova', 2999.00, 120, 2100.00),
  (2, '无线耳机 Pro', 1, 'Nova', 699.00, 260, 360.00),
  (3, '空气净化器 X', 2, 'HomeMax', 1299.00, 80, 760.00),
  (4, '人体工学椅', 3, 'OfficeGo', 899.00, 60, 520.00)
ON DUPLICATE KEY UPDATE `product_name` = VALUES(`product_name`);

INSERT INTO `user` (`id`, `user_name`, `province`, `city`, `member_level`) VALUES
  (1, '张三', '浙江', '杭州', '金卡'),
  (2, '李四', '上海', '上海', '银卡'),
  (3, '王五', '广东', '深圳', '普通')
ON DUPLICATE KEY UPDATE `user_name` = VALUES(`user_name`);

INSERT INTO `orders` (`id`, `order_no`, `user_id`, `total_amount`, `discount_amount`, `channel`, `region`, `province`, `order_status`, `created_at`) VALUES
  (1, 'A20260501001', 1, 3698.00, 100.00, '小程序', '华东', '浙江', 'paid', '2026-05-01 10:00:00'),
  (2, 'A20260503001', 2, 1299.00, 0.00, '官网', '华东', '上海', 'paid', '2026-05-03 14:30:00'),
  (3, 'A20260505001', 3, 1798.00, 50.00, '门店', '华南', '广东', 'paid', '2026-05-05 18:20:00')
ON DUPLICATE KEY UPDATE `total_amount` = VALUES(`total_amount`);

INSERT INTO `order_item` (`id`, `order_id`, `product_id`, `quantity`, `unit_price`, `line_amount`) VALUES
  (1, 1, 1, 1, 2999.00, 2999.00),
  (2, 1, 2, 1, 699.00, 699.00),
  (3, 2, 3, 1, 1299.00, 1299.00),
  (4, 3, 4, 2, 899.00, 1798.00)
ON DUPLICATE KEY UPDATE `line_amount` = VALUES(`line_amount`);

INSERT INTO `purchase_record` (`id`, `product_id`, `purchase_quantity`, `purchase_amount`, `supplier`, `purchased_at`) VALUES
  (1, 1, 100, 210000.00, '华东供应链', '2026-04-15 09:00:00'),
  (2, 2, 200, 72000.00, '华东供应链', '2026-04-16 09:00:00'),
  (3, 3, 80, 60800.00, '家电供应商', '2026-04-20 09:00:00')
ON DUPLICATE KEY UPDATE `purchase_amount` = VALUES(`purchase_amount`);

INSERT INTO `query_example` (`id`, `question`, `is_active`) VALUES
  (1, '本月订单 GMV 是多少？', 1),
  (2, '各省份订单金额排名', 1),
  (3, '查询所有商品名称和价格', 1),
  (4, '各类目商品销量对比图', 1)
ON DUPLICATE KEY UPDATE `question` = VALUES(`question`), `is_active` = VALUES(`is_active`);

INSERT INTO `schema_metadata` (`table_name`, `column_name`, `business_name`, `description`, `is_metric`, `sort_order`) VALUES
  ('orders', 'total_amount', '订单金额/GMV', '订单成交金额，常用于 GMV、销售额、成交额统计', 1, 10),
  ('orders', 'discount_amount', '优惠金额', '订单优惠金额', 1, 20),
  ('order_item', 'quantity', '销量', '订单明细中的商品购买数量', 1, 30),
  ('order_item', 'line_amount', '明细金额', '订单明细行金额', 1, 40),
  ('product', 'price', '商品价格', '商品当前销售价格', 1, 50),
  ('product', 'stock', '库存', '商品当前库存数量', 1, 60)
ON DUPLICATE KEY UPDATE
  `business_name` = VALUES(`business_name`),
  `description` = VALUES(`description`),
  `is_metric` = VALUES(`is_metric`),
  `sort_order` = VALUES(`sort_order`);
