if [[ "$@" =~ "range" ]]; then
    python collect_data.py dump graph analyze_dir="./analyze/daily/,./analyze/currently/" show_actual y=temp_max,temp_min,temp minvar=temp_min maxvar=temp_max type=box
else
    python collect_data.py dump graph analyze_dir="./analyze/daily/,./analyze/currently/" show_actual y=temp_max,temp_min,temp type=box
fi
