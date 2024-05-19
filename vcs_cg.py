import xml.etree.ElementTree as ET
from collections import defaultdict

class vcs_cg(object):
    # cp/cc定义
    cp_define_data = defaultdict(str)
    cc_define_data = defaultdict(str)

    missed_cg_cp = defaultdict(str)
    missed_cg_cc = defaultdict(str)

    root = None

    def parse(self, file):
        # 从文件中解析XML
        tree = ET.parse(file)
        self.root = tree.getroot()

        # 查找cg_src节点
        cg_src = self.root.find('.//cg_src')

        # 查找cg_src节点下的cp/cc
        cg_srcs_cp = cg_src.findall('./cp')
        cg_srcs_cc = cg_src.findall('./cc')

        # 解析定义
        for cp in cg_srcs_cp:
            id = cp.get('id')
            self.cp_define_data[id] = {'exprname': cp.get('exprname'), 'is_real': cp.get('is_real')}

        for cc in cg_srcs_cc:
            id = cp.get('id')
            self.cc_define_data[id] = {'name': cp.get('name')}

    def get_missed_cg_cp(self):
        # 查找cg_src节点
        cg_src = self.root.find('.//cg_src')

        # 解析覆盖结果
        cg_covdef = cg_src.find('./cg_covdef')
        for cp in cg_covdef.findall('./cp'):
            cp_type = cp.get('type')
            cp_id = cp.get('id')
            exprname = self.cp_define_data[cp_id]['exprname']
            self.missed_cg_cp[exprname] = list()
            if cp_type == 'user':
                for bn in cp.findall('bn'):
                    id = bn.get('id')
                    name = bn.get('name') # 命中值
                    data = bn.get('data') # 命中次数
                    excl = bn.get('excl')
                    unreachable = bn.get('unreachable')

                    if data == '0' and excl == '0':
                        self.missed_cg_cp[exprname].append({'val':name, 'type':'cp.user'})
            elif cp_type == 'auto_c':
                data = cp.find('data')
                type = data.get('type')
                vals = data.get('vals') # 命中次数
                index = data.get('index') # 命中值

                if type == 'compact':
                    vals_arr = vals.split(' ')
                    index_arr = index.split(' ')
                    for i,_ in enumerate(vals_arr):
                        if vals_arr[i] == '0':
                            self.missed_cg_cp[exprname].append({'val':index_arr[i], 'type':'cp.auto_c'})

                else:
                    raise Exception('Unsupport tpye:' + type)
            else:
                raise Exception('Unsupport tpye:' + cp_type)


            pass
    
    def print_missed_cg_cp(self):
        print("missed_cg_cp:")
        for key in self.missed_cg_cp:
            for val in self.missed_cg_cp[key]:
                print(f"key:{key},val:{val['val']},type:{val['type']}")
                pass

    def get_missed_cg_cc(self):
        # 查找cg_src节点
        cg_src = self.root.find('.//cg_src')

        # 解析覆盖结果
        cg_covdef = cg_src.find('./cg_covdef')
        for cc in cg_covdef.findall('./cc'):
            for cn_nt_s in cc.findall('./covered_auto_crosses/cn_nt_s'):
                val = cn_nt_s.get('val') # 交叉1值
                cn_nt_s_d = cn_nt_s.find('./cn_t_s_d')
            # self.cg_result_cc[cp_id].append({'data':data})


vcs_cg = vcs_cg()
vcs_cg.parse('/code/vcs_example/func_cov/simv.vdb/snps/coverage/db/testdata/test/testbench.cumulative.xml')
vcs_cg.get_missed_cg_cp()
vcs_cg.print_missed_cg_cp()