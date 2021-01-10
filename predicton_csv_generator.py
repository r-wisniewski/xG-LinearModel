import csv

headings = ["X Location", "Y Location", "Strength"]

#create the input csv
with open("prediction.csv", mode="w") as results:
                results_writer = csv.writer(results, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                results_writer.writerow(headings)

#x is from the goal line towards center ice
#y is boards to boards
min_y = 0
min_x = 0 
max_y = 301
max_x = 297

for s in range(-2,3):
    print("Working on strength: ", s)
    for x in range(min_x,max_x,1):
        for y in range(min_y,max_y,1):
            array = [x,y,s]
            with open("prediction.csv", mode="a") as results:
                results_writer = csv.writer(results, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                results_writer.writerow(array)