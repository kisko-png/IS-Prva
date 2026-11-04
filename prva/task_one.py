#==========================================
# Section 1
# in this section we try to represent the problem 
# and setup a fitnes function  
#==========================================
import pygad
import os
import Input_output as io
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent 
DATA_DIR = ROOT_DIR/"data"

def fitnes_function():
    return 0

def main():
    #for testing
    files = os.listdir(DATA_DIR)

    for file in files:
        #print(file)
        lectures = io.txt2dict(DATA_DIR / file) #this works now after 2h fuck me
        print(lectures)
if __name__ == "__main__":
    main()  