# Creating a HiBitQuant Executable from Source Files

HiBitQuant is distributed as a compiled executable file to properly manage dependencies, but we recognize that you may want to make edits to HiBitQuant yourself. This can be accomplished by editing ```HiBitQuant.py```. After editing, however, it is recommended to recompile an executable for ease of distribution. This can be accomplished using an Python virtual environment and PyInstaller. Follow the steps below to accomplish this:

## Compiling HiBitQuant
1. Create Python virtual environment using the command ```python -m venv hibit_quant```.
2. Activate your virutal environment using ```activate``` in ```hibit_quant/Scripts```.
3. Install the correct dependencies found in ```hibit_requirements.txt``` plus any you may have added using the command ```pip install -r hibit_requirements.txt```.
4. Install PyInstaller using the command  ```pip install pyinstaller```.
5. Navigate to the directory containing ```hibit_gui.py``` and ensure that the ```resources``` folder and ```icon.ico``` are present in the same directory. You must also have ```build.spec``` in the same directory.
6. Compile the exe using the command ```pyinstaller hibit_build.spec --clean --noconfirm```
7. ```HiBitQuant.exe``` should now be in the ```dist``` folder. Include it along with the ```resources``` folder in the same directory, and it should be safe to execute.

Full list of commands:
```
python -m venv hibit_quant
cd hibit_quant/Scripts
activate
cd ..
cd ..
pip install -r hibit_requirements.txt
pip install pyinstaller
pyinstaller hibit_build.spec --clean --noconfirm
```

## Note for using operating systems other than Windows
You may need to tweak these commands or build files of you are compiling an executable in Mac or Linux. This repository was optimized for Windows machines.