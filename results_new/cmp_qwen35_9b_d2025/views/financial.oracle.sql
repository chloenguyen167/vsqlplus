-- origin=oracle row_preserving=True check=rows_equal
create view v_account as
select
   `account`.`account_id`,
   `account`.`district_id`,
   `district`.`A2`,
   `district`.`A3`,
   `district`.`A4`,
   `district`.`A5`,
   `district`.`A6`,
   `district`.`A7`,
   `district`.`A8`,
   `district`.`A9`,
   `district`.`A10`,
   `district`.`A11`,
   `district`.`A12`,
   `district`.`A13`,
   `district`.`A14`,
   `district`.`A15`,
   `district`.`A16`,
   `account`.`frequency`,
   `account`.`date`
from
   `account`
left join `district` on `account`.`district_id` = `district`.`district_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_card as
select
   `card`.`card_id`,
   `card`.`disp_id`,
   `disp`.`client_id`,
   `client`.`gender`,
   `client`.`birth_date`,
   `client`.`district_id`,
   `disp`.`account_id`,
   `disp`.`type` as `disp_type`,
   `card`.`type`,
   `card`.`issued`
from
   `card`
left join `disp` on `card`.`disp_id` = `disp`.`disp_id`
left join `client` on `disp`.`client_id` = `client`.`client_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_client as
select
   `client`.`client_id`,
   `client`.`gender`,
   `client`.`birth_date`,
   `client`.`district_id`,
   `district`.`A2`,
   `district`.`A3`,
   `district`.`A4`,
   `district`.`A5`,
   `district`.`A6`,
   `district`.`A7`,
   `district`.`A8`,
   `district`.`A9`,
   `district`.`A10`,
   `district`.`A11`,
   `district`.`A12`,
   `district`.`A13`,
   `district`.`A14`,
   `district`.`A15`,
   `district`.`A16`
from
   `client`
left join `district` on `client`.`district_id` = `district`.`district_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_disp as
select
   `disp`.`disp_id`,
   `disp`.`client_id`,
   `client`.`gender`,
   `client`.`birth_date`,
   `client`.`district_id`,
   `district`.`A2`,
   `district`.`A3`,
   `district`.`A4`,
   `district`.`A5`,
   `district`.`A6`,
   `district`.`A7`,
   `district`.`A8`,
   `district`.`A9`,
   `district`.`A10`,
   `district`.`A11`,
   `district`.`A12`,
   `district`.`A13`,
   `district`.`A14`,
   `district`.`A15`,
   `district`.`A16`,
   `disp`.`account_id`,
   `account`.`district_id` as `account_district_id`,
   `district_2`.`A2` as `district_A2`,
   `district_2`.`A3` as `district_A3`,
   `district_2`.`A4` as `district_A4`,
   `district_2`.`A5` as `district_A5`,
   `district_2`.`A6` as `district_A6`,
   `district_2`.`A7` as `district_A7`,
   `district_2`.`A8` as `district_A8`,
   `district_2`.`A9` as `district_A9`,
   `district_2`.`A10` as `district_A10`,
   `district_2`.`A11` as `district_A11`,
   `district_2`.`A12` as `district_A12`,
   `district_2`.`A13` as `district_A13`,
   `district_2`.`A14` as `district_A14`,
   `district_2`.`A15` as `district_A15`,
   `district_2`.`A16` as `district_A16`,
   `account`.`frequency`,
   `account`.`date`,
   `disp`.`type`
from
   `disp`
left join `client` on `disp`.`client_id` = `client`.`client_id`
left join `account` on `disp`.`account_id` = `account`.`account_id`
left join `district` on `client`.`district_id` = `district`.`district_id`
left join `district` district_2 on `account`.`district_id` = `district_2`.`district_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_loan as
select
   `loan`.`loan_id`,
   `loan`.`account_id`,
   `account`.`district_id`,
   `district`.`A2`,
   `district`.`A3`,
   `district`.`A4`,
   `district`.`A5`,
   `district`.`A6`,
   `district`.`A7`,
   `district`.`A8`,
   `district`.`A9`,
   `district`.`A10`,
   `district`.`A11`,
   `district`.`A12`,
   `district`.`A13`,
   `district`.`A14`,
   `district`.`A15`,
   `district`.`A16`,
   `account`.`frequency`,
   `account`.`date` as `account_date`,
   `loan`.`date`,
   `loan`.`amount`,
   `loan`.`duration`,
   `loan`.`payments`,
   `loan`.`status`
from
   `loan`
left join `account` on `loan`.`account_id` = `account`.`account_id`
left join `district` on `account`.`district_id` = `district`.`district_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_order as
select
   `order`.`order_id`,
   `order`.`account_id`,
   `account`.`district_id`,
   `account`.`frequency`,
   `account`.`date`,
   `order`.`bank_to`,
   `order`.`account_to`,
   `order`.`amount`,
   `order`.`k_symbol`
from
   `order`
left join `account` on `order`.`account_id` = `account`.`account_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_trans as
select
   `trans`.`trans_id`,
   `trans`.`account_id`,
   `account`.`district_id`,
   `district`.`A2`,
   `district`.`A3`,
   `district`.`A4`,
   `district`.`A5`,
   `district`.`A6`,
   `district`.`A7`,
   `district`.`A8`,
   `district`.`A9`,
   `district`.`A10`,
   `district`.`A11`,
   `district`.`A12`,
   `district`.`A13`,
   `district`.`A14`,
   `district`.`A15`,
   `district`.`A16`,
   `account`.`frequency`,
   `account`.`date` as `account_date`,
   `trans`.`date`,
   `trans`.`type`,
   `trans`.`operation`,
   `trans`.`amount`,
   `trans`.`balance`,
   `trans`.`k_symbol`,
   `trans`.`bank`,
   `trans`.`account`
from
   `trans`
left join `account` on `trans`.`account_id` = `account`.`account_id`
left join `district` on `account`.`district_id` = `district`.`district_id`
