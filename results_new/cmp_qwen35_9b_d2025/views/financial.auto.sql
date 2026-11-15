-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_account AS SELECT account.account_id AS account_id, account.district_id AS district_id, account.frequency AS frequency, account.date AS date, district.A2 AS A2, district.A3 AS A3, district.A4 AS A4, district.A5 AS A5, district.A6 AS A6, district.A7 AS A7, district.A8 AS A8, district.A9 AS A9, district.A10 AS A10, district.A11 AS A11, district.A12 AS A12, district.A13 AS A13, district.A14 AS A14, district.A15 AS A15, district.A16 AS A16 FROM account LEFT JOIN district AS district ON account.district_id = district.district_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_card AS SELECT card.card_id AS card_id, card.disp_id AS disp_id, card.type AS type, card.issued AS issued, disp.client_id AS client_id, disp.account_id AS account_id, disp.type AS disp_type, client.gender AS gender, client.birth_date AS birth_date, client.district_id AS district_id, account.district_id AS account_district_id, account.frequency AS frequency, account.date AS date FROM card LEFT JOIN disp AS disp ON card.disp_id = disp.disp_id LEFT JOIN client AS client ON disp.client_id = client.client_id LEFT JOIN account AS account ON disp.account_id = account.account_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_client AS SELECT client.client_id AS client_id, client.gender AS gender, client.birth_date AS birth_date, client.district_id AS district_id, district.A2 AS A2, district.A3 AS A3, district.A4 AS A4, district.A5 AS A5, district.A6 AS A6, district.A7 AS A7, district.A8 AS A8, district.A9 AS A9, district.A10 AS A10, district.A11 AS A11, district.A12 AS A12, district.A13 AS A13, district.A14 AS A14, district.A15 AS A15, district.A16 AS A16 FROM client LEFT JOIN district AS district ON client.district_id = district.district_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_disp AS SELECT disp.disp_id AS disp_id, disp.client_id AS client_id, disp.account_id AS account_id, disp.type AS type, client.gender AS gender, client.birth_date AS birth_date, client.district_id AS district_id, account.district_id AS account_district_id, account.frequency AS frequency, account.date AS date FROM disp LEFT JOIN client AS client ON disp.client_id = client.client_id LEFT JOIN account AS account ON disp.account_id = account.account_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_loan AS SELECT loan.loan_id AS loan_id, loan.account_id AS account_id, loan.date AS date, loan.amount AS amount, loan.duration AS duration, loan.payments AS payments, loan.status AS status, account.district_id AS district_id, account.frequency AS frequency, account.date AS account_date FROM loan LEFT JOIN account AS account ON loan.account_id = account.account_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_order AS SELECT `order`.order_id AS order_id, `order`.account_id AS account_id, `order`.bank_to AS bank_to, `order`.account_to AS account_to, `order`.amount AS amount, `order`.k_symbol AS k_symbol, account.district_id AS district_id, account.frequency AS frequency, account.date AS date FROM `order` LEFT JOIN account AS account ON `order`.account_id = account.account_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_trans AS SELECT trans.trans_id AS trans_id, trans.account_id AS account_id, trans.date AS date, trans.type AS type, trans.operation AS operation, trans.amount AS amount, trans.balance AS balance, trans.k_symbol AS k_symbol, trans.bank AS bank, trans.account AS account, account.district_id AS district_id, account.frequency AS frequency, account.date AS account_date FROM trans LEFT JOIN account AS account ON trans.account_id = account.account_id;
