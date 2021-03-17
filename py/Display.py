#
# Copyright 2021  Janick Bergeron <janick@bergeron.com>                                                                                                                             
#
# Licensed under the Apache License, Version 2.0 (the "License");                                                                                                                   
# you may not use this file except in compliance with the License.                                                                                                                  
# You may obtain a copy of the License at                                                                                                                                           
#
#    http://www.apache.org/licenses/LICENSE-2.0                                                                                                                                     
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,                                                                                                                 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                                                                                          
# See the License for the specific language governing permissions and                                                                                                               
# limitations under the License.
#

import tkinter as tk


class Display(tk.Tk):

    def __init__(self, height, width):
        super().__init__()
        self.topHalfFrame    = tk.Frame(master=self, relief=tk.RIDGE, height=height*2/3, width=width, borderwidth=5)
        self.bottomHalfFrame = tk.Frame(master=self, relief=tk.RIDGE, height=height*1/3, width=width, borderwidth=5)

        self.topHalfFrame.pack()
        self.bottomHalfFrame.pack()


window = Display(800, 1400)
window.mainloop()

