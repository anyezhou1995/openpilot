import json
from datetime import datetime
import shutil

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import math
import pickle

plt.ion()



def dist_from_center(x):
    with open("centerline.json", "r") as jsonFile:
        c = np.array(json.load(jsonFile))
    
    out= []
    
    for p3 in x:
        dx= np.square(p3[0] - c[:,0])
        dy= np.square(p3[1] - c[:,1])
        d= np.sqrt(dx + dy)
        
        ind= np.argsort(d)
        p1= c[ind[0]]
        p2= c[ind[1]]
        
        av= p1 - p2
        angle= math.degrees(np.tan(av[1] - av[0]))
        
        if angle > 0:
            d= p2- p1
        else:
            d= p1 - p2
    
        o= abs(np.cross(d,p3-p1)/np.linalg.norm(d))
        
        out.append(o)
        
    return np.array(out)

def relative_speed(ev, dv):
    return np.abs(ev - dv)

def time_to_col(d, v, offset=4.65):
    return d/v

def follow_distance(p1, p2):
    d= np.sqrt(np.square(p1 - p2).sum(axis=1))
    
    return np.abs(d - d.mean())
    
    
def read_log(direcs):
    results= {}
    for ld in direcs:
        LOG_DIR= ld
    
        log_files= [os.path.basename(x) for x in glob.glob(os.path.join(f"{LOG_DIR}", '*'))]
        runs= np.sort(np.array([datetime.strptime(name,"%H:%M:%S_%m-%d-%Y") for name in log_files]))
        for r in reversed(list(runs)):
            direc= r.strftime("%H:%M:%S_%m-%d-%Y")
            
            with open(f"{LOG_DIR}/{direc}/log.json", "r") as jsonFile:
                out = json.load(jsonFile)
                
            l= f"{direc} - {out['notes']} - {out['meta']})"
            meta= out['meta']
            
            print(l)
            keys= []
            for k1 in out['data'][0].keys():
                try:
                    for k2 in out['data'][0][k1].keys():
                        keys.append((k1, k2))
                except:
                    pass
            dd= {}
            for k in keys:
                dd.update({f"{k[0]}-{k[1]}" : np.array([x[k[0]][k[1]] for x in out['data']])})
                
            
            # entry= { 'run' : meta_keys[out['meta']],'stype' : ld}
            
            df = pd.DataFrame.from_dict(dd, orient='index').transpose()
            
            #-----------------------
            #ADJUSTED COLUMNS HERE
            
            #-----------------------
            
            if meta in results.keys():
                results[meta].append(df)
            else:
                results[meta] = [df]
                
    return results

class Logger():
    def __init__(self, message = '', path= 'logs'):
        self.log= {'meta' : message, 'data' : []}
        self.path= path
        
    def save_output(self, message= '', max_runs=1000):

        self.log['notes'] = message
        current_datetime = datetime.now()
        dir_name = current_datetime.strftime("%H:%M:%S_%m-%d-%Y")
        dir_name= f"{self.path}/{dir_name}"
        
        os.mkdir(dir_name)
        os.chmod(dir_name, 0o777)
        
        logs= [os.path.basename(x) for x in glob.glob(os.path.join("logs", '*'))]
        runs= np.array([datetime.strptime(name,"%H:%M:%S_%m-%d-%Y") for name in logs])
        if len(runs) > max_runs:
            direc= min(runs).strftime("%H:%M:%S_%m-%d-%Y")
            shutil.rmtree(f"output/runs/{direc}")
        
        
        jsdata= json.dumps(self.log)
        with open(f"{dir_name}/log.json", "w") as jsonFile:
            jsonFile.write(jsdata)
        os.chmod(f"{dir_name}/log.json", 0o777)
        
    def update(self, frame, data):
        entry= {'frame' : frame}
        
        # print("log", data[0][1]['zeta'])
        
        for d in data:
            entry.update({d[0] : d[1]})
        
        self.log['data'].append(entry)
    

def save_csv(results, direc):
    for k in results.keys():
        wk = k.replace("/", "")
        
        d= direc + f"/{wk}"
        os.mkdir(d)
        l= results[k]
        
        for n, df in enumerate(l):
            
            t= len(df) * 0.02
            df['t']= np.linspace(0,t, len(df))
            
            df['dummy-dist']= ((df['kin-y'] - df['dummy-y'])**2 + (df['kin-x'] - df['dummy-x'])**2).pow(1./2) - 4.7
            
            df.to_csv(d + f"/{n}.csv")
            
def read_csv(direc):
    print(os.listdir(direc))
    out_dict= {}
    keys= [name for name in os.listdir(direc) if os.path.isdir(os.path.join(direc, name))]
    
    for k in keys:
        run_list= []
        for file in glob.glob(os.path.join(direc, k) + '/*.csv'):
            run_list.append(pd.read_csv(file, index_col=0))
        out_dict[k] = run_list
        
    return out_dict
    
def legend_without_duplicate_labels(ax):
    handles, labels = ax.get_legend_handles_labels()
    unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
    ax.legend(*zip(*unique))
    
def keysort(keys, and_phrases, or_phrases):
    out= []
    for k in keys:
        and_add= True
        or_add = False
        for p in and_phrases:
            if p not in k:
                and_add= False
                break
        for p in or_phrases:
            if p in k:
                or_add= True
                break
        if and_add and or_add:
            out.append(k)
    return out
            


if __name__ == '__main__':
    import pandas as pd
    import matplotlib.colors as mcolors
    
    # results= read_log(['logs'])
    # results= pickle.load(open('1023_runs.p', 'rb'))
    # save_csv(results, '1023_csvlogs')
    # results= read_csv('1023_csvlogs')
    
    results= read_log(['sim_logs'])
    
    # results.update(replay_results)
    
    # replay_results= read_csv('1023_data/mil (night replays)')
    # results.update(replay_results)
    
    # ylab= 'RadarModelL1-vLead'
    # ylab= 'RadarModelL2-vLead'
    
    # ylab= 'RadarModelL1-prob'
    # ylab= 'RadarModelL2-prob'
    
    # ylab= 'RadarModelL1-dRel'
    # ylab= 'RadarModelL2-dRel'
    
    ylab= 'kin-v'
    
    
    fig, ax= plt.subplots()
    # ax.invert_xaxis()
    
    all_keys= list(results.keys())
    
    # keys= keysort(all_keys, ['stopping', ],['Clear', 'Rain'])
    # keys= keysort(all_keys, ['stopping', 'Tesla', 'Night'],[''])
    
    # keys= keysort(all_keys, ['stopping', 'REPLAY',],[''])
    keys= keysort(all_keys, ['stopping'],[''])
    
    # keys= ["Long stopping run 30mph. Clear. Black Tesla.", "Long stopping run 30mph. Glare. Black Tesla.", "Long stopping run 30mph. Night w/ headlights. Ambulance."]
    
    c= list(mcolors.TABLEAU_COLORS.keys())
    out= {}
    for n,k in enumerate(keys):
    
        dfs= results[k]
        # df2= results[keys[0]][1]
        
        
        
        cols= []
        for i in range(len(dfs)):
            
            df= dfs[i]
            
            if "Ambulance" in k:
                df['dummy-dist']= ((df['kin-y'] - df['dummy-y'])**2 + (df['kin-x'] - df['dummy-x'])**2).pow(1./2) - 5.57
            else:
                df['dummy-dist']= ((df['kin-y'] - df['dummy-y'])**2 + (df['kin-x'] - df['dummy-x'])**2).pow(1./2) - 4.78
                
            df['ttc'] = df['dummy-dist'] / df['kin-v']
            col= (df['ttc'] < 0.1).any()
            mttc= df['ttc'].min()
                
            t= len(df) * 0.02
            df['t']= np.linspace(0,t, len(df))
            
            a= (df['kin-v'][5:] - np.array(df['kin-v'][0:-5])) / 0.1
            df['a'] = a
            
            ob1= df['RadarModelL1-dRel'] + ((df['RadarModelL1-vLead']**2) / (2 * 2.5))
            ob2= df['RadarModelL2-dRel'] + ((df['RadarModelL2-vLead']**2) / (2 * 2.5))
            
            df['ob'] = np.min(np.stack([ob1.to_numpy(), ob2.to_numpy()]), axis=0)
            df['ob_default'] = df['dummy-dist'] * 1.5# + ((df['kin-v']**2) / (2 * 2.5))
            # df.loc[df['ob'] == 0, 'ob'] = df['ob_default'][df['ob'] == 0]
            # df['obact'] = df['dummy-dist']*1.2# + ((df['kin-v']**2) / (2 * 2.5))
            df['obrat'] = df['ob'] / df['dummy-dist']
            
            # df= df[df['ob'] > 0]
            # df= df[df['dummy-dist'] < 45]
            # df= df[df['dummy-dist'] > 5]
            
            # df= df[df['dummy-dist'] > 10]
            # df= df[df['dummy-dist'] < 25]
            # df= df[np.abs(df['obrat']) < 2]
            
            # df= df[df['ob'] > 0]
            # df= df[df['dummy-v'] < 16]
            # df= df[df['dummy-v'] > 14]
            # df= df[df['kin-v'] > 10]
            # df= df[df['dummy-dist'] < 23]
            # df= df[df['kin-x'] > -300]
             
            
            ob= np.argmin(np.stack([ob1.to_numpy(), ob2.to_numpy()]), axis=0)
            
            # col1= df['kin-v'].iloc[-1] > 0.06
            
            color= c[n]
            # color= cm.Oranges(1 - mttc / 4)
            
            ls= 'solid'
            al= 1
            # if col:
            #     ls= 'dashed'
            #     al= 1
            
            # ax.plot(df['dummy-dist'].iloc[-1], df[ylab].iloc[-1],c=color, label= k, linestyle= 'solid', alpha= 1)
            
            # ax.plot(df['t'], df['kin-v'],color=color, label= k, linestyle= ls, alpha= al)
            # ax.plot(df['dummy-dist'], df['obact'], c= 'black', label= "Distance (m)")
            # ax.plot(df['dummy-dist'], df['ob'], c=color, label= k, linestyle= ls, alpha= al)
            ax.plot(df['dummy-dist'], df['RadarModelL1-dRel'], c=color, label= k, linestyle= ls, alpha= al)
            # ax.plot(df['t'],df['dummy-dist'], label= k, c= color)
            
            # ax.plot(c=color, label= k, linestyle= 'solid', alpha= 0.3)
            
            # cols.append((df['ob'] / df['dummy-dist']).mean())
            # print(k, df['obrat'].mean())
            # ax.scatter(95-n, df['obrat'].mean())
            # cols.append(df['ttc'].min())
        out.update({ k.replace(" REPLAY", "") : cols})
        
    # ax.plot(df['dummy-dist'].iloc[-1], df[ylab].iloc[-1],c='black', label= 'Collision', linestyle= 'dashed', alpha= 1)
        
    # for n in range(len(df2)):
    #     ax.plot(df2[n]['kin-y'], df2[n][ylab], c='orange', label= 'Glare')
    
    plt.title("Replay- ")
    plt.xlabel("Distance (m)")
    plt.ylabel("DetectedDistance")
    # plt.colorbar(location= 'right', label= "Detection ratio ($dr_{mean}$) for $d_{t} > 10m$")
    legend_without_duplicate_labels(ax)