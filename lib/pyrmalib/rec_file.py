"""
       Copyright 2022 Sergey Utkin utkins01@gmail.com

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import sys
import os
import ast

# key UP, DOWN, PAGE UD|DOWN, TAB
NO_ACTION_KEYS = ['\x1bOB', '\x1bOA', '\x1b[6~', '\x1b[5~', '\t', '\x04', '\x1b[B', '\x1b[A', '\x1bOH', '\x1b', '\x0f']

class RecFile:
    stdin = []

    def __init__(self, filename):
        self.stdin = []
        if not os.path.isfile(filename):
            raise OSError('RecFile: filename is not regular file')
        f = open(filename, 'r')
        for line in f:
            line = ast.literal_eval(line)
            if isinstance(line, list) and line[1] == "i":
                self.stdin.append(line[2])

    def stdin_to_line(self):
        lines = []
        cursor = 0
        line = []
        try: 
            for elem in self.stdin:
                if elem == '\r':
                    if len(line) != 0:
                        lines.append("".join(line))
                        line.clear()
                        cursor = 0
                elif elem == '\x1b[H':                      # key HOME
                    cursor = 0
                elif elem in NO_ACTION_KEYS:
                    pass
                elif elem == '\x1b[F':                      # key END
                    cursor = len(line)
                elif elem == '\x1b[D':                      # key LEFT
                    if cursor > 0:
                        cursor -= 1
                elif elem == '\x1b[C':                      # key RIGHT
                    if cursor < len(line):
                        cursor += 1
                elif elem == '\x7f':                        # key BACKSPACE
                    if len(line) > 0:
                        line.pop(cursor - 1)
                        cursor -= 1
                elif elem == '\x1b[3~':                     # key DELETE
                    line.pop(cursor)
                else:
                    for ch in elem:
                        line.insert(cursor, ch)
                        cursor += 1
            return "\n".join(lines)
        except:
            return "ERROR: Ошибка выполнения анализа файла."

    def __repr__(self):
        return "{0}".format(self.__dict__)


if __name__ == '__main__':
    f = RecFile(sys.argv[1])
    print(f.stdin_to_line())
