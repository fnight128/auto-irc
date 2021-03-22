# -*- coding: utf-8 -*-
"""
@author: Frank 
"""
import sys, glob

Ha_kJ = 2625.500

if (len(sys.argv) < 2): sys.exit("No jobname given! Please review your script")
jobName = sys.argv[1]

finalList = []

with open (jobName + "-scan-parameters.csv", "r") as scanParams:
    finalList = scanParams.read().splitlines()

fileNames = "{job}-scan-{num}.out".format(job = jobName, num = "{num}")

allFiles = fileNames.format(num = "*")

numFiles = len(glob.glob(allFiles))

energies = [""] * numFiles

#Extract energies
for i in range(numFiles):
    fileName = fileNames.format(num = i + 1)
    with open (fileName, "r") as orcaOut:
        lines = orcaOut.read().splitlines()
        if not ("****ORCA TERMINATED NORMALLY****" in lines[-2]):
            sys.exit("Error in orca termination for file" + fileName)
        for line in reversed(lines):
            if "FINAL SINGLE POINT ENERGY " in line:
                #e.g. "FINAL SINGLE POINT ENERGY     -1293.603138876193
                energies[i] = float(line.split()[4])
                break

#Convert from hartree and "normalise"(?)
lowestEnergy = min(energies)
for i in range(len(energies)):
    energies[i] = (energies[i] - lowestEnergy) * Ha_kJ
    finalList[i] = finalList[i].replace("energy", str(energies[i]))
print(energies)


with open(jobName + "-scan.csv", "w") as scanResults:
    scanResults.write("\n".join(finalList))

