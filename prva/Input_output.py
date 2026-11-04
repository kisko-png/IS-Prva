#=============================================
#  In this section the I/O operations happen
#  Currently only the reading and processing of
#  input data is supported
#============================================
import ast
#loactes the parent dir and aims it at the data folder

def txt2dict(path):
    data = {}
    with open(path, "r") as file:
        for line in file:
            string, values = line.strip().split(" ", 1)

            #normalise input aka wtf are these quotation marks they hate us patrik
            values = values.replace("“", '"').replace("”", '"')

            try:
                data[string] = ast.literal_eval(values)
            except (ValueError, SyntaxError):
                values = values.strip("[]")
                data[string] = [ 
                    item.strip() for item in values.split(",")
                ]
    return data