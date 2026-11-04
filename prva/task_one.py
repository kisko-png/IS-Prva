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
    """ 
    #for testing
    files = os.listdir(DATA_DIR)
    for file in files: #used for testing you can try it out
        print(file)
        lectures = io.txt2dict(DATA_DIR / file) #this works now after 2h fuck me
        print(lectures)
    """
    clases = io.txt2dict(DATA_DIR/"Classes.txt")
    classroms = io.txt2dict(DATA_DIR/"Classrooms.txt")
    teachers = io.txt2dict(DATA_DIR/"Teachers.txt")

    print(classroms)
if __name__ == "__main__":
    main()  