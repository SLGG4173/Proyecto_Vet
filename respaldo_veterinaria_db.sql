-- MySQL dump 10.13  Distrib 9.1.0, for Win64 (x86_64)
--
-- Host: localhost    Database: veterinaria_db
-- ------------------------------------------------------
-- Server version	9.1.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('0177dec43b8b');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultas`
--

DROP TABLE IF EXISTS `consultas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_mascota` int DEFAULT NULL,
  `id_veterinario` int DEFAULT NULL,
  `fecha_hora` datetime NOT NULL,
  `motivo_consulta` text,
  `diagnostico` text,
  `tratamiento` text,
  `notas_adicionales` text,
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `estado_pago` varchar(50) NOT NULL DEFAULT 'Pendiente',
  PRIMARY KEY (`id`),
  KEY `id_mascota` (`id_mascota`),
  KEY `id_veterinario` (`id_veterinario`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultas`
--

LOCK TABLES `consultas` WRITE;
/*!40000 ALTER TABLE `consultas` DISABLE KEYS */;
INSERT INTO `consultas` VALUES (5,1,2,'2025-06-16 08:00:00','','Aun por ver','Profilaxis','','2025-06-11 20:35:35','Cancelado'),(6,1,1,'2025-06-16 08:00:00','Revisión Mensual','','','','2025-06-12 03:45:11','Pendiente'),(7,1,2,'2025-06-01 08:00:00','Quisquilloso para comer, rechazo a alimentos','Posible cambio en la comida','Volver a las comidas normales','Si sigue con problemas después de unos días volver a una cita','2025-06-12 03:58:54','Pagado');
/*!40000 ALTER TABLE `consultas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalleconsultaservicio`
--

DROP TABLE IF EXISTS `detalleconsultaservicio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalleconsultaservicio` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_consulta` int NOT NULL,
  `id_servicio` int NOT NULL,
  `cantidad` int NOT NULL DEFAULT '1',
  `precio_final_aplicado` decimal(10,2) NOT NULL,
  `descuento_aplicado` decimal(10,2) DEFAULT '0.00',
  `notas_servicio` text,
  PRIMARY KEY (`id`),
  KEY `id_servicio` (`id_servicio`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalleconsultaservicio`
--

LOCK TABLES `detalleconsultaservicio` WRITE;
/*!40000 ALTER TABLE `detalleconsultaservicio` DISABLE KEYS */;
INSERT INTO `detalleconsultaservicio` VALUES (1,5,1,1,15.00,0.00,''),(4,5,2,1,27.00,0.00,''),(5,6,1,1,15.00,0.00,''),(6,7,1,1,15.00,5.00,'Pequeño corte en la cola');
/*!40000 ALTER TABLE `detalleconsultaservicio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `duenos`
--

DROP TABLE IF EXISTS `duenos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `duenos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre_dueno` varchar(100) NOT NULL,
  `apellido_dueno` varchar(100) NOT NULL,
  `telefono_dueno` varchar(20) DEFAULT NULL,
  `email_dueno` varchar(100) DEFAULT NULL,
  `direccion_dueno` varchar(255) DEFAULT NULL,
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `password_hash` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_dueno` (`email_dueno`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `duenos`
--

LOCK TABLES `duenos` WRITE;
/*!40000 ALTER TABLE `duenos` DISABLE KEYS */;
INSERT INTO `duenos` VALUES (1,'sergio','garcia','0999999999','sgarciar4173@utm.edu.ec','calle 12','2025-05-26 02:48:28','scrypt:32768:8:1$P4Sv3PVxA2sFys9L$a2db463645003a1f7cc0e2f9ff81133dc51d9b5024562504a0cce6394dae6b3ac843e4518002e580b75fb4442536e5f7e08ca902e29b373c6cc7e7c755493d42');
/*!40000 ALTER TABLE `duenos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mascotas`
--

DROP TABLE IF EXISTS `mascotas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mascotas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre_mascota` varchar(100) NOT NULL,
  `especie` varchar(50) DEFAULT NULL,
  `raza` varchar(50) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `id_dueno` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_dueno` (`id_dueno`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mascotas`
--

LOCK TABLES `mascotas` WRITE;
/*!40000 ALTER TABLE `mascotas` DISABLE KEYS */;
INSERT INTO `mascotas` VALUES (1,'Taty','Gato','Siamés ','2025-05-22',1);
/*!40000 ALTER TABLE `mascotas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servicios`
--

DROP TABLE IF EXISTS `servicios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servicios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre_servicio` varchar(100) NOT NULL,
  `descripcion_servicio` text,
  `categoria` varchar(100) NOT NULL,
  `precio_base` decimal(10,2) NOT NULL DEFAULT '0.00',
  `duracion_estimada` int DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre_servicio` (`nombre_servicio`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servicios`
--

LOCK TABLES `servicios` WRITE;
/*!40000 ALTER TABLE `servicios` DISABLE KEYS */;
INSERT INTO `servicios` VALUES (1,'Profilaxis General','Prevención de enfermedades mediante la implementación de medidas oportunas','Prevención ',15.00,30,1,'2025-06-11 15:25:12'),(2,'V-Rabia','','Vacunas',45.00,5,1,'2025-06-11 17:04:27');
/*!40000 ALTER TABLE `servicios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `nombre_completo` varchar(150) DEFAULT NULL,
  `rol` enum('admin','veterinario','recepcionista') DEFAULT 'recepcionista',
  `is_active` tinyint(1) DEFAULT '1',
  `id_veterinario_profile` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `fk_usuario_veterinario` (`id_veterinario_profile`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Admin','scrypt:32768:8:1$q3gesNNMQZ9k7o2W$b5345dc3a8daa7f0bbfdbdc52c4b49d75d0c948aee766e4b20edc6e6337fae4bfe1ccb84c566bca15d7bc2097ec2b4837bfb38a7ce0aa380bb286ed67ccdb942','Administrador Principal','admin',1,NULL),(2,'Recepcionista','scrypt:32768:8:1$lHs0cUmBvxA9SL28$1abbdd55c957e593cb462be2b460ab7ee0c4de48259e0f9117630b5e9ee7201d7c4f2cd21d12a89601f701aa471e8ed2eae56b479c5fb4d3ad93e1c57cf1ca35','Ana Perez','recepcionista',1,NULL),(3,'drgonzalez','scrypt:32768:8:1$btbwiQxdfHdyINhh$e43015f369ff3f63e958c5c622e57c55416541fb63f53b88cf2d56d1e8643b140de4161b8407d2587e6b081b800f5f0f9729fa0c5ed6c7eaaa6808663f978690','Dr. Carlos Gonzalez','veterinario',1,NULL),(4,'Smartinelli','scrypt:32768:8:1$B4mSDwCzGekNIojE$d786325ad65323d1c3d90ddf9a52c363eb6785c2a9077859ef64c0e57c45df6690762b929818552246676d08b3487c6aeba670b9cc7d44c7dd25e169c5703d8c','Sandro Martinelli','veterinario',1,1),(5,'Ldonatti','scrypt:32768:8:1$CBEty4k7uBgmDwy6$b5d7668ef897b81b317c624d1a06adcab7f2052cf928d68920f0d7ce85258ddf2fd0f50e0fd539d8c18be5c8359ec0ad1b58ffbd853be8f1b9bb4207f1d49fc4','Lucas Donatti','veterinario',1,2);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `veterinarios`
--

DROP TABLE IF EXISTS `veterinarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `veterinarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre_veterinario` varchar(100) NOT NULL,
  `apellido_veterinario` varchar(100) NOT NULL,
  `telefono_veterinario` varchar(20) DEFAULT NULL,
  `email_veterinario` varchar(100) DEFAULT NULL,
  `licencia_veterinario` varchar(50) DEFAULT NULL,
  `fecha_contratacion` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_veterinario` (`email_veterinario`),
  UNIQUE KEY `uk_veterinario_licencia` (`licencia_veterinario`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `veterinarios`
--

LOCK TABLES `veterinarios` WRITE;
/*!40000 ALTER TABLE `veterinarios` DISABLE KEYS */;
INSERT INTO `veterinarios` VALUES (1,'Sandro','Martinelli','055568541','SMarti@gmail.com','136549465S','2025-05-01'),(2,'Lucas','Donatti','08954123','euler@gmail.com','4168wer','2025-05-01');
/*!40000 ALTER TABLE `veterinarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-11 21:43:55
