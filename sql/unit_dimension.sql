-- ============================================================================
--  unit_dimension.sql -- canonical unit dimension for `energy_database_new`
--
--  Measures are stored in one base unit per domain (TOE, GWh, MW, BCF, t,
--  USD/%/Persons). `dim_unit` lists every unit with its factor to the base
--  unit; `dim_unit_metadata` maps each measure column to its display units.
--  The app converts at render time: value_display = value_base * factor.
--  Safe and idempotent -- it never rewrites fact data.
-- ============================================================================

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 1. Master unit list.  value_in_base = value * to_base
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `dim_unit` (
  `unit_code`  varchar(20)   NOT NULL,
  `domain`     varchar(20)   NOT NULL,
  `unit_name`  varchar(60)   NOT NULL,
  `to_base`    decimal(24,12) NOT NULL COMMENT 'value_in_base = value * to_base',
  `is_base`    tinyint(1)    NOT NULL DEFAULT 0 COMMENT '1 = storage unit of the domain',
  `is_fixed`   tinyint(1)    NOT NULL DEFAULT 0 COMMENT '1 = not convertible (USD, %, Persons)',
  `sort_order` tinyint(4)    NOT NULL DEFAULT 0,
  PRIMARY KEY (`unit_code`),
  KEY `idx_unit_domain` (`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `dim_unit`
  (`unit_code`, `domain`, `unit_name`, `to_base`, `is_base`, `is_fixed`, `sort_order`)
VALUES
  -- Energy (base TOE)
  ('TOE',  'energy', 'Tonne of oil equivalent',            1.000000000000, 1, 0, 1),
  ('MTOE', 'energy', 'Million tonne of oil equivalent',    1000000.000000000000, 0, 0, 2),
  ('KTOE', 'energy', 'Thousand tonne of oil equivalent',   1000.000000000000, 0, 0, 3),
  -- Electricity (base GWh)
  ('GWh',  'electricity', 'Gigawatt hour',                 1.000000000000, 1, 0, 1),
  ('TWh',  'electricity', 'Terawatt hour',                 1000.000000000000, 0, 0, 2),
  ('MWh',  'electricity', 'Megawatt hour',                 0.001000000000, 0, 0, 3),
  -- Power (base MW)
  ('MW',   'power', 'Megawatt',                            1.000000000000, 1, 0, 1),
  ('GW',   'power', 'Gigawatt',                            1000.000000000000, 0, 0, 2),
  ('kW',   'power', 'Kilowatt',                            0.001000000000, 0, 0, 3),
  -- Gas (base BCF)
  ('BCF',   'gas', 'Billion cubic feet',                   1.000000000000, 1, 0, 1),
  ('TCF',   'gas', 'Trillion cubic feet',                  1000.000000000000, 0, 0, 2),
  ('MMSCF', 'gas', 'Million standard cubic feet (= MMCF)', 0.001000000000, 0, 0, 3),
  -- Emission (base t)
  ('t',    'emission', 'Tonne of CO2',                     1.000000000000, 1, 0, 1),
  ('Mt',   'emission', 'Million tonne of CO2',             1000000.000000000000, 0, 0, 2),
  ('kt',   'emission', 'Thousand tonne of CO2',            1000.000000000000, 0, 0, 3),
  -- Economic (fixed, never converted)
  ('USD',     'economic', 'US Dollar',                 1.000000000000, 0, 1, 1),
  ('%',       'economic', 'Percent (ratio)',           1.000000000000, 0, 1, 2),
  ('Persons', 'economic', 'Number of persons',         1.000000000000, 0, 1, 3),
  -- Non-convertible helper units already used inside fact tables
  ('Million USD', 'gas',      'Million US Dollar (LNG import value)', 1.000000000000, 0, 1, 9),
  ('tCO2/MWh',    'emission', 'Emission intensity ratio (tCO2 per MWh)', 1.000000000000, 0, 1, 9)
ON DUPLICATE KEY UPDATE
  `domain`     = VALUES(`domain`),
  `unit_name`  = VALUES(`unit_name`),
  `to_base`    = VALUES(`to_base`),
  `is_base`    = VALUES(`is_base`),
  `is_fixed`   = VALUES(`is_fixed`),
  `sort_order` = VALUES(`sort_order`);

-- ---------------------------------------------------------------------------
-- 2. Domain -> base (storage) unit declaration
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW `v_domain_base_unit` AS
SELECT 'energy'      AS `domain`, 'TOE' AS `base_unit`,
       'Primary energy supply, final consumption, losses, savings' AS `applies_to`
UNION ALL SELECT 'electricity', 'GWh', 'Generation, demand, imports, consumption, T&D losses'
UNION ALL SELECT 'power',       'MW',  'Installed capacity, renewable capacity'
UNION ALL SELECT 'gas',         'BCF', 'Gas production, consumption, reserves, LNG volume'
UNION ALL SELECT 'emission',    't',   'CO2 emissions (mass)'
UNION ALL SELECT 'economic',    'USD', 'GDP, growth %, population -- fixed, not converted';

-- ---------------------------------------------------------------------------
-- 3. Base unit -> display unit conversion ladder with the exact formula
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW `v_unit_conversion` AS
SELECT
  d.`domain`,
  d.`unit_code`  AS `display_unit`,
  CASE WHEN d.`is_fixed` = 1 THEN d.`unit_code` ELSE b.`unit_code` END AS `base_unit`,
  d.`to_base`,
  CASE WHEN d.`is_fixed` = 1 THEN 1.000000000000
       ELSE 1 / d.`to_base` END                                        AS `display_factor`,
  CASE WHEN d.`is_fixed` = 1
       THEN CONCAT(d.`unit_code`, ' (fixed - no conversion)')
       ELSE CONCAT('1 ', d.`unit_code`, ' = ', FORMAT(d.`to_base`, 6), ' ', b.`unit_code`)
  END                                                                  AS `formula`
FROM `dim_unit` d
LEFT JOIN `dim_unit` b
       ON b.`domain` = d.`domain` AND b.`is_base` = 1
ORDER BY d.`domain`, d.`sort_order`;

-- ---------------------------------------------------------------------------
-- 4. Guard rail: compare dim_unit_metadata against dim_unit
--    `status` must be OK for every row -------------------------------------
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW `v_unit_metadata_check` AS
SELECT
  m.`domain`, m.`table_name`, m.`column_name`, m.`base_unit`,
  m.`display_unit`, m.`conversion_factor` AS `db_factor`,
  c.`display_factor`                      AS `expected_factor`,
  CASE WHEN c.`display_factor` IS NULL THEN 'NO MASTER ROW'
       WHEN ABS(m.`conversion_factor` - c.`display_factor`) < 0.000000001 THEN 'OK'
       ELSE 'MISMATCH' END                AS `status`
FROM `dim_unit_metadata` m
LEFT JOIN `v_unit_conversion` c
       ON c.`domain` = m.`domain` AND c.`display_unit` = m.`display_unit`;

-- ---------------------------------------------------------------------------
-- 5. Guard rail: metadata rows that point at a column which does not exist
--    (returns 0 rows in a healthy database) --------------------------------
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW `v_unit_metadata_orphans` AS
SELECT m.`id`, m.`domain`, m.`table_name`, m.`column_name`, m.`display_unit`
FROM `dim_unit_metadata` m
LEFT JOIN `information_schema`.`COLUMNS` c
       ON c.`TABLE_SCHEMA` = DATABASE()
      AND c.`TABLE_NAME`   = m.`table_name`
      AND c.`COLUMN_NAME`  = m.`column_name`
WHERE c.`COLUMN_NAME` IS NULL;

-- ---------------------------------------------------------------------------
-- 6. Template: register a new measure column + all its display units
--    (safe to re-run thanks to the unique key uk_tc_unit)
-- ---------------------------------------------------------------------------
-- INSERT INTO dim_unit_metadata
--   (domain, table_name, column_name, base_unit, display_unit, conversion_factor, is_default)
-- SELECT 'power', 'fact_elec_generation', 'installed_capacity_mw',
--        'MW', u.unit_code, 1 / u.to_base,
--        IF(u.unit_code = 'MW', 1, 0)
-- FROM dim_unit u
-- WHERE u.domain = 'power'
-- ON DUPLICATE KEY UPDATE conversion_factor = VALUES(conversion_factor);

-- ---------------------------------------------------------------------------
-- 7. Verification (run manually after import)
-- ---------------------------------------------------------------------------
-- SELECT * FROM v_domain_base_unit;
-- SELECT * FROM v_unit_conversion ORDER BY domain, display_unit;
-- SELECT status, COUNT(*) FROM v_unit_metadata_check GROUP BY status;
-- SELECT COUNT(*) AS orphans FROM v_unit_metadata_orphans;
