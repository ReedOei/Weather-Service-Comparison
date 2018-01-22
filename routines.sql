-- MySQL dump 10.13  Distrib 5.7.19, for Linux (x86_64)
--
-- Host: localhost    Database: Main
-- ------------------------------------------------------
-- Server version	5.7.19-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping routines for database 'Main'
--
/*!50003 DROP PROCEDURE IF EXISTS `usp_NoteInsert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`roei`@`%` PROCEDURE `usp_NoteInsert`(
	in content varchar(4000),
    in note_type varchar(100),
    in meta_field_1 varchar(1000),
    in meta_field_2 varchar(1000),
    in meta_field_3 varchar(1000),
    in meta_field_4 varchar(1000),
    in meta_field_5 varchar(1000),
    in meta_field_6 varchar(1000)
)
BEGIN
	set @note_type_id := -1;

    select @note_type_id := id
    from main_notetype
    where description = note_type;

    if @note_type_id = -1 then
		set @note_type_id = 2;
	end if;

	insert into main_note
    (
		active,
        date,
        content,
        meta_field_1,
        meta_field_2,
        meta_field_3,
        meta_field_4,
        meta_field_5,
        meta_field_6,
        note_type_id
    )
    values
    (
		1,
        now(),
        content,
        meta_field_1,
        meta_field_2,
        meta_field_3,
        meta_field_4,
        meta_field_5,
        meta_field_6,
        @note_type_id
    );
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherActualTemps` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `usp_WeatherActualTemps`(
	return_result bit,
    begin_time datetime,
    end_time datetime
)
BEGIN
    drop table if exists actual_temperatures;
    create temporary table actual_temperatures
    (
		prediction_time date,
        temperature_max float,
        temperature_min float,
        location_id int
    );

    insert into actual_temperatures
    (
		prediction_time,
        temperature_max,
        temperature_min,
        location_id
    )
    select date(WD.prediction_time),
			  max(WD.temperature),
              min(WD.temperature),
              location_id
    from weather_weatherdata as WD
        where (begin_time is null or WD.prediction_time >= begin_time) and
				   (end_time is null or WD.prediction_time <= end_time)
    group by date(WD.prediction_time), location_id;

    if return_result then
		select *
        from actual_temperatures
        order by prediction_time asc;
    end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherAggregateMethods` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`roei`@`%` PROCEDURE `usp_WeatherAggregateMethods`(
	service_id int,
    begin_time datetime,
    end_time datetime
)
BEGIN
	call usp_WeatherActualTemps(0, begin_time, end_time);

    drop table if exists avg_forecast_aggregate;
    create temporary table avg_forecast_aggregate
    (
		prediction_time date,
        temperature_max float,
        temperature_min float,
        precip_chance float,
        wind_speed float,
        wind_bearing float,
        humidity float,
        location_id int
    );

    call usp_WeatherForecastAggregate(service_id, 'avg', 0, begin_time, end_time);
    insert into avg_forecast_aggregate
    select * from aggregated_forecast;

    drop table if exists first_forecast_aggregate;
    create temporary table first_forecast_aggregate
    (
		prediction_time date,
        temperature_max float,
        temperature_min float,
        precip_chance float,
        wind_speed float,
        wind_bearing float,
        humidity float,
        location_id int
    );

    call usp_WeatherForecastAggregate(service_id, 'first', 0, begin_time, end_time);
    insert into first_forecast_aggregate
    select * from aggregated_forecast;

    drop table if exists last_forecast_aggregate;
    create temporary table last_forecast_aggregate
    (
		prediction_time date,
        temperature_max float,
        temperature_min float,
        precip_chance float,
        wind_speed float,
        wind_bearing float,
        humidity float,
        location_id int
    );

    call usp_WeatherForecastAggregate(service_id, 'last', 0, begin_time, end_time);
    insert into last_forecast_aggregate
    select * from aggregated_forecast;

    drop table if exists decay_forecast_aggregate;
    create temporary table decay_forecast_aggregate
    (
		prediction_time date,
        temperature_max float,
        temperature_min float,
        precip_chance float,
        wind_speed float,
        wind_bearing float,
        humidity float,
        location_id int
    );

    call usp_WeatherForecastAggregate(service_id, 'decay', 0, begin_time, end_time);
    insert into decay_forecast_aggregate
    select * from aggregated_forecast;

    select AT.prediction_time as prediction_time,
			  AT.temperature_max as actual_temp_max,
              AT.temperature_min as actual_temp_min,
              AVG.temperature_max as avg_temp_max,
              AVG.temperature_min as avg_temp_min,
              AVG.precip_chance as avg_precip_chance,
              FST.temperature_max as fst_temp_max,
              FST.temperature_min as fst_temp_min,
              FST.precip_chance as fst_precip_chance,
              LST.temperature_max as lst_temp_max,
              LST.temperature_min as lst_temp_min,
              LST.precip_chance as lst_precip_chance,
              DCY.temperature_max as dcy_temp_max,
              DCY.temperature_min as dcy_temp_min,
              DCY.precip_chance as dcy_precip_chance
    from actual_temperatures as AT
    inner join avg_forecast_aggregate as AVG on AT.prediction_time = AVG.prediction_time
    inner join first_forecast_aggregate as FST on AT.prediction_time = FST.prediction_time
    inner join last_forecast_aggregate as LST on AT.prediction_time = LST.prediction_time
    inner join decay_forecast_aggregate as DCY on AT.prediction_time = DCY.prediction_time
    order by prediction_time desc;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherDataInsert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`roei`@`%` PROCEDURE `usp_WeatherDataInsert`(
    in prediction_time datetime,
    in temperature float,
    in is_precip bit,
    in precip_type varchar(50),
    in wind_speed float,
    in wind_bearing float,
    in humidity float,
	in location_id int,
    in service_name varchar(100)
)
BEGIN
	start transaction;

    select @service_id := S.id
    from weather_weatherservice S
    where S.short_name = service_name;

    insert into weather_weatherdata
    (
		prediction_time,
        temperature,
        is_precip,
        precip_type,
        wind_speed,
        wind_bearing,
        humidity,
        location_id,
        service_id
    )
    values
    (
		prediction_time,
        temperature,
        is_precip,
        precip_type,
        wind_speed,
        wind_bearing,
        humidity,
        location_id,
        @service_id
    );

    commit;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherForecastAggregate` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `usp_WeatherForecastAggregate`(
	service_id int,
    method varchar(100),
    return_results bit,
    begin_time datetime,
    end_time datetime
)
BEGIN
	set service_id = ifnull(service_id, -1);

	drop table if exists aggregated_forecast;
	create temporary table aggregated_forecast
    (
		prediction_time date,
        temperature_max float,
        temperature_min float,
        precip_chance float,
        wind_speed float,
        wind_bearing float,
        humidity float,
        location_id int
    );

    if method = 'avg' then
		insert into aggregated_forecast
		(
			prediction_time,
			temperature_max,
			temperature_min,
			precip_chance,
			wind_speed,
			wind_bearing,
			humidity,
			location_id
		)
		select date(WF.prediction_time),
			      avg(WF.temperature_max),
                  avg(WF.temperature_min),
                  avg(WF.precip_chance),
                  avg(WF.wind_speed),
                  avg(WF.wind_bearing),
                  avg(WF.humidity),
                  location_id
		from weather_weatherforecast as WF
		where (service_id = -1 or WF.service_id = service_id)
		group by date(WF.prediction_time), location_id;
	elseif method = 'first' then
		insert into aggregated_forecast
		(
			prediction_time,
			temperature_max,
			temperature_min,
			precip_chance,
			wind_speed,
			wind_bearing,
			humidity,
			location_id
		)
		select date(WF.prediction_time),
				  max(WF.temperature_max),
				  max(WF.temperature_min),
				  max(WF.precip_chance),
				  max(WF.wind_speed),
				  max(WF.wind_bearing),
				  max(WF.humidity),
				  location_id
		from weather_weatherforecast as WF
		inner join
		(
			select date(WF.prediction_time) as prediction_time, min(WF.forecasted_time) as forecasted_time
			from weather_weatherforecast as WF
			where (service_id = -1 or WF.service_id = service_id)
			group by date(WF.prediction_time)
		) as D on D.forecasted_time = WF.forecasted_time and D.prediction_time = WF.prediction_time
		where (service_id = -1 or WF.service_id = service_id)
		group by date(WF.prediction_time), location_id;
	elseif method = 'last' then
		insert into aggregated_forecast
		(
			prediction_time,
			temperature_max,
			temperature_min,
			precip_chance,
			wind_speed,
			wind_bearing,
			humidity,
			location_id
		)
		select date(WF.prediction_time),
				  max(WF.temperature_max),
				  max(WF.temperature_min),
				  max(WF.precip_chance),
				  max(WF.wind_speed),
				  max(WF.wind_bearing),
				  max(WF.humidity),
				  location_id
		from weather_weatherforecast as WF
		inner join
		(
			select date(WF.prediction_time) as prediction_time, max(WF.forecasted_time) as forecasted_time
			from weather_weatherforecast as WF
			where (service_id = -1 or WF.service_id = service_id)
			group by date(WF.prediction_time)
		) as D on D.forecasted_time = WF.forecasted_time and D.prediction_time = WF.prediction_time
		where (service_id = -1 or WF.service_id = service_id)
		group by date(WF.prediction_time), location_id;
	elseif method = 'decay' then
		insert into aggregated_forecast
		(
			prediction_time,
			temperature_max,
			temperature_min,
			precip_chance,
			wind_speed,
			wind_bearing,
			humidity,
			location_id
		)
		select date(WF.prediction_time),
			      sum(WF.temperature_max * pow(1.05, timestampdiff(day, WF.prediction_time, WF.forecasted_time))) / max(M.mult),
                  sum(WF.temperature_min * pow(1.05, timestampdiff(day, WF.prediction_time, WF.forecasted_time))) / max(M.mult),
                  sum(WF.precip_chance * pow(1.05, timestampdiff(day, WF.prediction_time, WF.forecasted_time))) / max(M.mult),
                  avg(WF.wind_speed * pow(1.05, timestampdiff(day, WF.prediction_time, WF.forecasted_time))) / max(M.mult),
                  avg(WF.wind_bearing * pow(1.05, timestampdiff(day, WF.prediction_time, WF.forecasted_time))) / max(M.mult),
                  avg(WF.humidity * pow(1.05, timestampdiff(day, WF.prediction_time, WF.forecasted_time))) / max(M.mult),
                  location_id
		from weather_weatherforecast as WF
        inner join
        (
			select date(WF.prediction_time) as prediction_time,
					  sum(pow(1.05, timestampdiff(day, WF.prediction_time, WF.forecasted_time))) as mult
            from weather_weatherforecast as WF
			where (service_id = -1 or WF.service_id = service_id)
            group by date(WF.prediction_time)
        ) as M on M.prediction_time = date(WF.prediction_time)
		where (service_id = -1 or WF.service_id = service_id)
		group by date(WF.prediction_time), location_id;
    end if;

    if return_results then
		select *
		from aggregated_forecast
        where (begin_time is null or prediction_time >= begin_time) and
				   (end_time is null or prediction_time <= end_time)
		order by prediction_time asc;
	end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherForecastDailyInsert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`roei`@`%` PROCEDURE `usp_WeatherForecastDailyInsert`(
  forecasted_time datetime,
  prediction_time datetime,
  temperature_max float,
  temperature_min float,
  precip_chance float,
  precip_type varchar(50),
  wind_speed float,
  wind_bearing float,
  humidity float,
  location_id int,
  service_name varchar(100)
)
BEGIN
	start transaction;

    select @service_id := S.id
    from weather_weatherservice S
    where S.short_name = service_name;

    insert into weather_weatherforecast
    (
		forecasted_time,
	    prediction_time,
	    temperature_max,
	    temperature_min,
	    precip_chance,
	    precip_type,
		wind_speed,
	    wind_bearing,
	    humidity,
	    location_id,
	    service_id
    )
    values
    (
		forecasted_time,
	    prediction_time,
	    temperature_max,
	    temperature_min,
	    precip_chance,
	    precip_type,
		wind_speed,
	    wind_bearing,
	    humidity,
	    location_id,
	    @service_id
    );

    commit;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherForecastTempChart` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`roei`@`%` PROCEDURE `usp_WeatherForecastTempChart`(
	service_id int,
    method varchar(100),
    begin_time datetime,
    end_time datetime
)
BEGIN
	call usp_WeatherActualTemps(0, begin_time, end_time);
    call usp_WeatherForecastAggregate(service_id, method, 0, begin_time, end_time);

    select AT.prediction_time,
		      AT.temperature_max as actual_temp_max, AT.temperature_min as actual_temp_min,
              AF.temperature_max as prediction_temp_max, AF.temperature_min as prediction_temp_min
    from actual_temperatures as AT
    inner join aggregated_forecast as AF on AT.prediction_time = AF.prediction_time;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherLocationInfoGet` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `usp_WeatherLocationInfoGet`(
	in location_code varchar(100) -- The location code is cityname+countryname
)
BEGIN
	select id,
		   name,
           latitude,
           longitude,
           state_name,
           state_name_short,
           zip_code,
           country_name,
           country_name_short
    from weather_location
	where concat(replace(name, ' ', ''), ',', country_name_short) like location_code;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherLocationsGet` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `usp_WeatherLocationsGet`()
BEGIN
	select M.location_id,
		   concat(replace(L.name, ' ', ''), ',', L.country_name_short) as location_code,
		   S.short_name as service
    from weather_monitor M
    inner join weather_location L on M.location_id = L.id
    inner join weather_weatherservice S on M.service_id = S.id
    where M.active = 1;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherPrecipAccuracy` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `usp_WeatherPrecipAccuracy`(
    _service_id int
)
BEGIN
	drop table if exists ranges;
	create temporary table ranges ( i int, low float, high float);

	insert into ranges (i, low, high)
	values (0, 0, 0.10),
			   (1, 0.1, 0.20),
			   (2, 0.2, 0.30),
			   (3, 0.3, 0.40),
			   (4, 0.4, 0.50),
			   (5, 0.5, 0.60),
			   (6, 0.6, 0.70),
			   (7, 0.7, 0.80),
			   (8, 0.8, 0.9),
			   (9, 0.9, 1);

	call usp_WeatherForecastAggregate(_service_id, 'last', 0, null, null);

	select r.i, r.low, r.high, sum(is_precip) / count(*) as actual_chance, sum(is_precip) as precip, count(*) as total_predictions
	from
    (
		select date(wd.prediction_time) as prediction_time,
			  case
				when sum(wd.is_precip) > 1 then 1
                else 0 end as is_precip
		from weather_weatherdata as wd
		group by date(wd.prediction_time)
    ) as C
	inner join aggregated_forecast as AF on C.prediction_time = AF.prediction_time
	inner join ranges as r on AF.precip_chance >= r.low and AF.precip_chance < r.high
	group by r.i, r.low, r.high;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `usp_WeatherTempAccuracy` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `usp_WeatherTempAccuracy`(
	service_id int,
    method varchar(100),
    return_results bit
)
BEGIN

	call usp_WeatherForecastAggregate(service_id, method, 0, null, null);

	call usp_WeatherActualTemps(0, null, null);

    drop table if exists temp_accuracy_results;
    create temporary table temp_accuracy_results
    (
		n int,
        method varchar(100),
        max_diff_mean float,
        max_diff_stddev float,
        min_diff_mean float,
        min_diff_stddev float
    );

	insert into temp_accuracy_results
    (
		n,
        method,
        max_diff_mean,
        max_diff_stddev,
        min_diff_mean,
        min_diff_stddev
    )
    select count(*) as n,
		      method,
			  avg(AF.temperature_max - AT.temperature_max) as max_diff_mean,
			  stddev(AF.temperature_max - AT.temperature_max) as max_diff_stddev,
              avg(AF.temperature_min - AT.temperature_min) as min_diff_mean,
			  stddev(AF.temperature_min - AT.temperature_min) as min_diff_stddev
    from actual_temperatures as AT
    inner join aggregated_forecast AF on AT.prediction_time = AF.prediction_time;

    if return_results then
		select *
        from temp_accuracy_results;
	end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-08-26 11:04:29
