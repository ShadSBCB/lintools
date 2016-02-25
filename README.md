# LINTools [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.45076.svg)](http://dx.doi.org/10.5281/zenodo.45076)

LINTools (or Ligand Interaction Network Tools) is an open source program fully written in Python. It produces diagrams of interaction between protein and ligands in a molecular dynamics trajectory or a topology file. It can be used to investigate docking poses, show the residues that are spending most time in the vicinity of the ligand and possibly other things. Examples shall follow on a later date.

#Dependencies
LINTools require these packages:
* RDKit (installation instructions with Anaconda available from RDKit GitHub account: https://github.com/rdkit/conda-rdkit)
* Shapely (available on GitHub https://github.com/Toblerity/Shapely)
* MDAnalysis (available on GitHub https://github.com/MDAnalysis/mdanalysis)
* OpenBabel with Python bindings

If this is a problem for your computer's architecture, a Dockerfile has also been provided.

You will need a topology file and (optional) trajectory.

Usage:
For a topology file (no trajectory data):
```
lintools -t my_top_file.pdb -o my_output
(Optional: --cutoff [a number] --residueoffset [a number] --diagram_type "amino" or "domains" -df domain text file )
```

For trajectory data:
```
lintools -t my_top_file.pdb -x my_traj.xtc -o my_output 
(Optional: same as above + --analysis "occurance"or  "rmsf" and for occurance analysis it is possible to choose up to three trajectories
which are displayed as clock diagrams. --diagram_type "clock" must be specified)
```

With configuration file (written after every run):
```
python lintools.py -conf file_config.txt -o outname 
(Optional: if you want a repeat of the same graph you produced, use just -conf flag, but if you want to change something e.g. cutoff or diagram type, use the respective flag with new value).
```

Domain representation

The domains can be represented as circles of particular color. The domain can be anything you define  - transmembrane helix, specific chain, known binding site. Any range can be specified - see example below.
Domain text file should contain lines of your domains, containing ID - a number from 1 up to 12 (twelve different colors available at the moment), range of residues and text ID for your domain, all separated by semicolons. Optional: Add user-defined color to your domain in HEX, also, can specify whether the circles should be dashed or not by supplying a Y/N article after the color. Also, if you want to show something like a binding site that spans several domains, use color “None” and dashed “Y” to show dashed circles for your binding site. See the example how it could be done in new_domains.pdf)

Example domain file:
```
1;1-20,24;TMH 1
2;26-35,40-56;TMH 2;#D9774B 
3;61-100;TMH 3;Y      # Not allowed
3;61-100;Chain B;#889DCC;Y 
4;34,56,78;Binding site;None;Y    #This will make a dashed circle regardless of the original assignment, always has to come last in the domain file.
```
The test.pdf and new_domains.pdf files were produced using crystal structure with PDB ID 4XP1 and displays the LDP residue.

Please post an issue if you have suggestions for improvements.
