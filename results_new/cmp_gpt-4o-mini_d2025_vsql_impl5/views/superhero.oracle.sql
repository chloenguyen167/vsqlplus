-- origin=oracle row_preserving=True check=rows_equal
create view v_hero_attribute as
select
   `hero_attribute`.`hero_id`,
   `superhero`.`superhero_name`,
   `superhero`.`full_name`,
   `gender`.`gender`,
   `superhero`.`eye_colour_id`,
   `superhero`.`hair_colour_id`,
   `superhero`.`skin_colour_id`,
   `superhero`.`race_id`,
   `publisher`.`publisher_name`,
   `superhero`.`alignment_id`,
   `superhero`.`height_cm`,
   `superhero`.`weight_kg`,
   `attribute`.`attribute_name`,
   `hero_attribute`.`attribute_value`
from
   `hero_attribute`
left join `superhero` on `hero_attribute`.`hero_id` = `superhero`.`id`
left join `attribute` on `hero_attribute`.`attribute_id` = `attribute`.`id`
left join `gender` on `superhero`.`gender_id` = `gender`.`id`
left join `publisher` on `superhero`.`publisher_id` = `publisher`.`id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_hero_power as
select
   `hero_power`.`hero_id`,
   `superhero`.`superhero_name`,
   `superhero`.`full_name`,
   `gender`.`gender`,
   `eye_colour`.`colour` as `eye_colour`,
   `hair_colour`.`colour` as `hair_colour`,
   `skin_colour`.`colour` as `skin_colour`,
   `superhero`.`race_id`,
   `publisher`.`publisher_name`,
   `superhero`.`alignment_id`,
   `superhero`.`height_cm`,
   `superhero`.`weight_kg`,
   `superpower`.`power_name`
from
   `hero_power`
left join `superhero` on `hero_power`.`hero_id` = `superhero`.`id`
left join `superpower` on `hero_power`.`power_id` = `superpower`.`id`
left join `gender` on `superhero`.`gender_id` = `gender`.`id`
left join `colour` eye_colour on `superhero`.`eye_colour_id` = `eye_colour`.`id`
left join `colour` hair_colour on `superhero`.`hair_colour_id` = `hair_colour`.`id`
left join `colour` skin_colour on `superhero`.`skin_colour_id` = `skin_colour`.`id`
left join `publisher` on `superhero`.`publisher_id` = `publisher`.`id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_superhero as
select
   `superhero`.`id`,
   `superhero`.`superhero_name`,
   `superhero`.`full_name`,
   `gender`.`gender`,
   `eye_colour`.`colour` as `eye_colour`,
   `hair_colour`.`colour` as `hair_colour`,
   `skin_colour`.`colour` as `skin_colour`,
   `race`.`race`,
   `publisher`.`publisher_name`,
   `alignment`.`alignment`,
   `superhero`.`height_cm`,
   `superhero`.`weight_kg`
from
   `superhero`
left join `gender` on `superhero`.`gender_id` = `gender`.`id`
left join `colour` eye_colour on `superhero`.`eye_colour_id` = `eye_colour`.`id`
left join `colour` hair_colour on `superhero`.`hair_colour_id` = `hair_colour`.`id`
left join `colour` skin_colour on `superhero`.`skin_colour_id` = `skin_colour`.`id`
left join `race` on `superhero`.`race_id` = `race`.`id`
left join `publisher` on `superhero`.`publisher_id` = `publisher`.`id`
left join `alignment` on `superhero`.`alignment_id` = `alignment`.`id`
