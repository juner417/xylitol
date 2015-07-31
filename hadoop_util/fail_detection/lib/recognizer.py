#!/usr/bin/python
#-*- coding: utf-8 -*-
# fail recognizer
# file indent 4 space
import os, sys
import socket, subprocess, MySQLdb, logging, ConfigParser, urllib2, re, time, types, getpass
import commons

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(levelname)s] %(message)s')

class SvcRecog(object):
    def __init__(self, svc, config_file):
        # Initialize Recognizer object
        # config_file is must full path
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        logging.info('[%s] service object is created - config:%s' % (svc, config_file))
        self.svc = svc
        self.svc_acc = config.get(svc, svc.split('-')[0]+'_acc')
        self.svc_home = config.get(svc, svc.split('-')[0]+'_home')
        self.svc_host = config.get(svc, svc.split('-')[0]+'_host')
        self.svc_url = config.get(svc, svc.split('-')[0]+'_url')
        self.svc_port = config.get(svc, svc.split('-')[0]+'_port')
        self.mail_recv = config.get('alert', 'mail_recv')
        self.mail_send = config.get('alert', 'mail_send')
        self.jira_recv = config.get('alert', 'jira_recv')
        self.jira_send = config.get('alert', 'jira_send')
        self.svc_err = []
        self.res_arr = {} # 0 : normal, 1: warnning, -1: error
        self.err_msg = {}

        if svc == 'db':
            self.db_name = config.get(svc, svc.split('-')[0]+'_db')
            self.db_user = config.get(svc, svc.split('-')[0]+'_user')
            self.db_passwd = config.get(svc, svc.split('-')[0]+'_passwd')
            self.db_games = config.get(svc, svc.split('-')[0]+'_games').split(',')
        else:
            self.svc_pid_file = config.get(svc, svc.split('-')[0]+'_pid')
    
    def is_port_open(self):
        # 서비스 포트 확인
        svc_url = self.svc_url
        svc_port = int(self.svc_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        try:
            sock.connect((svc_url, svc_port))
            self.svc_err.append(0)
            self.res_arr['port'] = 'Open'
            logging.info('[%s] service port open %s:%s' % (self.svc, svc_url,svc_port))
            sock.close
        except: 
            self.svc_err.append(-1)
            self.res_arr['port'] = 'Close'
            self.err_msg['port'] = '[%s][FAIL] service port has closed %s:%s' % (self.svc, svc_url,svc_port)
            logging.error('[%s] service port has closed %s:%s' % (self.svc, svc_url,svc_port))
            sock.close
    
    def is_pid_exist(self):
        # 서비스 pid 파일 확인 
        ssh = subprocess.Popen(['ssh', self.svc_acc+'@'+self.svc_host, 'cat %s' % self.svc_pid_file ], 
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
            
        pid = ssh.stdout.readline().strip('\n')
        ssh.terminate()
        # pid 확인했으면 그 pid로 프로세스 확인
        if pid != "":
            pid_dir = subprocess.Popen(['ssh', self.svc_acc+'@'+self.svc_host, '[ -d /proc/%s ] && echo $?' % pid], 
                                       shell=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            pid_exist = pid_dir.stdout.readline().strip('\n')
            pid_dir.terminate()

            self.svc_err.append(0)
            logging.info('[%s] %s pid : %s, process exist! ' % (self.svc, self.svc_host, pid))
            self.res_arr['pid'] = pid
        else: 
            pid = -1
            self.svc_err.append(pid)
            logging.error('[%s] %s server has not pidfile ' % (self.svc, self.svc_host))
            self.res_arr['pid'] = pid
            self.err_msg['pid'] = '[%s][FAIL] %s server has not pidfile ' % (self.svc, self.svc_host)
   
    def set_heap_size(self):
        # subprocess로 jstat -gc [pid]  heap size 획득
        # java lib만들면 없앨 예정(임시)
        pid = self.res_arr['pid']
        if pid == -1:
            logging.error('[%s] Cannot read heap size. because service has not pid. ' %(self.svc))
            err = [-1]
        else:
            heap_pipe = subprocess.Popen(['ssh', self.svc_acc+'@'+self.svc_host, '/usr/lib/jvm/java-6/bin/jstat',
                                        '-gc', self.res_arr['pid']],
                                         shell=False,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, close_fds=True)
            err = heap_pipe.stderr.readlines()

        if len(err) == 0:
            res_tmp = heap_pipe.stdout.readlines()
            heap = res_tmp[1].strip('\n').split()
            # 결과 저장
            total = float(heap[0]) + float(heap[1]) + float(heap[4]) + float(heap[6]) + float(heap[8])
            use = float(heap[2]) + float(heap[3]) + float(heap[5]) + float(heap[7]) + float(heap[9])
            per = round(use / total *100, 2)
            self.heap_total_gb = round(total/1024/1024,2)
            self.heap_use_gb = round( use/1024/1024,2)

            self.svc_err.append(0)
            self.res_arr['heap_size'] = '%s/%s(GB) %s %%' %(self.heap_use_gb, self.heap_total_gb, per)
            logging.info('[%s] service heap size : %s / %s (GB) - %s %%' % (self.svc,
                          self.heap_use_gb, self.heap_total_gb, per))
        else:
            self.heap_total_gb = -1
            self.heap_use_gb = -1
            self.svc_err.append(-1)
            self.res_arr['heap_size'] = -1
            self.err_msg['heap_size'] = '[%s][FAIL] Fail to loading heap size' % (self.svc)
 
    def detect_error(self):
        #check the error count
        self.res_table = ""
        self.jira_table = ""
        error_cnt = self.svc_err.count(-1)
        warn_cnt = self.svc_err.count(1)

        if error_cnt == 0 and warn_cnt == 0:
            logging.info('[%s] service is FINE' % self.svc)
            self.err_msg['total_result'] = '[%s] A service is fine ' % (self.svc) 
        elif error_cnt == 0 and warn_cnt < 3:
            logging.info('[%s] service is FINE, But you must check warn msg' % self.svc)
            self.err_msg['total_result'] = '[%s] A service is fine, But %s warn msg' % (self.svc, warn_cnt)
        else:
            logging.info('[%s] service is NOT good (error:%s, warn:%s)' % (self.svc, error_cnt, warn_cnt))
            self.err_msg['total_result'] = '[%s] A service NOT good (error:%s, warn:%s) ' % (
                                            self.svc, error_cnt, warn_cnt) 

        # create email table
        self.res_table = commons.create_table(0, self.svc+' STATUS')
        status = self.get_reskey()
        for i in status:
            if i == "comment": 
                self.res_table += commons.res_mapping(i, self.err_msg)

                # create jira table
                self.jira_table = '||%s result|' % (self.svc)
                keys = self.err_msg.keys()
                self.jira_table += '%s \n' % self.err_msg['total_result']
                keys.remove('total_result')
                for key in keys:  
                    if isinstance(self.err_msg[key], types.ListType):
                        for val in self.err_msg[key]:
                            self.jira_table += '%s \n' % val
                    else:
                        self.jira_table += '%s \n' % self.err_msg[key]
                self.jira_table += '| \n'
            else:
                self.res_table += commons.res_mapping(i, self.res_arr[i])

        self.res_table += commons.create_table(1)

    def get_reskey(self):
        # self.res_arr, self.err_msg dic의 key를 return
        # 이걸로 detect_error 호출할때 status를 배열로 전달
        # res_arr key에 comment를 추가하는 이유는 comment는 저장안하기 때문에
        keys = self.res_arr.keys() 
        keys.append('comment')
        return keys
    
    def get_restable(self):
        return self.res_table

    def get_jiratable(self):
        return self.jira_table

    def get_resarr(self):
        return self.res_arr

    def get_errmsg(self):
        return self.err_msg
    
    def get_svcname(self):
        #print(self.svc)
        return self.svc

        
class HadoopSvcRecog(SvcRecog):
    def __init__(self, config_file):
        SvcRecog.__init__(self, 'hadoop', config_file)
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        logging.info('[%s] additional parameter read: %s' % (self.svc, config_file))
        self.hadoop_monitor_port = config.get('hadoop', 'hadoop_monitor_port')
        self.hadoop_tt_nodes = int(config.get('hadoop', 'hadoop_tt_nodes'))

    def set_nodes(self):
        # jobtracker.jsp에서 nodes 개수 획득
        # java lib만들면 없앨 예정(임시)
        try: 
            resp = urllib2.urlopen("http://%s:%s/jobtracker.jsp" %(self.svc_url, self.hadoop_monitor_port))
            web_pg = resp.read() 
            pattern = "machines.jsp\?type=active"
            for line in web_pg.split("<td>"): # resp로 가져온 데이터가 한줄로 저장되어 split으로 list에 저장
                if re.search(pattern, line):
                    value = line
        
            tmp = value.split(">", 2)
            node_cnt = tmp[1].strip("</a")
            if int(node_cnt) == self.hadoop_tt_nodes:
                self.svc_err.append(0)
                self.res_arr['hadoop_node_count'] = '%s/%s' % (node_cnt, self.hadoop_tt_nodes)
                logging.info('[%s] tasktracerk node count : %s/%s ' % (self.svc, node_cnt, self.hadoop_tt_nodes))
            else:
                self.svc_err.append(1)
                self.res_arr['hadoop_node_count'] = '%s/%s' % (node_cnt, self.hadoop_tt_nodes)
                self.err_msg['hadoop_node_count'] = '[%s][WARN] Make sure your tasktracker %s/%s' % (
                                                      self.svc, node_cnt, self.hadoop_tt_nodes)
                logging.warn('[%s] tasktracerk node count : %s/%s ' % (self.svc, node_cnt, self.hadoop_tt_nodes))
        except:
            node_cnt = -1
            self.svc_err.append(node_cnt)
            self.res_arr['hadoop_node_count'] = node_cnt
            self.err_msg['hadoop_node_count'] = '[%s][FAIL] jobtracker monitor page read fail' % (self.svc)
            logging.error('[%s] service port has closed %s:%s' % (self.svc, self.svc_url, self.hadoop_monitor_port))
            

class HdfsSvcRecog(SvcRecog):
    def __init__(self, config_file):
        SvcRecog.__init__(self, 'hdfs', config_file)
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        logging.info('[%s] additional parameter read: %s' % (self.svc, config_file))
        self.hdfs_monitor_port = config.get('hdfs', 'hdfs_monitor_port')
        self.hdfs_dn_nodes = int(config.get('hdfs', 'hdfs_dn_nodes'))

    def set_nodes(self):
        # dfshealth.jsp에서 nodes 개수 획득
        # java lib만들면 없앨 예정(임시)
        try:
            resp = urllib2.urlopen("http://%s:%s/dfshealth.jsp" %(self.svc_url, self.hdfs_monitor_port))
            web_pg = resp.read()
            pattern = "whatNodes\=LIVE"
            for line in web_pg.split('<a'):
                if re.search(pattern, line):
                    value = line
             
            tmp = value.split()
            node_cnt = tmp[6].strip("<tr")

            if int(node_cnt) == self.hdfs_dn_nodes :
                self.svc_err.append(0)
                self.res_arr['hdfs_node_count'] = '%s/%s' % (node_cnt, self.hdfs_dn_nodes)
                logging.info('[%s] datanode count %s/%s' %(self.svc, node_cnt, self.hdfs_dn_nodes))
            else:
                self.svc_err.append(1)
                self.res_arr['hdfs_node_count'] = '%s/%s' % (node_cnt, self.hdfs_dn_nodes)
                self.err_msg['hdfs_node_count'] = '[%s][WARN] Make sure your datanode %s/%s' % (
                                                   self.svc, node_cnt, self.hdfs_dn_nodes) 
                logging.warn('[%s] datanode count %s/%s' %(self.svc, node_cnt, self.hdfs_dn_nodes))
        except:
            node_cnt = -1
            self.svc_err.append(node_cnt)
            self.res_arr['hdfs_node_count'] = node_cnt
            self.err_msg['hdfs_node_count'] = '[%s][FAIL] datanode monitor parge read fail' %(self.svc)
            logging.error('[%s] service port has cloesed %s:%s' % (self.svc, self.svc_url, self.hdfs_monitor_port))

    def set_hdfs_size(self):
        # dfsadmin -report에서 hdfs size 획득
        # java lib 만들면 없앨 예정(임시) 
        size_pipe = subprocess.Popen(['ssh', self.svc_acc+'@'+self.svc_host, '('+self.svc_home+'/bin/hadoop', 
                                      'dfsadmin', '-report)'],
                                      shell=False,
                                      stdout=subprocess.PIPE)
        out = size_pipe.stdout.readlines()
        size_pipe.terminate()
        if len(out) != 0:
            total_cap = int(out[1].strip('\n').split()[2])
            remain = int(out[2].strip('\n').split()[2])
            used = int(out[3].strip('\n').split()[2])
            per_tmp = out[4].strip('\n').split()[2]
            per = per_tmp.strip('%')
            self.hdfs_capa_tb = round(total_cap/1024/1024/1024/1024,2)
            self.hdfs_used_tb = round(used/1024/1024/1024/1024, 2)
        
            self.svc_err.append(0)
            self.res_arr['hdfs_size'] = '%s/%s(TB) %s %%' %(self.hdfs_used_tb, self.hdfs_capa_tb, per)
            logging.info('[%s] service usage size : %s / %s (TB) - %s %%' % (self.svc,
                          self.hdfs_used_tb, self.hdfs_capa_tb, per))
        else: 
            self.hdfs_capa_tb = -1
            self.hdfs_used_tb = -1
            self.svc_err.append(-1)
            self.res_arr['hdfs_size'] = -1
            self.err_msg['hdfs_size'] = '[%s][FAIL] Fail to loading HDFS usage' % (self.svc)

class DbSvcRecog(SvcRecog):
    def __init__(self, config_file):
        SvcRecog.__init__(self, 'db', config_file)

    def generate_sql(self, entity_id, mode):
        # delay 조회 sql 생성
        unixtime = int(time.time())
        if entity_id == 'an':
            svrs = range(1, 48) + range(70,72) + range(111,114) + range(115,119)
            stype = [1, 101]
            ignore = [ 40, 42, 44]
            for i in ignore:
                svrs.remove(i)
            svr_com = ",".join(map(str, svrs))
            stype_com = ",".join(map(str, stype))
        else : 
            self.svc_err.append(1)
            self.res_arr[mode] = 'entity_id : %s ' % (entity_id)
            self.err_msg[mode] = '[%s][WARN] Make sure entity id name %s' % (
                                               self.svc, entity_id)
            logging.warn('[%s] db entity_id :%s' %(self.svc, entity_id))    
  
        if mode == 'day':
            sql = '''select * from tbl where svr in (%s)''' % (svr_com)
        else :
            sql = '''select * from tbl_another where svr in (%s)''' % (svr_com)
        
        return sql 

    def get_delay_svr(self, mode):
        # db 조회
        try: 
            if mode == 'day':
                dict_index = "db_day"
            else:
                dict_index = "db_month"

            db = MySQLdb.connect(host=self.svc_host, port=int(self.svc_port), user=self.db_user, 
                                 passwd=self.db_passwd, db=self.db_name)

            res = []
            for entity in self.db_games:
                sql = self.generate_sql(entity, dict_index)
                cur = db.cursor()
                cur.execute(sql)
                for row in cur.fetchall():
                    res.append(row)
                cur.close()       
          
            db.close()
        except IOError as e:
            res = []
            self.svc_err.append(-1)
            self.res_arr[dict_index] = res
            self.err_msg[dict_index] = '[%s][FAIL] Fail to search db' % (self.svc)
    
        #상태 확인을 위한 분류 
        ok=[];warn=[];cri=[];fail=[]; 
        # dictionary value에 배열을 넣으려면 미리 선언해줘야 함..
        # 미리 선언 안하면 key erro 발생
        self.res_arr[dict_index] = []
        self.err_msg[dict_index] = []
        res.append(('dummy','1970-01-01_00:00:00'))
        for i in res:
            if res[0] == i:
                game = i[0]

            if game != i[0] : 
                if len(fail) == 0 and len(cri) == 0 and len(warn) == 0:
                    self.svc_err.append(0)
                    self.res_arr[dict_index].append('[%s][GOOD]-normal: %s, warn: %s, critical: %s, fail: %s' % (
                                               game, len(ok), len(warn), len(cri), len(fail)))
                elif len(warn) > 0 and len(fail) == 0 and len(cri) == 0:
                    for it in range(0, len(warn)):
                        self.svc_err.append(1)

                    self.res_arr[dict_index].append('[%s][WARN]-normal: %s, warn: %s, critical: %s, fail: %s' % (
                                               game, len(ok), len(warn), len(cri), len(fail)))
                    for msg in warn:
                        self.err_msg[dict_index].append(msg)
                    logging.warn('[%s][DELAY] %s %s - warn: %s, critical: %s, fail: %s' % (
                                               self.svc, game, dict_index, len(warn), len(cri), len(fail)))
                else:
                    for it in range(0, len(warn)):
                        self.svc_err.append(1)
                    for it in range(0, len(cri)+len(fail)):
                        self.svc_err.append(-1)

                    self.res_arr[dict_index].append('[%s][ERROR]-normal: %s, warn: %s, critical: %s, fail: %s' % (
                                               game, len(ok), len(warn), len(cri), len(fail)))

                    for msg in warn+cri+fail:
                        self.err_msg[dict_index].append(msg)

                    logging.error('[%s][DELAY] %s %s - warn: %s, critical: %s, fail: %s' % (
                                               self.svc, game, dict_index, len(warn), len(cri), len(fail)))
            
                logging.info('[%s][%s] %s lar status - ok: %s, warn: %s, cri: %s, fail: %s' %(
                              self.svc, mode, game, len(ok),len(warn), len(cri), len(fail)))
                ok=[];warn=[];cri=[];fail=[]; 

            if re.search('warn', i[5]):
                warn.append('[%s][%s] %s-%s last: %s %s' % (mode, i[0], str(i[1]).zfill(2), str(i[2]).zfill(2), 
                                                             i[4], i[5]))
            elif re.search('critical', i[5]):
                cri.append('[%s][%s] %s-%s last: %s %s' % (mode, i[0], str(i[1]).zfill(2), str(i[2]).zfill(2), 
                                                             i[4], i[5]))
            elif re.search('fail', i[5]):
                fail.append('[%s][%s] %s-%s last: %s %s' % (mode, i[0], str(i[1]).zfill(2), str(i[2]).zfill(2), 
                                                             i[4], i[5]))
            else:
                ok.append('[%s][%s] %s-%s last: %s %s' % (mode, i[0], str(i[1]).zfill(2), str(i[2]).zfill(2), 
                                                             i[4], i[5]))
            game = i[0]

    def is_pid_exist(self):
        # 서비스 pid 파일 확인 overide
        ssh = subprocess.Popen(['ssh', self.svc_acc+'@'+self.svc_host,
                                'ps -ef | grep mysql | grep -v grep | awk \'{print $2}\''],
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        pid = ssh.stdout.readline().strip('\n')
        ssh.terminate()
        # pid 확인했으면 그 pid로 프로세스 확인
        if pid != "":
            pid_dir = subprocess.Popen(['ssh', self.svc_acc+'@'+self.svc_host, '[ -d /proc/%s ] && echo $?' % pid],
                                       shell=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            pid_exist = pid_dir.stdout.readline().strip('\n')
            pid_dir.terminate()

            self.svc_err.append(0)
            logging.info('[%s] %s pid : %s, process exist! ' % (self.svc, self.svc_host, pid))
            self.res_arr['pid'] = pid
        else:
            pid = -1
            self.svc_err.append(pid)
            logging.error('[%s] %s server has not pidfile ' % (self.svc, self.svc_host))
            self.res_arr['pid'] = pid
            self.err_msg['pid'] = '[%s][FAIL] %s server has not pidfile ' % (self.svc, self.svc_host)

    def set_heap_size(self):
        # db는 heap이 필요없음
        logging.info('[%s] Heap size is not neccessary for db' % self.svc)

class HiveSvcRecog(SvcRecog):
    def __init__(self, config_file):
        SvcRecog.__init__(self, 'hive', config_file)

    def run_dummy(self, sql):
        res = subprocess.Popen([self.svc_home+'/bin/hive', '-e', sql],
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)    
        res.wait()
        out, err = res.communicate()
        out = out.strip('\n')
        if out == '1':
            self.svc_err.append(0)
            self.res_arr['hive_dummy_res'] = out
        else:
            out = -1
            self.svc_err.append(out)
            self.res_arr['hive_dummy_res'] = out
            self.err_msg['hive_dummy_res'] = '[%s][FAIL] Fail to runnig dummy query' %(self.svc) 

