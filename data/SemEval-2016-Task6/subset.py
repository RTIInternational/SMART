import csv

def subset(file, target, name):
    with open('{}.csv'.format(file), encoding = 'latin1') as inf, \
         open('{}-{}.csv'.format(file, name), mode = 'wt', encoding = 'utf-8') as outf:
        reader = csv.DictReader(inf)
        writer = csv.DictWriter(outf, fieldnames = ['Tweet', 'Stance'], extrasaction = 'ignore')
        writer.writeheader()
        for row in reader:
            if row['Target'] == target:
                writer.writerow(row)

for file in ['test', 'train']:
    subset(file, 'Feminist Movement', 'feminism')
