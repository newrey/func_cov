
all:	clean comp run cov_rpt gz_xml

clean:
	\rm -rf simv* csrc* *.log DVEfiles urgReport vdCovLog novas* ucli.key
comp:
	vcs  -cm line+cond+fsm+tgl+branch+assert+path -lca -sverilog -full64 testbench.sv -l comp.log
run:
	./simv +vcs+lic+wait -l run.log
cov_rpt:
	urg -lca -dir simv.vdb

gz_xml:
	cd simv.vdb/snps/coverage/db/testdata/test \
	&& mv testbench.cumulative.xml testbench.cumulative.xml.gz && gzip -d testbench.cumulative.xml.gz\
	&& mv siminfo.xml siminfo.xml.gz && gzip -d siminfo.xml.gz\
	&& mv testbench.inst.xml testbench.inst.xml.gz && gzip -d testbench.inst.xml.gz