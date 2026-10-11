-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_atom AS SELECT atom.atom_id AS atom_id, atom.molecule_id AS molecule_id, atom.element AS element, molecule.label AS molecule_label FROM atom LEFT JOIN molecule AS molecule ON atom.molecule_id = molecule.molecule_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_bond AS SELECT bond.bond_id AS bond_id, bond.molecule_id AS molecule_id, bond.bond_type AS bond_type, molecule.label AS molecule_label FROM bond LEFT JOIN molecule AS molecule ON bond.molecule_id = molecule.molecule_id;

-- origin=auto row_preserving=True check=rows_equal
CREATE VIEW v_connected AS SELECT connected.atom_id AS atom_id, connected.atom_id2 AS atom_id2, connected.bond_id AS bond_id, bond.molecule_id AS bond_molecule_id, bond.bond_type AS bond_type, bond_molecule.label AS bond_molecule_label, atom_id2.molecule_id AS atom_id2_molecule_id, atom_id2.element AS atom_id2_element, atom_id2_molecule.label AS atom_id2_molecule_label, atom.molecule_id AS atom_molecule_id, atom.element AS atom_element, atom_molecule.label AS atom_molecule_label FROM connected LEFT JOIN bond AS bond ON connected.bond_id = bond.bond_id LEFT JOIN molecule AS bond_molecule ON bond.molecule_id = bond_molecule.molecule_id LEFT JOIN atom AS atom_id2 ON connected.atom_id2 = atom_id2.atom_id LEFT JOIN molecule AS atom_id2_molecule ON atom_id2.molecule_id = atom_id2_molecule.molecule_id LEFT JOIN atom AS atom ON connected.atom_id = atom.atom_id LEFT JOIN molecule AS atom_molecule ON atom.molecule_id = atom_molecule.molecule_id;
