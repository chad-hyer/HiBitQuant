# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 16:43:05 2025

@author: hyerc

Primarily generated using Gemini
"""
import sys
import csv
import pandas as pd
import numpy as np
import matplotlib
import re
import os
from scipy.stats import linregress
matplotlib.use('QtAgg')

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                               QStackedWidget, QComboBox, QLineEdit, QGridLayout,
                               QFrame, QMessageBox, QScrollArea, QSplitter, QGroupBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
                               QSizePolicy, QSpacerItem, QCheckBox)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QColor, QPainter, QAction, QIcon, QFont, QPalette, QBrush, QPen

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtGui import QPixmap
from matplotlib.figure import Figure
import seaborn as sns

# --- Constants ---
COLORS = [
    '#2563eb', '#dc2626', '#16a34a', '#d97706', '#9333ea', 
    '#db2777', '#0891b2', '#84cc16', '#4b5563', '#000000',
    '#e11d48', '#059669', '#7c3aed', '#ea580c', '#0284c7',
    '#65a30d', '#be123c', '#4f46e5', '#b45309', '#334155'
]

# --- Data Logic ---

class DataParser:
    @staticmethod
    def parse_file(filepath):
        try:
            if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
                df_raw = pd.read_excel(filepath, header=None)
                rows = df_raw.values.tolist()
            else:
                with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
                    reader = csv.reader(f)
                    rows = list(reader)

            all_data = []
            well_pat = re.compile(r'^[A-P][0-9]{1,2}$')
            
            i = 0
            while i < len(rows):
                row = [str(x).strip() for x in rows[i]]
                
                # Check Column 1 for 'Time'
                is_time_row = False
                if len(row) > 1 and (row[1].lower() == 'time' or 'time' in row[1].lower()):
                    is_time_row = True
                
                if is_time_row:
                    has_well_headers = any(well_pat.match(col) for col in row)

                    if has_well_headers:
                        header = row
                        block_data = []
                        i += 1
                        
                        while i < len(rows):
                            data_row = rows[i]
                            if not data_row or len(data_row) < 2 or not str(data_row[1]).strip():
                                break
                            
                            try:
                                data_row = [str(x).strip() for x in data_row]
                                time_val = DataParser.parse_time(str(data_row[1]))
                                
                                row_dict = {'Time': time_val}
                                for idx, val in enumerate(data_row):
                                    if idx < len(header):
                                        well = header[idx]
                                        if well and well_pat.match(well): 
                                            try:
                                                row_dict[well] = float(val)
                                            except:
                                                row_dict[well] = np.nan
                                block_data.append(row_dict)
                                i += 1
                            except ValueError:
                                break
                        
                        if block_data:
                            all_data.extend(block_data)
                    else:
                        i += 1
                else:
                    i += 1

            if not all_data:
                raise ValueError("No valid data blocks found. Ensure the file contains 'Time' in the second column (Column B) followed by Well IDs.")

            df = pd.DataFrame(all_data)
            df = df.groupby('Time').first().reset_index()
            df = df.sort_values('Time')
            
            return df

        except Exception as e:
            raise e

    @staticmethod
    def parse_time(time_str):
        s = str(time_str).strip()
        if ':' in s:
            parts = list(map(float, s.split(':')))
            if len(parts) == 3: 
                return parts[0]*60 + parts[1] + parts[2]/60
            elif len(parts) == 2:
                return parts[0]*60 + parts[1]
        return float(s)

# --- Custom Widgets ---

class WellButton(QWidget):
    def __init__(self, well_id, size=30):
        super().__init__()
        self.well_id = well_id
        self.setFixedSize(size, size)
        self.is_selected = False
        self.is_valid = True # Default to valid until data proves otherwise
        self.color = None
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(well_id)

    def set_valid(self, valid):
        self.is_valid = valid
        if not valid:
            self.setCursor(Qt.ForbiddenCursor)
            self.setToolTip(f"{self.well_id} (No Data)")
            self.set_selected(False)
            self.set_color(None)
        else:
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip(self.well_id)
        self.update()

    def set_color(self, color):
        self.color = color
        self.update()

    def set_selected(self, selected):
        if not self.is_valid: return 
        self.is_selected = selected
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        
        # Determine Visual State
        if not self.is_valid:
            # INVALID / NO DATA STATE
            painter.setBrush(QColor("#e5e7eb")) 
            painter.setPen(QColor("#9ca3af")) 
            painter.drawRect(rect)
            
            # Draw 'X' Cross
            pen = QPen(QColor("#9ca3af"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(rect.topLeft(), rect.bottomRight())
            painter.drawLine(rect.topRight(), rect.bottomLeft())
            
        elif self.color:
            # ASSIGNED STATE
            painter.setBrush(QColor(self.color))
            painter.setPen(Qt.NoPen)
            painter.drawRect(rect)
        else:
            # DEFAULT EMPTY STATE
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(QColor("#a0a0a0"))
            painter.drawRect(rect)

        # SELECTION HIGHLIGHT
        if self.is_selected and self.is_valid:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QColor("#000000"))
            pen = painter.pen()
            pen.setWidth(3) # Thicker border for better visibility
            painter.setPen(pen)
            painter.drawRect(rect)

class PlateMapWidget(QWidget):
    selection_changed = Signal(list) 

    def __init__(self, format=96):
        super().__init__()
        self.format = format
        self.layout = QGridLayout(self)
        self.layout.setSpacing(2)
        self.wells = {} 
        self.selected_wells = set()
        self.valid_wells = None
        self.is_dragging = False
        self.drag_target_state = True 
        self.rebuild_grid()

    def set_valid_wells(self, valid_wells_list):
        """Updates which wells are clickable based on data presence."""
        self.valid_wells = set(valid_wells_list) if valid_wells_list is not None else None
        
        for well_id, btn in self.wells.items():
            if self.valid_wells is None:
                btn.set_valid(True)
            else:
                # If well ID is in our list of valid data columns, it's valid.
                btn.set_valid(well_id in self.valid_wells)
        
        self.update() # Force repaint

    def rebuild_grid(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.wells = {}
        self.selected_wells.clear()

        rows = 8 if self.format == 96 else 16
        cols = 12 if self.format == 96 else 24
        size = 32 if self.format == 96 else 20
        font_size = 10 if self.format == 96 else 8

        # Headers
        for c in range(cols):
            lbl = QLabel(str(c+1))
            lbl.setAlignment(Qt.AlignCenter)
            font = QFont("Arial", font_size)
            font.setBold(True)
            lbl.setFont(font)
            self.layout.addWidget(lbl, 0, c+1)

        for r in range(rows):
            letter = chr(65 + r)
            lbl = QLabel(letter)
            lbl.setAlignment(Qt.AlignCenter)
            font = QFont("Arial", font_size)
            font.setBold(True)
            lbl.setFont(font)
            self.layout.addWidget(lbl, r+1, 0)

            for c in range(cols):
                well_id = f"{letter}{c+1}"
                btn = WellButton(well_id, size)
                if self.valid_wells is not None:
                    btn.set_valid(well_id in self.valid_wells)
                self.layout.addWidget(btn, r+1, c+1)
                self.wells[well_id] = btn

    def set_selection(self, well_ids):
        """Programmatically select specific wells."""
        self.clear_selection()
        for wid in well_ids:
            if wid in self.wells and self.wells[wid].is_valid:
                self.wells[wid].set_selected(True)
                self.selected_wells.add(wid)
        self.selection_changed.emit(list(self.selected_wells))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            w = self.childAt(event.position().toPoint())
            if isinstance(w, WellButton) and w.is_valid:
                # Toggle logic: If clicking a selected well, target is deselect.
                self.drag_target_state = not w.is_selected
                self._set_well_state(w, self.drag_target_state)
            else:
                # Clicking empty space doesn't clear in this logic to allow
                # easier multi-select, but we can refine if needed.
                if not isinstance(w, WellButton):
                   self.clear_selection()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            w = self.childAt(event.position().toPoint())
            if isinstance(w, WellButton) and w.is_valid:
                self._set_well_state(w, self.drag_target_state)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.selection_changed.emit(list(self.selected_wells))

    def _set_well_state(self, btn, state):
        if state:
            self.selected_wells.add(btn.well_id)
            btn.set_selected(True)
        else:
            if btn.well_id in self.selected_wells:
                self.selected_wells.remove(btn.well_id)
            btn.set_selected(False)

    def clear_selection(self):
        for wid in list(self.selected_wells):
            self.wells[wid].set_selected(False)
        self.selected_wells.clear()
        self.selection_changed.emit([])

    def assign_color(self, well_ids, color):
        for wid in well_ids:
            if wid in self.wells:
                self.wells[wid].set_color(color)

    def set_format(self, fmt):
        if self.format != fmt:
            self.format = fmt
            self.rebuild_grid()


# --- Main Application Logic ---

class HiBitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HiBit Quant")
        self.setWindowIcon(QIcon('resources/icon.png'))
        self.resize(1300, 850)

        # State
        self.df = None
        self.conditions = [] 
        self.color_idx = 0
        self.standard_curves = {} # Dict to store curve metadata
        self.editing_condition_index = None # Track if we are in edit mode

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Navbar
        self.setup_header()

        # Stacked Pages
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.setup_upload_page()
        self.setup_map_page()
        self.setup_plot_page()
        self.setup_quant_page()

        # Load standard curves if available
        self.load_standard_curves()

    def setup_header(self):
        header = QFrame()
        header.setFrameShape(QFrame.HLine)
        header.setFrameShadow(QFrame.Sunken)
        
        container = QWidget()
        header_layout = QHBoxLayout(container)
        header_layout.setContentsMargins(0,0,0,10)
        
        title = QLabel("HiBit Quant")
        logo = QLabel()
        image = QPixmap("resources/icon.png").scaled(
            QSize(30,30),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation)
        logo.setPixmap(image)
        font = QFont("Arial", 14)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        
        header_layout.addStretch()

        self.btn_nav_upload = QPushButton("1. Upload")
        self.btn_nav_map = QPushButton("2. Map Plate")
        self.btn_nav_plot = QPushButton("3. Visualize")
        self.btn_nav_quant = QPushButton("4. Quantification")
        
        self.nav_btns = [self.btn_nav_upload, self.btn_nav_map, self.btn_nav_plot, self.btn_nav_quant]
        for btn in self.nav_btns:
            btn.setCheckable(True)
            btn.clicked.connect(self.navigate)
            header_layout.addWidget(btn)
        
        self.main_layout.addWidget(container)
        self.main_layout.addWidget(header)
        self.btn_nav_upload.setChecked(True)

    def navigate(self):
        sender = self.sender()
        if sender == self.btn_nav_upload:
            self.stack.setCurrentIndex(0)
        elif sender == self.btn_nav_map:
            if self.df is None:
                QMessageBox.warning(self, "Data Missing", "Please upload a file first.")
                self.btn_nav_upload.setChecked(True)
                sender.setChecked(False)
                return
            self.stack.setCurrentIndex(1)
        elif sender == self.btn_nav_plot:
            if not self.conditions:
                QMessageBox.warning(self, "Conditions Missing", "Please define at least one condition.")
                self.btn_nav_map.setChecked(True)
                sender.setChecked(False)
                return
            self.update_plots()
            self.stack.setCurrentIndex(2)
        elif sender == self.btn_nav_quant:
            if not self.conditions:
                QMessageBox.warning(self, "Conditions Missing", "Please define conditions first.")
                self.btn_nav_map.setChecked(True)
                sender.setChecked(False)
                return
            self.update_quant_table()
            self.update_quant_plot() # Initial plot update
            self.stack.setCurrentIndex(3)
        
        for b in self.nav_btns:
            if b != sender: b.setChecked(False)

    # --- Page 1: Upload ---
    def setup_upload_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        
        group = QGroupBox("Import Data")
        group.setFixedSize(500, 300)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(20)
        group_layout.addStretch()
        
        lbl = QLabel("Supports .csv and .xlsx from Biotek/Synergy")
        lbl.setAlignment(Qt.AlignCenter)
        
        btn = QPushButton("Browse Files")
        btn.setFixedSize(150, 40)
        btn.clicked.connect(self.browse_file)
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setAlignment(Qt.AlignCenter)
        
        group_layout.addWidget(lbl)
        group_layout.addWidget(btn, 0, Qt.AlignCenter) 
        group_layout.addWidget(self.file_label)
        group_layout.addStretch()
        
        h_layout.addWidget(group)
        h_layout.addStretch()
        layout.addStretch()
        layout.addLayout(h_layout)
        layout.addStretch()

        self.stack.addWidget(page)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", "Data Files (*.csv *.xlsx *.txt)")
        if path:
            try:
                self.df = DataParser.parse_file(path)
                self.file_label.setText(f"Loaded: {path.split('/')[-1]}")
                palette = self.file_label.palette()
                palette.setColor(QPalette.WindowText, Qt.darkGreen)
                self.file_label.setPalette(palette)
                
                # --- Valid Well Detection ---
                non_na_counts = self.df.notna().sum(axis=0)
                valid_columns = non_na_counts[non_na_counts > 0].index.tolist()
                valid_wells = [str(w) for w in valid_columns if w != 'Time']
                
                # --- Auto-detect Plate Format ---
                is_384 = False
                for w in valid_wells:
                    match = re.match(r'^([A-Z])([0-9]+)$', w)
                    if match:
                        row_letter = match.group(1)
                        col_num = int(match.group(2))
                        if row_letter > 'H' or col_num > 12:
                            is_384 = True
                            break

                self.plate_widget.set_valid_wells(valid_wells)
                
                target_index = 1 if is_384 else 0
                if self.combo_fmt.currentIndex() != target_index:
                    self.combo_fmt.setCurrentIndex(target_index)
                
                fmt_str = "384-Well" if is_384 else "96-Well"
                QMessageBox.information(self, "Success", f"Parsed {len(self.df)} time points.\nFound {len(valid_wells)} valid wells (with data).\nDetected: {fmt_str}")
                
                self.stack.setCurrentIndex(1)
                self.btn_nav_map.setChecked(True)
                self.btn_nav_upload.setChecked(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to parse file:\n{str(e)}")

    # --- Page 2: Map ---
    def setup_map_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)

        left_panel = QGroupBox("Plate Layout")
        left_layout = QVBoxLayout(left_panel)
        
        controls_layout = QHBoxLayout()
        lbl_fmt = QLabel("Format:")
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["96 Well", "384 Well"])
        self.combo_fmt.currentIndexChanged.connect(self.change_plate_format)
        
        self.btn_import_guide = QPushButton("Import Guide File")
        self.btn_import_guide.clicked.connect(self.import_guide_file)

        controls_layout.addWidget(lbl_fmt)
        controls_layout.addWidget(self.combo_fmt)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_import_guide)
        
        left_layout.addLayout(controls_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        wrapper = QWidget()
        wrapper_layout = QGridLayout(wrapper) 
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.plate_widget = PlateMapWidget(96)
        self.plate_widget.selection_changed.connect(self.update_selection_info)
        
        wrapper_layout.addWidget(self.plate_widget, 0, 0, Qt.AlignCenter)
        scroll.setWidget(wrapper)
        
        left_layout.addWidget(scroll)

        right_panel = QGroupBox("Condition Settings")
        right_panel.setFixedWidth(350)
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel("Condition Name:"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Drug A")
        right_layout.addWidget(self.input_name)

        # --- Added Dilution Factor Input ---
        right_layout.addWidget(QLabel("Dilution Factor (Optional):"))
        self.input_dilution = QLineEdit()
        self.input_dilution.setPlaceholderText("Default: 1.0")
        right_layout.addWidget(self.input_dilution)
        # -----------------------------------

        right_layout.addWidget(QLabel("Concentration (µg/mL) (Optional):"))
        self.input_conc = QLineEdit()
        self.input_conc.setPlaceholderText("Optional (for Dose-Response plot only)")
        right_layout.addWidget(self.input_conc)

        # Button Stack for Assign vs Save/Cancel
        self.btn_stack = QStackedWidget()
        
        # Mode 0: Add Mode
        self.page_add = QWidget()
        l_add = QVBoxLayout(self.page_add)
        l_add.setContentsMargins(0,0,0,0)
        self.btn_assign = QPushButton("Assign Selection")
        self.btn_assign.clicked.connect(self.assign_condition)
        l_add.addWidget(self.btn_assign)
        
        # Mode 1: Edit Mode
        self.page_edit = QWidget()
        l_edit = QHBoxLayout(self.page_edit)
        l_edit.setContentsMargins(0,0,0,0)
        self.btn_save_edit = QPushButton("Save Changes")
        self.btn_save_edit.clicked.connect(self.save_edited_condition)
        self.btn_cancel_edit = QPushButton("Cancel")
        self.btn_cancel_edit.clicked.connect(self.cancel_edit_mode)
        l_edit.addWidget(self.btn_save_edit)
        l_edit.addWidget(self.btn_cancel_edit)
        
        self.btn_stack.addWidget(self.page_add)
        self.btn_stack.addWidget(self.page_edit)
        
        right_layout.addWidget(self.btn_stack)

        self.lbl_sel_count = QLabel("0 wells selected")
        self.lbl_sel_count.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_sel_count)
        
        right_layout.addSpacing(20)
        right_layout.addWidget(QLabel("Defined Conditions:"))
        
        self.condition_list = QTableWidget()
        self.condition_list.setColumnCount(5) # Increased column count
        self.condition_list.setHorizontalHeaderLabels(["Name", "Dilution", "Conc", "Edit", "Del"]) # Updated Headers
        header = self.condition_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.condition_list.verticalHeader().setVisible(False)
        self.condition_list.setSelectionBehavior(QTableWidget.SelectRows)
        
        right_layout.addWidget(self.condition_list)

        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        self.stack.addWidget(page)

    def change_plate_format(self, index):
        fmt = 96 if index == 0 else 384
        self.plate_widget.set_format(fmt)

    def update_selection_info(self, selected_wells):
        self.lbl_sel_count.setText(f"{len(selected_wells)} wells selected")

    def import_guide_file(self):
        """Imports conditions from a guide CSV/Excel file."""
        if self.df is None:
             QMessageBox.warning(self, "Wait", "Please upload raw data first so we know which wells are valid.")
             return

        path, _ = QFileDialog.getOpenFileName(self, "Import Guide File", "", "CSV Files (*.csv *.xlsx)")
        if not path: return

        try:
            if path.endswith('.csv'):
                df_guide = pd.read_csv(path)
            else:
                df_guide = pd.read_excel(path)

            # --- Parse Guide File ---
            # Assumption: Row indices in Col 0 (A, B, C), Column headers in Row 0 (1, 2, 3...)
            # We iterate through the dataframe.
            
            # Map column headers to strings to find '1', '2' etc.
            df_guide.columns = [str(c).strip() for c in df_guide.columns]
            
            # Find the "Row" identifier column if it exists, otherwise assume index 0
            row_col_idx = 0
            if 'Row' in df_guide.columns:
                row_col_idx = df_guide.columns.get_loc('Row')
            
            new_conditions_map = {} # Key: Name, Value: {wells: [], conc: val, color: ...}

                
            for c in df_guide.columns:
                # Check if column header is a number (1-24)
                if c.isdigit():
                    col_num = int(c)
                    for r in range(len(df_guide)):
                        row_letter = str(df_guide.iloc[r, row_col_idx]).strip().upper()
                        if not re.match(r'^[A-P]$', row_letter): continue # Skip non-letter rows
                        well_id = f"{row_letter}{col_num}"
                        
                        cell_val = str(df_guide.iloc[r][c]).strip()
                        if not cell_val or cell_val.lower() == 'nan': continue
                        
                        # Parse {Name}@{Dilution}~{Conc}
                        # Regex to handle optional parts
                        match = re.match(r'^(?P<name>[^@~]+)(?:@(?P<dilution>[^~]+))?(?:~(?P<conc>.+))?$', cell_val)
                        if not match: continue
                        
                        name = match.group('name').strip()
                        dil_str = match.group('dilution')
                        conc_str = match.group('conc')
                        
                        dilution = 1.0
                        if dil_str:
                            try: dilution = float(dil_str)
                            except: pass
                            
                        conc = None
                        if conc_str:
                            try: conc = float(conc_str)
                            except: pass
                        
                        if name not in new_conditions_map:
                             color = COLORS[self.color_idx % len(COLORS)]
                             self.color_idx += 1
                             new_conditions_map[name] = {
                                 'name': name,
                                 'conc': conc,
                                 'dilution': dilution,
                                 'color': color,
                                 'wells': []
                             }
                        
                        # Consistency check
                        if conc is not None and new_conditions_map[name]['conc'] is None:
                             new_conditions_map[name]['conc'] = conc
                        if dilution != 1.0 and new_conditions_map[name]['dilution'] == 1.0:
                             new_conditions_map[name]['dilution'] = dilution
                        
                        new_conditions_map[name]['wells'].append(well_id)

            # Apply to app
            count = 0
            for name, data in new_conditions_map.items():
                if not data['wells']: continue
                
                # Remove these wells from any existing conditions
                for cond in self.conditions:
                    cond['wells'] = [w for w in cond['wells'] if w not in data['wells']]
                self.conditions = [c for c in self.conditions if c['wells']]

                self.conditions.append({
                    'id': f"{name}_{len(self.conditions)}",
                    'name': name,
                    'conc': data['conc'],
                    'dilution': data['dilution'],
                    'color': data['color'],
                    'wells': data['wells']
                })
                self.plate_widget.assign_color(data['wells'], data['color'])
                count += 1
            
            self.update_condition_list()
            QMessageBox.information(self, "Import Successful", f"Imported {count} conditions from guide file.")

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to parse guide file:\n{str(e)}")


    def assign_condition(self):
        wells = list(self.plate_widget.selected_wells)
        if not wells:
            return
        
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please provide a condition name.")
            return

        conc_str = self.input_conc.text().strip()
        conc = None
        if conc_str:
            try:
                conc = float(conc_str)
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Concentration must be a number.")
                return

        dil_str = self.input_dilution.text().strip()
        dilution = 1.0
        if dil_str:
            try:
                dilution = float(dil_str)
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Dilution Factor must be a number.")
                return

        color = COLORS[self.color_idx % len(COLORS)]
        self.color_idx += 1

        # Remove these wells from other conditions to avoid duplicates
        for cond in self.conditions:
            cond['wells'] = [w for w in cond['wells'] if w not in wells]
        self.conditions = [c for c in self.conditions if c['wells']]

        new_cond = {
            'id': f"{name}_{len(self.conditions)}",
            'name': name,
            'conc': conc,
            'dilution': dilution,
            'color': color,
            'wells': wells
        }
        self.conditions.append(new_cond)

        self.plate_widget.assign_color(wells, color)
        self.plate_widget.clear_selection()
        self.update_condition_list()
        self.input_conc.clear()
        self.input_dilution.clear()
        self.input_name.clear() 

    def edit_condition(self, index):
        """Enter Edit Mode for a specific condition."""
        if index < 0 or index >= len(self.conditions): return
        
        self.editing_condition_index = index
        cond = self.conditions[index]
        
        # 1. Populate Inputs
        self.input_name.setText(cond['name'])
        if cond['conc'] is not None:
            self.input_conc.setText(str(cond['conc']))
        else:
            self.input_conc.clear()

        # Handle dilution (if key missing in old saves, default to 1.0)
        dil = cond.get('dilution', 1.0)
        self.input_dilution.setText(str(dil))
            
        # 2. Select Wells on Grid
        self.plate_widget.set_selection(cond['wells'])
        
        # 3. Switch UI to Edit Mode
        self.btn_stack.setCurrentIndex(1) # Show Save/Cancel
        self.condition_list.setEnabled(False) # Lock list while editing
        self.btn_import_guide.setEnabled(False)

    def save_edited_condition(self):
        """Save changes made in Edit Mode."""
        if self.editing_condition_index is None: return
        
        # Validate Inputs
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Name cannot be empty.")
            return
            
        conc_str = self.input_conc.text().strip()
        conc = None
        if conc_str:
            try:
                conc = float(conc_str)
            except ValueError:
                 QMessageBox.warning(self, "Input Error", "Concentration must be a number.")
                 return

        dil_str = self.input_dilution.text().strip()
        dilution = 1.0
        if dil_str:
            try:
                dilution = float(dil_str)
            except ValueError:
                 QMessageBox.warning(self, "Input Error", "Dilution Factor must be a number.")
                 return
        
        # Get currently selected wells (user might have modified them)
        wells = list(self.plate_widget.selected_wells)
        if not wells:
            QMessageBox.warning(self, "Selection Error", "Condition must have at least one well.")
            return

        # Update the condition object
        cond = self.conditions[self.editing_condition_index]
        old_wells = cond['wells']
        old_color = cond['color']
        
        # If wells changed, we need to handle potential conflicts?
        # For simplicity, we just claim these wells.
        # Remove these wells from ANY other condition first (except self)
        for i, c in enumerate(self.conditions):
            if i != self.editing_condition_index:
                c['wells'] = [w for w in c['wells'] if w not in wells]
        
        cond['name'] = name
        cond['conc'] = conc
        cond['dilution'] = dilution
        cond['wells'] = wells
        
        # Update Visuals
        self.plate_widget.assign_color(old_wells, None)
        self.plate_widget.assign_color(wells, old_color)
        
        self.cancel_edit_mode() # Exit mode (which refreshes list)

    def cancel_edit_mode(self):
        """Exit edit mode without saving changes (or after saving)."""
        self.editing_condition_index = None
        self.input_name.clear()
        self.input_conc.clear()
        self.input_dilution.clear()
        self.plate_widget.clear_selection()
        self.btn_stack.setCurrentIndex(0) # Back to Add mode
        self.condition_list.setEnabled(True)
        self.btn_import_guide.setEnabled(True)
        self.update_condition_list() # Refresh list text

    def update_condition_list(self):
        # First, filter out any empty conditions that might have occurred during editing/stealing
        self.conditions = [c for c in self.conditions if c['wells']]
        
        self.condition_list.setRowCount(len(self.conditions))
        for i, cond in enumerate(self.conditions):
            item_name = QTableWidgetItem(cond['name'])
            item_name.setForeground(QColor(cond['color']))
            font = QFont()
            font.setBold(True)
            item_name.setFont(font)
            self.condition_list.setItem(i, 0, item_name)
            
            # Dilution Column
            dil = cond.get('dilution', 1.0)
            self.condition_list.setItem(i, 1, QTableWidgetItem(str(dil)))

            c_val = f"{cond['conc']}" if cond['conc'] is not None else "-"
            self.condition_list.setItem(i, 2, QTableWidgetItem(c_val))

            # Edit Button
            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(40, 24)
            btn_edit.clicked.connect(lambda checked=False, idx=i: self.edit_condition(idx))
            self.condition_list.setCellWidget(i, 3, btn_edit)

            # Delete Button
            btn_del = QPushButton("X")
            btn_del.setFixedSize(24, 24)
            btn_del.clicked.connect(lambda checked=False, idx=i: self.delete_condition(idx))
            self.condition_list.setCellWidget(i, 4, btn_del)

    def delete_condition(self, index):
        cond = self.conditions.pop(index)
        self.plate_widget.assign_color(cond['wells'], None) 
        self.update_condition_list()

    # --- Page 3: Plots ---
    def setup_plot_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        toolbar_layout = QHBoxLayout()
        btn_export_csv = QPushButton("Export Data (CSV)")
        btn_export_csv.clicked.connect(self.export_csv)
        btn_save_fig = QPushButton("Save Figure")
        btn_save_fig.clicked.connect(self.save_figure)

        toolbar_layout.addWidget(QLabel("Results"))
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(btn_export_csv)
        toolbar_layout.addWidget(btn_save_fig)
        layout.addLayout(toolbar_layout)

        splitter = QSplitter(Qt.Horizontal)
        
        kinetic_container = QGroupBox("Kinetic Trace")
        k_layout = QVBoxLayout(kinetic_container)
        
        self.fig_kinetic = Figure(figsize=(5, 4), dpi=100)
        self.canvas_kinetic = FigureCanvas(self.fig_kinetic)
        self.ax_kinetic = self.fig_kinetic.add_subplot(111)
        
        k_layout.addWidget(self.canvas_kinetic)
        k_layout.addWidget(NavigationToolbar(self.canvas_kinetic, kinetic_container))
        
        k_form = QFormLayout()
        self.k_title = QLineEdit("Kinetic Trace")
        self.k_xlabel = QLineEdit("Time (min)")
        self.k_ylabel = QLineEdit("RLU")
        
        for w in [self.k_title, self.k_xlabel, self.k_ylabel]:
            w.returnPressed.connect(self.update_plots)

        k_form.addRow("Title:", self.k_title)
        k_form.addRow("X-Axis:", self.k_xlabel)
        k_form.addRow("Y-Axis:", self.k_ylabel)
        k_layout.addLayout(k_form)

        splitter.addWidget(kinetic_container)

        dose_container = QGroupBox("Standard Curve")
        d_layout = QVBoxLayout(dose_container)
        
        self.fig_dose = Figure(figsize=(5, 4), dpi=100)
        self.canvas_dose = FigureCanvas(self.fig_dose)
        self.ax_dose = self.fig_dose.add_subplot(111)

        d_layout.addWidget(self.canvas_dose)
        d_layout.addWidget(NavigationToolbar(self.canvas_dose, dose_container))
        
        d_form = QFormLayout()
        self.d_title = QLineEdit("Standard Curve")
        self.d_xlabel = QLineEdit("Concentration (µg/mL)")
        self.d_ylabel = QLineEdit("Max RLU")

        for w in [self.d_title, self.d_xlabel, self.d_ylabel]:
            w.returnPressed.connect(self.update_plots)

        d_form.addRow("Title:", self.d_title)
        d_form.addRow("X-Axis:", self.d_xlabel)
        d_form.addRow("Y-Axis:", self.d_ylabel)
        d_layout.addLayout(d_form)
        
        splitter.addWidget(dose_container)

        layout.addWidget(splitter)
        self.stack.addWidget(page)

    def update_plots(self):
        self.ax_kinetic.clear()
        self.ax_dose.clear()

        if self.df is None: return

        for cond in self.conditions:
            valid_wells = [w for w in cond['wells'] if w in self.df.columns]
            if not valid_wells: continue
            
            subset = self.df[valid_wells]
            mean = subset.mean(axis=1)
            std = subset.std(axis=1)
            time = self.df['Time']

            self.ax_kinetic.errorbar(time, mean, yerr=std, label=cond['name'], 
                                     color=cond['color'], fmt='-o', capsize=3, markersize=4, alpha=0.8)
        
        self.ax_kinetic.set_title(self.k_title.text())
        self.ax_kinetic.set_xlabel(self.k_xlabel.text())
        self.ax_kinetic.set_ylabel(self.k_ylabel.text())
        
        self.ax_kinetic.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        self.ax_kinetic.grid(True, which='both', linestyle='--', alpha=0.5)
        
        self.fig_kinetic.tight_layout()
        self.canvas_kinetic.draw()

        dose_data = []
        for cond in self.conditions:
            if cond['conc'] is not None:
                valid_wells = [w for w in cond['wells'] if w in self.df.columns]
                if not valid_wells: continue
                
                max_vals = self.df[valid_wells].max(axis=0)
                mean_max = max_vals.mean()
                std_max = max_vals.std()
                
                dose_data.append({
                    'conc': cond['conc'],
                    'mean': mean_max,
                    'std': std_max,
                    'name': cond['name'],
                    'color': cond['color']
                })
        
        if len(dose_data) >= 2:
            dose_df = pd.DataFrame(dose_data).sort_values('conc')
            
            self.ax_dose.errorbar(dose_df['conc'], dose_df['mean'], yerr=dose_df['std'], 
                                  fmt='none', capsize=5, ecolor='black', zorder=1)
            
            for _, row in dose_df.iterrows():
                self.ax_dose.scatter(row['conc'], row['mean'], color=row['color'], s=60, label=row['name'], zorder=2)

            slope, intercept, r_value, p_value, std_err = linregress(dose_df['conc'], dose_df['mean'])
            
            x_range = np.linspace(dose_df['conc'].min(), dose_df['conc'].max(), 100)
            y_pred = slope * x_range + intercept
            self.ax_dose.plot(x_range, y_pred, 'k--', alpha=0.7, zorder=1)
            
            eq_text = f"y = {slope:.2f}x + {intercept:.2f}\nR² = {r_value**2:.4f}"
            self.ax_dose.text(0.05, 0.95, eq_text, transform=self.ax_dose.transAxes, 
                              verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            self.ax_dose.set_xlabel(self.d_xlabel.text())
            self.ax_dose.set_ylabel(self.d_ylabel.text())
            self.ax_dose.set_title(self.d_title.text())
            self.ax_dose.grid(True, which='both', linestyle='--', alpha=0.5)
        else:
            self.ax_dose.text(0.5, 0.5, "Assign concentrations to at least\n2 conditions.", 
                             ha='center', va='center', transform=self.ax_dose.transAxes)

        self.fig_dose.tight_layout()
        self.canvas_dose.draw()

    def export_csv(self):
        if self.df is None or not self.conditions: return
        
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "processed_data.csv", "CSV Files (*.csv)")
        if path:
            export_df = pd.DataFrame({'Time': self.df['Time']})
            for cond in self.conditions:
                valid_wells = [w for w in cond['wells'] if w in self.df.columns]
                if valid_wells:
                    subset = self.df[valid_wells]
                    export_df[f"{cond['name']} (Mean)"] = subset.mean(axis=1)
                    export_df[f"{cond['name']} (Std)"] = subset.std(axis=1)
            
            export_df.to_csv(path, index=False)
            QMessageBox.information(self, "Export", "Data exported successfully.")

    def save_figure(self):
        msg = QMessageBox()
        msg.setWindowTitle("Save Figure")
        msg.setText("Which figure would you like to save?")
        btn_k = msg.addButton("Kinetic Trace", QMessageBox.ActionRole)
        btn_d = msg.addButton("Standard Curve", QMessageBox.ActionRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()

        target_fig = None
        if msg.clickedButton() == btn_k:
            target_fig = self.fig_kinetic
        elif msg.clickedButton() == btn_d:
            target_fig = self.fig_dose
        
        if target_fig:
            path, _ = QFileDialog.getSaveFileName(self, "Save Figure", "figure.png", "Images (*.png *.jpg *.svg)")
            if path:
                target_fig.savefig(path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Saved", f"Figure saved to {path}")

    # --- Page 4: Quantification ---
    def setup_quant_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Controls
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Standard Curve:"))
        
        self.combo_curve = QComboBox()
        self.combo_curve.currentIndexChanged.connect(self.on_std_curve_change)
        h_layout.addWidget(self.combo_curve)
        
        h_layout.addSpacing(20)
        h_layout.addWidget(QLabel("Equation: y = mx + b"))
        
        self.input_m = QLineEdit()
        self.input_m.setPlaceholderText("Slope (m)")
        self.input_b = QLineEdit()
        self.input_b.setPlaceholderText("Intercept (b)")
        
        h_layout.addWidget(QLabel("m:"))
        h_layout.addWidget(self.input_m)
        h_layout.addWidget(QLabel("b:"))
        h_layout.addWidget(self.input_b)
        
        btn_calc = QPushButton("Recalculate")
        btn_calc.clicked.connect(lambda: (self.update_quant_table(), self.update_quant_plot()))
        h_layout.addWidget(btn_calc)

        # Added Export Button here
        btn_export_quant = QPushButton("Export Quant Data")
        btn_export_quant.clicked.connect(self.export_quant_data)
        h_layout.addWidget(btn_export_quant)

        self.check_alerts = QCheckBox("Show Range Alerts")
        self.check_alerts.setChecked(True)
        self.check_alerts.stateChanged.connect(self.update_quant_plot)
        h_layout.addWidget(self.check_alerts)

        # Added Stock Conc Toggle
        self.check_stock = QCheckBox("Plot Stock Conc")
        self.check_stock.stateChanged.connect(self.update_quant_plot)
        h_layout.addWidget(self.check_stock)

        h_layout.addStretch()
        
        layout.addLayout(h_layout)

        splitter = QSplitter(Qt.Horizontal)

        # Table
        self.quant_table = QTableWidget()
        self.quant_table.setColumnCount(6)
        self.quant_table.setHorizontalHeaderLabels(["Condition", "Avg Peak RLU", "Concentration (µg/mL)", "Std Dev", "Dilution", "Stock Conc (µg/mL)"])
        self.quant_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        splitter.addWidget(self.quant_table)

        # Bar Plot
        self.fig_quant = Figure(figsize=(5, 4), dpi=100)
        self.canvas_quant = FigureCanvas(self.fig_quant)
        self.ax_quant = self.fig_quant.add_subplot(111)
        
        plot_container = QWidget()
        p_layout = QVBoxLayout(plot_container)
        p_layout.addWidget(NavigationToolbar(self.canvas_quant, self))
        p_layout.addWidget(self.canvas_quant)
        
        splitter.addWidget(plot_container)
        layout.addWidget(splitter)
        # Export button removed from bottom
        
        self.stack.addWidget(page)

    def load_standard_curves(self):
        try:
            if os.path.exists("resources/HiBit_quant_standard_curve.csv"):
                df_curves = pd.read_csv("resources/HiBit_quant_standard_curve.csv")
                self.combo_curve.clear()
                self.standard_curves = {}
                
                for _, row in df_curves[::-1].iterrows():
                    name = str(row['Name'])
                    self.standard_curves[name] = row.to_dict()
                    self.combo_curve.addItem(name)
                
                self.combo_curve.addItem("Custom", None)
        except Exception as e:
            print(f"Error loading standard curves: {e}")

    def on_std_curve_change(self, index):
        name = self.combo_curve.currentText()
        if name in self.standard_curves:
            data = self.standard_curves[name]
            self.input_m.setText(str(data['m']))
            self.input_b.setText(str(data['b']))
            # Trigger update
            self.update_quant_table()
            self.update_quant_plot()

    def update_quant_table(self):
        if self.df is None: return
        
        try:
            m = float(self.input_m.text())
            b = float(self.input_b.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values for m and b.")
            return

        self.quant_table.setRowCount(0)
        
        for cond in self.conditions:
            valid_wells = [w for w in cond['wells'] if w in self.df.columns]
            if not valid_wells: continue
            
            max_vals = self.df[valid_wells].max(axis=0)
            mean_max = max_vals.mean()
            std_max = max_vals.std()
            
            if m != 0:
                calc_conc = (mean_max - b) / m
                # Propagate error: std(Conc) = std(RLU) / m
                std_conc = std_max / abs(m)
                
                dil = cond.get('dilution', 1.0)
                stock_conc = calc_conc * dil
                
                conc_str = f"{calc_conc:.4f}"
                std_str = f"{std_conc:.4f}"
                dil_str = f"{dil}"
                stock_str = f"{stock_conc:.4f}"
            else:
                conc_str = "Error (m=0)"
                std_str = "-"
                dil_str = "-"
                stock_str = "-"
            
            row = self.quant_table.rowCount()
            self.quant_table.insertRow(row)
            self.quant_table.setItem(row, 0, QTableWidgetItem(cond['name']))
            self.quant_table.setItem(row, 1, QTableWidgetItem(f"{mean_max:.2f}"))
            self.quant_table.setItem(row, 2, QTableWidgetItem(conc_str))
            self.quant_table.setItem(row, 3, QTableWidgetItem(std_str))
            self.quant_table.setItem(row, 4, QTableWidgetItem(dil_str))
            self.quant_table.setItem(row, 5, QTableWidgetItem(stock_str))

    def update_quant_plot(self):
        if self.df is None: return
        try:
            m = float(self.input_m.text())
            b = float(self.input_b.text())
            if m == 0: raise ValueError("m cannot be 0")
        except ValueError:
             return # User warned in table update already

        self.ax_quant.clear()
        
        names = []
        means = []
        stds = []
        colors = []
        raw_means = [] # To check against limits
        
        # Get thresholds for current curve
        curve_name = self.combo_curve.currentText()
        low_limit = -np.inf
        high_limit = np.inf
        
        if curve_name in self.standard_curves:
            try:
                low_limit = float(self.standard_curves[curve_name]['Low'])
                high_limit = float(self.standard_curves[curve_name]['High'])
            except:
                pass 

        is_stock_mode = self.check_stock.isChecked()

        for cond in self.conditions:
            valid_wells = [w for w in cond['wells'] if w in self.df.columns]
            if not valid_wells: continue
            
            max_rlus = self.df[valid_wells].max(axis=0)
            # Calculated Concentration (Pre-dilution)
            concs = (max_rlus - b) / m
            
            raw_mean = concs.mean()
            raw_std = concs.std()
            
            names.append(cond['name'])
            colors.append(cond['color'])
            raw_means.append(raw_mean)
            
            if is_stock_mode:
                dil = cond.get('dilution', 1.0)
                means.append(raw_mean * dil)
                stds.append(raw_std * dil)
            else:
                means.append(raw_mean)
                stds.append(raw_std)

        x_pos = np.arange(len(names))
        
        bars = self.ax_quant.bar(x_pos, means, yerr=stds, align='center', alpha=0.7, ecolor='black', capsize=10, color=colors)
        
        # Labels and Titles based on Mode
        if is_stock_mode:
            self.ax_quant.set_ylabel('Stock Concentration (µg/mL)')
            self.ax_quant.set_title('Stock Concentrations')
        else:
            self.ax_quant.set_ylabel('Concentration (µg/mL)')
            self.ax_quant.set_title('Calculated Concentrations')
        
        self.ax_quant.set_xticks(x_pos)
        self.ax_quant.set_xticklabels(names, rotation=45, ha='right')
        self.ax_quant.yaxis.grid(True)
        
        # Calculate dynamic offset for labels/alerts
        if means:
            # Handle potential NaNs for max calculation
            valid_means = [m for m in means if not np.isnan(m)]
            y_max = max(valid_means) if valid_means else 1
            offset = y_max * 0.05
        else:
            offset = 1

        # --- Add Data Labels ---
        for i, val in enumerate(means):
            # Safe height calculation handling single points (std=nan)
            err = stds[i] if not np.isnan(stds[i]) else 0
            # Place label slightly above the error bar
            label_y = val + err + (offset * 0.2)
            
            self.ax_quant.text(x_pos[i], label_y, f"{val:.2f}", 
                               ha='center', va='bottom', 
                               color='black', fontsize=9)

        # --- Check Limits & Add Alert Symbols ---
        if self.check_alerts.isChecked():
            out_of_range_flag = False
            for i, raw_val in enumerate(raw_means): # Check RAW value against limits
                if raw_val < low_limit or raw_val > high_limit:
                    # Plot symbol based on PLOTTED value (means[i])
                    val = means[i]
                    err = stds[i] if not np.isnan(stds[i]) else 0
                    
                    symbol_y = val + err + offset
                    
                    self.ax_quant.text(x_pos[i], symbol_y, "!", 
                                       ha='center', va='bottom', 
                                       color='red', fontsize=16, fontweight='bold')
                    out_of_range_flag = True

            if out_of_range_flag:
                self.ax_quant.plot([], [], marker='None', linestyle='None', label='! = Out of Range')

        self.fig_quant.tight_layout()
        self.canvas_quant.draw()

    def export_quant_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Quant Results", "quant_results.csv", "CSV (*.csv)")
        if path:
            headers = [self.quant_table.horizontalHeaderItem(i).text() for i in range(self.quant_table.columnCount())]
            data = []
            for row in range(self.quant_table.rowCount()):
                row_data = {}
                for col, header in enumerate(headers):
                    item = self.quant_table.item(row, col)
                    row_data[header] = item.text() if item else ""
                data.append(row_data)
            
            df = pd.DataFrame(data)
            df.to_csv(path, index=False)
            QMessageBox.information(self, "Export", "Quantification data exported successfully.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, Qt.white)
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(0, 0, 255))
    palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)

    window = HiBitApp()
    window.show()
    sys.exit(app.exec())