from os import path

class DetailInfo:
    def __init__(self):
        pass

    def print(self):
        var_dict = vars(self)
        print("------------------------------------------------")
        print(f"* {self.__class__.__name__} *")
        for i in var_dict:
            var = var_dict[i]
            print(f"[{i}]: {var}")


class ErrorHandle:
    def data_save(self, **kwargs):
        for key in self.kwargs:
            with open(f"data_save/{key}", "w") as file:
                file.write(str(kwargs[key]))


    def save_current(self, id):
        cur = dict()
        cur['vendor_id'] = id
        with open(f"data_save/current", "w", encoding='utf-8') as file:
            file.write(str(cur))

    def read_current(self):
        with open(f"data_save/current", "r") as file:
            x = file.read()
        return eval(x)

    def file_checking(self):
        x = path.isfile('data_save/current')
        return x