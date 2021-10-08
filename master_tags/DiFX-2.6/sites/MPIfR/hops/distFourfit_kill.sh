
for pid in `ps axuf|grep fourfit_d|cut -c10-16`; do kill -9 $pid; done

