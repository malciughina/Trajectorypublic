import os
import datetime
import numpy as np
import database_io
import pandas as pd

from evaluation import evalaute_segmentation
from trajectory_segmenter import moving_median, moving_avg
from trajectory_segmenter import segment_trajectories
from trajectory_segmenter import segment_trajectories_random, segment_trajectories_random2
from trajectory_segmenter import segment_trajectories_user_adaptive


from collections import defaultdict


def merge_trajectories(trajectories):
    all_traj = []
    for tid in sorted(trajectories, key=lambda x: int(x)):
        traj = trajectories[tid]
        all_traj.extend(traj.object)
    return all_traj


def evaluate(alltraj, traj_list):
    nbr_traj = len(traj_list)
    nbr_points_list = list()
    length_list = list()
    duration_list = list()
    sampling_rate_list = list()
    for t in traj_list:
        nbr_points_list.append(len(t))
        length_list.append(t.length())
        duration_list.append(t.duration())
        sampling_rate_list.extend([t.object[i+1][2] - t.object[i][2] for i in range(0, len(t)-1)])

    avg_nbr_points = np.mean(nbr_points_list)
    avg_length = np.mean(length_list)
    avg_duration = np.mean(duration_list)
    avg_sampling_rate = np.mean(sampling_rate_list)
    std_sampling_rate = np.std(sampling_rate_list)
    med_sampling_rate = np.median(sampling_rate_list)

    time_precision, dist_coverage, mobility_f1 = evalaute_segmentation(alltraj, traj_list, print_report=False)

    res = [nbr_traj, avg_nbr_points, avg_length, avg_duration,
           avg_sampling_rate, std_sampling_rate, med_sampling_rate,
           time_precision, dist_coverage, mobility_f1]
    return res


def run(cur, uid, input_table):
    results = list()
    imh = database_io.load_individual_mobility_history(cur, uid, input_table)

    trajectories = imh['trajectories']
    alltraj = merge_trajectories(trajectories)
    nbr_points = len(alltraj)
    if nbr_points <= 100:
        raise Exception

    sampling_rate_list = [alltraj[i+1][2] - alltraj[i][2] for i in range(0, len(alltraj)-1)]
    avg_sampling_rate = np.mean(sampling_rate_list)
    std_sampling_rate = np.std(sampling_rate_list)
    med_sampling_rate = np.median(sampling_rate_list)
    base_res = [input_table, uid, nbr_points, avg_sampling_rate, std_sampling_rate, med_sampling_rate]


    traj_list, user_temporal_thr = segment_trajectories_user_adaptive(alltraj, uid, temporal_thr=60, spatial_thr=50,
                                                                      max_speed=0.07, gap=60, max_lim=3600 * 48,
                                                                      window=15, smooth_fun=moving_median, min_size=10,return_cut=True)

    eval_res = evaluate(alltraj, traj_list)
    results.append(base_res + ['ATS'] + eval_res + [user_temporal_thr])
    nbr_traj_adaptive = len(traj_list)
    print(len(traj_list))


    traj_list = segment_trajectories_random2(alltraj, uid, nbr_traj=nbr_traj_adaptive)
    eval_res = evaluate(alltraj, traj_list)
    results.append(base_res + ['RND2'] + eval_res + [-1])
    print('pippi',len(traj_list) )

    traj_list = segment_trajectories(alltraj, uid, temporal_thr=1200, spatial_thr=50, max_speed=0.07)
    eval_res = evaluate(alltraj, traj_list)
    results.append(base_res + ['FTS_1200'] + eval_res + [1200])

    traj_list = segment_trajectories(alltraj, uid, temporal_thr=120, spatial_thr=50, max_speed=0.07)
    eval_res = evaluate(alltraj, traj_list)
    results.append(base_res + ['FTS_120'] + eval_res + [120])

    traj_list = segment_trajectories_random(alltraj, uid)
    eval_res = evaluate(alltraj, traj_list)
    results.append(base_res + ['RND1'] + eval_res + [-1])

    #traj_list = segment_trajectories_random(alltraj, uid, nbr_traj=nbr_traj_adaptive)
    #if len(traj_list) > 25:
     #   eval_res = evaluate(alltraj, traj_list)
      #  results.append(base_res + ['RND2'] + eval_res + [-1])

    return results


def main():
    input_table = 'tak.uk_traj'
    path = '/home/agnese/PycharmProjects/TrajectorySegmentation/Risultati/'
    filename = 'LONDON_traj_seg_exp2000.csv'
   # data = pd.read_csv("/home/agnese/PycharmProjects/TrajectorySegmentation/Results/" + "traj_seg_exp100.csv")

    header = ['input_table', 'uid', 'nbr_points', 'avg_sampling_rate', 'std_sampling_rate', 'med_sampling_rate',
              'method', 'nbr_traj', 'avg_nbr_points', 'avg_length', 'avg_duration',
              'avg_sampling_rate_traj', 'std_sampling_rate_traj', 'med_sampling_rate_traj',
              'time_precision', 'dist_coverage', 'mobility_f1', 'temporal_thr']

    processed_users = list()
    if os.path.isfile(filename):
        # os.remove(filename)
        df = pd.read_csv(path+filename)
        processed_users = list(df['uid'])
        fileout = open(filename, 'a')
    else:
        fileout = open(filename, 'w')
        fileout.write('%s\n' % (','.join(header)))
        fileout.flush()

    # users_list = ['100006',
    #               '100022',
    #               '100026',
    #               '10008',
    #               '100086',
    #               '100087',
    #               '100088',
    #               '100090',
    #               '100100',
    #               '100117']

    # con = database_io.get_connection()
    # cur = con.cursor()
    # users_list = database_io.extract_users_list('tak.italy_traj', cur)
    # cur.close()
    #
    con = database_io.get_connection()
    cur = con.cursor()
    users_list = pd.read_csv(path+'london_all_users_list.csv')
    print(users_list.head())


    users_list= users_list['uid'].tolist()

    # return -1

    #users_list = database_io.extract_users_list('tak.uk_traj', cur)
    # users_list = map(int, users_list)
    # print(users_list)

    # users_list = [int(uid) for uid in users_list]
    print(len(users_list))

    count = 0
    nbr_exp = 2000
    #for i, uid in enumerate(users_list):
        #print(datetime.datetime.now(), uid, input_table, '[%s/%s]' % (i, len(users_list)))
        #results = run(cur, uid, input_table)
        #for j, res in enumerate(results):
        #    fileout.write('%s\n' % (','.join([str(r) for r in res])))
        #    f1_dict[res[6]].append(res[-2])
        #    tp_dict[res[6]].append(res[-4])
        #fileout.flush()
    for i, uid in enumerate(users_list):
        print(datetime.datetime.now(), uid, input_table, '[%s/%s]' % (i, len(users_list)))
        if uid in processed_users:
            count+=1
            if count>= nbr_exp:
                break
            continue
        try:
           results = run(cur, uid, input_table)
           for j, res in enumerate(results):
               fileout.write('%s\n' % (','.join([str(r) for r in res])))
               fileout.flush()
        except Exception:
            print(datetime.datetime.now(), uid, input_table, 'Error')
            continue

        count += 1
        if count >= nbr_exp:
            break

    fileout.flush()
    cur.close()
    con.close()

    fileout.close()

    # print('')
    # for k, v in f1_dict.items():
    #     print(k, np.mean(v), np.std(v), np.median(v), np.mean(tp_dict[k]), np.std(tp_dict[k]), np.median(tp_dict[k]))


if __name__ == '__main__':
    main()