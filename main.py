#!/bin/env python3

"""
                                                    .-"``"-.
                                                   /______; \
                                                  {_______}\|
                                                  (/ a a \)(_)
                                                  (.-.).-.)
    ________________________________________ooo__(    ^    )___________________________________________
   /                                              '-.___.-'                                            \
  | Usage                                                                                               |
  | ==================                                                                                  |
  |                                                                                                     |
  | (1) First create instances of Namelist for the namelists to compare:                                |
  |                                                                                                     |
  |     >>> nml_a = Namelist(<path to namelist A>, <label for namelist A>)                              |
  |                                                                                                     |
  |     >>> nml_b = Namelist(<path to namelist B>, <label for namelist B>)                              |
  |                                                                                                     |
  | (2) Create a diff from namelist A to B (what changed in B from A):                                  |
  |                                                                                                     |
  |     >>> dd_A_B = nml_a.diff(nml_b)                                                                  |
  |                                                                                                     |
  | (3) Apply the diff to namelist A                                                                    |
  |                                                                                                     |
  |     >>> nml_a.apply(dd_A_B)                                                                         |
  |                                                                                                     |
  | (4) Write the updated namelist                                                                      |
  |                                                                                                     |
  |     >>> nml_a.write()                                                                               |
  |                                                                                                     |
  |     if the comments shall be preserved, do:                                                         |
  |                                                                                                     |
  |     >>> nml_a.write(patch=True)                                                                     |
  |                                                                                                     |
  |     (no worries, the old namelist is copied to '<namlist path>.bak' before the changes are applied) |
  |                                                                                                     |
  | note:                                                                                               |
  |                                                                                                     |
  |   Namelist.diff() returns a NamelistDiff object with the following attribute                        |
  |                                                                                                     |
  |   - 'A'             : label of namelist A                                                           |
  |   - 'B'             : label of namelist B                                                           |
  |   - 'A_unique'      : unique keys in A for depth=i (p[i])                                           |
  |   - 'B_unique'      : unique keys in B for depth=i (p[i])                                           |
  |                                                                                                     |
  |   - 'diff'          : different values for identical keys for depth=i (p[i])                        |
  |   - 'equal'         : equal values for identical keys for depth=i (p[i])                            |
   \________________________________________________________ooo________________________________________/
                                                 |_  |  _|  jgs
                                                 \___|___/
                                                 {___|___}
                                                  |_ | _|
                                                  /-'Y'-\
                                                 (__/ \__)        [Created with boxes -d santa]

"""
import uuid
import json
from pathlib import Path
from typing import Union, Tuple
from dataclasses import dataclass, field

import yaml
import f90nml
import pandas as pd


class Namelist:
    def __init__(self,
                 namelist_path: Union[str, Path],
                 label: Union[None, str] = None):
        self.namelist_path = Path(namelist_path)
        self.namelist = f90nml.read(self.namelist_path)
        self.label = label

    def apply(self, diff_dict: dict) -> None:
        if diff_dict.A != self.label:
            raise ValueError(
                "Labels of base namelists differ -> "
                f"'{self.label}' != '{diff_dict.A}'"
            )

        # apply changes to namelist
        for changes in diff_dict.diff.values():
            Namelist._update_nml(self.namelist, changes)

    def diff(self: 'Namelist', reference: 'Namelist') -> 'NamelistDiff':
        """Compute the difference between current Namelist and other"""

        diff = NamelistDiff(
            A=getattr(self, "label", "self"),
            B=getattr(reference, "label", "reference")
        )

        self._compare_dicts(
            self.namelist.todict(),
            reference.namelist.todict(),
            diff)

        return diff

    def write(self,
              out: Union[str, Path, None] = None,
              patch: bool = False,
              overwrite: bool = False
              ) -> None:
        """
        Write namefile to a file.

        Parameter
        ---------
        out: str or pathlib.Path or None (optional)
            Name of the output file. If not given objects namelist_path
            attribute will be used. Default is None.
        patch: bool (optional)
            If True will writte the file using patch method and original
            file. This keeps the comments in the file. Default is False.
        overwrite: bool (optional)
            If False and output file exists the original file will be
            move with '.bak' extension. If True and any file with the
            same name will be removed. Default is False.

        """
        # make a backup of old namelists
        if out is None:
            out = self.namelist_path
        else:
            out = Path(out)

        if out.exists() and not overwrite:
            path = out.parent
            name = out.name
            cpy = name + ".0.bak"
            for i in range(1001):
                if (path / cpy).exists():
                    cpy = name + f".{i+1}.bak"
                else:
                    break

            if i == 1000:
                raise ValueError(f"Too many copies [{i}]")

            old_file_path = path / cpy
            print(f"copy {out} to {old_file_path}")
            out.rename(old_file_path)
        else:
            old_file_path = self.namelist_path

        # write namelist
        if patch:
            if out == old_file_path:
                tmp_fn = str(uuid.uuid4())
                f90nml.patch(old_file_path, self.namelist, tmp_fn)
                old_file_path.unlink()
                tmp_fn.rename(out)
            else:
                f90nml.patch(old_file_path, self.namelist, out)
        else:
            self.namelist.write(out, force=True)

    @staticmethod
    def _compare_dicts(self_nml: dict, ref_nml: dict, diff: 'NamelistDiff',
                       i: int = 0, path: list = []) -> None:
        """
        Compare the keys and values between two dictionaries and update
        a NamelistDiff object
        """
        u_self, u_ref, common = Namelist._compare_keys(self_nml, ref_nml)
        Namelist._update_dict(diff.A_unique, [i]+path, list(u_self))
        Namelist._update_dict(diff.B_unique, [i]+path, list(u_ref))
        for key in common:
            new_path = path + [key]
            if isinstance(self_nml[key], dict):
                # keep entering a nested level
                Namelist._compare_dicts(
                    self_nml[key], ref_nml[key], diff, i+1, new_path)
            else:
                # compare values
                Namelist._compare_values(
                    self_nml[key], ref_nml[key], diff, i, new_path)

    @staticmethod
    def _compare_keys(self_nml: dict, ref_nml: dict) -> Tuple[set, set, set]:
        """Return unique elements in each dictionary and the commo ones"""
        self_keys = set(self_nml)
        ref_keys = set(ref_nml)
        return (
            self_keys.difference(ref_keys),
            ref_keys.difference(self_keys),
            self_keys.intersection(ref_keys)
        )

    @staticmethod
    def _compare_values(self_val: object, ref_val: object,
                        diff: 'NamelistDiff', i: int = 0,
                        path: list = []) -> None:
        """Compare two values from a namelist"""
        if self_val == ref_val:
            Namelist._update_dict(
                diff.equal, [i]+path, self_val)
        else:
            Namelist._update_dict(
                diff.diff, [i]+path, [self_val, ref_val])

    @staticmethod
    def _update_dict(indict: dict, path: list, value: list) -> None:
        """Update dictionary addying new entries if needed"""
        cdict = indict
        if not value:
            return
        for key in path[:-1]:
            if key not in cdict:
                cdict[key] = {}
            cdict = cdict[key]

        cdict[path[-1]] = value

    @staticmethod
    def _update_nml(nml: f90nml.namelist.Namelist, changes: dict):
        """Update the namelist with the changes dictionary"""
        for key, value in changes.items():
            if isinstance(value, dict):
                Namelist._update_nml(nml[key], value)
            else:
                nml[key] = value[1]


@dataclass
class NamelistDiff:
    A: str
    B: str
    A_unique: dict = field(default_factory=dict)
    B_unique: dict = field(default_factory=dict)
    equal: dict = field(default_factory=dict)
    diff: dict = field(default_factory=dict)

    def __str__(self) -> str:
        out = f"\nKeys only in '{self.A}'\n"
        out += self.yaml_dump(self.A_unique)
        out += f"\n\nKeys only in '{self.B}'\n"
        out += self.yaml_dump(self.B_unique)
        out += "\n\nIdentical values\n"
        out += self.yaml_dump(self.equal)
        out += "\n\nDifferent values\n"
        out += self.yaml_dump(self.diff)
        return out

    def yaml_dump(self, dict: dict = None, **kwargs) -> str:
        """
        Dump data as yaml

        Parameters
        ----------
        dict: dict or None
            Dictionary to dump. If none the whole object will be dumped.
        kwargs:
            yaml.dump kwargs.

        Returns
        -------
        str

        """
        if dict:
            return yaml.dump(dict, **kwargs)
        else:
            return yaml.dump(self.__dict__, **kwargs)

    def json_dump(self, dict: dict = None, **kwargs) -> str:
        """
        Dump data as json

        Parameters
        ----------
        dict: dict or None
            Dictionary to dump. If none the whole object will be dumped.
        kwargs:
            json.dump kwargs.

        Returns
        -------
        str

        """
        if dict:
            return json.dumps(dict, **kwargs)
        else:
            return json.dumps(self.__dict__, **kwargs)

    def to_spreadsheet(self, out: Union[str, Path]) -> None:
        """
        Save the difference information in an spreadsheet file

        Parameters
        ----------
        out: str or pathlib.Path
            Name of the output file to save

        """
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(out, engine='xlsxwriter')

        # Write each dataframe to a different worksheet.
        self._convert_to_df(self.A_unique, 0).to_excel(
            writer, sheet_name=f'{self.A} unique')
        self._convert_to_df(self.B_unique, 0).to_excel(
            writer, sheet_name=f'{self.B} unique')
        self._convert_to_df(self.equal, 1).to_excel(
            writer, sheet_name='equal')
        self._convert_to_df(self.diff, 2).to_excel(
            writer, sheet_name='diff')

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

    def _convert_to_df(self, indict: dict, n_values: int) -> pd.DataFrame:
        out = []
        for val in indict.values():
            out += NamelistDiff._to_lists(val, max(indict), n_values)

        df = pd.DataFrame(out)
        if n_values == 0:
            df.columns = [f"level {i}" for i in range(len(df.columns))]
        elif n_values == 1:
            df.columns = [f"level {i}" for i in range(len(df.columns)-1)]\
                + ["value"]
        else:
            df.columns = [f"level {i}" for i in range(len(df.columns)-2)]\
                + [self.A, self.B]

        return df

    @staticmethod
    def _to_lists(indict: dict, n: int, n_values: int) -> list:
        if isinstance(indict, dict):
            outs = []
            for key, values in indict.items():
                out = NamelistDiff._to_lists(values, n-1, n_values)
                outs += [[key] + val for val in out]
            return outs
        elif n_values == 0:
            return [[val] + [None]*n for val in indict]
        elif n_values == 1:
            return [[None]*(n+1)+[indict]]
        else:
            return [[None]*(n+1)+indict]


if __name__ == '__main__':
    pass
