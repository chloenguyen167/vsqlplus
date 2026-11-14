-- origin=oracle row_preserving=True check=rows_equal
CREATE VIEW v_atom AS SELECT atom.atom_id AS atom_id, atom.element AS element, molecule.label AS label FROM atom LEFT JOIN molecule ON atom.molecule_id = molecule.molecule_id;

-- origin=oracle row_preserving=True check=rows_equal
CREATE VIEW v_bond AS SELECT bond.bond_id AS bond_id, bond.bond_type AS bond_type, molecule.label AS label FROM bond LEFT JOIN molecule ON bond.molecule_id = molecule.molecule_id;

-- origin=oracle row_preserving=True check=rows_equal
CREATE VIEW v_connected AS SELECT connected.atom_id AS atom_id, connected.atom_id2 AS atom_id2, atom.molecule_id AS atom_molecule_id, atom.element AS atom_element, atom_id2.molecule_id AS atom_id2_molecule_id, atom_id2.element AS atom_id2_element, bond.molecule_id AS molecule_id, bond.bond_type AS bond_type FROM connected LEFT JOIN atom ON connected.atom_id = atom.atom_id LEFT JOIN atom atom_id2 ON connected.atom_id2 = atom_id2.atom_id LEFT JOIN bond ON connected.bond_id = bond.bond_id;
