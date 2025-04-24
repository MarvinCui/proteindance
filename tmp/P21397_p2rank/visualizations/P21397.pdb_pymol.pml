from pymol import cmd,stored

set depth_cue, 1
set fog_start, 0.4

set_color b_col, [36,36,85]
set_color t_col, [10,10,10]
set bg_rgb_bottom, b_col
set bg_rgb_top, t_col      
set bg_gradient

set  spec_power  =  200
set  spec_refl   =  0

load "data/P21397.pdb", protein
create ligands, protein and organic
select xlig, protein and organic
delete xlig

hide everything, all

color white, elem c
color bluewhite, protein
#show_as cartoon, protein
show surface, protein
#set transparency, 0.15

show sticks, ligands
set stick_color, magenta




# SAS points

load "data/P21397.pdb_points.pdb.gz", points
hide nonbonded, points
show nb_spheres, points
set sphere_scale, 0.2, points
cmd.spectrum("b", "green_red", selection="points", minimum=0, maximum=0.7)


stored.list=[]
cmd.iterate("(resn STP)","stored.list.append(resi)")    # read info about residues STP
lastSTP=stored.list[-1] # get the index of the last residue
hide lines, resn STP

cmd.select("rest", "resn STP and resi 0")

for my_index in range(1,int(lastSTP)+1): cmd.select("pocket"+str(my_index), "resn STP and resi "+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.show("spheres","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_scale","0.4","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_transparency","0.1","pocket"+str(my_index))



set_color pcol1 = [0.361,0.576,0.902]
select surf_pocket1, protein and id [1718,1668,1672,1674,2609,1716,2685,2683,2699,1687,1676,1678,1680,1681,854,1688,1694,740,741,2593,849,850,851,852,855,847,848,1445,1440,1448,3256,3258,3260,3262,3254,1442,3257,3259,2684,514,2793,2807,2808,512,3545,3552,3557,3547,3548,3550,3558,3554,1710,3559,3563,508,509,376,494,495,496,497,500,505,3565,1691,1692,3252,3255,367,3178,3182,3248,3250,362,363,364,2418] 
set surface_color,  pcol1, surf_pocket1 
set_color pcol2 = [0.365,0.278,0.702]
select surf_pocket2, protein and id [357,360,362,363,355,2209,3223,3236,2229,3225,325,313,3227,367,370,3483,3493,2182,2188,2206,3255,3475,3478,3582,155,156,159,2173,147,148,2180,2181,145,1941,308,309,297,1937,310,3559,3563,376,497,3545,3548,3550,3558] 
set surface_color,  pcol2, surf_pocket2 
set_color pcol3 = [0.792,0.361,0.902]
select surf_pocket3, protein and id [1644,3880,3891,997,1000,3890,3898,3930,3931,3932,3933,977,3928,3899,1008,1009,1011,856,859,860,863,865,851,848,1680,1643,854,871,875,877,881,939,966,964,971,941] 
set surface_color,  pcol3, surf_pocket3 
set_color pcol4 = [0.702,0.278,0.533]
select surf_pocket4, protein and id [1433,1402,1435,2846,2848,2849,1405,1408,2635,2640,2641,2642,2643,2623,2620,2627,1393,1397,1364,1367,1478,1480,1487,1495,1496,2821,1479,2833,2836,2873] 
set surface_color,  pcol4, surf_pocket4 
set_color pcol5 = [0.902,0.361,0.361]
select surf_pocket5, protein and id [1578,3489,3505,3297,3388,1543,3296,3498,1120,1106,1135,3331,3330,3400] 
set surface_color,  pcol5, surf_pocket5 
set_color pcol6 = [0.702,0.533,0.278]
select surf_pocket6, protein and id [2407,1463,2411,2400,3189,3190,3191,1467,1469,1471,3283,3286,2392,3240,2862,2861,1506,1505] 
set surface_color,  pcol6, surf_pocket6 
   

deselect

orient
