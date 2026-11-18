#=============================================
#  In this section the I/O operations happen
#  Currently only the reading and processing of
#  input data is supported
#============================================
import ast
#locates the parent dir and aims it at the data folder
def txt2dict(path):
    data = {}
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
               continue
            name, values = line.split(None, 1)

            value = (values.replace("“", '"').replace("”", '"')).replace("‘", "'").replace("’", "'")

            try:
                data[name] = ast.literal_eval(values)
            except(ValueError, SyntaxError):
                    values = value.strip("[]")
                    data[name] = [item.strip().strip("'\"") for item in values.split(",")]
    return data