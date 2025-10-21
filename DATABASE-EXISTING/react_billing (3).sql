-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Oct 10, 2025 at 04:50 PM
-- Server version: 8.4.3
-- PHP Version: 8.3.16

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `react_billing`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_logs`
--

CREATE TABLE `activity_logs` (
  `id` int NOT NULL,
  `user_id` bigint NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT (now()),
  `action` varchar(255) NOT NULL,
  `details` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `activity_logs`
--

INSERT INTO `activity_logs` (`id`, `user_id`, `timestamp`, `action`, `details`) VALUES
(1, 4, '2025-09-09 14:26:23', 'PATCH /pelanggan/5', '{\"no_ktp\": \"2323223423423412\", \"nama\": \"Jhon\", \"alamat\": \"Rusun Pinus Elok\", \"alamat_2\": \"Pinus Coba 1\", \"tgl_instalasi\": \"2025-09-09\", \"blok\": \"A2\", \"unit\": \"33\", \"no_telp\": \"09877654323432\", \"email\": \"mana@coba.com\", \"id_brand\": \"ajn-01\", \"layanan\": \"Internet 20 Mbps\", \"id\": 5, \"harga_layanan\": {\"id_brand\": \"ajn-01\", \"brand\": \"Jakinet\", \"pajak\": 11, \"xendit_key_name\": \"JAKINET\"}}'),
(2, 4, '2025-09-09 14:38:38', 'POST /data_teknis/check-ip', '{\"ip_address\": \"200.12.33.11\", \"current_id\": null}'),
(3, 4, '2025-09-09 14:39:08', 'POST /data_teknis/check-ip', '{\"ip_address\": \"101.101.101.\", \"current_id\": null}'),
(4, 4, '2025-09-09 14:39:10', 'POST /data_teknis/check-ip', '{\"ip_address\": \"101.101.101.48\", \"current_id\": null}'),
(5, 4, '2025-09-09 14:46:39', 'POST /data_teknis/check-ip', '{\"ip_address\": \"200.200.200.111\", \"current_id\": null}'),
(6, 4, '2025-09-09 14:46:55', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"profile_pppoe\": \"20Mbps-d\", \"pelanggan_id\": 5, \"mikrotik_server_id\": 2, \"olt\": \"Pinus\", \"id_pelanggan\": \"coba-coa\", \"password_pppoe\": \"212121212\", \"ip_pelanggan\": \"200.200.200.111\", \"id_vlan\": \"200\"}'),
(7, 4, '2025-09-09 14:47:47', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 6, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 5}'),
(8, 4, '2025-09-09 14:47:48', 'POST /langganan/', '{\"pelanggan_id\": 5, \"paket_layanan_id\": 6, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_mulai_langganan\": null, \"sertakan_bulan_depan\": false}'),
(9, 4, '2025-09-09 15:05:27', 'POST /permissions/generate', NULL),
(10, 4, '2025-09-09 17:03:59', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundary5MhBk2LK8DiunapN]'),
(11, 4, '2025-09-09 17:04:37', 'PATCH /mikrotik_servers/2', '{\"name\": \"Parama\", \"host_ip\": \"12.12.12.10\", \"username\": \"userapi\", \"port\": 9729, \"is_active\": true, \"id\": 2, \"ros_version\": \"7.1.2\", \"last_connection_status\": \"Success\", \"last_connected_at\": \"2025-09-08T21:17:52\"}'),
(12, 4, '2025-09-09 17:05:13', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryMRuAecHRQUCxAGAW]'),
(13, 4, '2025-09-09 17:11:57', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundarymSrKR27Hz8y4tIUq]'),
(14, 4, '2025-09-09 19:44:09', 'POST /pelanggan/', '{\"nama\": \"Ahmad Rizki\", \"no_ktp\": \"4543455345345344\", \"email\": \"ahmad@admin.com\", \"no_telp\": \"08986937819\", \"layanan\": \"Internet 10 Mbps\", \"alamat\": \"Tambun\", \"blok\": \"a\", \"unit\": \"4\", \"tgl_instalasi\": \"2025-09-09\", \"alamat_2\": \"Pinus Coba 1\", \"id_brand\": \"ajn-02\"}'),
(15, 4, '2025-09-09 19:46:03', 'POST /data_teknis/check-ip', '{\"ip_address\": \"12.21.33.22\", \"current_id\": null}'),
(16, 4, '2025-09-09 19:46:09', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"profile_pppoe\": \"10Mbps-c\", \"pelanggan_id\": 156, \"mikrotik_server_id\": 1, \"olt\": \"Tambun\", \"id_pelanggan\": \"COBAAA\", \"password_pppoe\": \"1212212\", \"ip_pelanggan\": \"12.21.33.22\", \"id_vlan\": \"1111\"}'),
(17, 4, '2025-09-09 19:47:06', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 4, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 156}'),
(18, 4, '2025-09-09 19:47:11', 'POST /langganan/', '{\"pelanggan_id\": 156, \"paket_layanan_id\": 4, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_mulai_langganan\": null, \"sertakan_bulan_depan\": false}'),
(19, 4, '2025-09-09 19:47:42', 'POST /invoices/generate', '{\"langganan_id\": 58}'),
(20, 4, '2025-09-09 19:48:07', 'DELETE /invoices/1', NULL),
(21, 4, '2025-09-18 14:58:19', 'DELETE /data_teknis/51', NULL),
(22, 4, '2025-09-18 14:58:23', 'DELETE /langganan/58', NULL),
(23, 4, '2025-09-18 14:58:26', 'DELETE /pelanggan/156', NULL),
(24, 4, '2025-09-18 14:58:53', 'POST /pelanggan/', '{\"nama\": \"Ahmad Rizki\", \"no_ktp\": \"2323232332343445\", \"email\": \"ahmad@ajnusa.com\", \"no_telp\": \"08986937819\", \"layanan\": \"Internet 20 Mbps\", \"alamat\": \"Tambun\", \"blok\": \"AA\", \"unit\": \"22\", \"tgl_instalasi\": \"2025-09-18\", \"alamat_2\": \"Jl. Bintara jaya\", \"id_brand\": \"ajn-02\"}'),
(25, 4, '2025-09-18 14:59:12', 'POST /data_teknis/check-ip', '{\"ip_address\": \"200.100.22.111\", \"current_id\": null}'),
(26, 4, '2025-09-18 14:59:20', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"profile_pppoe\": \"20Mbps-a\", \"id_pelanggan\": \"TESTTTTT\", \"password_pppoe\": \"password\", \"pelanggan_id\": 157, \"mikrotik_server_id\": 1, \"olt\": \"Tambun\", \"ip_pelanggan\": \"200.100.22.111\", \"id_vlan\": \"11111\"}'),
(27, 4, '2025-09-18 14:59:25', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 9, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 157}'),
(28, 4, '2025-09-18 14:59:28', 'POST /langganan/', '{\"pelanggan_id\": 157, \"paket_layanan_id\": 9, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_mulai_langganan\": null, \"sertakan_bulan_depan\": false}'),
(29, 4, '2025-09-18 15:57:28', 'POST /invoices/generate', '{\"langganan_id\": 59}'),
(30, 4, '2025-09-18 16:02:43', 'DELETE /invoices/2', NULL),
(31, 4, '2025-09-18 16:03:55', 'POST /invoices/generate', '{\"langganan_id\": 59}'),
(32, 4, '2025-09-18 23:02:05', 'DELETE /langganan/59', NULL),
(33, 4, '2025-09-18 23:02:10', 'DELETE /data_teknis/52', NULL),
(34, 4, '2025-09-18 23:56:45', 'DELETE /pelanggan/157', NULL),
(35, 4, '2025-09-18 23:57:31', 'POST /pelanggan/', '{\"nama\": \"Ahmad Rizki\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 20 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"A\", \"unit\": \"2\", \"tgl_instalasi\": \"2025-09-18\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-02\"}'),
(36, 4, '2025-09-19 00:00:44', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(37, 4, '2025-09-19 00:00:50', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"profile_pppoe\": \"20Mbps-a\", \"id_pelanggan\": \"COBAAAAAAAAA\", \"password_pppoe\": \"***REDACTED***\", \"pelanggan_id\": 158, \"mikrotik_server_id\": 1, \"olt\": \"Tambun\", \"ip_pelanggan\": \"200.111.111.222\", \"id_vlan\": \"121212\"}'),
(38, 4, '2025-09-19 00:01:02', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 9, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 158}'),
(39, 4, '2025-09-19 00:01:04', 'POST /langganan/', '{\"pelanggan_id\": 158, \"paket_layanan_id\": 9, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_mulai_langganan\": null, \"sertakan_bulan_depan\": false}'),
(40, 4, '2025-09-19 00:01:15', 'POST /invoices/generate', '{\"langganan_id\": 60}'),
(41, 4, '2025-09-19 00:01:53', 'DELETE /data_teknis/53', NULL),
(42, 4, '2025-09-19 00:01:56', 'DELETE /langganan/60', NULL),
(43, 4, '2025-09-19 00:02:00', 'DELETE /pelanggan/158', NULL),
(44, 4, '2025-09-19 00:21:49', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7HSQRFkI6jbBGKC2]'),
(45, 4, '2025-09-19 09:51:15', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundarynBTLrs1bMiAxx8Aw]'),
(46, 4, '2025-09-19 09:54:46', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryBy1ffmG8he4Kwoxo]'),
(47, 4, '2025-09-19 09:57:42', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryZz13JGcJGPvt0HJA]'),
(48, 4, '2025-09-19 14:43:22', 'POST /invoices/generate', '{\"langganan_id\": 61}'),
(49, 4, '2025-09-19 22:59:41', 'POST /calculator/prorate', '{\"id_brand\": \"ajn-01\", \"paket_layanan_id\": 6, \"tgl_mulai\": \"2025-09-19\"}'),
(50, 4, '2025-09-19 23:00:08', 'POST /permissions/generate', NULL),
(51, 4, '2025-09-19 23:00:16', 'PATCH /roles/2', '{\"name\": \"admin\", \"permission_ids\": [89, 13, 81, 70, 66, 9, 93, 17, 45, 5, 56, 62, 21, 101, 97, 1, 33, 85, 29, 37, 41, 25, 92, 16, 84, 73, 69, 12, 96, 20, 48, 8, 59, 65, 24, 104, 100, 4, 36, 88, 32, 40, 44, 28, 91, 15, 83, 72, 68, 11, 95, 19, 47, 7, 58, 64, 23, 103, 99, 3, 35, 87, 31, 39, 43, 27, 90, 14, 82, 71, 67, 10, 94, 18, 46, 6, 57, 63, 22, 102, 98, 2, 34, 86, 30, 38, 42, 26, 61, 55, 76, 79, 75, 52, 53, 77, 74, 78, 80, 49, 50, 51, 60, 54]}'),
(52, 4, '2025-09-19 23:27:14', 'POST /invoices/generate', '{\"langganan_id\": 61}'),
(53, 4, '2025-09-19 23:40:43', 'POST /invoices/generate', '{\"langganan_id\": 61}'),
(54, 4, '2025-09-19 23:45:36', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 4, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 202}'),
(55, 4, '2025-09-19 23:45:41', 'PATCH /langganan/61', '{\"paket_layanan_id\": 4, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_jatuh_tempo\": \"2025-10-01\", \"harga_awal\": 166500}'),
(56, 4, '2025-09-19 23:50:43', 'POST /invoices/generate', '{\"langganan_id\": 62}'),
(57, 4, '2025-09-19 23:59:48', 'POST /invoices/generate', '{\"langganan_id\": 62}'),
(58, 4, '2025-09-20 00:03:14', 'POST /invoices/generate', '{\"langganan_id\": 62}'),
(59, 4, '2025-09-20 00:12:55', 'POST /invoices/generate', '{\"langganan_id\": 62}'),
(60, 4, '2025-09-20 01:16:44', 'POST /invoices/generate', '{\"langganan_id\": 62}'),
(61, 4, '2025-09-20 01:27:53', 'POST /invoices/generate', '{\"langganan_id\": 62}'),
(62, 4, '2025-09-20 19:27:53', 'POST /pelanggan/', '{\"nama\": \"Irsyad\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 10 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"A\", \"unit\": \"3\", \"tgl_instalasi\": \"2025-09-20\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-02\"}'),
(63, 4, '2025-09-20 19:53:13', 'DELETE /pelanggan/204', NULL),
(64, 4, '2025-09-20 19:54:02', 'POST /pelanggan/', '{\"nama\": \"Irsyad\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 10 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"sas\", \"unit\": \"22\", \"tgl_instalasi\": \"2025-09-20\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-02\"}'),
(65, 4, '2025-09-20 23:47:40', 'DELETE /pelanggan/205', NULL),
(66, 4, '2025-09-20 23:48:16', 'POST /pelanggan/', '{\"nama\": \"Irsyad\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 20 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"S\", \"unit\": \"33\", \"tgl_instalasi\": \"2025-09-20\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-02\"}'),
(67, 4, '2025-09-20 23:54:28', 'POST /users/', '{\"name\": \"Deni\", \"email\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"role_id\": 8}'),
(68, 4, '2025-09-20 23:55:49', 'DELETE /pelanggan/206', NULL),
(69, 4, '2025-09-20 23:56:21', 'POST /pelanggan/', '{\"nama\": \"Irsyad\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 10 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"A\", \"unit\": \"22\", \"tgl_instalasi\": \"2025-09-20\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-02\"}'),
(70, 7, '2025-09-20 23:58:01', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(71, 7, '2025-09-21 00:00:31', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(72, 7, '2025-09-21 00:02:54', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(73, 4, '2025-09-21 00:04:11', 'POST /mikrotik_servers/1/test_connection', NULL),
(74, 7, '2025-09-21 00:05:02', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(75, 7, '2025-09-21 00:05:12', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"profile_pppoe\": \"10Mbps-c\", \"pelanggan_id\": 207, \"mikrotik_server_id\": 1, \"olt\": \"Tambun\", \"id_pelanggan\": \"ART-002\", \"password_pppoe\": \"***REDACTED***\", \"ip_pelanggan\": \"20.20.2.111\"}'),
(76, 6, '2025-09-21 00:09:11', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 4, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 207}'),
(77, 6, '2025-09-21 00:09:13', 'POST /langganan/', '{\"pelanggan_id\": 207, \"paket_layanan_id\": 4, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_mulai_langganan\": null, \"sertakan_bulan_depan\": false}'),
(78, 6, '2025-09-21 00:17:36', 'PATCH /pelanggan/207', '{\"no_ktp\": \"***REDACTED***\", \"nama\": \"Irsyad\", \"alamat\": \"***REDACTED***\", \"alamat_2\": \"***REDACTED***\", \"tgl_instalasi\": \"2025-09-20\", \"blok\": \"A\", \"unit\": \"22\", \"no_telp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"id_brand\": \"ajn-02\", \"layanan\": \"Internet 10 Mbps\", \"id\": 207, \"harga_layanan\": {\"id_brand\": \"ajn-02\", \"brand\": \"Jelantik\", \"pajak\": 11, \"xendit_key_name\": \"JELANTIK\"}}'),
(79, 6, '2025-09-21 00:17:59', 'POST /invoices/generate', '{\"langganan_id\": 63}'),
(80, 4, '2025-09-21 01:49:01', 'POST /invoices/generate', '{\"langganan_id\": 63}'),
(81, 4, '2025-09-21 22:34:00', 'POST /permissions/generate', NULL),
(82, 4, '2025-09-21 22:36:05', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(83, 4, '2025-09-21 22:39:11', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(84, 4, '2025-09-21 22:50:02', 'POST /notifications/83/mark-as-read', NULL),
(85, 4, '2025-09-21 23:06:20', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(86, 4, '2025-09-22 09:11:40', 'POST /notifications/85/mark-as-read', NULL),
(87, 4, '2025-09-22 09:17:48', 'POST /pelanggan/', '{\"nama\": \"Jhon\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 10 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"A\", \"unit\": \"3\", \"tgl_instalasi\": \"2025-09-22\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-02\"}'),
(88, 7, '2025-09-22 09:18:37', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(89, 7, '2025-09-22 09:18:53', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"profile_pppoe\": \"10Mbps-c\", \"password_pppoe\": \"***REDACTED***\", \"pelanggan_id\": 208, \"mikrotik_server_id\": 1, \"olt\": \"Tambun\", \"id_pelanggan\": \"Testtt2039\", \"ip_pelanggan\": \"30.10.22.11\", \"id_vlan\": \"2002\"}'),
(90, 6, '2025-09-22 09:20:11', 'POST /notifications/1758507536775/mark-as-read', NULL),
(91, 6, '2025-09-22 09:23:38', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 4, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 208}'),
(92, 6, '2025-09-22 09:23:40', 'POST /langganan/', '{\"pelanggan_id\": 208, \"paket_layanan_id\": 4, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_mulai_langganan\": null, \"sertakan_bulan_depan\": false}'),
(93, 6, '2025-09-22 09:23:56', 'POST /invoices/generate', '{\"langganan_id\": 64}'),
(94, 7, '2025-09-22 09:24:09', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(95, 6, '2025-09-22 09:27:50', 'DELETE /invoices/16', NULL),
(96, 6, '2025-09-22 09:27:57', 'POST /invoices/generate', '{\"langganan_id\": 64}'),
(97, 6, '2025-09-22 09:31:15', 'DELETE /invoices/17', NULL),
(98, 6, '2025-09-22 09:31:21', 'POST /invoices/generate', '{\"langganan_id\": 64}'),
(99, 6, '2025-09-22 09:32:15', 'POST /notifications/1758508300372/mark-as-read', NULL),
(100, 6, '2025-09-22 09:39:44', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(101, 4, '2025-09-22 11:00:40', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(102, 4, '2025-09-22 11:01:50', 'POST /mikrotik_servers/', '{\"id\": null, \"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"port\": 9729, \"username\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"is_active\": true}'),
(103, 4, '2025-09-22 11:02:12', 'PATCH /mikrotik_servers/3', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 3, \"ros_version\": null, \"last_connection_status\": null, \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(104, 4, '2025-09-22 11:03:00', 'PATCH /mikrotik_servers/3', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 3, \"ros_version\": null, \"last_connection_status\": null, \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(105, 4, '2025-09-22 11:14:26', 'DELETE /mikrotik_servers/3', NULL),
(106, 4, '2025-09-22 11:14:46', 'POST /mikrotik_servers/', '{\"id\": null, \"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"port\": 9729, \"username\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"is_active\": true}'),
(107, 4, '2025-09-22 11:30:39', 'DELETE /mikrotik_servers/4', NULL),
(108, 4, '2025-09-22 11:45:34', 'POST /mikrotik_servers/1/test_connection', NULL),
(109, 4, '2025-09-22 11:46:15', 'PATCH /mikrotik_servers/5', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9728, \"is_active\": true, \"id\": 5, \"ros_version\": null, \"last_connection_status\": null, \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(110, 4, '2025-09-22 11:48:14', 'PATCH /mikrotik_servers/5', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 5, \"ros_version\": null, \"last_connection_status\": null, \"last_connected_at\": null}'),
(111, 4, '2025-09-22 11:50:47', 'DELETE /mikrotik_servers/5', NULL),
(112, 4, '2025-09-22 11:51:07', 'POST /mikrotik_servers/', '{\"id\": null, \"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"port\": 9729, \"username\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"is_active\": true}'),
(113, 4, '2025-09-22 11:53:51', 'POST /mikrotik_servers/1/test_connection', NULL),
(114, 4, '2025-09-22 11:54:01', 'POST /mikrotik_servers/2/test_connection', NULL),
(115, 4, '2025-09-22 13:40:47', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(116, 4, '2025-09-22 13:41:04', 'POST /mikrotik_servers/1/test_connection', NULL),
(117, 4, '2025-09-22 13:48:01', 'POST /mikrotik_servers/2/test_connection', NULL),
(118, 4, '2025-09-22 13:48:16', 'PATCH /mikrotik_servers/6', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 6, \"ros_version\": null, \"last_connection_status\": null, \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(119, 4, '2025-09-22 13:48:22', 'POST /mikrotik_servers/6/test_connection', NULL),
(120, 4, '2025-09-22 13:48:31', 'POST /mikrotik_servers/6/test_connection', NULL),
(121, 4, '2025-09-22 13:57:22', 'PATCH /mikrotik_servers/6', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 6, \"ros_version\": null, \"last_connection_status\": null, \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(122, 4, '2025-09-22 13:57:23', 'POST /mikrotik_servers/6/test_connection', NULL),
(123, 4, '2025-09-22 13:57:30', 'POST /mikrotik_servers/6/test_connection', NULL),
(124, 4, '2025-09-22 14:26:04', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(125, 4, '2025-09-22 14:26:12', 'POST /mikrotik_servers/2/test_connection', NULL),
(126, 4, '2025-09-22 14:30:30', 'PATCH /mikrotik_servers/6', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 6, \"ros_version\": null, \"last_connection_status\": null, \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(127, 4, '2025-09-22 14:30:33', 'POST /mikrotik_servers/6/test_connection', NULL),
(128, 4, '2025-09-22 14:30:36', 'POST /mikrotik_servers/6/test_connection', NULL),
(129, 4, '2025-09-22 14:45:01', 'PATCH /mikrotik_servers/6', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 6, \"ros_version\": null, \"last_connection_status\": \"failure\", \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(130, 4, '2025-09-22 14:45:03', 'POST /mikrotik_servers/6/test_connection', NULL),
(131, 4, '2025-09-22 14:45:08', 'POST /mikrotik_servers/6/test_connection', NULL),
(132, 4, '2025-09-22 14:50:48', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(133, 4, '2025-09-22 14:51:03', 'POST /mikrotik_servers/6/test_connection', NULL),
(134, 4, '2025-09-22 15:01:30', 'PATCH /mikrotik_servers/1', '{\"name\": \"Tambun\", \"host_ip\": \"17.17.17.2\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 1, \"ros_version\": \"6.49.10 (long-term)\", \"last_connection_status\": \"failure\", \"last_connected_at\": \"2025-09-21T00:04:12\", \"password\": \"***REDACTED***\"}'),
(135, 4, '2025-09-22 15:01:32', 'POST /mikrotik_servers/1/test_connection', NULL),
(136, 4, '2025-09-22 15:01:37', 'PATCH /mikrotik_servers/6', '{\"name\": \"Waringin\", \"host_ip\": \"18.18.18.6\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 6, \"ros_version\": null, \"last_connection_status\": \"failure\", \"last_connected_at\": null, \"password\": \"***REDACTED***\"}'),
(137, 4, '2025-09-22 15:01:39', 'POST /mikrotik_servers/6/test_connection', NULL),
(138, 4, '2025-09-22 15:01:45', 'PATCH /mikrotik_servers/2', '{\"name\": \"Parama\", \"host_ip\": \"12.12.12.10\", \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"id\": 2, \"ros_version\": \"7.7 (stable)\", \"last_connection_status\": \"failure\", \"last_connected_at\": \"2025-09-08T21:17:52\", \"password\": \"***REDACTED***\"}'),
(139, 4, '2025-09-22 15:01:47', 'POST /mikrotik_servers/2/test_connection', NULL),
(140, 4, '2025-09-22 19:24:33', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(141, 4, '2025-09-22 19:33:53', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(142, 4, '2025-09-22 19:50:08', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundarynFEjiIOkzQ9lMkqw]'),
(143, 4, '2025-09-22 19:50:21', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryTtQUxvP4hcuyB60R]'),
(144, 4, '2025-09-22 19:50:30', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryNRdYT6RFv9O3beMf]'),
(145, 4, '2025-09-22 21:11:36', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(146, 4, '2025-09-22 21:11:49', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(147, 4, '2025-09-25 10:24:00', 'PATCH /mikrotik_servers/1', '{\"last_connection_message\": \"Decryption failed. The encryption key may be incorrect or the data is corrupted.\", \"last_connection_time\": \"2025-09-25T03:23:46.522461+00:00\", \"name\": \"Tambun\", \"host_ip\": \"17.17.17.2\", \"password\": \"***REDACTED***\", \"ros_version\": \"6.49.10 (long-term)\", \"last_connection_status\": \"failure\", \"created_at\": \"2025-07-17T19:32:01\", \"id\": 1, \"username\": \"***REDACTED***\", \"port\": 9729, \"is_active\": true, \"last_connected_at\": \"2025-09-21T00:04:12\", \"updated_at\": \"2025-09-25T10:16:35\"}'),
(148, 4, '2025-09-25 10:24:08', 'POST /mikrotik_servers/1/test_connection', NULL),
(149, 4, '2025-09-25 10:24:39', 'POST /mikrotik_servers/', '{\"id\": null, \"name\": \"coba\", \"host_ip\": \"20.20.11.11\", \"port\": 8728, \"username\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"is_active\": true}'),
(150, 4, '2025-09-25 10:24:47', 'DELETE /mikrotik_servers/7', NULL),
(151, 4, '2025-09-25 10:30:58', 'POST /mikrotik_servers/', '{\"id\": null, \"name\": \"Tambun\", \"host_ip\": \"17.17.17.2\", \"port\": 9729, \"username\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"is_active\": true}'),
(152, 4, '2025-09-25 10:31:10', 'POST /mikrotik_servers/8/test_connection', NULL),
(153, 4, '2025-09-25 10:32:36', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundary6aFgpDgTDUKYDd2B]'),
(154, 4, '2025-09-25 10:32:46', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundary68gaerDJp7bK72lL]'),
(155, 4, '2025-09-25 10:33:03', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundarysJuUw8apFAmYm7wq]'),
(156, 4, '2025-09-25 10:34:20', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 9, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 212}'),
(157, 4, '2025-09-25 10:34:26', 'PATCH /langganan/68', '{\"paket_layanan_id\": 9, \"status\": \"Suspended\", \"metode_pembayaran\": \"Otomatis\", \"tgl_jatuh_tempo\": \"2025-10-01\", \"harga_awal\": 231990}'),
(158, 4, '2025-09-25 10:40:34', 'POST /invoices/generate', '{\"langganan_id\": 68}'),
(159, 4, '2025-09-25 11:00:32', 'POST /invoices/generate', '{\"langganan_id\": 67}'),
(160, 4, '2025-09-25 11:01:03', 'POST /notifications/mark-all-as-read', NULL),
(161, 4, '2025-09-25 12:38:00', 'PATCH /pelanggan/211', '{\"id\": 211, \"no_ktp\": \"***REDACTED***\", \"nama\": \"Ahmad\", \"alamat\": \"***REDACTED***\", \"alamat_2\": \"***REDACTED***\", \"tgl_instalasi\": \"2024-01-15\", \"blok\": \"A\", \"unit\": \"12\", \"no_telp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"id_brand\": \"ajn-02\", \"layanan\": \"Internet 10 Mbps\", \"harga_layanan\": {\"id_brand\": \"ajn-02\", \"brand\": \"Jelantik\", \"pajak\": 11, \"xendit_key_name\": \"JELANTIK\"}}'),
(162, 4, '2025-09-25 12:38:08', 'PATCH /pelanggan/212', '{\"id\": 212, \"no_ktp\": \"***REDACTED***\", \"nama\": \"Rizki\", \"alamat\": \"***REDACTED***\", \"alamat_2\": \"***REDACTED***\", \"tgl_instalasi\": \"2024-02-20\", \"blok\": \"B\", \"unit\": \"25\", \"no_telp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"id_brand\": \"ajn-02\", \"layanan\": \"Internet 20 Mbps\", \"harga_layanan\": {\"id_brand\": \"ajn-02\", \"brand\": \"Jelantik\", \"pajak\": 11, \"xendit_key_name\": \"JELANTIK\"}}'),
(163, 4, '2025-09-25 13:49:07', 'POST /permissions/generate', NULL),
(164, 4, '2025-09-25 20:00:39', 'POST /mikrotik_servers/8/test_connection', NULL),
(165, 4, '2025-09-25 20:05:27', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 9, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 212}'),
(166, 4, '2025-09-25 20:05:31', 'PATCH /langganan/68', '{\"paket_layanan_id\": 9, \"status\": \"Suspended\", \"metode_pembayaran\": \"Otomatis\", \"tgl_jatuh_tempo\": \"2025-10-01\", \"harga_awal\": 231990}'),
(167, 4, '2025-09-25 20:06:11', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 9, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 212}'),
(168, 4, '2025-09-25 20:06:19', 'PATCH /langganan/68', '{\"paket_layanan_id\": 9, \"status\": \"Suspended\", \"metode_pembayaran\": \"Otomatis\", \"tgl_jatuh_tempo\": \"2025-12-01\", \"harga_awal\": 231990}'),
(169, 4, '2025-09-25 20:06:28', 'POST /invoices/generate', '{\"langganan_id\": 68}'),
(170, 4, '2025-09-25 20:07:16', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": 61}'),
(171, 4, '2025-09-25 20:07:26', 'PATCH /data_teknis/61', '{\"pelanggan_id\": 212, \"mikrotik_server_id\": 8, \"odp_id\": null, \"otb\": 0, \"odc\": 0, \"port_odp\": 0, \"id_vlan\": \"1\", \"id_pelanggan\": \"COBA-3030\", \"password_pppoe\": \"***REDACTED***\", \"ip_pelanggan\": \"200.110.11.20\", \"profile_pppoe\": \"20Mbps-a\", \"olt\": \"Tambun\", \"olt_custom\": null, \"pon\": 0, \"onu_power\": -20, \"sn\": null, \"speedtest_proof\": null, \"id\": 61}'),
(172, 4, '2025-09-25 20:08:25', 'POST /calculator/prorate', '{\"id_brand\": \"ajn-02\", \"paket_layanan_id\": 9, \"tgl_mulai\": \"2025-09-25\"}'),
(173, 4, '2025-09-25 20:23:02', 'POST /invoices/generate', '{\"langganan_id\": 67}'),
(174, 4, '2025-09-25 20:23:23', 'POST /notifications/1758806606943/mark-as-read', NULL),
(175, 4, '2025-09-27 00:42:52', 'DELETE /langganan/68', NULL),
(176, 4, '2025-09-27 00:42:52', 'DELETE /langganan/67', NULL),
(177, 4, '2025-09-27 00:42:58', 'DELETE /data_teknis/60', NULL),
(178, 4, '2025-09-27 00:42:58', 'DELETE /data_teknis/61', NULL),
(179, 4, '2025-09-27 00:43:04', 'DELETE /pelanggan/211', NULL),
(180, 4, '2025-09-27 00:43:04', 'DELETE /pelanggan/212', NULL),
(181, 4, '2025-09-27 00:45:21', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryaPZUsJtMc1UO4GBM]'),
(182, 4, '2025-09-27 00:46:31', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryl9xqhpvor2qSNa9k]'),
(183, 4, '2025-09-27 00:47:11', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryzZ0tjDqOIGAMGtLe]'),
(184, 4, '2025-09-27 01:00:49', 'POST /invoices/generate', '{\"langganan_id\": 69}'),
(185, 4, '2025-09-27 01:01:10', 'POST /notifications/mark-all-as-read', NULL),
(186, 4, '2025-09-27 01:28:06', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(187, 4, '2025-09-27 10:25:49', 'DELETE /langganan/69', NULL),
(188, 4, '2025-09-27 10:25:49', 'DELETE /langganan/70', NULL),
(189, 4, '2025-09-27 10:25:54', 'DELETE /data_teknis/62', NULL),
(190, 4, '2025-09-27 10:25:54', 'DELETE /data_teknis/63', NULL),
(191, 4, '2025-09-27 10:26:01', 'DELETE /pelanggan/214', NULL),
(192, 4, '2025-09-27 10:26:01', 'DELETE /pelanggan/213', NULL),
(193, 4, '2025-09-27 11:46:31', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(194, 4, '2025-09-27 16:11:16', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryORnVmIVsmpF7WTyR]'),
(195, 4, '2025-09-27 16:11:31', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryVJJFAJDlesyawlIL]'),
(196, 4, '2025-09-27 16:11:46', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryfxzTAO78aDXOSEUH]'),
(197, 4, '2025-09-27 16:17:41', 'POST /calculator/prorate', '{\"id_brand\": \"ajn-01\", \"paket_layanan_id\": 6, \"tgl_mulai\": \"2025-09-27\"}'),
(198, 4, '2025-09-28 20:25:49', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(199, 4, '2025-09-29 10:57:55', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(200, 4, '2025-09-29 13:29:45', 'DELETE /langganan/71', NULL),
(201, 4, '2025-09-29 13:29:45', 'DELETE /langganan/72', NULL),
(202, 4, '2025-09-29 13:29:51', 'DELETE /data_teknis/65', NULL),
(203, 4, '2025-09-29 13:29:51', 'DELETE /data_teknis/64', NULL),
(204, 4, '2025-09-29 13:29:58', 'DELETE /pelanggan/216', NULL),
(205, 4, '2025-09-29 13:29:58', 'DELETE /pelanggan/215', NULL),
(206, 4, '2025-09-29 13:30:21', 'POST /pelanggan/', '{\"nama\": \"Ahmad Rizki\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 10 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"X\", \"unit\": \"3\", \"tgl_instalasi\": \"2025-09-29\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-02\"}'),
(207, 4, '2025-09-29 13:32:36', 'POST /mikrotik_servers/8/test_connection', NULL),
(208, 4, '2025-09-29 13:32:59', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(209, 4, '2025-09-29 13:33:01', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(210, 4, '2025-09-29 13:40:16', 'POST /mikrotik_servers/8/test_connection', NULL),
(211, 4, '2025-09-29 13:42:30', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(212, 4, '2025-09-29 13:42:41', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"id_pelanggan\": \"AHMAD200000\", \"password_pppoe\": \"***REDACTED***\", \"pelanggan_id\": 217, \"mikrotik_server_id\": 8, \"olt\": \"Tambun\", \"ip_pelanggan\": \"10.10.20.30\", \"profile_pppoe\": \"10Mbps-a\", \"id_vlan\": \"10\"}'),
(213, 4, '2025-09-29 13:50:08', 'DELETE /data_teknis/66', NULL),
(214, 4, '2025-09-29 15:00:18', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(215, 4, '2025-09-29 19:50:02', 'DELETE /pelanggan/217', NULL),
(216, 4, '2025-09-29 19:50:12', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryNPAIejwBJGUSI5oQ]'),
(217, 4, '2025-09-29 19:50:28', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryGBytdYPhVeAoBgLS]'),
(218, 4, '2025-09-29 19:50:41', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundary3ZMbgwyjmALLBIC2]'),
(219, 4, '2025-09-29 20:52:04', 'POST /invoices/generate', '{\"langganan_id\": 73}'),
(220, 4, '2025-09-29 20:52:11', 'POST /invoices/generate', '{\"langganan_id\": 74}'),
(221, 4, '2025-09-29 20:53:37', 'POST /notifications/mark-all-as-read', NULL),
(222, 4, '2025-09-30 09:15:12', 'DELETE /langganan/73', NULL),
(223, 4, '2025-09-30 09:15:12', 'DELETE /langganan/74', NULL),
(224, 4, '2025-09-30 09:15:19', 'DELETE /data_teknis/68', NULL),
(225, 4, '2025-09-30 09:15:19', 'DELETE /data_teknis/67', NULL),
(226, 4, '2025-09-30 09:15:26', 'DELETE /pelanggan/219', NULL),
(227, 4, '2025-09-30 09:15:26', 'DELETE /pelanggan/218', NULL),
(228, 4, '2025-09-30 09:15:37', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryoaZsXjbVUSMUL3te]'),
(229, 4, '2025-09-30 09:15:57', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryT0pL2Gx0SOV3eh4o]'),
(230, 4, '2025-09-30 09:17:40', 'DELETE /data_teknis/70', NULL),
(231, 4, '2025-09-30 09:17:40', 'DELETE /data_teknis/69', NULL),
(232, 4, '2025-09-30 09:17:47', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundarycuuJJp5mcPBMmAav]'),
(233, 4, '2025-09-30 09:17:59', 'DELETE /data_teknis/72', NULL),
(234, 4, '2025-09-30 09:17:59', 'DELETE /data_teknis/71', NULL),
(235, 4, '2025-09-30 09:18:06', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryPFmZbhotuGQW3VYM]'),
(236, 4, '2025-09-30 09:18:37', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryvt2Tpmy17fkFeyR4]'),
(237, 4, '2025-09-30 09:22:40', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(238, 4, '2025-09-30 09:43:24', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(239, 4, '2025-10-04 15:54:15', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(240, 4, '2025-10-04 16:37:11', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(241, 4, '2025-10-04 17:34:13', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(242, 4, '2025-10-04 17:50:54', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(243, 4, '2025-10-04 19:30:44', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(244, 4, '2025-10-04 19:34:01', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(245, 4, '2025-10-04 21:18:01', 'POST /invoices/generate', '{\"langganan_id\": 75}'),
(246, 4, '2025-10-04 21:18:40', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(247, 4, '2025-10-04 21:30:35', 'POST /permissions/generate', NULL),
(248, 4, '2025-10-04 21:30:45', 'PATCH /roles/2', '{\"name\": \"admin\", \"permission_ids\": [89, 13, 81, 70, 66, 9, 93, 17, 45, 5, 56, 62, 21, 101, 97, 1, 33, 85, 29, 37, 41, 25, 92, 16, 84, 73, 69, 12, 96, 20, 48, 8, 59, 65, 24, 104, 100, 4, 36, 88, 32, 40, 44, 28, 91, 15, 83, 72, 68, 11, 95, 19, 47, 7, 58, 64, 23, 103, 99, 3, 35, 87, 31, 39, 43, 27, 90, 14, 82, 71, 67, 10, 94, 18, 46, 6, 57, 63, 22, 102, 98, 2, 34, 86, 30, 38, 42, 26, 61, 55, 76, 79, 75, 52, 53, 77, 74, 78, 80, 49, 50, 51, 60, 54]}'),
(249, 4, '2025-10-04 22:23:43', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(250, 4, '2025-10-04 22:34:54', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(251, 4, '2025-10-05 09:46:40', 'POST /mikrotik_servers/8/test_connection', NULL),
(252, 4, '2025-10-05 10:40:37', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(253, 4, '2025-10-05 15:07:52', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(254, 4, '2025-10-05 15:59:17', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(255, 4, '2025-10-05 16:13:14', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(256, 4, '2025-10-05 20:44:10', 'DELETE /langganan/76', NULL),
(257, 4, '2025-10-05 20:44:10', 'DELETE /langganan/75', NULL),
(258, 4, '2025-10-05 20:44:31', 'DELETE /data_teknis/74', NULL),
(259, 4, '2025-10-05 20:44:31', 'DELETE /data_teknis/73', NULL),
(260, 4, '2025-10-05 20:44:38', 'DELETE /pelanggan/220', NULL),
(261, 4, '2025-10-05 20:44:38', 'DELETE /pelanggan/221', NULL),
(262, 4, '2025-10-05 20:44:48', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7XQ3UfvasQvoEIgW]'),
(263, 4, '2025-10-05 20:44:57', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryswCqcOkS5s4vl8he]'),
(264, 4, '2025-10-05 20:45:06', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryxfQnPkm3A6vX6R8A]'),
(265, 4, '2025-10-05 20:45:31', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(266, 4, '2025-10-05 21:37:10', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(267, 4, '2025-10-06 09:51:49', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(268, 4, '2025-10-06 09:55:36', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(269, 4, '2025-10-06 10:48:54', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(270, 4, '2025-10-06 19:49:29', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(271, 4, '2025-10-06 19:51:09', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(272, 4, '2025-10-06 20:04:08', 'POST /calculator/prorate', '{\"id_brand\": \"ajn-01\", \"paket_layanan_id\": 6, \"tgl_mulai\": \"2025-10-06\"}'),
(273, 4, '2025-10-06 20:04:36', 'POST /permissions/generate', NULL),
(274, 4, '2025-10-06 20:08:18', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(275, 4, '2025-10-06 20:33:43', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(276, 4, '2025-10-06 20:34:38', 'POST /users/', '{\"name\": \"KOMAR\", \"email\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"role_id\": 6}'),
(277, 4, '2025-10-06 20:34:45', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(278, 8, '2025-10-06 20:35:01', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(279, 4, '2025-10-07 10:14:14', 'DELETE /invoices/27', NULL),
(280, 4, '2025-10-07 10:22:45', 'POST /invoices/generate', '{\"langganan_id\": 77}'),
(281, 4, '2025-10-07 10:46:32', 'POST /invoices/generate', '{\"langganan_id\": 77}'),
(282, 4, '2025-10-07 21:26:24', 'DELETE /langganan/78', NULL),
(283, 4, '2025-10-07 21:26:24', 'DELETE /langganan/77', NULL),
(284, 4, '2025-10-07 21:26:32', 'DELETE /data_teknis/75', NULL),
(285, 4, '2025-10-07 21:26:32', 'DELETE /data_teknis/76', NULL),
(286, 4, '2025-10-07 21:36:57', 'DELETE /pelanggan/223', NULL),
(287, 4, '2025-10-07 21:36:57', 'DELETE /pelanggan/222', NULL),
(288, 4, '2025-10-07 21:38:22', 'POST /mikrotik_servers/', '{\"id\": null, \"name\": \"Tipar\", \"host_ip\": \"12.12.12.6\", \"port\": 9729, \"username\": \"***REDACTED***\", \"password\": \"***REDACTED***\", \"is_active\": true}'),
(289, 4, '2025-10-07 21:38:25', 'POST /mikrotik_servers/9/test_connection', NULL),
(290, 4, '2025-10-07 21:43:13', 'POST /pelanggan/', '{\"nama\": \"Ahmad\", \"no_ktp\": \"***REDACTED***\", \"email\": \"***REDACTED***\", \"no_telp\": \"***REDACTED***\", \"layanan\": \"Internet 20 Mbps\", \"alamat\": \"***REDACTED***\", \"blok\": \"AA\", \"unit\": \"21\", \"tgl_instalasi\": \"2025-10-07\", \"alamat_2\": \"***REDACTED***\", \"id_brand\": \"ajn-01\"}'),
(291, 4, '2025-10-07 21:43:46', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": null}'),
(292, 4, '2025-10-07 21:43:58', 'POST /data_teknis/', '{\"pon\": 0, \"otb\": 0, \"odc\": 0, \"odp\": 0, \"onu_power\": 0, \"id_pelanggan\": \"COBA-COBAAHMAD\", \"password_pppoe\": \"***REDACTED***\", \"pelanggan_id\": 224, \"mikrotik_server_id\": 9, \"olt\": \"Tipar\", \"ip_pelanggan\": \"102.102.100.76\", \"profile_pppoe\": \"20Mbps-f\", \"id_vlan\": \"102\"}'),
(293, 4, '2025-10-07 22:03:40', 'POST /langganan/calculate-price', '{\"paket_layanan_id\": 6, \"metode_pembayaran\": \"Otomatis\", \"pelanggan_id\": 224}'),
(294, 4, '2025-10-07 22:03:43', 'POST /langganan/', '{\"pelanggan_id\": 224, \"paket_layanan_id\": 6, \"status\": \"Aktif\", \"metode_pembayaran\": \"Otomatis\", \"tgl_mulai_langganan\": null, \"sertakan_bulan_depan\": false}'),
(295, 4, '2025-10-07 22:05:06', 'POST /invoices/generate', '{\"langganan_id\": 79}'),
(296, 4, '2025-10-07 22:05:53', 'POST /data_teknis/check-ip', '{\"ip_address\": \"***REDACTED***\", \"current_id\": 77}'),
(297, 4, '2025-10-07 22:05:58', 'PATCH /data_teknis/77', '{\"pelanggan_id\": 224, \"mikrotik_server_id\": 9, \"odp_id\": null, \"otb\": 0, \"odc\": 0, \"port_odp\": null, \"id_vlan\": \"102\", \"id_pelanggan\": \"COBA-COBAAHMAD\", \"password_pppoe\": \"***REDACTED***\", \"ip_pelanggan\": \"102.102.100.77\", \"profile_pppoe\": \"20Mbps-f\", \"olt\": \"Tipar\", \"olt_custom\": null, \"pon\": 0, \"onu_power\": 0, \"sn\": null, \"speedtest_proof\": null, \"id\": 77}'),
(298, 4, '2025-10-07 22:06:08', 'DELETE /langganan/79', NULL),
(299, 4, '2025-10-07 22:06:13', 'DELETE /data_teknis/77', NULL),
(300, 4, '2025-10-07 22:06:21', 'DELETE /pelanggan/224', NULL),
(301, 4, '2025-10-08 09:29:30', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(302, 4, '2025-10-08 09:56:57', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(303, 4, '2025-10-08 10:06:19', 'POST /auth/logout', '{\"refresh_token\": \"***REDACTED***\"}'),
(304, 4, '2025-10-08 12:11:33', 'POST /pelanggan/import', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryQ9WZL94yM8xoM6TQ]'),
(305, 4, '2025-10-08 12:11:41', 'POST /data_teknis/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryWSlifPcLEERm8PmQ]'),
(306, 4, '2025-10-08 12:11:51', 'POST /langganan/import/csv', '[Data non-JSON, Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryLJBInC5CBGdhUF6O]');

-- --------------------------------------------------------

--
-- Table structure for table `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `alembic_version`
--

INSERT INTO `alembic_version` (`version_num`) VALUES
('2210f33597f3');

-- --------------------------------------------------------

--
-- Table structure for table `data_teknis`
--

CREATE TABLE `data_teknis` (
  `id` bigint NOT NULL,
  `pelanggan_id` bigint NOT NULL,
  `id_vlan` varchar(191) DEFAULT NULL,
  `id_pelanggan` varchar(191) NOT NULL,
  `password_pppoe` varchar(191) NOT NULL,
  `ip_pelanggan` varchar(191) DEFAULT NULL,
  `profile_pppoe` varchar(191) DEFAULT NULL,
  `olt` varchar(191) DEFAULT NULL,
  `olt_custom` varchar(191) DEFAULT NULL,
  `pon` int DEFAULT NULL,
  `otb` int DEFAULT NULL,
  `odc` int DEFAULT NULL,
  `speedtest_proof` varchar(191) DEFAULT NULL,
  `onu_power` int DEFAULT NULL,
  `mikrotik_server_id` bigint DEFAULT NULL,
  `sn` varchar(191) DEFAULT NULL,
  `odp_id` int DEFAULT NULL,
  `port_odp` int DEFAULT NULL,
  `mikrotik_sync_pending` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `data_teknis`
--

INSERT INTO `data_teknis` (`id`, `pelanggan_id`, `id_vlan`, `id_pelanggan`, `password_pppoe`, `ip_pelanggan`, `profile_pppoe`, `olt`, `olt_custom`, `pon`, `otb`, `odc`, `speedtest_proof`, `onu_power`, `mikrotik_server_id`, `sn`, `odp_id`, `port_odp`, `mikrotik_sync_pending`) VALUES
(78, 225, '1', 'COBA-2020', 'pass', '200.10.222.11', '10Mbps-a', 'Tambun', NULL, 0, 0, 0, NULL, -20, 8, NULL, NULL, 0, 0),
(79, 226, '1', 'COBA-3030', 'pass', '200.110.11.11', '20Mbps-a', 'Tambun', NULL, 0, 0, 0, NULL, -20, 8, NULL, NULL, 0, 0);

-- --------------------------------------------------------

--
-- Table structure for table `harga_layanan`
--

CREATE TABLE `harga_layanan` (
  `id_brand` varchar(191) NOT NULL,
  `brand` varchar(191) NOT NULL,
  `pajak` decimal(5,2) NOT NULL,
  `xendit_key_name` varchar(50) NOT NULL DEFAULT 'JAKINET'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `harga_layanan`
--

INSERT INTO `harga_layanan` (`id_brand`, `brand`, `pajak`, `xendit_key_name`) VALUES
('ajn-01', 'Jakinet', 11.00, 'JAKINET'),
('ajn-02', 'Jelantik', 11.00, 'JELANTIK'),
('ajn-03', 'Jelantik Nagrak', 11.00, 'JAKINET');

-- --------------------------------------------------------

--
-- Table structure for table `inventory_history`
--

CREATE TABLE `inventory_history` (
  `id` int NOT NULL,
  `action` varchar(255) NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT (now()),
  `item_id` int NOT NULL,
  `user_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `inventory_items`
--

CREATE TABLE `inventory_items` (
  `id` int NOT NULL,
  `serial_number` varchar(255) NOT NULL,
  `mac_address` varchar(255) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `purchase_date` date DEFAULT NULL,
  `notes` text,
  `item_type_id` int NOT NULL,
  `status_id` int NOT NULL,
  `pelanggan_id` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `inventory_items`
--

INSERT INTO `inventory_items` (`id`, `serial_number`, `mac_address`, `location`, `purchase_date`, `notes`, `item_type_id`, `status_id`, `pelanggan_id`) VALUES
(1, 'SNGCTE333', 'ACDFFFSSSASD', 'Rusun Pinus', NULL, 'Dismantel rusun', 5, 4, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `inventory_item_types`
--

CREATE TABLE `inventory_item_types` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `inventory_item_types`
--

INSERT INTO `inventory_item_types` (`id`, `name`) VALUES
(1, 'Mikrotik'),
(3, 'OLT HSGQ - EPON'),
(4, 'OLT HSGQ -GPON'),
(2, 'OLT ZTE C320'),
(5, 'ONT/ONU - ZTE');

-- --------------------------------------------------------

--
-- Table structure for table `inventory_statuses`
--

CREATE TABLE `inventory_statuses` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `inventory_statuses`
--

INSERT INTO `inventory_statuses` (`id`, `name`) VALUES
(5, 'Dismantle'),
(2, 'Gudang'),
(4, 'Hilang'),
(6, 'Perbaikan'),
(1, 'Rusak'),
(3, 'Terpasang');

-- --------------------------------------------------------

--
-- Table structure for table `invoices`
--

CREATE TABLE `invoices` (
  `id` bigint NOT NULL,
  `invoice_number` varchar(191) NOT NULL,
  `pelanggan_id` bigint NOT NULL,
  `id_pelanggan` varchar(255) NOT NULL,
  `brand` varchar(191) NOT NULL,
  `total_harga` decimal(15,2) NOT NULL,
  `no_telp` varchar(191) NOT NULL,
  `email` varchar(191) NOT NULL,
  `tgl_invoice` date NOT NULL,
  `tgl_jatuh_tempo` date NOT NULL,
  `status_invoice` varchar(50) NOT NULL,
  `payment_link` text,
  `expiry_date` datetime DEFAULT NULL,
  `xendit_id` varchar(191) DEFAULT NULL,
  `xendit_external_id` varchar(191) DEFAULT NULL,
  `paid_amount` decimal(15,2) DEFAULT NULL,
  `paid_at` timestamp NULL DEFAULT NULL,
  `is_processing` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` timestamp NULL DEFAULT NULL,
  `metode_pembayaran` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `langganan`
--

CREATE TABLE `langganan` (
  `id` bigint NOT NULL,
  `pelanggan_id` bigint NOT NULL,
  `paket_layanan_id` bigint NOT NULL,
  `tgl_jatuh_tempo` date DEFAULT NULL,
  `tgl_invoice_terakhir` date DEFAULT NULL,
  `status` varchar(100) NOT NULL DEFAULT 'Aktif',
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `metode_pembayaran` varchar(50) NOT NULL DEFAULT 'Otomatis',
  `harga_awal` decimal(15,2) DEFAULT NULL,
  `tgl_mulai_langganan` date DEFAULT NULL,
  `tgl_berhenti` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `langganan`
--

INSERT INTO `langganan` (`id`, `pelanggan_id`, `paket_layanan_id`, `tgl_jatuh_tempo`, `tgl_invoice_terakhir`, `status`, `created_at`, `updated_at`, `metode_pembayaran`, `harga_awal`, `tgl_mulai_langganan`, `tgl_berhenti`) VALUES
(80, 225, 3, '2025-10-01', NULL, 'Aktif', '2025-10-08 12:11:51', '2025-10-08 12:11:51', 'Otomatis', 135135.00, NULL, NULL),
(81, 226, 6, '2025-10-02', NULL, 'Aktif', '2025-10-08 12:11:51', '2025-10-08 12:11:51', 'Otomatis', 199000.00, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `mikrotik_servers`
--

CREATE TABLE `mikrotik_servers` (
  `id` bigint NOT NULL,
  `name` varchar(191) NOT NULL,
  `host_ip` varchar(191) NOT NULL,
  `username` varchar(191) NOT NULL,
  `password` text NOT NULL,
  `port` int NOT NULL,
  `ros_version` varchar(191) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `last_connection_status` varchar(191) DEFAULT NULL,
  `last_connected_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now())
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `mikrotik_servers`
--

INSERT INTO `mikrotik_servers` (`id`, `name`, `host_ip`, `username`, `password`, `port`, `ros_version`, `is_active`, `last_connection_status`, `last_connected_at`, `created_at`, `updated_at`) VALUES
(8, 'Tambun', '17.17.17.2', 'userapi', 'masukapi123!', 9729, '6.49.10 (long-term)', 1, 'success', NULL, '2025-09-25 10:30:58', '2025-09-29 13:32:36'),
(9, 'Tipar', '12.12.12.6', 'userapi', 'masukapi123!', 9729, '7.14.2 (stable)', 1, 'success', NULL, '2025-10-07 21:38:22', '2025-10-07 21:38:25');

-- --------------------------------------------------------

--
-- Table structure for table `odp`
--

CREATE TABLE `odp` (
  `id` int NOT NULL,
  `kode_odp` varchar(100) NOT NULL,
  `alamat` varchar(255) DEFAULT NULL,
  `kapasitas_port` int NOT NULL,
  `olt_id` int NOT NULL,
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `parent_odp_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `olt`
--

CREATE TABLE `olt` (
  `id` int NOT NULL,
  `nama_olt` varchar(100) NOT NULL,
  `ip_address` varchar(100) NOT NULL,
  `tipe_olt` varchar(50) NOT NULL,
  `username` varchar(100) DEFAULT NULL,
  `password` varchar(100) DEFAULT NULL,
  `mikrotik_server_id` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `paket_layanan`
--

CREATE TABLE `paket_layanan` (
  `id` bigint NOT NULL,
  `id_brand` varchar(191) NOT NULL,
  `nama_paket` varchar(191) NOT NULL,
  `kecepatan` int NOT NULL,
  `harga` decimal(15,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `paket_layanan`
--

INSERT INTO `paket_layanan` (`id`, `id_brand`, `nama_paket`, `kecepatan`, `harga`) VALUES
(3, 'ajn-01', 'Internet 10 Mbps', 10, 135135.00),
(4, 'ajn-02', 'Internet 10 Mbps', 10, 150000.00),
(5, 'ajn-03', 'Internet 10 Mbps', 10, 135135.00),
(6, 'ajn-01', 'Internet 20 Mbps', 20, 199000.00),
(7, 'ajn-01', 'Internet 30 Mbps', 30, 224000.00),
(8, 'ajn-01', 'Internet 50 Mbps', 50, 254000.00),
(9, 'ajn-02', 'Internet 20 Mbps', 20, 209000.00),
(10, 'ajn-02', 'Internet 30 Mbps', 30, 249000.00),
(11, 'ajn-02', 'Internet 50 Mbps', 50, 289000.00),
(12, 'ajn-03', 'Internet 20 Mbps', 20, 199000.00),
(13, 'ajn-03', 'Internet 30 Mbps', 30, 224000.00),
(14, 'ajn-03', 'Internet 50 Mbps', 50, 254000.00);

-- --------------------------------------------------------

--
-- Table structure for table `payment_callback_logs`
--

CREATE TABLE `payment_callback_logs` (
  `id` bigint NOT NULL,
  `idempotency_key` varchar(255) DEFAULT NULL,
  `xendit_id` varchar(255) NOT NULL,
  `external_id` varchar(255) NOT NULL,
  `callback_data` varchar(1000) DEFAULT NULL,
  `status` varchar(50) NOT NULL,
  `processed_at` datetime NOT NULL DEFAULT (now()),
  `created_at` datetime NOT NULL DEFAULT (now())
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `payment_callback_logs`
--

INSERT INTO `payment_callback_logs` (`id`, `idempotency_key`, `xendit_id`, `external_id`, `callback_data`, `status`, `processed_at`, `created_at`) VALUES
(1, NULL, '579c8d61f23fa4ca35e52da4', 'invoice_123124123', '{\"id\": \"579c8d61f23fa4ca35e52da4\", \"external_id\": \"invoice_123124123\", \"user_id\": \"5781d19b2e2385880609791c\", \"is_high\": true, \"payment_method\": \"BANK_TRANSFER\", \"status\": \"PAID\", \"merchant_name\": \"Xendit\", \"amount\": 50000, \"paid_amount\": 50000, \"bank_code\": \"PERMATA\", \"paid_at\": \"2016-10-12T08:15:03.404Z\", \"payer_email\": \"wildan@xendit.co\", \"description\": \"This is a description\", \"adjusted_received_amount\": 47500, \"fees_paid_amount\": 0, \"updated\": \"2016-10-10T08:15:03.404Z\", \"created\": \"2016-10-10T08:15:03.404Z\", \"currency\": \"IDR\", \"payment_channel\": \"PERMATA\", \"payment_destination\": \"888888888888\"}', 'PAID', '2025-10-07 10:05:42', '2025-10-07 10:05:42'),
(2, NULL, '68e48785e403c65493430e80', 'Jakinet/ftth/Ahmad/Oktober-2025/Rusun/28', '{\"id\": \"68e48785e403c65493430e80\", \"external_id\": \"Jakinet/ftth/Ahmad/Oktober-2025/Rusun/28\", \"user_id\": \"646b2edbd8bd47a22176e25d\", \"payment_method\": \"BANK_TRANSFER\", \"status\": \"PAID\", \"merchant_name\": \"Artacomindo Jejaring Nusa\", \"amount\": 135135, \"paid_amount\": 135135, \"bank_code\": \"MANDIRI\", \"paid_at\": \"2025-10-07T03:23:01.000Z\", \"description\": \"Biaya berlangganan internet up to 10 Mbps jatuh tempo pembayaran tanggal 01/10/2025\", \"is_high\": false, \"created\": \"2025-10-07T03:22:46.044Z\", \"updated\": \"2025-10-07T03:23:01.335Z\", \"currency\": \"IDR\", \"payment_channel\": \"MANDIRI\", \"payment_destination\": \"8860866922237\", \"items\": [{\"name\": \"Biaya berlangganan internet up to 10 Mbps\", \"price\": 121743, \"quantity\": 1}], \"fees\": [{\"type\": \"Tax\", \"value\": 13392}], \"payment_id\": \"5cb08401-9fc0-4c12-b090-aaecf5e31caa\"}', 'PAID', '2025-10-07 10:23:02', '2025-10-07 10:23:02'),
(3, NULL, '68e48d1843f0668d90d24ab5', 'Jakinet/ftth/Ahmad/November-2025/Rusun/29', '{\"id\": \"68e48d1843f0668d90d24ab5\", \"external_id\": \"Jakinet/ftth/Ahmad/November-2025/Rusun/29\", \"user_id\": \"646b2edbd8bd47a22176e25d\", \"payment_method\": \"BANK_TRANSFER\", \"status\": \"PAID\", \"merchant_name\": \"Artacomindo Jejaring Nusa\", \"amount\": 135135, \"paid_amount\": 135135, \"bank_code\": \"MANDIRI\", \"paid_at\": \"2025-10-07T03:46:40.000Z\", \"description\": \"Biaya berlangganan internet up to 10 Mbps jatuh tempo pembayaran tanggal 01/11/2025\", \"is_high\": false, \"created\": \"2025-10-07T03:46:32.962Z\", \"updated\": \"2025-10-07T03:46:40.965Z\", \"currency\": \"IDR\", \"payment_channel\": \"MANDIRI\", \"payment_destination\": \"8860811977564\", \"items\": [{\"name\": \"Biaya berlangganan internet up to 10 Mbps\", \"price\": 121743, \"quantity\": 1}], \"fees\": [{\"type\": \"Tax\", \"value\": 13392}], \"payment_id\": \"3fa9da38-3740-4b54-a1e9-be0c76512b68\"}', 'PAID', '2025-10-07 10:46:41', '2025-10-07 10:46:41'),
(4, '', '68e52c2343f0668d90d30fe9', 'Jakinet/ftth/Ahmad/November-2025/Rusun/30', '{\"id\": \"68e52c2343f0668d90d30fe9\", \"external_id\": \"Jakinet/ftth/Ahmad/November-2025/Rusun/30\", \"user_id\": \"646b2edbd8bd47a22176e25d\", \"payment_method\": \"BANK_TRANSFER\", \"status\": \"PAID\", \"merchant_name\": \"Artacomindo Jejaring Nusa\", \"amount\": 220890, \"paid_amount\": 220890, \"bank_code\": \"MANDIRI\", \"paid_at\": \"2025-10-07T15:05:23.000Z\", \"description\": \"Biaya berlangganan internet up to 20 Mbps jatuh tempo pembayaran tanggal 01/11/2025\", \"is_high\": false, \"created\": \"2025-10-07T15:05:07.747Z\", \"updated\": \"2025-10-07T15:05:23.726Z\", \"currency\": \"IDR\", \"payment_channel\": \"MANDIRI\", \"payment_destination\": \"8860822352004\", \"items\": [{\"name\": \"Biaya berlangganan internet up to 20 Mbps\", \"price\": 199000, \"quantity\": 1}], \"fees\": [{\"type\": \"Tax\", \"value\": 21890}], \"payment_id\": \"14be24b2-49a4-49c3-8c0e-51250da914e0\"}', 'PAID', '2025-10-07 22:05:23', '2025-10-07 22:05:23');

-- --------------------------------------------------------

--
-- Table structure for table `pelanggan`
--

CREATE TABLE `pelanggan` (
  `id` bigint NOT NULL,
  `no_ktp` varchar(191) NOT NULL,
  `nama` varchar(191) NOT NULL,
  `alamat` varchar(191) NOT NULL,
  `alamat_custom` varchar(191) DEFAULT NULL,
  `alamat_2` text,
  `tgl_instalasi` date DEFAULT NULL,
  `blok` varchar(191) NOT NULL,
  `unit` varchar(191) NOT NULL,
  `no_telp` varchar(191) NOT NULL,
  `email` varchar(191) NOT NULL,
  `id_brand` varchar(191) DEFAULT NULL,
  `layanan` varchar(191) DEFAULT NULL,
  `brand_default` varchar(191) DEFAULT NULL,
  `mikrotik_server_id` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now())
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `pelanggan`
--

INSERT INTO `pelanggan` (`id`, `no_ktp`, `nama`, `alamat`, `alamat_custom`, `alamat_2`, `tgl_instalasi`, `blok`, `unit`, `no_telp`, `email`, `id_brand`, `layanan`, `brand_default`, `mikrotik_server_id`, `created_at`, `updated_at`) VALUES
(225, 'gAAAAABo5fKFPP-HM_Exl3xdBwFeQ7WZW8D7Kyxgj8pxBTSjZ2Q46rGLZlGF0-HNXXN6K-955sjpvj1yozpIhHBVdGk_wXp402YLWt7cYzQBv9V9VOOF-wc=', 'Ahmad', 'Rusun Albo', NULL, 'RT 01 RW A', '2024-01-15', 'A', '12', '08986937819', 'ahmad@ajnusa.com', 'ajn-01', 'Internet 10 Mbps', NULL, NULL, '2025-10-08 12:11:33', '2025-10-08 12:11:33'),
(226, 'gAAAAABo5fKFGv_q1_to1TyLSOj7msbKOn4NFePGUi5V4OU8AUyDzFJeUoOIbSlj7RvGo5iqLZIkGMePaYT8_linglvAHz_KqhbAdCC6d2wrdQTSTcG5pLE=', 'Rizki', 'Rusun Albo', NULL, 'RW B', '2024-02-20', 'B', '25', '087843975540', 'ahmad@admin.com', 'ajn-01', 'Internet 20 Mbps', NULL, NULL, '2025-10-08 12:11:33', '2025-10-08 12:11:33');

-- --------------------------------------------------------

--
-- Table structure for table `permissions`
--

CREATE TABLE `permissions` (
  `id` bigint NOT NULL,
  `name` varchar(191) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `permissions`
--

INSERT INTO `permissions` (`id`, `name`) VALUES
(89, 'create_activity_log'),
(13, 'create_brand_paket'),
(81, 'create_dashboard'),
(70, 'create_dashboard_jakinet'),
(66, 'create_dashboard_pelanggan'),
(9, 'create_data_teknis'),
(93, 'create_inventory'),
(17, 'create_invoices'),
(45, 'create_kelola_s&k'),
(5, 'create_langganan'),
(56, 'create_laporan_pendapatan'),
(62, 'create_manajemen_inventaris'),
(21, 'create_mikrotik_servers'),
(101, 'create_odp_management'),
(97, 'create_olt'),
(1, 'create_pelanggan'),
(33, 'create_permissions'),
(85, 'create_reports_revenue'),
(29, 'create_roles'),
(37, 'create_s&k'),
(41, 'create_simulasi_harga'),
(25, 'create_users'),
(92, 'delete_activity_log'),
(16, 'delete_brand_paket'),
(84, 'delete_dashboard'),
(73, 'delete_dashboard_jakinet'),
(69, 'delete_dashboard_pelanggan'),
(12, 'delete_data_teknis'),
(96, 'delete_inventory'),
(20, 'delete_invoices'),
(48, 'delete_kelola_s&k'),
(8, 'delete_langganan'),
(59, 'delete_laporan_pendapatan'),
(65, 'delete_manajemen_inventaris'),
(24, 'delete_mikrotik_servers'),
(104, 'delete_odp_management'),
(100, 'delete_olt'),
(4, 'delete_pelanggan'),
(36, 'delete_permissions'),
(88, 'delete_reports_revenue'),
(32, 'delete_roles'),
(40, 'delete_s&k'),
(44, 'delete_simulasi_harga'),
(28, 'delete_users'),
(91, 'edit_activity_log'),
(15, 'edit_brand_paket'),
(83, 'edit_dashboard'),
(72, 'edit_dashboard_jakinet'),
(68, 'edit_dashboard_pelanggan'),
(11, 'edit_data_teknis'),
(95, 'edit_inventory'),
(19, 'edit_invoices'),
(47, 'edit_kelola_s&k'),
(7, 'edit_langganan'),
(58, 'edit_laporan_pendapatan'),
(64, 'edit_manajemen_inventaris'),
(23, 'edit_mikrotik_servers'),
(103, 'edit_odp_management'),
(99, 'edit_olt'),
(3, 'edit_pelanggan'),
(35, 'edit_permissions'),
(87, 'edit_reports_revenue'),
(31, 'edit_roles'),
(39, 'edit_s&k'),
(43, 'edit_simulasi_harga'),
(27, 'edit_users'),
(90, 'view_activity_log'),
(14, 'view_brand_paket'),
(82, 'view_dashboard'),
(71, 'view_dashboard_jakinet'),
(67, 'view_dashboard_pelanggan'),
(10, 'view_data_teknis'),
(94, 'view_inventory'),
(18, 'view_invoices'),
(46, 'view_kelola_s&k'),
(6, 'view_langganan'),
(57, 'view_laporan_pendapatan'),
(63, 'view_manajemen_inventaris'),
(22, 'view_mikrotik_servers'),
(102, 'view_odp_management'),
(98, 'view_olt'),
(2, 'view_pelanggan'),
(34, 'view_permissions'),
(86, 'view_reports_revenue'),
(30, 'view_roles'),
(38, 'view_s&k'),
(42, 'view_simulasi_harga'),
(26, 'view_users'),
(61, 'view_widget_alamat_aktif'),
(55, 'view_widget_invoice_bulanan'),
(76, 'view_widget_pelanggan_distribusi_chart'),
(79, 'view_widget_pelanggan_metrik_cepat'),
(75, 'view_widget_pelanggan_pendapatan_jakinet'),
(52, 'view_widget_pelanggan_per_lokasi'),
(53, 'view_widget_pelanggan_per_paket'),
(77, 'view_widget_pelanggan_pertumbuhan_chart'),
(74, 'view_widget_pelanggan_statistik_utama'),
(78, 'view_widget_pelanggan_status_overview_chart'),
(80, 'view_widget_pelanggan_tren_pendapatan_chart'),
(49, 'view_widget_pendapatan_bulanan'),
(50, 'view_widget_statistik_pelanggan'),
(51, 'view_widget_statistik_server'),
(60, 'view_widget_status_langganan'),
(54, 'view_widget_tren_pertumbuhan');

-- --------------------------------------------------------

--
-- Table structure for table `roles`
--

CREATE TABLE `roles` (
  `id` bigint NOT NULL,
  `name` varchar(191) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `roles`
--

INSERT INTO `roles` (`id`, `name`) VALUES
(2, 'admin'),
(6, 'Finance'),
(9, 'Monitoring'),
(8, 'NOC');

-- --------------------------------------------------------

--
-- Table structure for table `role_has_permissions`
--

CREATE TABLE `role_has_permissions` (
  `permission_id` bigint NOT NULL,
  `role_id` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `role_has_permissions`
--

INSERT INTO `role_has_permissions` (`permission_id`, `role_id`) VALUES
(1, 2),
(2, 2),
(3, 2),
(4, 2),
(5, 2),
(6, 2),
(7, 2),
(8, 2),
(9, 2),
(10, 2),
(11, 2),
(12, 2),
(13, 2),
(14, 2),
(15, 2),
(16, 2),
(17, 2),
(18, 2),
(19, 2),
(20, 2),
(21, 2),
(22, 2),
(23, 2),
(24, 2),
(25, 2),
(26, 2),
(27, 2),
(28, 2),
(29, 2),
(30, 2),
(31, 2),
(32, 2),
(33, 2),
(34, 2),
(35, 2),
(36, 2),
(37, 2),
(38, 2),
(39, 2),
(40, 2),
(41, 2),
(42, 2),
(43, 2),
(44, 2),
(45, 2),
(46, 2),
(47, 2),
(48, 2),
(49, 2),
(50, 2),
(51, 2),
(52, 2),
(53, 2),
(54, 2),
(55, 2),
(56, 2),
(57, 2),
(58, 2),
(59, 2),
(60, 2),
(61, 2),
(62, 2),
(63, 2),
(64, 2),
(65, 2),
(66, 2),
(67, 2),
(68, 2),
(69, 2),
(70, 2),
(71, 2),
(72, 2),
(73, 2),
(74, 2),
(75, 2),
(76, 2),
(77, 2),
(78, 2),
(79, 2),
(80, 2),
(81, 2),
(82, 2),
(83, 2),
(84, 2),
(85, 2),
(86, 2),
(87, 2),
(88, 2),
(89, 2),
(90, 2),
(91, 2),
(92, 2),
(93, 2),
(94, 2),
(95, 2),
(96, 2),
(97, 2),
(98, 2),
(99, 2),
(100, 2),
(101, 2),
(102, 2),
(103, 2),
(104, 2),
(1, 6),
(2, 6),
(3, 6),
(4, 6),
(5, 6),
(6, 6),
(7, 6),
(8, 6),
(9, 6),
(10, 6),
(11, 6),
(12, 6),
(13, 6),
(14, 6),
(15, 6),
(16, 6),
(17, 6),
(18, 6),
(19, 6),
(20, 6),
(49, 6),
(50, 6),
(51, 6),
(52, 6),
(53, 6),
(54, 6),
(55, 6),
(1, 8),
(2, 8),
(3, 8),
(4, 8),
(5, 8),
(6, 8),
(7, 8),
(8, 8),
(9, 8),
(10, 8),
(11, 8),
(12, 8),
(13, 8),
(14, 8),
(15, 8),
(16, 8),
(17, 8),
(18, 8),
(19, 8),
(20, 8),
(21, 8),
(22, 8),
(23, 8),
(24, 8),
(25, 8),
(26, 8),
(27, 8),
(28, 8),
(29, 8),
(30, 8),
(31, 8),
(32, 8),
(33, 8),
(34, 8),
(35, 8),
(36, 8),
(37, 8),
(38, 8),
(39, 8),
(40, 8),
(41, 8),
(42, 8),
(43, 8),
(44, 8),
(45, 8),
(46, 8),
(47, 8),
(48, 8),
(49, 8),
(50, 8),
(51, 8),
(52, 8),
(53, 8),
(54, 8),
(55, 8),
(56, 8),
(57, 8),
(58, 8),
(59, 8),
(60, 8),
(61, 8),
(62, 8),
(63, 8),
(64, 8),
(65, 8),
(66, 8),
(67, 8),
(68, 8),
(69, 8),
(70, 8),
(71, 8),
(72, 8),
(73, 8),
(52, 9),
(54, 9),
(57, 9),
(61, 9),
(74, 9),
(75, 9),
(76, 9),
(77, 9),
(78, 9),
(79, 9),
(80, 9);

-- --------------------------------------------------------

--
-- Table structure for table `syarat_ketentuan`
--

CREATE TABLE `syarat_ketentuan` (
  `id` int NOT NULL,
  `judul` varchar(255) NOT NULL,
  `konten` text NOT NULL,
  `tipe` varchar(50) DEFAULT NULL,
  `versi` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT (now())
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `syarat_ketentuan`
--

INSERT INTO `syarat_ketentuan` (`id`, `judul`, `konten`, `tipe`, `versi`, `created_at`) VALUES
(1, 'UPDATE FITUR DATA TEKNIS', 'TEST', 'Pembaruan', 'v2.1.1', '2025-08-18 20:44:32'),
(2, 'KETENTUAN', 'KETENTUANN', 'Ketentuan', NULL, '2025-08-18 21:00:35');

-- --------------------------------------------------------

--
-- Table structure for table `system_settings`
--

CREATE TABLE `system_settings` (
  `id` int NOT NULL,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `system_settings`
--

INSERT INTO `system_settings` (`id`, `setting_key`, `setting_value`) VALUES
(1, 'maintenance_mode', 'false|Sistem dalam kondisi Maintenance.');

-- --------------------------------------------------------

--
-- Table structure for table `token_blacklist`
--

CREATE TABLE `token_blacklist` (
  `id` bigint NOT NULL,
  `jti` varchar(36) NOT NULL,
  `user_id` bigint NOT NULL,
  `token_type` varchar(50) NOT NULL,
  `expires_at` datetime NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `revoked` tinyint(1) NOT NULL,
  `revoked_at` datetime DEFAULT NULL,
  `revoked_reason` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `token_blacklist`
--

INSERT INTO `token_blacklist` (`id`, `jti`, `user_id`, `token_type`, `expires_at`, `created_at`, `revoked`, `revoked_at`, `revoked_reason`) VALUES
(1, 'd15d2586-3eff-4986-9794-6b1512c9d7b6', 4, 'Refresh', '2025-09-28 22:30:52', '2025-09-21 22:36:05', 1, '2025-09-21 15:36:06', 'User logout'),
(2, '863810ca-6b87-4931-9c52-afb1bcd23785', 4, 'Refresh', '2025-09-28 22:36:37', '2025-09-21 22:39:11', 1, '2025-09-21 15:39:11', 'User logout'),
(3, 'cf6eb975-8078-4e5f-a745-753bb62c80da', 4, 'Refresh', '2025-09-28 22:39:18', '2025-09-21 23:06:20', 1, '2025-09-21 16:06:20', 'User logout'),
(4, 'c2684286-8a90-4dc0-a58c-8108f224c975', 4, 'Refresh', '2025-09-28 23:06:22', '2025-09-22 09:00:48', 1, '2025-09-22 02:00:49', 'Token refreshed - old token invalidated'),
(5, '2a9f4359-1649-4d95-9240-25bf3a77c465', 7, 'Refresh', '2025-09-29 09:17:08', '2025-09-22 09:24:08', 1, '2025-09-22 02:24:09', 'User logout'),
(6, 'c7871736-3f36-4bf9-bf5e-1551a1dc4854', 6, 'Refresh', '2025-09-29 09:16:28', '2025-09-22 09:39:44', 1, '2025-09-22 02:39:45', 'User logout'),
(7, '3a67ac65-dd69-4f02-a961-59c1fc742e98', 4, 'Refresh', '2025-09-29 09:00:48', '2025-09-22 11:00:26', 1, '2025-09-22 04:00:26', 'Token refreshed - old token invalidated'),
(8, 'a3fab5f6-fae1-41bb-a632-b562039d1be2', 4, 'Refresh', '2025-09-29 11:00:26', '2025-09-22 11:00:40', 1, '2025-09-22 04:00:41', 'User logout'),
(9, '7a3ce261-b907-4393-a7e4-24ec3f200127', 4, 'Refresh', '2025-09-29 11:00:47', '2025-09-22 11:32:27', 1, '2025-09-22 04:32:28', 'Token refreshed - old token invalidated'),
(10, 'e7b36e28-096f-45db-b4d3-092e5fdcaa9e', 4, 'Refresh', '2025-09-29 11:42:39', '2025-09-22 13:32:37', 1, '2025-09-22 06:32:38', 'Token refreshed - old token invalidated'),
(11, '6123c784-40cb-418b-a6ec-fe96fbe83a60', 4, 'Refresh', '2025-09-29 13:32:37', '2025-09-22 13:40:47', 1, '2025-09-22 06:40:48', 'User logout'),
(13, 'd14a3464-b21a-48ad-8068-be021fbadd89', 4, 'Refresh', '2025-09-29 13:40:53', '2025-09-22 14:25:24', 1, '2025-09-22 07:25:24', 'Token refreshed - old token invalidated'),
(14, '42e0217c-cdb6-400d-a9ba-20e6dbdad486', 4, 'Refresh', '2025-09-29 14:25:24', '2025-09-22 14:26:04', 1, '2025-09-22 07:26:05', 'User logout'),
(15, 'cca94803-908f-48dd-a7ff-2e89ef02535b', 4, 'Refresh', '2025-09-29 14:26:06', '2025-09-22 14:50:48', 1, '2025-09-22 07:50:48', 'User logout'),
(16, 'cf8c93d7-ee8a-4078-a784-493812d28f2d', 4, 'Refresh', '2025-09-29 14:50:52', '2025-09-22 17:16:04', 1, '2025-09-22 10:16:05', 'User logout'),
(17, 'fd96f8f5-8058-4f53-8fdc-cb9a2c062d02', 4, 'Refresh', '2025-09-29 17:29:16', '2025-09-22 17:29:16', 1, '2025-09-22 10:29:17', 'User logout'),
(18, 'fc4918e0-2960-49a9-b644-e57a35045617', 4, 'Refresh', '2025-09-29 17:31:38', '2025-09-22 17:31:38', 1, '2025-09-22 10:31:39', 'User logout'),
(19, '2b521f64-e883-4382-8df5-d5a2bf7311ce', 4, 'Refresh', '2025-09-29 17:32:14', '2025-09-22 17:32:15', 1, '2025-09-22 10:32:15', 'User logout'),
(20, 'f564634d-d50c-4442-ac77-237268f51c93', 4, 'Refresh', '2025-09-29 17:33:23', '2025-09-22 17:33:23', 1, '2025-09-22 10:33:24', 'User logout'),
(21, '069d814d-4b23-4dc9-a825-b6ec319622ad', 4, 'Refresh', '2025-09-29 19:24:33', '2025-09-22 19:24:33', 1, '2025-09-22 12:24:33', 'User logout'),
(22, '14301f4b-4c4d-4ff0-bbe2-77ee96452abc', 4, 'Refresh', '2025-09-29 19:33:52', '2025-09-22 19:33:53', 1, '2025-09-22 12:33:53', 'User logout'),
(23, '6abc8531-3de6-4743-8d14-89774214c4ba', 4, 'Refresh', '2025-09-29 19:36:50', '2025-09-22 21:11:36', 1, '2025-09-22 14:11:36', 'User logout'),
(24, '2b707d5f-f6bc-45fd-aa52-c93e60967783', 4, 'Refresh', '2025-09-29 21:11:45', '2025-09-22 21:11:49', 1, '2025-09-22 14:11:49', 'User logout'),
(25, '2d6c41bc-3ad5-4e87-8ee5-4ae797d5c5fb', 4, 'Refresh', '2025-10-02 10:16:23', '2025-09-25 12:24:21', 1, '2025-09-25 05:24:22', 'User logout'),
(27, 'f80e9fcc-45ee-4975-a2cb-d12884ab2039', 4, 'Refresh', '2025-10-02 19:58:25', '2025-09-27 00:42:13', 1, '2025-09-26 17:42:14', 'User logout'),
(29, 'f9ed1687-42a7-408f-91bb-57aca4783ab3', 4, 'Refresh', '2025-10-04 00:42:24', '2025-09-27 01:28:06', 1, '2025-09-26 18:28:06', 'User logout'),
(30, '4908299f-89a2-4b9e-b96f-9b9490f7082c', 4, 'Refresh', '2025-10-04 10:19:42', '2025-09-27 11:46:31', 1, '2025-09-27 04:46:32', 'User logout'),
(31, 'e63a67d6-be42-44c3-8755-083804556676', 4, 'Refresh', '2025-10-04 16:01:13', '2025-09-27 18:48:21', 1, '2025-09-27 11:48:22', 'User logout'),
(33, 'a0600fd0-608f-4c62-869a-b5b26d144172', 4, 'Refresh', '2025-10-04 18:48:24', '2025-09-28 20:14:23', 1, '2025-09-28 13:14:23', 'User logout'),
(35, 'e7723187-4cf7-4d99-896b-05795dc2605b', 4, 'Refresh', '2025-10-05 20:14:26', '2025-09-28 20:25:49', 1, '2025-09-28 13:25:49', 'User logout'),
(36, 'e16aba55-27c1-4a88-951d-cf5bb076e4d6', 4, 'Refresh', '2025-10-06 09:05:01', '2025-09-29 10:57:55', 1, '2025-09-29 03:57:55', 'User logout'),
(37, '5c7e7d79-4f05-4ec9-9530-e078ddbc3c1a', 4, 'Refresh', '2025-10-06 10:58:05', '2025-09-29 13:29:29', 1, '2025-09-29 06:29:30', 'User logout'),
(38, '6cc2dbd4-394a-4c9b-b59c-2f2e32449af2', 4, 'Refresh', '2025-10-06 13:29:36', '2025-09-29 15:00:17', 1, '2025-09-29 08:00:18', 'User logout'),
(39, '4b9eb771-a454-4665-b094-6dd2296a3dec', 4, 'Refresh', '2025-10-06 19:36:03', '2025-09-30 09:14:50', 1, '2025-09-30 02:14:51', 'User logout'),
(40, 'e809e782-3b88-4ce9-9e91-3523378902d0', 4, 'Refresh', '2025-10-07 09:15:00', '2025-09-30 09:22:39', 1, '2025-09-30 02:22:39', 'User logout'),
(41, 'ab685a83-2433-48a6-8ccd-a44b2aee472c', 4, 'Refresh', '2025-10-07 09:41:29', '2025-09-30 09:43:24', 1, '2025-09-30 02:43:24', 'User logout'),
(42, '890f07a2-5cd7-429a-826b-a55998d4b6bb', 4, 'Refresh', '2025-10-11 15:51:42', '2025-10-04 15:54:15', 1, '2025-10-04 08:54:15', 'User logout'),
(43, '7b67fd8d-53de-415d-8772-383a78998ebe', 4, 'Refresh', '2025-10-11 16:36:51', '2025-10-04 16:37:11', 1, '2025-10-04 09:37:11', 'User logout'),
(44, '6c95cce0-7865-42ed-8c59-0e960e0d6de4', 4, 'Refresh', '2025-10-11 16:46:01', '2025-10-04 17:34:13', 1, '2025-10-04 10:34:14', 'User logout'),
(45, '5209da4c-93cd-4c66-b7d3-889841b79c89', 4, 'Refresh', '2025-10-11 17:49:32', '2025-10-04 17:50:54', 1, '2025-10-04 10:50:55', 'User logout'),
(46, 'f0437d9e-3b16-4ffa-be78-c04985a6ad0a', 4, 'Refresh', '2025-10-11 19:11:24', '2025-10-04 19:30:44', 1, '2025-10-04 12:30:44', 'User logout'),
(47, '8d4bc4b8-4c86-4e73-9e92-003f66870d7a', 4, 'Refresh', '2025-10-11 19:30:50', '2025-10-04 19:34:01', 1, '2025-10-04 12:34:02', 'User logout'),
(48, 'eb680de1-18fc-46bb-aa13-8a2d71814535', 4, 'Refresh', '2025-10-11 19:34:51', '2025-10-04 21:18:40', 1, '2025-10-04 14:18:41', 'User logout'),
(49, '5c55dd74-7920-497f-bfc4-7826586712ca', 4, 'Refresh', '2025-10-11 21:18:42', '2025-10-04 22:23:43', 1, '2025-10-04 15:23:44', 'User logout'),
(50, 'a6cb9a45-8f51-41e0-a13b-533a7daac7c8', 4, 'Refresh', '2025-10-11 22:23:46', '2025-10-04 22:34:54', 1, '2025-10-04 15:34:55', 'User logout'),
(51, 'fdc9cbbc-c96b-410a-826d-0d6a0d82aa79', 4, 'Refresh', '2025-10-12 09:46:32', '2025-10-05 10:40:37', 1, '2025-10-05 03:40:38', 'User logout'),
(52, '4d92881a-50d4-41a5-be95-852f58acd2ac', 4, 'Refresh', '2025-10-12 14:48:42', '2025-10-05 15:07:52', 1, '2025-10-05 08:07:52', 'User logout'),
(53, '72c7c171-b6c0-4c9d-ae25-7d10c410bf5d', 4, 'Refresh', '2025-10-12 15:09:47', '2025-10-05 15:59:17', 1, '2025-10-05 08:59:18', 'User logout'),
(54, 'e35eac5d-c8a0-4919-a2d0-30fe1a71f18d', 4, 'Refresh', '2025-10-12 15:59:20', '2025-10-05 16:13:14', 1, '2025-10-05 09:13:14', 'User logout'),
(55, '53780c4f-e4ff-460a-a120-6f781045f4d2', 4, 'Refresh', '2025-10-12 19:20:56', '2025-10-05 20:45:31', 1, '2025-10-05 13:45:31', 'User logout'),
(56, '2f523b14-6991-45ca-97a1-5cdc47c758da', 4, 'Refresh', '2025-10-12 21:18:03', '2025-10-05 21:37:10', 1, '2025-10-05 14:37:11', 'User logout'),
(57, '1d1762af-9c70-4f9c-af7f-368f59c09f0d', 4, 'Refresh', '2025-10-13 09:51:35', '2025-10-06 09:51:49', 1, '2025-10-06 02:51:49', 'User logout'),
(58, 'e1f552a3-7205-4be7-9587-e1630466013b', 4, 'Refresh', '2025-10-13 09:52:07', '2025-10-06 09:55:36', 1, '2025-10-06 02:55:37', 'User logout'),
(59, '40b2bf79-fff7-449e-9ab1-360e24f96581', 4, 'Refresh', '2025-10-13 10:44:46', '2025-10-06 10:48:54', 1, '2025-10-06 03:48:55', 'User logout'),
(60, '15d6a78a-96fb-4f02-a3d7-e0339e627129', 4, 'Refresh', '2025-10-13 19:37:53', '2025-10-06 19:49:29', 1, '2025-10-06 12:49:29', 'User logout'),
(61, '11ef4610-417a-4022-96d1-d68316023797', 4, 'Refresh', '2025-10-13 19:49:31', '2025-10-06 19:51:09', 1, '2025-10-06 12:51:09', 'User logout'),
(62, '08112946-f461-4891-b197-dccce563b6e2', 4, 'Refresh', '2025-10-13 20:03:44', '2025-10-06 20:08:18', 1, '2025-10-06 13:08:19', 'User logout'),
(63, 'e3173773-811b-4e94-89ec-e8646fadf32e', 4, 'Refresh', '2025-10-13 20:16:20', '2025-10-06 20:33:43', 1, '2025-10-06 13:33:44', 'User logout'),
(64, 'b17b8015-2716-4812-b4df-be61b2ed1fdd', 4, 'Refresh', '2025-10-13 20:33:47', '2025-10-06 20:34:45', 1, '2025-10-06 13:34:46', 'User logout'),
(65, '4a86175b-dd5e-4a2d-b927-3879a2201535', 8, 'Refresh', '2025-10-13 20:34:59', '2025-10-06 20:35:01', 1, '2025-10-06 13:35:02', 'User logout'),
(66, 'd34d1768-7c05-4c7b-96f9-d7fcc8ab0110', 4, 'Refresh', '2025-10-13 21:01:13', '2025-10-07 10:02:04', 1, '2025-10-07 03:02:05', 'User logout'),
(67, '64934207-d98c-43e2-b7af-b9ab8b7509a2', 4, 'Refresh', '2025-10-15 09:29:22', '2025-10-08 09:29:30', 1, '2025-10-08 02:29:30', 'User logout'),
(68, 'bce0a6d0-e466-4920-83a5-3ef7b58e281a', 4, 'Refresh', '2025-10-15 09:29:43', '2025-10-08 09:56:57', 1, '2025-10-08 02:56:58', 'User logout'),
(69, 'd12d4fc8-ff6f-4687-bf27-b1ed45594624', 4, 'Refresh', '2025-10-15 09:57:11', '2025-10-08 10:06:18', 1, '2025-10-08 03:06:19', 'User logout'),
(70, 'ebd4eda4-b488-4d6c-9600-3a1025b137dd', 4, 'Refresh', '2025-10-15 12:11:17', '2025-10-08 14:21:49', 1, '2025-10-08 07:21:49', 'User logout');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` bigint NOT NULL,
  `name` varchar(191) NOT NULL,
  `email` varchar(191) NOT NULL,
  `email_verified_at` timestamp NULL DEFAULT NULL,
  `password` varchar(191) NOT NULL,
  `remember_token` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `role_id` bigint DEFAULT NULL,
  `revoked_before` datetime DEFAULT NULL,
  `password_changed_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `email_verified_at`, `password`, `remember_token`, `created_at`, `updated_at`, `role_id`, `revoked_before`, `password_changed_at`, `is_active`) VALUES
(4, 'Ahmad', 'ahmad@ajnusa.com', NULL, '$2b$12$nTuJEXJ4114sbltYKFLrievZJfqGLUgrFnTlUYpCqWLDWdrOtSxRm', NULL, '2025-07-20 11:56:17', '2025-07-20 11:56:17', 2, NULL, NULL, 1),
(5, 'Abbas', 'abbas@ajnusa.com', NULL, '$2b$12$Rt9DvhmacupMVDoXt1A9PeoVMbg5jixUIvTFftDCkg49wLKQapbLi', NULL, '2025-07-20 12:33:08', '2025-09-03 13:59:05', 9, NULL, NULL, 1),
(6, 'Adolf', 'adolf@ajnusa.com', NULL, '$2b$12$471CKrySK.ZXIHCwDcm4FuTVGhHhenSo9WaOu3dTrrbEFrOwn5yNy', NULL, '2025-08-27 11:50:48', '2025-08-27 11:50:48', 6, NULL, NULL, 1),
(7, 'Deni', 'coba@coba.com', NULL, '$2b$12$tJKtQGLl92lslHqht/XMhuoIsJDc3e2sQOMULFOd/N5woINYHG/FC', NULL, '2025-09-20 23:54:28', '2025-09-20 23:54:28', 8, NULL, NULL, 1),
(8, 'Komar', 'komar@aj.com', NULL, 'gAAAAABo48VuAgTB0_BPi1y2eyPAT0j1NO4J7klbX3cHbqJmhnXsSlUU_m7flQybRTbCIqZhTbSBc_Ewtzk0PwPxVmihdK3XQ9SYuHT5BNJ9Xm4Z0L6Kp34yJhEnmUqFQmBT5moiBUY7mouiFdmv9lt0qjkCrR97_w==', NULL, '2025-10-06 20:34:38', '2025-10-06 20:34:38', 6, NULL, '2025-10-06 13:34:38', 1);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `ix_activity_logs_id` (`id`);

--
-- Indexes for table `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Indexes for table `data_teknis`
--
ALTER TABLE `data_teknis`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_data_teknis_pelanggan_id` (`pelanggan_id`),
  ADD KEY `ix_data_teknis_id` (`id`),
  ADD KEY `ix_data_teknis_id_pelanggan` (`id_pelanggan`),
  ADD KEY `ix_data_teknis_ip_pelanggan` (`ip_pelanggan`),
  ADD KEY `ix_data_teknis_olt` (`olt`),
  ADD KEY `ix_data_teknis_sn` (`sn`),
  ADD KEY `idx_datateknis_customer_network` (`pelanggan_id`,`ip_pelanggan`),
  ADD KEY `idx_datateknis_ip_pelanggan` (`ip_pelanggan`),
  ADD KEY `idx_datateknis_mikrotik_vlan` (`mikrotik_server_id`,`id_vlan`),
  ADD KEY `idx_datateknis_password_pppoe` (`password_pppoe`),
  ADD KEY `idx_datateknis_pelanggan_id` (`pelanggan_id`),
  ADD KEY `idx_datateknis_sync_pending` (`mikrotik_sync_pending`),
  ADD KEY `idx_datateknis_sync_status` (`mikrotik_sync_pending`,`pelanggan_id`),
  ADD KEY `ix_data_teknis_id_vlan` (`id_vlan`),
  ADD KEY `ix_data_teknis_mikrotik_server_id` (`mikrotik_server_id`),
  ADD KEY `ix_data_teknis_mikrotik_sync_pending` (`mikrotik_sync_pending`),
  ADD KEY `ix_data_teknis_odc` (`odc`),
  ADD KEY `ix_data_teknis_odp_id` (`odp_id`),
  ADD KEY `ix_data_teknis_olt_custom` (`olt_custom`),
  ADD KEY `ix_data_teknis_onu_power` (`onu_power`),
  ADD KEY `ix_data_teknis_otb` (`otb`),
  ADD KEY `ix_data_teknis_password_pppoe` (`password_pppoe`),
  ADD KEY `ix_data_teknis_pon` (`pon`),
  ADD KEY `ix_data_teknis_port_odp` (`port_odp`),
  ADD KEY `ix_data_teknis_profile_pppoe` (`profile_pppoe`),
  ADD KEY `ix_data_teknis_speedtest_proof` (`speedtest_proof`),
  ADD KEY `idx_datateknis_odp_location` (`odp_id`,`port_odp`),
  ADD KEY `idx_datateknis_olt_port` (`olt`,`pon`),
  ADD KEY `idx_datateknis_onu_status` (`onu_power`,`mikrotik_sync_pending`),
  ADD KEY `idx_datateknis_pppoe_credentials` (`id_pelanggan`,`password_pppoe`);

--
-- Indexes for table `harga_layanan`
--
ALTER TABLE `harga_layanan`
  ADD PRIMARY KEY (`id_brand`);

--
-- Indexes for table `inventory_history`
--
ALTER TABLE `inventory_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `item_id` (`item_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `inventory_items`
--
ALTER TABLE `inventory_items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_inventory_items_serial_number` (`serial_number`),
  ADD UNIQUE KEY `mac_address` (`mac_address`),
  ADD KEY `item_type_id` (`item_type_id`),
  ADD KEY `pelanggan_id` (`pelanggan_id`),
  ADD KEY `status_id` (`status_id`);

--
-- Indexes for table `inventory_item_types`
--
ALTER TABLE `inventory_item_types`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_inventory_item_types_name` (`name`);

--
-- Indexes for table `inventory_statuses`
--
ALTER TABLE `inventory_statuses`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_inventory_statuses_name` (`name`);

--
-- Indexes for table `invoices`
--
ALTER TABLE `invoices`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_invoices_invoice_number` (`invoice_number`),
  ADD KEY `ix_invoices_pelanggan_id` (`pelanggan_id`),
  ADD KEY `idx_invoice_late_payment` (`paid_at`,`tgl_jatuh_tempo`),
  ADD KEY `idx_invoice_brand_revenue` (`brand`,`tgl_invoice`,`total_harga`),
  ADD KEY `idx_invoice_customer_status` (`pelanggan_id`,`status_invoice`),
  ADD KEY `idx_invoice_date_range` (`tgl_invoice`,`tgl_jatuh_tempo`),
  ADD KEY `idx_invoice_number_lookup` (`invoice_number`,`status_invoice`),
  ADD KEY `idx_invoice_payment_method` (`metode_pembayaran`,`status_invoice`),
  ADD KEY `idx_invoice_payment_tracking` (`status_invoice`,`paid_at`),
  ADD KEY `idx_invoice_revenue_analysis` (`status_invoice`,`tgl_invoice`,`total_harga`),
  ADD KEY `idx_invoice_status_brand` (`status_invoice`,`brand`),
  ADD KEY `idx_invoice_xendit_lookup` (`xendit_id`,`status_invoice`),
  ADD KEY `ix_invoices_id` (`id`);

--
-- Indexes for table `langganan`
--
ALTER TABLE `langganan`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_langganan_pelanggan_id` (`pelanggan_id`),
  ADD KEY `ix_langganan_status` (`status`),
  ADD KEY `ix_langganan_tgl_jatuh_tempo` (`tgl_jatuh_tempo`),
  ADD KEY `idx_langganan_revenue_tracking` (`status`,`harga_awal`,`tgl_jatuh_tempo`),
  ADD KEY `idx_langganan_package_customer` (`paket_layanan_id`,`pelanggan_id`,`status`),
  ADD KEY `idx_langganan_active_subscriptions` (`status`,`paket_layanan_id`),
  ADD KEY `idx_langganan_customer_package` (`pelanggan_id`,`paket_layanan_id`,`status`),
  ADD KEY `idx_langganan_customer_status` (`pelanggan_id`,`status`),
  ADD KEY `idx_langganan_due_date` (`status`,`tgl_jatuh_tempo`),
  ADD KEY `idx_langganan_package_status` (`paket_layanan_id`,`status`),
  ADD KEY `idx_langganan_payment_analysis` (`metode_pembayaran`,`status`,`tgl_jatuh_tempo`),
  ADD KEY `idx_langganan_subscription_dates` (`tgl_mulai_langganan`,`tgl_jatuh_tempo`,`tgl_berhenti`),
  ADD KEY `ix_langganan_created_at` (`created_at`),
  ADD KEY `ix_langganan_harga_awal` (`harga_awal`),
  ADD KEY `ix_langganan_id` (`id`),
  ADD KEY `ix_langganan_metode_pembayaran` (`metode_pembayaran`),
  ADD KEY `ix_langganan_paket_layanan_id` (`paket_layanan_id`),
  ADD KEY `ix_langganan_tgl_berhenti` (`tgl_berhenti`),
  ADD KEY `ix_langganan_tgl_invoice_terakhir` (`tgl_invoice_terakhir`),
  ADD KEY `ix_langganan_tgl_mulai_langganan` (`tgl_mulai_langganan`),
  ADD KEY `ix_langganan_updated_at` (`updated_at`);

--
-- Indexes for table `mikrotik_servers`
--
ALTER TABLE `mikrotik_servers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_mikrotik_servers_name` (`name`),
  ADD KEY `ix_mikrotik_servers_host_ip` (`host_ip`),
  ADD KEY `ix_mikrotik_servers_is_active` (`is_active`),
  ADD KEY `ix_mikrotik_servers_last_connection_status` (`last_connection_status`),
  ADD KEY `idx_mikrotik_active_host` (`is_active`,`host_ip`),
  ADD KEY `idx_mikrotik_active_status` (`is_active`,`last_connection_status`),
  ADD KEY `idx_mikrotik_host_name` (`host_ip`,`name`),
  ADD KEY `idx_mikrotik_is_active` (`is_active`),
  ADD KEY `idx_mikrotik_last_connected_at` (`last_connected_at`),
  ADD KEY `idx_mikrotik_last_connection_status` (`last_connection_status`),
  ADD KEY `idx_mikrotik_ros_version` (`ros_version`),
  ADD KEY `ix_mikrotik_servers_created_at` (`created_at`),
  ADD KEY `ix_mikrotik_servers_id` (`id`),
  ADD KEY `ix_mikrotik_servers_last_connected_at` (`last_connected_at`),
  ADD KEY `ix_mikrotik_servers_port` (`port`),
  ADD KEY `ix_mikrotik_servers_ros_version` (`ros_version`),
  ADD KEY `ix_mikrotik_servers_updated_at` (`updated_at`),
  ADD KEY `ix_mikrotik_servers_username` (`username`);

--
-- Indexes for table `odp`
--
ALTER TABLE `odp`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `kode_odp` (`kode_odp`),
  ADD KEY `olt_id` (`olt_id`),
  ADD KEY `ix_odp_id` (`id`),
  ADD KEY `fk_odp_parent_odp_id_odp` (`parent_odp_id`);

--
-- Indexes for table `olt`
--
ALTER TABLE `olt`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ip_address` (`ip_address`),
  ADD UNIQUE KEY `nama_olt` (`nama_olt`),
  ADD KEY `ix_olt_id` (`id`),
  ADD KEY `mikrotik_server_id` (`mikrotik_server_id`);

--
-- Indexes for table `paket_layanan`
--
ALTER TABLE `paket_layanan`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_brand` (`id_brand`);

--
-- Indexes for table `payment_callback_logs`
--
ALTER TABLE `payment_callback_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_callback_log_xendit_id` (`xendit_id`),
  ADD KEY `ix_payment_callback_logs_id` (`id`),
  ADD KEY `ix_payment_callback_logs_xendit_id` (`xendit_id`),
  ADD KEY `idx_callback_log_external_id` (`external_id`),
  ADD KEY `ix_payment_callback_logs_external_id` (`external_id`),
  ADD KEY `ix_payment_callback_logs_idempotency_key` (`idempotency_key`),
  ADD KEY `idx_callback_log_idempotency_key` (`idempotency_key`),
  ADD KEY `idx_callback_log_status` (`status`);

--
-- Indexes for table `pelanggan`
--
ALTER TABLE `pelanggan`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_pelanggan_email` (`email`),
  ADD KEY `ix_pelanggan_id` (`id`),
  ADD KEY `mikrotik_server_id` (`mikrotik_server_id`),
  ADD KEY `idx_pelanggan_brand_count` (`id_brand`,`nama`),
  ADD KEY `idx_pelanggan_brand_location` (`id_brand`,`alamat`),
  ADD KEY `idx_pelanggan_blok_unit` (`blok`,`unit`),
  ADD KEY `idx_pelanggan_brand_status` (`id_brand`,`layanan`),
  ADD KEY `idx_pelanggan_installation_trends` (`tgl_instalasi`,`id_brand`),
  ADD KEY `idx_pelanggan_ktp_email` (`no_ktp`,`email`),
  ADD KEY `idx_pelanggan_nama_alamat` (`nama`,`alamat`);

--
-- Indexes for table `permissions`
--
ALTER TABLE `permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `ix_roles_id` (`id`);

--
-- Indexes for table `role_has_permissions`
--
ALTER TABLE `role_has_permissions`
  ADD PRIMARY KEY (`permission_id`,`role_id`),
  ADD KEY `role_id` (`role_id`);

--
-- Indexes for table `syarat_ketentuan`
--
ALTER TABLE `syarat_ketentuan`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_syarat_ketentuan_id` (`id`);

--
-- Indexes for table `system_settings`
--
ALTER TABLE `system_settings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_system_settings_setting_key` (`setting_key`);

--
-- Indexes for table `token_blacklist`
--
ALTER TABLE `token_blacklist`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_token_blacklist_jti` (`jti`),
  ADD KEY `ix_token_blacklist_created_at` (`created_at`),
  ADD KEY `ix_token_blacklist_revoked_at` (`revoked_at`),
  ADD KEY `idx_token_blacklist_user_id` (`user_id`),
  ADD KEY `idx_token_blacklist_created_at` (`created_at`),
  ADD KEY `ix_token_blacklist_revoked_reason` (`revoked_reason`),
  ADD KEY `idx_token_blacklist_token_type` (`token_type`),
  ADD KEY `idx_token_blacklist_revoked` (`revoked`),
  ADD KEY `ix_token_blacklist_id` (`id`),
  ADD KEY `idx_token_blacklist_revoked_at` (`revoked_at`),
  ADD KEY `idx_token_blacklist_user_type` (`user_id`,`token_type`),
  ADD KEY `idx_token_blacklist_jti` (`jti`),
  ADD KEY `ix_token_blacklist_revoked` (`revoked`),
  ADD KEY `idx_token_blacklist_expires_at` (`expires_at`),
  ADD KEY `idx_token_blacklist_expires_revoked` (`expires_at`,`revoked`),
  ADD KEY `idx_token_blacklist_created_revoked` (`created_at`,`revoked`),
  ADD KEY `idx_token_blacklist_user_expires` (`user_id`,`expires_at`),
  ADD KEY `idx_token_blacklist_type_revoked` (`token_type`,`revoked`),
  ADD KEY `ix_token_blacklist_user_id` (`user_id`),
  ADD KEY `idx_token_blacklist_jti_revoked` (`jti`,`revoked`),
  ADD KEY `ix_token_blacklist_token_type` (`token_type`),
  ADD KEY `ix_token_blacklist_expires_at` (`expires_at`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_users_email` (`email`),
  ADD KEY `role_id` (`role_id`),
  ADD KEY `ix_users_id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=307;

--
-- AUTO_INCREMENT for table `data_teknis`
--
ALTER TABLE `data_teknis`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=80;

--
-- AUTO_INCREMENT for table `inventory_history`
--
ALTER TABLE `inventory_history`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `inventory_items`
--
ALTER TABLE `inventory_items`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `inventory_item_types`
--
ALTER TABLE `inventory_item_types`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `inventory_statuses`
--
ALTER TABLE `inventory_statuses`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `invoices`
--
ALTER TABLE `invoices`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=31;

--
-- AUTO_INCREMENT for table `langganan`
--
ALTER TABLE `langganan`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=82;

--
-- AUTO_INCREMENT for table `mikrotik_servers`
--
ALTER TABLE `mikrotik_servers`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `odp`
--
ALTER TABLE `odp`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `olt`
--
ALTER TABLE `olt`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `paket_layanan`
--
ALTER TABLE `paket_layanan`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `payment_callback_logs`
--
ALTER TABLE `payment_callback_logs`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `pelanggan`
--
ALTER TABLE `pelanggan`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=227;

--
-- AUTO_INCREMENT for table `permissions`
--
ALTER TABLE `permissions`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=105;

--
-- AUTO_INCREMENT for table `roles`
--
ALTER TABLE `roles`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `syarat_ketentuan`
--
ALTER TABLE `syarat_ketentuan`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `system_settings`
--
ALTER TABLE `system_settings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `token_blacklist`
--
ALTER TABLE `token_blacklist`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=71;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `data_teknis`
--
ALTER TABLE `data_teknis`
  ADD CONSTRAINT `data_teknis_ibfk_1` FOREIGN KEY (`pelanggan_id`) REFERENCES `pelanggan` (`id`),
  ADD CONSTRAINT `data_teknis_ibfk_2` FOREIGN KEY (`odp_id`) REFERENCES `odp` (`id`),
  ADD CONSTRAINT `fk_data_teknis_server` FOREIGN KEY (`mikrotik_server_id`) REFERENCES `mikrotik_servers` (`id`);

--
-- Constraints for table `inventory_history`
--
ALTER TABLE `inventory_history`
  ADD CONSTRAINT `inventory_history_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory_items` (`id`),
  ADD CONSTRAINT `inventory_history_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `inventory_items`
--
ALTER TABLE `inventory_items`
  ADD CONSTRAINT `inventory_items_ibfk_1` FOREIGN KEY (`item_type_id`) REFERENCES `inventory_item_types` (`id`),
  ADD CONSTRAINT `inventory_items_ibfk_2` FOREIGN KEY (`pelanggan_id`) REFERENCES `pelanggan` (`id`),
  ADD CONSTRAINT `inventory_items_ibfk_3` FOREIGN KEY (`status_id`) REFERENCES `inventory_statuses` (`id`);

--
-- Constraints for table `invoices`
--
ALTER TABLE `invoices`
  ADD CONSTRAINT `invoices_ibfk_1` FOREIGN KEY (`pelanggan_id`) REFERENCES `pelanggan` (`id`);

--
-- Constraints for table `langganan`
--
ALTER TABLE `langganan`
  ADD CONSTRAINT `langganan_ibfk_2` FOREIGN KEY (`paket_layanan_id`) REFERENCES `paket_layanan` (`id`),
  ADD CONSTRAINT `langganan_ibfk_3` FOREIGN KEY (`pelanggan_id`) REFERENCES `pelanggan` (`id`);

--
-- Constraints for table `odp`
--
ALTER TABLE `odp`
  ADD CONSTRAINT `fk_odp_parent_odp_id_odp` FOREIGN KEY (`parent_odp_id`) REFERENCES `odp` (`id`),
  ADD CONSTRAINT `odp_ibfk_1` FOREIGN KEY (`olt_id`) REFERENCES `olt` (`id`);

--
-- Constraints for table `olt`
--
ALTER TABLE `olt`
  ADD CONSTRAINT `olt_ibfk_1` FOREIGN KEY (`mikrotik_server_id`) REFERENCES `mikrotik_servers` (`id`);

--
-- Constraints for table `paket_layanan`
--
ALTER TABLE `paket_layanan`
  ADD CONSTRAINT `paket_layanan_ibfk_1` FOREIGN KEY (`id_brand`) REFERENCES `harga_layanan` (`id_brand`);

--
-- Constraints for table `pelanggan`
--
ALTER TABLE `pelanggan`
  ADD CONSTRAINT `pelanggan_ibfk_1` FOREIGN KEY (`id_brand`) REFERENCES `harga_layanan` (`id_brand`),
  ADD CONSTRAINT `pelanggan_ibfk_2` FOREIGN KEY (`mikrotik_server_id`) REFERENCES `mikrotik_servers` (`id`);

--
-- Constraints for table `role_has_permissions`
--
ALTER TABLE `role_has_permissions`
  ADD CONSTRAINT `role_has_permissions_ibfk_1` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`),
  ADD CONSTRAINT `role_has_permissions_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);

--
-- Constraints for table `token_blacklist`
--
ALTER TABLE `token_blacklist`
  ADD CONSTRAINT `token_blacklist_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
