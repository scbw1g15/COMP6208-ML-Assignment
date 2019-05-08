import csv
import os 
import matplotlib.pyplot as plt 
import numpy as np
import pandas as pd
from scipy.interpolate import griddata,interp1d
from scipy.fftpack import fft, rfft
from scipy.signal import cheby2
from scipy import signal
from math import atan2,sqrt

# ['time','frontal','vertical','lateral','id','rssi','phase','frequency','roll','pitch','activity']
class Tool():
    def __init__(self):
        S1_PATH = os.path.join('COMP6208-ML-Assignment','Datasets_Healthy_Older_People','S1_Dataset')
        # S1_PATH = os.path.join('..','..','Datasets_Healthy_Older_People','S1_Dataset')
        # S2_PATH = os.path.join('..','..','Datasets_Healthy_Older_People','S2_Dataset')
        # S1_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),'Datasets_Healthy_Older_People','S1_Dataset')
        # S1_PATH = S1_PATH.replace('\\','/')
        patient_list = []
        for filename in os.listdir(S1_PATH):
            if filename != 'README.txt':
                data_path = os.path.join(S1_PATH, filename).replace('\\','/')
                data = []
                with open(data_path, 'r', newline='') as csvfile:
                    patient_data = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_MINIMAL)
                    for d in patient_data:
                        d = [float(x) for x in d]
                        data.append(d)
                    data = [*zip(*data)]
                    roll, pitch, yaw = self.get_pitch_roll(data[1],data[2],data[3])
                    data.insert(-1,roll)
                    data.insert(-1,pitch)
                    data.insert(-1,yaw)
                    data = [*zip(*data)]
                patient_list.append(data)
        patient_index = []
        for patient in patient_list:
            indexes = [0,0,0,0]
            count = 0
            for data in patient:
                count +=1
                indexes[int(data[-1])-1] += 1
            indexes = [a/count for a in indexes]
            patient_index.append(indexes)
        self.patient_activity = patient_index
        self.patient_list = patient_list
        self.interpolated_data = []

    def get_pitch_roll(self,x_list ,z_list, y_list):
        roll, pitch, yaw = [], [], []
        for i in range(len(x_list)):
            x,y,z = float(x_list[i]),float(y_list[i]),float(z_list[i])
            # roll.append(atan2((y),sqrt(z * z + x * x ))*57.3)
            # yaw.append(atan2((z),sqrt(y * y  + x * x ))*57.3)
            # pitch.append(atan2((x) , sqrt(y * y  + z * z ))*57.3)
            roll.append(atan2((x) , sqrt(y * y  + z * z )))
            pitch.append(atan2(y,z))
            yaw.append(atan2(y,x))
        return roll,pitch,yaw

    def filter_unbalances(self, percentage):
        percentage_cutoff = percentage/100
        patient_list_filtered = self.patient_list.copy()
        patient_activity_filtered = self.patient_activity.copy()
        count = 0
        for i in range(len(self.patient_activity)):
            patient = self.patient_activity[i]
            for index in patient:
                #activity index for each activity
                if index >percentage_cutoff:
                    patient_list_filtered.pop(i-count)
                    patient_activity_filtered.pop(i-count)
                    count+=1
        print("Number of Remaining Patients: ", len(patient_list_filtered))
        return patient_list_filtered,patient_activity_filtered
    
    def time_series_features(self,time_steps):
        ts_patient_list = []
        patient_list = self.patient_list.copy()
        for patient in patient_list:
            t_patient = [*zip(*patient)]
            for i in range(1,time_steps+1):
                #accelerometer data is the only data that will be taken into account for time-series
                none_array = [None for t in range(i)]
                x = none_array+list(t_patient[1])[i::]
                y = none_array+list(t_patient[2])[i::]
                z = none_array+list(t_patient[3])[i::]
                t_patient.append(x)
                t_patient.append(y)
                t_patient.append(z)
                
            ut_patient = [*zip(*t_patient)][time_steps::]
            ts_patient_list.append(ut_patient)
        return ts_patient_list

    def pad_label(self,new_time_stamp, old_time_stamp, labels):
        new_labels = []
        pt_old = 0
        for i in new_time_stamp:
            if i >= old_time_stamp[pt_old]:
                new_labels.append(labels[pt_old])
                pt_old +=1
            else:
                new_labels.append(-1)
        return new_labels



    def interpolate_timeseries(self,window, steps, kind='linear', filtering = False, filter_features = [], ts_features = [1,2,3,4,5,6,7,8,9,10]):
        #‘linear’, ‘nearest’, ‘zero’, ‘slinear’, ‘quadratic’, ‘cubic’, 
        # ‘previous’, ‘next’, where ‘zero’, ‘slinear’, ‘quadratic’ and ‘cubic’ for type
        # window in seconds, steps also in seconds, window is how far back we look at for the time series management 
        # data is number of features needed
        # for feature in data[1::]: 
        #     interpolated_data.append(interp1d(np.arange(feature)))
        ts_patient_list = []
        labels_list = []
        patient_list = self.patient_list.copy()
        headers = ['time','frontal','vertical','lateral','id','rssi','phase','frequency','roll','pitch','Yaw','activity']
        indexing1 =[headers[g] for g in ts_features]
        # for i in np.arange(0,window,steps):#creating symmetrical multi index
        #     for f in ts_features:
        #         title = headers[f] + " t -"+str(round(i*10)/10)
        #         indexing1.append(title)
        for p in range(len(patient_list)):
            patient= patient_list[p]
            t_patient = [*zip(*patient)]
            time_stamp = t_patient[0]

            interp_data = []
            end = float(time_stamp[-1])
            new_time_stamp = np.arange(0,end,steps)
            interp_data.append(new_time_stamp)
            for a in range(1,len(t_patient)):
                feature = t_patient[a]
                if a==11:
                    # function = interp1d(time_stamp,feature,kind = 'zero')
                    interp_feature = self.pad_label(new_time_stamp,time_stamp,feature)# padding
                elif a==4:
                    function = interp1d(time_stamp,feature,kind = 'previous') # uncomment for continuous data interp
                    interp_feature = function(new_time_stamp)
                else:
                    function = interp1d(time_stamp,feature, kind = kind)
                    interp_feature = function(new_time_stamp)
                    # Filtering function
                    if filtering == True:
                        if a in filter_features:
                            filt_interp_feature = self.lowpass(interp_feature,3 ,10) 
                            interp_feature = filt_interp_feature  
                interp_data.append(interp_feature)
            patient_labels = interp_data[11]
            interp_data = [interp_data[r] for r in ts_features]
            #turn to time series data 
            c = 1
            for i in np.arange(steps,window, steps):#repeats for the number of elements in the window
                padding = [0 for x in range(c)]
                c+=1
                for z in range(len(ts_features)):
                    shifted_feature = np.array(list(padding)+list(interp_data[z]))
                    interp_data.append(shifted_feature[0:len(new_time_stamp)])
            ts_patient = [*zip(*interp_data)]
            #Clean the interpolated labels
            patient_labels_clean = [x for x in patient_labels if x>0]
            # plotting################################################################################################
            # function1 = interp1d(time_stamp,t_patient[1], kind = 'linear')
            # # function2 = interp1d(time_stamp,t_patient[1], kind = 'quadratic')
            # interp_types = ['Non','Linear-With Filter','Linear-W/out Filter','Quadratic']
            # f, axarr = plt.subplots(3, sharex=True, sharey=False)
            # f.suptitle('Euler Coordinates Transform')
            # patient_labels_clean = t_patient[11]
            # axarr[0].scatter(time_stamp, t_patient[1],marker = '.',color = 'r', label ="Frontal" )
            # axarr[0].scatter(time_stamp, t_patient[2],marker = '.',color = 'g', label ="Vertical" )
            # axarr[0].scatter(time_stamp, t_patient[3],marker = '.',color = 'b', label = "Lateral")
            # axarr[1].plot(new_time_stamp, interp_data[5],marker = '',color = 'r', label ="Roll")
            # axarr[1].plot(new_time_stamp, interp_data[6],marker = '',color = 'g', label ="Pitch")
            # # axarr[1].plot(new_time_stamp, interp_data[7],marker = '',color = 'b', label ="Yaw")
            # axarr[2].scatter(time_stamp, patient_labels_clean, label = "Labels")
            # # axarr[2].plot(new_time_stamp, function1(new_time_stamp),marker = '',color = 'g', label =interp_types[2])
            # # axarr[3].scatter(new_time_stamp, function2(new_time_stamp),marker = '.',color = 'y', label =interp_types[3])
            # for i,ax in enumerate(axarr):
            #     ax.set(xlabel='Time (s)', ylabel='Acceleration (g)')
            #     ax.legend()
            
            # plt.show()
            #########################################################################################################################################


            ts_patient_cleaned = [ts_patient[x] for x in range(len(patient_labels)) if patient_labels[x]>0]#clean the interpolated label features

            # patient_labels_clean = t_patient[11]
            indexing2 = np.array(np.arange(0,window,steps))
            indexes = pd.MultiIndex.from_product([indexing2,indexing1])
            pd_p = pd.DataFrame(ts_patient_cleaned,columns=indexes)
            ts_patient_list.append(pd_p)   
            labels_list.append(patient_labels_clean)
        
        return ts_patient_list, labels_list

    def lowpass(self,data, order, cutoff):
        xn = data
        b, a = signal.butter(order, cutoff, fs = 1000)
        y = signal.filtfilt(b, a, xn)
        return y


    def time_series_features_window_steps(self,window,steps,data):
        #data defines how many features are going to be time series fixed
        #window defined in seconds and steps that are taken into account 
        ts_patient_list = []
        patient_list = self.patient_list.copy()
        for p in range(len(patient_list)):
            patient= patient_list[p]
            t_patient = [*zip(*patient)]
            t_patient += [ [0] for k in range(int(window/steps)*data)] #necessary to append to index
            for t in range(1,len(t_patient[0])):
                index=1
                time_table = np.arange(steps,window+steps,steps)
                
                for i_t_c in range(int(window/steps)):
                    
                    if index<=t:
                        timestamp_prev = float(t_patient[0][t-index])
                    else:
                        for r in range(i_t_c,int(window/steps)):
                            for i in range(data):
                                t_patient[9+r*data+i].append(0)
                        break
                    t_current = float(t_patient[0][t]) - time_table[i_t_c]
                    if timestamp_prev>=t_current:
                        for i in range(data):
                            t_patient[9+i_t_c*data+i].append(t_patient[1+i][t-index])
                        index+=1
                    else:
                        for i in range(data):
                            t_patient[9+i_t_c*data+i].append(0)
            ut_patient = [*zip(*t_patient)]#untransposed
            # ut_patient = self.interpolate(ut_patient)
            ts_patient_list.append(ut_patient)
        return ts_patient_list
    
    # def time_series_features_window2(self,window,steps,data,interpolation): replaced by interpolate
    #     #window and steps given in seconds
    #     ts_patient_list = []
    #     patient_list = self.patient_list.copy()
    #     for p in range(len(patient_list)):
    #         patient= patient_list[p]
    #         t_patient = [*zip(*patient)]
    #         p1 = 0
    #         time_series_data = [[] for a in range(data)]
    #         end = float(t_patient[0][-1])#last time_stamp in patient record
    #         for p2 in np.arange(0,end,steps):
    #             timestamp = float(t_patient[0][p1])
    #             if p2 >= timestamp:
    #                 for a in range(data):
    #                     time_series_data[a].append(t_patient[a][p1])
    #                 p1+=1
    #             else:
    #                 for a in range(data):
    #                     time_series_data[a].append(0) 
    #     return ts_patient_list

    def plot(self):
        fig = plt.figure()
        ax=fig.add_subplot(111)
        pat_id = 0
        markers = ['.','x','^','v']
        colours = ['red','green','blue','black']
        label = ['sit on bed', 'sit on chair','lying','ambulating']
        for index in self.patient_activity:
            if not pat_id:
                for idx, ind in enumerate(index):
                    ax.scatter(pat_id,ind,c = colours[idx],marker=markers[idx],label = label[idx])
            else:
                for idx, ind in enumerate(index):
                    ax.scatter(pat_id,ind,c = colours[idx],marker=markers[idx])
            pat_id += 1
        ax.legend(loc = 1)
        ax.set_xlabel('Patient ID')
        ax.set_ylabel('Time spent on activity (%)')
        plt.show()
        print ("Done")




# an = Tool()
# time_series_patients, patients_labels = an.interpolate_timeseries(10,0.1,ts_features=[1,2,3,4,5,8,9,], kind='linear')
# # # # # time_patients = an.time_series_features_window2(5.0,0.1,4,True)
# sum = 0
# for i in patients_labels:
#     sum = sum+len(i)
# print(sum)

# sum=0


# for i in time_series_patients:
#     sum = sum+len(i)
# print(sum)
# # filtered_data,filtered_activity = an.filter_unbalances(60) 
   
# print("Done") 
# for act in filtered_activity:
#     for ind in act:
#         if ind>0.7:
#             print("op")