/*!40101 SET @OLD_CHARACTER_SET_CLIENT = @@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS = 0 */;
/*!40101 SET @OLD_SQL_MODE = @@SQL_MODE, SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES = @@SQL_NOTES, SQL_NOTES = 0 */;

-- Database: `azurstat_data`
CREATE DATABASE IF NOT EXISTS `azurstat_data` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `azurstat_data`;

-- Table: `azurstat_data.parse_records`
CREATE TABLE IF NOT EXISTS `parse_records`
(
    `id`        INT(11)      NOT NULL AUTO_INCREMENT,
    `imgid`     CHAR(16)     NOT NULL COMMENT '图片uid' COLLATE 'utf8_general_ci',
    `server`    CHAR(4)      NULL     DEFAULT NULL COMMENT '游戏服务器' COLLATE 'utf8_general_ci',
    `scene`     VARCHAR(32)  NULL     DEFAULT NULL COMMENT '掉落场景' COLLATE 'utf8_general_ci',
    `error`     TINYINT(4)   NOT NULL DEFAULT '0' COMMENT '是否出现错误',
    `error_msg` VARCHAR(255) NULL     DEFAULT NULL COMMENT '错误信息' COLLATE 'utf8_general_ci',
    PRIMARY KEY (`id`) USING BTREE,
    UNIQUE INDEX `id` (`id`) USING BTREE,
    UNIQUE INDEX `imgid` (`imgid`) USING BTREE,
    INDEX `scene` (`scene`, `imgid`) USING BTREE
)
    COLLATE = 'utf8_general_ci'
    ENGINE = InnoDB
;

-- Table: `azurstat_data.research_projects`
CREATE TABLE IF NOT EXISTS `research_projects`
(
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`imgid` CHAR(16) NOT NULL COMMENT '图片uid' COLLATE 'utf8_general_ci',
	`server` CHAR(4) NULL DEFAULT NULL COMMENT '游戏服务器' COLLATE 'utf8_general_ci',
	`series` TINYINT(4) NOT NULL DEFAULT '0' COMMENT '科研期数',
	`project` VARCHAR(16) NULL DEFAULT NULL COMMENT '科研名称' COLLATE 'utf8_general_ci',
	`item` VARCHAR(255) NULL DEFAULT NULL COMMENT '物品名称' COLLATE 'utf8_general_ci',
	`amount` INT(11) NULL DEFAULT NULL COMMENT '物品数量',
	`tag` VARCHAR(16) NULL DEFAULT NULL COMMENT '额外信息，追赶或者BONUS等' COLLATE 'utf8_general_ci',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `id` (`id`) USING BTREE,
	INDEX `samples` (`series`, `project`, `imgid`) USING BTREE,
	INDEX `stats` (`series`, `project`, `item`, `tag`, `imgid`, `amount`) USING BTREE,
	INDEX `imgid` (`imgid`) USING BTREE,
	INDEX `item` (`item`) USING BTREE
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;

-- Table: `azurstat_data.research_items`
CREATE TABLE IF NOT EXISTS `research_items`
(
    `id`      int(11)    NOT NULL AUTO_INCREMENT,
    `imgid`   char(16)   NOT NULL COMMENT '图片uid',
    `server`  char(4)             DEFAULT NULL COMMENT '游戏服务器',
    `series`  tinyint(4) NOT NULL DEFAULT '0' COMMENT '科研期数',
    `project` varchar(16)         DEFAULT NULL COMMENT '科研名称',
    `item`    varchar(255)        DEFAULT NULL COMMENT '物品名称',
    `amount`  int(11)             DEFAULT NULL COMMENT '物品数量',
    `tag`     varchar(16)         DEFAULT NULL COMMENT '额外信息，追赶或者BONUS等',
    PRIMARY KEY (`id`),
    UNIQUE KEY `id` (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8;