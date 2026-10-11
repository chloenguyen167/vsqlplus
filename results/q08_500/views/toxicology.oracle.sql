-- origin=oracle row_preserving=True check=rows_equal
CREATE VIEW v_atom AS SELECT atom.atom_id AS atom_id, atom.molecule_id AS molecule_id, atom.element AS element, molecule.label AS molecule_label FROM atom LEFT JOIN molecule AS molecule ON atom.molecule_id = molecule.molecule_id;

-- origin=oracle row_preserving=True check=rows_equal
CREATE VIEW v_bond AS SELECT bond.bond_id AS bond_id, bond.molecule_id AS molecule_id, bond.bond_type AS bond_type, molecule.label AS molecule_label FROM bond LEFT JOIN molecule AS molecule ON bond.molecule_id = molecule.molecule_id;

-- origin=oracle row_preserving=True check=rows_equal
CREATE VIEW v_connected AS SELECT connected.atom_id AS atom_id, connected.atom_id2 AS atom_id2, connected.bond_id AS bond_id, bond.molecule_id AS bond_molecule_id, bond.bond_type AS bond_type, atom_id2.molecule_id AS atom_id2_molecule_id, atom_id2.element AS atom_id2_element, atom.molecule_id AS atom_molecule_id, atom.element AS atom_element FROM connected LEFT JOIN bond AS bond ON connected.bond_id = bond.bond_id LEFT JOIN atom AS atom_id2 ON connected.atom_id2 = atom_id2.atom_id LEFT JOIN atom AS atom ON connected.atom_id = atom.atom_id;

-- origin=oracle_fan row_preserving=False check=rows_differ(346038 vs 9111)
CREATE VIEW v_atom_bond_molecule AS SELECT atom.atom_id AS atom_id, atom.molecule_id AS molecule_id, atom.element AS element, molecule.label AS molecule_label, bond.bond_id AS bond_id, bond.bond_type AS bond_type FROM atom LEFT JOIN molecule AS molecule ON atom.molecule_id = molecule.molecule_id LEFT JOIN bond AS bond ON molecule.molecule_id = bond.molecule_id;
