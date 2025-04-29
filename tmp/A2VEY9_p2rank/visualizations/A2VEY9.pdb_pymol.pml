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

load "data/A2VEY9.pdb", protein
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

load "data/A2VEY9.pdb_points.pdb.gz", points
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
select surf_pocket1, protein and id [386,1399,1401,385,1547,1549,1578,414,384,403,405,410,404,407,381,1368,1370,1371,1369,1372,1388,1557,1992,1993,1966,1402,1403,1404,1405,1406,1408,1409,2100,1366,1936,1938,1973,1903,1968,1577,1606,1602,434,431,433,1604,1633] 
set surface_color,  pcol1, surf_pocket1 
set_color pcol2 = [0.278,0.298,0.702]
select surf_pocket2, protein and id [1452,1453,1454,2334,2335,2382,2332,4985,4981,4983,4984,5004,2330,2359,1332,4956,4958,4959,4960,4961,4980,4982,4992,5013,1451,1450,2366,2337,2340,1244,1248,2251,2244,2246,2249,2247,1235,1234,1236,1070,1079,1080,1081,1086,1088,1336,1339,1340,1343,1331] 
set surface_color,  pcol2, surf_pocket2 
set_color pcol3 = [0.533,0.361,0.902]
select surf_pocket3, protein and id [2408,156,157,158,2406,2413,2416,2417,153,154,788,790,792,794,798,799,2411,197,199,2520,2466,2487,2491,2493,2494,2528,2527,4890,4893,1311] 
set surface_color,  pcol3, surf_pocket3 
set_color pcol4 = [0.565,0.278,0.702]
select surf_pocket4, protein and id [4899,4901,859,4900,857,4924,4927,808,835,838,840,839,1132,1229,1206,1205,1202,868,870,1209,1049,897,1200] 
set surface_color,  pcol4, surf_pocket4 
set_color pcol5 = [0.902,0.361,0.878]
select surf_pocket5, protein and id [1642,1664,1667,1668,1669,1693,4235,1690,4257,4251,1884,1894,1896,1920,1914,1916,1918,1644,1643,4225,4250,4230] 
set surface_color,  pcol5, surf_pocket5 
set_color pcol6 = [0.702,0.278,0.533]
select surf_pocket6, protein and id [1121,1141,1115,2160,2162,2164,2153,2151,2152,1238,1239,2117,2252,1117,1107,1116,2241,1102,1111,1259,2108,2141,2143,1253,1240,1242,2115] 
set surface_color,  pcol6, surf_pocket6 
set_color pcol7 = [0.902,0.361,0.490]
select surf_pocket7, protein and id [260,254,255,256,257,258,743,745,334,357,368,371,337,336] 
set surface_color,  pcol7, surf_pocket7 
set_color pcol8 = [0.702,0.329,0.278]
select surf_pocket8, protein and id [1640,1642,4251,1955,1957,1920,1959,1960,1918,1644,1945,4250] 
set surface_color,  pcol8, surf_pocket8 
set_color pcol9 = [0.902,0.620,0.361]
select surf_pocket9, protein and id [557,558,1675,1676,531,1648,1622,1624,1652,1656,1647,1651,1649,584,586,607,608] 
set surface_color,  pcol9, surf_pocket9 
set_color pcol10 = [0.702,0.631,0.278]
select surf_pocket10, protein and id [639,641,644,654,655,472,470,471,473,474,475,616,468,441,444,442] 
set surface_color,  pcol10, surf_pocket10 
   

deselect

orient
