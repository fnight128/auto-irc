# -*- coding: utf-8 -*-
"""
@author: Frank 
"""
import sys
from shutil import copyfile

periodicTable = ["Nothing","H","He","Li","Be","B","C","N","O","F","Ne","Na","Mg","Al","Si","P","S","Cl","Ar","K","Ca","Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Ga","Ge","As","Se","Br","Kr",
                 "Rb","Sr","Y","Zr","Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","In","Sn","Sb","Te","I","Xe","Cs","Ba","La","Ce","Pr","Nd","Pm","Sm","Eu","Gd","Tb","Dy","Ho","Er","Tm","Yb","Lu","Hf","Ta","W","Re","Os",
                 "Ir","Pt","Au","Hg","Tl","Pb","Bi","Po","At","Rn","Fr","Ra","Ac","Th","Pa","U","Np","Pu","Am","Cm","Bk","Cf","Es","Fm","Md","No","Lr","Rf","Db","Sg","Bh","Hs","Mt","Ds","Rg","Uub","Uut","Uuq","Uup",
                 "Uuh","Uus","Uuo"]

fileNameFormat = "{job}-scan-{fileNum}.inp"


if (len(sys.argv) < 2): sys.exit("No jobname given! Please review your script")
jobName = sys.argv[1]

lines = ""

with open(jobName + ".log", "r") as gOut:
    lines = gOut.read().splitlines()
#Don't run single points on incorrectly terminated jobs
if (not (" Normal termination of Gaussian " in lines[-1])):
    sys.exit("Gaussian Terminated with Error, quitting.")

#Extract charge/multiplicity and scan parameters before starting, to avoid errors
#Also allows generation of x axis in csv
chargeMult = ""

startVal = 0
stepNum  = 0
stepSize = 0

#Need to know whether scan defined by zmatrix or modredundant
zmat   = False
modred = False


for line in lines:
    #annoying gaussian
    line = line.replace(". ", ".0")
    if " Multiplicity = " in line:
        #example " Charge = -1 Multiplicity = 1"
        splitLine = line.split()
        chargeMult = splitLine[2] + " " + splitLine[5]

    #if established to be zmatrix, extract scan parameters
    elif zmat:
        if "Scan" in line:
            #if structure defined by z-matrix, reading scan parameters is really simple e.g.
            #"   R   0.9    Scan 10  0.01 "
            splitLine = line.split()
            startVal = float(splitLine[1])
            stepNum   = int(splitLine[3])
            stepSize  = float(splitLine[4])
            #No further parameters to extract
            break

    #if established to be modredundant, extract scan parameters (more tedious)
    elif modred:
        #modredundant more difficult, gives parameters in 2 different places
        if " S " in line:
            #If
            #e.g. "B  1  2  S  15 0.1000 "
            splitLine = line.split()
            stepNum = int(splitLine[4])
            stepSize  = float(splitLine[5])
        elif "Scan" in line:
            #e.g. " ! R1  R(1,2)   0.6066    Scan  !"
            splitLine = line.split()
            startVal = float(splitLine[3])
            #No further parameters to extract
            break

    #Check if input is via zmatrix or modredundant
    elif " Variables:" in line: zmat = True
    elif "following ModRedundant input section" in line: modred = True
else: sys.exit("Couldn't interpret scan. Did you really run a scan?")

stepList = ""
#e.g. 5 step scan leads to starting material + 5 scanned geometries --> need stepNum + 1
for i in range(int(stepNum + 1)):
    stepList += str(startVal + i * stepSize) + ",energy\n"

#Write a template file of scan steps, to add energies to later
with open(jobName + "-scan-parameters.csv", "w") as scanResults:
    scanResults.write(stepList)


coordStart = "\n\n * xyz " + chargeMult + "\n"
optFound   = False
coordFound = False
coords  = coordStart
fileNum    = 1

for line in lines:
    if " Optimization completed." in line: optFound = True
    if not optFound: continue
    #Once the optimised structure is found, start looking for its coords
    if " Standard orientation: " in line: coordFound = True
    if not coordFound: continue
    #Got close to coords, start explicitly looking
    splitLine = line.split()
    if len(splitLine) == 0: continue
    if splitLine[0].isnumeric():
        #e.g. line = " 1 6 0 1.85 0.13 0.12 "
        if len(splitLine) < 6: sys.exit("Invalid coordinate line found:" + line)
        atomNum = int(splitLine[1])
        if not 0 < atomNum < len(periodicTable): sys.exit("Invalid element found with atomic number " + atomNum)
        elem = periodicTable[atomNum]
        x = splitLine[3]
        y = splitLine[4]
        z = splitLine[5]
        coords += "{} {} {} {} \n".format(elem, x, y, z)
    #First line following optimisation is always rotational constants 
    elif splitLine[0] == "Rotational":
        #print("done")
        #This means all coords collected
        coords += "* \n\n"
        #Create new file and insert coords
        newInpName = fileNameFormat.format(job = jobName, fileNum = fileNum)
        copyfile(jobName + ".inp", newInpName)
        with open(newInpName, "a") as newInp:
            newInp.write(coords)
        #Continue looking through file for the next finished optimisation
        coordFound = False
        optFound   = False
        coords = coordStart
        fileNum += 1 #no ++ in python :(

if(fileNum != stepNum): 
    sys.exit("Warning: number of output files is different to number of" + 
          " intended scans. Likely error during Gaussian's scans.")

print("Successfully created " + fileNum + " ORCA input files.")