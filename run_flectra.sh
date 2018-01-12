# ps -ef |grep flectra | grep -v grep | awk '{print $2}' | xargs kill -9
./flectra-bin -c flectra.conf

