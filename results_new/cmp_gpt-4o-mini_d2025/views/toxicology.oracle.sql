-- origin=oracle row_preserving=True check=rows_equal
create view v_atom as
select
   `atom`.`atom_id`,
   `atom`.`molecule_id`,
   `molecule`.`label`,
   `atom`.`element`
from
   `atom`
left join `molecule` on `atom`.`molecule_id` = `molecule`.`molecule_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_bond as
select
   `bond`.`bond_id`,
   `bond`.`molecule_id`,
   `molecule`.`label`,
   `bond`.`bond_type`
from
   `bond`
left join `molecule` on `bond`.`molecule_id` = `molecule`.`molecule_id`

-- origin=oracle row_preserving=True check=rows_equal
create view v_connected as
select
   `connected`.`atom_id`,
   `atom`.`molecule_id` as `atom_molecule_id`,
   `atom`.`element` as `atom_element`,
   `connected`.`atom_id2`,
   `atom_id2`.`molecule_id` as `atom_id2_molecule_id`,
   `atom_id2`.`element` as `atom_id2_element`,
   `connected`.`bond_id`,
   `bond`.`molecule_id`,
   `bond`.`bond_type`
from
   `connected`
left join `atom` on `connected`.`atom_id` = `atom`.`atom_id`
left join `atom` atom_id2 on `connected`.`atom_id2` = `atom_id2`.`atom_id`
left join `bond` on `connected`.`bond_id` = `bond`.`bond_id`
