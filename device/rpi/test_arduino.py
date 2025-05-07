import serial

arduino = serial.Serial('/dev/ttyACM0', 9600)
arduino.write(bytearray([255, 0, 0]))  # Красный
print(arduino.readline().decode().strip())