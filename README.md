##[CssCoco](https://github.com/boryanagoncharenko/CssCoco) Sublime Text 3 Plugin

###Installation:
1. Install [CssCoco](https://github.com/boryanagoncharenko/CssCoco#installation)
2. Add the plugin using [Package Control](https://packagecontrol.io/):
  * Open package control and choose `Package Control: Add repository`. Input the following link: `https://github.com/boryanagoncharenko/Sublime-CssCoco`
  * Open package control and choose `Package Control: Install Package`. Search for `Sublime-CssCoco` and install it.
3. Open the CssCoco settings file (`Cmd+Shift+,`) and set the `csscoco_path` to your `csscoco` executable path. Also, set the `conventions_file` variable to the path to your .coco file ([here](https://github.com/boryanagoncharenko/CssCoco/tree/master/samples) are some sample .coco files).

###Usage:
Open a .css file in Sublime Text 3 and hit `Cmd+Shift+C`. Similarly to other linter tools, rows that contain a violation will be marked with a border. When you place your cursor on a row with violation, the specific error message will appear in the statusbar.

By default CssCoco will lint every CSS file on file Save. You can change this option from the CssCoco settings file (`Cmd+Shift+,`).