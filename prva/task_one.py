#==========================================
# Section 1
# in this section we try to represent the problem 
# and setup a fitness function
#==========================================
import Input_output as io
from pathlib import Path
import model_helper_functions as mhf

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
    classes = io.txt2dict(DATA_DIR/"Classes.txt")
    classrooms = io.txt2dict(DATA_DIR/"Classrooms.txt")
    teachers = io.txt2dict(DATA_DIR/"Teachers.txt")

    classroom_names = classrooms.keys()
    teacher_names = teachers.keys()

    lectures = mhf.generate_list_of_lectures(classes)

    print(lectures)
if __name__ == "__main__":
    main()  