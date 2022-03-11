#! /usr/bin/env python3
import argparse
import sys
from os import path
try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
except:
    print('Error. Missing matplotlib module. please install it: python3 -m pip install matplotlib')
try:
    import pandas as pd
except:
    print('Error. Missing pandas module. please install it: python3 -m pip install pandas')
try:
    from rich import print
except:
    print('Error. Missing rich module. please install it: python3 -m pip install rich')


def stopCal(start, durate):
    if durate[-1] == 'd':
        st_new = start+pd.DateOffset(days=int(durate[:-1]))
    return st_new


def lineCal(line, labels: dict):
    ret = [*line[0:2]]
    if line[2].strip().split(' ')[0] == 'after':
        try:
            ret.append(labels[line[2].strip().split(' ')[1]])
        except:
            print(line, labels)
        pass
    else:
        ret.append(pd.to_datetime(line[2]))
    ret.append(stopCal(ret[2], line[3]))
    if line[4] not in labels.keys():
        labels[line[4].strip()] = ret[-1]
    return ret, labels


def buildCD(sessions):
    colors = ['#E64646', '#E69646', '#34D05C', '#34D0C3', '#3475D0']
    i = 0
    c_dict = {}
    for elem in sessions:
        c_dict[elem] = colors[i]
        i += 1
        if i == len(colors):
            i = 0
    return c_dict


def color(row, c_dict):
    return c_dict[row['Session']]


def build(inputFile, display):
    computed = []
    labels = {}
    if path.exists(inputFile):
        with open(inputFile, 'r') as f:
            lines = f.readlines()
    else:
        print("Error. The input file not exists")
        sys.exit()
    header = lines[0].strip().split(',')
    for line in lines[1:]:
        arr = line.strip().split(',')
        elem, labels = lineCal(arr, labels)
        computed.append(elem)
    df = pd.DataFrame(computed, columns=['Session', 'Task', 'Start', 'End'])
    proj_start = df.Start.min()
    df['start_num'] = (df.Start-proj_start).dt.days
    df['end_num'] = (df.End-proj_start).dt.days
    df['days_start_to_end'] = df.end_num - df.start_num
    sessions = df['Session'].unique()
    cdict = buildCD(sessions)
    
    df['color'] = df.apply(color, axis=1, c_dict=cdict)
    if display:
        orDF = pd.read_csv(inputFile)
        print('Input Data:')
        print(orDF)
        print("Output Data:")
        print(df)
        sys.exit()
    return df


def visualize(df, title: str = 'Gantt PLOT', step: int = 1, outputFile: str = None, show: bool = False):
    if show:
        dpi = 100
    else:
        dpi = 300
    if step < 1:
        step = 1
    fd = df[::-1]
    proj_start = df.Start.min()
    fig, (ax, ax1) = plt.subplots(2, figsize=(20, 6), gridspec_kw={
        'height_ratios': [6, 1]}, facecolor='#36454F', dpi=dpi)

    ax.set_facecolor('#36454F')
    ax1.set_facecolor('#36454F')
    # bars
    ax.barh(df.Task, df.days_start_to_end,
            left=df.start_num, color=df.color, alpha=0.5, height=0.6)
    for idx, row in df.iterrows():
        ax.text(row.start_num + (row.days_start_to_end // 2), idx, row.Task,
                va='center', ha='center', alpha=0.8, color='w')
    sessions = df['Session'].unique()
    c_dict = buildCD(sessions)
    id = -0.6
    flag = False
    for session in sessions:
        filter = df[df['Session'] == session]
        if flag:
            ax.axhspan(id, id + len(filter), facecolor='#FFFFFF', alpha=0.2)
            flag = False
        else:
            flag = True
        id += len(filter)

    # grid lines
    ax.set_axisbelow(True)
    ax.xaxis.grid(color='k', linestyle='dashed', alpha=0.4, which='both')

    # ticks
    xticks_labels = pd.date_range(
        proj_start, end=df.End.max()).strftime("%d/%m/%y")
    xticks2 = [index for index, element in enumerate(
        xticks_labels) if element[0:2] == '01']
    ax.set_xticks(xticks2[::step])

    ax.set_xticklabels([element[3:] for index, element in enumerate(
        xticks_labels) if element[0:2] == '01'][::step], color='w')
    ax.set_yticks([])

    plt.setp([ax.get_xticklines()], color='w')

    # align x axis
    ax.set_xlim(0, df.end_num.max())

    # remove spines
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['left'].set_position(('outward', 10))
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_color('w')
    plt.suptitle(title, color='w')

    ##### LEGENDS #####
    legend_elements = []
    for session in sessions:
        legend_elements.append(Patch(facecolor=c_dict[session], label=session))

    legend = ax1.legend(handles=legend_elements,
                        loc='upper center', ncol=5, frameon=False)
    plt.setp(legend.get_texts(), color='w')

    # clean second axis
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    if show:
        plt.show()
    else:
        plt.savefig(outputFile, facecolor='#36454F')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='PyGantt', description='Build simple Gantt diagram from CSV file')
    parser.add_argument('-i', '--input', metavar='FILE', type=str,
                        help='The CSV input file. The default is gantt.csv', default=path.expanduser('./gantt.csv'))
    parser.add_argument('-o', '--output', metavar='FILE', type=str,
                        help='The PNG output file. The default is gantt.png', default=path.expanduser('./gantt.png'))
    parser.add_argument('-t', '--title', metavar='TITLE',
                        help=' Title of the plot', default='Gantt Plot')
    parser.add_argument('-x', '--xticks', metavar='NUM', type=int,
                        help='Set the x Thicks frequency to NUM. The default is every month (1)', default=1)
    parser.add_argument('-s', '--show', action='store_true',
                        help='Display the plot. No output will be saved', default=False)
    parser.add_argument('-d', '--display', action='store_true',
                        help='Display the input data and the computed one and exit', default=False)
    args = parser.parse_args()
    df = build(args.input, args.display)
    visualize(df, args.title, outputFile=args.output,
              show=args.show, step=args.xticks)
