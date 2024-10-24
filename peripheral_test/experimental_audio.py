##############################################
# STEREO INMP441 MEMS Microphone + I2S Module
##############################################
#
# Recording and saving audio files using MEMS mic
#
##############################################
import pyaudio
import wave
import datetime
import os
import numpy as np

##############################################
# function for setting up pyserial (pyaudio)
##############################################
def pyserial_start():
    audio = pyaudio.PyAudio()  # create pyaudio instantiation
    stream = audio.open(format=pyaudio_format, rate=samp_rate, channels=chans, 
                        input_device_index=dev_index, input=True, frames_per_buffer=CHUNK)
    stream.stop_stream()  # stop stream to prevent overload
    return stream, audio

def pyserial_end(stream, audio):
    stream.close()  # close the stream
    audio.terminate()  # close the pyaudio connection

##############################################
# function for grabbing data from buffer
##############################################
def data_grabber(stream, rec_len):
    stream.start_stream()  # start data stream
    stream.read(CHUNK, exception_on_overflow=False)  # flush port first 
    t_0 = datetime.datetime.now()  # get datetime of recording start
    print('Recording Started.')
    data_frames = []  # initialize list for data frames
    for _ in range(0, int((samp_rate * rec_len) / CHUNK)):
        stream_data = stream.read(CHUNK, exception_on_overflow=False)
        data_frames.append(stream_data)  # append data
    stream.stop_stream()  # stop data stream
    print('Recording Stopped.')
    return data_frames, t_0

##############################################
# Save data as .wav file
##############################################
def data_saver(audio, data_frames, t_0):
    data_folder = './data/'  # folder where data will be saved locally
    if not os.path.isdir(data_folder):
        os.mkdir(data_folder)  # create folder if it doesn't exist
    filename = datetime.datetime.strftime(t_0, '%Y_%m_%d_%H_%M_%S_pyaudio')  # filename based on recording time
    wf = wave.open(data_folder + filename + '.wav', 'wb')  # open .wav file for saving
    wf.setnchannels(chans)  # set channels in .wav file 
    wf.setsampwidth(audio.get_sample_size(pyaudio_format))  # set bit depth in .wav file
    wf.setframerate(samp_rate)  # set sample rate in .wav file
    wf.writeframes(b''.join(data_frames))  # write frames in .wav file
    wf.close()  # close .wav file
    return filename

##############################################
# Main Data Acquisition Procedure
##############################################
if __name__ == "__main__":
    # Acquisition parameters
    CHUNK = 44100  # frames to keep in buffer between reads
    samp_rate = 44100  # sample rate [Hz]
    pyaudio_format = pyaudio.paInt16  # 16-bit device
    chans = 1  # only read 1 channel
    dev_index = 0  # index of sound device
    record_length = 5  # seconds to record

    # Start the stream
    stream, audio = pyserial_start()

    # Record audio
    input('Press Enter to Record Audio')
    data_frames, t_0 = data_grabber(stream, record_length)  # grab the data

    # Save the recorded audio as .wav file
    filename = data_saver(audio, data_frames, t_0)  # save the data
    print(f'Audio saved as {filename}.wav')

    # Close the stream and audio connection
    pyserial_end(stream, audio)