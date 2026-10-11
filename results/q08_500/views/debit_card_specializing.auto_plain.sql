-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_yearmonth AS SELECT yearmonth.CustomerID AS CustomerID, yearmonth.Date AS Date, yearmonth.Consumption AS Consumption, Customer.Segment AS Segment, Customer.Currency AS Currency FROM yearmonth LEFT JOIN customers AS Customer ON yearmonth.CustomerID = Customer.CustomerID;
