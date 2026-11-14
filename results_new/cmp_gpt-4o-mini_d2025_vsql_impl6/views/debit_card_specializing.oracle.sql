-- origin=oracle row_preserving=True check=rows_equal
create view v_transactions_1k as
select
   `transactions_1k`.`TransactionID`,
   `transactions_1k`.`Date`,
   `transactions_1k`.`Time`,
   `transactions_1k`.`CustomerID`,
   `customers`.`Segment`,
   `customers`.`Currency`,
   `transactions_1k`.`CardID`,
   `transactions_1k`.`GasStationID`,
   `gasstations`.`ChainID`,
   `gasstations`.`Country`,
   `gasstations`.`Segment` as `GasStation_Segment`,
   `transactions_1k`.`ProductID`,
   `products`.`Description`,
   `transactions_1k`.`Amount`,
   `transactions_1k`.`Price`
from
   `transactions_1k`
left join `customers` on `transactions_1k`.`CustomerID` = `customers`.`CustomerID`
left join `gasstations` on `transactions_1k`.`GasStationID` = `gasstations`.`GasStationID`
left join `products` on `transactions_1k`.`ProductID` = `products`.`ProductID`

-- origin=oracle row_preserving=True check=rows_equal
create view v_yearmonth as
select
   `yearmonth`.`CustomerID`,
   `customers`.`Segment`,
   `customers`.`Currency`,
   `yearmonth`.`Date`,
   `yearmonth`.`Consumption`
from
   `yearmonth`
left join `customers` on `yearmonth`.`CustomerID` = `customers`.`CustomerID`
