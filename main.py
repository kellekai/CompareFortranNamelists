# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import f90nml

base_dir = "/home/kkeller/BSC/EarthScience/Projects/DestinationEarth_ECMWF/Lab/Nemo/DE_340_issue_152/"
v40_namelist_dir = "namelists_v40/"
v42_namelist_dir = "namelists_v42/"


def check_key(dict, key, mode):
    res = True
    if mode == 'create':
        if key not in dict.keys():
            dict[key] = {}

    return res


class NemoNamelist:
    def __init__(self,
                 namelist_path,
                 label=None,
                 verbose=False):
        self.namelist_path = namelist_path
        self.namelist = f90nml.read(namelist_path)
        self.label = label
        self.verbose = verbose

    def print_out(self, msg):
        if self.verbose:
            print(msg)

    def diff(self: 'NemoNamelist', reference: 'NemoNamelist'):

        diff_dict = {}

        # set labels for printout
        if self.label:
            nml_a = self.label
        else:
            nml_a = 'self'
        if reference.label:
            nml_b = reference.label
        else:
            nml_b = 'reference'

        diff_dict['A'] = nml_a
        diff_dict['B'] = nml_b

        # identifies keys in self but not in reference
        self.print_out("keys only in " + nml_a)
        ukeys = []
        ikeys = []
        for key in self.namelist.todict().keys():
            if key not in reference.namelist.todict().keys():
                ukeys.append(key)
                self.print_out(f"\t: {key}")
            else:
                ikeys.append(key)
        diff_dict['A:unique_p1'] = ukeys
        diff_dict['identical_p1'] = ikeys

        # identifies keys in reference but not in keys
        self.print_out("keys only in " + nml_b)
        ukeys = []
        for key in reference.namelist.todict().keys():
            if key not in self.namelist.todict().keys():
                ukeys.append(key)
                self.print_out(f"\t: {key}")
        diff_dict['B:unique_p1'] = ukeys

        for p1key in diff_dict['identical_p1']:

            # identify unique keys in A and identical keys in children
            self.print_out("sub-keys for '" + p1key + "' only in " + nml_a)
            ukeys = []
            ikeys = []
            for ckey in self.namelist[p1key].keys():
                if ckey not in reference.namelist[p1key].keys():
                    ukeys.append(ckey)
                    self.print_out(f"\t\t{p1key}: {ckey}")
                else:
                    ikeys.append(ckey)
            check_key(diff_dict, 'A:unique_p2', 'create')
            check_key(diff_dict, 'identical_p2', 'create')
            diff_dict['A:unique_p2'][p1key] = ukeys
            diff_dict['identical_p2'][p1key] = ikeys

            # identify unique key in children for B
            self.print_out("sub-keys for '" + p1key + "' only in " + nml_b)
            ukeys = []
            for ckey in reference.namelist[p1key].keys():
                if ckey not in self.namelist[p1key].keys():
                    ukeys.append(ckey)
                    self.print_out(f"\t\t{p1key}: {ckey}")
            check_key(diff_dict, 'B:unique_p2', 'create')
            diff_dict['B:unique_p2'][p1key] = ukeys

            # identify unique and equal keys in second level
            for p2key in diff_dict['identical_p2'][p1key]:
                if(type(self.namelist[p1key][p2key]) is f90nml.Namelist):
                    self.print_out("sub-sub-keys for '" + p1key + " -> " + p2key + "' only in " + nml_a)
                    ukeys = []
                    ikeys = []
                    for ckey in self.namelist[p1key][p2key].keys():
                        if ckey not in reference.namelist[p1key][p2key].keys():
                            ukeys.append(ckey)
                            self.print_out(f"\t\t\t{p1key}->{p2key}: {ckey}")
                        else:
                            ikeys.append(ckey)
                    check_key(diff_dict, 'A:unique_p3', 'create')
                    check_key(diff_dict, 'identical_p3', 'create')
                    check_key(diff_dict['A:unique_p3'], p1key, 'create')
                    check_key(diff_dict['identical_p3'], p1key, 'create')
                    diff_dict['A:unique_p3'][p1key][p2key] = ukeys
                    diff_dict['identical_p3'][p1key][p2key] = ikeys

                if(type(reference.namelist[p1key][p2key]) is f90nml.Namelist):
                    self.print_out("sub-sub-keys for '" + p1key + " -> " + p2key + "' only in " + nml_b)
                    ukeys = []
                    ikeys = []
                    for ckey in reference.namelist[p1key][p2key].keys():
                        if ckey not in self.namelist[p1key][p2key].keys():
                            ukeys.append(ckey)
                            self.print_out(f"\t\t\t{p1key}->{p2key}: {ckey}")
                        else:
                            ikeys.append(ckey)
                    check_key(diff_dict, 'B:unique_p3', 'create')
                    check_key(diff_dict['B:unique_p3'], p1key, 'create')
                    diff_dict['B:unique_p3'][p1key][p2key] = ukeys

            # compare settings
            diff_dict['diff'] = {}
            diff_dict['same'] = {}
            for p1key in diff_dict['identical_p2'].keys():
                for p2key in diff_dict['identical_p2'][p1key]:
                    if type(self.namelist[p1key][p2key]) is f90nml.Namelist:
                        for p3key in diff_dict['identical_p3'][p1key][p2key]:
                            if self.namelist[p1key][p2key][p3key] != reference.namelist[p1key][p2key][p3key]:
                                check_key(diff_dict['diff'], p1key, 'create')
                                check_key(diff_dict['diff'][p1key], p2key, 'create')
                                diff_dict['diff'][p1key][p2key][p3key] = [self.namelist[p1key][p2key][p3key],
                                                                          reference.namelist[p1key][p2key][p3key]]
                            else:
                                check_key(diff_dict['same'], p1key, 'create')
                                check_key(diff_dict['same'][p1key], p2key, 'create')
                                diff_dict['same'][p1key][p2key][p3key] = self.namelist[p1key][p2key][p3key]
                    else:
                        if self.namelist[p1key][p2key] != reference.namelist[p1key][p2key]:
                            check_key(diff_dict['diff'], p1key, 'create')
                            diff_dict['diff'][p1key][p2key] = [self.namelist[p1key][p2key],reference.namelist[p1key][p2key]]
                        else:
                            check_key(diff_dict['same'], p1key, 'create')
                            diff_dict['same'][p1key][p2key] = self.namelist[p1key][p2key]

        return diff_dict

    def apply(self, diff_dict: dict):
        if diff_dict['A'] != self.label:
            print(f"ERROR: labels of base namelists differ -> '{self.label}' != '{diff_dict['A']}'")
            return

        # apply changes to namelist
        for p1key in diff_dict['diff'].keys():
                for p2key in diff_dict['diff'][p1key].keys():
                    if type(diff_dict['diff'][p1key][p2key]) is dict:
                        for p3key in diff_dict['diff'][p1key][p2key].keys():
                            self.namelist[p1key][p2key][p3key] = diff_dict['diff'][p1key][p2key][p3key][1]
                    else:
                        self.namelist[p1key][p2key] = diff_dict['diff'][p1key][p2key][1]

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pass

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
