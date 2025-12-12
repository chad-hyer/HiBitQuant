# HiBitQuant
<p align="center" style="font-size: 24px">
    <img src="https://github.com/chad-hyer/HiBitQuant/blob/cff8dff6f31388c03381d588144c448caf0aa5d7/src/icon.png" alt="HiBitQuant Logo" width="75" height="575">
    <br>
    <b>HiBitQuant</b>
</p>

HiBitQuant is a software tool for quantifying protein concentrations of HiBit-tagged proteins using luminescence kinetics experiments from Synergy plate readers. It directly takes these plate reader outputs and allows the user to specify condition information using a GUI. HiBitQuant then graphs the kinetic traces and quantifies protein concentrations based on predefined standard curves. HiBitQuant also has built in tools for creating new standard curves.

## Authors

[Chad D. Hyer](https://www.linkedin.com/in/chadhyer), [Michael C. Jewett](https://www.linkedin.com/in/michael-jewett-751a792/)

## Acknowledgements

Stanford University Department of Bioengineering

Michael Jewett Lab

Disclaimer: Gemini was used in the creation of the GUI.

## Contact

For inquiries about HiBitQuant or to request additional intormation, please use our GitHub or direct inquiries to chadhyer@stanford.edu. We will do our best to respond in a timely fashion, so you can use our software for your needs.

## Instructions

HiBit Quant runs as a standalone executable that was compiled using PyInstaller. Download the correct vesion of HiBitQuant from [Releases](https://github.com/chad-hyer/HiBitQuant/releases) that matches your OS. Alternatively, you can run ```HiBitQuant.py``` found in the ```src``` directory using a dedicated python environment included in [these instructions](https://github.com/chad-hyer/HiBitQuant/blob/main/src/building_hibit_gui.md). When running ```HiBitQuant.exe``` ensure that the included ```resources``` directory is contained in the same directory as ```HiBitQuant.exe``` to ensure all features are available. Once set up, HiBitQuant follows this workflow:
1. Perform HiBit quantification using the attached [SOP](https://github.com/chad-hyer/HiBitQuant/blob/main/resources/HiBit%20Quantification%20SOP.docx).
2. Load raw ```.csv``` or ```.xlsx``` file as exported from Biotek/Synergy.
3. Select the plate layout (384 or 96 well plate).
4. Specify conditions' information. This is done by selecting wells, assigning a condition name, a dilution factor (optional), and concentration value (optional). Multiple selected wells in a condition will be used as replicates and will impact downstream calculations. Including a dilution factor allows for the autocalculation of stock concentrations, and including concentrations allows for the plotting of standard curves in the ```Visualize``` tab. Both are optional. Alternatively, a guide file can be imported to automatically assign values to wells based on a [guide file]([https://github.com/chad-hyer/HiBitQuant/blob/528387ac9e6308886c10ec8a629108176090f9ab/resources/condition_guide_template.xlsx](https://github.com/chad-hyer/HiBitQuant/blob/main/resources/condition_guide_template.xlsx)).
5. Inspect kinetic traces in ```Visualize```. Standard curves and kinetic trace data and figures can be exported on this tab.
6. In ```Quantification```, specify the standard curve that will be used to calculate concentration values. Standard curves are contained in ```HiBit_quant_standard_curve.csv``` found in ```resources```. You may alternatively define a custom standard curve in the GUI or add new ones to ```HiBit_quant_standard_curve.csv```.
7. Figures in ```Quantification``` can be modified or exported using the options in the menus. ```Range Alerts``` can be included to indicate if a measured value is outside of the dynamic range of a standard curve, and dilution factors can be used to plot stock concentrations rather than calculated values. All calculations can also be exported by clicking ```Export Quant Data```.
