-- origin=oracle row_preserving=True check=rows_equal
create view v_attendance as
select
   `attendance`.`link_to_event`,
   `event`.`event_name`,
   `event`.`event_date`,
   `event`.`type`,
   `event`.`notes`,
   `event`.`location`,
   `event`.`status`,
   `attendance`.`link_to_member`,
   `member`.`first_name`,
   `member`.`last_name`,
   `member`.`email`,
   `member`.`position`,
   `member`.`t_shirt_size`,
   `member`.`phone`,
   `member`.`zip`,
   `member`.`link_to_major`
from
   `attendance`
left join `event` on `attendance`.`link_to_event` = `event`.`event_id`
left join `member` on `attendance`.`link_to_member` = `member`.`member_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_budget as
select
   `budget`.`budget_id`,
   `budget`.`category`,
   `budget`.`spent`,
   `budget`.`remaining`,
   `budget`.`amount`,
   `budget`.`event_status`,
   `budget`.`link_to_event`,
   `event`.`event_name`,
   `event`.`event_date`,
   `event`.`type`,
   `event`.`notes`,
   `event`.`location`,
   `event`.`status`
from
   `budget`
left join `event` on `budget`.`link_to_event` = `event`.`event_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_expense as
select
   `expense`.`expense_id`,
   `expense`.`expense_description`,
   `expense`.`expense_date`,
   `expense`.`cost`,
   `expense`.`approved`,
   `expense`.`link_to_member`,
   `member`.`first_name`,
   `member`.`last_name`,
   `member`.`email`,
   `member`.`position`,
   `member`.`t_shirt_size`,
   `member`.`phone`,
   `member`.`zip`,
   `member`.`link_to_major`,
   `expense`.`link_to_budget`,
   `budget`.`category`,
   `budget`.`spent`,
   `budget`.`remaining`,
   `budget`.`amount`,
   `budget`.`event_status`,
   `budget`.`link_to_event`,
   `event`.`event_name`,
   `event`.`event_date`,
   `event`.`type`,
   `event`.`notes`,
   `event`.`location`,
   `event`.`status`
from
   `expense`
left join `member` on `expense`.`link_to_member` = `member`.`member_id`
left join `budget` on `expense`.`link_to_budget` = `budget`.`budget_id`
left join `event` on `budget`.`link_to_event` = `event`.`event_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_income as
select
   `income`.`income_id`,
   `income`.`date_received`,
   `income`.`amount`,
   `income`.`source`,
   `income`.`notes`,
   `income`.`link_to_member`,
   `member`.`first_name`,
   `member`.`last_name`,
   `member`.`email`,
   `member`.`position`,
   `member`.`t_shirt_size`,
   `member`.`phone`,
   `member`.`zip`,
   `member`.`link_to_major`
from
   `income`
left join `member` on `income`.`link_to_member` = `member`.`member_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_member as
select
   `member`.`member_id`,
   `member`.`first_name`,
   `member`.`last_name`,
   `member`.`email`,
   `member`.`position`,
   `member`.`t_shirt_size`,
   `member`.`phone`,
   `member`.`zip`,
   `zip_code`.`type`,
   `zip_code`.`city`,
   `zip_code`.`county`,
   `zip_code`.`state`,
   `zip_code`.`short_state`,
   `member`.`link_to_major`,
   `major`.`major_name`,
   `major`.`department`,
   `major`.`college`
from
   `member`
left join `zip_code` on `member`.`zip` = `zip_code`.`zip_code`
left join `major` on `member`.`link_to_major` = `major`.`major_id`
