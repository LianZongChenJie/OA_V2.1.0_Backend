# 修改行政区划自增属性
ALTER TABLE oa20_dev.oa_area MODIFY COLUMN id int(11) unsigned NOT NULL;

#售票管理，开票状态添加未开票状态
ALTER TABLE oa20_dev.oa_ticket MODIFY COLUMN open_status tinyint(1) unsigned DEFAULT 1 NULL COMMENT '开票状态：0,未开票，1正常 2已作废';
