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
    `id`        int(11)    NOT NULL AUTO_INCREMENT,
    `imgid`     char(16)   NOT NULL COMMENT '图片uid',
    `server`    char(4)             DEFAULT NULL COMMENT '游戏服务器',
    `scene`     varchar(32)         DEFAULT NULL COMMENT '掉落场景',
    `error`     tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否出现错误',
    `error_msg` varchar(255)        DEFAULT NULL COMMENT '错误信息',
    PRIMARY KEY (`id`),
    UNIQUE KEY `id` (`id`),
    UNIQUE KEY `imgid` (`imgid`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

-- Table: `azurstat_data.research_projects`
CREATE TABLE IF NOT EXISTS `research_projects`
(
    `id`           int(11)    NOT NULL AUTO_INCREMENT,
    `imgid`        char(16)   NOT NULL COMMENT '图片uid',
    `server`       char(4)             DEFAULT NULL COMMENT '游戏服务器',
    `focus_series` tinyint(4) NOT NULL DEFAULT '0' COMMENT '科研倾向',
    `series`       tinyint(4) NOT NULL DEFAULT '0' COMMENT '科研期数',
    `project`      varchar(16)         DEFAULT NULL COMMENT '科研名称',
    PRIMARY KEY (`id`),
    UNIQUE KEY `id` (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

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