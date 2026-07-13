# Damien's Folder

## What are the files doing 

### Main.py
Main.py is simply the file that pilots all the other files. 
The program must be launched from main.py

### Physics.py
Physics.py is the file where I added most of the constants and variables related to the chopper experiment.
I defined the functions that allow the calculations of the flux and all the corrections related to it.
I then added all type of functions that can calculate uncertainties, cross sections...

### Plot.py
Plot.py is the file where I created all the functions that allow me to plot the different graphs.

### Gui.py
Gui.py is the graphical user interface file where I can modify all the different features on the gui. (file download / buttons / tools)

### Config.py
Config.py allow me to add parameters that I wish to be modified by the operator inside the gui.

### Utils.py
Utils.py is the file where I define all the functions that are not directly related to the plot of graphs but rather tools or functionalities that can be used inside the gui (save file / export file...).

### Physics_NAA.py
Physics_NAA.py is the same as physics.py but for the Neutron Activation Analysis.

### Plot_NAA.py
Plot_NAA.py is the same as plot.py but for the Neutron Activation Analysis.

## How does the GUI works ?

### Load files :
You have to press "Load data files", then you can select as many files as you want but they must be data files that only contain 2 columns of data, otherwise it will not be loaded.

### Plot graphs : 
Once the files are loaded, you can select the files you want to be used for a specific plot. To do that you press the files in a dedicated order by using Ctrl. 

For plot 7 to 8 : Only the first file is ploted
For plot 10 : Select the file from the lowest reactor power to the highest.
For plot 11 : The first on is the data file of the experiment without sample.

### Parameters : 
You can go on the second page named "Physical Parameters" that allows you to modify the thickness and atom density of the sample used for the cross section (plot 11).
You can also modify the limits in time and energy. Useful to set borders for the fits (plot 5 to 8).

### Displays limits : 
Those cursors affect only the display of the graphs. You can increase or decrease the scale on the x and y axes.

### Buttons :
- Load Data files : select the wanted files to be loaded (2 columns max)

- Clear cache / reset : Delete the cache and all the loaded files

- Analysis selection : select the wanted graph to be ploted

- Plot : press the button to display the graph selected in analysis selection

- Clear : clear the current graph

- Quit Application : quit the application

- History : select a previous graph to be shown again
