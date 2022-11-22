# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

#base_dir = "/home/kkeller/BSC/EarthScience/Projects/DestinationEarth_ECMWF/Lab/Nemo/DE_340_issue_152/"
#v40_namelist_dir = "namelists_v40/"
#v42_namelist_dir = "namelists_v42/"

import f90nml

class NemoNamelist:
    def __init__(self, namelist_path, label=None):
        self.namelist_path = namelist_path
        self.namelist = f90nml.read(namelist_path)
        self.label = label

    def diff(self: 'NemoNamelist', reference: 'NemoNamelist'):
        if self.label:
            print("keys only in " + self.label)
        else:
            print("keys only in self")
        for key in self.namelist.todVict().keys():
            if key not in reference.namelist.todict().keys():
                print(f"\t: {key}")
        if reference.label:
            print("keys only in " + reference.label)
        else:
            print("keys only in reference")
        for key in reference.namelist.todict().keys():
            if key not in self.namelist.todict().keys():
                print(f"\t: {key}")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pass

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
