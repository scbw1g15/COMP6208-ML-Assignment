import csv
import os 
import matplotlib.pyplot as plt 

class analysis():
    def __init__(self):
        S1_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),'Datasets_Healthy_Older_People','S1_Dataset')
        S1_PATH = S1_PATH.replace('\\','/')
        patient_list = []
        for filename in os.listdir(S1_PATH):
            if filename != 'README.txt':
                data_path = os.path.join(S1_PATH, filename).replace('\\','/')
                data = []
                with open(data_path, 'r', newline='') as csvfile:
                    patient_data = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_MINIMAL)
                    for d in patient_data:
                        data.append(d)
                patient_list.append(data)
        patient_index = []
        for patient in patient_list:
            indexes = [0,0,0,0]
            count = 0
            for data in patient:
                count +=1
                indexes[int(data[-1])-1] = indexes[int(data[-1])-1]+1
            indexes = [a/count for a in indexes]
            patient_index.append(indexes)
        self.patient_activity = patient_index
        self.patient_list = patient_list

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
                #accelerometer data is the only data that will be taken into account for time-series4
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
        ax.legend()
        ax.set_xlabel('Patient ID')
        ax.set_ylabel('Time spent on activity (%)')
        plt.show()
        print ("done")

# an = analysis()
# an.time_series_features(6)    
# filtered_data,filtered_activity = an.filter_unbalances(70)      

# for act in filtered_activity:
#     for ind in act:
#         if ind>0.7:
#             print("op")