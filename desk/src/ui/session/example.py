#To do: Integral overlap matrix calculations, upload images with new saving scheme, Use PCA, USe ALl buttons, Save patient file
#Move process logic to patient class
#number_of_components = 4 #Add input for this number
#Important! self.patient.THb defined as np.absolute(Concentration_Matrix[0,:,:])+np.absolute(Concentration_Matrix[1,:,:])
#Be sure to change it if chromophore data changed

import os
import sys
import pandas as pd
import numpy as np
from PyQt6 import QtGui, QtCore
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QIcon, QImage, QFont
from PyQt6.QtCore import Qt, QRect, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget,
    QFileDialog, QDialog, QHBoxLayout, QFrame, QStackedLayout, QHBoxLayout,
    QButtonGroup, QRadioButton, QCheckBox, QTableWidget, QLineEdit, QTableWidgetItem, QSplitter)
from PIL import Image
from PyQt6.QtWidgets import QProgressDialog, QMessageBox
from PyQt6.QtCore import Qt, QTimer
import imageio.v2 as imageio
import scipy.linalg as spla
import numpy.linalg as la
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from skimage.filters import threshold_otsu
from skimage.transform import downscale_local_mean
import cv2
from skimage.filters import gaussian
from skimage import measure
import seaborn as sns
import io
from sklearn.decomposition import PCA as sklearnPCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import gaussian_kde
# from tqdm import tqdm

# Model: Patient
class Patient(QObject):
    progress_signal = pyqtSignal(int)

    def __init__(self, files_address=''):
        super().__init__()
        self.files_address = files_address
        self.result = None
        self.progress = 0

    def Segmentation_Otsu(self):
        to_fit_area = self.THb
        self.gaussian_blur = 2
        uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
        blured_area = gaussian(to_fit_area, self.gaussian_blur)
        min_value = blured_area.min()
        max_value = blured_area.max()
        treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)

        ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # Code below could be implemented if only the highes area of lesion is interesting to examine

        # treshold_in_real_map = ret*(max_value - min_value)/255 + min_value
    #     contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # #     area_list = []
    # #     for cnt in contours:
    # #         area_list.append(cv2.contourArea(cnt))
    # #     contour = contours[np.array(area_list).argmax()]
    #     #We are interested in only highest area contour

    #     image_with_contours = cv2.drawContours(uint8_to_fit_area, contours, -1, (255, 0, 255), 5)
    #     plt.imshow(image_with_contours)
    #     plt.xticks(ticks = [])
    #     plt.yticks(ticks = [])
    #     plt.show()


    # #     mask = np.zeros(to_fit_area.shape, np.uint8)
    # #     cv2.drawContours(mask, [contour], 0, 255, -1)
    # #     cv2.drawContours(mask, [contours], 0, 255, -1)

    #     plt.imshow(th*to_fit_area)
    #     plt.xticks(ticks = [])
    #     plt.yticks(ticks = [])
    #     plt.show()


        return th

    def Borders_values(self):
        step = 1
        to_fit_area = self.THb
        self.gaussian_blur = 2
        uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
        blured_area = gaussian(to_fit_area, self.gaussian_blur)
        min_value = blured_area.min()
        max_value = blured_area.max()
        treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
        ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    #     start = ret*(1-offset_percent_1/100)
    #     stop = max_value#ret*(1+offset_percent_2/100)
        stop = 255
        mean, std, area, length = self.line_array(treated_area, ret, stop)

        return mean, std, area, length

    def line_array(self, treated_area, start, stop):
        # self.progress = pyqtSignal(int)
        step = 1
        mean = []
        std = []
        area = []
        length = []
        for i in np.arange(start, stop, step):
            m, s, a, l = self.contours(treated_area, i, i+step)

            if (np.isnan(m) or np.isnan(s)):
                mean.append(mean[-1])
                std.append(std[-1])
                area.append(area[-1])
                length.append(length[-1])
            else:
                mean.append(m)
                std.append(s)
                area.append(a)
                length.append(l)

            # Emit progress
            progress = int((i - start) / (stop - start) * 100)
            self.progress_signal.emit(progress)

        return mean, std, area, length

    def contours(self, treated_area, tr_start, tr_end):

        _, binary = cv2.threshold(treated_area, tr_start, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(np.uint8(255*binary), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        area_ar = [cv2.contourArea(cnt) for cnt in contours]

        if area_ar == []:
            contour_area = 0
        else:
            contour_area = sum(area_ar)

        #     contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    #     area_list = []
    #     for cnt in contours:
    #         area_list.append(cv2.contourArea(cnt))
    #     contour = contours[np.array(area_list).argmax()]
        #We are interested in only highest area contour

        _, binary2 = cv2.threshold(treated_area, tr_end, 255, cv2.THRESH_BINARY)

        X = np.ravel((binary2-binary)*treated_area)
        X = [i for i in X if i!=0]
        return (np.mean(X), np.std(X), contour_area, len(X))

    def extract_skin_value(self):
        step = 1
        to_fit_area = self.THb
        self.gaussian_blur = 2
        uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
        blured_area = gaussian(to_fit_area, self.gaussian_blur)
        min_value = blured_area.min()
        max_value = blured_area.max()
        treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)

        ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        # plt.imshow(th)
        # plt.show()
        contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        new_b = 1 - th
        X = np.ravel(new_b * treated_area)
        X = [i for i in X if i!=0]
        return np.mean(X)

    def analysis_of_distributions(self):
        mean_array = {'hemangioma':{}, 'skin': {}}
        std_array = {'hemangioma':{}, 'skin': {}}
        contour_data_for_stat = {}
        dataframe_for_stat = pd.DataFrame(contour_data_for_stat)

        mask = self.Segmentation_Otsu()

        to_fit_area = self.THb
        # uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)

        X = np.ravel(mask * to_fit_area)/255
        values_hemangioma = np.array((np.array([i for i in X if i!=0]) - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255)

        X = np.ravel((255 - mask) * to_fit_area)/255
        values_skin = np.array((np.array([i for i in X if i!=0]) - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255)


        mean_array['skin'] = np.mean(values_skin)
        std_array['skin'] = np.std(values_skin)


        mean_array['hemangioma'] = np.mean(values_hemangioma)
        std_array['hemangioma'] = np.std(values_hemangioma)

        return mean_array['hemangioma'] / mean_array['skin']

    def check_patient_scores(self):
        """
        Checks the properties of the patient object and returns the first score found
        with its corresponding label. If no score is found, returns (None, None).

        Returns:
            tuple: (score, label) where label is one of "HAS", "HASI", or "HSS",
                   or (None, None) if no scores are found.
        """
        if isinstance(self.input_HAS_score, (int, float)):
            return self.input_HAS_score, "HAS"
        elif isinstance(self.input_HASI_score, (int, float)):
            return self.input_HASI_score, "HASI"
        elif isinstance(self.input_HSS_score, (int, float)):
            return self.input_HSS_score, "HSS"
        else:
            return None, None
    def calculate_probabilities(self, s_coefficient, score=None, scale_name=None):

        """
        Calculate the probability of a patient belonging to each category based on the given score and scale.
        Args:
            score (float): The score value for the chosen scale (e.g., HAS, HSS, HASI).
            scale_name (str): The name of the scale ('HAS', 'HSS', or 'HASI').

        Returns:
            dict: Probabilities for each category (Observation, Local Conservative, Operation).
                  If no score or scale is provided, returns equal probabilities.
        """
        # Parameters for each scale; determined from experimental data with the test study on 80 patients cohort
        parameters = {
            "HAS": {
                "Category 0": {"Intercept": 0.6181, "Coefficient": -0.2169},
                "Category 1": {"Intercept": 0.8007, "Coefficient": -0.0024},
                "Category 2": {"Intercept": -1.4188, "Coefficient": 0.2192}
            },
            "HSS": {
                "Category 0": {"Intercept": 0.3437, "Coefficient": -0.1875},
                "Category 1": {"Intercept": 0.7777, "Coefficient": 0.0010},
                "Category 2": {"Intercept": -1.1214, "Coefficient": 0.1865}
            },
            "HASI": {
                "Category 0": {"Intercept": 0.8867, "Coefficient": -0.1543},
                "Category 1": {"Intercept": 1.0033, "Coefficient": -0.0280},
                "Category 2": {"Intercept": -1.8900, "Coefficient": 0.1822}
            }
        }


        # Calculate Likelihoods using Real Data

        categories = ["Observation", "Local Conservative", "Operation"]

        real_data = {
    "Observation": [
        3.21393269, 26.57572901, 1.97897979, 5.48259599, 2.99981, 3.31745544,
        13.27689141, 1.71745906, 17.48231325, 1.87580825, 12.64986065,
        7.87167763, 1.71366846, 13.61160749, 2.31452927, 22.6661329,
        44.90186825, 36.8487924, 14.78203206
    ],
    "Local Conservative": [
        7.3522544, 3.02525876, 17.97379823, 20.92351022, 24.72729263,
        24.00776019, 10.33037404, 3.52843382, 19.7609681, 26.77218002,
        1.65112093, 11.55317624, 3.30694099, 3.82502304, 4.20041205,
        5.71131541, 25.49669084, 11.99578407, 2.88923068, 16.32942033,
        10.51932178, 18.42635627, 1.66447679, 6.29955688, 14.67185596,
        32.53059061, 12.19990989, 32.70948272, 18.51845014, 20.23320976,
        31.62748937, 1.37786158, 1.73443908, 26.28364305, 20.46232858,
        15.06569079, 9.55950523, 4.08012488, 23.07724569, 11.36823735,
        2.98220644, 3.18974336, 1.98305401, 1.67706588, 31.09508714,
        1.7800393, 3.4768971, 19.89810703, 5.30606471
    ],
    "Operation": [
        12.40563717, 17.50582966, 34.99986717, 3.59924032, 2.20970812,
        11.19131621, 10.14635472, 2.28083667, 6.46990814, 2.9558964,
        8.57629769, 1.37140096
    ]
}


        likelihoods = []
        for i, category in enumerate(categories):
            category_data = real_data[category]
            kde = gaussian_kde(category_data)
            likelihood = kde.evaluate([s_coefficient])[0]  # Estimate likelihood for the given score!!!!!!!
            likelihoods.append(likelihood)

        # Return equal probabilities if no input is provided
        if score is None or scale_name is None:
            # Step 3: Combine Priors and Likelihoods to Get Posteriors
            joint_probabilities = [1/3 * likelihoods[i] for i in range(3)]
            evidence = sum(joint_probabilities)
            posteriors = [jp / evidence for jp in joint_probabilities]

            # Step 4: Convert to Percentages
            percentages = [round(p * 100, 1) for p in posteriors]
            percentages[0] += round(100 - sum(percentages), 1)  # Adjust for rounding

            return dict(zip(categories, percentages))

        # Ensure valid scale name
        if scale_name not in parameters:
            raise ValueError(f"Invalid scale name: {scale_name}. Choose from 'HAS', 'HSS', or 'HASI'.")

        # Get parameters for the chosen scale
        scale_params = parameters[scale_name]

        # Calculate logits for each category
        logits = [
            scale_params[f"Category {i}"]["Intercept"] + scale_params[f"Category {i}"]["Coefficient"] * score
            for i in range(3)
        ]

        # Calculate probabilities using the softmax function
        exp_logits = np.exp(logits)
        probabilities = exp_logits / np.sum(exp_logits)

        # Step 3: Combine Priors and Likelihoods to Get Posteriors
        joint_probabilities = [probabilities[i] * likelihoods[i] for i in range(3)]
        evidence = sum(joint_probabilities)
        posteriors = [jp / evidence for jp in joint_probabilities]

        # Step 4: Convert to Percentages
        percentages = [round(p * 100, 1) for p in posteriors]
        percentages[0] += round(100 - sum(percentages), 1)  # Adjust for rounding

        return dict(zip(categories, percentages))



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.title = "HyperspectRus"
        self.setWindowTitle(self.title)
        # self.setWindowIcon(QtGui.QIcon('logo.jpg'))
        self.setStyleSheet("background-color: #dbe7e4;")

        self.Ref_address = r'C:/Users/admin/Desktop/Skoltech/ГПХ 2024/Step 1. 2024.09.11 Starting with PyQt6'
        self.selected_path = None

        df = pd.DataFrame(
            [[35413.747686, 48266.475592, 1288.594416, 100.0],
             [22543.710184, 19790.442082, 1317.883702, 100.0],
             [26312.342124, 29340.161853, 1243.050297, 100.0],
             [1513.971083, 9325.287882, 1201.872216, 100.0],
             [1161.464976, 7318.000622, 1137.740404, 100.0],
             [2435.635426, 2820.807862, 672.096616, 100.0],
             [3058.380772, 2578.204305, 563.051536, 100.0],
             [3880.828582, 3115.201821, 475.588304, 100.0]],
            index=['460', '495', '520', '630', '660', '800', '850', '880'],
            columns=['Hb02', 'Hb', 'Melanin', 'Background']
        )

        self.overlap_integral = df

        page_layout = QVBoxLayout()

        button_target_folder = QPushButton('Select a folder with hyperspectral photos')
        button_target_folder.clicked.connect(self.update_label_with_path)
        button_target_folder.setStyleSheet("background-color: #bcd4e6")
        button_target_folder.setToolTip("Click here to select a folder with hyperspectral photos")

        self.folder_path_label = QLabel("No folder selected")
        self.folder_path_label.setStyleSheet("font-size: 18px; color: #333;")

        button_customize = QPushButton('Customize default parameters')
        button_customize.clicked.connect(self.customize_button_clicked)
        button_customize.setStyleSheet("background-color: #bcd4e6")
        button_customize.setToolTip("Click here to change reference folder, LEDs parameters, Overlap integral")

        self.Ref_label = QLabel("Current reference folder is: " + self.Ref_address)
        self.Ref_label.setStyleSheet("font-size: 18px; color: #000;")

        page_layout.addWidget(button_target_folder)
        page_layout.addWidget(self.folder_path_label)
        page_layout.addWidget(button_customize)
        page_layout.addWidget(self.Ref_label)

        decision_button_layout = QHBoxLayout()
        self.stacklayout = QStackedLayout()
        page_layout.addLayout(decision_button_layout)
        page_layout.addLayout(self.stacklayout)

        btn1 = QPushButton("Submit")
        btn1.pressed.connect(self.submit_main)
        decision_button_layout.addWidget(btn1)
        btn1.setStyleSheet("background-color: #bcd4e6")

        btn2 = QPushButton("Cancel")
        btn2.pressed.connect(self.close)
        decision_button_layout.addWidget(btn2)
        btn2.setStyleSheet("background-color: #bcd4e6")

        widget = QWidget()
        widget.setLayout(page_layout)
        self.setCentralWidget(widget)

    def customize_button_clicked(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Customize Default Parameters")

        layout = QVBoxLayout()

        new_path_label = QLabel("No new path selected")
        new_path_label.setStyleSheet("font-size: 18px; color: #333;")

        def select_new_path():
            selected_path = QFileDialog.getExistingDirectory(dlg, caption='Select a new reference folder')
            if selected_path:
                new_path_label.setText(f"Selected Folder: {selected_path}")
                dlg.selected_path = selected_path
            else:
                new_path_label.setText("No new path selected")
                dlg.selected_path = None

        select_path_button = QPushButton("Select New Reference Folder")
        select_path_button.clicked.connect(select_new_path)
        select_path_button.setStyleSheet("background-color: #bcd4e6")

        # Horizontal separator line below select_path_button
        separator_line_1 = QFrame()
        separator_line_1.setFrameShape(QFrame.Shape.HLine)
        separator_line_1.setFrameShadow(QFrame.Shadow.Sunken)
        separator_line_1.setStyleSheet("background-color: black;")

        # Button to pick new file for LEDs spectra
        pick_leds_file_button = QPushButton("Pick new file for LEDs spectra")
        pick_leds_file_button.setStyleSheet("background-color: #bcd4e6")
        pick_leds_file_button.clicked.connect(self.pick_leds_file)  # Placeholder for LEDs file selection

        # LEDs label
        leds_label = QLabel("LEDs in use are: ['460', '495', '520', '630', '660', '800', '850', '880']")
        leds_label.setStyleSheet("font-size: 18px; color: #333;")

        # Horizontal separator line below LEDs label
        separator_line_2 = QFrame()
        separator_line_2.setFrameShape(QFrame.Shape.HLine)
        separator_line_2.setFrameShadow(QFrame.Shadow.Sunken)
        separator_line_2.setStyleSheet("background-color: black;")

        # Chromophores label and advice
        chromophores_label = QLabel("Target chromophores for calculations with \nBouguer-Lambert-Beer approach are: ['Hb02','Hb','Melanin','Background']")
        chromophores_label.setStyleSheet("font-size: 18px; color: #333;")

        chromophores_advice_label = QLabel("Chromophores choice should be made according to \nthe practical considerations for particular skin lesion")
        chromophores_advice_label.setStyleSheet("font-size: 14px; color: #333;")

        # Button to pick new file for chromophores spectra
        pick_chromophores_file_button = QPushButton("Pick new file for chromophores spectra")
        pick_chromophores_file_button.setStyleSheet("background-color: #bcd4e6")
        pick_chromophores_file_button.clicked.connect(self.pick_chromophores_file)  # Placeholder for chromophores file selection

        # Horizontal separator line below chromophores
        separator_line_3 = QFrame()
        separator_line_3.setFrameShape(QFrame.Shape.HLine)
        separator_line_3.setFrameShadow(QFrame.Shadow.Sunken)
        separator_line_3.setStyleSheet("background-color: black;")

        # Integral Overlap Matrix Description
        matrix_description_1 = QLabel("Integral overlap matrix:")
        matrix_description_1.setStyleSheet("font-size: 18px; color: #333;")
        matrix_description_2 = QLabel("This matrix will be used in calculations \nif you pick Bouguer-Lambert-Beer approach")
        matrix_description_2.setStyleSheet("font-size: 14px; color: #333;")

        # Create DataFrame and Table Widget
        df = pd.DataFrame(
            [[35413.747686, 48266.475592, 1288.594416, 100.0],
             [22543.710184, 19790.442082, 1317.883702, 100.0],
             [26312.342124, 29340.161853, 1243.050297, 100.0],
             [1513.971083, 9325.287882, 1201.872216, 100.0],
             [1161.464976, 7318.000622, 1137.740404, 100.0],
             [2435.635426, 2820.807862, 672.096616, 100.0],
             [3058.380772, 2578.204305, 563.051536, 100.0],
             [3880.828582, 3115.201821, 475.588304, 100.0]],
            index=['460', '495', '520', '630', '660', '800', '850', '880'],
            columns=['Hb02', 'Hb', 'Melanin', 'Background']
        )

        table_widget = QTableWidget(len(df.index), len(df.columns))
        table_widget.setHorizontalHeaderLabels(df.columns)
        table_widget.setVerticalHeaderLabels(df.index)
        table_widget.setStyleSheet("font-size: 14px;")

        def populate_table(dataframe):
            for i, row in enumerate(dataframe.values):
                for j, value in enumerate(row):
                    table_widget.setItem(i, j, QTableWidgetItem(f"{value:.2f}"))

        populate_table(df)

        # Button to recalculate matrix
        def recalculate_matrix():
            new_values = np.random.rand(*df.shape) * 50000  # Generate random numbers
            new_df = pd.DataFrame(new_values, index=df.index, columns=df.columns)

            self.overlap_integral = new_df

            populate_table(new_df)
            #Right now all it does is just puts random numbers, recalculations will be added later, once it'll
            #be clear, what is the general format of data (spectra files) for chromophores and LEDs
            #This function should be updated with the separate file named: IOMC_Start.ipynb
            #In this file parts of a new code are already written.

        recalculate_button = QPushButton("Recalculate Integral Overlap Matrix")
        recalculate_button.setStyleSheet("background-color: #bcd4e6")
        recalculate_button.clicked.connect(recalculate_matrix)

        # Button layout
        button_layout = QHBoxLayout()
        submit_button = QPushButton("Submit")
        cancel_button = QPushButton("Cancel")

        def submit():
            if hasattr(dlg, 'selected_path') and dlg.selected_path:
                self.Ref_address = dlg.selected_path
                self.Ref_label.setText("Current reference folder is: " + self.Ref_address)
            dlg.close()

        cancel_button.clicked.connect(dlg.close)
        submit_button.clicked.connect(submit)

        submit_button.setStyleSheet("background-color: #bcd4e6")
        cancel_button.setStyleSheet("background-color: #bcd4e6")

        button_layout.addWidget(submit_button)
        button_layout.addWidget(cancel_button)

        # Layout additions
        layout.addWidget(new_path_label)
        layout.addWidget(select_path_button)
        layout.addWidget(separator_line_1)
        layout.addWidget(leds_label)
        layout.addWidget(pick_leds_file_button)
        layout.addWidget(separator_line_2)
        layout.addWidget(chromophores_label)
        layout.addWidget(chromophores_advice_label)
        layout.addWidget(pick_chromophores_file_button)
        layout.addWidget(separator_line_3)
        layout.addWidget(matrix_description_1)
        layout.addWidget(matrix_description_2)
        layout.addWidget(table_widget)
        layout.addWidget(recalculate_button)
        layout.addLayout(button_layout)

        dlg.setLayout(layout)
        dlg.exec()

    def pick_leds_file(self):
        """Placeholder for picking new LEDs file."""
        #In the next version it should also change the text of wich Chromophores/LEDs are in use
        file_path, _ = QFileDialog.getOpenFileName(self, "Select LEDs Spectra File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            print(f"Selected LEDs Spectra File: {file_path}")

    def pick_chromophores_file(self):
        """Placeholder for picking new chromophores file."""
        #In the next version it should also change the text of wich Chromophores/LEDs are in use
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Chromophores Spectra File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            print(f"Selected Chromophores Spectra File: {file_path}")



    def update_label_with_path(self):
        selected_path = QFileDialog.getExistingDirectory(self, caption='Select a folder')
        if selected_path:
            self.selected_path = selected_path
            self.folder_path_label.setText(f"Selected Folder: {selected_path}")
        else:
            self.folder_path_label.setText("No folder selected")

    def submit_main(self):
        if not self.selected_path:
            self.folder_path_label.setText("No folder selected. Cannot proceed.")
            return

        image_files = [
            os.path.join(self.selected_path, f)
            for f in os.listdir(self.selected_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        if not image_files:
            self.folder_path_label.setText("No images found in the selected folder.")
            return

        self.patient = Patient(files_address = self.selected_path)
        self.patient.overlap_integral = self.overlap_integral
        self.patient.Ref_address = self.Ref_address

        # Open the new window to show the first image
        self.image_viewer = ImageViewer(image_files, self, self.patient)
        self.image_viewer.show()

        # Close the main window
        self.close()


class ImageViewer(QMainWindow):
    def __init__(self, image_files, main_window, patient):
        super(ImageViewer, self).__init__()
        self.main_window = main_window  # Reference to the main window
        self.patient = patient  # Shared object reference

        self.image_files = image_files
        self.current_index = 0
        self.setWindowTitle("HyperspectRus Image Viewer")
        self.last_clicks = [(None, None), (None, None)]  # To store the coordinates of the last two clicks
        self.rectangle_visible = False  # Tracks if a rectangle is currently drawn

        # Main layout
        self.layout = QHBoxLayout()

        # Image Display Section
        self.image_layout = QVBoxLayout()
        self.image_label = QLabel(self)
        self.image_label.setScaledContents(True)
        self.image_label.setFrameShape(QFrame.Shape.Box)
        self.image_label.mousePressEvent = self.track_click
        self.update_image()

        # Add navigation buttons
        navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button.clicked.connect(self.show_next_image)
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)

        self.image_layout.addWidget(self.image_label)
        self.image_layout.addLayout(navigation_layout)

        # Coordinate Display Section
        self.coord_layout = QVBoxLayout()
        self.coord_label_1 = QLabel("Last Click 1: (0, 0)")
        self.coord_label_2 = QLabel("Last Click 2: (0, 0)")
        self.coord_label_1.setStyleSheet("font-size: 18px; color: #333;")
        self.coord_label_2.setStyleSheet("font-size: 18px; color: #333;")
        self.coord_layout.addWidget(self.coord_label_1)
        self.coord_layout.addWidget(self.coord_label_2)

        # Choices storage
        self.processing_area = "Use whole image for processing"
        self.correct_camera_drift = False
        self.processing_approach = "Use BLB"

        # Processing Area Options
        self.radio_group_1 = QButtonGroup(self)
        self.radio_whole_image = QRadioButton("Use whole image for processing")
        self.radio_selected_field = QRadioButton("Use only selected field for processing")
        self.radio_selected_field.setChecked(True)
        self.radio_group_1.addButton(self.radio_whole_image)
        self.radio_group_1.addButton(self.radio_selected_field)

        # Correct Camera Drift
        self.camera_drift_toggle = QCheckBox("Correct for camera drift")
        self.camera_drift_toggle.stateChanged.connect(self.toggle_camera_drift)
        self.camera_drift_toggle.setToolTip("This option doesn't work right now, \nbut will be implemented in the future")

        # Horizontal Separators for Correct Camera Drift
        separator_line_before_drift = QFrame()
        separator_line_before_drift.setFrameShape(QFrame.Shape.HLine)
        separator_line_before_drift.setFrameShadow(QFrame.Shadow.Sunken)
        separator_line_before_drift.setStyleSheet("background-color: black;")

        separator_line_after_drift = QFrame()
        separator_line_after_drift.setFrameShape(QFrame.Shape.HLine)
        separator_line_after_drift.setFrameShadow(QFrame.Shadow.Sunken)
        separator_line_after_drift.setStyleSheet("background-color: black;")


        # Processing Approach
        self.processing_label = QLabel("Please pick an approach that you want to use \nfor image processing, and visualization:")
        self.radio_group_2 = QButtonGroup(self)
        self.radio_blb = QRadioButton("Use BLB")
        self.radio_pca = QRadioButton("Use PCA")
        self.radio_all = QRadioButton("Use All")
        self.radio_blb.setChecked(True)
        self.radio_group_2.addButton(self.radio_blb)
        self.radio_group_2.addButton(self.radio_pca)
        self.radio_group_2.addButton(self.radio_all)

        separator_line_before_input = QFrame()
        separator_line_before_input.setFrameShape(QFrame.Shape.HLine)
        separator_line_before_input.setFrameShadow(QFrame.Shadow.Sunken)
        separator_line_before_input.setStyleSheet("background-color: black;")

        data_input_label = QLabel("Please input available information about the patient:")
        data_input_label.setStyleSheet("font-size: 18px; color: #333;")

        self.input_id = QLineEdit(self)
        self.input_id.setPlaceholderText("ID:")

        # Processing Approach
        self.treatment_label = QLabel("Treatment tactics:")
        self.radio_group_treatment = QButtonGroup(self)
        self.radio_observation = QRadioButton("Observation")
        self.radio_local = QRadioButton("Local conservative (Timolol etc.)")
        self.radio_operation = QRadioButton("Operation")
        self.radio_observation.setChecked(True)
        self.radio_group_treatment.addButton(self.radio_observation)
        self.radio_group_treatment.addButton(self.radio_local)
        self.radio_group_treatment.addButton(self.radio_operation)

        self.input_visit = QLineEdit(self)
        self.input_visit.setPlaceholderText("Number of visit:")


        self.input_age = QLineEdit(self)
        self.input_age.setPlaceholderText("Age (months):")

        self.input_location = QLineEdit(self)
        self.input_location.setPlaceholderText("Location:")

        self.input_HSS_score = QLineEdit(self)
        self.input_HSS_score.setPlaceholderText("HSS score:")

        self.input_HAS_score = QLineEdit(self)
        self.input_HAS_score.setPlaceholderText("HAS score:")

        self.input_HASI_score = QLineEdit(self)
        self.input_HASI_score.setPlaceholderText("HASI score:")


        # Submit and Cancel Buttons
        self.button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit")
        self.cancel_button = QPushButton("Cancel")
        self.submit_button.clicked.connect(self.submit)
        self.cancel_button.clicked.connect(self.cancel_action)
        self.submit_button.setToolTip("Start processing according to the given parameters")
        self.cancel_button.setToolTip("Return back to the main menu")
        self.submit_button.setStyleSheet("background-color: aquamarine; color: black;")
        self.cancel_button.setStyleSheet("background-color: salmon; color: black;")


        # Add buttons and align center
        self.button_layout.addWidget(self.submit_button)#, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.button_layout.addWidget(self.cancel_button)#, alignment=Qt.AlignmentFlag.AlignHCenter)
        # self.button_layout.addStretch()  # Add space to center the buttons vertically

        # Combine layouts
        self.coord_layout.addWidget(self.radio_whole_image)
        self.coord_layout.addWidget(self.radio_selected_field)
        self.coord_layout.addWidget(separator_line_before_drift)
        self.coord_layout.addWidget(self.camera_drift_toggle)
        self.coord_layout.addWidget(separator_line_after_drift)
        self.coord_layout.addWidget(self.processing_label)
        self.coord_layout.addWidget(self.radio_blb)
        self.coord_layout.addWidget(self.radio_pca)
        self.coord_layout.addWidget(self.radio_all)
        self.coord_layout.addWidget(separator_line_before_input)
        self.coord_layout.addWidget(data_input_label)
        self.coord_layout.addWidget(self.input_id)
        self.coord_layout.addWidget(self.input_visit)
        self.coord_layout.addWidget(self.treatment_label)
        self.coord_layout.addWidget(self.radio_observation)
        self.coord_layout.addWidget(self.radio_local)
        self.coord_layout.addWidget(self.radio_operation)
        self.coord_layout.addWidget(self.input_age)
        self.coord_layout.addWidget(self.input_location)
        self.coord_layout.addWidget(self.input_HSS_score)
        self.coord_layout.addWidget(self.input_HAS_score)
        self.coord_layout.addWidget(self.input_HASI_score)


        # Adjust column width to 1/3 the size of the photo
        self.coord_layout.setContentsMargins(10, 10, 10, 10)
        self.coord_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Combine layouts
        self.layout.addLayout(self.image_layout)
        self.coord_layout.addLayout(self.button_layout)
        self.layout.addLayout(self.coord_layout)


        # Set central widget
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    def cancel_action(self):
        # Reopen the main window and close the result window
        self.main_window.show()
        self.close()

    def toggle_camera_drift(self, state):
        """Toggle the camera drift correction."""
        self.correct_camera_drift = state == Qt.CheckState.Checked

    def submit(self):
        """Store the user's choices."""
        self.processing_area = (
            "Use whole image for processing" if self.radio_whole_image.isChecked()
            else "Use only selected field for processing"
        )


        self.processing_approach = (
            "Use BLB" if self.radio_blb.isChecked() else
            "Use PCA" if self.radio_pca.isChecked() else
            "Use All"
        )

        self.input_treatment = (
            "Observation" if self.radio_observation.isChecked() else
            "Local Conservative" if self.radio_local.isChecked() else
            "Operation"
        )

        # print("Processing Area:", self.processing_area)
        # print("Correct Camera Drift:", self.correct_camera_drift)
        # print("Processing Approach:", self.processing_approach)

        self.patient.processing_approach = self.processing_approach
        self.patient.processing_area = self.processing_area
        self.patient.input_id = self.input_id.text()
        self.patient.input_visit = self.input_visit.text()
        self.patient.input_treatment = self.input_treatment
        self.patient.input_age = self.input_age.text()
        self.patient.input_location = self.input_location.text()
        self.patient.input_HSS_score = self.input_HSS_score.text()
        self.patient.input_HSS_score = float(self.patient.input_HSS_score) if self.patient.input_HSS_score != '' else self.patient.input_HSS_score
        self.patient.input_HAS_score = self.input_HAS_score.text()
        self.patient.input_HAS_score = float(self.patient.input_HAS_score) if self.patient.input_HAS_score != '' else self.patient.input_HAS_score
        self.patient.input_HASI_score = self.input_HASI_score.text()
        self.patient.input_HASI_score = float(self.patient.input_HASI_score) if self.patient.input_HASI_score != '' else self.patient.input_HASI_score


        # print(vars(self.patient))
        # Open the progress bar dialog
        self.progress_dialog = ProgressDialog(self.patient)
        self.progress_dialog.show()
        self.close()

    def update_image(self):
        """Update the displayed image, downscaled by a factor of 2."""
        if self.image_files:
            image_path = self.image_files[self.current_index]
            pixmap = QPixmap(image_path)
            self.patient.scale_factor_for_image_display = 2
            scaled_pixmap = pixmap.scaled(
                pixmap.width() // self.patient.scale_factor_for_image_display, pixmap.height() // self.patient.scale_factor_for_image_display
            )  # Downscale by factor of 2
            self.image_label.setPixmap(scaled_pixmap)
            self.setWindowTitle(f"Image Viewer - {image_path}")


    def show_previous_image(self):
        """Show the previous image in the list."""
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.update_image()

    def show_next_image(self):
        """Show the next image in the list."""
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.update_image()

    def track_click(self, event):
        """Track the cursor position on the image when clicked."""
        x, y = event.pos().x(), event.pos().y()

        if self.rectangle_visible:
            # On third click, clear the rectangle
            self.last_clicks = [(None, None), (None, None)]
            self.rectangle_visible = False
            self.update_image()
        else:
            # Update last clicks
            self.last_clicks = [(x, y), self.last_clicks[0]]

            # Draw rectangle if two clicks are available
            if None not in self.last_clicks[1]:
                self.rectangle_visible = True
                self.draw_rectangle()

        # Update labels
        self.coord_label_1.setText(f"Last Click 1: ({self.last_clicks[0][0]}, {self.last_clicks[0][1]})")
        self.coord_label_2.setText(f"Last Click 2: ({self.last_clicks[1][0]}, {self.last_clicks[1][1]})")

        # Store click coordinates at patient for ROI processing.
        # scale_factor_for_coordinates = 2 # be sure to have it the same as in update_image(self)

        self.patient.ROI = (self.last_clicks[0][0], self.last_clicks[0][1], self.last_clicks[1][0], self.last_clicks[1][1])

    def draw_rectangle(self):
        """Draw a transparent rectangle with red borders between the two clicks."""
        if None in self.last_clicks[1]:
            return

        x1, y1 = self.last_clicks[1]
        x2, y2 = self.last_clicks[0]

        pixmap = self.image_label.pixmap()
        if pixmap:
            pixmap_copy = pixmap.copy()
            painter = QPainter(pixmap_copy)
            pen = QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine)  # Red border
            painter.setPen(pen)
            painter.setBrush(QColor(255, 0, 0, 20))  # Transparent red fill
            painter.drawRect(QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)))
            painter.end()

            self.image_label.setPixmap(pixmap_copy)



class PCA_Result_Window(QMainWindow):
    def __init__(self, PCA_result, patient):
        super().__init__()
        self.PCA_result = PCA_result
        self.patient = patient

        # Set up the window
        self.setWindowTitle(f"PCA Result Viewer for Patient {getattr(self.patient.input_id, 'name', 'Unknown')}")

        # Create the UI
        self.initUI()

    def initUI(self):
        # Extract the 0th slice
        slice_0 = self.PCA_result[:, :, 0]

        # Normalize the image data to 0-255 for visualization
        normalized_image = ((slice_0 - slice_0.min()) / (slice_0.max() - slice_0.min()) * 255).astype(np.uint8)

        # Convert the numpy array to QImage
        height, width = normalized_image.shape
        image = QImage(normalized_image.data, width, height, QImage.Format.Format_Grayscale8)

        # Create a QLabel to display the image
        image_label = QLabel(self)
        image_label.setPixmap(QPixmap.fromImage(image))
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set up the layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(image_label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)



class ProgressDialog(QProgressDialog):
    def __init__(self, patient):
        super().__init__()
        self.patient = patient  # Patient object
        self.setWindowTitle("Processing Data")
        self.setLabelText("Processing images...")
        self.setRange(0, 100)  # Set progress range from 0 to 100
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setValue(0)  # Start at 0% progress
        self.patient.progress_signal.connect(self.setValue)

        # processing
        QTimer.singleShot(0, self.process_data)
        # self.patient.progress.connect(self.setValue)

    def read_images(self, file_paths):
        """Updated image reading workflow."""
        for current_dir, next_dir, files in os.walk(file_paths, topdown=True):
            continue

        for b in range(np.array(files).size):
            if files[b][::-1][4] != str(b+1):
                print('Error in order of files', files[b][::-1][4], str(b+1))
                break
            files[b] = current_dir + '/' + files[b]

        gray = lambda rgb : np.dot(rgb[... , :3] , [1. , 1., 1. ])

        for k in range(np.array(files).size):
            files[k] = gray(imageio.imread(files[k]))

        files = np.array(files) + 1e-4
        return files

    def read_images_PCA(self, file_paths):
        for current_dir, next_dir, files in os.walk(file_paths, topdown=True):
            continue
        images_cube = (np.array(imageio.imread(current_dir + '/' + files[i])) for i in range(8))
        hypercube_of_images = np.dstack((tuple(images_cube)))
        return hypercube_of_images

    def process_data(self):
        """Main processing logic with progress updates."""
        if self.patient.processing_approach == "Use All":
            QMessageBox.critical(self, "Error", "Unsupported processing approach!")
            self.close()
            return
        if self.patient.processing_approach == "Use PCA":
            self.setLabelText("Uploading images...")
            QApplication.processEvents()  # Ensure the dialog updates immediately

            y_min, y_max = sorted([self.patient.ROI[1], self.patient.ROI[3]])
            x_min, x_max = sorted([self.patient.ROI[0], self.patient.ROI[2]])

            scf = self.patient.scale_factor_for_image_display

            if self.patient.processing_area == "Use only selected field for processing":
                files_hypercube = self.read_images_PCA(self.patient.files_address)
                files_hypercube = files_hypercube[scf*y_min:scf*y_max, scf*x_min:scf*x_max, :]
            else:
                files_hypercube = self.read_images_PCA(self.patient.files_address)

            print(files_hypercube.shape)
            self.setValue(100)
            self.setLabelText("Processing images...")
            QApplication.processEvents()  # Ensure the dialog updates immediately

            width = files_hypercube.shape[0]
            height = files_hypercube.shape[1]
            channels = files_hypercube.shape[2]
            image = np.reshape(files_hypercube, (width*height, channels))

            df = pd.DataFrame(image)
            number_of_components = 4 #Add input for this number
            PCA_transformer = sklearnPCA(n_components=number_of_components, svd_solver='arpack')
            # Has to be arpack or fixed random number for results to be reproducable between different trials
            # X_std = StandardScaler().fit_transform(df) Values already normalized in 8bit because of the camera [0:255]
            # Y_sklearn = sklearn_pca.fit_transform(X_std)
            PCA_transformed_hypercube = PCA_transformer.fit_transform(df)
            output = {}
            print('Explained_variance_ratio_by_each_component = ', PCA_transformer.explained_variance_ratio_)
            print('Explained_variance_ratio = ', np.sum(PCA_transformer.explained_variance_ratio_))


            y_df = pd.DataFrame(PCA_transformed_hypercube)
            output = np.array(y_df).reshape((width,height,number_of_components))
            self.patient.THb = output[:,:,0]

            self.setLabelText("Performing segmentation and color gradient calculations...")
            QApplication.processEvents()


            mean, std, area, length = self.patient.Borders_values()
            skin = self.patient.extract_skin_value()

            print('Mean Border Gradient')
            print(-np.mean(np.diff(mean/skin) / np.diff(np.sqrt(np.array(area)/4/np.pi))))
            hemangioma_to_skin_mean_PCA = self.patient.analysis_of_distributions()
            print('Mean Ratio')
            print(hemangioma_to_skin_mean_PCA)

            self.image_window = PCA_Result_Window(output, self.patient)
            self.image_window.show()

            plt.imshow(output[:,:,0])
            plt.colorbar()
            plt.show()
            plt.imshow(output[:,:,1])
            plt.colorbar()
            plt.show()
            plt.imshow(output[:,:,2])
            plt.colorbar()
            plt.show()
            plt.imshow(output[:,:,3])
            plt.colorbar()
            plt.show()
            # Close the dialog
            self.close()

        if self.patient.processing_approach == "Use BLB":
            if self.patient.processing_area == "Use only selected field for processing":
            # Step 1: Read hypercubes from file paths
                self.setLabelText("Uploading images...")
                QApplication.processEvents()  # Ensure the dialog updates immediately

                y_min, y_max = sorted([self.patient.ROI[1], self.patient.ROI[3]])
                x_min, x_max = sorted([self.patient.ROI[0], self.patient.ROI[2]])

                scf = self.patient.scale_factor_for_image_display

                files_hypercube = self.read_images(self.patient.files_address)
                self.setValue(50)
                ref_hypercube = self.read_images(self.patient.Ref_address)
                self.setValue(100)
                result_hypercube = files_hypercube/ref_hypercube#, where=(ref_hypercube != 0))
                result_hypercube = result_hypercube[:, scf*y_min:scf*y_max, scf*x_min:scf*x_max]
            else:
                files_hypercube = self.read_images(self.patient.files_address)
                self.setValue(50)
                ref_hypercube = self.read_images(self.patient.Ref_address)
                self.setValue(100)
                result_hypercube = files_hypercube/ref_hypercube

            # Step 2: Check for shape compatibility
            if files_hypercube.shape != ref_hypercube.shape:
                QMessageBox.critical(self, "Error", "Hypercube dimensions do not match!")
                self.close()
                return

            # Step 3: Divide files hypercube by reference hypercube
            self.setLabelText("Processing images...")
            QApplication.processEvents()  # Ensure the dialog updates immediately


            Integral_overlap_matrix = self.patient.overlap_integral
            Q, R = la.qr(Integral_overlap_matrix, mode="complete")
            R_new = R[:4]
            Q_new = Q.T[:4]

            amount_of_choromophores = R_new.shape[0]

            Concentration_Matrix = np.zeros([amount_of_choromophores, result_hypercube.shape[1], result_hypercube.shape[2]])
            height_total = result_hypercube.shape[1]  # Total height for progress calculation

            for hight_it in range(height_total):
                for width_it in range(result_hypercube.shape[2]):
                    OD_column = -np.log10(result_hypercube[:, hight_it, width_it] + 1e-10)
                    Concentration_Matrix[:, hight_it, width_it] = spla.solve_triangular(R_new, Q_new.dot(OD_column), lower=False)

                # Update progress
                progress_percent = int((hight_it + 1) / height_total * 100)  # Calculate progress percentage
                self.setValue(progress_percent)

            self.patient.THb = np.absolute(Concentration_Matrix[0,:,:])+np.absolute(Concentration_Matrix[1,:,:]) # Debug: result_hypercube[0,:,:]#

            self.setLabelText("Performing segmentation...")
            QApplication.processEvents()  # Ensure the dialog updates immediately

            # Open image display window after processing
            self.image_window = HyperspectralBLBResults(self.patient)
            self.image_window.show()
            # Close the dialog
            self.close()
            # plt.imshow(Concentration_Matrix[0,:,:])
            # plt.show()

            # Display success message
            # QMessageBox.information(self, "Success", "Processing completed successfully!")
            # print(f"Result hypercube shape: {result_hypercube.shape}")
            # print("Concentration_Matrix shape", Concentration_Matrix.shape)


        # except Exception as e:
        #     QMessageBox.critical(self, "Error", f"An error occurred during processing: {e}")
        #     print(f"Processing error: {e}")


class HyperspectralBLBResults(QMainWindow):
    def __init__(self, patient):
        super().__init__()
        self.patient = patient  # Patient object with properties
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Hyperspectral BLB Results")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout (Horizontal Split)
        main_layout = QHBoxLayout()

        # Left Panel: Display Image from Patient Property 1
        left_panel = QVBoxLayout()
        self.left_image_label = QLabel(self)
        left_panel.addWidget(self.left_image_label)

        # Right Panel: Display Image from Patient Property 2
        right_panel = QVBoxLayout()
        self.right_image_label = QLabel(self)
        right_panel.addWidget(self.right_image_label)

        # Add Text Below the Right Image
        self.ratio_label = QLabel("Ratio", self)
        self.ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(self.ratio_label)

        # Add Text Below the Right Image
        self.probabilities_label = QLabel("Probability", self)
        self.probabilities_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(self.probabilities_label)



        # Add Text Below the Right Image
        self.recommendation_label = QLabel("Recommendation", self)
        self.recommendation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(self.recommendation_label)
        self.recommendation_label.setText('\nНе является лечебной рекомендацией.\nIs not a therapeutic recommendation.')
        self.recommendation_label.setStyleSheet("font-size: 8pt;")

        # Add Save Button Below the Text
        self.save_button = QPushButton("Save Results", self)
        self.save_button.clicked.connect(self.save_patient_object)  # Connect to save function
        right_panel.addWidget(self.save_button)

        # Add Panels with Black Separator Line
        left_widget = QWidget()
        left_widget.setLayout(left_panel)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        separator = QWidget()
        separator.setFixedWidth(2)
        separator.setStyleSheet("background-color: black;")

        # Add to Main Layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(separator)
        main_layout.addWidget(right_widget)

        self.central_widget.setLayout(main_layout)

        # Display Images
        self.display_image_with_contours(self.left_image_label)
        self.display_histogram_plot(self.right_image_label)

    def save_patient_object(self):
        """Save the patient object to a file."""
        import pickle
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Patient Object", "", "Pickle Files (*.pkl)")
        if file_path:
            with open(file_path, 'wb') as file:
                pickle.dump(self.patient, file)

    def display_histogram_plot(self, label):
        """
        Display a violin plot for X and inv_X on the QLabel in the QMainWindow.

        Args:
            label (QLabel): The QLabel where the plot will be displayed.
        """
        # Step 1: Perform Otsu Segmentation
        otsu_result = self.patient.Segmentation_Otsu()


        ####################
        # Step 2: Define mask and inverse mask
        mask = otsu_result.astype(np.uint8)  # Convert to binary (0s and 1s)
        inverse_mask = 255 - mask  # Invert the mask

        # Step 3: Calculate X and inv_X
        X = np.ravel(mask * self.patient.THb) / 255
        inv_X = np.ravel(inverse_mask * self.patient.THb) / 255

        X = np.array((np.array([i for i in X if i!=0]) - self.patient.THb.min())/(self.patient.THb.max() - self.patient.THb.min())*255)
        inv_X = np.array((np.array([i for i in inv_X if i!=0]) - self.patient.THb.min())/(self.patient.THb.max() - self.patient.THb.min())*255)

        new_text = 'S-Coefficient: ' + str(round(np.mean(X)/np.mean(inv_X), 2))
        self.ratio_label.setText(new_text)
        scores_choice = self.patient.check_patient_scores()
        probabilities = self.patient.calculate_probabilities(np.mean(X)/np.mean(inv_X), scores_choice[0], scores_choice[1])
        print(scores_choice)
        result_probabilities = '\n'.join(f"{key}: {value}" for key, value in probabilities.items())
        result_text = ('Based on the hyperspectral assessment, the probabilities (In %)'
                        '\nindicate how likely the patient is to be prescribed'
                        '\none of the following treatment strategies:\n\n' + result_probabilities)

        self.probabilities_label.setText(result_text)

        # Step 4: Create the violin plot
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.hist(X, bins=50, alpha=0.7, label='Hemangioma', color='salmon')
        ax.hist(inv_X, bins=50, alpha=0.7, label='Skin', color='navajowhite')
        # pd.Series(X).plot.kde(alpha=0.7, label='Hemangioma', color='salmon')
        # pd.Series(inv_X).plot.kde(alpha=0.7, label='Skin', color='dodgerblue')

        ax.set_title("Histogram of Total Hemoglobin values")
        ax.set_xlabel("Normalized Values of THb concentration")
        ax.set_yscale('log')
        ax.set_xscale('log')
        ax.set_ylabel("Frequency of occurance")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

        # Step 5: Save the plot to an in-memory buffer
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
        buffer.seek(0)  # Rewind the buffer for reading
        plt.close(fig)  # Close the figure to free memory

        # Step 6: Load the image from the buffer into a QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read(), format='PNG')

        # Step 7: Set the QPixmap on the QLabel
        label.setPixmap(pixmap)

    def display_image_with_contours(self, label):
        """Generate and display an image with Otsu-based contours overlaid on THb."""
        # Step 1: Perform Otsu Segmentation on THb
        otsu_result = self.patient.Segmentation_Otsu()
        # Step 2: Generate contours directly using OpenCV
        otsu_binary = otsu_result.astype(np.uint8)  # Convert binary mask to uint8 (required by OpenCV)
        contours, _ = cv2.findContours(otsu_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Step 3: Normalize the original THb image for visualization
        base_image = self.patient.THb
        normalized_image = cv2.normalize(base_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Step 4: Create a colored version of the image for contour overlay
        color_image = cv2.cvtColor(normalized_image, cv2.COLOR_GRAY2BGR)

        # Step 5: Overlay the contours on the image
        cv2.drawContours(color_image, contours, -1, (0, 0, 255), 2)  # Red contours (BGR: 0,0,255)

        # Step 6: Convert the resulting image to QPixmap
        height, width, channels = color_image.shape
        bytes_per_line = channels * width
        q_image = QImage(color_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        scaled_pixmap = pixmap.scaled(
                pixmap.width() // self.patient.scale_factor_for_image_display, pixmap.height() // self.patient.scale_factor_for_image_display
            )  # Downscale by factor of 2

        # Display in QLabel
        label.setPixmap(scaled_pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet('''QWidget {font-size: 18px;}''')
    app.setStyle('Breeze')
    # Set taskbar icon
    app.setWindowIcon(QIcon("logo.ico"))  # Replace with the actual path to your .ico file

    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window.')
