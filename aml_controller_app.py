# TODO: Put the GUI and the timer on different threads

from AML_NGC3 import NGC3 as AML

import sys
import os
import time as t
import pyvisa as visa
import pandas as pd

from PyQt5 import QtWidgets as qtw
from PyQt5 import uic
from PyQt5 import QtCore as qtc


UI_gauge_controller, baseClass = uic.loadUiType('aml_pressure_gauge_widget.ui')


class IonGaugeController(baseClass, UI_gauge_controller):

    def __init__(self, *args, **kwargs):
        super(IonGaugeController, self).__init__(*args, **kwargs)
        self.rm = visa.ResourceManager("@py")

        self.column_names = ["Time", "Ion Gauge", "Pirani 1", "Pirani 2", "Active Gauge", "Temperature"]
        self.data = pd.DataFrame(columns=self.column_names)
        self.available_gauges = []
        self.units = []
        self.start_time = ""
        self.gauge_plotted = ""
        self.filename = ""
        self.timer = qtc.QTimer(self, interval=1000, timeout=self.next_datum)

        self.setupUi(self)
        self.refresh_com_ports()

        # signals and slots
        self.connect_button.clicked.connect(self.connect)
        self.disconnect_button.clicked.connect(self.disconnect)
        self.refresh_button.clicked.connect(self.refresh_com_ports)

        self.local_radio_button.toggled.connect(self.set_control)
        self.remote_radio_button.toggled.connect(self.set_control)

        self.gauge_on_button.clicked.connect(self.gauge_on)
        self.gauge_off_button.clicked.connect(self.gauge_off)

        # self.single_collection_radio_button.toggled.connect(self.set_single_collection)
        # self.time_series_radio_button.toggled.connect(self.set_time_series)

        # self.filename_line_edit.textChanged.connect(self.overwrite_warning)
        self.next_button.clicked.connect(self.next_datum)
        self.start_save_button.clicked.connect(self.start_save)
        self.stop_button.clicked.connect(self.stop)
        self.save_button.clicked.connect(self.check_filename)
        self.save_button.clicked.connect(self.save)
        self.clear_button.clicked.connect(self.clear)

        # Gray out button when not connected
        self.disconnect_button.setEnabled(False)
        self.gauge_on_button.setEnabled(False)
        self.gauge_off_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.start_save_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        self.show()

        # self.connect()
        # self.start_save()

    def connect(self):
        port = self.com_port_box.currentText()
        if port != "":
            self.ion_gauge = AML(self.rm, port, delay=False)
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.gauge_on_button.setEnabled(True)
            self.gauge_off_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.start_save_button.setEnabled(True)
            self.save_button.setEnabled(True)
        else:
            print('No resource available')

    def disconnect(self):
        self.ion_gauge.close()
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.gauge_on_button.setEnabled(False)
        self.gauge_off_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.start_save_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def refresh_com_ports(self):
        ports = self.rm.list_resources()
        self.com_port_box.clear()
        self.com_port_box.addItems(ports)

    def set_control(self):
        if self.remote_radio_button.isChecked():
            self.ion_gauge.remote = True
        else:
            self.ion_gauge.remote = False

    def gauge_on(self):
        if self.filament1_radio_button.isChecked():
            self.ion_gauge.filament = 1
        elif self.filament2_radio_button.isChecked():
            self.ion_gauge.filament = 2

        if self.half_mA_radio_button.isChecked():
            self.ion_gauge.current = 0.5
        elif self.five_mA_radio_button.isChecked():
            # TODO: Make a pop-up warning for high current
            self.ion_gauge.current = 5


    def gauge_off(self):
        self.ion_gauge.gauge_off()


    def next_datum(self):
        print('Getting next datum')
        status_read = self.ion_gauge.status()
        new_data = [status_read[i][1] for i, e in enumerate(status_read)]
        print('New datum received')
        # If the loop just started, the time starts, the units and the available gauges are found
        if self.start_time == "":
            self.start_time = t.time()

            self.units = [status_read[i][2] for i, e in enumerate(status_read)]
            self.units = ['s'] + self.units

            for i, e in enumerate(new_data):
                if e == 'NA':
                    self.available_gauges.append(False)
                elif e == 1000.0 and i in [1, 2]:
                    self.available_gauges.append(True)
                elif e == 1024 and i == 4:
                    self.available_gauges.append(False)
                else:
                    self.available_gauges.append(True)

        time = t.time() - self.start_time
        print(time)

        new_data.insert(0, time)
        self.data.loc[self.data.shape[0]] = new_data
        print('Datum appended to previous data')

        self.save()
        self.plot()

    def plot(self):
        print('Formatting data for plot')

        if self.data['Time'].iloc[-1] < 60*5:
            time_units = 's'
            time = self.data['Time']
        elif 60*5 <= self.data['Time'].iloc[-1] < 60*60*3:
            time_units = 'm'
            time = self.data['Time']/60
        elif 60*60*3 <= self.data['Time'].iloc[-1] < 60*60*24*2:
            time_units = 'h'
            time = self.data['Time']/(60*60)
        else:
            time_units = 'd'
            time = self.data['Time']/(60*60*24)

        if self.ion_gauge_radio_button.isChecked():
            self.gauge_plotted = 'Ion Gauge'
        if self.pirani_1_radio_button.isChecked():
            self.gauge_plotted = 'Pirani 1'
        if self.pirani_2_radio_button.isChecked():
            self.gauge_plotted = 'Pirani 2'
        if self.active_gauge_radio_button.isChecked():
            self.gauge_plotted = 'Active Gauge'
        if self.temperature_radio_button.isChecked():
            self.gauge_plotted = 'Temperature'

        # print(self.data[self.gauge_plotted].iloc[0])
        if not isinstance(self.data[self.gauge_plotted].iloc[0], (int, float)):
            self.stop()

        if self.data.columns.get_loc(self.gauge_plotted) in {1, 2, 3, 4}:
            y_quantity = "Pressure"
        else:
            y_quantity = "Temperature"

        self.units_on_plot = self.units[self.data.columns.get_loc(self.gauge_plotted)]

        print('Plotting')
        self.plot_widget.cla()
        self.plot_widget.set_xlabel(time_units)
        self.plot_widget.set_ylabel(y_quantity, self.units_on_plot)
        self.plot_widget.plot(time, self.data[self.gauge_plotted])
        self.plot_widget.draw()

    def start_save(self):

        interval = float(self.time_interval_line_edit.text())
        if self.minutes_radio_button.isChecked():
            interval *= 60
        if interval < 1:
            interval = 1
            self.time_interval_line_edit.setText('1')
        self.timer.setInterval(interval*1000)
        self.check_filename()
        self.next_datum()
        self.timer.start()

        self.disconnect_button.setEnabled(False)
        self.local_radio_button.setEnabled(False)
        self.remote_radio_button.setEnabled(False)
        self.filament1_radio_button.setEnabled(False)
        self.filament2_radio_button.setEnabled(False)
        self.half_mA_radio_button.setEnabled(False)
        self.five_mA_radio_button.setEnabled(False)
        self.gauge_off_button.setEnabled(False)

        self.ion_gauge_radio_button.setEnabled(False)
        self.pirani_1_radio_button.setEnabled(False)
        self.pirani_2_radio_button.setEnabled(False)
        self.active_gauge_radio_button.setEnabled(False)
        self.temperature_radio_button.setEnabled(False)

        self.time_interval_line_edit.setEnabled(False)
        self.minutes_radio_button.setEnabled(False)
        self.seconds_radio_button.setEnabled(False)
        self.filename_line_edit.setEnabled(False)

        self.next_button.setEnabled(False)
        self.start_save_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)

    def stop(self):
        self.timer.stop()

        self.disconnect_button.setEnabled(True)
        self.local_radio_button.setEnabled(True)
        self.remote_radio_button.setEnabled(True)
        self.filament1_radio_button.setEnabled(True)
        self.filament2_radio_button.setEnabled(True)
        self.half_mA_radio_button.setEnabled(True)
        self.five_mA_radio_button.setEnabled(True)
        self.gauge_off_button.setEnabled(True)

        self.ion_gauge_radio_button.setEnabled(True)
        self.pirani_1_radio_button.setEnabled(True)
        self.pirani_2_radio_button.setEnabled(True)
        self.active_gauge_radio_button.setEnabled(True)
        self.temperature_radio_button.setEnabled(True)

        self.time_interval_line_edit.setEnabled(True)
        self.minutes_radio_button.setEnabled(True)
        self.seconds_radio_button.setEnabled(True)
        self.filename_line_edit.setEnabled(True)

        self.next_button.setEnabled(True)
        self.start_save_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)
        self.clear_button.setEnabled(True)


    def check_filename(self):
        self.filename = self.filename_line_edit.text()

        if self.filename == "":
            self.filename == 'tmp'
        elif self.filename[-1] == "/":
            self.filename += 'tmp'

        path, file = os.path.split(self.filename)

        if os.path.isfile(self.filename + '.csv') and file != 'tmp':
            print("Filename already exists. Date and time appended to filename\n")
            self.filename += t.strftime("%Y-%m-%d_%H-%M-%S")
        if os.path.isfile(self.filename + '.tsv') and file != 'tmp':
            print("Filename already exists. Date and time appended to filename\n")
            self.filename += t.strftime("%Y-%m-%d_%H-%M-%S")
        if os.path.isfile(self.filename + '.h5') and file != 'tmp':
            print("Filename already exists. Date and time appended to filename\n")
            self.filename += t.strftime("%Y-%m-%d_%H-%M-%S")

        if not os.path.exists(path):
            os.makedirs(path)


    def save(self):
        temp_names = [self.column_names[i]+ " ("+self.units[i]+")" for i in range(len(self.units))]
        self.data.columns = temp_names
        if self.csv_check_box.isChecked():
            self.data.to_csv(self.filename+".csv")
        if self.tsv_check_box.isChecked():
            self.data.to_csv(self.filename+".tsv", sep='\t')
        if self.h5_check_box.isChecked():
            self.data.to_hdf(self.filename+".h5", key='pressure', format='fixed')
        self.data.columns = self.column_names

    def clear(self):
        self.data = self.data[0:0]
        print(self.data)
        self.start_time = ""
        self.available_gauges = []
        self.plot_widget.set_xlabel('')
        self.plot_widget.set_ylabel('','')
        self.plot_widget.cla()
        self.plot_widget.set_yscale_log()
        self.plot_widget.draw()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = IonGaugeController()
    sys.exit(app.exec())

