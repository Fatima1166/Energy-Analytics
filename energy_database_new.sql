-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 02, 2026 at 06:21 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `energy_database_new`
--

-- --------------------------------------------------------

--
-- Table structure for table `dim_country`
--

CREATE TABLE `dim_country` (
  `country_id` smallint(5) UNSIGNED NOT NULL,
  `country_name` varchar(100) NOT NULL,
  `country_code` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_country`
--

INSERT INTO `dim_country` (`country_id`, `country_name`, `country_code`) VALUES
(1, 'Afghanistan', 'AFG'),
(2, 'Africa', 'OWID_AFR'),
(3, 'Africa (GCP)', NULL),
(4, 'Albania', 'ALB'),
(5, 'Algeria', 'DZA'),
(6, 'Andorra', 'AND'),
(7, 'Angola', 'AGO'),
(8, 'Anguilla', 'AIA'),
(9, 'Antarctica', 'ATA'),
(10, 'Antigua and Barbuda', 'ATG'),
(11, 'Argentina', 'ARG'),
(12, 'Armenia', 'ARM'),
(13, 'Aruba', 'ABW'),
(14, 'Asia', 'OWID_ASI'),
(15, 'Asia (GCP)', NULL),
(16, 'Asia (excl. China and India)', NULL),
(17, 'Australia', 'AUS'),
(18, 'Austria', 'AUT'),
(19, 'Azerbaijan', 'AZE'),
(20, 'Bahamas', 'BHS'),
(21, 'Bahrain', 'BHR'),
(22, 'Bangladesh', 'BGD'),
(23, 'Barbados', 'BRB'),
(24, 'Belarus', 'BLR'),
(25, 'Belgium', 'BEL'),
(26, 'Belize', 'BLZ'),
(27, 'Benin', 'BEN'),
(28, 'Bermuda', 'BMU'),
(29, 'Bhutan', 'BTN'),
(30, 'Bolivia', 'BOL'),
(31, 'Bonaire Sint Eustatius and Saba', 'BES'),
(32, 'Bosnia and Herzegovina', 'BIH'),
(33, 'Botswana', 'BWA'),
(34, 'Brazil', 'BRA'),
(35, 'British Virgin Islands', 'VGB'),
(36, 'Brunei', 'BRN'),
(37, 'Bulgaria', 'BGR'),
(38, 'Burkina Faso', 'BFA'),
(39, 'Burundi', 'BDI'),
(40, 'Cambodia', 'KHM'),
(41, 'Cameroon', 'CMR'),
(42, 'Canada', 'CAN'),
(43, 'Cape Verde', 'CPV'),
(44, 'Central African Republic', 'CAF'),
(45, 'Central America (GCP)', NULL),
(46, 'Chad', 'TCD'),
(47, 'Chile', 'CHL'),
(48, 'China', 'CHN'),
(49, 'Christmas Island', 'CXR'),
(50, 'Colombia', 'COL'),
(51, 'Comoros', 'COM'),
(52, 'Congo', 'COG'),
(53, 'Cook Islands', 'COK'),
(54, 'Costa Rica', 'CRI'),
(55, 'Cote d\'Ivoire', 'CIV'),
(56, 'Croatia', 'HRV'),
(57, 'Cuba', 'CUB'),
(58, 'Curacao', 'CUW'),
(59, 'Cyprus', 'CYP'),
(60, 'Czechia', 'CZE'),
(61, 'Democratic Republic of Congo', 'COD'),
(62, 'Denmark', 'DNK'),
(63, 'Djibouti', 'DJI'),
(64, 'Dominica', 'DMA'),
(65, 'Dominican Republic', 'DOM'),
(66, 'East Timor', 'TLS'),
(67, 'Ecuador', 'ECU'),
(68, 'Egypt', 'EGY'),
(69, 'El Salvador', 'SLV'),
(70, 'Equatorial Guinea', 'GNQ'),
(71, 'Eritrea', 'ERI'),
(72, 'Estonia', 'EST'),
(73, 'Eswatini', 'SWZ'),
(74, 'Ethiopia', 'ETH'),
(75, 'Europe', 'OWID_EUR'),
(76, 'Europe (GCP)', NULL),
(77, 'Europe (excl. EU-27)', NULL),
(78, 'Europe (excl. EU-28)', NULL),
(79, 'European Union (27)', 'OWID_EU27'),
(80, 'European Union (28)', NULL),
(81, 'Faroe Islands', 'FRO'),
(82, 'Fiji', 'FJI'),
(83, 'Finland', 'FIN'),
(84, 'France', 'FRA'),
(85, 'French Polynesia', 'PYF'),
(86, 'Gabon', 'GAB'),
(87, 'Gambia', 'GMB'),
(88, 'Georgia', 'GEO'),
(89, 'Germany', 'DEU'),
(90, 'Ghana', 'GHA'),
(91, 'Greece', 'GRC'),
(92, 'Greenland', 'GRL'),
(93, 'Grenada', 'GRD'),
(94, 'Guatemala', 'GTM'),
(95, 'Guinea', 'GIN'),
(96, 'Guinea-Bissau', 'GNB'),
(97, 'Guyana', 'GUY'),
(98, 'Haiti', 'HTI'),
(99, 'High-income countries', 'OWID_HIC'),
(100, 'Honduras', 'HND'),
(101, 'Hong Kong', 'HKG'),
(102, 'Hungary', 'HUN'),
(103, 'Iceland', 'ISL'),
(104, 'India', 'IND'),
(105, 'Indonesia', 'IDN'),
(106, 'International aviation', NULL),
(107, 'International shipping', NULL),
(108, 'Iran', 'IRN'),
(109, 'Iraq', 'IRQ'),
(110, 'Ireland', 'IRL'),
(111, 'Israel', 'ISR'),
(112, 'Italy', 'ITA'),
(113, 'Jamaica', 'JAM'),
(114, 'Japan', 'JPN'),
(115, 'Jordan', 'JOR'),
(116, 'Kazakhstan', 'KAZ'),
(117, 'Kenya', 'KEN'),
(118, 'Kiribati', 'KIR'),
(119, 'Kosovo', 'OWID_KOS'),
(120, 'Kuwait', 'KWT'),
(121, 'Kuwaiti Oil Fires (GCP)', NULL),
(122, 'Kyrgyzstan', 'KGZ'),
(123, 'Laos', 'LAO'),
(124, 'Latvia', 'LVA'),
(125, 'Lebanon', 'LBN'),
(126, 'Lesotho', 'LSO'),
(127, 'Liberia', 'LBR'),
(128, 'Libya', 'LBY'),
(129, 'Liechtenstein', 'LIE'),
(130, 'Lithuania', 'LTU'),
(131, 'Low-income countries', 'OWID_LIC'),
(132, 'Lower-middle-income countries', 'OWID_LMC'),
(133, 'Luxembourg', 'LUX'),
(134, 'Macao', 'MAC'),
(135, 'Madagascar', 'MDG'),
(136, 'Malawi', 'MWI'),
(137, 'Malaysia', 'MYS'),
(138, 'Maldives', 'MDV'),
(139, 'Mali', 'MLI'),
(140, 'Malta', 'MLT'),
(141, 'Marshall Islands', 'MHL'),
(142, 'Mauritania', 'MRT'),
(143, 'Mauritius', 'MUS'),
(144, 'Mexico', 'MEX'),
(145, 'Micronesia (country)', 'FSM'),
(146, 'Middle East (GCP)', NULL),
(147, 'Moldova', 'MDA'),
(148, 'Mongolia', 'MNG'),
(149, 'Montenegro', 'MNE'),
(150, 'Montserrat', 'MSR'),
(151, 'Morocco', 'MAR'),
(152, 'Mozambique', 'MOZ'),
(153, 'Myanmar', 'MMR'),
(154, 'Namibia', 'NAM'),
(155, 'Nauru', 'NRU'),
(156, 'Nepal', 'NPL'),
(157, 'Netherlands', 'NLD'),
(158, 'New Caledonia', 'NCL'),
(159, 'New Zealand', 'NZL'),
(160, 'Nicaragua', 'NIC'),
(161, 'Niger', 'NER'),
(162, 'Nigeria', 'NGA'),
(163, 'Niue', 'NIU'),
(164, 'Non-OECD (GCP)', NULL),
(165, 'North America', 'OWID_NAM'),
(166, 'North America (GCP)', NULL),
(167, 'North America (excl. USA)', NULL),
(168, 'North Korea', 'PRK'),
(169, 'North Macedonia', 'MKD'),
(170, 'Norway', 'NOR'),
(171, 'OECD (GCP)', NULL),
(172, 'Oceania', 'OWID_OCE'),
(173, 'Oceania (GCP)', NULL),
(174, 'Oman', 'OMN'),
(175, 'Pakistan', 'PAK'),
(176, 'Palau', 'PLW'),
(177, 'Palestine', 'PSE'),
(178, 'Panama', 'PAN'),
(179, 'Papua New Guinea', 'PNG'),
(180, 'Paraguay', 'PRY'),
(181, 'Peru', 'PER'),
(182, 'Philippines', 'PHL'),
(183, 'Poland', 'POL'),
(184, 'Portugal', 'PRT'),
(185, 'Qatar', 'QAT'),
(186, 'Romania', 'ROU'),
(187, 'Russia', 'RUS'),
(188, 'Rwanda', 'RWA'),
(189, 'Ryukyu Islands (GCP)', NULL),
(190, 'Saint Helena', 'SHN'),
(191, 'Saint Kitts and Nevis', 'KNA'),
(192, 'Saint Lucia', 'LCA'),
(193, 'Saint Pierre and Miquelon', 'SPM'),
(194, 'Saint Vincent and the Grenadines', 'VCT'),
(195, 'Samoa', 'WSM'),
(196, 'Sao Tome and Principe', 'STP'),
(197, 'Saudi Arabia', 'SAU'),
(198, 'Senegal', 'SEN'),
(199, 'Serbia', 'SRB'),
(200, 'Seychelles', 'SYC'),
(201, 'Sierra Leone', 'SLE'),
(202, 'Singapore', 'SGP'),
(203, 'Sint Maarten (Dutch part)', 'SXM'),
(204, 'Slovakia', 'SVK'),
(205, 'Slovenia', 'SVN'),
(206, 'Solomon Islands', 'SLB'),
(207, 'Somalia', 'SOM'),
(208, 'South Africa', 'ZAF'),
(209, 'South America', 'OWID_SAM'),
(210, 'South America (GCP)', NULL),
(211, 'South Korea', 'KOR'),
(212, 'South Sudan', 'SSD'),
(213, 'Spain', 'ESP'),
(214, 'Sri Lanka', 'LKA'),
(215, 'Sudan', 'SDN'),
(216, 'Suriname', 'SUR'),
(217, 'Sweden', 'SWE'),
(218, 'Switzerland', 'CHE'),
(219, 'Syria', 'SYR'),
(220, 'Taiwan', 'TWN'),
(221, 'Tajikistan', 'TJK'),
(222, 'Tanzania', 'TZA'),
(223, 'Thailand', 'THA'),
(224, 'Togo', 'TGO'),
(225, 'Tonga', 'TON'),
(226, 'Trinidad and Tobago', 'TTO'),
(227, 'Tunisia', 'TUN'),
(228, 'Turkey', 'TUR'),
(229, 'Turkmenistan', 'TKM'),
(230, 'Turks and Caicos Islands', 'TCA'),
(231, 'Tuvalu', 'TUV'),
(232, 'Uganda', 'UGA'),
(233, 'Ukraine', 'UKR'),
(234, 'United Arab Emirates', 'ARE'),
(235, 'United Kingdom', 'GBR'),
(236, 'United States', 'USA'),
(237, 'Upper-middle-income countries', 'OWID_UMC'),
(238, 'Uruguay', 'URY'),
(239, 'Uzbekistan', 'UZB'),
(240, 'Vanuatu', 'VUT'),
(241, 'Venezuela', 'VEN'),
(242, 'Vietnam', 'VNM'),
(243, 'Wallis and Futuna', 'WLF'),
(244, 'World', 'OWID_WRL'),
(245, 'Yemen', 'YEM'),
(246, 'Zambia', 'ZMB'),
(247, 'Zimbabwe', 'ZWE');

-- --------------------------------------------------------

--
-- Table structure for table `dim_emission_factor`
--

CREATE TABLE `dim_emission_factor` (
  `factor_id` tinyint(3) UNSIGNED NOT NULL,
  `source_id` tinyint(3) UNSIGNED NOT NULL,
  `fuel_type` varchar(30) NOT NULL,
  `emission_factor_tco2_mwh` decimal(6,4) NOT NULL,
  `reference` varchar(120) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_emission_factor`
--

INSERT INTO `dim_emission_factor` (`factor_id`, `source_id`, `fuel_type`, `emission_factor_tco2_mwh`, `reference`) VALUES
(1, 1, 'Oil', 0.7000, 'IPCC default'),
(2, 2, 'Gas', 0.4000, 'IPCC default'),
(3, 5, 'Coal', 0.9000, 'IPCC default'),
(4, 6, 'Hydro', 0.0000, 'Renewable - zero direct'),
(5, 7, 'Nuclear', 0.0000, 'Zero direct'),
(6, 9, 'Renewable', 0.0000, 'Zero direct');

-- --------------------------------------------------------

--
-- Table structure for table `dim_energy_source`
--

CREATE TABLE `dim_energy_source` (
  `source_id` tinyint(3) UNSIGNED NOT NULL,
  `source_name` varchar(60) NOT NULL,
  `unit` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_energy_source`
--

INSERT INTO `dim_energy_source` (`source_id`, `source_name`, `unit`) VALUES
(1, 'Oil', 'TOE'),
(2, 'Gas', 'TOE'),
(3, 'LNG Imports', 'TOE'),
(4, 'LPG', 'TOE'),
(5, 'Coal', 'TOE'),
(6, 'Hydro Electricity', 'TOE'),
(7, 'Nuclear Electricity', 'TOE'),
(8, 'Imported Electricity', 'TOE'),
(9, 'Renewable Electricity', 'TOE'),
(10, 'Electricity (Final)', 'TOE');

-- --------------------------------------------------------

--
-- Table structure for table `dim_province`
--

CREATE TABLE `dim_province` (
  `province_id` tinyint(3) UNSIGNED NOT NULL,
  `province_name` varchar(60) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_province`
--

INSERT INTO `dim_province` (`province_id`, `province_name`) VALUES
(5, 'AJK'),
(4, 'Balochistan'),
(6, 'Islamabad'),
(7, 'Karachi'),
(3, 'KPK'),
(1, 'Punjab'),
(2, 'Sindh'),
(8, 'Sindh Interior');

-- --------------------------------------------------------

--
-- Table structure for table `dim_sector`
--

CREATE TABLE `dim_sector` (
  `sector_id` tinyint(3) UNSIGNED NOT NULL,
  `sector_name` varchar(60) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_sector`
--

INSERT INTO `dim_sector` (`sector_id`, `sector_name`) VALUES
(4, 'Agriculture'),
(7, 'Bulk Supply'),
(14, 'Cement'),
(2, 'Commercial'),
(1, 'Domestic'),
(11, 'Fertilizer as Feedstock'),
(13, 'Fertilizer in Fuel Use'),
(9, 'General Industries'),
(3, 'Industrial'),
(8, 'Other Govt'),
(10, 'Power'),
(15, 'SSGC'),
(5, 'Street Light'),
(6, 'Traction'),
(12, 'Transport');

-- --------------------------------------------------------

--
-- Table structure for table `dim_unit`
--

CREATE TABLE `dim_unit` (
  `unit_code` varchar(20) NOT NULL,
  `domain` varchar(20) NOT NULL,
  `unit_name` varchar(60) NOT NULL,
  `to_base` decimal(24,12) NOT NULL COMMENT 'value_in_base = value * to_base',
  `is_base` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1 = storage unit of the domain',
  `is_fixed` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1 = not convertible (USD, %, Persons)',
  `sort_order` tinyint(4) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_unit`
--

INSERT INTO `dim_unit` (`unit_code`, `domain`, `unit_name`, `to_base`, `is_base`, `is_fixed`, `sort_order`) VALUES
('%', 'economic', 'Percent (ratio)', 1.000000000000, 0, 1, 2),
('BCF', 'gas', 'Billion cubic feet', 1.000000000000, 1, 0, 1),
('GW', 'power', 'Gigawatt', 1000.000000000000, 0, 0, 2),
('GWh', 'electricity', 'Gigawatt hour', 1.000000000000, 1, 0, 1),
('kt', 'emission', 'Thousand tonne of CO2', 1000.000000000000, 0, 0, 3),
('KTOE', 'energy', 'Thousand tonne of oil equivalent', 1000.000000000000, 0, 0, 3),
('kW', 'power', 'Kilowatt', 0.001000000000, 0, 0, 3),
('Million USD', 'gas', 'Million US Dollar (LNG import value)', 1.000000000000, 0, 1, 9),
('MMSCF', 'gas', 'Million standard cubic feet (= MMCF)', 0.001000000000, 0, 0, 3),
('Mt', 'emission', 'Million tonne of CO2', 1000000.000000000000, 0, 0, 2),
('MTOE', 'energy', 'Million tonne of oil equivalent', 1000000.000000000000, 0, 0, 2),
('MW', 'power', 'Megawatt', 1.000000000000, 1, 0, 1),
('MWh', 'electricity', 'Megawatt hour', 0.001000000000, 0, 0, 3),
('Persons', 'economic', 'Number of persons', 1.000000000000, 0, 1, 3),
('t', 'emission', 'Tonne of CO2', 1.000000000000, 1, 0, 1),
('TCF', 'gas', 'Trillion cubic feet', 1000.000000000000, 0, 0, 2),
('tCO2/MWh', 'emission', 'Emission intensity ratio (tCO2 per MWh)', 1.000000000000, 0, 1, 9),
('TOE', 'energy', 'Tonne of oil equivalent', 1.000000000000, 1, 0, 1),
('TWh', 'electricity', 'Terawatt hour', 1000.000000000000, 0, 0, 2),
('USD', 'economic', 'US Dollar', 1.000000000000, 0, 1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `dim_unit_metadata`
--

CREATE TABLE `dim_unit_metadata` (
  `id` int(11) NOT NULL,
  `domain` varchar(20) NOT NULL,
  `table_name` varchar(60) NOT NULL,
  `column_name` varchar(60) NOT NULL,
  `base_unit` varchar(20) NOT NULL,
  `display_unit` varchar(20) NOT NULL,
  `conversion_factor` decimal(18,10) NOT NULL DEFAULT 1.0000000000,
  `is_default` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_unit_metadata`
--

INSERT INTO `dim_unit_metadata` (`id`, `domain`, `table_name`, `column_name`, `base_unit`, `display_unit`, `conversion_factor`, `is_default`) VALUES
(40, 'energy', 'fact_energy_overview', 'total_primary_supply_toe', 'TOE', 'TOE', 1.0000000000, 0),
(41, 'energy', 'fact_energy_overview', 'total_primary_supply_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(42, 'energy', 'fact_energy_overview', 'total_primary_supply_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(43, 'energy', 'fact_energy_overview', 'total_final_consumption_toe', 'TOE', 'TOE', 1.0000000000, 0),
(44, 'energy', 'fact_energy_overview', 'total_final_consumption_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(45, 'energy', 'fact_energy_overview', 'total_final_consumption_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(46, 'energy', 'fact_energy_overview', 'supply_consumption_gap_toe', 'TOE', 'TOE', 1.0000000000, 0),
(47, 'energy', 'fact_energy_overview', 'supply_consumption_gap_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(48, 'energy', 'fact_energy_overview', 'supply_consumption_gap_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(49, 'energy', 'fact_energy_overview', 'transformation_losses_toe', 'TOE', 'TOE', 1.0000000000, 0),
(50, 'energy', 'fact_energy_overview', 'transformation_losses_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(51, 'energy', 'fact_energy_overview', 'transformation_losses_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(52, 'energy', 'fact_energy_overview', 'td_losses_toe', 'TOE', 'TOE', 1.0000000000, 0),
(53, 'energy', 'fact_energy_overview', 'td_losses_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(54, 'energy', 'fact_energy_overview', 'td_losses_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(55, 'energy', 'fact_energy_overview', 'total_losses_toe', 'TOE', 'TOE', 1.0000000000, 0),
(56, 'energy', 'fact_energy_overview', 'total_losses_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(57, 'energy', 'fact_energy_overview', 'total_losses_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(58, 'energy', 'fact_energy_overview', 'savings_toe', 'TOE', 'TOE', 1.0000000000, 0),
(59, 'energy', 'fact_energy_overview', 'savings_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(60, 'energy', 'fact_energy_overview', 'savings_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(61, 'energy', 'fact_primary_energy_supply', 'supply_toe', 'TOE', 'TOE', 1.0000000000, 0),
(62, 'energy', 'fact_primary_energy_supply', 'supply_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(63, 'energy', 'fact_primary_energy_supply', 'supply_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(64, 'energy', 'fact_final_energy_consumption', 'consumption_toe', 'TOE', 'TOE', 1.0000000000, 0),
(65, 'energy', 'fact_final_energy_consumption', 'consumption_toe', 'TOE', 'KTOE', 0.0010000000, 0),
(66, 'energy', 'fact_final_energy_consumption', 'consumption_toe', 'TOE', 'MTOE', 0.0000010000, 1),
(67, 'electricity', 'fact_elec_generation', 'generation_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(68, 'electricity', 'fact_elec_generation', 'generation_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(69, 'electricity', 'fact_elec_generation', 'generation_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(70, 'electricity', 'fact_elec_generation', 'consumption_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(71, 'electricity', 'fact_elec_generation', 'consumption_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(72, 'electricity', 'fact_elec_generation', 'consumption_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(73, 'electricity', 'fact_elec_generation', 'imports_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(74, 'electricity', 'fact_elec_generation', 'imports_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(75, 'electricity', 'fact_elec_generation', 'imports_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(76, 'electricity', 'fact_renewable_energy', 'gen_solar_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(77, 'electricity', 'fact_renewable_energy', 'gen_solar_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(78, 'electricity', 'fact_renewable_energy', 'gen_solar_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(79, 'electricity', 'fact_renewable_energy', 'gen_wind_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(80, 'electricity', 'fact_renewable_energy', 'gen_wind_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(81, 'electricity', 'fact_renewable_energy', 'gen_wind_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(82, 'electricity', 'fact_renewable_energy', 'gen_hydro_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(83, 'electricity', 'fact_renewable_energy', 'gen_hydro_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(84, 'electricity', 'fact_renewable_energy', 'gen_hydro_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(85, 'electricity', 'fact_renewable_energy', 'gen_coal_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(86, 'electricity', 'fact_renewable_energy', 'gen_coal_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(87, 'electricity', 'fact_renewable_energy', 'gen_coal_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(88, 'electricity', 'fact_renewable_energy', 'gen_gas_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(89, 'electricity', 'fact_renewable_energy', 'gen_gas_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(90, 'electricity', 'fact_renewable_energy', 'gen_gas_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(91, 'electricity', 'fact_renewable_energy', 'gen_nuclear_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(92, 'electricity', 'fact_renewable_energy', 'gen_nuclear_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(93, 'electricity', 'fact_renewable_energy', 'gen_nuclear_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(94, 'electricity', 'fact_renewable_energy', 'demand_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(95, 'electricity', 'fact_renewable_energy', 'demand_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(96, 'electricity', 'fact_renewable_energy', 'demand_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(97, 'electricity', 'fact_td_losses', 'td_losses_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(98, 'electricity', 'fact_td_losses', 'td_losses_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(99, 'electricity', 'fact_td_losses', 'td_losses_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(100, 'electricity', 'fact_elec_province_consumption', 'consumption_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(101, 'electricity', 'fact_elec_province_consumption', 'consumption_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(102, 'electricity', 'fact_elec_province_consumption', 'consumption_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(103, 'electricity', 'fact_elec_sector_consumption', 'consumption_gwh', 'GWh', 'MWh', 1000.0000000000, 0),
(104, 'electricity', 'fact_elec_sector_consumption', 'consumption_gwh', 'GWh', 'GWh', 1.0000000000, 1),
(105, 'electricity', 'fact_elec_sector_consumption', 'consumption_gwh', 'GWh', 'TWh', 0.0010000000, 0),
(106, 'power', 'fact_elec_generation', 'installed_capacity_mw', 'MW', 'kW', 1000.0000000000, 0),
(107, 'power', 'fact_elec_generation', 'installed_capacity_mw', 'MW', 'MW', 1.0000000000, 1),
(108, 'power', 'fact_elec_generation', 'installed_capacity_mw', 'MW', 'GW', 0.0010000000, 0),
(109, 'power', 'fact_renewable_energy', 'capacity_mw', 'MW', 'kW', 1000.0000000000, 0),
(110, 'power', 'fact_renewable_energy', 'capacity_mw', 'MW', 'MW', 1.0000000000, 1),
(111, 'power', 'fact_renewable_energy', 'capacity_mw', 'MW', 'GW', 0.0010000000, 0),
(112, 'power', 'fact_renewable_capacity', 'installed_capacity_mw', 'MW', 'kW', 1000.0000000000, 0),
(113, 'power', 'fact_renewable_capacity', 'installed_capacity_mw', 'MW', 'MW', 1.0000000000, 1),
(114, 'power', 'fact_renewable_capacity', 'installed_capacity_mw', 'MW', 'GW', 0.0010000000, 0),
(115, 'gas', 'fact_natural_gas', 'production_bcf', 'BCF', 'MMSCF', 1000.0000000000, 0),
(116, 'gas', 'fact_natural_gas', 'production_bcf', 'BCF', 'BCF', 1.0000000000, 1),
(117, 'gas', 'fact_natural_gas', 'production_bcf', 'BCF', 'TCF', 0.0010000000, 0),
(118, 'gas', 'fact_natural_gas', 'consumption_bcf', 'BCF', 'MMSCF', 1000.0000000000, 0),
(119, 'gas', 'fact_natural_gas', 'consumption_bcf', 'BCF', 'BCF', 1.0000000000, 1),
(120, 'gas', 'fact_natural_gas', 'consumption_bcf', 'BCF', 'TCF', 0.0010000000, 0),
(121, 'gas', 'fact_gas_sector_consumption', 'consumption_bcf', 'BCF', 'MMSCF', 1000.0000000000, 0),
(122, 'gas', 'fact_gas_sector_consumption', 'consumption_bcf', 'BCF', 'BCF', 1.0000000000, 1),
(123, 'gas', 'fact_gas_sector_consumption', 'consumption_bcf', 'BCF', 'TCF', 0.0010000000, 0),
(124, 'gas', 'fact_gas_province_consumption', 'consumption_bcf', 'BCF', 'MMSCF', 1000.0000000000, 0),
(125, 'gas', 'fact_gas_province_consumption', 'consumption_bcf', 'BCF', 'BCF', 1.0000000000, 1),
(126, 'gas', 'fact_gas_province_consumption', 'consumption_bcf', 'BCF', 'TCF', 0.0010000000, 0),
(127, 'gas', 'fact_lng_imports', 'imports_bcf', 'BCF', 'MMSCF', 1000.0000000000, 0),
(128, 'gas', 'fact_lng_imports', 'imports_bcf', 'BCF', 'BCF', 1.0000000000, 1),
(129, 'gas', 'fact_lng_imports', 'imports_bcf', 'BCF', 'TCF', 0.0010000000, 0),
(130, 'gas', 'fact_gas_reserves', 'proved_reserves_bcf', 'BCF', 'MMSCF', 1000.0000000000, 0),
(131, 'gas', 'fact_gas_reserves', 'proved_reserves_bcf', 'BCF', 'BCF', 1.0000000000, 1),
(132, 'gas', 'fact_gas_reserves', 'proved_reserves_bcf', 'BCF', 'TCF', 0.0010000000, 0),
(133, 'gas', 'fact_lng_imports', 'imports_value_musd', 'Million USD', 'Million USD', 1.0000000000, 1),
(134, 'emission', 'fact_co2_emissions', 'co2_emissions_t', 't', 't', 1.0000000000, 0),
(135, 'emission', 'fact_co2_emissions', 'co2_emissions_t', 't', 'kt', 0.0010000000, 0),
(136, 'emission', 'fact_co2_emissions', 'co2_emissions_t', 't', 'Mt', 0.0000010000, 1),
(137, 'emission', 'fact_economic_indicators', 'co2_emissions_tonnes', 't', 't', 1.0000000000, 0),
(138, 'emission', 'fact_economic_indicators', 'co2_emissions_tonnes', 't', 'kt', 0.0010000000, 0),
(139, 'emission', 'fact_economic_indicators', 'co2_emissions_tonnes', 't', 'Mt', 0.0000010000, 1),
(140, 'emission', 'dim_emission_factor', 'emission_factor_tco2_mwh', 'tCO2/MWh', 'tCO2/MWh', 1.0000000000, 1),
(141, 'emission', 'fact_derived_ef', 'avg_ef_tco2_mwh', 'tCO2/MWh', 'tCO2/MWh', 1.0000000000, 1),
(142, 'economic', 'fact_economic_indicators', 'gdp_current_usd', 'USD', 'USD', 1.0000000000, 1),
(143, 'economic', 'fact_economic_indicators', 'gdp_growth_pct', '%', '%', 1.0000000000, 1),
(144, 'economic', 'fact_economic_indicators', 'population', 'Persons', 'Persons', 1.0000000000, 1);

-- --------------------------------------------------------

--
-- Table structure for table `dim_unit_metadata_backup`
--

CREATE TABLE `dim_unit_metadata_backup` (
  `id` int(11) NOT NULL DEFAULT 0,
  `domain` varchar(20) NOT NULL,
  `table_name` varchar(60) NOT NULL,
  `column_name` varchar(60) NOT NULL,
  `base_unit` varchar(20) NOT NULL,
  `display_unit` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_unit_metadata_backup`
--

INSERT INTO `dim_unit_metadata_backup` (`id`, `domain`, `table_name`, `column_name`, `base_unit`, `display_unit`) VALUES
(1, 'energy', 'fact_energy_overview', 'total_primary_supply_toe', 'TOE', 'TOE'),
(2, 'energy', 'fact_energy_overview', 'total_final_consumption_toe', 'TOE', 'TOE'),
(3, 'energy', 'fact_energy_overview', 'supply_consumption_gap_toe', 'TOE', 'TOE'),
(4, 'energy', 'fact_energy_overview', 'transformation_losses_toe', 'TOE', 'TOE'),
(5, 'energy', 'fact_energy_overview', 'td_losses_toe', 'TOE', 'TOE'),
(6, 'energy', 'fact_energy_overview', 'total_losses_toe', 'TOE', 'TOE'),
(7, 'energy', 'fact_energy_overview', 'savings_toe', 'TOE', 'TOE'),
(8, 'energy', 'fact_primary_energy_supply', 'supply_toe', 'TOE', 'TOE'),
(9, 'energy', 'fact_final_energy_consumption', 'consumption_toe', 'TOE', 'TOE'),
(10, 'electricity', 'fact_elec_generation', 'generation_gwh', 'GWh', 'GWh'),
(11, 'electricity', 'fact_elec_generation', 'consumption_gwh', 'GWh', 'GWh'),
(12, 'electricity', 'fact_elec_generation', 'imports_gwh', 'GWh', 'GWh'),
(13, 'electricity', 'fact_renewable_energy', 'gen_solar_gwh', 'GWh', 'GWh'),
(14, 'electricity', 'fact_renewable_energy', 'gen_wind_gwh', 'GWh', 'GWh'),
(15, 'electricity', 'fact_renewable_energy', 'gen_hydro_gwh', 'GWh', 'GWh'),
(16, 'electricity', 'fact_renewable_energy', 'gen_coal_gwh', 'GWh', 'GWh'),
(17, 'electricity', 'fact_renewable_energy', 'gen_gas_gwh', 'GWh', 'GWh'),
(18, 'electricity', 'fact_renewable_energy', 'gen_nuclear_gwh', 'GWh', 'GWh'),
(19, 'electricity', 'fact_renewable_energy', 'demand_gwh', 'GWh', 'GWh'),
(20, 'electricity', 'fact_td_losses', 'td_losses_gwh', 'GWh', 'GWh'),
(21, 'electricity', 'fact_elec_province_consumption', 'consumption_gwh', 'GWh', 'GWh'),
(22, 'electricity', 'fact_elec_sector_consumption', 'consumption_gwh', 'GWh', 'GWh'),
(23, 'power', 'fact_elec_generation', 'installed_capacity_mw', 'MW', 'MW'),
(24, 'power', 'fact_renewable_energy', 'capacity_mw', 'MW', 'MW'),
(25, 'power', 'fact_renewable_capacity', 'installed_capacity_mw', 'MW', 'MW'),
(26, 'gas', 'fact_natural_gas', 'production_bcf', 'BCF', 'BCF'),
(27, 'gas', 'fact_natural_gas', 'consumption_bcf', 'BCF', 'BCF'),
(28, 'gas', 'fact_gas_sector_consumption', 'consumption_bcf', 'BCF', 'BCF'),
(29, 'gas', 'fact_gas_province_consumption', 'consumption_bcf', 'BCF', 'BCF'),
(30, 'gas', 'fact_lng_imports', 'imports_bcf', 'BCF', 'BCF'),
(31, 'gas', 'fact_gas_reserves', 'proved_reserves_bcf', 'BCF', 'BCF'),
(32, 'emission', 'fact_co2_emissions', 'co2_emissions_t', 't', 't'),
(33, 'emission', 'fact_economic_indicators', 'co2_emissions_tonnes', 't', 't'),
(34, 'economic', 'fact_economic_indicators', 'gdp_current_usd', 'USD', 'USD'),
(35, 'economic', 'fact_economic_indicators', 'gdp_growth_pct', '%', '%'),
(36, 'economic', 'fact_economic_indicators', 'population', 'Persons', 'Persons'),
(37, 'gas', 'fact_lng_imports', 'imports_value_musd', 'Million USD', 'Million USD'),
(38, 'emission', 'dim_emission_factor', 'emission_factor_tco2_mwh', 'tCO2/MWh', 'tCO2/MWh'),
(39, 'emission', 'fact_derived_ef', 'avg_ef_tco2_mwh', 'tCO2/MWh', 'tCO2/MWh');

-- --------------------------------------------------------

--
-- Table structure for table `dim_users`
--

CREATE TABLE `dim_users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(100) DEFAULT 'Energy Analyst',
  `role` varchar(20) DEFAULT 'admin',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_users`
--

INSERT INTO `dim_users` (`user_id`, `username`, `password_hash`, `full_name`, `role`, `created_at`) VALUES
(2, 'admin', '$2b$12$tuhCgdlmz1en6c99ddgwL.QZSbJs.kyywJcy4ZMEmJMmjQHTF7cSq', 'Energy Administrator', 'admin', '2026-09-23 13:19:26');

-- --------------------------------------------------------

--
-- Table structure for table `dim_utility`
--

CREATE TABLE `dim_utility` (
  `utility_id` tinyint(3) UNSIGNED NOT NULL,
  `utility_name` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_utility`
--

INSERT INTO `dim_utility` (`utility_id`, `utility_name`) VALUES
(1, 'SNGPL'),
(2, 'SSGCL');

-- --------------------------------------------------------

--
-- Table structure for table `dim_year`
--

CREATE TABLE `dim_year` (
  `year_id` int(10) UNSIGNED NOT NULL,
  `fiscal_year` varchar(10) NOT NULL COMMENT 'e.g. 2005-06',
  `calendar_year` smallint(5) UNSIGNED DEFAULT NULL COMMENT 'Start calendar year'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dim_year`
--

INSERT INTO `dim_year` (`year_id`, `fiscal_year`, `calendar_year`) VALUES
(1, '1999-2000', 1999),
(2, '2000-01', 2000),
(3, '2001-02', 2001),
(4, '2002-03', 2002),
(5, '2003-04', 2003),
(6, '2004-05', 2004),
(7, '2005-06', 2005),
(8, '2006-07', 2006),
(9, '2007-08', 2007),
(10, '2008-09', 2008),
(11, '2009-10', 2009),
(12, '2010-11', 2010),
(13, '2011-12', 2011),
(14, '2012-13', 2012),
(15, '2013-14', 2013),
(16, '2014-15', 2014),
(17, '2015-16', 2015),
(18, '2016-17', 2016),
(19, '2017-18', 2017),
(20, '2018-19', 2018),
(21, '2019-20', 2019),
(22, '2020-21', 2020),
(23, '2021-22', 2021),
(24, '2022-23', 2022),
(25, '2023-24', 2023),
(26, '2024-25', 2024);

-- --------------------------------------------------------

--
-- Table structure for table `fact_co2_emissions`
--

CREATE TABLE `fact_co2_emissions` (
  `co2_id` int(10) UNSIGNED NOT NULL,
  `country_id` smallint(5) UNSIGNED NOT NULL,
  `calendar_year` smallint(5) UNSIGNED NOT NULL,
  `co2_emissions_t` decimal(20,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_co2_emissions`
--

INSERT INTO `fact_co2_emissions` (`co2_id`, `country_id`, `calendar_year`, `co2_emissions_t`, `created_at`, `updated_at`) VALUES
(1, 175, 2000, 103939720.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(2, 175, 2001, 105400680.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(3, 175, 2002, 110566250.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(4, 175, 2003, 113141820.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(5, 175, 2004, 124636830.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(6, 175, 2005, 129947430.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(7, 175, 2006, 137911580.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(8, 175, 2007, 148349010.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(9, 175, 2008, 147901400.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(10, 175, 2009, 148354980.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(11, 175, 2010, 147503980.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(12, 175, 2011, 149488300.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(13, 175, 2012, 150555070.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(14, 175, 2013, 148183040.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(15, 175, 2014, 150809500.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(16, 175, 2015, 144895550.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(17, 175, 2016, 176740980.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(18, 175, 2017, 211980740.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(19, 175, 2018, 203499680.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(20, 175, 2019, 190825870.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(21, 175, 2020, 215509550.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(22, 175, 2021, 243552350.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(23, 175, 2022, 211969710.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(24, 175, 2023, 186860880.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35'),
(25, 175, 2024, 179800380.00, '2026-09-30 03:58:35', '2026-09-30 03:58:35');

-- --------------------------------------------------------

--
-- Table structure for table `fact_consm_conn`
--

CREATE TABLE `fact_consm_conn` (
  `connection_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `utility_id` tinyint(3) UNSIGNED NOT NULL,
  `province_id` tinyint(3) UNSIGNED NOT NULL,
  `sector_id` tinyint(3) UNSIGNED NOT NULL,
  `consumers_added` int(11) DEFAULT NULL COMMENT 'Negative = disconnections',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_consm_conn`
--

INSERT INTO `fact_consm_conn` (`connection_id`, `year_id`, `utility_id`, `province_id`, `sector_id`, `consumers_added`, `created_at`, `updated_at`) VALUES
(1, 20, 1, 1, 1, 363445, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 20, 1, 1, 2, 2209, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 20, 1, 1, 3, 108, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 20, 1, 3, 1, 64323, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 20, 1, 3, 2, 314, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 20, 1, 3, 3, 12, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 20, 2, 8, 1, 34100, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 20, 2, 8, 2, 126, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 20, 2, 8, 3, -1, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 20, 2, 7, 1, 60403, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 20, 2, 7, 2, 1710, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 20, 2, 7, 3, 63, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 20, 2, 4, 1, 9586, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 20, 2, 4, 2, 66, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 20, 2, 4, 3, 1, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 17, 1, 1, 1, 255736, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 17, 1, 1, 2, 188, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(18, 17, 1, 1, 3, 1, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(19, 17, 1, 3, 1, 35620, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(20, 17, 1, 3, 2, 84, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(21, 17, 1, 3, 3, 0, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(22, 17, 2, 8, 1, 30213, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(23, 17, 2, 8, 2, -134, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(24, 17, 2, 8, 3, 4, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(25, 17, 2, 7, 1, 28026, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(26, 17, 2, 7, 2, -302, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(27, 17, 2, 7, 3, 17, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(28, 17, 2, 4, 1, 4939, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(29, 17, 2, 4, 2, 109, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(30, 17, 2, 4, 3, 0, '2026-09-29 06:36:33', '2026-09-29 06:36:33');

-- --------------------------------------------------------

--
-- Table structure for table `fact_derived_ef`
--

CREATE TABLE `fact_derived_ef` (
  `ef_id` int(10) UNSIGNED NOT NULL,
  `country_name` varchar(60) NOT NULL,
  `year_from` smallint(5) UNSIGNED DEFAULT NULL,
  `year_to` smallint(5) UNSIGNED DEFAULT NULL,
  `avg_ef_tco2_mwh` decimal(6,4) DEFAULT NULL,
  `method` varchar(160) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_derived_ef`
--

INSERT INTO `fact_derived_ef` (`ef_id`, `country_name`, `year_from`, `year_to`, `avg_ef_tco2_mwh`, `method`, `created_at`) VALUES
(1, 'Pakistan', 2020, 2024, 1.4757, 'Derived: OWID CO2 / total generation', '2026-09-30 03:58:35');

-- --------------------------------------------------------

--
-- Table structure for table `fact_economic_indicators`
--

CREATE TABLE `fact_economic_indicators` (
  `economic_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `calendar_year` int(11) NOT NULL,
  `gdp_current_usd` decimal(20,2) NOT NULL,
  `gdp_growth_pct` decimal(10,4) DEFAULT NULL,
  `population` bigint(20) DEFAULT NULL,
  `co2_emissions_tonnes` decimal(20,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_economic_indicators`
--

INSERT INTO `fact_economic_indicators` (`economic_id`, `year_id`, `calendar_year`, `gdp_current_usd`, `gdp_growth_pct`, `population`, `co2_emissions_tonnes`, `created_at`, `updated_at`) VALUES
(1, 2, 2000, 99484802344.53, 4.2601, 154879127, 103939720.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 3, 2001, 97145618479.90, 3.6514, 159270907, 105400680.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 4, 2002, 97923302809.35, 2.5948, 163222549, 110566250.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 5, 2003, 112371913740.82, 5.4013, 167753796, 113141820.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 6, 2004, 132216048339.41, 7.8313, 172924242, 124636830.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 7, 2005, 145208562960.77, 7.5195, 178069030, 129947430.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 8, 2006, 161871385506.36, 5.5578, 183038779, 137911580.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 9, 2007, 184140869997.46, 4.1697, 187851928, 148349010.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 10, 2008, 202203748583.85, 1.7014, 192544690, 147901400.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 11, 2009, 187337783856.47, 2.8260, 197010185, 148354980.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 12, 2010, 196709621849.59, 1.6066, 200929007, 147503980.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 13, 2011, 230586581059.67, 2.4992, 204732665, 149488300.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 14, 2012, 250106966104.70, 4.3967, 208206075, 150555070.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 15, 2013, 258657231672.41, 4.4004, 211776703, 148183040.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 16, 2014, 271390474857.63, 4.6747, 215198702, 150809500.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 17, 2015, 299963590534.77, 4.7311, 218592020, 144895550.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 18, 2016, 313630000130.44, 5.5476, 221912855, 176740980.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(18, 19, 2017, 339205534861.10, 6.5193, 224676833, 211980740.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(19, 20, 2018, 356128166704.92, 6.1572, 228547683, 203499680.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(20, 21, 2019, 320909472770.67, 2.4989, 231993486, 190825870.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(21, 22, 2020, 300425609817.98, -1.2741, 235001746, 215509550.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(22, 23, 2021, 348516647445.15, 6.5139, 240485658, 243552350.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(23, 24, 2022, 374890295666.69, 4.7781, 243700667, 211969710.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(24, 25, 2023, 336686348609.27, -0.4149, 247504495, 186860880.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(25, 26, 2024, 371747087751.31, 3.0818, 251269164, 179800380.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33');

-- --------------------------------------------------------

--
-- Table structure for table `fact_elec_generation`
--

CREATE TABLE `fact_elec_generation` (
  `generation_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `installed_capacity_mw` decimal(10,2) DEFAULT NULL,
  `generation_gwh` decimal(12,2) DEFAULT NULL,
  `imports_gwh` decimal(12,2) DEFAULT NULL,
  `consumption_gwh` decimal(12,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_elec_generation`
--

INSERT INTO `fact_elec_generation` (`generation_id`, `year_id`, `installed_capacity_mw`, `generation_gwh`, `imports_gwh`, `consumption_gwh`, `created_at`, `updated_at`) VALUES
(1, 4, 17787.00, 75682.00, NULL, 51655.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 5, 18252.00, 80827.00, 73.00, 57491.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 6, 19379.00, 85629.00, 109.00, 61328.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 7, 19450.00, 93774.00, 146.00, 67603.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 8, 19420.00, 98384.00, 171.00, 72712.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 9, 19420.00, 95860.00, 199.00, 73400.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 10, 19786.00, 91843.00, 227.00, 70371.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 11, 20922.00, 95608.00, 249.00, 74348.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 12, 22477.00, 94285.00, 269.00, 77099.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 13, 22797.00, 95091.00, 274.00, 76761.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 14, 22812.00, 96122.00, 375.00, 76789.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 15, 23531.00, 103670.00, 419.00, 83409.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 16, 23579.00, 106966.00, 443.00, 85818.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 17, 25889.00, 111300.00, 463.00, 90431.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 18, 29944.00, 123118.00, 496.00, 95530.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 19, 33554.00, 131275.00, 556.00, 106227.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 20, 35114.00, 128532.00, 487.00, 109461.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(35, 21, 39145.00, 134241.49, 513.74, 112493.86, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(36, 22, 38719.00, 143588.08, 498.37, 121559.44, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(37, 23, 39772.00, 154056.18, 514.36, 133665.45, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(38, 24, 43835.00, 138539.00, 478.62, 121863.30, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(39, 25, 45940.00, 137196.07, 377.58, 118245.92, '2026-09-29 06:58:14', '2026-09-29 06:58:14');

-- --------------------------------------------------------

--
-- Table structure for table `fact_elec_province_consumption`
--

CREATE TABLE `fact_elec_province_consumption` (
  `prov_cons_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `province_id` tinyint(3) UNSIGNED NOT NULL,
  `consumption_gwh` decimal(12,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_elec_province_consumption`
--

INSERT INTO `fact_elec_province_consumption` (`prov_cons_id`, `year_id`, `province_id`, `consumption_gwh`, `created_at`, `updated_at`) VALUES
(1, 4, 1, 32328.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 4, 2, 10704.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 4, 3, 6758.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 4, 4, 2864.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 4, 5, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 5, 1, 35374.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 5, 2, 11624.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 5, 3, 7230.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 5, 4, 3263.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 5, 5, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 6, 1, 37696.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 6, 2, 12496.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 6, 3, 7644.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 6, 4, 3492.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 6, 5, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 7, 1, 42018.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 7, 2, 13500.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(18, 7, 3, 8255.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(19, 7, 4, 3829.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(20, 7, 5, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(21, 8, 1, 45294.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(22, 8, 2, 14201.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(23, 8, 3, 8459.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(24, 8, 4, 3965.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(25, 8, 5, 792.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(26, 9, 1, 45040.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(27, 9, 2, 14726.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(28, 9, 3, 8223.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(29, 9, 4, 4089.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(30, 9, 5, 1322.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(31, 10, 1, 43465.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(32, 10, 2, 14518.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(33, 10, 3, 7560.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(34, 10, 4, 4110.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(35, 10, 5, 719.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(36, 11, 1, 45906.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(37, 11, 2, 15293.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(38, 11, 3, 8259.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(39, 11, 4, 4099.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(40, 11, 5, 790.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(41, 12, 1, 47638.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(42, 12, 2, 15876.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(43, 12, 3, 8712.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(44, 12, 4, 4048.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(45, 12, 5, 825.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(46, 13, 1, 46981.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(47, 13, 2, 16325.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(48, 13, 3, 8528.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(49, 13, 4, 4086.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(50, 13, 5, 841.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(51, 14, 1, 46467.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(52, 14, 2, 17193.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(53, 14, 3, 8455.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(54, 14, 4, 3812.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(55, 14, 5, 862.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(56, 15, 1, 52008.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(57, 15, 2, 17839.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(58, 15, 3, 8837.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(59, 15, 4, 3744.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(60, 15, 5, 901.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(61, 16, 1, 53249.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(62, 16, 2, 18997.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(63, 16, 3, 8700.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(64, 16, 4, 3994.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(65, 16, 5, 878.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(66, 17, 1, 57245.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(67, 17, 2, 19213.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(68, 17, 3, 8812.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(69, 17, 4, 4220.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(70, 17, 5, 941.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(71, 18, 1, 60940.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(72, 18, 2, 19479.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(73, 18, 3, 9660.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(74, 18, 4, 4452.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(75, 18, 5, 999.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(76, 19, 1, 69718.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(77, 19, 2, 20850.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(78, 19, 3, 10278.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(79, 19, 4, 4915.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(80, 19, 5, 1166.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(81, 20, 1, 71735.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(82, 20, 2, 21016.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(83, 20, 3, 10677.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(84, 20, 4, 4778.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(85, 20, 5, 1255.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(171, 21, 1, 80000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(172, 21, 2, 26500.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(173, 21, 3, 13600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(174, 21, 4, 6600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(175, 21, 5, 2800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(176, 22, 1, 82000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(177, 22, 2, 27200.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(178, 22, 3, 14000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(179, 22, 4, 6800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(180, 22, 5, 2900.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(181, 23, 1, 84000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(182, 23, 2, 28000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(183, 23, 3, 14400.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(184, 23, 4, 7000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(185, 23, 5, 3000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(186, 24, 1, 86000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(187, 24, 2, 28800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(188, 24, 3, 14800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(189, 24, 4, 7200.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(190, 24, 5, 3100.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(191, 25, 1, 88000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(192, 25, 2, 29600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(193, 25, 3, 15200.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(194, 25, 4, 7400.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(195, 25, 5, 3200.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(196, 26, 1, 90000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(197, 26, 2, 30400.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(198, 26, 3, 15600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(199, 26, 4, 7600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(200, 26, 5, 3300.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15');

-- --------------------------------------------------------

--
-- Table structure for table `fact_elec_sector_consumption`
--

CREATE TABLE `fact_elec_sector_consumption` (
  `elec_sector_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `sector_id` tinyint(3) UNSIGNED NOT NULL,
  `consumption_gwh` decimal(12,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_elec_sector_consumption`
--

INSERT INTO `fact_elec_sector_consumption` (`elec_sector_id`, `year_id`, `sector_id`, `consumption_gwh`, `created_at`, `updated_at`) VALUES
(1, 4, 1, 23624.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 4, 2, 3218.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 4, 3, 16181.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 4, 4, 6016.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 4, 5, 244.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 4, 6, 10.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 4, 7, 3318.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 4, 8, 45.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 5, 1, 25846.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 5, 2, 3689.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 5, 3, 17366.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 5, 4, 6669.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 5, 5, 262.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 5, 6, 9.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 5, 7, 3603.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 5, 8, 46.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 6, 1, 27601.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(18, 6, 2, 4080.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(19, 6, 3, 18591.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(20, 6, 4, 6988.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(21, 6, 5, 305.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(22, 6, 6, 12.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(23, 6, 7, 3700.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(24, 6, 8, 50.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(25, 7, 1, 30720.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(26, 7, 2, 4730.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(27, 7, 3, 19803.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(28, 7, 4, 7949.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(29, 7, 5, 353.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(30, 7, 6, 13.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(31, 7, 7, 3985.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(32, 7, 8, 51.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(33, 8, 1, 33335.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(34, 8, 2, 5363.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(35, 8, 3, 21066.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(36, 8, 4, 8176.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(37, 8, 5, 387.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(38, 8, 6, 12.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(39, 8, 7, 4246.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(40, 8, 8, 127.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(41, 9, 1, 33704.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(42, 9, 2, 5572.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(43, 9, 3, 20729.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(44, 9, 4, 8472.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(45, 9, 5, 415.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(46, 9, 6, 8.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(47, 9, 7, 4342.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(48, 9, 8, 158.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(49, 10, 1, 32282.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(50, 10, 2, 5252.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(51, 10, 3, 19330.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(52, 10, 4, 8795.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(53, 10, 5, 430.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(54, 10, 6, 5.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(55, 10, 7, 4177.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(56, 10, 8, 101.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(57, 11, 1, 34272.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(58, 11, 2, 5605.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(59, 11, 3, 19823.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(60, 11, 4, 9689.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(61, 11, 5, 458.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(62, 11, 6, 2.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(63, 11, 7, 4417.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(64, 11, 8, 81.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(65, 12, 1, 35885.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(66, 12, 2, 5782.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(67, 12, 3, 21207.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(68, 12, 4, 8971.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(69, 12, 5, 456.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(70, 12, 6, 1.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(71, 12, 7, 4715.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(72, 12, 8, 82.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(73, 13, 1, 35589.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(74, 13, 2, 5754.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(75, 13, 3, 21801.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(76, 13, 4, 8548.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(77, 13, 5, 478.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(78, 13, 6, 1.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(79, 13, 7, 4502.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(80, 13, 8, 88.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(81, 14, 1, 36116.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(82, 14, 2, 6007.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(83, 14, 3, 22313.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(84, 14, 4, 7697.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(85, 14, 5, 457.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(86, 14, 6, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(87, 14, 7, 4137.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(88, 14, 8, 61.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(89, 15, 1, 39549.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(90, 15, 2, 6375.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(91, 15, 3, 24356.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(92, 15, 4, 8290.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(93, 15, 5, 458.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(94, 15, 6, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(95, 15, 7, 4313.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(96, 15, 8, 68.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(97, 16, 1, 41450.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(98, 16, 2, 6512.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(99, 16, 3, 24979.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(100, 16, 4, 8033.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(101, 16, 5, 441.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(102, 16, 6, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(103, 16, 7, 4334.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(104, 16, 8, 69.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(105, 17, 1, 44486.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(106, 17, 2, 7181.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(107, 17, 3, 25035.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(108, 17, 4, 8526.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(109, 17, 5, 459.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(110, 17, 6, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(111, 17, 7, 4666.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(112, 17, 8, 76.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(113, 18, 1, 48698.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(114, 18, 2, 7856.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(115, 18, 3, 24010.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(116, 18, 4, 9221.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(117, 18, 5, 484.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(118, 18, 6, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(119, 18, 7, 5018.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(120, 18, 8, 242.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(121, 19, 1, 54028.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(122, 19, 2, 8606.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(123, 19, 3, 27468.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(124, 19, 4, 10128.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(125, 19, 5, 475.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(126, 19, 6, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(127, 19, 7, 5515.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(128, 19, 8, 708.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(129, 20, 1, 53685.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(130, 20, 2, 8513.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(131, 20, 3, 28760.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(132, 20, 4, 9809.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(133, 20, 5, 451.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(134, 20, 6, 0.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(135, 20, 7, 5622.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(136, 20, 8, 2618.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(273, 21, 1, 64000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(274, 21, 2, 9800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(275, 21, 3, 31500.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(276, 21, 4, 11800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(277, 21, 5, 670.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(278, 21, 6, 13.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(279, 21, 7, 6800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(280, 21, 8, 275.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(281, 22, 1, 66000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(282, 22, 2, 10200.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(283, 22, 3, 32500.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(284, 22, 4, 12200.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(285, 22, 5, 690.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(286, 22, 6, 14.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(287, 22, 7, 7000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(288, 22, 8, 285.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(289, 23, 1, 68000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(290, 23, 2, 10600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(291, 23, 3, 33500.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(292, 23, 4, 12600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(293, 23, 5, 710.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(294, 23, 6, 15.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(295, 23, 7, 7200.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(296, 23, 8, 295.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(297, 24, 1, 70000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(298, 24, 2, 11000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(299, 24, 3, 34500.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(300, 24, 4, 13000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(301, 24, 5, 730.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(302, 24, 6, 16.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(303, 24, 7, 7400.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(304, 24, 8, 305.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(305, 25, 1, 72000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(306, 25, 2, 11400.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(307, 25, 3, 35500.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(308, 25, 4, 13400.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(309, 25, 5, 750.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(310, 25, 6, 17.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(311, 25, 7, 7600.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(312, 25, 8, 315.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(313, 26, 1, 74000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(314, 26, 2, 11800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(315, 26, 3, 36500.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(316, 26, 4, 13800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(317, 26, 5, 770.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(318, 26, 6, 18.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(319, 26, 7, 7800.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15'),
(320, 26, 8, 325.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15');

-- --------------------------------------------------------

--
-- Table structure for table `fact_energy_overview`
--

CREATE TABLE `fact_energy_overview` (
  `overview_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `total_primary_supply_toe` decimal(18,3) DEFAULT NULL,
  `total_final_consumption_toe` decimal(18,3) DEFAULT NULL,
  `supply_consumption_gap_toe` decimal(18,3) DEFAULT NULL,
  `transformation_losses_toe` decimal(18,3) DEFAULT NULL,
  `td_losses_toe` decimal(18,3) DEFAULT NULL,
  `total_losses_toe` decimal(18,3) DEFAULT NULL,
  `energy_used_in_transformation` decimal(12,3) DEFAULT NULL,
  `energy_sector_own_use` decimal(12,3) DEFAULT NULL,
  `savings_toe` decimal(18,3) DEFAULT NULL,
  `savings_pct` decimal(8,4) DEFAULT NULL,
  `sustainability_class` enum('Futuristic','Sustainable','Unsustainable','Critical') DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_energy_overview`
--

INSERT INTO `fact_energy_overview` (`overview_id`, `year_id`, `total_primary_supply_toe`, `total_final_consumption_toe`, `supply_consumption_gap_toe`, `transformation_losses_toe`, `td_losses_toe`, `total_losses_toe`, `energy_used_in_transformation`, `energy_sector_own_use`, `savings_toe`, `savings_pct`, `sustainability_class`, `created_at`, `updated_at`) VALUES
(1, 7, 58059000.000, 33940000.000, 24119000.000, 16427000.000, 2067000.000, 18494000.000, 19200.000, 707.000, 5625000.000, 9.6884, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(2, 8, 60620000.000, 36000000.000, 24620000.000, 16960000.000, 2214000.000, 19174000.000, 19873.000, 699.000, 5446000.000, 8.9838, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(3, 9, 62910000.000, 39410000.000, 23500000.000, 16960000.000, 2214000.000, 19174000.000, 19873.000, 699.000, 4326000.000, 6.8765, 'Unsustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(4, 10, 62560000.000, 37340000.000, 25220000.000, 16539000.000, 2267000.000, 18806000.000, 19602.000, 795.000, 6414000.000, 10.2526, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(5, 11, 63080000.000, 38760000.000, 24320000.000, 18397000.000, 1772000.000, 20169000.000, 20820.000, 652.000, 4151000.000, 6.5805, 'Unsustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(6, 12, 64520000.000, 38840000.000, 25680000.000, 17114000.000, 2468000.000, 19582000.000, 20188.000, 606.000, 6098000.000, 9.4513, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(7, 13, 64650000.000, 40020000.000, 24630000.000, 18322000.000, 2838000.000, 21160000.000, 21717.000, 557.000, 3470000.000, 5.3674, 'Unsustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(8, 14, 64580000.000, 40180000.000, 24400000.000, 18495000.000, 1999000.000, 20494000.000, 21050.000, 557.000, 3906000.000, 6.0483, 'Unsustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(9, 15, 66840000.000, 39810000.000, 27030000.000, 18138000.000, 2365000.000, 20503000.000, 21179.000, 677.000, 6527000.000, 9.7651, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(10, 16, 70260000.000, 41980000.000, 28280000.000, 19613000.000, 3294000.000, 22907000.000, 23589.000, 682.000, 5373000.000, 7.6473, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(11, 17, 73960000.000, 45380000.000, 28580000.000, 20374000.000, 3519000.000, 23893000.000, 245454.000, 651.000, 4687000.000, 6.3372, 'Unsustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(12, 18, 79580000.000, 50120000.000, 29460000.000, 22036000.000, 1838000.000, 23874000.000, 24580.000, 706.000, 5586000.000, 7.0194, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(13, 19, 79580000.000, 50120000.000, 29460000.000, 22036000.000, 1838000.000, 23874000.000, 24580.000, 706.000, 5586000.000, 7.0194, 'Sustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(14, 20, 86300000.000, 54990000.000, 31310000.000, 27819000.000, 1433000.000, 26386000.000, 27202.000, 816.000, 4924000.000, 5.7057, 'Unsustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41'),
(15, 21, 83810000.000, 54990000.000, 28820000.000, 18529000.000, 5128000.000, 23657000.000, 24628.000, 972.000, 5163000.000, 6.1604, 'Unsustainable', '2026-09-29 06:36:33', '2026-09-30 17:08:41');

-- --------------------------------------------------------

--
-- Table structure for table `fact_final_energy_consumption`
--

CREATE TABLE `fact_final_energy_consumption` (
  `consumption_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `source_id` tinyint(3) UNSIGNED NOT NULL,
  `consumption_toe` bigint(20) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_final_energy_consumption`
--

INSERT INTO `fact_final_energy_consumption` (`consumption_id`, `year_id`, `source_id`, `consumption_toe`, `created_at`, `updated_at`) VALUES
(1, 4, 1, 10865717, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 4, 2, 9109870, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 4, 4, 352766, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 4, 5, 1691274, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 4, 10, 4288227, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 5, 1, 11145365, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 5, 2, 10067245, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 5, 4, 380370, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 5, 5, 2703906, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 5, 10, 4682063, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 6, 1, 11710920, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 6, 2, 11637566, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 6, 4, 450379, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 6, 5, 3310512, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 6, 10, 4994560, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 7, 1, 10877601, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 7, 2, 13325251, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(18, 7, 4, 625792, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(19, 7, 5, 3611490, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(20, 7, 10, 5505555, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(21, 8, 1, 10575330, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(22, 8, 2, 14701024, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(23, 8, 4, 658225, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(24, 8, 5, 4149041, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(25, 8, 10, 5921635, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(26, 9, 1, 11528722, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(27, 9, 2, 15881990, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(28, 9, 4, 619944, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(29, 9, 5, 5404715, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(30, 9, 10, 5977697, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(31, 10, 1, 10842614, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(32, 10, 2, 16307898, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(33, 10, 4, 569995, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(34, 10, 5, 3893001, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(35, 10, 10, 5731032, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(36, 11, 1, 10829455, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(37, 11, 2, 17024933, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(38, 11, 4, 576631, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(39, 11, 5, 4282061, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(40, 11, 10, 6054921, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(41, 12, 1, 11252938, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(42, 12, 2, 16781247, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(43, 12, 4, 503272, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(44, 12, 5, 4025380, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(45, 12, 10, 6278947, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(46, 13, 1, 11617788, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(47, 13, 2, 17618199, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(48, 13, 4, 481064, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(49, 13, 5, 4057678, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(50, 13, 10, 6251421, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(51, 14, 1, 12219941, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(52, 14, 2, 17521615, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(53, 14, 4, 528417, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(54, 14, 5, 3661193, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(55, 14, 10, 6253675, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(56, 15, 1, 12718011, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(57, 15, 2, 16277023, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(58, 15, 4, 585560, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(59, 15, 5, 3446131, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(60, 15, 10, 6792794, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(61, 16, 1, 13851467, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(62, 16, 2, 15755616, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(63, 16, 4, 756414, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(64, 16, 5, 4631627, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(65, 16, 10, 6989011, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(66, 17, 1, 16290075, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(67, 17, 2, 15544358, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(68, 17, 4, 1210419, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(69, 17, 5, 4975472, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(70, 17, 10, 7364702, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(71, 18, 1, 17904977, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(72, 18, 2, 17031100, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(73, 18, 4, 1308471, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(74, 18, 5, 6097816, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(75, 18, 10, 7779939, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(76, 19, 1, 19264954, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(77, 19, 2, 16693880, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(78, 19, 4, 1385427, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(79, 19, 5, 8940477, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(80, 19, 10, 8708151, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(81, 20, 1, 17364897, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(82, 20, 2, 17275180, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(83, 20, 4, 1148380, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(84, 20, 5, 10292739, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(85, 20, 10, 8914489, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(171, 21, 1, 21981213, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(172, 21, 2, 38239874, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(173, 21, 5, 12267027, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(174, 21, 10, 11649183, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(175, 22, 1, 21498848, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(176, 22, 2, 35393245, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(177, 22, 5, 13573950, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(178, 22, 10, 12610490, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(179, 23, 1, 24868656, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(180, 23, 2, 38599365, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(181, 23, 5, 15209994, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(182, 23, 10, 14076527, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(183, 24, 1, 24243188, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(184, 24, 2, 32813014, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(185, 24, 5, 12981318, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(186, 24, 10, 15170249, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(187, 25, 1, 19246954, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(188, 25, 2, 32513289, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(189, 25, 5, 11139335, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(190, 25, 10, 14828031, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(191, 26, 1, 19751315, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(192, 26, 2, 31858940, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(193, 26, 5, 9865813, '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(194, 26, 10, 15085125, '2026-09-29 06:58:14', '2026-09-29 06:58:14');

-- --------------------------------------------------------

--
-- Table structure for table `fact_gas_province_consumption`
--

CREATE TABLE `fact_gas_province_consumption` (
  `gas_prov_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `province_id` tinyint(3) UNSIGNED NOT NULL,
  `consumption_bcf` decimal(10,3) DEFAULT NULL,
  `share_pct` decimal(8,4) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_gas_province_consumption`
--

INSERT INTO `fact_gas_province_consumption` (`gas_prov_id`, `year_id`, `province_id`, `consumption_bcf`, `share_pct`, `created_at`, `updated_at`) VALUES
(1, 20, 1, 720.386, 49.5616, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 20, 3, 78.777, 5.4198, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 20, 2, 518.647, 35.6822, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 20, 4, 135.707, 9.3365, '2026-09-29 06:36:33', '2026-09-29 06:36:33');

-- --------------------------------------------------------

--
-- Table structure for table `fact_gas_reserves`
--

CREATE TABLE `fact_gas_reserves` (
  `reserve_id` tinyint(3) UNSIGNED NOT NULL,
  `reference_year` smallint(5) UNSIGNED NOT NULL,
  `proved_reserves_bcf` decimal(12,3) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_gas_reserves`
--

INSERT INTO `fact_gas_reserves` (`reserve_id`, `reference_year`, `proved_reserves_bcf`, `created_at`, `updated_at`) VALUES
(1, 1998, 14.126, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(2, 2008, 21.189, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(3, 2017, 14.126, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(4, 2018, 14.126, '2026-09-29 06:36:33', '2026-09-30 17:08:42');

-- --------------------------------------------------------

--
-- Table structure for table `fact_gas_sector_consumption`
--

CREATE TABLE `fact_gas_sector_consumption` (
  `gas_sector_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `sector_id` tinyint(3) UNSIGNED NOT NULL,
  `consumption_bcf` decimal(12,3) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_gas_sector_consumption`
--

INSERT INTO `fact_gas_sector_consumption` (`gas_sector_id`, `year_id`, `sector_id`, `consumption_bcf`, `created_at`, `updated_at`) VALUES
(1, 15, 1, 269.135, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(2, 15, 2, 38.117, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(3, 15, 9, 250.490, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(4, 15, 10, 349.535, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(5, 15, 11, 164.378, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(6, 15, 12, 87.634, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(7, 15, 13, 52.139, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(8, 15, 14, 0.522, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(9, 15, 15, 0.000, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(10, 16, 1, 278.069, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(11, 16, 2, 35.187, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(12, 16, 9, 239.591, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(13, 16, 10, 371.562, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(14, 16, 11, 166.903, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(15, 16, 12, 66.517, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(16, 16, 13, 58.609, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(17, 16, 14, 0.831, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(18, 16, 15, 0.000, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(19, 17, 1, 271.302, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(20, 17, 2, 33.633, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(21, 17, 9, 230.436, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(22, 17, 10, 440.593, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(23, 17, 11, 182.076, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(24, 17, 12, 64.455, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(25, 17, 13, 80.847, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(26, 17, 14, 0.497, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(27, 17, 15, 0.000, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(28, 18, 1, 290.868, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(29, 18, 2, 32.858, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(30, 18, 9, 261.267, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(31, 18, 10, 446.941, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(32, 18, 11, 182.241, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(33, 18, 12, 67.245, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(34, 18, 13, 94.564, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(35, 18, 14, 0.583, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(36, 18, 15, 0.000, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(37, 19, 1, 284.428, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(38, 19, 2, 32.096, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(39, 19, 9, 273.339, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(40, 19, 10, 544.654, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(41, 19, 11, 181.662, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(42, 19, 12, 70.455, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(43, 19, 13, 66.442, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(44, 19, 14, 0.886, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(45, 19, 15, 0.000, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(46, 20, 1, 311.887, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(47, 20, 2, 31.205, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(48, 20, 9, 245.958, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(49, 20, 10, 511.140, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(50, 20, 11, 196.576, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(51, 20, 12, 65.099, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(52, 20, 13, 37.258, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(53, 20, 14, 0.387, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(54, 20, 15, 53.261, '2026-09-29 06:36:33', '2026-09-30 17:08:42');

-- --------------------------------------------------------

--
-- Table structure for table `fact_lng_imports`
--

CREATE TABLE `fact_lng_imports` (
  `lng_import_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `imports_bcf` decimal(12,3) DEFAULT NULL,
  `imports_value_musd` decimal(10,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_lng_imports`
--

INSERT INTO `fact_lng_imports` (`lng_import_id`, `year_id`, `imports_bcf`, `imports_value_musd`, `created_at`, `updated_at`) VALUES
(1, 16, 0.002, 151.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(2, 17, 0.101, 642.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(3, 18, 0.187, 1278.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(4, 19, 0.314, 2452.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(5, 20, 3.734, 3392.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42');

-- --------------------------------------------------------

--
-- Table structure for table `fact_natural_gas`
--

CREATE TABLE `fact_natural_gas` (
  `gas_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `production_bcf` decimal(10,3) DEFAULT NULL,
  `consumption_bcf` decimal(10,3) DEFAULT NULL,
  `gap_bcf` decimal(10,3) DEFAULT NULL,
  `gap_with_lng_bcf` decimal(10,3) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_natural_gas`
--

INSERT INTO `fact_natural_gas` (`gas_id`, `year_id`, `production_bcf`, `consumption_bcf`, `gap_bcf`, `gap_with_lng_bcf`, `created_at`, `updated_at`) VALUES
(1, 1, 818.342, 712.100, 106.242, 106.242, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 2, 875.433, 768.068, 107.365, 107.365, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 3, 923.758, 824.604, 99.154, 99.154, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 4, 992.589, 872.265, 120.324, 120.324, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 5, 1202.750, 1051.418, 151.332, 151.332, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 6, 1344.964, 1157.628, 187.336, 187.336, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 7, 1400.026, 1221.762, 178.264, 178.264, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 8, 1413.581, 1220.929, 192.652, 192.652, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 9, 1454.194, 1275.212, 178.982, 178.982, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 10, 1460.679, 1269.433, 191.246, 191.246, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 11, 1482.847, 1277.821, 205.026, 205.026, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 12, 1471.591, 1240.671, 230.920, 230.920, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 13, 1558.959, 1288.198, 270.761, 270.761, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 14, 1505.841, 1267.980, 237.861, 237.861, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 15, 1493.508, 1220.493, 273.015, 273.015, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 16, 1465.760, 1224.893, 240.867, 240.869, '2026-09-29 06:36:33', '2026-09-29 06:39:32'),
(17, 17, 1481.551, 1304.919, 176.632, 176.733, '2026-09-29 06:36:33', '2026-09-29 06:39:32'),
(18, 18, 1471.855, 1377.307, 94.548, 94.735, '2026-09-29 06:36:33', '2026-09-29 06:39:32'),
(19, 19, 1458.936, 1454.697, 4.239, 4.553, '2026-09-29 06:36:33', '2026-09-29 06:39:32'),
(20, 20, 1436.546, 1453.517, -16.971, -13.237, '2026-09-29 06:36:33', '2026-09-29 06:39:32');

-- --------------------------------------------------------

--
-- Table structure for table `fact_primary_energy_supply`
--

CREATE TABLE `fact_primary_energy_supply` (
  `supply_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `source_id` tinyint(3) UNSIGNED NOT NULL,
  `supply_toe` bigint(20) DEFAULT NULL,
  `imports_toe` bigint(20) DEFAULT NULL,
  `imports_pct` decimal(8,4) DEFAULT NULL,
  `unit` varchar(10) DEFAULT 'TOE',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_primary_energy_supply`
--

INSERT INTO `fact_primary_energy_supply` (`supply_id`, `year_id`, `source_id`, `supply_toe`, `imports_toe`, `imports_pct`, `unit`, `created_at`, `updated_at`) VALUES
(1, 4, 1, 18016214, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 4, 2, 20590425, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 4, 3, 0, 0, 0.0002, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 4, 4, 181661, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 4, 5, 2519881, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 4, 6, 5335041, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 4, 7, 415242, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 4, 8, 85, 85, 0.0002, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 5, 1, 15221024, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 5, 2, 25254481, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 5, 3, 0, 0, 0.0343, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 5, 4, 205526, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 5, 5, 3300491, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 5, 6, 6431312, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 5, 7, 420135, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 5, 8, 17418, 17418, 0.0343, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 6, 1, 16329979, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(18, 6, 2, 27953380, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(19, 6, 3, 0, 0, 0.0469, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(20, 6, 4, 251789, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(21, 6, 5, 4227842, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(22, 6, 6, 6127429, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(23, 6, 7, 667234, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(24, 6, 8, 26050, 26050, 0.0469, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(25, 7, 1, 16411834, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(26, 7, 2, 29202362, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(27, 7, 3, 0, 0, 0.0599, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(28, 7, 4, 400430, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(29, 7, 5, 4049654, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(30, 7, 6, 7366452, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(31, 7, 7, 592887, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(32, 7, 8, 34775, 34775, 0.0599, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(33, 8, 1, 18188280, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(34, 8, 2, 29322338, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(35, 8, 3, 0, 0, 0.0673, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(36, 8, 4, 470998, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(37, 8, 5, 4426678, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(38, 8, 6, 7626755, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(39, 8, 7, 546159, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(40, 8, 8, 40781, 40781, 0.0673, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(41, 9, 1, 19206441, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(42, 9, 2, 29872105, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(43, 9, 3, 0, 0, 0.0756, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(44, 9, 4, 418952, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(45, 9, 5, 5783844, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(46, 9, 6, 6851955, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(47, 9, 7, 734537, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(48, 9, 8, 47550, 47550, 0.0756, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(49, 10, 1, 20103060, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(50, 10, 2, 30255885, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(51, 10, 3, 0, 0, 0.0867, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(52, 10, 4, 401705, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(53, 10, 5, 4732823, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(54, 10, 6, 6631841, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(55, 10, 7, 386165, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(56, 10, 8, 54266, 54266, 0.0867, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(57, 11, 1, 19806314, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(58, 11, 2, 30808523, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(59, 11, 3, 0, 0, 0.0944, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(60, 11, 4, 395583, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(61, 11, 5, 4621639, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(62, 11, 6, 6705533, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(63, 11, 7, 690821, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(64, 11, 8, 59537, 59537, 0.0944, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(65, 12, 1, 20674840, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(66, 12, 2, 30683357, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(67, 12, 3, 0, 0, 0.0993, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(68, 12, 4, 339633, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(69, 12, 5, 4350868, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(70, 12, 6, 7593074, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(71, 12, 7, 816370, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(72, 12, 8, 64093, 64093, 0.0993, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(73, 13, 1, 19958483, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(74, 13, 2, 32033074, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(75, 13, 3, 0, 0, 0.1012, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(76, 13, 4, 321214, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(77, 13, 5, 4285400, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(78, 13, 6, 6806704, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(79, 13, 7, 1256791, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(80, 13, 8, 65515, 65515, 0.1012, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(81, 14, 1, 20968730, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(82, 14, 2, 31144006, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(83, 14, 3, 0, 0, 0.1386, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(84, 14, 4, 309524, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(85, 14, 5, 3863081, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(86, 14, 6, 7126623, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(87, 14, 7, 1086846, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(88, 14, 8, 89542, 89542, 0.1386, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(89, 15, 1, 23006510, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(90, 15, 2, 30964868, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(91, 15, 3, 0, 0, 0.1490, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(92, 15, 4, 363710, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(93, 15, 5, 3590386, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(94, 15, 6, 7607804, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(95, 15, 7, 1215042, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(96, 15, 8, 99907, 99907, 0.1490, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(97, 15, 9, 191407, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(98, 16, 1, 24970360, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(99, 16, 2, 29977755, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(100, 16, 3, 472503, 472503, 0.8228, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(101, 16, 4, 457197, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(102, 16, 5, 4952556, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(103, 16, 6, 7751133, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(104, 16, 7, 1385283, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(105, 16, 8, 105632, 105632, 0.8228, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(106, 16, 9, 191407, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(107, 17, 1, 25280073, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(108, 17, 2, 30460521, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(109, 17, 3, 2404128, 2404128, 3.3997, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(110, 17, 4, 908705, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(111, 17, 5, 5066935, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(112, 17, 6, 8266670, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(113, 17, 7, 1099261, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(114, 17, 8, 110525, 110525, 3.3997, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(115, 17, 9, 369731, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(116, 18, 1, 27366526, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(117, 18, 2, 30163334, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(118, 18, 3, 4455734, 4455734, 5.7476, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(119, 18, 4, 1008637, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(120, 18, 5, 6482401, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(121, 18, 6, 7681699, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(122, 18, 7, 1670560, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(123, 18, 8, 118480, 118480, 5.7476, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(124, 18, 9, 636825, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(125, 19, 1, 26903431, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(126, 19, 2, 29849030, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(127, 19, 3, 7492597, 7492597, 8.8356, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(128, 19, 4, 1054006, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(129, 19, 5, 10925200, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(130, 19, 6, 6665328, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(131, 19, 7, 2358200, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(132, 19, 8, 132659, 132659, 8.8356, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(133, 19, 9, 920580, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(134, 20, 1, 21568315, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(135, 20, 2, 29318489, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(136, 20, 3, 8913006, 8913006, 10.7733, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(137, 20, 4, 953834, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(138, 20, 5, 12933087, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(139, 20, 6, 6525607, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(140, 20, 7, 2365268, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(141, 20, 8, 116196, 116196, 10.7733, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(142, 20, 9, 1117482, NULL, NULL, 'TOE', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(285, 21, 1, 21981213, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(286, 21, 2, 38239874, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(287, 21, 5, 12267027, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(288, 21, 6, 7690979, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(289, 21, 7, 1954374, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(290, 21, 9, 985155, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(291, 22, 1, 21498848, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(292, 22, 2, 35393245, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(293, 22, 5, 13573950, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(294, 22, 6, 8489589, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(295, 22, 7, 2027484, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(296, 22, 9, 901207, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(297, 23, 1, 24868656, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(298, 23, 2, 38599365, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(299, 23, 5, 15209994, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(300, 23, 6, 7969957, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(301, 23, 7, 3323884, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(302, 23, 9, 1068004, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(303, 24, 1, 24243187, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(304, 24, 2, 32813014, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(305, 24, 5, 12981318, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(306, 24, 6, 7415642, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(307, 24, 7, 4700623, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(308, 24, 9, 1418532, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(309, 25, 1, 19246954, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(310, 25, 2, 32513288, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(311, 25, 5, 11139334, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(312, 25, 6, 8064427, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(313, 25, 7, 4691948, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(314, 25, 9, 1385447, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(315, 26, 1, 19751315, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(316, 26, 2, 31858940, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(317, 26, 5, 9865813, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(318, 26, 6, 8180756, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(319, 26, 7, 4780460, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14'),
(320, 26, 9, 1290496, NULL, NULL, 'TOE', '2026-09-29 06:58:14', '2026-09-29 06:58:14');

-- --------------------------------------------------------

--
-- Table structure for table `fact_renewable_capacity`
--

CREATE TABLE `fact_renewable_capacity` (
  `renewable_capacity_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `renewable_source` varchar(50) NOT NULL,
  `installed_capacity_mw` decimal(12,2) DEFAULT NULL,
  `source_name` varchar(100) DEFAULT 'Pakistan Bureau of Statistics (PBS)',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_renewable_capacity`
--

INSERT INTO `fact_renewable_capacity` (`renewable_capacity_id`, `year_id`, `renewable_source`, `installed_capacity_mw`, `source_name`, `created_at`, `updated_at`) VALUES
(1, 8, 'Hydel', 6474.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 8, 'Wind', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 8, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 8, 'Bagasse', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 9, 'Hydel', 6555.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 9, 'Wind', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 9, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 9, 'Bagasse', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 10, 'Hydel', 6555.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 10, 'Wind', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 10, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 10, 'Bagasse', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 11, 'Hydel', 6573.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 11, 'Wind', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 11, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 11, 'Bagasse', 8.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 12, 'Hydel', 6573.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(18, 12, 'Wind', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(19, 12, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(20, 12, 'Bagasse', 8.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(21, 13, 'Hydel', 6645.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(22, 13, 'Wind', 56.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(23, 13, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(24, 13, 'Bagasse', 8.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(25, 14, 'Hydel', 6825.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(26, 14, 'Wind', 106.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(27, 14, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(28, 14, 'Bagasse', 72.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(29, 15, 'Hydel', 6985.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(30, 15, 'Wind', 106.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(31, 15, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(32, 15, 'Bagasse', 133.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(33, 16, 'Hydel', 7115.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(34, 16, 'Wind', 256.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(35, 16, 'Solar', 0.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(36, 16, 'Bagasse', 157.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(37, 17, 'Hydel', 7115.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(38, 17, 'Wind', 340.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(39, 17, 'Solar', 400.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(40, 17, 'Bagasse', 219.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(41, 18, 'Hydel', 7115.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(42, 18, 'Wind', 792.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(43, 18, 'Solar', 400.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(44, 18, 'Bagasse', 456.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(45, 19, 'Hydel', 7270.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(46, 19, 'Wind', 1042.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(47, 19, 'Solar', 436.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(48, 19, 'Bagasse', 469.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(49, 20, 'Hydel', 9757.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(50, 20, 'Wind', 1242.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(51, 20, 'Solar', 505.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(52, 20, 'Bagasse', 527.00, 'Pakistan Bureau of Statistics (PBS)', '2026-09-29 06:36:33', '2026-09-29 06:36:33');

-- --------------------------------------------------------

--
-- Table structure for table `fact_renewable_energy`
--

CREATE TABLE `fact_renewable_energy` (
  `renewable_energy_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `calendar_year` int(11) DEFAULT NULL,
  `capacity_mw` decimal(12,2) DEFAULT NULL,
  `gen_solar_gwh` decimal(15,2) DEFAULT NULL,
  `gen_wind_gwh` decimal(15,2) DEFAULT NULL,
  `gen_hydro_gwh` decimal(15,2) DEFAULT NULL,
  `gen_other_renewables_gwh` decimal(15,2) DEFAULT NULL,
  `share_solar_pct` decimal(8,2) DEFAULT NULL,
  `share_wind_pct` decimal(8,2) DEFAULT NULL,
  `share_hydro_pct` decimal(8,2) DEFAULT NULL,
  `demand_gwh` decimal(15,2) DEFAULT NULL,
  `primary_energy_gwh` decimal(15,2) DEFAULT NULL,
  `gen_coal_gwh` decimal(15,2) DEFAULT NULL,
  `gen_gas_gwh` decimal(15,2) DEFAULT NULL,
  `gen_nuclear_gwh` decimal(15,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_renewable_energy`
--

INSERT INTO `fact_renewable_energy` (`renewable_energy_id`, `year_id`, `calendar_year`, `capacity_mw`, `gen_solar_gwh`, `gen_wind_gwh`, `gen_hydro_gwh`, `gen_other_renewables_gwh`, `share_solar_pct`, `share_wind_pct`, `share_hydro_pct`, `demand_gwh`, `primary_energy_gwh`, `gen_coal_gwh`, `gen_gas_gwh`, `gen_nuclear_gwh`, `created_at`, `updated_at`) VALUES
(1, 1, 1999, NULL, 0.00, 0.00, 0.00, NULL, NULL, NULL, NULL, NULL, 473720.00, NULL, NULL, NULL, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(2, 2, 2000, 5175.89, 0.00, 0.00, 17190.00, NULL, 0.00, 0.00, 25.85, 66490.00, 483750.00, 240.00, 21780.00, 380.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(3, 3, 2001, 5313.89, 0.00, 0.00, 18940.00, NULL, 0.00, 0.00, 26.27, 72110.00, 495150.00, 280.00, 24850.00, 1980.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(4, 4, 2002, 5319.89, 0.00, 0.00, 22350.00, NULL, 0.00, 0.00, 29.50, 75770.00, 514110.00, 230.00, 27010.00, 1800.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(5, 5, 2003, 5900.89, 0.00, 0.00, 26940.00, NULL, 0.00, 0.00, 32.82, 82150.00, 554230.00, 200.00, 39210.00, 1810.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(6, 6, 2004, 6775.89, 0.00, 0.00, 25670.00, NULL, 0.00, 0.00, 29.86, 86070.00, 618900.00, 170.00, 43470.00, 1930.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(7, 7, 2005, 6777.29, 0.00, 0.00, 30860.00, NULL, 0.00, 0.00, 32.64, 94710.00, 641340.00, 130.00, 41290.00, 2410.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(8, 8, 2006, 6763.29, 0.00, 0.00, 31950.00, NULL, 0.00, 0.00, 32.10, 99700.00, 679630.00, 140.00, 35810.00, 2550.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(9, 9, 2007, 6798.03, 0.00, 0.00, 31950.00, NULL, 0.00, 0.00, 29.86, 96350.00, 717060.00, 140.00, 32920.00, 2310.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(10, 10, 2008, 6922.47, 0.00, 0.00, 27780.00, NULL, 0.00, 0.00, 29.87, 93240.00, 718680.00, 110.00, 29680.00, 1740.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(11, 11, 2009, 6932.12, 0.00, 10.00, 28090.00, NULL, 0.00, 0.01, 29.23, 96360.00, 745360.00, 120.00, 28080.00, 2640.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(12, 12, 2010, 7012.37, 10.00, 10.00, 31810.00, NULL, 0.01, 0.01, 33.65, 94810.00, 749470.00, 90.00, 25880.00, 2560.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(13, 13, 2011, 7025.21, 30.00, 20.00, 28520.00, NULL, 0.03, 0.02, 30.07, 95100.00, 753330.00, 100.00, 27650.00, 3840.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(14, 14, 2012, 7142.21, 70.00, 10.00, 29860.00, NULL, 0.07, 0.01, 30.44, 98480.00, 701790.00, 60.00, 27120.00, 5270.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(15, 15, 2013, 7564.44, 140.00, 400.00, 31870.00, NULL, 0.13, 0.38, 30.39, 105300.00, 775380.00, 160.00, 26670.00, 4400.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(16, 16, 2014, 7915.10, 240.00, 800.00, 32470.00, NULL, 0.22, 0.74, 30.09, 108350.00, 786310.00, 140.00, 28350.00, 4580.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(17, 17, 2015, 8127.70, 380.00, 790.00, 34630.00, NULL, 0.34, 0.70, 30.70, 113250.00, 829310.00, 150.00, 35000.00, 4330.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(18, 18, 2016, 8807.87, 680.00, 1330.00, 32180.00, NULL, 0.55, 1.08, 26.18, 123400.00, 900440.00, 620.00, 41430.00, 5440.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(19, 19, 2017, 9224.03, 920.00, 2100.00, 27920.00, NULL, 0.71, 1.61, 21.42, 130920.00, 951990.00, 10910.00, 49200.00, 8110.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(20, 20, 2018, 12203.88, 920.00, 3160.00, 27340.00, NULL, 0.71, 2.45, 21.19, 129510.00, 967480.00, 15770.00, 57440.00, 9290.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(21, 21, 2019, 12349.05, 2610.00, 2880.00, 33580.00, NULL, 1.93, 2.13, 24.88, 135480.00, 973640.00, 25860.00, 46020.00, 9070.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(22, 22, 2020, 12764.35, 4100.00, 2900.00, 33550.00, NULL, 2.81, 1.98, 22.95, 146660.00, 959670.00, 27550.00, 49470.00, 9640.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(23, 23, 2021, 13248.49, 5790.00, 4580.00, 33550.00, NULL, 3.55, 2.81, 20.56, 163710.00, 1066010.00, 25910.00, 48670.00, 15740.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(24, 24, 2022, 15097.66, 7720.00, 6340.00, 34580.00, NULL, 4.39, 3.60, 19.65, 176430.00, 979100.00, 27490.00, 46980.00, 22280.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(25, 25, 2023, 16133.72, 11350.00, 6050.00, 37900.00, NULL, 6.60, 3.52, 22.04, 172450.00, 904240.00, 26440.00, 45510.00, 22440.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42'),
(26, 26, 2024, 17525.32, 19830.00, 5160.00, 38270.00, NULL, 11.33, 2.95, 21.87, 175440.00, 888370.00, 24360.00, 43980.00, 22880.00, '2026-09-29 06:36:33', '2026-09-30 17:08:42');

-- --------------------------------------------------------

--
-- Table structure for table `fact_td_losses`
--

CREATE TABLE `fact_td_losses` (
  `td_loss_id` int(10) UNSIGNED NOT NULL,
  `year_id` int(10) UNSIGNED NOT NULL,
  `td_losses_gwh` decimal(12,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fact_td_losses`
--

INSERT INTO `fact_td_losses` (`td_loss_id`, `year_id`, `td_losses_gwh`, `created_at`, `updated_at`) VALUES
(1, 4, 20043.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(2, 5, 20371.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(3, 6, 21037.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(4, 7, 22506.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(5, 8, 21912.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(6, 9, 18742.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(7, 10, 19396.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(8, 11, 18957.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(9, 12, 15315.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(10, 13, 16054.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(11, 14, 16372.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(12, 15, 16932.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(13, 16, 17627.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(14, 17, 17209.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(15, 18, 23582.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(16, 19, 21110.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(17, 20, 16765.00, '2026-09-29 06:36:33', '2026-09-29 06:36:33'),
(35, 21, 24000.00, '2026-09-29 06:58:15', '2026-09-29 06:58:15');

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_domain_base_unit`
-- (See below for the actual view)
--
CREATE TABLE `v_domain_base_unit` (
`domain` varchar(11)
,`base_unit` varchar(3)
,`applies_to` varchar(57)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_re_with_co2`
-- (See below for the actual view)
--
CREATE TABLE `v_re_with_co2` (
`year_id` int(10) unsigned
,`calendar_year` int(11)
,`capacity_mw` decimal(12,2)
,`gen_solar_gwh` decimal(15,2)
,`gen_wind_gwh` decimal(15,2)
,`gen_hydro_gwh` decimal(15,2)
,`gen_coal_gwh` decimal(15,2)
,`gen_gas_gwh` decimal(15,2)
,`gen_nuclear_gwh` decimal(15,2)
,`demand_gwh` decimal(15,2)
,`re_gen_gwh` decimal(17,2)
,`fossil_gen_gwh` decimal(16,2)
,`co2_emissions_t` decimal(20,2)
,`co2_mt` decimal(21,2)
,`pakistan_ef_tco2_mwh` decimal(6,4)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_unit_conversion`
-- (See below for the actual view)
--
CREATE TABLE `v_unit_conversion` (
`domain` varchar(20)
,`display_unit` varchar(20)
,`base_unit` varchar(20)
,`to_base` decimal(24,12)
,`display_factor` decimal(25,12)
,`formula` varchar(71)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_unit_metadata_check`
-- (See below for the actual view)
--
CREATE TABLE `v_unit_metadata_check` (
`domain` varchar(20)
,`table_name` varchar(60)
,`column_name` varchar(60)
,`base_unit` varchar(20)
,`display_unit` varchar(20)
,`db_factor` decimal(18,10)
,`expected_factor` decimal(25,12)
,`status` varchar(13)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_unit_metadata_orphans`
-- (See below for the actual view)
--
CREATE TABLE `v_unit_metadata_orphans` (
`id` int(11)
,`domain` varchar(20)
,`table_name` varchar(60)
,`column_name` varchar(60)
,`display_unit` varchar(20)
);

-- --------------------------------------------------------

--
-- Structure for view `v_domain_base_unit`
--
DROP TABLE IF EXISTS `v_domain_base_unit`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_domain_base_unit`  AS SELECT 'energy' AS `domain`, 'TOE' AS `base_unit`, 'Primary energy supply, final consumption, losses, savings' AS `applies_to`union all select 'electricity' AS `electricity`,'GWh' AS `GWh`,'Generation, demand, imports, consumption, T&D losses' AS `Generation, demand, imports, consumption, T&D losses` union all select 'power' AS `power`,'MW' AS `MW`,'Installed capacity, renewable capacity' AS `Installed capacity, renewable capacity` union all select 'gas' AS `gas`,'BCF' AS `BCF`,'Gas production, consumption, reserves, LNG volume' AS `Gas production, consumption, reserves, LNG volume` union all select 'emission' AS `emission`,'t' AS `t`,'CO2 emissions (mass)' AS `CO2 emissions (mass)` union all select 'economic' AS `economic`,'USD' AS `USD`,'GDP, growth %, population -- fixed, not converted' AS `GDP, growth %, population -- fixed, not converted`  ;

-- --------------------------------------------------------

--
-- Structure for view `v_re_with_co2`
--
DROP TABLE IF EXISTS `v_re_with_co2`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_re_with_co2`  AS SELECT `re`.`year_id` AS `year_id`, `re`.`calendar_year` AS `calendar_year`, `re`.`capacity_mw` AS `capacity_mw`, `re`.`gen_solar_gwh` AS `gen_solar_gwh`, `re`.`gen_wind_gwh` AS `gen_wind_gwh`, `re`.`gen_hydro_gwh` AS `gen_hydro_gwh`, `re`.`gen_coal_gwh` AS `gen_coal_gwh`, `re`.`gen_gas_gwh` AS `gen_gas_gwh`, `re`.`gen_nuclear_gwh` AS `gen_nuclear_gwh`, `re`.`demand_gwh` AS `demand_gwh`, coalesce(`re`.`gen_solar_gwh`,0) + coalesce(`re`.`gen_wind_gwh`,0) + coalesce(`re`.`gen_hydro_gwh`,0) AS `re_gen_gwh`, coalesce(`re`.`gen_coal_gwh`,0) + coalesce(`re`.`gen_gas_gwh`,0) AS `fossil_gen_gwh`, `c`.`co2_emissions_t` AS `co2_emissions_t`, round(`c`.`co2_emissions_t` / 1000000,2) AS `co2_mt`, (select `fact_derived_ef`.`avg_ef_tco2_mwh` from `fact_derived_ef` where `fact_derived_ef`.`country_name` = 'Pakistan' limit 1) AS `pakistan_ef_tco2_mwh` FROM ((`fact_renewable_energy` `re` left join `dim_country` `dc` on(`dc`.`country_name` = 'Pakistan')) left join `fact_co2_emissions` `c` on(`c`.`country_id` = `dc`.`country_id` and `c`.`calendar_year` = `re`.`calendar_year`)) ;

-- --------------------------------------------------------

--
-- Structure for view `v_unit_conversion`
--
DROP TABLE IF EXISTS `v_unit_conversion`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_unit_conversion`  AS SELECT `d`.`domain` AS `domain`, `d`.`unit_code` AS `display_unit`, CASE WHEN `d`.`is_fixed` = 1 THEN `d`.`unit_code` ELSE `b`.`unit_code` END AS `base_unit`, `d`.`to_base` AS `to_base`, CASE WHEN `d`.`is_fixed` = 1 THEN 1.000000000000 ELSE 1 / `d`.`to_base` END AS `display_factor`, CASE WHEN `d`.`is_fixed` = 1 THEN concat(`d`.`unit_code`,' (fixed - no conversion)') ELSE concat('1 ',`d`.`unit_code`,' = ',format(`d`.`to_base`,6),' ',`b`.`unit_code`) END AS `formula` FROM (`dim_unit` `d` left join `dim_unit` `b` on(`b`.`domain` = `d`.`domain` and `b`.`is_base` = 1)) ORDER BY `d`.`domain` ASC, `d`.`sort_order` ASC ;

-- --------------------------------------------------------

--
-- Structure for view `v_unit_metadata_check`
--
DROP TABLE IF EXISTS `v_unit_metadata_check`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_unit_metadata_check`  AS SELECT `m`.`domain` AS `domain`, `m`.`table_name` AS `table_name`, `m`.`column_name` AS `column_name`, `m`.`base_unit` AS `base_unit`, `m`.`display_unit` AS `display_unit`, `m`.`conversion_factor` AS `db_factor`, `c`.`display_factor` AS `expected_factor`, CASE WHEN `c`.`display_factor` is null THEN 'NO MASTER ROW' WHEN abs(`m`.`conversion_factor` - `c`.`display_factor`) < 0.000000001 THEN 'OK' ELSE 'MISMATCH' END AS `status` FROM (`dim_unit_metadata` `m` left join `v_unit_conversion` `c` on(`c`.`domain` = `m`.`domain` and `c`.`display_unit` = `m`.`display_unit`)) ;

-- --------------------------------------------------------

--
-- Structure for view `v_unit_metadata_orphans`
--
DROP TABLE IF EXISTS `v_unit_metadata_orphans`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_unit_metadata_orphans`  AS SELECT `m`.`id` AS `id`, `m`.`domain` AS `domain`, `m`.`table_name` AS `table_name`, `m`.`column_name` AS `column_name`, `m`.`display_unit` AS `display_unit` FROM (`dim_unit_metadata` `m` left join `information_schema`.`columns` `c` on(`c`.`TABLE_SCHEMA` = database() and `c`.`TABLE_NAME` = `m`.`table_name` and `c`.`COLUMN_NAME` = `m`.`column_name`)) WHERE `c`.`COLUMN_NAME` is null ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `dim_country`
--
ALTER TABLE `dim_country`
  ADD PRIMARY KEY (`country_id`),
  ADD UNIQUE KEY `uk_country_name` (`country_name`),
  ADD KEY `idx_country_code` (`country_code`);

--
-- Indexes for table `dim_emission_factor`
--
ALTER TABLE `dim_emission_factor`
  ADD PRIMARY KEY (`factor_id`),
  ADD UNIQUE KEY `uk_source` (`source_id`);

--
-- Indexes for table `dim_energy_source`
--
ALTER TABLE `dim_energy_source`
  ADD PRIMARY KEY (`source_id`),
  ADD UNIQUE KEY `uk_source_name` (`source_name`);

--
-- Indexes for table `dim_province`
--
ALTER TABLE `dim_province`
  ADD PRIMARY KEY (`province_id`),
  ADD UNIQUE KEY `uk_province_name` (`province_name`);

--
-- Indexes for table `dim_sector`
--
ALTER TABLE `dim_sector`
  ADD PRIMARY KEY (`sector_id`),
  ADD UNIQUE KEY `uk_sector_name` (`sector_name`);

--
-- Indexes for table `dim_unit`
--
ALTER TABLE `dim_unit`
  ADD PRIMARY KEY (`unit_code`),
  ADD KEY `idx_unit_domain` (`domain`);

--
-- Indexes for table `dim_unit_metadata`
--
ALTER TABLE `dim_unit_metadata`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_tc_unit` (`table_name`,`column_name`,`display_unit`),
  ADD KEY `idx_domain` (`domain`);

--
-- Indexes for table `dim_users`
--
ALTER TABLE `dim_users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `dim_utility`
--
ALTER TABLE `dim_utility`
  ADD PRIMARY KEY (`utility_id`),
  ADD UNIQUE KEY `uk_utility_name` (`utility_name`);

--
-- Indexes for table `dim_year`
--
ALTER TABLE `dim_year`
  ADD PRIMARY KEY (`year_id`),
  ADD UNIQUE KEY `uk_fiscal_year` (`fiscal_year`),
  ADD KEY `idx_calendar_year` (`calendar_year`);

--
-- Indexes for table `fact_co2_emissions`
--
ALTER TABLE `fact_co2_emissions`
  ADD PRIMARY KEY (`co2_id`),
  ADD UNIQUE KEY `uk_country_year` (`country_id`,`calendar_year`),
  ADD KEY `idx_year` (`calendar_year`);

--
-- Indexes for table `fact_consm_conn`
--
ALTER TABLE `fact_consm_conn`
  ADD PRIMARY KEY (`connection_id`),
  ADD UNIQUE KEY `uk_year_utility_province_sector` (`year_id`,`utility_id`,`province_id`,`sector_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_utility` (`utility_id`),
  ADD KEY `idx_province` (`province_id`),
  ADD KEY `idx_sector` (`sector_id`);

--
-- Indexes for table `fact_derived_ef`
--
ALTER TABLE `fact_derived_ef`
  ADD PRIMARY KEY (`ef_id`),
  ADD KEY `idx_country` (`country_name`);

--
-- Indexes for table `fact_economic_indicators`
--
ALTER TABLE `fact_economic_indicators`
  ADD PRIMARY KEY (`economic_id`),
  ADD UNIQUE KEY `uk_year` (`year_id`),
  ADD KEY `idx_calendar_year` (`calendar_year`),
  ADD KEY `idx_year` (`year_id`);

--
-- Indexes for table `fact_elec_generation`
--
ALTER TABLE `fact_elec_generation`
  ADD PRIMARY KEY (`generation_id`),
  ADD UNIQUE KEY `uk_year` (`year_id`),
  ADD KEY `idx_year` (`year_id`);

--
-- Indexes for table `fact_elec_province_consumption`
--
ALTER TABLE `fact_elec_province_consumption`
  ADD PRIMARY KEY (`prov_cons_id`),
  ADD UNIQUE KEY `uk_year_province` (`year_id`,`province_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_province` (`province_id`);

--
-- Indexes for table `fact_elec_sector_consumption`
--
ALTER TABLE `fact_elec_sector_consumption`
  ADD PRIMARY KEY (`elec_sector_id`),
  ADD UNIQUE KEY `uk_year_sector` (`year_id`,`sector_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_sector` (`sector_id`);

--
-- Indexes for table `fact_energy_overview`
--
ALTER TABLE `fact_energy_overview`
  ADD PRIMARY KEY (`overview_id`),
  ADD UNIQUE KEY `uk_year` (`year_id`),
  ADD KEY `idx_year` (`year_id`);

--
-- Indexes for table `fact_final_energy_consumption`
--
ALTER TABLE `fact_final_energy_consumption`
  ADD PRIMARY KEY (`consumption_id`),
  ADD UNIQUE KEY `uk_year_source` (`year_id`,`source_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_source` (`source_id`);

--
-- Indexes for table `fact_gas_province_consumption`
--
ALTER TABLE `fact_gas_province_consumption`
  ADD PRIMARY KEY (`gas_prov_id`),
  ADD UNIQUE KEY `uk_year_province` (`year_id`,`province_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_province` (`province_id`);

--
-- Indexes for table `fact_gas_reserves`
--
ALTER TABLE `fact_gas_reserves`
  ADD PRIMARY KEY (`reserve_id`),
  ADD UNIQUE KEY `uk_reference_year` (`reference_year`);

--
-- Indexes for table `fact_gas_sector_consumption`
--
ALTER TABLE `fact_gas_sector_consumption`
  ADD PRIMARY KEY (`gas_sector_id`),
  ADD UNIQUE KEY `uk_year_sector` (`year_id`,`sector_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_sector` (`sector_id`);

--
-- Indexes for table `fact_lng_imports`
--
ALTER TABLE `fact_lng_imports`
  ADD PRIMARY KEY (`lng_import_id`),
  ADD UNIQUE KEY `uk_year` (`year_id`),
  ADD KEY `idx_year` (`year_id`);

--
-- Indexes for table `fact_natural_gas`
--
ALTER TABLE `fact_natural_gas`
  ADD PRIMARY KEY (`gas_id`),
  ADD UNIQUE KEY `uk_year` (`year_id`),
  ADD KEY `idx_year` (`year_id`);

--
-- Indexes for table `fact_primary_energy_supply`
--
ALTER TABLE `fact_primary_energy_supply`
  ADD PRIMARY KEY (`supply_id`),
  ADD UNIQUE KEY `uk_year_source` (`year_id`,`source_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_source` (`source_id`);

--
-- Indexes for table `fact_renewable_capacity`
--
ALTER TABLE `fact_renewable_capacity`
  ADD PRIMARY KEY (`renewable_capacity_id`),
  ADD UNIQUE KEY `uk_year_source` (`year_id`,`renewable_source`),
  ADD KEY `idx_year` (`year_id`);

--
-- Indexes for table `fact_renewable_energy`
--
ALTER TABLE `fact_renewable_energy`
  ADD PRIMARY KEY (`renewable_energy_id`),
  ADD UNIQUE KEY `uk_year` (`year_id`),
  ADD KEY `idx_year` (`year_id`),
  ADD KEY `idx_calendar_year` (`calendar_year`);

--
-- Indexes for table `fact_td_losses`
--
ALTER TABLE `fact_td_losses`
  ADD PRIMARY KEY (`td_loss_id`),
  ADD UNIQUE KEY `uk_year` (`year_id`),
  ADD KEY `idx_year` (`year_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `dim_country`
--
ALTER TABLE `dim_country`
  MODIFY `country_id` smallint(5) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=248;

--
-- AUTO_INCREMENT for table `dim_emission_factor`
--
ALTER TABLE `dim_emission_factor`
  MODIFY `factor_id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `dim_energy_source`
--
ALTER TABLE `dim_energy_source`
  MODIFY `source_id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `dim_province`
--
ALTER TABLE `dim_province`
  MODIFY `province_id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `dim_sector`
--
ALTER TABLE `dim_sector`
  MODIFY `sector_id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `dim_unit_metadata`
--
ALTER TABLE `dim_unit_metadata`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=145;

--
-- AUTO_INCREMENT for table `dim_users`
--
ALTER TABLE `dim_users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `dim_utility`
--
ALTER TABLE `dim_utility`
  MODIFY `utility_id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `dim_year`
--
ALTER TABLE `dim_year`
  MODIFY `year_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- AUTO_INCREMENT for table `fact_co2_emissions`
--
ALTER TABLE `fact_co2_emissions`
  MODIFY `co2_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT for table `fact_consm_conn`
--
ALTER TABLE `fact_consm_conn`
  MODIFY `connection_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=61;

--
-- AUTO_INCREMENT for table `fact_derived_ef`
--
ALTER TABLE `fact_derived_ef`
  MODIFY `ef_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `fact_economic_indicators`
--
ALTER TABLE `fact_economic_indicators`
  MODIFY `economic_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT for table `fact_elec_generation`
--
ALTER TABLE `fact_elec_generation`
  MODIFY `generation_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=40;

--
-- AUTO_INCREMENT for table `fact_elec_province_consumption`
--
ALTER TABLE `fact_elec_province_consumption`
  MODIFY `prov_cons_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=201;

--
-- AUTO_INCREMENT for table `fact_elec_sector_consumption`
--
ALTER TABLE `fact_elec_sector_consumption`
  MODIFY `elec_sector_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=321;

--
-- AUTO_INCREMENT for table `fact_energy_overview`
--
ALTER TABLE `fact_energy_overview`
  MODIFY `overview_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `fact_final_energy_consumption`
--
ALTER TABLE `fact_final_energy_consumption`
  MODIFY `consumption_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=195;

--
-- AUTO_INCREMENT for table `fact_gas_province_consumption`
--
ALTER TABLE `fact_gas_province_consumption`
  MODIFY `gas_prov_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `fact_gas_reserves`
--
ALTER TABLE `fact_gas_reserves`
  MODIFY `reserve_id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `fact_gas_sector_consumption`
--
ALTER TABLE `fact_gas_sector_consumption`
  MODIFY `gas_sector_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55;

--
-- AUTO_INCREMENT for table `fact_lng_imports`
--
ALTER TABLE `fact_lng_imports`
  MODIFY `lng_import_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `fact_natural_gas`
--
ALTER TABLE `fact_natural_gas`
  MODIFY `gas_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

--
-- AUTO_INCREMENT for table `fact_primary_energy_supply`
--
ALTER TABLE `fact_primary_energy_supply`
  MODIFY `supply_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=321;

--
-- AUTO_INCREMENT for table `fact_renewable_capacity`
--
ALTER TABLE `fact_renewable_capacity`
  MODIFY `renewable_capacity_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;

--
-- AUTO_INCREMENT for table `fact_renewable_energy`
--
ALTER TABLE `fact_renewable_energy`
  MODIFY `renewable_energy_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;

--
-- AUTO_INCREMENT for table `fact_td_losses`
--
ALTER TABLE `fact_td_losses`
  MODIFY `td_loss_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `dim_emission_factor`
--
ALTER TABLE `dim_emission_factor`
  ADD CONSTRAINT `fk_ef_source` FOREIGN KEY (`source_id`) REFERENCES `dim_energy_source` (`source_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_co2_emissions`
--
ALTER TABLE `fact_co2_emissions`
  ADD CONSTRAINT `fk_co2_country` FOREIGN KEY (`country_id`) REFERENCES `dim_country` (`country_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_consm_conn`
--
ALTER TABLE `fact_consm_conn`
  ADD CONSTRAINT `fk_cc_province` FOREIGN KEY (`province_id`) REFERENCES `dim_province` (`province_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_cc_sector` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_cc_utility` FOREIGN KEY (`utility_id`) REFERENCES `dim_utility` (`utility_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_cc_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_economic_indicators`
--
ALTER TABLE `fact_economic_indicators`
  ADD CONSTRAINT `fk_ei_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_elec_generation`
--
ALTER TABLE `fact_elec_generation`
  ADD CONSTRAINT `fk_elec_gen_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_elec_province_consumption`
--
ALTER TABLE `fact_elec_province_consumption`
  ADD CONSTRAINT `fk_epc_province` FOREIGN KEY (`province_id`) REFERENCES `dim_province` (`province_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_epc_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_elec_sector_consumption`
--
ALTER TABLE `fact_elec_sector_consumption`
  ADD CONSTRAINT `fk_esc_sector` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_esc_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_energy_overview`
--
ALTER TABLE `fact_energy_overview`
  ADD CONSTRAINT `fk_overview_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_final_energy_consumption`
--
ALTER TABLE `fact_final_energy_consumption`
  ADD CONSTRAINT `fk_fec_source` FOREIGN KEY (`source_id`) REFERENCES `dim_energy_source` (`source_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_fec_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_gas_province_consumption`
--
ALTER TABLE `fact_gas_province_consumption`
  ADD CONSTRAINT `fk_gpc_province` FOREIGN KEY (`province_id`) REFERENCES `dim_province` (`province_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_gpc_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_gas_sector_consumption`
--
ALTER TABLE `fact_gas_sector_consumption`
  ADD CONSTRAINT `fk_gsc_sector` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_gsc_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_lng_imports`
--
ALTER TABLE `fact_lng_imports`
  ADD CONSTRAINT `fk_lng_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_natural_gas`
--
ALTER TABLE `fact_natural_gas`
  ADD CONSTRAINT `fk_gas_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_primary_energy_supply`
--
ALTER TABLE `fact_primary_energy_supply`
  ADD CONSTRAINT `fk_supply_source` FOREIGN KEY (`source_id`) REFERENCES `dim_energy_source` (`source_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_supply_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_renewable_capacity`
--
ALTER TABLE `fact_renewable_capacity`
  ADD CONSTRAINT `fk_rc_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_renewable_energy`
--
ALTER TABLE `fact_renewable_energy`
  ADD CONSTRAINT `fk_re_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `fact_td_losses`
--
ALTER TABLE `fact_td_losses`
  ADD CONSTRAINT `fk_td_year` FOREIGN KEY (`year_id`) REFERENCES `dim_year` (`year_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
