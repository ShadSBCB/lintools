from topol import Topol_Data
import MDAnalysis
import rdkit
from rdkit import Chem
from collections import Counter
from itertools import combinations

class Occurrence_analysis(object): 
    def __init__(self, topology, trajectory, ligand_name, cutoff, offset, topol_object):
        self.residue_counts = {}
        self.universe = topol_object
        self.occurence_count(topology,trajectory,ligand_name, cutoff, offset)
    def occurence_count(self, topology, trajectory, ligand_name, cutoff, offset):
        """Counts the occurence of protein residues within a specified cutoff from a ligand and calculates which residues have been within cutoff for more than 50 ns (by default).
            :Arguments:
                *grofile*
                    string of the name of the GROMACS gro file
                *xtcfile*
                    trajectory file
                    
                *ligand_name*
                    string of the ligand name
                *cutoff*
                    cutoff distance from the ligand that is taken into account in angstroms
            :Returns:
                *residue_counts*
                    a dictionary of residues and how many times during the simulation they are within
                    a cutoff value from the ligand"""
        self.residue_counts={}
        i=0
        for traj in trajectory:
            i+=1
            topol_data = Topol_Data(topology,traj,ligand_name, offset)
            md_sim = topol_data.universe
            frame_dict = {}
            firstframe_ps=None
            for frame in md_sim.trajectory:
                selection = md_sim.select_atoms('protein and around '+str(cutoff)+' (segid '+str(self.universe.ligand.segids[0])+' and resid '+str(self.universe.ligand.resids[0])+')')               
                residue_list = [atom.resname+str(atom.resid) for atom in selection]
                residue_list2 = [atom.resid for atom in selection]
                frame_dict[frame.time]=set(residue_list)

                if firstframe_ps == None:
                    firstframe_ps = frame.time
            

            lastframe_time = max([f for f in frame_dict.keys()])
            self.universe.frame_count = len(frame_dict)

            self.residue_counts[i] = Counter([item for sublist in frame_dict.values() for item in sublist])
       
    def get_closest_residues_old(self,input_frame_cutoff):
        """Find the list of residues to be plotted using cutoff"""
        frame_cutoff=int(self.universe.frame_count)*int(input_frame_cutoff)/100
        self.universe.dict_of_plotted_res={}
        if len(self.residue_counts)==1:
            for res in self.residue_counts[1].keys():
                if self.residue_counts[1][res]>frame_cutoff:
                    self.universe.dict_of_plotted_res[res]=res[3:],self.residue_counts[1][res]
        else :
            list_of_plotted_res=[]
            new_res_list={}
            for xtc in self.residue_counts:
                for res in self.residue_counts[xtc]:
                    new_res_list[res]=[]
            for res in new_res_list:
                for xtc in self.residue_counts:
                    if res in self.residue_counts[xtc].keys():
                        new_res_list[res].append(self.residue_counts[xtc][res])
                    else:
                        new_res_list[res].append(0)
            for res in new_res_list:
                for (index1, value1),(index2, value2) in combinations(enumerate(new_res_list[res]),2):
                    if value1>frame_cutoff and value2>frame_cutoff:
                        if res not in list_of_plotted_res:
                            list_of_plotted_res.append(res)
        if len(self.residue_counts)==2:
            for residue in list_of_plotted_res:
                self.universe.dict_of_plotted_res[residue]=residue[3:], self.residue_counts[1][residue], self.residue_counts[2][residue]
        if len(self.residue_counts)==3:
            for residue in list_of_plotted_res:
                self.universe.dict_of_plotted_res[residue]=residue[3:], self.residue_counts[1][residue], self.residue_counts[2][residue], self.residue_counts[3][residue]


    def get_closest_residues(self,input_frame_cutoff):
         """Find the list of residues to be plotted using cutoff"""
         frame_cutoff=int(self.universe.frame_count)*int(input_frame_cutoff)/100
         self.universe.dict_of_plotted_res={}
         if len(self.residue_counts)==1:
             for res in self.residue_counts[1].keys():
                 if self.residue_counts[1][res]>frame_cutoff:
                     self.universe.dict_of_plotted_res[res]=res[3:],self.residue_counts[1][res]
         else :
             list_of_plotted_res=[]
             new_res_list={}
             for xtc in self.residue_counts:
                 for res in self.residue_counts[xtc]:
                    new_res_list[res]=[]
             for res in new_res_list:
                 for xtc in self.residue_counts:
                     if res in self.residue_counts[xtc].keys():
                         new_res_list[res].append(self.residue_counts[xtc][res])
                     else:
                         new_res_list[res].append(0)
             if len(self.residue_counts)<4:
                 for res in new_res_list:
                     for (index1, value1),(index2, value2) in combinations(enumerate(new_res_list[res]),2):
                         if value1>frame_cutoff and value2>frame_cutoff:
                             if res not in list_of_plotted_res:
                                 list_of_plotted_res.append(res)
             else: 
                 for res in new_res_list:
                     for (index1, value1),(index2, value2),(index3,value3) in combinations(enumerate(new_res_list[res]),3):
                         if value1>frame_cutoff and value2>frame_cutoff and value3>frame_cutoff:
                             if res not in list_of_plotted_res:
                                 list_of_plotted_res.append(res)

         if len(self.residue_counts)>1:
             for residue in list_of_plotted_res:
                 res_counts_tuple = [residue[3:],self.residue_counts[1][residue]]
                 for count in range(2, len(self.residue_counts)+1):
                     res_counts_tuple.append(self.residue_counts[count][residue])
                     self.universe.dict_of_plotted_res[residue] = tuple(res_counts_tuple) 