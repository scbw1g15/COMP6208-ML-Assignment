import csv
import os 
import matplotlib.pyplot as plt 

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

fig = plt.figure()
ax=fig.add_subplot(111)
pat_id = 0
markers = ['.','x','^','v']
colours = ['red','green','blue','black']
label = ['sit on bed', 'sit on chair','lying','ambulating']
for index in patient_index:
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
            