#!/bin/bash
# Installs a tiny job runner on the render machine: any job.tgz uploaded to the
# job folder is unpacked and its run.sh executed, one job at a time.
W=/opt/umrah; T=197a7cf9035120fd78d4b4d1; OUT=$W/www/$T
cat > $W/runner.sh <<'SH'
#!/bin/bash
W=/opt/umrah; T=197a7cf9035120fd78d4b4d1; OUT=$W/www/$T; n=0
while true; do
  if [ -f $OUT/job.tgz ]; then
    n=$((n+1)); J=$W/jobs/$n; mkdir -p $J
    tar -xzf $OUT/job.tgz -C $J && rm -f $OUT/job.tgz
    echo "$(date -u +%H:%M:%S) job $n start" >> $OUT/status.txt
    (cd $J && bash run.sh > $J/log.txt 2>&1); rc=$?
    cp $J/log.txt $OUT/job$n.log
    echo "$(date -u +%H:%M:%S) job $n end (exit $rc)" >> $OUT/status.txt
  fi
  sleep 5
done
SH
chmod +x $W/runner.sh
pkill -f /opt/umrah/runner.sh 2>/dev/null
setsid nohup $W/runner.sh >/dev/null 2>&1 < /dev/null &
echo "$(date -u +%H:%M:%S) runner installed" >> $OUT/status.txt
echo "Runner installed on $(hostname) - you can close this window."
