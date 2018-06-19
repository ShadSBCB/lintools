from collections import defaultdict
import csv
import MDAnalysis
from MDAnalysis.analysis import hbonds
from timeit import default_timer as timer
from rdkit import Chem
import rdkit
import numpy as np
import os

class HBonds(object):
    """
    This module analyses hydrogen bonds the ligand forms with the protein (version "09.2016").
    The donor and acceptor atoms in ligand molecule are detected by RDKit, then the bonds are
    detected by MDAnalysis hydrogen bonding analysis and counted by time (how many total bonds
    per frame) and by type (fraction of time per each hydrogen bond). Information about the
    total count of hydrogen bonds over time is provided in a data file (CSV format). Each hydro-
    gen bond is then analysed to decide whether to plot it in the final image.

    Takes:
        * topology_data_object * - information about the system (lintools.Data object)
        * trajectory * - list of trajectories
        * start_frame_num * - list^^ of frame numbers for start of analysis (Opt)
        * end_frame_num * - list^^ of frame numbers for end of analysis (Opt)
        * skip * - list^^ of numbers of how many frames should be skipped for this analysis (Opt)
        * distance * - distance between hydrogen bond donor and acceptor atoms in angstroms
        * analysis_cutoff * - (user-defined) fraction of time a hydrogen bond has to be
            present for to be plotted (default - 0.3). It is multiplied by number of trajectories

    ^^ The reason these values are lists is because several trajectories can be submitted for
    analysis and different values could be required for each simulation. Therefore, similarly
    as with trajectories, start, end and skip variables are submitted as lists with values
    corresponding for each trajectory.

    Example: trajectory = ["1.xtc","2.xtc"] #Both are 1000 frames, but the user only wants to
             analyse second half the the second trajectory
             start = [0(for the first traj),500(for the second traj)]
             Other values can be left as default.
    """
    __version__ = "06.2018"
    def __init__(self, topology_data_object, trajectory, start_frame_num=None,end_frame_num=None,skip=None,analysis_cutoff=0.3,distance=3):
        self.hbonds = None
        self.HDonorSmarts = Chem.MolFromSmarts('[$([N;!H0;v3]),$([N;!H0;+1;v4]),$([O,S;H1;+0]),$([n;H1;+0])]')
        haccep = "[$([O,S;H1;v2]-[!$(*=[O,N,P,S])]),$([O,S;H0;v2]),$([O,S;-]),$([N;v3;!$(N-*=!@[O,N,P,S])]),$([nH0,o,s;+0])]"
        self.HAcceptorSmarts = Chem.MolFromSmarts(haccep)
        self.donors = []
        self.acceptors = []
        self.topology_data = topology_data_object
        self.trajectory = trajectory
        self.hbonds = {}
        self.hbonds_timesteps={}
        self.hbonds_by_time = {}
        self.hbonds_by_type = {}
        self.hbonds_timesteps_by_type = {}
        self.start_frame_num = start_frame_num
        self.end_frame_num = end_frame_num
        self.skip = skip
        self.find_donors_and_acceptors_in_ligand()
        if len(trajectory)>0:
            self.analyse_hydrogen_bonds_traj(distance)
        else:
            self.analyse_hydrogen_bonds_topology(distance)
        self.determine_hbonds_for_drawing(analysis_cutoff)
        self.write_output_files()
    def find_donors_and_acceptors_in_ligand(self):
        """
        Since MDAnalysis a pre-set list for acceptor and donor atoms for proteins and solvents
        from specific forcefields, it is necessary to find donor and acceptor atoms for the
        ligand molecule. This function uses RDKit and searches through ligand atoms to find
        matches for pre-set list of possible donor and acceptor atoms. The resulting list is then
        parsed to MDAnalysis through the donors and acceptors arguments.
        """
        atom_names=[x.name for x in self.topology_data.universe.ligand]
        try:
            for atom in self.topology_data.mol.GetSubstructMatches(self.HDonorSmarts, uniquify=1):
                self.donors.append(atom_names[atom[0]])
            for atom in self.topology_data.mol.GetSubstructMatches(self.HAcceptorSmarts, uniquify=1):
                self.acceptors.append(atom_names[atom[0]])
        except Exception as e:
            m = Chem.MolFromPDBFile("lig.pdb")
            self.donors = []
            self.acceptors = []
            for atom in m.GetSubstructMatches(self.HDonorSmarts, uniquify=1):
                self.donors.append(atom_names[atom[0]])
            haccep = "[$([O,S;H1;v2]-[!$(*=[O,N,P,S])]),$([O,S;H0;v2]),$([O,S;-]),$([N;v3;!$(N-*=!@[O,N,P,S])]),$([nH0,o,s;+0])]"
            self.HAcceptorSmarts = Chem.MolFromSmarts(haccep)
            for atom in m.GetSubstructMatches(self.HAcceptorSmarts, uniquify=1):
                self.acceptors.append(atom_names[atom[0]])
    def analyse_hydrogen_bonds_traj(self,distance=3):
        """
        MDAnalysis.analysis.hbonds module is used to analyse hydrogen bonds formed between protein
        and ligand for each submitted trajectory. The hydrogen bonds are then counted by total value
        per frame (count_by_time), as well as obtaining the frequency of each individual hydrogen
        bond (count_by_type).

        Format of h.table below is time, donor_index, acceptor_index, donor_resnm, donor_resid, donor_atom, acceptor_resnm, acceptor_resid, acceptor_atom, distance, angle.
        count_by_type should return atom indices, residue names, residue numbers (for donors and acceptors) and the fraction of the total time, but actually format is:-
        
        donor_atom, acceptor_atom, donor_atom_name, acceptor_atom_name, donor_resname, donor_resid, acceptor_resname, acceptor_resid, time.


        Takes:
            * distance * - distance between hydrogen bond donor and acceptor in angstroms
        Output:
            * self.hbonds * - array with information about all detected hydrogen bonds
            * self.hbonds_by_time * - total hbond number by frame
            * self.hbonds_by_type * - frequency of each hydrogen bond

        """
        i=0
        for traj in self.trajectory:
            self.topology_data.load_trajectory(traj)
            start = timer()
            h = MDAnalysis.analysis.hbonds.HydrogenBondAnalysis(self.topology_data.universe,'(segid '+str(self.topology_data.universe.ligand.segids[0])+' and resid '+str(self.topology_data.universe.ligand.resids[0])+')',"protein",distance=3,acceptors=self.acceptors,donors=self.donors,start=self.start_frame_num[i],stop=self.end_frame_num[i],step=self.skip[i])
            h.run()
            h.generate_table()
            end = timer()
            self.hbonds[i]=h.table
            self.hbonds_timesteps[i] =h.timesteps
            self.hbonds_by_time[i] = h.count_by_time()
            self.hbonds_by_type[i] = self.count_by_type(h.table,h.timesteps)
            self.hbonds_timesteps_by_type[i] = h.timesteps_by_type()
            i+=1

    def count_by_type(self,table,timesteps):
        """Count how many times each individual hydrogen bonds occured throughout the simulation.
        Returns numpy array."""
        hbonds = defaultdict(int)
        for contact in table:
            #count by residue name not by protein ring
            pkey = (contact.donor_index,contact.acceptor_index,contact.donor_atom, contact.acceptor_atom,contact.donor_resnm,contact.donor_resid, contact.acceptor_resnm,contact.acceptor_resid)
            hbonds[pkey]+=1
        dtype = [("donor_index",int),("acceptor_index",int),("donor_atom","|U4"),("acceptor_atom","|U4"),("donor_resnm","|U8"),("donor_resid","|U8"),("acceptor_resnm","|U8"),("acceptor_resid","|U8"),("frequency",float) ]
        out = np.empty((len(hbonds),),dtype=dtype)
        tsteps = float(len(timesteps))
        for cursor,(key,count) in enumerate(hbonds.iteritems()):
            out[cursor] = key + (count / tsteps,)
        return out.view(np.recarray)

    def analyse_hydrogen_bonds_topology(self,distance=3):
        #This is the routine that is called if only a single coordinate file is requested.
        """
        MDAnalysis.analysis.hbonds module is used to analyse hydrogen bonds formed between protein
        and ligand for each submitted trajectory. The hydrogen bonds are then counted by total value
        per frame (count_by_time), as well as obtaining the frequency of each individual hydrogen
        bond (count_by_type). This function is used in case no trajectory has been submitted for analysis.

        Takes:
            * distance * - distance between hydrogen bond donor and acceptor in angstroms
        Output:
            * self.hbonds * - array with information about all detected hydrogen bonds
            * self.hbonds_by_time * - total hbond number by frame
            * self.hbonds_by_type * - frequency of each hydrogen bond
        """

        h = MDAnalysis.analysis.hbonds.HydrogenBondAnalysis(self.topology_data.universe,'(segid '+str(self.topology_data.universe.ligand.segids[0])+' and resid '+str(self.topology_data.universe.ligand.resids[0])+')',"protein",distance=3,acceptors=self.acceptors,donors=self.donors)
        h.run()
        h.generate_table()
        self.hbonds[0]=h.table
        self.hbonds_by_time[0] = h.count_by_time()
        self.hbonds_by_type[0] = h.count_by_type()
    
    def determine_hbonds_for_drawing(self, analysis_cutoff):
        """
        Since plotting all hydrogen bonds could lead to a messy plot, a cutoff has to be imple-
        mented. In this function the frequency of each hydrogen bond is summated and the total
        compared against analysis cutoff - a fraction multiplied by trajectory count. Those
        hydrogen bonds that are present for longer than analysis cutoff will be plotted in the
        final plot.

        Takes:
            * analysis_cutoff * - (user-defined) fraction of time a hydrogen bond has to be
            present for to be plotted (default - 0.3). It is multiplied by number of trajectories
        Output:
            * frequency * - dictionary of hydrogen bond donor-acceptor indices and frequencies
            These hydrogen bonds will be plotted in the final image.

        """
        self.frequency = defaultdict(int)
        for traj in self.hbonds_by_type:
            for bond in self.hbonds_by_type[traj]:
            # frequency[(residue_atom_idx,ligand_atom_name,residue_atom_name)]=frequency
            # residue atom name will be used to determine if hydrogen bond is interacting with a sidechain or bakcbone
            # Following looks problematic for the trajectory subroutine as LD's routine does not return indices..?
                if bond["donor_resnm"]!="LIG":
                    self.frequency[(bond["donor_index"],bond["acceptor_atom"],bond["donor_atom"],bond["acceptor_index"])] += bond["frequency"]
                #check whether ligand is donor or acceptor
                else:
                    self.frequency[(bond["acceptor_index"],bond["donor_atom"],bond["acceptor_atom"],bond["donor_index"])] += bond["frequency"]

        #Add the frequency counts
        self.frequency = {i:self.frequency[i] for i in self.frequency if self.frequency[i]>(int(len(self.trajectory))*analysis_cutoff)}


        #change the ligand atomname to a heavy atom - required for plot since only heavy atoms shown in final image
        self.hbonds_for_drawing = {}
        for bond in self.frequency:
            atomname = bond[1]
            if atomname.startswith("O",0) or atomname.startswith("N",0):
                lig_atom=atomname
            else:
                atomindex = [index for index,atom in enumerate(self.topology_data.universe.ligand.atoms) if atom.name==atomname][0]
                rdkit_atom = self.topology_data.mol.GetAtomWithIdx(atomindex)
                for neigh in rdkit_atom.GetNeighbors():
                    neigh_atom_id = neigh.GetIdx()
                lig_atom = [atom.name for index,atom in enumerate(self.topology_data.universe.ligand.atoms) if index==neigh_atom_id][0]
            self.hbonds_for_drawing[(bond[0],lig_atom,bond[2],bond[3])]=self.frequency[bond]

    def write_output_files(self):
        #This is probably not the most efficient code, but its probably easier to read (PCB).
        #Note that total may be more than the apparent sum because the total is the total hbonds for each time, whereas we are only dumping out individual files for ones where
        #there is greater a certain % of time occurance.
        
        """
        The total hydrogen bond count per frame is provided as CSV output file.
        Each trajectory has a separate file.
        """
        os.mkdir("analysis")
        os.chdir("analysis")
        os.mkdir("hydrogen_bonds")
        os.chdir("hydrogen_bonds")
        for traj in range(len(self.trajectory)):
            with open('hbonds_data_total_'+str(traj)+'.csv', 'wb') as outfile:
                hwriter = csv.writer(outfile, delimiter=',')
                for time in self.hbonds_by_time[traj]:
                    hwriter.writerow([time[0],time[1]])
            for bond in self.hbonds_by_type[traj]:
                if bond["donor_resnm"]=="LIG" and (bond["acceptor_index"],bond["donor_index"]) in [(k[0],k[3]) for k,v in self.hbonds_for_drawing.items()]:
                    with open('hbond_'+bond["acceptor_resnm"]+"_"+str(bond["acceptor_resid"])+"_"+bond["donor_atom"]+"_"+str(traj)+".csv","wb") as outfile:
                        hwriter = csv.writer(outfile, delimiter=',')
                        for time in self.hbonds_timesteps[traj]:
                            result = 0
                            for x in self.hbonds[traj]:
                                if (x[0]==time and x["acceptor_index"]==bond["acceptor_index"]):
                                    result = result + 1
                            hwriter.writerow([time,result])
                if bond["donor_resnm"]!="LIG" and (bond["donor_index"],bond["acceptor_index"]) in [(k[0],k[3]) for k,v in self.hbonds_for_drawing.items()]:
                    with open('hbond_'+bond["donor_resnm"]+"_"+str(bond["donor_resid"])+"_"+bond["acceptor_atom"]+"_"+str(traj)+".csv","wb") as outfile:
                        hwriter = csv.writer(outfile, delimiter=',')
                        for time in self.hbonds_timesteps[traj]:
                            result = 0
                            for x in self.hbonds[traj]:
                                if (x[0]==time and x["donor_index"]==bond["donor_index"]):
                                    result = result + 1
                            hwriter.writerow([time,result])
        os.chdir("../../")
