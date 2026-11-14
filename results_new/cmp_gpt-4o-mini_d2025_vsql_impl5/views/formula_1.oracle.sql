-- origin=oracle row_preserving=True check=rows_equal
create view v_constructorResults as
select
   `constructorResults`.`constructorResultsId`,
   `constructorResults`.`raceId`,
   `races`.`year`,
   `races`.`round`,
   `races`.`circuitId`,
   `races`.`name`,
   `races`.`date`,
   `races`.`time`,
   `races`.`url`,
   `constructorResults`.`constructorId`,
   `constructors`.`constructorRef`,
   `constructors`.`name` as `constructor_name`,
   `constructors`.`nationality`,
   `constructors`.`url` as `constructor_url`,
   `constructorResults`.`points`,
   `constructorResults`.`status`
from
   `constructorResults`
left join `races` on `constructorResults`.`raceId` = `races`.`raceId`
left join `constructors` on `constructorResults`.`constructorId` = `constructors`.`constructorId`

-- origin=oracle row_preserving=True check=rows_equal
create view v_constructorStandings as
select
   `constructorStandings`.`constructorStandingsId`,
   `constructorStandings`.`raceId`,
   `constructorStandings`.`constructorId`,
   `constructors`.`constructorRef`,
   `constructors`.`name`,
   `constructors`.`nationality`,
   `constructors`.`url`,
   `constructorStandings`.`points`,
   `constructorStandings`.`position`,
   `constructorStandings`.`positionText`,
   `constructorStandings`.`wins`
from
   `constructorStandings`
left join `constructors` on `constructorStandings`.`constructorId` = `constructors`.`constructorId`

-- origin=oracle row_preserving=True check=rows_equal
create view v_driverStandings as
select
   `driverStandings`.`driverStandingsId`,
   `driverStandings`.`raceId`,
   `races`.`year`,
   `races`.`round`,
   `races`.`circuitId`,
   `races`.`name`,
   `races`.`date`,
   `races`.`time`,
   `races`.`url`,
   `driverStandings`.`driverId`,
   `drivers`.`driverRef`,
   `drivers`.`number`,
   `drivers`.`code`,
   `drivers`.`forename`,
   `drivers`.`surname`,
   `drivers`.`dob`,
   `drivers`.`nationality`,
   `drivers`.`url` as `driver_url`,
   `driverStandings`.`points`,
   `driverStandings`.`position`,
   `driverStandings`.`positionText`,
   `driverStandings`.`wins`
from
   `driverStandings`
left join `races` on `driverStandings`.`raceId` = `races`.`raceId`
left join `drivers` on `driverStandings`.`driverId` = `drivers`.`driverId`

-- origin=oracle row_preserving=True check=rows_equal
create view v_lapTimes as
select
   `lapTimes`.`raceId`,
   `races`.`year`,
   `races`.`round`,
   `races`.`circuitId`,
   `races`.`name`,
   `races`.`date`,
   `races`.`time` as `race_time`,
   `races`.`url`,
   `lapTimes`.`driverId`,
   `drivers`.`driverRef`,
   `drivers`.`number`,
   `drivers`.`code`,
   `drivers`.`forename`,
   `drivers`.`surname`,
   `drivers`.`dob`,
   `drivers`.`nationality`,
   `drivers`.`url` as `driver_url`,
   `lapTimes`.`lap`,
   `lapTimes`.`position`,
   `lapTimes`.`time`,
   `lapTimes`.`milliseconds`
from
   `lapTimes`
left join `races` on `lapTimes`.`raceId` = `races`.`raceId`
left join `drivers` on `lapTimes`.`driverId` = `drivers`.`driverId`

-- origin=oracle row_preserving=True check=rows_equal
create view v_pitStops as
select
   `pitStops`.`raceId`,
   `pitStops`.`driverId`,
   `drivers`.`driverRef`,
   `drivers`.`number`,
   `drivers`.`code`,
   `drivers`.`forename`,
   `drivers`.`surname`,
   `drivers`.`dob`,
   `drivers`.`nationality`,
   `drivers`.`url`,
   `pitStops`.`stop`,
   `pitStops`.`lap`,
   `pitStops`.`time`,
   `pitStops`.`duration`,
   `pitStops`.`milliseconds`
from
   `pitStops`
left join `drivers` on `pitStops`.`driverId` = `drivers`.`driverId`

-- origin=oracle row_preserving=True check=rows_equal
create view v_qualifying as
select
   `qualifying`.`qualifyId`,
   `qualifying`.`raceId`,
   `races`.`year`,
   `races`.`round`,
   `races`.`circuitId`,
   `circuits`.`circuitRef`,
   `circuits`.`name` as `circuit_name`,
   `circuits`.`location`,
   `circuits`.`country`,
   `circuits`.`lat`,
   `circuits`.`lng`,
   `circuits`.`alt`,
   `circuits`.`url` as `circuit_url`,
   `races`.`name`,
   `races`.`date`,
   `races`.`time`,
   `races`.`url`,
   `qualifying`.`driverId`,
   `drivers`.`driverRef`,
   `drivers`.`number` as `driver_number`,
   `drivers`.`code`,
   `drivers`.`forename`,
   `drivers`.`surname`,
   `drivers`.`dob`,
   `drivers`.`nationality`,
   `drivers`.`url` as `driver_url`,
   `qualifying`.`constructorId`,
   `qualifying`.`number`,
   `qualifying`.`position`,
   `qualifying`.`q1`,
   `qualifying`.`q2`,
   `qualifying`.`q3`
from
   `qualifying`
left join `races` on `qualifying`.`raceId` = `races`.`raceId`
left join `drivers` on `qualifying`.`driverId` = `drivers`.`driverId`
left join `circuits` on `races`.`circuitId` = `circuits`.`circuitId`

-- origin=oracle row_preserving=True check=rows_equal
create view v_races as
select
   `races`.`raceId`,
   `races`.`year`,
   `seasons`.`url` as `seasons`,
   `races`.`round`,
   `races`.`circuitId`,
   `circuits`.`circuitRef`,
   `circuits`.`name` as `circuit_name`,
   `circuits`.`location`,
   `circuits`.`country`,
   `circuits`.`lat`,
   `circuits`.`lng`,
   `circuits`.`alt`,
   `circuits`.`url` as `circuit_url`,
   `races`.`name`,
   `races`.`date`,
   `races`.`time`,
   `races`.`url`
from
   `races`
left join `seasons` on `races`.`year` = `seasons`.`year`
left join `circuits` on `races`.`circuitId` = `circuits`.`circuitId`

-- origin=oracle row_preserving=True check=rows_equal
create view v_results as
select
   `results`.`resultId`,
   `results`.`raceId`,
   `races`.`year`,
   `races`.`round`,
   `races`.`circuitId`,
   `circuits`.`circuitRef`,
   `circuits`.`name` as `circuit_name`,
   `circuits`.`location`,
   `circuits`.`country`,
   `circuits`.`lat`,
   `circuits`.`lng`,
   `circuits`.`alt`,
   `circuits`.`url` as `circuit_url`,
   `races`.`name`,
   `races`.`date`,
   `races`.`time` as `race_time`,
   `races`.`url`,
   `results`.`driverId`,
   `drivers`.`driverRef`,
   `drivers`.`number` as `driver_number`,
   `drivers`.`code`,
   `drivers`.`forename`,
   `drivers`.`surname`,
   `drivers`.`dob`,
   `drivers`.`nationality`,
   `drivers`.`url` as `driver_url`,
   `results`.`constructorId`,
   `constructors`.`constructorRef`,
   `constructors`.`name` as `constructor_name`,
   `constructors`.`nationality` as `constructor_nationality`,
   `constructors`.`url` as `constructor_url`,
   `results`.`number`,
   `results`.`grid`,
   `results`.`position`,
   `results`.`positionText`,
   `results`.`positionOrder`,
   `results`.`points`,
   `results`.`laps`,
   `results`.`time`,
   `results`.`milliseconds`,
   `results`.`fastestLap`,
   `results`.`rank`,
   `results`.`fastestLapTime`,
   `results`.`fastestLapSpeed`,
   `results`.`statusId`,
   `status`.`status`
from
   `results`
left join `races` on `results`.`raceId` = `races`.`raceId`
left join `drivers` on `results`.`driverId` = `drivers`.`driverId`
left join `constructors` on `results`.`constructorId` = `constructors`.`constructorId`
left join `status` on `results`.`statusId` = `status`.`statusId`
left join `circuits` on `races`.`circuitId` = `circuits`.`circuitId`
