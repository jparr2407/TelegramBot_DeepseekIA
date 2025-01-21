CREATE TABLE `historico_mensagens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(30) NOT NULL,
  `mensagem` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`)
);