if [ -z "$1" ]; then
    ANALYZE_DIR="./analyze/daily/"
else
    ANALYZE_DIR="./analyze/$1/"
fi

python collect_data.py dump graph=True var=precip_chance analyze_dir="$ANALYZE_DIR" type=box ymin=0 ymax=1
